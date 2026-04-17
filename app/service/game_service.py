"""GameService is the service layer for game lifecycle management. It orchestrates the flow of a game
from tutorial to play,and handles all interactions with the database and PI system.
"""

import uuid
from datetime import datetime, timezone

from app.games.core.base_game import BaseGame
from app.games.core.tutorial import TutorialRunner
from app.repository.run_repository import abandon_run, create_run, save_run, save_trials
from app.repository.tutorial_repository import set_tutorial_completed
from app.repository.stats_repository import fetch_player_game_stats, upsert_player_game_stats
from app.service.pi_system import TrialResult as PITrialResult, process_run, calculate_pi_trial_raw
from app.utils.logger import logger



def _compute_player_stats_update(
    current: dict | None,
    pi_run: float,
    avg_accuracy: float,
    trial_count: int,
    avg_reaction_time_ms: float | None = None,
    quality_score: float | None = None,
    consistency_score: float | None = None,
) -> dict:
    """Compute the new player_game_stats values after a completed run."""
    if current:
        old_bank = current.get("accumulated_pi", 0.0)
        total_runs = current.get("total_runs", 0)
        total_trials = current.get("total_trials", 0)
        best_pi = current.get("best_pi_run")
        old_rt = current.get("avg_reaction_time_ms") or 0.0
        old_acc = current.get("avg_accuracy_overall") or 0.0
        old_quality = current.get("quality_average") or 0.0
        old_consistency = current.get("consistency_average") or 0.0
    else:
        old_bank = 0.0
        total_runs = 0
        total_trials = 0
        best_pi = None
        old_rt = old_acc = old_quality = old_consistency = 0.0

    def _running_avg(old_val: float, new_val: float | None) -> float:
        """Count-weighted running average. Bootstraps from new_val when old is uninitialized."""
        if new_val is None:
            return old_val
        if total_runs == 0 or old_val == 0.0:
            return new_val
        return (old_val * total_runs + new_val) / (total_runs + 1)

    new_bank = _running_avg(old_bank, pi_run)
    new_best_pi = pi_run if (best_pi is None or pi_run > best_pi) else best_pi

    now = datetime.now(timezone.utc).isoformat()

    logger.info("\nPI UPDATE:\n pi_run=%.2f  |  old_avg=%.2f  new_avg=%.2f  (runs=%d)", pi_run, old_bank, new_bank, total_runs)

    return {
        "accumulated_pi": new_bank,
        "total_runs": total_runs + 1,
        "total_trials": total_trials + max(0, int(trial_count)),
        "best_pi_run": new_best_pi,
        "last_run_at": now,
        "updated_at": now,
        "avg_reaction_time_ms": _running_avg(old_rt, avg_reaction_time_ms),
        "avg_accuracy_overall": _running_avg(old_acc, avg_accuracy),
        "quality_average": _running_avg(old_quality, quality_score),
        "consistency_average": _running_avg(old_consistency, consistency_score),
    }


class GameService:
    """Orchestrates game lifecycle: tutorial -> play -> save."""

    def __init__(self, game: BaseGame):
        self.game = game
        self._run_id: str | None = None
        self._run_stage: str = "training"

    def create_tutorial_runner(self) -> TutorialRunner:
        """Create a TutorialRunner for the current game."""
        factory = getattr(self.game, "create_tutorial_runner", None)
        if callable(factory):
            return factory()
        return TutorialRunner(self.game)

    def complete_tutorial(self, runner: TutorialRunner) -> bool:
        """Mark the tutorial as completed in DB if passed."""
        passed = runner.passed

        if passed:
            try:
                set_tutorial_completed(
                    self.game.user_id,
                    self.game.game_slug,
                    run_id=self._run_id,
                )
                logger.info("Tutorial completed and saved for game=%s, run=%s", self.game.game_slug, self._run_id)
            except Exception as e:
                logger.warning("Tutorial passed but flag not saved: %s", e)
        else:
            logger.info("Tutorial not passed for game=%s", self.game.game_slug)

        return passed

    def start_run(self, stage: str = "training", initialize_game: bool = True) -> str:
        """Initialize a game run. Call in a background thread before starting tutorial or play."""
        if initialize_game:
            self.game.begin_run()

        self.game.started_at = datetime.now(timezone.utc)
        self._run_id = str(uuid.uuid4())
        self._run_stage = stage
        return self._run_id

    def persist_run_creation(self, stage: str | None = None) -> None:
        """Persist the run creation in DB. Call in a background thread immediately after start_run."""
        if not self._run_id or not self.game.started_at:
            logger.warning("persist_run_creation called before start_run — skipping")
            return
        try:
            create_run(
                run_id=self._run_id,
                user_id=self.game.user_id,
                game_slug=self.game.game_slug,
                stage=stage or self._run_stage,
                started_at=self.game.started_at,
            )
        except Exception as e:
            logger.warning("Failed to persist run creation: %s", e)

    def abort_run(self) -> None:
        """Cancel the current run (player quit before finishing)."""
        if self._run_id:
            abandon_run(self._run_id)
            self._run_id = None

    def finish_run(self, stage: str = "training", status: str = "completed") -> dict:
        """Finalize the run, compute PI, and save all results. Call in a background thread after play is done."""
        metrics = self.game.end_run()

        pi_trials = []
        for idx, trial in enumerate(self.game.trials, 1):
            trial_level = int(trial.stimulus_params.get("level", self.game.level))
            pi_trials.append(
                PITrialResult(
                    trial_number=idx,
                    level=trial_level,
                    is_correct=trial.is_correct,
                    reaction_time_ms=trial.reaction_time_ms,
                    scoring_payload=getattr(trial, "scoring_payload", {}) or {},
                )
            )

        run_result = process_run(
            player_id=self.game.user_id,
            game_slug=self.game.game_slug,
            run_id=self._run_id or "unknown",
            trials=pi_trials,
        )

        if len(self.game.trials) != len(run_result.trials):
            raise RuntimeError(
                f"Trial count mismatch: {len(self.game.trials)} game trials "
                f"vs {len(run_result.trials)} PI trials"
            )
        for game_trial, pi_trial in zip(self.game.trials, run_result.trials):
            game_trial.pi_trial = pi_trial.pi_trial
            game_trial.pi_adjusted = pi_trial.pi_adjusted
            game_trial.accuracy = pi_trial.accuracy
            game_trial.consecutive_bad_count = pi_trial.consecutive_bad_count
            game_trial.consecutive_correct_count = pi_trial.consecutive_correct_count
            game_trial.rt_exceeded_threshold = pi_trial.rt_exceeded_threshold

        normalized_metrics = {
            "avg_reaction_time_ms": metrics.get("avg_reaction_time_ms", 0.0),
            "avg_accuracy": metrics.get("accuracy", 0.0),
            "final_level": self.game.level,
            "total_trials": len(self.game.trials),
            "pi_run": run_result.pi_run,
            "pi_run_normalized_raw": run_result.pi_run_normalized_raw,
            "quality_score": run_result.quality_score,
            "consistency_score": run_result.consistency_score,
        }

        logger.info(
            "Saving run: run_id=%s, game_slug=%s, stage=%s, trials=%d, pi_run=%.2f",
            self._run_id[-12:] if self._run_id else "unknown",
            self.game.game_slug,
            stage,
            len(self.game.trials),
            run_result.pi_run,
        )

        try:
            run_id = save_run(
                user_id=self.game.user_id,
                game_slug=self.game.game_slug,
                stage=stage,
                status=status,
                trials=self.game.trials,
                level=self.game.level,
                started_at=self.game.started_at,
                run_id=self._run_id,
                metrics=normalized_metrics,
            )
            
            if run_id and len(self.game.trials) > 5:
                save_trials(run_id, self.game.game_slug, self.game.trials)

                if stage != "tutorial":
                    try:
                        current = fetch_player_game_stats(self.game.user_id, self.game.game_slug)
                        new_stats = _compute_player_stats_update(
                            current=current,
                            pi_run=run_result.pi_run,
                            avg_accuracy=run_result.avg_accuracy,
                            trial_count=len(self.game.trials),
                            avg_reaction_time_ms=run_result.avg_reaction_time,
                            quality_score=run_result.quality_score,
                            consistency_score=run_result.consistency_score,
                        )
                        upsert_player_game_stats(self.game.user_id, self.game.game_slug, new_stats)
                    except Exception as e:
                        logger.warning("Failed to update player game stats: %s", e)
                    
        except Exception as e:
            logger.exception("Failed to save run: %s", e)

        return {
            **metrics,
            "pi_run": round(run_result.pi_run, 2),
            "pi_run_normalized": round(run_result.pi_run_normalized_raw, 2),
            "quality_score": round(run_result.quality_score, 3),
            "consistency_score": round(run_result.consistency_score, 3),
        }
