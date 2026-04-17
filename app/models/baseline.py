"""Population baseline models for performance normalization."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PopulationBaseline:
    """Population-level reference metrics for game performance normalization."""
    game_slug: str
    median_rt: float
    median_pi_run: float
    pi_run_scale: float
    sample_size: int
    cached_at: datetime
