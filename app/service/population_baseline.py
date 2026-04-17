from __future__ import annotations

import statistics
from datetime import datetime, timezone, timedelta

from app.utils.logger import get_logger
from app.models.baseline import PopulationBaseline
from app.repository.population_repository import fetch_avg_reaction_times, fetch_recent_pi_runs
from app.service.game_constants import FALLBACK_REFERENCE_RT

logger = get_logger(__name__)

_TTL = timedelta(hours=6)
_cache: dict[str, PopulationBaseline] = {}

def _fetch_baseline(game_slug: str) -> PopulationBaseline:
    """Compute population baseline metrics from recent data."""
    rt_values = fetch_avg_reaction_times(game_slug)
    pi_values = fetch_recent_pi_runs(game_slug)

    sample_size = len(rt_values)

    if sample_size < 5:
        median_rt = float(FALLBACK_REFERENCE_RT.get(game_slug))
        median_pi_run = 0.0
        pi_run_scale = 0.5
    else:
        median_rt = statistics.median(rt_values)
        median_pi_run = statistics.median(pi_values) if pi_values else 0.0
        pi_run_scale = statistics.stdev(pi_values) if len(pi_values) >= 2 else 0.5

    return PopulationBaseline(
        game_slug=game_slug,
        median_rt=median_rt,
        median_pi_run=median_pi_run,
        pi_run_scale=pi_run_scale,
        sample_size=sample_size,
        cached_at=datetime.now(timezone.utc),
    )

def get_population_baseline(game_slug: str) -> PopulationBaseline:
    """Return cached population baseline with automatic refresh."""
    now = datetime.now(timezone.utc)
    cached = _cache.get(game_slug)
    if cached is None or (now - cached.cached_at) >= _TTL:
        try:
            _cache[game_slug] = _fetch_baseline(game_slug)
        except Exception as e:
            logger.warning(
                "Failed to fetch population baseline for %s: %s",
                game_slug,
                e,
            )

            if cached is not None:
                return cached
            _cache[game_slug] = PopulationBaseline(
                game_slug=game_slug,
                median_rt=float(FALLBACK_REFERENCE_RT.get(game_slug)),
                median_pi_run=0.0,
                pi_run_scale=0.5,
                sample_size=0,
                cached_at=now,
            )
    return _cache[game_slug]
