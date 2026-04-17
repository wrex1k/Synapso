from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QThread, Signal

from app.core.registry import registry
from app.repository.game_repository import fetch_games
from app.repository.stats_repository import fetch_game_stats, fetch_leaderboard
from app.repository.user_repository import fetch_avatar


@dataclass
class GamesData:
    """Container for games data used by the games controller."""
    games: list[dict] = field(default_factory=list)
    stats: dict[int, dict] = field(default_factory=dict)
    leaderboards: dict[int, dict] = field(default_factory=dict)
    avatars: dict[str, bytes] = field(default_factory=dict)


class GamesController(QObject):
    """Controller responsible for loading games catalog, stats, and leaderboards."""
    games_loaded = Signal()
    stats_loaded = Signal(int)
    leaderboard_loaded = Signal(int)
    avatar_loaded = Signal(str)

    def __init__(self, user_id: str, parent: QObject | None = None):
        super().__init__(parent)
        self._user_id = user_id
        self._threads: list[QThread] = []
        self._games_loaded = False

        self._data = GamesData()

        self._loading_stats: set[int] = set()
        self._loading_lbs: set[int] = set()

    def load_games(self) -> None:
        """Load the list of active games from the database."""
        if self._games_loaded:
            return

        thread = registry.run_thread(
            fetch_games,
            self._on_games_loaded,
            name="games-fetch",
        )
        self._keep_thread(thread)

    def load_stats(self, game_db_id: int) -> None:
        """Load stats for a specific game."""
        if game_db_id in self._data.stats or game_db_id in self._loading_stats:
            return
        
        self._loading_stats.add(game_db_id)
        thread = registry.run_thread(
            lambda: fetch_game_stats(game_db_id, self._user_id),
            lambda result: self._on_stats_loaded(game_db_id, result),
            name=f"stats-fetch-{game_db_id}",
        )
        self._keep_thread(thread)

    def load_all_stats(self, game_db_ids: list[int]) -> None:
        """Load stats for all games in parallel."""
        for gid in game_db_ids:
            self.load_stats(gid)

    def load_leaderboard(self, game_db_id: int) -> None:
        """Load leaderboard for a specific game."""
        if game_db_id in self._data.leaderboards:
            return
        if game_db_id in self._loading_lbs:
            return
        self._loading_lbs.add(game_db_id)
        thread = registry.run_thread(
            lambda: fetch_leaderboard(game_db_id, self._user_id),
            lambda result: self._on_leaderboard_loaded(game_db_id, result),
            name=f"leaderboard-fetch-{game_db_id}",
        )
        self._keep_thread(thread)

    def preload_avatars(self, avatar_paths: list[str]) -> None:
        """Preload multiple avatars in parallel."""
        for path in avatar_paths:
            if path and path != "default.webp" and path not in self._data.avatars:
                thread = registry.run_thread(
                    lambda p=path: fetch_avatar(p),
                    lambda result, p=path: self._on_avatar_loaded(p, result),
                    name=f"avatar-fetch-{path}",
                )
                self._keep_thread(thread)

    def invalidate_leaderboard(self, game_db_id: int) -> None:
        """Invalidate cached leaderboard to force refresh."""
        if game_db_id in self._data.leaderboards:
            del self._data.leaderboards[game_db_id]

    def invalidate_stats(self, game_db_id: int) -> None:
        """Invalidate cached stats to force refresh."""
        if game_db_id in self._data.stats:
            del self._data.stats[game_db_id]

    def _keep_thread(self, thread: QThread) -> None:
        """Track a running thread."""
        self._threads.append(thread)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)

    def _on_games_loaded(self, result: list[dict] | None) -> None:
        """Store loaded games and notify the UI."""
        if not result:
            return

        self._games_loaded = True
        self._data.games = result
        self.games_loaded.emit()

    def _on_stats_loaded(self, game_db_id: int, result: dict | None) -> None:
        """Store loaded stats and notify the UI."""
        self._loading_stats.discard(game_db_id)
        if not result:
            return

        self._data.stats[game_db_id] = result
        self.stats_loaded.emit(game_db_id)

    def _on_leaderboard_loaded(self, game_db_id: int, result: dict | None) -> None:
        """Store loaded leaderboard and notify the UI."""
        self._loading_lbs.discard(game_db_id)
        if not result:
            return

        self._data.leaderboards[game_db_id] = result
        self.leaderboard_loaded.emit(game_db_id)

    def _on_avatar_loaded(self, avatar_path: str, result: bytes | None) -> None:
        """Store loaded avatar and notify the UI."""
        if not result:
            return

        self._data.avatars[avatar_path] = result
        self.avatar_loaded.emit(avatar_path)

    def cleanup(self):
        """Stop any running threads."""
        for thread in self._threads:
            if thread.isRunning():
                thread.quit()
                thread.wait()
