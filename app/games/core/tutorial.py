from __future__ import annotations
from app.games.core.base_game import BaseGame
from app.models.tutorial import PhaseRequirements, PhaseResult, TutorialPhase

class TutorialRunner:
    """Four-phase tutorial runner for Stroop game with warmup, congruent, incongruent, and speed phases."""

    def __init__(self, game: BaseGame, requirements: PhaseRequirements | None = None):
        """Initialize tutorial runner with game instance and phase requirements."""
        self.game = game
        self.req = requirements or PhaseRequirements()
        self.phase: TutorialPhase = TutorialPhase.WARMUP
        self.phase_results: list[PhaseResult] = []
        self._phase_trials: list = []
        self._phase_peak_within: float = 0.0

    @property
    def passed(self) -> bool:
        """Return True if tutorial has been passed."""
        return self.phase == TutorialPhase.PASSED

    @property
    def failed(self) -> bool:
        """Return True if tutorial has failed."""
        return self.phase == TutorialPhase.FAILED

    def configure(self) -> None:
        """Configure game for tutorial mode and enter warmup phase."""
        self.game.total_trials = 50
        self.game.level = self.game.min_level
        self.game.initial_level = self.game.min_level
        self.game.begin_run()
        self._enter_phase(TutorialPhase.WARMUP)

    def next_trial_override(self) -> dict | None:
        """Return forced trial parameters during incongruent phase or None."""
        if self.phase == TutorialPhase.INCONGRUENT_TEST:
            return self._force_incongruent_stimulus()
        return None

    def check_after_trial(self) -> bool:
        """Check phase completion criteria after trial and advance if passed."""
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

    def get_progress_pct(self) -> int:
        """Return tutorial progress as percentage."""
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
            within = max(within, self._phase_peak_within)
        else:
            within = 0.0
        self._phase_peak_within = max(self._phase_peak_within, within)
        return int(base + within * 25)

    def get_phase_summary(self) -> list[dict]:
        """Return summary of all completed phases."""
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
        """Check warmup phase completion criteria."""
        pt = self._phase_trials
        correct = sum(1 for t in pt if t.is_correct)
        if correct >= self.req.warmup_required_correct:
            self._complete_phase(True, f"{correct} correct")
            self._enter_phase(TutorialPhase.CONGRUENT_CHECK)
        elif len(pt) >= self.req.warmup_max_trials:
            self._fail(f"{correct}/{len(pt)} correct")
        return False

    def _check_congruent(self) -> bool:
        """Check congruent phase completion criteria."""
        pt = self._phase_trials
        streak = self._trailing_streak(pt)
        if streak >= self.req.congruent_required_streak:
            self._complete_phase(True, f"streak {streak}")
            self._enter_phase(TutorialPhase.INCONGRUENT_TEST)
        elif len(pt) >= self.req.congruent_max_trials:
            self._fail(f"No streak {self.req.congruent_required_streak} in {self.req.congruent_max_trials}")
        return False

    def _check_incongruent(self) -> bool:
        """Check incongruent test phase completion criteria."""
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
        """Check speed phase completion criteria."""
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
        """Enter new phase and reset trial tracking."""
        self.phase = phase
        self._phase_trials = []
        self._phase_peak_within = 0.0

    def _complete_phase(self, passed: bool, note: str = "") -> None:
        """Record phase result and add to history."""
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
        """Mark tutorial as failed with reason."""
        self._complete_phase(False, reason)
        self._enter_phase(TutorialPhase.FAILED)

    @staticmethod
    def _trailing_streak(trials) -> int:
        """Calculate consecutive correct trials from end of list."""
        streak = 0
        for t in reversed(trials):
            if t.is_correct:
                streak += 1
            else:
                break
        return streak

    def _fast_correct_streak(self, trials) -> int:
        """Calculate consecutive fast correct trials from end of list."""
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
        """Force generation of incongruent trial during incongruent phase."""
        start_with_type = getattr(self.game, "start_trial_with_type", None)
        if callable(start_with_type):
            return start_with_type("incongruent")
        return self.game.start_trial()