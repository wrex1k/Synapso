from __future__ import annotations

import random

from app.games.core.base_game import BaseGame, TrialResult
from app.games.memory_grid.config import LEVEL_PARAMS, MAX_LEVEL, MIN_LEVEL
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryGridGame(BaseGame):
    """Spatial working-memory game based on reproducing highlighted cells."""

    def __init__(self, user_id: str):
        super().__init__(
            game_slug="memory_grid",
            user_id=user_id,
            min_level=MIN_LEVEL,
            max_level=MAX_LEVEL,
        )

    def _level_params(self) -> dict[str, int]:
        return LEVEL_PARAMS.get(self.level, LEVEL_PARAMS[MIN_LEVEL])

    def create_tutorial_runner(self) -> "MemoryGridTutorialRunner":
        return MemoryGridTutorialRunner(self)

    @staticmethod
    def _serialize_positions(positions: set[int] | list[int]) -> str:
        return ",".join(str(p) for p in sorted(positions))

    @staticmethod
    def _deserialize_positions(raw: str | None) -> set[int]:
        if not raw:
            return set()
        parsed: set[int] = set()
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                parsed.add(int(part))
            except ValueError:
                logger.debug("Ignoring malformed cell token: %r", part)
        return parsed

    def start_trial(self) -> dict:
        p = self._level_params()
        grid_size = p["grid_size"]
        target_count = random.randint(p["pattern_min"], p["pattern_max"])
        max_cells = grid_size * grid_size

        pattern_positions = sorted(random.sample(range(max_cells), target_count))

        return {
            "grid_size": grid_size,
            "pattern_positions": pattern_positions,
            "target_count": target_count,
            "stimulus_duration": p["display_ms"],
            "response_duration": p["response_ms"],
            "level": self.level,
            "trial_index": self.current_trial_index,
            "total_trials": self.total_trials,
        }

    def get_correct_answer(self, trial_params: dict) -> str:
        return self._serialize_positions(trial_params.get("pattern_positions", []))

    def evaluate_trial(
        self,
        trial_params: dict,
        response: str | None,
        reaction_time_ms: float,
    ) -> TrialResult:
        correct_set = set(trial_params.get("pattern_positions", []))
        selected_set = self._deserialize_positions(response)

        hits = len(correct_set & selected_set)
        misses = len(correct_set - selected_set)
        false_positives = len(selected_set - correct_set)
        error_count = misses + false_positives

        target_count = max(1, len(correct_set))
        accuracy_ratio = hits / target_count
        is_correct = error_count == 0 and len(selected_set) == len(correct_set)

        enriched_params = {
            **trial_params,
            "hits": hits,
            "misses": misses,
            "false_positives": false_positives,
            "error_count": error_count,
            "accuracy_ratio": accuracy_ratio,
        }

        result = TrialResult(
            stimulus_params=enriched_params,
            response=response,
            reaction_time_ms=reaction_time_ms,
            is_correct=is_correct,
            stimulus_payload={
                "level": trial_params.get("level"),
                "grid_size": trial_params.get("grid_size"),
                "pattern_positions": trial_params.get("pattern_positions", []),
            },
            response_payload={
                "selected_positions": sorted(selected_set),
                "reaction_time_ms": reaction_time_ms,
            },
            scoring_payload={
                "is_correct": is_correct,
                "hits": hits,
                "misses": misses,
                "false_positives": false_positives,
                "error_count": error_count,
                "target_count": target_count,
                "selection_count": len(selected_set),
                "accuracy_ratio": accuracy_ratio,
            },
        )

        self.trials.append(result)
        self.current_trial_index += 1
        self._adjust_level()
        return result

    def _adjust_level(self) -> None:
        window = 5
        if len(self.trials) < window:
            return

        recent = self.trials[-window:]
        error_ratios: list[float] = []
        for t in recent:
            target_count = max(1, int(t.stimulus_params.get("target_count", 1)))
            error_count = int(t.stimulus_params.get("error_count", 0))
            error_ratios.append(error_count / target_count)

        avg_error_ratio = sum(error_ratios) / len(error_ratios)

        if avg_error_ratio <= 0.20 and self.level < self.max_level:
            self.level += 1
        elif avg_error_ratio >= 0.45 and self.level > self.min_level:
            self.level -= 1


class MemoryGridTutorialRunner:
    """Tutorial progression by grid sizes 3x3 -> 4x4 -> 5x5."""

    def __init__(self, game: MemoryGridGame):
        self.game = game
        self._passed = False
        self._tutorial_levels = [1, 2, 3]
        self._index = 0

    @property
    def passed(self) -> bool:
        return self._passed

    def configure(self):
        self.game.total_trials = 10**9
        self._index = 0
        self._passed = False
        self.game.level = self._tutorial_levels[self._index]
        self.game.initial_level = self.game.level
        self.game.begin_run()

    def check_after_trial(self) -> bool:
        if not self.game.trials:
            return False

        self._index += 1
        if self._index >= len(self._tutorial_levels):
            self._passed = True
            return True

        next_level = self._tutorial_levels[self._index]
        self.game.level = next_level
        self.game.initial_level = next_level
        return False

    def get_progress_text(self) -> str:
        current = min(self._index + 1, len(self._tutorial_levels))
        total = len(self._tutorial_levels)
        return f"Grid {current}/{total}"

    def get_progress_pct(self) -> int:
        total = len(self._tutorial_levels)
        if total == 0:
            return 0
        return int(min(self._index, total) / total * 100)
