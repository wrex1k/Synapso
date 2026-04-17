"""
GameRepository provides functions to manage game data in Supabase:
- save_run:                save a completed game run with aggregate metrics
- get_tutorial_completed:  check if a user has completed the tutorial for a game
- set_tutorial_completed:  mark the tutorial as completed
"""
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import uuid

from app.repository.supabase_client import get_client, get_service_client, reset_client
from app.utils.logger import get_logger
from app.games.core.base_game import GAME_ID_MAP

logger = get_logger(__name__)


_RETRIABLE = ("Server disconnected", "ConnectionTerminated", "Connection reset", "JSON could not be generated")


def _with_retry(fn):
    """Call fn(). On transient HTTP/2 or connection errors, reset the client and retry once."""
    try:
        return fn()
    except Exception as e:
        err = str(e)
        if any(marker in err for marker in _RETRIABLE):
            logger.debug("Transient connection error (%s) — resetting client and retrying once", err)
            reset_client()
            return fn()
        raise


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


def get_tutorial_completed(user_id: str, game_slug: str) -> bool:
    """Check if the user has completed the tutorial for the specified game."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)

        result = (
            get_client()
            .table("game_tutorials")
            .select("completed")
            .eq("user_id", user_id)
            .eq("game_id", game_id)
            .limit(1)
            .execute()
        )

        if result.data:
            return bool(result.data[0].get("completed", False))
        return False

    except Exception as e:
        logger.warning("Failed to check tutorial status: %s", e)
        return False


def set_tutorial_completed(user_id: str, game_slug: str, run_id: str | None = None):
    """"Mark the tutorial as completed for the specified user and game."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)

        payload = {
            "user_id": user_id,
            "game_id": game_id,
            "run_id": run_id,
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        client = get_client()
        client.table("game_tutorials").upsert(
            payload,
            on_conflict="user_id,game_id",
        ).execute()

        logger.info(
            "Tutorial completed and saved to DB: game_slug=%s, user=..%s",
            game_slug, user_id[-10:],
        )

    except Exception as e:
        logger.exception("Failed to mark tutorial complete for game=%s: %s", game_slug, e)


def fetch_games() -> list[dict]:
    try:
        result = (
            get_client()
            .table("games")
            .select("id, name, description, is_active")
            .order("id")
            .execute()
        )
        active = [g for g in (result.data or []) if g.get("is_active")]
        logger.debug("Active games are: %s", ", ".join(game["name"] for game in active))
        return active
    except Exception as e:
        logger.warning("Failed to fetch games list: %s", e)
        return []


def _fetch_run_counts(client, game_db_id: int, today_start: str, week_start: str) -> dict:
    """Query the four run-count metrics from the DB."""
    base = client.table("runs").select("run_id", count="exact").eq("game_id", game_db_id).eq("stage", "training")

    total          = (base.eq("status", "completed").execute()).count or 0
    games_today    = (base.eq("status", "completed").gte("started_at", today_start).execute()).count or 0
    games_this_week = (base.eq("status", "completed").gte("started_at", week_start).execute()).count or 0
    players_playing = (base.eq("status", "running").execute()).count or 0

    return {
        "total_games": total,
        "games_today": games_today,
        "games_this_week": games_this_week,
        "players_playing": players_playing,
    }


def _fetch_player_stats(client, game_db_id: int) -> list[dict]:
    """ Fetch the player_game_stats rows for a game, used to compute leaderboard and averages."""
    res = (
        client.table("player_game_stats")
        .select("user_id, accumulated_pi, avg_reaction_time_ms, avg_accuracy_overall")
        .eq("game_id", game_db_id)
        .execute()
    )
    return res.data or []


def _avg_and_user_diff(rows: list[dict], field: str, user_id: str | None) -> tuple[float | None, float | None]:
    """ Compute the average of the specified field across all rows, and the difference between the user's value and the average."""
    if not user_id:
        values = [r[field] for r in rows if r.get(field) is not None]
        return (sum(values) / len(values) if values else None), None

    other_values = [r[field] for r in rows if r.get(field) is not None and r.get("user_id") != user_id]
    others_avg = sum(other_values) / len(other_values) if other_values else None

    user_values = [r[field] for r in rows if r.get(field) is not None and r.get("user_id") == user_id]
    if not user_values or others_avg is None:
        return others_avg, None

    return others_avg, sum(user_values) / len(user_values) - others_avg


def fetch_game_stats(game_db_id: int, user_id: str | None = None) -> dict:
    """Fetch activity counts and aggregate metrics for a game."""
    def _fetch():
        client = get_client()
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        counts = _fetch_run_counts(client, game_db_id, today_start, week_start)
        pgs_rows = _fetch_player_stats(client, game_db_id)

        avg_score, score_diff = _avg_and_user_diff(pgs_rows, "accumulated_pi", user_id)
        if score_diff is not None:
            score_diff = round(score_diff, 2)

        avg_reaction_time, rt_diff_ms = _avg_and_user_diff(pgs_rows, "avg_reaction_time_ms", user_id)
        acc_rows = [
            {
                "user_id": r["user_id"],
                "avg_accuracy": (r["avg_accuracy_overall"] * 100)
                if r.get("avg_accuracy_overall") is not None
                else None,
            }
            for r in pgs_rows
        ]
        avg_accuracy, acc_diff = _avg_and_user_diff(acc_rows, "avg_accuracy", user_id)

        return {
            **counts,
            "avg_score": avg_score,
            "score_diff": score_diff,
            "avg_reaction_time_ms": avg_reaction_time,
            "rt_diff_ms": rt_diff_ms,
            "avg_accuracy": avg_accuracy,
            "acc_diff": acc_diff,
        }

    try:
        return _with_retry(_fetch)
    except Exception as e:
        logger.warning("Failed to fetch game stats for game_id=%d: %s", game_db_id, e)
        return {
            "players_playing": 0,
            "games_today": 0,
            "games_this_week": 0,
            "total_games": 0,
            "avg_score": None,
            "score_diff": None,
            "avg_reaction_time_ms": None,
            "rt_diff_ms": None,
            "avg_accuracy": None,
            "acc_diff": None,
        }


def fetch_leaderboard(game_db_id: int, user_id: str, limit: int | None = None) -> dict:
    def _fetch():
        client = get_client()

        query = (
            client.table("player_game_stats")
            .select("user_id, accumulated_pi, users!inner(username, avatar_path)")
            .eq("game_id", game_db_id)
            .order("accumulated_pi", desc=True)
        )
        if limit is not None:
            query = query.limit(limit)

        res = query.execute()
        data = res.data or []
        if not data:
            return {"entries": [], "user_rank": None}

        user_ids = [row["user_id"] for row in data if row.get("user_id")]
        online_ids: set[str] = set()
        if user_ids:
            try:
                threshold = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
                act_res = (
                    client.table("user_activity")
                    .select("user_id")
                    .in_("user_id", user_ids)
                    .gte("last_seen", threshold)
                    .execute()
                )
                online_ids = {r["user_id"] for r in (act_res.data or [])}
            except Exception as exc:
                logger.debug("Could not fetch online status for leaderboard: %s", exc)

        entries = []
        user_rank = None
        for rank, row in enumerate(data, 1):
            uid = row["user_id"]
            user_info = row.get("users") or {}
            pi_val = row.get("accumulated_pi", 0.0)
            entries.append({
                "user_id": uid,
                "username": user_info.get("username", "Player"),
                "accumulated_pi": round(float(pi_val) if pi_val else 0.0, 2),
                "is_online": uid in online_ids,
                "avatar_path": user_info.get("avatar_path") or "default.webp",
            })
            if uid == user_id:
                user_rank = rank

        return {"entries": entries, "user_rank": user_rank}

    try:
        return _with_retry(_fetch)
    except Exception as e:
        logger.warning("Failed to fetch leaderboard for game_id=%d: %s", game_db_id, e)
        return {"entries": [], "user_rank": None}


def subscribe_leaderboard(
    game_db_id: int,
    on_change: Callable,
    on_loop_ready: Callable | None = None,
) -> None:
    """Subscribe to real-time changes in player_game_stats for the specified game, and call on_change() when a change is detected."""
    import asyncio
    from app.repository.supabase_client import create_realtime_client

    async def _run() -> None:
        client = await create_realtime_client()
        channel = client.channel(f"pgs-game-{game_db_id}")

        def _handle_realtime_change(payload: dict | None) -> None:
            logger.debug("Realtime raw payload for game_id=%d: %s", game_db_id, payload)
            data = (payload or {}).get("data") or {}
            event_type = data.get("type")
            if event_type not in ("INSERT", "UPDATE"):
                logger.debug("Realtime event ignored (type=%r)", event_type)
                return
            logger.info("Realtime leaderboard change detected (type=%s, game_id=%d) — refreshing", event_type, game_db_id)
            on_change()

        logger.info("Realtime: subscribing to player_game_stats for game_id=%d", game_db_id)
        await channel.on_postgres_changes(
            event="*",
            schema="public",
            table="player_game_stats",
            filter=f"game_id=eq.{game_db_id}",
            callback=_handle_realtime_change,
        ).subscribe()

        realtime = client.realtime
        listen_task = getattr(realtime, "_listen_task", None)
        if listen_task is not None:
            logger.info("Realtime: subscription active for game_id=%d, listening...", game_db_id)
            await listen_task
        else:
            logger.warning("Realtime: no _listen_task found for game_id=%d, falling back to Event", game_db_id)
            await asyncio.Event().wait()
        logger.warning("Realtime: listen() returned unexpectedly for game_id=%d", game_db_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if on_loop_ready is not None:
        on_loop_ready(loop)
    try:
        loop.run_until_complete(_run())
    except Exception as exc:
        logger.debug("Realtime listener ended for game_id=%d: %s", game_db_id, exc)
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        loop.close()


def fetch_pi_normalized_raw_values(game_slug: str) -> list[float]:
    """Return all pi_run_normalized_raw values for completed runs of the given game."""
    try:
        from app.repository.supabase_client import get_client
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


def fetch_player_game_stats(user_id: str, game_slug: str) -> dict | None:
    """Fetch the current player_game_stats row, or None if the player has no entry yet."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_service_client() or get_client()
        res = (
            client.table("player_game_stats")
            .select(
                "accumulated_pi, total_runs, total_trials, best_pi_run, "
                "avg_reaction_time_ms, avg_accuracy_overall, quality_average, consistency_average"
            )
            .eq("user_id", user_id)
            .eq("game_id", game_id)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.warning(
            "Failed to fetch player_game_stats for user=..%s, game_slug=%s: %s",
            user_id[-10:], game_slug, e,
        )
        return None


def upsert_player_game_stats(user_id: str, game_slug: str, data: dict) -> dict | None:
    """Upsert the player_game_stats row for the user and game with the provided data, returning the new row or None on failure."""
    try:
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_service_client() or get_client()
        response = (
            client.table("player_game_stats")
            .upsert({"user_id": user_id, "game_id": game_id, **data}, on_conflict="user_id,game_id")
            .execute()
        )
        logger.debug("player_game_stats upserted: user=..%s, game_slug=%s", user_id[-10:], game_slug)
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(
            "Failed to upsert player_game_stats for user=..%s, game_slug=%s: %s",
            user_id[-10:], game_slug, e,
        )
        return None