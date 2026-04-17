"""
GameRepository manages the games catalog in Supabase:
- fetch_games: return all active games ordered by id
"""
from app.repository.supabase_client import get_client, with_retry
from app.utils.logger import get_logger

logger = get_logger(__name__)



def fetch_games() -> list[dict]:
    """Return all active games, ordered by id."""
    def _fetch():
        result = (
            get_client()
            .table("games")
            .select("id, name, is_active")
            .order("id")
            .execute()
        )
        return [g for g in (result.data or []) if g.get("is_active")]
    try:
        games = with_retry(_fetch)
        logger.debug("Active games are: %s", ", ".join(g["name"] for g in games))
        return games
    except Exception as e:
        logger.warning("Failed to fetch games list: %s", e)
        return []
