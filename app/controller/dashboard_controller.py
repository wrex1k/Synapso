from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from PySide6.QtCore import QObject, Signal, QThread

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

        logger.debug(
            "DashboardController initialized: user_id=%s username=%s",
            getattr(self._user, "id", None),
            getattr(self._user, "username", None),
        )

    @property
    def loaded_once(self) -> bool:
        return self._loaded_once

    def mark_loaded_once(self) -> None:
        self._loaded_once = True

    def is_loading(self) -> bool:
        return any(getattr(t, "isRunning", lambda: False)() for t in self._threads)

    def load(self) -> None:
        logger.debug("DashboardController.load: starting background fetch")
        self.loading_started.emit()
        thread = registry.run_thread(
            self._fetch_all,
            self._on_data_loaded,
            name="dashboard-fetch",
        )
        self._keep_thread(thread)

    def _keep_thread(self, thread: QThread) -> None:
        logger.debug("DashboardController._keep_thread: registering thread=%s", thread)
        self._threads.append(thread)

        def _cleanup_thread(t=thread):
            logger.debug("DashboardController thread finished: thread=%s", t)
            if t in self._threads:
                self._threads.remove(t)
                logger.debug(
                    "DashboardController thread removed from registry: remaining=%d",
                    len(self._threads),
                )
            self.loading_finished.emit()

        thread.finished.connect(_cleanup_thread)

    def _fetch_all(self) -> DashboardData:
        logger.debug(
            "DashboardController._fetch_all: begin user_id=%s",
            getattr(self._user, "id", None),
        )

        time_played_total = 0
        try:
            time_played_total = get_time_played(self._user.id) or 0
            logger.debug(
                "DashboardController._fetch_all: total_time_played=%s",
                time_played_total,
            )
        except Exception:
            logger.exception("Failed to load total time played")

        try:
            all_stats = fetch_all_user_stats(self._user.id) or {"games": []}
            logger.debug(
                "DashboardController._fetch_all: all_stats loaded games_count=%d payload=%s",
                len(all_stats.get("games", [])),
                all_stats,
            )
        except Exception:
            logger.exception("Failed to load all user stats")
            all_stats = {"games": []}

        per_game: dict[str, dict | None] = {}
        histories: dict[str, list[dict]] = {}

        for slug in _GAME_SLUGS:
            try:
                per_game[slug] = fetch_player_game_stats(self._user.id, slug)
                logger.debug(
                    "DashboardController._fetch_all: per_game[%s]=%s",
                    slug,
                    per_game[slug],
                )
            except Exception:
                logger.exception("Failed to load per-game stats for %s", slug)
                per_game[slug] = None

            try:
                histories[slug] = fetch_user_run_history(self._user.id, slug, limit=20) or []
                logger.debug(
                    "DashboardController._fetch_all: histories[%s] count=%d sample=%s",
                    slug,
                    len(histories[slug]),
                    (histories[slug] or [None])[0],
                )
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
        logger.debug("DashboardController._on_data_loaded: result=%s", result)

        if not result:
            logger.debug("DashboardController._on_data_loaded: empty result")
            return

        self._data = result
        self.data_changed.emit()

    # -------------------------------------------------------------------------
    # Public models for View
    # -------------------------------------------------------------------------

    def get_welcome_model(self) -> dict[str, str]:
        streak = self._compute_current_streak()
        all_runs = self._get_all_runs_sorted_desc()
        total_games = len(all_runs)
        favorite_game_slug = self._get_most_played_slug()

        model = {
            "daily_streak": self._format_day_label(streak) if streak else "—",
            "total_games": str(total_games) if total_games else "—",
            "time_played": self._format_time(self._data.time_played_total),
            "favorite_game": self._label_for_slug(favorite_game_slug),
        }

        logger.debug("DashboardController.get_welcome_model: %s", model)
        return model

    def get_activity_model(self) -> dict[str, str]:
        history_runs = self._get_all_runs_sorted_desc()
        total_runs = len(history_runs)
        total_trials = sum((row.get("total_trials") or 0) for _, _, row in history_runs)
        streak = self._compute_current_streak()

        goal = self._estimate_daily_goal()
        done = len(self._get_today_runs())

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

        model = {
            "total_runs": str(total_runs) if total_runs else "—",
            "total_trials": str(total_trials) if total_trials else "—",
            "current_streak": self._format_day_label(streak) if streak else "—",
            "time_played": self._format_time(self._data.time_played_total),
            "goal_progress": f"{done} / {goal}",
            "goal_hint": goal_hint,
        }

        logger.debug("DashboardController.get_activity_model: %s", model)
        return model

    def get_recent_games_model(self) -> list[dict[str, str]]:
        runs = self._get_all_runs_sorted_desc()
        items: list[dict[str, str]] = []

        for dt, slug, row in runs[:3]:
            pi = row.get("pi_run")
            pi_text = f"{pi:.2f} PI" if isinstance(pi, (int, float)) else "—"
            items.append(
                {
                    "game": self._label_for_slug(slug),
                    "date": self._relative_datetime_text(dt),
                    "pi": pi_text,
                }
            )

        logger.debug("DashboardController.get_recent_games_model: %s", items)
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

        model = {
            "slug": most_played_slug,
            "values": values,
            "y_range": y_range,
        }

        logger.debug("DashboardController.get_trend_chart_model: %s", model)
        return model

    def get_highlights_model(self) -> dict[str, str]:
        fav_row = self._get_most_played_row()

        if not fav_row:
            model = {
                "best_accuracy": "—",
                "fastest_reaction": "—",
            }
            logger.debug("DashboardController.get_highlights_model: no favorite game data")
            return model

        model = {
            "best_accuracy": self._fmt_pct(fav_row.get("avg_accuracy_overall")),
            "fastest_reaction": self._fmt_ms(fav_row.get("avg_reaction_time_ms")),
        }

        logger.debug("DashboardController.get_highlights_model: %s", model)
        return model

    def get_continue_model(self) -> dict[str, Any]:
        runs = self._get_all_runs_sorted_desc()
        if not runs:
            model = {
                "slug": None,
                "game_name": "—",
                "info": "—",
                "enabled": False,
            }
            logger.debug("DashboardController.get_continue_model: no runs")
            return model

        dt, slug, _row = runs[0]
        model = {
            "slug": slug,
            "game_name": self._label_for_slug(slug),
            "info": self._relative_datetime_text(dt),
            "enabled": True,
        }

        logger.debug("DashboardController.get_continue_model: %s", model)
        return model

    # -------------------------------------------------------------------------
    # Internal logic
    # -------------------------------------------------------------------------

    def _get_today_runs(self) -> list[tuple[datetime | None, str, dict]]:
        today = datetime.now(timezone.utc).date()
        runs = [
            item
            for item in self._get_all_runs_sorted_desc()
            if item[0] and item[0].date() == today
        ]
        logger.debug(
            "DashboardController._get_today_runs: today=%s count=%d",
            today,
            len(runs),
        )
        return runs

    def _get_all_runs_sorted_desc(self) -> list[tuple[datetime | None, str, dict]]:
        runs: list[tuple[datetime | None, str, dict]] = []

        for slug, hist in self._data.histories.items():
            for row in hist or []:
                runs.append((self._parse_dt(row.get("started_at")), slug, row))

        runs.sort(key=lambda item: item[0] or _MIN_UTC, reverse=True)

        logger.debug(
            "DashboardController._get_all_runs_sorted_desc: total=%d per_slug=%s",
            len(runs),
            {slug: len(hist or []) for slug, hist in self._data.histories.items()},
        )
        return runs

    def _compute_current_streak(self) -> int:
        today = datetime.now(timezone.utc).date()
        days = {
            dt.date()
            for dt, _, _ in self._get_all_runs_sorted_desc()
            if dt is not None and dt.date() <= today
        }

        if not days:
            logger.debug("DashboardController._compute_current_streak: no days available")
            return 0

        cursor = today if today in days else today - timedelta(days=1)
        streak = 0

        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)

        logger.debug(
            "DashboardController._compute_current_streak: today=%s unique_days=%d streak=%d",
            today,
            len(days),
            streak,
        )
        return streak

    def _estimate_daily_goal(self) -> int:
        runs_by_day: dict[Any, int] = {}
        for dt, _, _ in self._get_all_runs_sorted_desc():
            if dt is None:
                continue
            day = dt.date()
            runs_by_day[day] = runs_by_day.get(day, 0) + 1

        if not runs_by_day:
            logger.debug("DashboardController._estimate_daily_goal: no runs_by_day, fallback=3")
            return 3

        avg = sum(runs_by_day.values()) / len(runs_by_day)
        goal = max(1, round(avg))

        logger.debug(
            "DashboardController._estimate_daily_goal: runs_by_day=%s avg=%.3f goal=%d",
            runs_by_day,
            avg,
            goal,
        )
        return goal

    def _get_most_played_row(self) -> dict | None:
        games = self._data.all_stats.get("games", []) or []
        row = max(
            (g for g in games if g.get("total_runs") is not None),
            key=lambda g: g.get("total_runs") or 0,
            default=None,
        )
        logger.debug("DashboardController._get_most_played_row: row=%s", row)
        return row

    def _get_most_played_slug(self) -> str | None:
        row = self._get_most_played_row()
        if not row:
            return None
        slug = self._game_slug_from_id(row.get("game_id"))
        logger.debug("DashboardController._get_most_played_slug: slug=%s", slug)
        return slug

    def _game_slug_from_id(self, game_id: Any) -> str | None:
        inverse = {value: key for key, value in GAME_ID_MAP.items()}
        slug = inverse.get(game_id)
        logger.debug(
            "DashboardController._game_slug_from_id: game_id=%s slug=%s",
            game_id,
            slug,
        )
        return slug

    def _safe_y_range(self, values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 1.0

        low = min(values)
        high = max(values)

        if abs(high - low) < 1e-9:
            padding = max(0.1, abs(low) * 0.1)
            result = (round(low - padding, 3), round(high + padding, 3))
            logger.debug(
                "DashboardController._safe_y_range: flat values=%s result=%s",
                values,
                result,
            )
            return result

        padding = (high - low) * 0.12
        result = (round(low - padding, 3), round(high + padding, 3))
        logger.debug(
            "DashboardController._safe_y_range: low=%s high=%s padding=%s result=%s",
            low,
            high,
            padding,
            result,
        )
        return result

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