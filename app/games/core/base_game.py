from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

GAME_ID_MAP = {
    "stroop": 1,
    "memory_grid": 2,
    "mental_rotation": 3,
}

NUM_TRIALS_PER_RUN = 20

@dataclass
class TrialResult:
    stimulus_params: dict
    response: str | None
    reaction_time_ms: float
    is_correct: bool
    pi_trial: float = 0.0
    pi_adjusted: float = 0.0
    accuracy: float = 0.0
    consecutive_bad_count: int = 0
    consecutive_correct_count: int = 0
    rt_exceeded_threshold: bool = False
    stimulus_payload: dict = field(default_factory=dict)
    response_payload: dict = field(default_factory=dict)
    scoring_payload: dict = field(default_factory=dict)


class BaseGame(ABC):
    def __init__(
        self,
        game_slug: str,
        user_id: str,
        total_trials: int = NUM_TRIALS_PER_RUN,
        initial_level: int = 1,
        min_level: int = 1,
        max_level: int = 1,
    ):
        self.game_slug = game_slug
        self.user_id = user_id
        self.total_trials = total_trials
        self.initial_level = initial_level
        self.min_level = min_level
        self.max_level = max_level

        self.level: int = initial_level
        self.current_trial_index: int = 0
        self.trials: list[TrialResult] = []
        self.started_at: datetime | None = None

    @abstractmethod
    def start_trial(self) -> dict:
        """Return stimulus parameters for the next trial."""

    @abstractmethod
    def get_correct_answer(self, trial_params: dict) -> str:
        """Return the expected answer for the given trial parameters."""

    @abstractmethod
    def evaluate_trial(
        self,
        trial_params: dict,
        response: str | None,
        reaction_time_ms: float,
    ) -> TrialResult:
        """Evaluate trial and return result with game-specific payloads."""

    def begin_run(self) -> None:
        self.level = self.initial_level
        self.current_trial_index = 0
        self.trials = []
        self.started_at = None

    def get_progress(self) -> dict:
        return {
            "current_trial": self.current_trial_index,
            "total_trials": self.total_trials,
            "level": self.level,
        }

    def end_run(self) -> dict:
        if not self.trials:
            return {
                "avg_reaction_time_ms": None,
                "accuracy": None,
                "pi": None,
                "total_trials": 0,
            }

        correct = [t for t in self.trials if t.is_correct]
        accuracy_decimal = len(correct) / len(self.trials)
        avg_rt = sum(t.reaction_time_ms for t in self.trials) / len(self.trials)
        accuracy_percent = accuracy_decimal * 100

        return {
            "avg_reaction_time_ms": avg_rt,
            "accuracy": accuracy_percent,
            "pi": None,
            "total_trials": len(self.trials),
        }

    def _adjust_level(self) -> None:
        window = 5
        if len(self.trials) < window:
            return

        recent = self.trials[-window:]
        accuracy = sum(1 for t in recent if t.is_correct) / window

        if accuracy >= 0.8 and self.level < self.max_level:
            self.level += 1
        elif accuracy < 0.5 and self.level > self.min_level:
            self.level -= 1
