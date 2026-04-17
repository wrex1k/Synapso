from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import statistics
import math

from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.service.pi_adapters import compute_trial_accuracy



# contants
DELTA = 100                    # ms buffer | prevents extreme scores on sub-100ms RT
K = 1000                       # scaling factor | fallback scaling constant
K_PER_GAME: dict[str, int] = {
    "stroop": 800,
    "memory_grid": 2400,
    "mental_rotation": 2550,
}
MIN_LEVEL = 1
MAX_LEVEL = 6

# Fixed reference reaction times per game (ms)
REFERENCE_RT: dict[str, int] = {
    "stroop": 700,
    "memory_grid": 1700,
    "mental_rotation": 1300,
}

# RT floor = round(reference_rt * 0.35)
RT_FLOOR: dict[str, int] = {
    slug: round(rt * 0.35) for slug, rt in REFERENCE_RT.items()
}

# Fixed reference baselines for centering pi_run around zero
REFERENCE_BASELINE_PARAMS: dict[str, dict] = {
    "stroop":          {"accuracy": 0.70, "reaction_time_ms": 700,  "level": 1},
    "memory_grid":     {"accuracy": 0.25, "reaction_time_ms": 1700, "level": 1},
    "mental_rotation": {"accuracy": 0.60, "reaction_time_ms": 1300, "level": 1},
}

# Rating-eligibility accuracy thresholds (percent, 0-100 — matches runs.avg_accuracy canonical scale)
RATING_ACCURACY_THRESHOLDS: dict[str, float] = {
    "stroop": 50.0,
    "memory_grid": 30.0,
    "mental_rotation": 50.0,
}

# Skill rating constants
SKILL_RATING_BASE = 1000
SKILL_RATING_SCALE = 100
SKILL_RATING_WINDOW = 7

# Consistency window
CONSISTENCY_WINDOW = 5


# Cached baseline
_BASELINE_CACHE: dict[str, float] = {}


def get_fixed_baseline(game_slug: str) -> float:
    """Return the fixed per-game baseline (pi_trial_raw at reference params)."""
    if game_slug not in _BASELINE_CACHE:
        params = REFERENCE_BASELINE_PARAMS.get(game_slug, REFERENCE_BASELINE_PARAMS["stroop"])
        _BASELINE_CACHE[game_slug] = calculate_pi_trial_raw(
            accuracy=params["accuracy"],
            reaction_time_ms=params["reaction_time_ms"],
            level=params["level"],
            game_slug=game_slug,
        )
    return _BASELINE_CACHE[game_slug]



# Data classes
@dataclass
class TrialResult:
    trial_number: int
    level: int
    is_correct: bool
    reaction_time_ms: float
    accuracy: float = 0.0
    pi_trial: float = 0.0
    scoring_payload: dict = field(default_factory=dict)


@dataclass
class RunResult:
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



# Per-trial scoring
def calculate_pi_trial_raw(
    accuracy: float,
    reaction_time_ms: float,
    level: int,
    game_slug: str = "stroop",
    delta: int = DELTA,
) -> float:
    """Core trial score: (accuracy / (effective_rt + DELTA)) * K * exp(0.15 * level)."""
    accuracy = max(0.0, min(1.0, accuracy))
    level = max(MIN_LEVEL, min(MAX_LEVEL, level))
    k = K_PER_GAME.get(game_slug, K)
    rt_floor = RT_FLOOR.get(game_slug, round(REFERENCE_RT.get(game_slug, 700) * 0.35))
    effective_rt = max(reaction_time_ms, rt_floor)
    level_bonus = math.exp(0.15 * level)
    return (accuracy / (effective_rt + delta)) * k * level_bonus



# Run processing
def process_run(
    player_id: str,
    game_slug: str,
    run_id: str,
    trials: list[TrialResult],
    stage: str = "training",
    recent_runs: list[dict] | None = None,
) -> RunResult:
    """Process a completed run: compute pi_trial, pi_run, quality, consistency, rating eligibility."""
    if not trials:
        logger.warning("Empty trials for run %s", run_id)
        return RunResult(
            player_id=player_id, game_id=game_slug, run_id=run_id,
            timestamp=datetime.now(timezone.utc),
        )

    logger.info(
        "\n%s\nPROCESSING RUN %s | %d trials\n%s",
        "=" * 90, run_id[-12:], len(trials), "=" * 90,
    )

    # 1. Compute trial accuracy
    for trial in trials:
        trial.accuracy = compute_trial_accuracy(game_slug=game_slug, trial=trial)

    # 2. Compute pi_trial for each trial
    for trial in trials:
        raw_pi = calculate_pi_trial_raw(
            trial.accuracy, trial.reaction_time_ms, trial.level, game_slug=game_slug,
        )
        trial.pi_trial = raw_pi
        logger.debug(
            "Trial %2d | L%d | acc=%.3f rt=%.0fms -> pi_trial=%.4f",
            trial.trial_number, trial.level, trial.accuracy,
            trial.reaction_time_ms, raw_pi,
        )

    # 3. Compute pi_run = mean(pi_trial) - fixed_baseline
    pi_trials = [t.pi_trial for t in trials]
    pi_run_raw = statistics.mean(pi_trials)
    baseline = get_fixed_baseline(game_slug)
    pi_run = pi_run_raw - baseline

    if math.isnan(pi_run) or math.isinf(pi_run):
        logger.warning("Invalid pi_run (%.4f) for %s, resetting to 0", pi_run, run_id)
        pi_run = 0.0

    # 4. Compute run metrics
    accuracies = [t.accuracy for t in trials]
    reaction_times = [t.reaction_time_ms for t in trials]
    avg_accuracy = statistics.mean(accuracies)
    avg_rt = statistics.mean(reaction_times)
    final_level = trials[-1].level

    # 5. Quality score (0-100)
    quality_score = calculate_quality_score(
        avg_accuracy=avg_accuracy,
        avg_reaction_time_ms=avg_rt,
        final_level=final_level,
        game_slug=game_slug,
    )

    # 6. Consistency score (rolling across recent runs)
    consistency_score = calculate_consistency_score(
        current_pi_run=pi_run,
        current_avg_accuracy=avg_accuracy,
        current_avg_rt=avg_rt,
        recent_runs=recent_runs,
    )

    # 7. Rating eligibility — binary accuracy in percent (matches runs.avg_accuracy canonical scale)
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

    logger.info(
        "\n%s\nRUN COMPLETE\n"
        "  pi_run            = %+.4f\n"
        "  quality_score     = %.1f\n"
        "  consistency_score = %.1f\n"
        "  rating_eligible   = %s\n"
        "%s\n",
        "--" * 45, pi_run, quality_score, consistency_score,
        rating_eligible, "--" * 45,
    )

    return result



# Quality score
def calculate_quality_score(
    avg_accuracy: float,
    avg_reaction_time_ms: float,
    final_level: int,
    game_slug: str = "stroop",
) -> float:
    """
    Quality (0-100):
      50% accuracy + 30% speed + 20% difficulty
    """
    accuracy_component = max(0.0, min(1.0, avg_accuracy))

    ref_rt = REFERENCE_RT.get(game_slug, 700)
    rt_floor = RT_FLOOR.get(game_slug, round(ref_rt * 0.35))
    speed_component = max(0.0, min(1.0, ref_rt / max(avg_reaction_time_ms, rt_floor)))

    difficulty_component = 1.0 - math.exp(-0.25 * max(final_level - 1, 0))

    quality = 100.0 * (
        0.50 * accuracy_component +
        0.30 * speed_component +
        0.20 * difficulty_component
    )

    return max(0.0, min(100.0, quality))


# Consistency score
def calculate_consistency_score(
    current_pi_run: float,
    current_avg_accuracy: float,
    current_avg_rt: float,
    recent_runs: list[dict] | None = None,
) -> float:
    """
    Consistency (0-100): rolling stability across last up to 5 runs including current.
    If fewer than 2 runs, returns 100.
    """
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
                pi_list.append(float(pi_val))
                acc_list.append(float(acc_val))
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


# Skill rating
def calculate_skill_rating(eligible_pi_runs: list[float]) -> int:
    """
    Compute skill_rating from last up to 7 rating-eligible pi_run values.
    Values should be ordered by ended_at descending (most recent first).
    """
    values = eligible_pi_runs[:SKILL_RATING_WINDOW]

    if not values:
        return SKILL_RATING_BASE

    n = len(values)
    if n <= 4:
        rating_pi = statistics.mean(values)
    else:
        sorted_vals = sorted(values)
        trimmed = sorted_vals[1:-1]
        rating_pi = statistics.mean(trimmed)

    return round(SKILL_RATING_BASE + SKILL_RATING_SCALE * rating_pi)
