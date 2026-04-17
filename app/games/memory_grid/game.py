from __future__ import annotations

import random
from enum import Enum, auto

from app.games.core.base_game import BaseGame, TrialResult
from app.games.memory_grid.config import LEVEL_PARAMS, MAX_LEVEL, MIN_LEVEL
from app.utils.logger import logger

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


class _MGPhase(Enum):
    WARMUP = auto()
    SMALL_GRID = auto()
    LARGER_GRID = auto()
    PASSED = auto()
    FAILED = auto()


class MemoryGridTutorialRunner:
    """
    3-phase tutorial (each trial takes 5-7 s, so phases are kept short):
      WARMUP       – 3×3 grid (level 1).  2 correct / max 5 trials.
      SMALL_GRID   – 3×3 grid (level 1).  2 consecutive correct / max 7 trials.
      LARGER_GRID  – 4×4 grid (level 2).  2 correct (total) / max 7 trials.
    """

    _WARMUP_REQUIRED_CORRECT = 2
    _WARMUP_MAX_TRIALS = 5
    _SMALL_REQUIRED_STREAK = 2
    _SMALL_MAX_TRIALS = 7
    _LARGER_REQUIRED_CORRECT = 2
    _LARGER_MAX_TRIALS = 7

    _LEVEL_SMALL  = 1
    _LEVEL_LARGER = 2

    def __init__(self, game: MemoryGridGame):
        self.game = game
        self._phase = _MGPhase.WARMUP
        self._phase_trials: list = []
        self._failed_reason: str = ""

    @property
    def passed(self) -> bool:
        return self._phase == _MGPhase.PASSED

    @property
    def failed(self) -> bool:
        return self._phase == _MGPhase.FAILED

    def configure(self):
        self.game.total_trials = 10**9
        self._phase = _MGPhase.WARMUP
        self._phase_trials = []
        self._failed_reason = ""
        self.game.level = self._LEVEL_SMALL
        self.game.initial_level = self._LEVEL_SMALL
        self.game.begin_run()

    def check_after_trial(self) -> bool:
        if self._phase in (_MGPhase.PASSED, _MGPhase.FAILED):
            return self.passed
        latest = self.game.trials[-1] if self.game.trials else None
        if not latest:
            return False
        self._phase_trials.append(latest)
        if self._phase == _MGPhase.WARMUP:
            return self._check_warmup()
        if self._phase == _MGPhase.SMALL_GRID:
            return self._check_small()
        if self._phase == _MGPhase.LARGER_GRID:
            return self._check_larger()
        return False

    def get_progress_text(self) -> str:
        pt = self._phase_trials
        if self._phase == _MGPhase.WARMUP:
            correct = sum(1 for t in pt if t.is_correct)
            return f"Warm-up: {correct}/{self._WARMUP_REQUIRED_CORRECT}"
        if self._phase == _MGPhase.SMALL_GRID:
            return f"3\u00d73 streak: {self._trailing_streak(pt)}/{self._SMALL_REQUIRED_STREAK}"
        if self._phase == _MGPhase.LARGER_GRID:
            correct = sum(1 for t in pt if t.is_correct)
            return f"4\u00d74: {correct}/{self._LARGER_REQUIRED_CORRECT}"
        if self._phase == _MGPhase.PASSED:
            return "\u2713 Tutorial passed!"
        if self._phase == _MGPhase.FAILED:
            return f"\u2717 Failed: {self._failed_reason}"
        return ""

    def get_progress_pct(self) -> int:
        if self._phase == _MGPhase.PASSED:
            return 100
        base_map = {
            _MGPhase.WARMUP:       0,
            _MGPhase.SMALL_GRID:  33,
            _MGPhase.LARGER_GRID: 66,
        }
        base = base_map.get(self._phase, 0)
        pt = self._phase_trials
        if self._phase == _MGPhase.WARMUP:
            within = min(sum(1 for t in pt if t.is_correct) / self._WARMUP_REQUIRED_CORRECT, 1.0)
        elif self._phase == _MGPhase.SMALL_GRID:
            within = min(self._trailing_streak(pt) / self._SMALL_REQUIRED_STREAK, 1.0)
        elif self._phase == _MGPhase.LARGER_GRID:
            within = min(sum(1 for t in pt if t.is_correct) / self._LARGER_REQUIRED_CORRECT, 1.0)
        else:
            within = 0.0
        return int(base + within * 33)

    def _check_warmup(self) -> bool:
        pt = self._phase_trials
        correct = sum(1 for t in pt if t.is_correct)
        if correct >= self._WARMUP_REQUIRED_CORRECT:
            self._enter_phase(_MGPhase.SMALL_GRID, self._LEVEL_SMALL)
        elif len(pt) >= self._WARMUP_MAX_TRIALS:
            self._fail(f"only {correct}/{len(pt)} correct in warm-up")
        return False

    def _check_small(self) -> bool:
        pt = self._phase_trials
        streak = self._trailing_streak(pt)
        if streak >= self._SMALL_REQUIRED_STREAK:
            self._enter_phase(_MGPhase.LARGER_GRID, self._LEVEL_LARGER)
        elif len(pt) >= self._SMALL_MAX_TRIALS:
            self._fail(f"no {self._SMALL_REQUIRED_STREAK}-streak in {self._SMALL_MAX_TRIALS} trials")
        return False

    def _check_larger(self) -> bool:
        pt = self._phase_trials
        correct = sum(1 for t in pt if t.is_correct)
        if correct >= self._LARGER_REQUIRED_CORRECT:
            self._phase = _MGPhase.PASSED
            self._phase_trials = []
            return True
        if len(pt) >= self._LARGER_MAX_TRIALS:
            self._fail(f"only {correct}/{len(pt)} correct on 4\u00d74")
        return False

    def _enter_phase(self, phase: _MGPhase, level: int) -> None:
        self._phase = phase
        self._phase_trials = []
        self.game.level = level
        self.game.initial_level = level

    def _fail(self, reason: str) -> None:
        self._failed_reason = reason
        self._phase = _MGPhase.FAILED
        self._phase_trials = []

    @staticmethod
    def _trailing_streak(trials) -> int:
        streak = 0
        for t in reversed(trials):
            if t.is_correct:
                streak += 1
            else:
                break
        return streak
