from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from app.games.core.base_game import BaseGame

class TutorialPhase(Enum):
    WARMUP = auto()
    CONGRUENT_CHECK = auto()
    INCONGRUENT_TEST = auto()
    SPEED_CHECK = auto()
    PASSED = auto()
    FAILED = auto()

@dataclass
class PhaseResult:
    phase: TutorialPhase
    trials_in_phase: int
    correct_in_phase: int
    passed: bool
    note: str = ""

@dataclass(frozen=True)
class PhaseRequirements:
    warmup_required_correct: int = 3
    warmup_max_trials: int = 8
    congruent_required_streak: int = 3
    congruent_max_trials: int = 10
    incongruent_min_trials: int = 6
    incongruent_required_accuracy: float = 0.7
    incongruent_max_trials: int = 14
    speed_required_streak: int = 3
    speed_max_rt_ratio: float = 0.7
    speed_max_trials: int = 10

class TutorialRunner:
    def __init__(self, game: BaseGame, requirements: PhaseRequirements | None = None):
        self.game = game
        self.req = requirements or PhaseRequirements()
        self.phase: TutorialPhase = TutorialPhase.WARMUP
        self.phase_results: list[PhaseResult] = []
        self._phase_trials: list = []
        self._failed_reason: str = ""

    @property
    def passed(self) -> bool:
        return self.phase == TutorialPhase.PASSED

    @property
    def failed(self) -> bool:
        return self.phase == TutorialPhase.FAILED

    def configure(self) -> None:
        self.game.total_trials = 50
        self.game.level = self.game.min_level
        self.game.initial_level = self.game.min_level
        self.game.begin_run()
        self._enter_phase(TutorialPhase.WARMUP)

    def next_trial_override(self) -> dict | None:
        if self.phase == TutorialPhase.INCONGRUENT_TEST:
            return self._force_incongruent_stimulus()
        return None

    def check_after_trial(self) -> bool:
        if self.phase in (TutorialPhase.PASSED, TutorialPhase.FAILED):
            return self.passed
        latest = self.game.trials[-1] if self.game.trials else None
        if not latest:
            return False
        self._phase_trials.append(latest)
        if self.phase == TutorialPhase.WARMUP:
            return self._check_warmup()
        if self.phase == TutorialPhase.CONGRUENT_CHECK:
            return self._check_congruent()
        if self.phase == TutorialPhase.INCONGRUENT_TEST:
            return self._check_incongruent()
        if self.phase == TutorialPhase.SPEED_CHECK:
            return self._check_speed()
        return False

    def get_progress_text(self) -> str:
        pt = self._phase_trials
        if self.phase == TutorialPhase.WARMUP:
            correct = sum(1 for t in pt if t.is_correct)
            return f"Warm-up: {correct}/{self.req.warmup_required_correct}"
        if self.phase == TutorialPhase.CONGRUENT_CHECK:
            return f"Congruent streak: {self._trailing_streak(pt)}/{self.req.congruent_required_streak}"
        if self.phase == TutorialPhase.INCONGRUENT_TEST:
            window = pt[-self.req.incongruent_min_trials:]
            correct = sum(1 for t in window if t.is_correct)
            pct = int(100 * correct / len(window)) if window else 0
            return f"Incongruent: {pct}% over {len(window)} trials"
        if self.phase == TutorialPhase.SPEED_CHECK:
            return f"Speed streak: {self._fast_correct_streak(pt)}/{self.req.speed_required_streak}"
        if self.phase == TutorialPhase.PASSED:
            return "✓ Tutorial passed!"
        if self.phase == TutorialPhase.FAILED:
            return f"✗ Failed: {self._failed_reason}"
        return ""

    def get_progress_pct(self) -> int:
        if self.phase == TutorialPhase.PASSED:
            return 100
        base_map = {
            TutorialPhase.WARMUP: 0,
            TutorialPhase.CONGRUENT_CHECK: 25,
            TutorialPhase.INCONGRUENT_TEST: 50,
            TutorialPhase.SPEED_CHECK: 75,
        }
        base = base_map.get(self.phase, 0)
        pt = self._phase_trials
        if self.phase == TutorialPhase.WARMUP:
            within = min(sum(1 for t in pt if t.is_correct) / self.req.warmup_required_correct, 1.0)
        elif self.phase == TutorialPhase.CONGRUENT_CHECK:
            within = min(self._trailing_streak(pt) / self.req.congruent_required_streak, 1.0)
        elif self.phase == TutorialPhase.INCONGRUENT_TEST:
            within = min(len(pt) / self.req.incongruent_min_trials, 1.0)
        elif self.phase == TutorialPhase.SPEED_CHECK:
            within = min(self._fast_correct_streak(pt) / self.req.speed_required_streak, 1.0)
        else:
            within = 0.0
        return int(base + within * 25)

    def get_phase_summary(self) -> list[dict]:
        return [
            {
                "phase": r.phase.name,
                "trials": r.trials_in_phase,
                "correct": r.correct_in_phase,
                "passed": r.passed,
                "note": r.note,
            }
            for r in self.phase_results
        ]

    def _check_warmup(self) -> bool:
        pt = self._phase_trials
        correct = sum(1 for t in pt if t.is_correct)
        if correct >= self.req.warmup_required_correct:
            self._complete_phase(True, f"{correct} correct")
            self._enter_phase(TutorialPhase.CONGRUENT_CHECK)
        elif len(pt) >= self.req.warmup_max_trials:
            self._fail(f"{correct}/{len(pt)} correct")
        return False

    def _check_congruent(self) -> bool:
        pt = self._phase_trials
        streak = self._trailing_streak(pt)
        if streak >= self.req.congruent_required_streak:
            self._complete_phase(True, f"streak {streak}")
            self._enter_phase(TutorialPhase.INCONGRUENT_TEST)
        elif len(pt) >= self.req.congruent_max_trials:
            self._fail(f"No streak {self.req.congruent_required_streak} in {self.req.congruent_max_trials}")
        return False

    def _check_incongruent(self) -> bool:
        pt = self._phase_trials
        n = len(pt)
        if n < self.req.incongruent_min_trials:
            return False
        correct = sum(1 for t in pt if t.is_correct)
        accuracy = correct / n
        if accuracy >= self.req.incongruent_required_accuracy:
            self._complete_phase(True, f"{correct}/{n} ({int(accuracy*100)}%)")
            self._enter_phase(TutorialPhase.SPEED_CHECK)
        elif n >= self.req.incongruent_max_trials:
            self._fail(f"Incongruent accuracy too low: {correct}/{n} ({int(accuracy*100)}%)")
        return False

    def _check_speed(self) -> bool:
        pt = self._phase_trials
        streak = self._fast_correct_streak(pt)
        if streak >= self.req.speed_required_streak:
            self._complete_phase(True, f"streak {streak}")
            self._enter_phase(TutorialPhase.PASSED)
            return True
        if len(pt) >= self.req.speed_max_trials:
            self._fail(f"No fast streak {self.req.speed_required_streak} in {self.req.speed_max_trials}")
        return False

    def _enter_phase(self, phase: TutorialPhase) -> None:
        self.phase = phase
        self._phase_trials = []

    def _complete_phase(self, passed: bool, note: str = "") -> None:
        self.phase_results.append(
            PhaseResult(
                phase=self.phase,
                trials_in_phase=len(self._phase_trials),
                correct_in_phase=sum(1 for t in self._phase_trials if t.is_correct),
                passed=passed,
                note=note,
            )
        )

    def _fail(self, reason: str) -> None:
        self._failed_reason = reason
        self._complete_phase(False, reason)
        self._enter_phase(TutorialPhase.FAILED)

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
            if stim_ms > 0 and t.reaction_time_ms > stim_ms * self.req.speed_max_rt_ratio:
                break
            streak += 1
        return streak

    def _force_incongruent_stimulus(self) -> dict:
        start_with_type = getattr(self.game, "start_trial_with_type", None)
        if callable(start_with_type):
            return start_with_type("incongruent")
        return self.game.start_trial()