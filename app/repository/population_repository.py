from app.repository.supabase_client import get_client
from app.games.core.base_game import GAME_ID_MAP
from app.utils.logger import get_logger

logger = get_logger(__name__)

def fetch_avg_reaction_times(game_slug: str) -> list[float]:
    """Return all reaction time values for game."""
    game_id = GAME_ID_MAP.get(game_slug)
    client = get_client()
    rows = (
        client.table("player_game_stats")
        .select("avg_reaction_time_ms")
        .eq("game_id", game_id)
        .execute()
    ).data or []
    return [r["avg_reaction_time_ms"] for r in rows if r.get("avg_reaction_time_ms") is not None]

def fetch_recent_pi_runs(game_slug: str, limit: int = 2000) -> list[float]:
    """Return PI values from recent completed training runs."""
    game_id = GAME_ID_MAP.get(game_slug)
    client = get_client()
    rows = (
        client.table("runs")
        .select("pi_run")
        .eq("game_id", game_id)
        .eq("status", "completed")
        .eq("stage", "training")
        .order("ended_at", desc=True)
        .limit(limit)
        .execute()
    ).data or []
    return [r["pi_run"] for r in rows if r.get("pi_run") is not None]
