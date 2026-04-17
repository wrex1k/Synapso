from __future__ import annotations

import random
from enum import Enum, auto

from app.games.core.base_game import BaseGame, TrialResult
from app.games.mental_rotation.config import LEVEL_PARAMS, MAX_LEVEL, MIN_LEVEL, SHAPES


class MentalRotationGame(BaseGame):
    def __init__(self, user_id: str):
        super().__init__(
            game_slug="mental_rotation",
            user_id=user_id,
            min_level=MIN_LEVEL,
            max_level=MAX_LEVEL,
        )
        self._last_shape_id: str | None = None
        self._last_mirrored_history: list[bool] = []

    def _level_params(self) -> dict:
        return LEVEL_PARAMS.get(self.level, LEVEL_PARAMS[MIN_LEVEL])

    def begin_run(self) -> None:
        super().begin_run()
        self._last_shape_id = None
        self._last_mirrored_history = []

    def create_tutorial_runner(self) -> "MentalRotationTutorialRunner":
        return MentalRotationTutorialRunner(self)

    def start_trial(self) -> dict:
        level_params = self._level_params()

        shape_ids = level_params["shape_ids"]
        candidates = [s for s in shape_ids if s != self._last_shape_id]
        if not candidates:
            candidates = shape_ids
        shape_id = random.choice(candidates)
        self._last_shape_id = shape_id

        rotation_angle = random.randint(int(level_params["angle_min"]), int(level_params["angle_max"]))

        mirror_prob = float(level_params["mirror_prob"])
        if len(self._last_mirrored_history) >= 3 and len(set(self._last_mirrored_history[-3:])) == 1:
            forced = not self._last_mirrored_history[-1]
            mirrored = forced
        else:
            mirrored = random.random() < mirror_prob
        self._last_mirrored_history.append(mirrored)
        if len(self._last_mirrored_history) > 6:
            self._last_mirrored_history.pop(0)

        correct_key = "f" if mirrored else "k"

        return {
            "shape_id": shape_id,
            "shape_blocks": SHAPES[shape_id],
            "rotation_angle": rotation_angle,
            "mirrored": mirrored,
            "correct_key": correct_key,
            "stimulus_duration": int(level_params["display_ms"]),
            "level": self.level,
            "trial_index": self.current_trial_index,
            "total_trials": self.total_trials,
            "available_keys": ["k", "f"],
        }

    def get_correct_answer(self, trial_params: dict) -> str:
        return str(trial_params.get("correct_key", "f")).lower()

    def evaluate_trial(
        self,
        trial_params: dict,
        response: str | None,
        reaction_time_ms: float,
    ) -> TrialResult:
        response_key = response.lower() if isinstance(response, str) else None
        correct_key = self.get_correct_answer(trial_params)
        is_correct = response_key == correct_key

        shape_id = str(trial_params.get("shape_id"))
        rotation_angle = int(trial_params.get("rotation_angle", 0))
        mirrored = bool(trial_params.get("mirrored", False))

        result = TrialResult(
            stimulus_params=trial_params,
            response=response_key,
            reaction_time_ms=reaction_time_ms,
            is_correct=is_correct,
            stimulus_payload={
                "shape_id": shape_id,
                "rotation_angle": rotation_angle,
                "mirrored": mirrored,
                "level": trial_params.get("level"),
            },
            response_payload={
                "response_key": response_key,
                "reaction_time_ms": reaction_time_ms,
            },
            scoring_payload={
                "is_correct": is_correct,
                "shape_id": shape_id,
                "rotation_angle": rotation_angle,
                "mirrored": mirrored,
                "correct_key": correct_key,
                "response_key": response_key,
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
        performance = sum(1 for t in recent if t.is_correct) / window

        if performance >= 0.8 and self.level < self.max_level:
            self.level += 1
        elif performance <= 0.5 and self.level > self.min_level:
            self.level -= 1


class _MRPhase(Enum):
    WARMUP = auto()
    ROTATION_CHECK = auto()
    MIRROR_TEST = auto()
    SPEED_CHECK = auto()
    PASSED = auto()
    FAILED = auto()


class MentalRotationTutorialRunner:
    _WARMUP_REQUIRED_CORRECT = 3
    _WARMUP_MAX_TRIALS = 8
    _ROTATION_REQUIRED_STREAK = 3
    _ROTATION_MAX_TRIALS = 10
    _MIRROR_MIN_TRIALS = 6
    _MIRROR_REQUIRED_ACCURACY = 0.70
    _MIRROR_MAX_TRIALS = 14
    _SPEED_REQUIRED_STREAK = 3
    _SPEED_MAX_RT_RATIO = 0.70   # respond within 70% of stimulus window
    _SPEED_MAX_TRIALS = 10

    _LEVEL_WARMUP    = 1   # 0%  mirror, 15-45°,   2000 ms
    _LEVEL_ROTATION  = 2   # 20% mirror, 45-75°,   1800 ms
    _LEVEL_MIRROR    = 4   # 40% mirror, 105-135°, 1400 ms
    _LEVEL_SPEED     = 3   # 30% mirror, 75-105°,  1600 ms

    def __init__(self, game: MentalRotationGame):
        self.game = game
        self._phase = _MRPhase.WARMUP
        self._phase_trials: list = []
        self._failed_reason: str = ""

    @property
    def passed(self) -> bool:
        return self._phase == _MRPhase.PASSED

    @property
    def failed(self) -> bool:
        return self._phase == _MRPhase.FAILED

    def configure(self):
        self.game.total_trials = 10**9
        self._phase = _MRPhase.WARMUP
        self._phase_trials = []
        self._failed_reason = ""
        self.game.level = self._LEVEL_WARMUP
        self.game.initial_level = self._LEVEL_WARMUP
        self.game.begin_run()

    def check_after_trial(self) -> bool:
        if self._phase in (_MRPhase.PASSED, _MRPhase.FAILED):
            return self.passed
        latest = self.game.trials[-1] if self.game.trials else None
        if not latest:
            return False
        self._phase_trials.append(latest)
        if self._phase == _MRPhase.WARMUP:
            return self._check_warmup()
        if self._phase == _MRPhase.ROTATION_CHECK:
            return self._check_rotation()
        if self._phase == _MRPhase.MIRROR_TEST:
            return self._check_mirror()
        if self._phase == _MRPhase.SPEED_CHECK:
            return self._check_speed()
        return False

    def get_progress_text(self) -> str:
        pt = self._phase_trials
        if self._phase == _MRPhase.WARMUP:
            correct = sum(1 for t in pt if t.is_correct)
            return f"Warm-up: {correct}/{self._WARMUP_REQUIRED_CORRECT}"
        if self._phase == _MRPhase.ROTATION_CHECK:
            return f"Rotation streak: {self._trailing_streak(pt)}/{self._ROTATION_REQUIRED_STREAK}"
        if self._phase == _MRPhase.MIRROR_TEST:
            n = len(pt)
            correct = sum(1 for t in pt if t.is_correct)
            pct = int(100 * correct / n) if n else 0
            return f"Mirror: {pct}% ({n}/{self._MIRROR_MIN_TRIALS} trials)"
        if self._phase == _MRPhase.SPEED_CHECK:
            return f"Speed streak: {self._fast_correct_streak(pt)}/{self._SPEED_REQUIRED_STREAK}"
        if self._phase == _MRPhase.PASSED:
            return "\u2713 Tutorial passed!"
        if self._phase == _MRPhase.FAILED:
            return f"\u2717 Failed: {self._failed_reason}"
        return ""

    def get_progress_pct(self) -> int:
        if self._phase == _MRPhase.PASSED:
            return 100
        base_map = {
            _MRPhase.WARMUP:         0,
            _MRPhase.ROTATION_CHECK: 25,
            _MRPhase.MIRROR_TEST:    50,
            _MRPhase.SPEED_CHECK:    75,
        }
        base = base_map.get(self._phase, 0)
        pt = self._phase_trials
        if self._phase == _MRPhase.WARMUP:
            within = min(sum(1 for t in pt if t.is_correct) / self._WARMUP_REQUIRED_CORRECT, 1.0)
        elif self._phase == _MRPhase.ROTATION_CHECK:
            within = min(self._trailing_streak(pt) / self._ROTATION_REQUIRED_STREAK, 1.0)
        elif self._phase == _MRPhase.MIRROR_TEST:
            within = min(len(pt) / self._MIRROR_MIN_TRIALS, 1.0)
        elif self._phase == _MRPhase.SPEED_CHECK:
            within = min(self._fast_correct_streak(pt) / self._SPEED_REQUIRED_STREAK, 1.0)
        else:
            within = 0.0
        return int(base + within * 25)

    def _check_warmup(self) -> bool:
        pt = self._phase_trials
        correct = sum(1 for t in pt if t.is_correct)
        if correct >= self._WARMUP_REQUIRED_CORRECT:
            self._enter_phase(_MRPhase.ROTATION_CHECK, self._LEVEL_ROTATION)
        elif len(pt) >= self._WARMUP_MAX_TRIALS:
            self._fail(f"only {correct}/{len(pt)} correct in warm-up")
        return False

    def _check_rotation(self) -> bool:
        pt = self._phase_trials
        streak = self._trailing_streak(pt)
        if streak >= self._ROTATION_REQUIRED_STREAK:
            self._enter_phase(_MRPhase.MIRROR_TEST, self._LEVEL_MIRROR)
        elif len(pt) >= self._ROTATION_MAX_TRIALS:
            self._fail(f"no {self._ROTATION_REQUIRED_STREAK}-streak in {self._ROTATION_MAX_TRIALS} trials")
        return False

    def _check_mirror(self) -> bool:
        pt = self._phase_trials
        n = len(pt)
        if n < self._MIRROR_MIN_TRIALS:
            return False
        correct = sum(1 for t in pt if t.is_correct)
        accuracy = correct / n
        if accuracy >= self._MIRROR_REQUIRED_ACCURACY:
            self._enter_phase(_MRPhase.SPEED_CHECK, self._LEVEL_SPEED)
        elif n >= self._MIRROR_MAX_TRIALS:
            self._fail(f"mirror accuracy {int(accuracy * 100)}% after {n} trials")
        return False

    def _check_speed(self) -> bool:
        pt = self._phase_trials
        streak = self._fast_correct_streak(pt)
        if streak >= self._SPEED_REQUIRED_STREAK:
            self._phase = _MRPhase.PASSED
            self._phase_trials = []
            return True
        if len(pt) >= self._SPEED_MAX_TRIALS:
            self._fail(f"no fast streak of {self._SPEED_REQUIRED_STREAK} in {self._SPEED_MAX_TRIALS} trials")
        return False

    def _enter_phase(self, phase: _MRPhase, level: int) -> None:
        self._phase = phase
        self._phase_trials = []
        self.game.level = level
        self.game.initial_level = level

    def _fail(self, reason: str) -> None:
        self._failed_reason = reason
        self._phase = _MRPhase.FAILED
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

    def _fast_correct_streak(self, trials) -> int:
        streak = 0
        for t in reversed(trials):
            if not t.is_correct:
                break
            stim_ms = t.stimulus_params.get("stimulus_duration", 0)
            if stim_ms > 0 and t.reaction_time_ms > stim_ms * self._SPEED_MAX_RT_RATIO:
                break
            streak += 1
        return streak
