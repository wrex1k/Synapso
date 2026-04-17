"""
StatsRepository manages player performance statistics, leaderboards, and game activity in Supabase:
- fetch_game_stats:         activity counts and aggregate metrics for a game's info panel
- fetch_leaderboard:        ranked player list for a game
- subscribe_leaderboard:    real-time leaderboard change subscription
- fetch_player_game_stats:  a single user's cumulative stats for a game
- upsert_player_game_stats: persist updated cumulative stats for a user/game
- fetch_all_user_stats:     all cumulative stats for a user across every game
"""
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.repository.supabase_client import get_client, with_retry
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.games.core.base_game import GAME_ID_MAP



def _fetch_run_counts(client, game_db_id: int, today_start: str, week_start: str) -> dict:
    """Query the four run-count metrics from the DB."""
    def build_base():
        """Build a fresh base query for each count operation."""
        return client.table("runs").select("run_id", count="exact").eq("game_id", game_db_id).eq("stage", "training")

    total           = (build_base().eq("status", "completed").execute()).count or 0
    games_today     = (build_base().eq("status", "completed").gte("started_at", today_start).execute()).count or 0
    games_this_week = (build_base().eq("status", "completed").gte("started_at", week_start).execute()).count or 0
    players_playing = (build_base().eq("status", "running").execute()).count or 0

    return {
        "total_games": total,
        "games_today": games_today,
        "games_this_week": games_this_week,
        "players_playing": players_playing,
    }


def _fetch_player_stats(client, game_db_id: int) -> list[dict]:
    """Fetch the player_game_stats rows for a game, used to compute leaderboard and averages."""
    res = (
        client.table("player_game_stats")
        .select("user_id, avg_reaction_time_ms, avg_accuracy, quality_average, skill_rating")
        .eq("game_id", game_db_id)
        .execute()
    )
    rows = res.data or []
    for row in rows:
        if "quality_average" in row:
            row["avg_quality"] = row.pop("quality_average")
        if "skill_rating" in row:
            row["elo_rating"] = row.pop("skill_rating")
        q = row.get("avg_quality")
        if q is not None and 0 < q <= 1:
            row["avg_quality"] = q * 100
    return rows


def _avg_and_user_diff(rows: list[dict], field: str, user_id: str | None) -> tuple[float | None, float | None]:
    """Compute the average of the specified field across all rows, and the difference between the user's value and the average."""
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

        avg_quality, quality_diff = _avg_and_user_diff(pgs_rows, "avg_quality", user_id)
        if quality_diff is not None:
            quality_diff = round(quality_diff, 1)

        avg_reaction_time, rt_diff_ms = _avg_and_user_diff(pgs_rows, "avg_reaction_time_ms", user_id)
        acc_rows = [
            {
                "user_id": r["user_id"],
                "avg_accuracy": (r["avg_accuracy"] * 100)
                if r.get("avg_accuracy") is not None
                else None,
            }
            for r in pgs_rows
        ]
        avg_accuracy, acc_diff = _avg_and_user_diff(acc_rows, "avg_accuracy", user_id)

        return {
            **counts,
            "avg_quality": avg_quality,
            "quality_diff": quality_diff,
            "avg_reaction_time_ms": avg_reaction_time,
            "rt_diff_ms": rt_diff_ms,
            "avg_accuracy": avg_accuracy,
            "acc_diff": acc_diff,
        }

    try:
        return with_retry(_fetch)
    except Exception as e:
        logger.warning("Failed to fetch game stats for game_id=%d: %s", game_db_id, e)
        return {
            "players_playing": 0,
            "games_today": 0,
            "games_this_week": 0,
            "total_games": 0,
            "avg_quality": None,
            "quality_diff": None,
            "avg_reaction_time_ms": None,
            "rt_diff_ms": None,
            "avg_accuracy": None,
            "acc_diff": None,
        }


def fetch_leaderboard(game_db_id: int, user_id: str, limit: int | None = None) -> dict:
    """Fetch ranked player list for a game, annotated with online status."""
    def _fetch():
        client = get_client()

        query = (
            client.table("player_game_stats")
            .select("user_id, skill_rating, users!inner(username, avatar_path)")
            .eq("game_id", game_db_id)
            .order("skill_rating", desc=True)
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
            rating_val = row.get("skill_rating", 1000)
            entries.append({
                "user_id": uid,
                "username": user_info.get("username", "Player"),
                "elo_rating": round(float(rating_val) if rating_val else 1000, 0),
                "is_online": uid in online_ids,
                "avatar_path": user_info.get("avatar_path") or "default.webp",
            })
            if uid == user_id:
                user_rank = rank

        return {"entries": entries, "user_rank": user_rank}

    try:
        return with_retry(_fetch)
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
    try:
        if on_loop_ready is not None:
            on_loop_ready(loop)
        loop.run_until_complete(_run())
    except BaseException as exc:
        logger.warning("Realtime listener ended for game_id=%d: %s", game_db_id, exc)
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


def fetch_player_game_stats(user_id: str, game_slug: str) -> dict | None:
    """Fetch the current player_game_stats row, or None if the player has no entry yet."""
    def _fetch():
        game_id = GAME_ID_MAP.get(game_slug, 1)
        client = get_client()
        res = (
            client.table("player_game_stats")
            .select(
                "total_runs, total_trials, best_pi_run, "
                "avg_reaction_time_ms, avg_accuracy, quality_average, "
                "consistency_average, skill_rating"
            )
            .eq("user_id", user_id)
            .eq("game_id", game_id)
            .execute()
        )
        row = res.data[0] if res.data else None
        if row is not None:
            # Rename DB column names to internal keys used throughout the codebase
            if "quality_average" in row:
                row["avg_quality"] = row.pop("quality_average")
            if "consistency_average" in row:
                row["avg_consistency"] = row.pop("consistency_average")
            if "skill_rating" in row:
                row["elo_rating"] = row.pop("skill_rating")
            # Compatibility: pre-backfill rows may store on 0-1 scale
            q = row.get("avg_quality")
            if q is not None and 0 < q <= 1:
                row["avg_quality"] = q * 100
            c = row.get("avg_consistency")
            if c is not None and 0 < c <= 1:
                row["avg_consistency"] = c * 100
        return row
    try:
        return with_retry(_fetch)
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
        client = get_client()
        # Remap internal keys to actual DB column names
        _KEY_MAP = {
            "avg_quality": "quality_average",
            "avg_consistency": "consistency_average",
            "elo_rating": "skill_rating",
        }
        db_data = {_KEY_MAP.get(k, k): v for k, v in data.items()}
        response = (
            client.table("player_game_stats")
            .upsert({"user_id": user_id, "game_id": game_id, **db_data}, on_conflict="user_id,game_id")
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

def fetch_all_user_stats(user_id: str) -> dict:
    """Fetch all cumulative stats for a user across every game they have played."""
    def _fetch():
        client = get_client()
        result = (
            client.table("player_game_stats")
            .select(
                "game_id, total_runs, total_trials, best_pi_run, "
                "avg_reaction_time_ms, avg_accuracy, quality_average, "
                "consistency_average, skill_rating"
            )
            .eq("user_id", user_id)
            .execute()
        )
        rows = result.data or []
        for row in rows:
            # Rename DB column names to internal keys used throughout the codebase
            if "quality_average" in row:
                row["avg_quality"] = row.pop("quality_average")
            if "consistency_average" in row:
                row["avg_consistency"] = row.pop("consistency_average")
            if "skill_rating" in row:
                row["elo_rating"] = row.pop("skill_rating")
            # Compatibility: pre-backfill rows may store on 0-1 scale
            q = row.get("avg_quality")
            if q is not None and 0 < q <= 1:
                row["avg_quality"] = q * 100
            c = row.get("avg_consistency")
            if c is not None and 0 < c <= 1:
                row["avg_consistency"] = c * 100
        return {"games": rows}
    try:
        return with_retry(_fetch)
    except Exception as e:
        logger.warning("Failed to fetch all stats for user=..%s: %s", user_id[-10:], e)
        return {"games": []}