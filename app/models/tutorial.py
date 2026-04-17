"""Tutorial phase models for tracking tutorial progress."""

from dataclasses import dataclass
from enum import Enum, auto


class TutorialPhase(Enum):
    """Tutorial progression phases."""
    WARMUP = auto()
    CONGRUENT_CHECK = auto()
    INCONGRUENT_TEST = auto()
    SPEED_CHECK = auto()
    PASSED = auto()
    FAILED = auto()


@dataclass
class PhaseResult:
    """Container for phase completion result and statistics."""
    phase: TutorialPhase
    trials_in_phase: int
    correct_in_phase: int
    passed: bool
    note: str = ""


@dataclass(frozen=True)
class PhaseRequirements:
    """Configuration parameters for tutorial phase completion criteria."""
    warmup_required_correct: int = 3
    warmup_max_trials: int = 8
    congruent_required_streak: int = 3
    congruent_max_trials: int = 10
    incongruent_min_trials: int = 6
    incongruent_required_accuracy: float = 0.65
    incongruent_max_trials: int = 14
    speed_required_streak: int = 3
    speed_max_rt_ratio: float = 0.7
    speed_max_trials: int = 10
