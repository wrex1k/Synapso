"""
RunRepository manages game run and trial data in Supabase:
- create_run:                     create a new run and return its ID
- abandon_run:                    mark a run as abandoned
- save_run:                       finalize a run with aggregate metrics
- save_trials:                    persist individual trial rows
- fetch_pi_run_values:            raw PI run values for normalization
- fetch_pi_normalized_raw_values: normalized PI values for normalization
- fetch_user_run_history:         recent completed runs for a user/game
"""
from datetime import datetime, timezone
import uuid

from app.repository.supabase_client import get_client, get_service_client, with_retry
from app.utils.logger import logger
from app.games.core.base_game import GAME_ID_MAP



def create_run(user_id: str, game_slug: str, stage: str, started_at: datetime):
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)

        logger.debug(
            "create_run: game_slug=%s, user=..%s, stage=%s",
            game_slug, user_id[-10:], stage,
        )

        payload = {
            "user_id": user_id,
            "game_id": game_id,
            "stage": stage,
            "started_at": started_at.isoformat(),
            "status": "running",
        }

        client = get_client()
        result = client.table("runs").insert(payload).execute()

        if result.data:
            logger.info("Run created: run_id=%s, game_slug=%s, stage=%s", result.data[0]["run_id"], game_slug, stage)

        return result.data[0]["run_id"] if result.data else None

    except Exception as e:
        logger.exception("Failed to create run: %s", e)
        return None


def abandon_run(run_id: str) -> None:
    """Mark a run as abandoned in the database."""
    try:
        get_client().table("runs").update({
            "status": "abandoned",
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }).eq("run_id", run_id).execute()
        logger.info("Run abandoned: run_id=%s", run_id)
    except Exception as e:
        logger.warning("Failed to mark run abandoned %s: %s", run_id, e)


def save_run(
    user_id: str,
    game_slug: str,
    stage: str,
    status: str,
    trials: list,
    level: int,
    metrics: dict,
    started_at: datetime | None = None,
    run_id: str | None = None,
) -> str | None:
    """Save a completed game run with aggregate metrics."""
    try:
        effective_run_id = run_id or str(uuid.uuid4())

        game_id = GAME_ID_MAP.get(game_slug, 1)

        stage_normalized = stage.lower()
        if stage_normalized not in ("tutorial", "training"):
            stage_normalized = "training"

        status_normalized = (status or "completed").lower()
        if status_normalized not in ("completed", "abandoned"):
            status_normalized = "completed"

        now = datetime.now(timezone.utc)
        update_data = {
            "ended_at": now.isoformat(),
            "pi_run": metrics.get("pi_run", 0.0),
            "pi_run_normalized_raw": metrics.get("pi_run_normalized_raw", 0.0),
            "final_level": metrics.get("final_level", 1),
            "avg_reaction_time_ms": metrics.get("avg_reaction_time_ms"),
            "avg_accuracy": metrics.get("avg_accuracy"),
            "total_trials": metrics.get("total_trials", len(trials)),
            "quality_score": metrics.get("quality_score", 0.0),
            "consistency_score": metrics.get("consistency_score", 0.0),
            "status": status_normalized,
        }

        client = get_client()

        if run_id:
            result = client.table("runs").update(update_data).eq("run_id", effective_run_id).execute()

            if result.data and len(result.data) > 0:
                logger.debug("Run UPDATE successful: run_id=%s", effective_run_id)
            else:
                logger.debug("Run UPDATE matched 0 rows, using UPSERT fallback: run_id=%s", effective_run_id)
                upsert_data = {
                    "run_id": effective_run_id,
                    "user_id": user_id,
                    "game_id": game_id,
                    "stage": stage_normalized,
                    "started_at": (started_at or now).isoformat(),
                    **update_data,
                }
                result = client.table("runs").upsert(upsert_data, on_conflict="run_id").execute()
        else:
            insert_data = {
                "run_id": effective_run_id,
                "user_id": user_id,
                "game_id": game_id,
                "stage": stage_normalized,
                "started_at": (started_at or now).isoformat(),
                **update_data,
            }
            result = client.table("runs").insert(insert_data).execute()

        logger.debug("Run saved: game_slug=%s, stage=%s", game_slug, stage_normalized)
        return effective_run_id

    except Exception as e:
        logger.exception("Failed to save run for game=%s, run_id=%s: %s", game_slug, run_id, e)
        return None


def save_trials(run_id: str, game_slug: str, trials: list) -> None:
    """Save individual trial data for a completed run."""
    if not trials:
        return

    game_id = GAME_ID_MAP.get(game_slug, 1)

    logger.debug(
        "save_trials: run_id=%s, game_slug=%s, trial_count=%d",
        run_id, game_slug, len(trials),
    )

    try:
        rows = []
        for i, trial in enumerate(trials):
            cur_level = trial.stimulus_params.get("level", 1)

            if i + 1 < len(trials):
                next_level = trials[i + 1].stimulus_params.get("level", cur_level)
                if next_level > cur_level:
                    action = "level_up"
                elif next_level < cur_level:
                    action = "level_down"
                else:
                    action = "continue"
            else:
                action = "end"

            base_row = {
                "run_id": run_id,
                "game_id": game_id,
                "trial_number": i + 1,
                "difficulty_level": cur_level,
                "reaction_time_ms": int(trial.reaction_time_ms),
                "correct": trial.is_correct,
                "adaptive_action": action,
                "stimulus_payload": getattr(trial, "stimulus_payload", {}) or {},
                "response_payload": getattr(trial, "response_payload", {}) or {},
                "scoring_payload": getattr(trial, "scoring_payload", {}) or {},
            }

            if hasattr(trial, "pi_trial") and trial.pi_trial is not None:
                base_row["pi_trial"] = trial.pi_trial
            if hasattr(trial, "pi_adjusted") and trial.pi_adjusted is not None:
                base_row["pi_adjusted"] = trial.pi_adjusted
            if hasattr(trial, "accuracy") and trial.accuracy is not None:
                base_row["accuracy"] = trial.accuracy
            if hasattr(trial, "consecutive_bad_count"):
                base_row["consecutive_bad_count"] = trial.consecutive_bad_count
            if hasattr(trial, "consecutive_correct_count"):
                base_row["consecutive_correct_count"] = trial.consecutive_correct_count
            if hasattr(trial, "rt_exceeded_threshold"):
                base_row["rt_exceeded_threshold"] = trial.rt_exceeded_threshold

            rows.append(base_row)

        client = get_service_client() or get_client()
        result = client.table("trials").insert(rows).execute()
        logger.debug("save_trials: result.data length=%d", len(result.data) if result.data else 0)
        logger.info("Saved %d trials to trials table for run=%s", len(rows), run_id)

    except Exception as e:
        logger.exception("Failed to save trials for run=%s: %s", run_id, e)


def fetch_pi_normalized_raw_values(game_slug: str) -> list[float]:
    """Return all pi_run_normalized_raw values for completed runs of the given game."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_client()
        if not client:
            return []
        result = (
            client.table("runs")
            .select("pi_run_normalized_raw")
            .eq("game_id", game_id)
            .eq("status", "completed")
            .execute()
        )
        return [
            r["pi_run_normalized_raw"]
            for r in (result.data or [])
            if r.get("pi_run_normalized_raw") is not None
        ]
    except Exception as e:
        logger.warning("Failed to fetch pi_run_normalized_raw values for '%s': %s", game_slug, e)
        return []


def fetch_pi_run_values(game_slug: str) -> list[float]:
    """Return all pi_run values for completed runs of the given game."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_client()
        if not client:
            return []
        result = (
            client.table("runs")
            .select("pi_run")
            .eq("game_id", game_id)
            .eq("status", "completed")
            .execute()
        )
        return [
            r["pi_run"]
            for r in (result.data or [])
            if r.get("pi_run") is not None
        ]
    except Exception as e:
        logger.warning("Failed to fetch pi_run values for '%s': %s", game_slug, e)
        return []
    
def fetch_user_run_history(user_id: str, game_slug: str, limit: int = 20) -> list[dict]:
    """Return the most recent completed runs for a user and game, in chronological order."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_client()
        result = (
            client.table("runs")
            .select(
                "run_id, started_at, ended_at, pi_run, pi_run_normalized_raw, "
                "final_level, avg_reaction_time_ms, avg_accuracy, total_trials, "
                "quality_score, consistency_score"
            )
            .eq("user_id", user_id)
            .eq("game_id", game_id)
            .eq("status", "completed")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = result.data or []
        return list(reversed(rows))
    except Exception as e:
        logger.warning(
            "Failed to fetch run history for user=..%s, game_slug=%s: %s",
            user_id[-10:], game_slug, e,
        )
        return []
