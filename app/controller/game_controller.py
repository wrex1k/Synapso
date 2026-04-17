"""GameController manages the full lifecycle of a single game (tutorial + play runs).
Signals let the UI react without any direct coupling to game/renderer internals.
Each start_tutorial / start_play call spawns a short-lived QThread so the
Pygame window never blocks the PySide6 event loop.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.core.registry import registry

from app.games.stroop.game import StroopGame
from app.games.stroop.renderer import StroopRenderer
from app.games.memory_grid.game import MemoryGridGame
from app.games.memory_grid.renderer import MemoryGridRenderer
from app.games.mental_rotation.game import MentalRotationGame
from app.games.mental_rotation.renderer import MentalRotationRenderer
from app.service.game_service import GameService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Maps game_id strings to factory callables that create fresh game instances.
_GAME_FACTORIES = {
    "stroop": lambda user_id: StroopGame(user_id),
    "memory_grid": lambda user_id: MemoryGridGame(user_id),
    "mental_rotation": lambda user_id: MentalRotationGame(user_id),
}

# Maps game_id to its pygame renderer class.
_RENDERER_FACTORIES = {
    "stroop": StroopRenderer,
    "memory_grid": MemoryGridRenderer,
    "mental_rotation": MentalRotationRenderer,
}


class GameController(QObject):
    game_started = Signal()
    game_ended = Signal()

    tutorial_passed = Signal()
    tutorial_abandoned = Signal()

    run_finished = Signal(dict)
    run_abandoned = Signal()

    def __init__(self, user_id: str, game_id: str, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._game_id = game_id
        self._operation = registry.operation(f"game_{game_id}")

    def _make_service(self) -> tuple[StroopGame, GameService]:
        factory = _GAME_FACTORIES.get(self._game_id)
        if factory is None:
            raise ValueError(f"Unknown game_id: {self._game_id!r}")
        game = factory(self._user_id)
        return game, GameService(game)

    def is_tutorial_completed(self) -> bool:
        _, service = self._make_service()
        return service.is_tutorial_completed()

    def is_running(self) -> bool:
        return self._operation.is_running()

    def start_tutorial(self):
        if self._operation.is_running():
            logger.warning("Game already running for %s", self._game_id)
            return

        logger.info("User started tutorial for: %s", self._game_id)
        game, service = self._make_service()
        self.game_started.emit()

        self._operation.start(
            registry.run_thread,
            lambda: self._run_tutorial(game, service),
            self._on_tutorial_result,
            name=f"tutorial-{self._game_id}",
        )

    def _run_tutorial(self, game, service) -> bool:
        try:
            runner = service.create_tutorial_runner()
            runner.configure()
            renderer_cls = _RENDERER_FACTORIES[self._game_id]
            renderer = renderer_cls(game)
            passed = renderer.run_tutorial_trials(runner)
            
            if passed:
                service.start_run(stage="tutorial")
                service.complete_tutorial(runner)
                logger.info("Tutorial passed and saved for game: %s", self._game_id)
            else:
                logger.info("Tutorial abandoned for game: %s", self._game_id)
            return passed
        except Exception:
            service.abort_run()
            logger.exception("Tutorial error for %s", self._game_id)
            return False

    @Slot(object)
    def _on_tutorial_result(self, passed: bool):
        self.game_ended.emit()
        if passed:
            self.tutorial_passed.emit()
            logger.info("Tutorial passed for game %s", self._game_id)
        else:
            self.tutorial_abandoned.emit()
            logger.info("Tutorial not passed / abandoned for game %s", self._game_id)

    def start_play(self):
        if self._operation.is_running():
            logger.warning("Game already running for %s", self._game_id)
            return

        logger.info("User started game: %s", self._game_id)
        game, service = self._make_service()
        self.game_started.emit()

        self._operation.start(
            registry.run_thread,
            lambda: self._run_play(game, service),
            self._on_play_result,
            name=f"play-{self._game_id}",
        )

    def _run_play(self, game, service) -> dict:
        try:
            service.start_run()
            renderer_cls = _RENDERER_FACTORIES[self._game_id]
            renderer = renderer_cls(game)
            completed = renderer.run_all_trials()
            if not completed:
                service.abort_run()
                return {}
            return service.finish_run(stage="training")
        except Exception:
            service.abort_run()
            logger.exception("Play error for %s", self._game_id)
            return {}

    @Slot(object)
    def _on_play_result(self, metrics: dict):
        self.game_ended.emit()
        if metrics:
            self.run_finished.emit(metrics)
            logger.info("Run finished for game %s metrics=%s", self._game_id, metrics)
        else:
            self.run_abandoned.emit()
            logger.info("Run abandoned / empty for game %s", self._game_id)
