from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from app.core.registry import registry
from app.games.core.base_game import GAME_SLUGS, GAME_ID_TO_SLUG
from app.models.user import User
from app.repository.run_repository import parse_datetime
from app.service.stats_service import get_dashboard_stats, calculate_user_streak, estimate_daily_goal, calculate_goal_status
from app.utils.formatters import format_time_duration, format_day_label, format_percentage, format_milliseconds, format_relative_datetime, format_pi, format_game_label

from translations.translation import translate

_MIN_UTC = datetime.min.replace(tzinfo=timezone.utc)

MAX_RECENT_GAMES = 3
TREND_CHART_POINTS = 10

@dataclass
class DashboardData:
    """Container for dashboard data used by the dashboard controller."""
    time_played_total: int
    all_stats: dict[str, Any]
    histories: dict[str, list[dict]]


class DashboardController(QObject):
    """Controller responsible for loading dashboard data and building UI models."""
    data_changed = Signal()
    loading_started = Signal()
    loading_finished = Signal()

    def __init__(self, user: User, parent: QObject | None = None):
        super().__init__(parent)
        self._user = user
        self._threads: list[QThread] = []
        self._loaded_once = False

        self._data = DashboardData(
            time_played_total=0,
            all_stats={"games": []},
            histories={},
        )

    @property
    def loaded_once(self) -> bool:
        """Return whether the dashboard has already been loaded at least once."""
        return self._loaded_once

    def mark_loaded_once(self) -> None:
        """Mark the dashboard as loaded at least once."""
        self._loaded_once = True

    def is_loading(self) -> bool:
        """Return whether any dashboard loading thread is currently running."""
        return any(thread.isRunning() for thread in self._threads)

    def load(self) -> None:
        """Start asynchronous loading of dashboard data if no load is currently running."""
        if self.is_loading():
            return
    
        self.loading_started.emit()
        thread = registry.run_thread(
            self._fetch_all,
            self._on_data_loaded,
            name="dashboard-fetch",
        )
        self._keep_thread(thread)

    def _keep_thread(self, thread: QThread) -> None:
        """Track a running thread and emit loading_finished after the last one completes."""
        self._threads.append(thread)

        def _cleanup_thread(t: QThread = thread):
            if t in self._threads:
                self._threads.remove(t)

            if not self.is_loading():
                self.loading_finished.emit()

        thread.finished.connect(_cleanup_thread)

    def _fetch_all(self) -> DashboardData:
        """Fetch all dashboard data required for dashboard view models."""
        data = get_dashboard_stats(self._user.id, GAME_SLUGS)
        
        return DashboardData(
            time_played_total=data["time_played_total"],
            all_stats=data["all_stats"],
            histories=data["histories"],
        )

    def _on_data_loaded(self, result: DashboardData | None) -> None:
        """Store loaded dashboard data and notify the UI when loading succeeds."""
        if not result:
            return

        self._data = result
        self.data_changed.emit()

    def _compute_base_stats(self) -> dict[str, Any]:
        """Compute shared dashboard statistics reused by multiple dashboard sections."""
        games = self._data.all_stats.get("games", [])
        streak = calculate_user_streak(self._data.histories)
        goal = estimate_daily_goal(self._data.histories)
        today_runs = self._get_today_runs()
        
        return {
            "streak": streak,
            "total_runs": sum(g.get("total_runs", 0) for g in games),
            "time_played": self._data.time_played_total,
            "favorite_slug": self._get_most_played_slug(),
            "goal": goal,
            "today_done": len(today_runs),
        }

    def get_welcome_model(self) -> dict[str, str]:
        """Return formatted data for the welcome section."""
        stats = self._compute_base_stats()

        return {
            "daily_streak": format_day_label(stats["streak"]),
            "total_games": str(stats["total_runs"]),
            "time_played": format_time_duration(stats["time_played"]),
            "favorite_game": format_game_label(stats["favorite_slug"]),
        }

    def get_goal_model(self) -> dict[str, str]:
        """Return formatted data for the daily goal section."""
        stats = self._compute_base_stats()
        
        goal_status = calculate_goal_status(stats["today_done"], stats["goal"])
        
        if goal_status["status"] == "completed":
            goal_hint = translate("DashboardView", "Goal completed for today")
        elif goal_status["status"] == "not_started":
            goal_hint = translate("DashboardView", "Start a session to begin today's goal")
        else:
            goal_hint = translate("DashboardView", "{count} more session(s) to reach today's goal").format(count=goal_status["remaining"])

        return {
            "goal_progress": f"{goal_status['shown_done']} / {goal_status['goal']}",
            "goal_hint": goal_hint,
        }

    def get_trend_chart_model(self) -> dict[str, Any]:
        """Return recent PI values and chart range for the most played game."""
        most_played_slug = self._get_most_played_slug()
        if not most_played_slug:
            return {"slug": None, "values": [], "y_range": (0.0, 1.0)}

        runs: list[tuple[datetime | None, float]] = []
        for row in self._data.histories.get(most_played_slug, []):
            pi = row.get("pi_run")
            if pi is None:
                continue
            runs.append((parse_datetime(row.get("started_at")), float(pi)))

        runs.sort(key=lambda item: item[0] or _MIN_UTC)
        values = [pi for _, pi in runs][-TREND_CHART_POINTS:]
        y_range = self._calculate_safe_y_range(values) if values else (0.0, 1.0)

        return {
            "slug": most_played_slug,
            "values": values,
            "y_range": y_range,
        }

    def get_highlights_model(self) -> dict[str, str]:
        """Return highlight metrics for the most played game."""
        fav_row = self._get_most_played_row()

        if not fav_row:
            return {
                "best_accuracy": translate("DashboardView", "No data"),
                "fastest_reaction": translate("DashboardView", "No data"),
            }

        return {
            "best_accuracy": format_percentage(fav_row.get("avg_accuracy")),
            "fastest_reaction": format_milliseconds(fav_row.get("avg_reaction_time_ms")),
        }

    def get_recent_games_model(self) -> list[dict[str, str]]:
        """Return formatted summaries of the most recent game sessions."""
        runs = self._get_all_runs_sorted_desc()
        items: list[dict[str, str]] = []

        for dt, slug, row in runs[:MAX_RECENT_GAMES]:
            items.append(
                {
                    "game": format_game_label(slug),
                    "date": format_relative_datetime(dt),
                    "pi": format_pi(row.get("pi_run")),
                    "reaction": format_milliseconds(row.get("avg_reaction_time_ms")),
                    "accuracy": format_percentage(row.get("avg_accuracy")),
                }
            )

        return items
    
    def get_continue_model(self) -> dict[str, Any]:
        """Return data for the continue section based on the latest played session."""
        runs = self._get_all_runs_sorted_desc()
        no_data = translate("DashboardView", "No data")
        if not runs:
            return {
                "slug": None,
                "game_name": no_data,
                "info": no_data,
                "enabled": False,
            }

        dt, slug, _row = runs[0]
        return {
            "slug": slug,
            "game_name": format_game_label(slug),
            "info": format_relative_datetime(dt),
            "enabled": True,
        }

    def _get_today_runs(self) -> list[tuple[datetime | None, str, dict]]:
        """Return all runs started on the current local date."""
        today = datetime.now().astimezone().date()
        return [
            item
            for item in self._get_all_runs_sorted_desc()
            if item[0] and item[0].date() == today
        ]

    def _get_all_runs_sorted_desc(self) -> list[tuple[datetime | None, str, dict]]:
        """Collect all runs across games and sort them from newest to oldest."""
        runs: list[tuple[datetime | None, str, dict]] = []

        for slug, hist in self._data.histories.items():
            for row in hist:
                runs.append((parse_datetime(row.get("started_at")), slug, row))

        runs.sort(key=lambda item: item[0] or _MIN_UTC, reverse=True)
        return runs

    def _get_most_played_row(self) -> dict | None:
        """Return the aggregated stats row for the most played game."""
        games = self._data.all_stats.get("games", [])
        return max(
            (g for g in games if g.get("total_runs") is not None),
            key=lambda g: g.get("total_runs") or 0,
            default=None,
        )

    def _get_most_played_slug(self) -> str | None:
        """Return the slug of the most played game."""
        row = self._get_most_played_row()
        if not row:
            return None
        return GAME_ID_TO_SLUG.get(row.get("game_id"))

    def _calculate_safe_y_range(self, values: list[float]) -> tuple[float, float]:
        """Calculate safe Y-axis range with padding for chart display."""
        if not values:
            return 0.0, 1.0

        low = min(values)
        high = max(values)

        if abs(high - low) < 1e-9:
            padding = max(0.1, abs(low) * 0.1)
            return round(low - padding, 3), round(high + padding, 3)

        padding = (high - low) * 0.12
        return round(low - padding, 3), round(high + padding, 3)

    def cleanup(self):
        """Stop any running threads."""
        for thread in self._threads:
            if thread.isRunning():
                thread.quit()
                thread.wait()
