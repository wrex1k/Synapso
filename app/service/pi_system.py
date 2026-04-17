from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import statistics
import math

from app.utils.logger import logger
from app.games.stroop.config import get_rt_penalty_thresholds as get_stroop_rt_thresholds
from app.games.memory_grid.config import get_rt_penalty_thresholds as get_memory_grid_rt_thresholds
from app.games.mental_rotation.config import get_rt_penalty_thresholds as get_mental_rotation_rt_thresholds
from app.service.pi_adapters import compute_trial_accuracy



# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DELTA = 100                    # ms buffer | prevents extreme scores on sub-100ms RT
K = 1000                       # scaling factor | sets order of magnitude of raw pi
CONSISTENCY_WINDOW = 10        # recent runs used for quality/consistency averages
CONSECUTIVE_BAD_PENALTY = 0.5  # geometric penalty base per consecutive wrong trial
STREAK_BONUS_BASE = 0.05       # bonus per correct trial in a streak
STREAK_BONUS_MAX = 0.40        # hard cap on streak bonus
SKILL_SCORE_PI_RUNS = 10       # recent runs that feed the pi_performance component
MIN_LEVEL = 1
MAX_LEVEL = 6

FALLBACK_PARAMS: dict[str, dict] = {
    "stroop":          {"accuracy": 0.70, "reaction_time_ms": 700,  "level": 1},
    "memory_grid":     {"accuracy": 0.25, "reaction_time_ms": 1700, "level": 1},
    "mental_rotation": {"accuracy": 0.60, "reaction_time_ms": 1300, "level": 1},
}


def _rt_penalty_thresholds_for_game(game_slug: str) -> dict[int, int]:
    if game_slug == "stroop":
        return get_stroop_rt_thresholds()
    if game_slug == "memory_grid":
        return get_memory_grid_rt_thresholds()
    if game_slug == "mental_rotation":
        return get_mental_rotation_rt_thresholds()
    return get_stroop_rt_thresholds()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TrialResult:
    trial_number: int
    level: int
    is_correct: bool
    reaction_time_ms: float
    accuracy: float = 0.0           # Partial accuracy 0.0-1.0
    pi_trial: float = 0.0           # Raw pi before adjustments
    pi_adjusted: float = 0.0        # Final pi after modifiers and baseline
    scoring_payload: dict = field(default_factory=dict)
    consecutive_bad_count: int = 0
    consecutive_correct_count: int = 0
    rt_exceeded_threshold: bool = False


@dataclass
class RunResult:
    player_id: str
    game_id: str
    run_id: str
    timestamp: datetime
    trials: list[TrialResult] = field(default_factory=list)
    pi_run: float = 0.0                  # mean(pi_adjusted) — canonical metric
    pi_run_normalized_raw: float = 0.0  # mean(pi_trial) — for baseline computation
    quality_score: float = 0.0
    consistency_score: float = 0.0
    avg_accuracy: float = 0.0
    avg_reaction_time: float = 0.0
    final_level: int = 1


@dataclass
class PlayerStats:
    player_id: str
    username: str
    avatar_path: str = "default.webp"
    accumulated_pi: float = field(default=0.0)
    total_runs: int = 0
    total_trials: int = 0
    avg_accuracy_overall: float = 0.0
    quality_average: float = 0.0
    consistency_average: float = 0.0
    runs_history: list[RunResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_at: datetime | None = None
    best_pi_run: float = 0.0

    def last_n_runs(self, n: int = 5) -> list[RunResult]:
        return self.runs_history[-n:]

    def pi_trend(self, n: int = 5) -> float | None:
        runs = self.last_n_runs(n)
        return statistics.mean([r.pi_run for r in runs]) if runs else None

    def quality_trend(self, n: int = 5) -> float | None:
        runs = self.last_n_runs(n)
        return statistics.mean([r.quality_score for r in runs]) if runs else None

    def consistency_trend(self, n: int = 5) -> float | None:
        runs = self.last_n_runs(n)
        return statistics.mean([r.consistency_score for r in runs]) if runs else None


@dataclass
class GamePiStats:
    mean: float
    std: float


# Baseline: loaded once at startup, median of pi_run_normalized_raw across all runs.
# Population reference: pi_adjusted=0 → median, >0 → above, <0 → below. Call load_baseline_on_startup() in App.__init__().

_BASELINE: dict[str, float] = {}

FALLBACK_PI_STATS: dict[str, GamePiStats] = {
    "stroop":          GamePiStats(mean=0.0, std=0.5),
    "memory_grid":     GamePiStats(mean=0.0, std=0.3),
    "mental_rotation": GamePiStats(mean=0.0, std=0.4),
}

_GAME_PI_STATS: dict[str, GamePiStats] = {}


def load_baseline_on_startup(game_slug: str = "stroop") -> None:
    """
    Fetch the baseline from the DB and hold it for the session.
    Call once from App.__init__() before the first game starts.
    """
    _BASELINE[game_slug] = _fetch_baseline_from_db(game_slug)
    logger.info(f"Baseline loaded at startup for '{game_slug}': {_BASELINE[game_slug]:.4f}")


def load_game_pi_stats(game_slug: str) -> None:
    """
    Load population mean and stddev of pi_run for the specified game.
    """
    try:
        from app.repository.run_repository import fetch_pi_run_values

        pi_values = fetch_pi_run_values(game_slug)

        if len(pi_values) < 10:
            logger.warning(
                f"Fallback pi_stats for '{game_slug}' "
                f"(runs in DB: {len(pi_values)})"
            )
            _GAME_PI_STATS[game_slug] = FALLBACK_PI_STATS.get(
                game_slug, FALLBACK_PI_STATS["stroop"]
            )
            return

        mean = statistics.mean(pi_values)
        std = statistics.stdev(pi_values)
        _GAME_PI_STATS[game_slug] = GamePiStats(mean=mean, std=std)
        logger.info(
            f"Pi stats for '{game_slug}': mean={mean:.4f} std={std:.4f} ({len(pi_values)} runs)"
        )

    except Exception as e:
        logger.warning(f"Pi stats DB error for '{game_slug}': {e}, using fallback")
        _GAME_PI_STATS[game_slug] = FALLBACK_PI_STATS.get(
            game_slug, FALLBACK_PI_STATS["stroop"]
        )


def get_global_baseline(game_slug: str = "stroop") -> float:
    """Return the session baseline. Fetches lazily if startup load was skipped."""
    if game_slug not in _BASELINE:
        logger.warning(
            f"Baseline not loaded for '{game_slug}' -- was load_baseline_on_startup() called?"
        )
        _BASELINE[game_slug] = _fetch_baseline_from_db(game_slug)
    return _BASELINE[game_slug]


def _fetch_baseline_from_db(game_slug: str = "stroop") -> float:
    try:
        from app.repository.run_repository import fetch_pi_normalized_raw_values

        pi_values = fetch_pi_normalized_raw_values(game_slug)

        if len(pi_values) < 5:
            logger.warning(
                f"Fallback baseline for '{game_slug}' "
                f"(runs in DB: {len(pi_values)})"
            )
            return _calculate_fallback_baseline(game_slug)

        baseline = statistics.median(pi_values)
        logger.info(f"Baseline for '{game_slug}': {baseline:.4f} ({len(pi_values)} runs)")
        return baseline

    except Exception as e:
        logger.warning(f"Baseline DB error: {e}, using fallback")
        return _calculate_fallback_baseline(game_slug)


def _calculate_fallback_baseline(game_slug: str = "stroop") -> float:
    """
    Used when the DB has fewer than 5 completed runs.
    Returns a game-specific calibrated baseline from FALLBACK_PARAMS.
    Falls back to stroop values if the slug is not recognised.
    """
    params = FALLBACK_PARAMS.get(game_slug, FALLBACK_PARAMS["stroop"])
    baseline = calculate_pi_trial_raw(
        accuracy=params["accuracy"],
        reaction_time_ms=params["reaction_time_ms"],
        level=params["level"],
    )
    logger.warning(f"Using fallback baseline for '{game_slug}': {baseline:.4f}")
    return baseline


def normalize_pi_run(pi_run: float, game_slug: str) -> float:
    """
    Normalizuje pi_run na z-score pomocou populačných štatistík.
    Výstup: 0 = priemerný hráč, +1 = o 1 std nad priemerom, atď.
    Clamp na [-4, 4] aby single outlier run nezničil skill_score.
    """
    stats = _GAME_PI_STATS.get(game_slug) or FALLBACK_PI_STATS.get(game_slug)
    if not stats or stats.std < 1e-6:
        return 0.0
    z = (pi_run - stats.mean) / stats.std
    return max(-4.0, min(4.0, z))


# ---------------------------------------------------------------------------
# Per-trial scoring
# ---------------------------------------------------------------------------

def calculate_pi_trial_raw(
    accuracy: float,
    reaction_time_ms: float,
    level: int,
    delta: int = DELTA,
    k: int = K,
) -> float:
    reaction_time_ms = max(0.0, reaction_time_ms)
    accuracy = max(0.0, min(1.0, accuracy))
    level = max(MIN_LEVEL, min(MAX_LEVEL, level))
    level_bonus = math.exp(0.15 * level)
    return (accuracy / (reaction_time_ms + delta)) * k * level_bonus


def calculate_pi_trial(
    trial: TrialResult,
    global_baseline: float,
    rt_thresholds: dict[int, int] | None = None,
    apply_rt_penalty: bool = True,
    apply_consecutive_penalty: bool = True,
    apply_streak_bonus: bool = True,
) -> float:
    """
    Compute adjusted pi: raw pi → RT penalty → consecutive penalty → streak bonus → baseline.
    Call via process_run(); trial.accuracy must be corrected RGB-distance value first.
    """
    raw_pi = calculate_pi_trial_raw(trial.accuracy, trial.reaction_time_ms, trial.level)
    pi = raw_pi
    logger.debug(
        f"Trial {trial.trial_number:2d} | L{trial.level} | "
        f"acc={trial.accuracy:.3f} rt={trial.reaction_time_ms:.0f}ms "
        f"-> raw_pi={raw_pi:.4f}"
    )

    thresholds = rt_thresholds or get_stroop_rt_thresholds()
    if apply_rt_penalty and trial.level in thresholds:
        max_rt = thresholds[trial.level]
        if trial.reaction_time_ms > max_rt:
            trial.rt_exceeded_threshold = True
            rt_ratio = trial.reaction_time_ms / max_rt
            penalty = max(0.1, 1.0 / rt_ratio)
            pi_before = pi
            pi *= penalty
            logger.debug(
                f"  RT penalty: {trial.reaction_time_ms:.0f}>{max_rt}ms "
                f"ratio={rt_ratio:.2f} x{penalty:.3f} -> {pi_before:.4f}->{pi:.4f}"
            )

    if apply_consecutive_penalty and trial.consecutive_bad_count > 0:
        if (not trial.is_correct) or trial.accuracy < 0.5:
            penalty = CONSECUTIVE_BAD_PENALTY ** trial.consecutive_bad_count
            pi_before = pi
            pi *= penalty
            logger.debug(
                f"  Consec bad x{trial.consecutive_bad_count}: "
                f"{CONSECUTIVE_BAD_PENALTY}^{trial.consecutive_bad_count}={penalty:.3f} "
                f"-> {pi_before:.4f}->{pi:.4f}"
            )

    if apply_streak_bonus and trial.is_correct and trial.consecutive_correct_count > 1:
        bonus = min(STREAK_BONUS_MAX, STREAK_BONUS_BASE * (trial.consecutive_correct_count - 1))
        pi_before = pi
        pi *= (1.0 + bonus)
        logger.debug(
            f"  Streak x{trial.consecutive_correct_count}: "
            f"+{bonus:.1%} -> {pi_before:.4f}->{pi:.4f}"
        )

    pi_adjusted = pi - global_baseline
    trial.pi_trial = raw_pi
    trial.pi_adjusted = pi_adjusted

    logger.debug(
        f"  pi={pi:.4f} - baseline({global_baseline:.4f}) = {pi_adjusted:+.4f}"
    )

    return pi_adjusted


# ---------------------------------------------------------------------------
# Run processing
# ---------------------------------------------------------------------------

def process_run(
    player_id: str,
    game_slug: str,
    run_id: str,
    trials: list[TrialResult],
) -> RunResult:
    if not trials:
        logger.warning(f"Empty trials for run {run_id}")
        return RunResult(
            player_id=player_id, game_id=game_slug, run_id=run_id,
            timestamp=datetime.now(timezone.utc),
        )

    logger.info(
        f"\n{'='*90}"
        f"\nPROCESSING RUN {run_id[-12:]} | {len(trials)} trials"
        f"\n{'='*90}"
    )

    global_baseline = get_global_baseline(game_slug)
    rt_thresholds = _rt_penalty_thresholds_for_game(game_slug)
    logger.info(f"Baseline (per-trial): {global_baseline:.4f}\n")

    for trial in trials:
        trial.accuracy = compute_trial_accuracy(game_slug=game_slug, trial=trial)

    consecutive_bad = 0
    consecutive_correct = 0
    for trial in trials:
        if trial.is_correct:
            consecutive_bad = 0
            consecutive_correct += 1
        else:
            consecutive_correct = 0
            consecutive_bad += 1
        trial.consecutive_bad_count = consecutive_bad
        trial.consecutive_correct_count = consecutive_correct

    adjusted_pis: list[float] = []
    for trial in trials:
        pi_adj = calculate_pi_trial(
            trial=trial,
            global_baseline=global_baseline,
            rt_thresholds=rt_thresholds,
            apply_rt_penalty=True,
            apply_consecutive_penalty=True,
            apply_streak_bonus=True,
        )
        adjusted_pis.append(pi_adj)
        trial.pi_adjusted = pi_adj

    num_trials = len(trials)
    pi_run = statistics.mean(adjusted_pis)
    pi_run_normalized_raw = statistics.mean([t.pi_trial for t in trials])

    binary_accuracy = sum(1 for t in trials if t.is_correct) / num_trials
    if game_slug == "memory_grid":
        effective_accuracy = statistics.mean([t.accuracy for t in trials])
        spam_threshold = 0.30
        hard_cutoff = 0.15
    else:
        effective_accuracy = binary_accuracy
        spam_threshold = 0.50
        hard_cutoff = 0.35

    if effective_accuracy < spam_threshold:
        factor = max(0.0, effective_accuracy / spam_threshold)
        pi_run *= factor
        # pi_run_normalized_raw is NOT damped — it must stay a clean
        # mean(pi_trial) for future baseline computation.
        if effective_accuracy < hard_cutoff and pi_run > 0:
            pi_run = 0.0
        logger.info(
            "Low accuracy damping applied: eff_acc=%.3f (binary=%.3f) factor=%.3f pi_run=%.4f",
            effective_accuracy,
            binary_accuracy,
            factor,
            pi_run,
        )

    if math.isnan(pi_run) or math.isinf(pi_run):
        logger.warning(f"Invalid pi_run ({pi_run}) for {run_id}, resetting to 0")
        pi_run = 0.0
        pi_run_normalized_raw = 0.0

    accuracies = [t.accuracy for t in trials]
    reaction_times = [t.reaction_time_ms for t in trials]
    avg_accuracy = statistics.mean(accuracies)
    avg_rt = statistics.mean(reaction_times)
    final_level = trials[-1].level

    quality_score = _calculate_quality_score(
        accuracies=accuracies,
        reaction_times=reaction_times,
        final_level=final_level,
        adjusted_pis=adjusted_pis,
    )
    consistency_score = _calculate_consistency_score(trials)

    result = RunResult(
        player_id=player_id,
        game_id=game_slug,
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        trials=trials,
        pi_run=pi_run,
        pi_run_normalized_raw=pi_run_normalized_raw,
        quality_score=quality_score,
        consistency_score=consistency_score,
        avg_accuracy=avg_accuracy,
        avg_reaction_time=avg_rt,
        final_level=final_level,
    )

    logger.info(
        f"\n{'--'*45}\nRUN COMPLETE\n"
        f"  pi_run                = {pi_run:+.4f}  (mean(pi_adjusted) — canonical run metric)\n"
        f"  pi_run_normalized_raw = {pi_run_normalized_raw:+.4f}  (mean(pi_trial) — baseline source)\n"
        f"  quality_score         = {quality_score:.3f}\n"
        f"  consistency_score     = {consistency_score:.3f}\n"
        f"{'--'*45}\n"
    )

    return result


# ---------------------------------------------------------------------------
# Quality and consistency
# ---------------------------------------------------------------------------

def _calculate_quality_score(
    accuracies: list[float],
    reaction_times: list[float],
    final_level: int,
    adjusted_pis: list[float],
) -> float:
    """
    Composite quality (0-1): 40% accuracy, 25% RT stability, 20% level reached, 15% pi sigmoid.
    """
    if not accuracies:
        return 0.0

    accuracy_component = statistics.mean(accuracies)

    if len(reaction_times) > 1:
        rt_mean = statistics.mean(reaction_times)
        rt_std = statistics.stdev(reaction_times)
        cv = rt_std / (rt_mean + 1e-9)
        rt_consistency_component = math.exp(-cv)
    else:
        rt_consistency_component = 1.0

    level_component = (final_level - MIN_LEVEL) / max(1, MAX_LEVEL - MIN_LEVEL)

    mean_adj_pi = statistics.mean(adjusted_pis) if adjusted_pis else 0.0
    pi_component = 1.0 / (1.0 + math.exp(-mean_adj_pi))

    quality = (
        accuracy_component        * 0.40 +
        rt_consistency_component  * 0.25 +
        level_component           * 0.20 +
        pi_component              * 0.15
    )

    return max(0.0, min(1.0, quality))


def _calculate_consistency_score(trials: list[TrialResult]) -> float:
    """
    Performance stability (0-1): avg of accuracy variance and RT coefficient of variation.
    """
    if len(trials) < 2:
        return 1.0

    accuracies = [t.accuracy for t in trials]
    acc_variance = statistics.variance(accuracies)
    acc_consistency = math.exp(-acc_variance)

    rts = [t.reaction_time_ms for t in trials]
    rt_mean = statistics.mean(rts)
    rt_std = statistics.stdev(rts)
    cv = rt_std / (rt_mean + 1e-9)
    rt_consistency = math.exp(-cv)

    return max(0.0, min(1.0, (acc_consistency + rt_consistency) / 2))


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class Leaderboard:
    """
    In-memory leaderboard. Skill score (0-1): 50% pi_performance + 25% quality + 15% consistency + 10% accuracy.
    """

    def __init__(self):
        self.players: dict[str, PlayerStats] = {}

    def add_or_get_player(
        self,
        player_id: str,
        username: str,
        avatar_path: str = "default.webp",
    ) -> PlayerStats:
        if player_id not in self.players:
            self.players[player_id] = PlayerStats(
                player_id=player_id,
                username=username,
                avatar_path=avatar_path,
            )
        return self.players[player_id]

    def update_player_after_run(self, player_id: str, run: RunResult) -> None:
        player = self.players.get(player_id)
        if not player:
            logger.warning(f"Player {player_id} not found in leaderboard")
            return

        player.runs_history.append(run)
        player.total_runs = len(player.runs_history)
        player.total_trials += len(run.trials)
        player.last_run_at = run.timestamp

        recent = player.runs_history[-CONSISTENCY_WINDOW:]
        player.quality_average = statistics.mean([r.quality_score for r in recent])
        player.consistency_average = statistics.mean([r.consistency_score for r in recent])

        all_acc = [t.accuracy for r in player.runs_history for t in r.trials]
        if all_acc:
            player.avg_accuracy_overall = statistics.mean(all_acc)

        if run.pi_run > player.best_pi_run:
            player.best_pi_run = run.pi_run

        skill_score = self._calculate_skill_score(player)
        logger.info(f"Player {player.username}: skill_score={skill_score:.4f}")

    def _calculate_skill_score(self, player: PlayerStats) -> float:
        if player.total_runs == 0:
            return 0.0

        recent_runs = player.runs_history[-SKILL_SCORE_PI_RUNS:]
        mean_pi = statistics.mean([
            normalize_pi_run(r.pi_run, r.game_id) for r in recent_runs
        ])

        pi_performance = 1.0 / (1.0 + math.exp(-0.25 * mean_pi))

        quality     = max(0.0, min(1.0, player.quality_average))
        consistency = max(0.0, min(1.0, player.consistency_average))
        accuracy    = max(0.0, min(1.0, player.avg_accuracy_overall))

        skill_score = (
            pi_performance * 0.50 +
            quality        * 0.25 +
            consistency    * 0.15 +
            accuracy       * 0.10
        )

        return max(0.0, min(1.0, skill_score))

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        players_with_scores = [
            (player, self._calculate_skill_score(player))
            for player in self.players.values()
        ]
        sorted_players = sorted(players_with_scores, key=lambda x: x[1], reverse=True)

        entries = []
        for rank, (player, skill_score) in enumerate(sorted_players[:limit], 1):
            recent_runs = player.runs_history[-SKILL_SCORE_PI_RUNS:]
            mean_pi = statistics.mean([
                normalize_pi_run(r.pi_run, r.game_id) for r in recent_runs
            ]) if recent_runs else 0.0
            entries.append({
                "rank": rank,
                "username": player.username,
                "avatar_path": player.avatar_path,
                "skill_score": round(skill_score, 4),
                "mean_pi": round(mean_pi, 4),
                "quality_score": round(player.quality_average, 3),
                "consistency_score": round(player.consistency_average, 3),
                "total_runs": player.total_runs,
            })
        return entries

    def get_player_stats(self, player_id: str) -> dict | None:
        player = self.players.get(player_id)
        if not player:
            return None

        skill_score = self._calculate_skill_score(player)
        recent_runs = player.runs_history[-SKILL_SCORE_PI_RUNS:]
        mean_pi = statistics.mean([
            normalize_pi_run(r.pi_run, r.game_id) for r in recent_runs
        ]) if recent_runs else 0.0

        return {
            "player_id": player_id,
            "username": player.username,
            "skill_score": round(skill_score, 4),
            "mean_pi": round(mean_pi, 4),
            "quality_average": round(player.quality_average, 3),
            "consistency_average": round(player.consistency_average, 3),
            "avg_accuracy": round(player.avg_accuracy_overall * 100, 1),
            "total_runs": player.total_runs,
            "total_trials": player.total_trials,
            "pi_trend_5": round(player.pi_trend(5), 4) if player.total_runs >= 5 else None,
            "quality_trend_5": round(player.quality_trend(5), 3) if player.total_runs >= 5 else None,
            "consistency_trend_5": round(player.consistency_trend(5), 3) if player.total_runs >= 5 else None,
            "best_pi_run": round(player.best_pi_run, 4),
            "accumulated_pi": round(player.accumulated_pi, 4),
        }