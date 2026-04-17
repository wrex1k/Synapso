from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from app.core.registry import registry
from app.games.core.base_game import GAME_ID_MAP
from app.models.user import User
from app.repository.activity_repository import get_time_played
from app.repository.run_repository import fetch_user_run_history
from app.repository.stats_repository import fetch_all_user_stats, fetch_player_game_stats
from app.utils.logger import get_logger
from translations.translation import get_translation_manager, translate

logger = get_logger(__name__)

_GAME_SLUGS = ["stroop", "memory_grid", "mental_rotation"]
_GAME_LABELS = {
    "stroop": "Stroop",
    "memory_grid": "Memory Grid",
    "mental_rotation": "Mental Rotation",
}
_GAME_ID_TO_SLUG = {value: key for key, value in GAME_ID_MAP.items()}
_MIN_UTC = datetime.min.replace(tzinfo=timezone.utc)


@dataclass
class DashboardData:
    time_played_total: int
    all_stats: dict[str, Any]
    per_game: dict[str, dict | None]
    histories: dict[str, list[dict]]


class DashboardController(QObject):
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
            per_game={},
            histories={},
        )

    @property
    def loaded_once(self) -> bool:
        return self._loaded_once

    def mark_loaded_once(self) -> None:
        self._loaded_once = True

    def is_loading(self) -> bool:
        return any(getattr(t, "isRunning", lambda: False)() for t in self._threads)

    def load(self) -> None:
        self.loading_started.emit()
        thread = registry.run_thread(
            self._fetch_all,
            self._on_data_loaded,
            name="dashboard-fetch",
        )
        self._keep_thread(thread)

    def _keep_thread(self, thread: QThread) -> None:
        self._threads.append(thread)

        def _cleanup_thread(t=thread):
            if t in self._threads:
                self._threads.remove(t)
            self.loading_finished.emit()

        thread.finished.connect(_cleanup_thread)

    def _fetch_all(self) -> DashboardData:
        time_played_total = 0
        try:
            time_played_total = get_time_played(self._user.id) or 0
        except Exception:
            logger.exception("Failed to load total time played")

        try:
            all_stats = fetch_all_user_stats(self._user.id) or {"games": []}
        except Exception:
            logger.exception("Failed to load all user stats")
            all_stats = {"games": []}

        per_game: dict[str, dict | None] = {}
        histories: dict[str, list[dict]] = {}

        for slug in _GAME_SLUGS:
            try:
                per_game[slug] = fetch_player_game_stats(self._user.id, slug)
            except Exception:
                logger.exception("Failed to load per-game stats for %s", slug)
                per_game[slug] = None

            try:
                histories[slug] = fetch_user_run_history(self._user.id, slug, limit=20) or []
            except Exception:
                logger.exception("Failed to load run history for %s", slug)
                histories[slug] = []

        return DashboardData(
            time_played_total=time_played_total,
            all_stats=all_stats,
            per_game=per_game,
            histories=histories,
        )

    def _on_data_loaded(self, result: DashboardData | None) -> None:
        if not result:
            return

        self._data = result
        self.data_changed.emit()

    def get_welcome_model(self) -> dict[str, str]:
        streak = self._compute_current_streak()
        all_runs = self._get_all_runs_sorted_desc()
        total_games = len(all_runs)
        favorite_game_slug = self._get_most_played_slug()

        return {
            "daily_streak": self._format_day_label(streak) if streak else "—",
            "total_games": str(total_games) if total_games else "—",
            "time_played": self._format_time(self._data.time_played_total),
            "favorite_game": self._label_for_slug(favorite_game_slug),
        }

    def get_activity_model(self) -> dict[str, str]:
        history_runs = self._get_all_runs_sorted_desc()
        total_runs = len(history_runs)
        total_trials = sum((row.get("total_trials") or 0) for _, _, row in history_runs)
        streak = self._compute_current_streak()

        goal = self._estimate_daily_goal()
        done = len(self._get_today_runs())
        shown_done = min(done, goal) if goal > 0 else done

        if done >= goal and goal > 0:
            goal_hint = translate("DashboardView", "Goal completed for today")
        elif done == 0:
            goal_hint = translate("DashboardView", "Start a session to begin today’s goal")
        else:
            remaining = max(goal - done, 0)
            goal_hint = translate(
                "DashboardView",
                "{count} more session(s) to reach today’s goal",
            ).format(count=remaining)

        return {
            "total_runs": str(total_runs) if total_runs else "—",
            "total_trials": str(total_trials) if total_trials else "—",
            "current_streak": self._format_day_label(streak) if streak else "—",
            "time_played": self._format_time(self._data.time_played_total),
            "goal_progress": f"{shown_done} / {goal}",
            "goal_hint": goal_hint,
        }

    def get_recent_games_model(self) -> list[dict[str, str]]:
        runs = self._get_all_runs_sorted_desc()
        items: list[dict[str, str]] = []

        for dt, slug, row in runs[:3]:
            pi = row.get("pi_run")
            pi_text = f"{pi:.2f} PI" if isinstance(pi, (int, float)) else "—"
            reaction = row.get("avg_reaction_time_ms")
            reaction_text = f"{int(reaction)} ms" if isinstance(reaction, (int, float)) else "—"
            acc = row.get("avg_accuracy")
            acc_text = f"{acc}%" if isinstance(acc, (int, float)) else "—"
            items.append(
                {
                    "game": self._label_for_slug(slug),
                    "date": self._relative_datetime_text(dt),
                    "pi": pi_text,
                    "reaction": reaction_text,
                    "accuracy": acc_text,
                }
            )

        return items

    def get_trend_chart_model(self) -> dict[str, Any]:
        most_played_slug = self._get_most_played_slug()
        if not most_played_slug:
            return {"slug": None, "values": [], "y_range": (0.0, 1.0)}

        runs: list[tuple[datetime | None, float]] = []
        for row in self._data.histories.get(most_played_slug, []) or []:
            pi = row.get("pi_run")
            if pi is None:
                continue
            runs.append((self._parse_dt(row.get("started_at")), float(pi)))

        runs.sort(key=lambda item: item[0] or _MIN_UTC)
        values = [pi for _, pi in runs][-10:]
        y_range = self._safe_y_range(values) if values else (0.0, 1.0)

        return {
            "slug": most_played_slug,
            "values": values,
            "y_range": y_range,
        }

    def get_highlights_model(self) -> dict[str, str]:
        fav_row = self._get_most_played_row()

        if not fav_row:
            return {
                "best_accuracy": "—",
                "fastest_reaction": "—",
            }

        return {
            "best_accuracy": self._fmt_pct(fav_row.get("avg_accuracy_overall")),
            "fastest_reaction": self._fmt_ms(fav_row.get("avg_reaction_time_ms")),
        }

    def get_continue_model(self) -> dict[str, Any]:
        runs = self._get_all_runs_sorted_desc()
        if not runs:
            return {
                "slug": None,
                "game_name": "—",
                "info": "—",
                "enabled": False,
            }

        dt, slug, _row = runs[0]
        return {
            "slug": slug,
            "game_name": self._label_for_slug(slug),
            "info": self._relative_datetime_text(dt),
            "enabled": True,
        }

    def _get_today_runs(self) -> list[tuple[datetime | None, str, dict]]:
        today = datetime.now(timezone.utc).date()
        return [
            item
            for item in self._get_all_runs_sorted_desc()
            if item[0] and item[0].date() == today
        ]

    def _get_all_runs_sorted_desc(self) -> list[tuple[datetime | None, str, dict]]:
        runs: list[tuple[datetime | None, str, dict]] = []

        for slug, hist in self._data.histories.items():
            for row in hist or []:
                runs.append((self._parse_dt(row.get("started_at")), slug, row))

        runs.sort(key=lambda item: item[0] or _MIN_UTC, reverse=True)
        return runs

    def _compute_current_streak(self) -> int:
        today = datetime.now(timezone.utc).date()
        days = {
            dt.date()
            for dt, _, _ in self._get_all_runs_sorted_desc()
            if dt is not None and dt.date() <= today
        }

        if not days:
            return 0

        cursor = today if today in days else today - timedelta(days=1)
        streak = 0

        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)

        return streak

    def _estimate_daily_goal(self) -> int:
        runs_by_day: dict[Any, int] = {}

        for dt, _, _ in self._get_all_runs_sorted_desc():
            if dt is None:
                continue
            day = dt.date()
            runs_by_day[day] = runs_by_day.get(day, 0) + 1

        if not runs_by_day:
            return 3

        avg = sum(runs_by_day.values()) / len(runs_by_day)
        return max(1, round(avg))

    def _get_most_played_row(self) -> dict | None:
        games = self._data.all_stats.get("games", []) or []
        return max(
            (g for g in games if g.get("total_runs") is not None),
            key=lambda g: g.get("total_runs") or 0,
            default=None,
        )

    def _get_most_played_slug(self) -> str | None:
        row = self._get_most_played_row()
        if not row:
            return None
        return self._game_slug_from_id(row.get("game_id"))

    def _game_slug_from_id(self, game_id: Any) -> str | None:
        return _GAME_ID_TO_SLUG.get(game_id)

    def _safe_y_range(self, values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 1.0

        low = min(values)
        high = max(values)

        if abs(high - low) < 1e-9:
            padding = max(0.1, abs(low) * 0.1)
            return round(low - padding, 3), round(high + padding, 3)

        padding = (high - low) * 0.12
        return round(low - padding, 3), round(high + padding, 3)

    def _label_for_slug(self, slug: str | None) -> str:
        if not slug:
            return "—"
        return translate("DashboardView", _GAME_LABELS.get(slug, slug))

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt + timedelta(hours=1)
        except Exception:
            logger.exception("DashboardController._parse_dt: failed to parse value=%s", value)
            return None

    def _relative_datetime_text(self, dt: datetime | None) -> str:
        if dt is None:
            return "—"

        now = datetime.now(timezone.utc)

        if dt.date() == now.date():
            return translate("DashboardView", "Today at {time}").format(
                time=dt.strftime("%H:%M")
            )

        if dt.date() == (now.date() - timedelta(days=1)):
            return translate("DashboardView", "Yesterday at {time}").format(
                time=dt.strftime("%H:%M")
            )

        return dt.strftime("%d.%m.%Y • %H:%M")

    def _format_time(self, seconds: int) -> str:
        if not seconds:
            return translate("DashboardView", "0 min")

        hours, rem = divmod(int(seconds), 3600)
        minutes = rem // 60

        if hours:
            return translate("DashboardView", "{hours}h {minutes}m").format(
                hours=hours,
                minutes=minutes,
            )

        return translate("DashboardView", "{minutes} min").format(minutes=minutes)

    def _format_day_label(self, count: int) -> str:
        lang = getattr(get_translation_manager(), "current_language", "en")

        if lang == "en" or str(lang).startswith("en-"):
            return f"{count} day" if count == 1 else f"{count} days"

        txt = translate("DashboardView", "%n day", n=count)
        result = txt.replace("%n", str(count))

        if result.endswith(" day") and not result.endswith(" days") and count != 1:
            return f"{count} days"

        return result

    def _fmt_pct(self, value: float | None) -> str:
        if value is None:
            return "—"
        pct = value * 100 if value <= 1.0 else value
        return f"{pct:.0f}%"

    def _fmt_ms(self, value: float | None) -> str:
        if value is None:
            return "—"
        return f"{int(value)} ms"