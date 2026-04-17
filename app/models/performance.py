"""Performance measurement models for game runs and trials."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TrialResult:
    """Represents a single trial with raw inputs and computed values."""
    trial_number: int
    level: int
    is_correct: bool
    reaction_time_ms: float
    accuracy: float = 0.0
    pi_trial: float = 0.0
    scoring_payload: dict = field(default_factory=dict)


@dataclass
class RunResult:
    """Aggregated results for a completed run with all performance metrics."""
    player_id: str
    game_id: str
    run_id: str
    timestamp: datetime
    trials: list[TrialResult] = field(default_factory=list)
    pi_run: float = 0.0
    quality_score: float = 0.0
    consistency_score: float = 0.0
    avg_accuracy: float = 0.0
    avg_reaction_time: float = 0.0
    final_level: int = 1
    rating_eligible: bool = False
