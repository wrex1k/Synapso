from __future__ import annotations

from datetime import datetime, timezone
import statistics
import math

from app.utils.logger import get_logger
from app.models.performance import RunResult, TrialResult

logger = get_logger(__name__)

from app.service.pi_adapters import compute_trial_accuracy
from app.service.population_baseline import get_population_baseline
from app.games.core.base_game import MIN_LEVEL, MAX_LEVEL
from app.service.game_constants import (
    FALLBACK_REFERENCE_RT,
    RT_FLOOR,
    K_PER_GAME,
    RATING_ACCURACY_THRESHOLDS,
)

DELTA = 100
K = 1000

ELO_BASE = 1000
ELO_K_NEW = 32
ELO_K_EST = 16
ELO_ESTABLISHED = 10
ELO_SIGMA = 0.5

CONSISTENCY_WINDOW = 5

def calculate_pi_trial_raw(
    accuracy: float,
    reaction_time_ms: float,
    level: int,
    game_slug: str = "stroop",
    delta: int = DELTA,
) -> float:
    """Compute raw Performance Index for a single trial."""
    accuracy = max(0.0, min(1.0, accuracy))
    level = max(MIN_LEVEL, min(MAX_LEVEL, level))
    k = K_PER_GAME.get(game_slug, K)

    rt_floor = RT_FLOOR.get(
        game_slug,
        round(FALLBACK_REFERENCE_RT.get(game_slug, 700) * 0.35),
    )
    effective_rt = max(reaction_time_ms, rt_floor)

    level_bonus = math.exp(0.15 * level)
    return (accuracy / (effective_rt + delta)) * k * level_bonus

def process_run(
    player_id: str,
    game_slug: str,
    run_id: str,
    trials: list[TrialResult],
    stage: str = "training",
    recent_runs: list[dict] | None = None,
) -> RunResult:
    """Process a completed run and compute all performance metrics."""
    if not trials:
        logger.warning("Empty trials for run %s", run_id)
        return RunResult(
            player_id=player_id,
            game_id=game_slug,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc),
        )

    logger.info(
        "\n%s\nPROCESSING RUN %s | %d trials\n%s",
        "=" * 90, run_id[-12:], len(trials), "=" * 90,
    )

    for trial in trials:
        trial.accuracy = compute_trial_accuracy(game_slug=game_slug, trial=trial)

    for trial in trials:
        trial.pi_trial = calculate_pi_trial_raw(
            trial.accuracy,
            trial.reaction_time_ms,
            trial.level,
            game_slug=game_slug,
        )

    pi_trials = [t.pi_trial for t in trials]
    pi_run = statistics.mean(pi_trials)

    if math.isnan(pi_run) or math.isinf(pi_run):
        logger.warning("Invalid pi_run (%.4f) for %s, resetting to 0", pi_run, run_id)
        pi_run = 0.0

    accuracies = [t.accuracy for t in trials]
    reaction_times = [t.reaction_time_ms for t in trials]

    avg_accuracy = statistics.mean(accuracies)
    avg_rt = statistics.mean(reaction_times)
    final_level = trials[-1].level

    quality_score = calculate_quality_score(
        avg_accuracy,
        avg_rt,
        final_level,
        game_slug=game_slug,
    )

    consistency_score = calculate_consistency_score(
        pi_run,
        avg_accuracy,
        avg_rt,
        recent_runs,
    )

    rating_eligible = False
    if stage == "training":
        binary_accuracy_pct = 100.0 * statistics.mean(
            1.0 if t.is_correct else 0.0 for t in trials
        )
        threshold = RATING_ACCURACY_THRESHOLDS.get(game_slug, 50.0)
        rating_eligible = binary_accuracy_pct >= threshold

    result = RunResult(
        player_id=player_id,
        game_id=game_slug,
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        trials=trials,
        pi_run=pi_run,
        quality_score=quality_score,
        consistency_score=consistency_score,
        avg_accuracy=avg_accuracy,
        avg_reaction_time=avg_rt,
        final_level=final_level,
        rating_eligible=rating_eligible,
    )

    return result

def calculate_quality_score(
    avg_accuracy: float,
    avg_reaction_time_ms: float,
    final_level: int,
    game_slug: str = "stroop",
) -> float:
    """Compute overall quality score from accuracy, speed, and difficulty."""
    accuracy_component = max(0.0, min(1.0, avg_accuracy))

    pop = get_population_baseline(game_slug)
    ref_rt = pop.median_rt
    rt_floor = RT_FLOOR.get(game_slug, round(ref_rt * 0.35))

    speed_component = max(
        0.0,
        min(1.3, ref_rt / max(avg_reaction_time_ms, rt_floor)),
    )

    difficulty_component = 1.0 - math.exp(-0.25 * max(final_level - 1, 0))

    quality = 100.0 * (
        0.50 * accuracy_component +
        0.30 * speed_component +
        0.20 * difficulty_component
    )

    return max(0.0, min(100.0, quality))

def calculate_consistency_score(
    current_pi_run: float,
    current_avg_accuracy: float,
    current_avg_rt: float,
    recent_runs: list[dict] | None = None,
) -> float:
    """Compute consistency score based on performance stability across recent runs."""
    pi_list = [current_pi_run]
    acc_list = [current_avg_accuracy]
    rt_list = [current_avg_rt]

    if recent_runs:
        window = recent_runs[-(CONSISTENCY_WINDOW - 1):]
        for run in window:
            pi_val = run.get("pi_run")
            acc_val = run.get("avg_accuracy")
            rt_val = run.get("avg_reaction_time_ms")

            if pi_val is not None and acc_val is not None and rt_val is not None:
                acc_norm = float(acc_val) / 100.0 if float(acc_val) > 1.0 else float(acc_val)
                pi_list.append(float(pi_val))
                acc_list.append(acc_norm)
                rt_list.append(float(rt_val))

    if len(pi_list) < 2:
        return 100.0

    pi_stability = math.exp(-statistics.stdev(pi_list) / 0.35)
    acc_stability = math.exp(-statistics.stdev(acc_list) / 0.10)

    rt_mean = statistics.mean(rt_list)
    rt_cv = statistics.stdev(rt_list) / max(rt_mean, 1.0)
    rt_stability = math.exp(-rt_cv / 0.25)

    consistency = 100.0 * (
        0.40 * pi_stability +
        0.30 * acc_stability +
        0.30 * rt_stability
    )

    return max(0.0, min(100.0, consistency))

def calculate_elo_rating(
    current_rating: int,
    pi_run: float,
    pop_median_pi_run: float,
    pop_pi_run_scale: float,
    eligible_run_count: int,
) -> int:
    """Update ELO rating based on performance relative to population median."""
    sigma = max(pop_pi_run_scale, ELO_SIGMA)
    K = ELO_K_NEW if eligible_run_count < ELO_ESTABLISHED else ELO_K_EST

    expected = 1.0 / (1.0 + 10.0 ** ((ELO_BASE - current_rating) / 400.0))
    actual = 1.0 / (1.0 + math.exp(-(pi_run - pop_median_pi_run) / sigma))

    new_rating = current_rating + K * (actual - expected)
    return round(new_rating)