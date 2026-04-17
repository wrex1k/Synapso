from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QObject, Signal

from app.core.registry import registry
from app.games.core.base_game import GAME_SLUGS
from app.service.stats_service import get_dashboard_stats

@dataclass
class StatisticsData:
    """Container for statistics data used by the statistics controller."""
    time_played_total: int = 0
    all_stats: dict[str, Any] = field(default_factory=lambda: {"games": []})
    per_game: dict[str, dict | None] = field(default_factory=dict)
    histories: dict[str, list[dict]] = field(default_factory=dict)


class StatisticsController(QObject):
    """Controller responsible for loading and managing statistics data."""
    data_changed = Signal()

    def __init__(self, user_id: str, parent: QObject | None = None):
        super().__init__(parent)
        self._user_id = user_id
        self._data = StatisticsData()
        self._fetch_op = registry.operation("statistics-controller-fetch")

    def is_loading(self) -> bool:
        """Return whether any loading thread is currently running."""
        return self._fetch_op.is_running()

    def load(self) -> None:
        """Start asynchronous loading of statistics data if no load is currently running."""
        if self.is_loading():
            return

        self._fetch_op.start(
            registry.run_thread,
            self._fetch_all,
            self._on_data_loaded,
            name="statistics-fetch",
        )

    def _fetch_all(self) -> StatisticsData:
        """Fetch all statistics data from the service layer."""
        data = get_dashboard_stats(self._user_id, GAME_SLUGS, history_limit=20)
        return StatisticsData(
            time_played_total=data["time_played_total"],
            all_stats=data["all_stats"],
            per_game=data["per_game"],
            histories=data["histories"],
        )

    def _on_data_loaded(self, result: StatisticsData | None) -> None:
        """Store loaded statistics data and notify the UI when loading succeeds."""
        if not result:
            return

        self._data = result
        self.data_changed.emit()

    def cleanup(self):
        """Cancel any running operations."""
        self._fetch_op.cancel()
