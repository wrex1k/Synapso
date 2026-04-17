"""
GameRepository manages the games catalog in Supabase:
- fetch_games: return all active games ordered by id
"""
from app.repository.supabase_client import get_client
from app.utils.logger import logger



def fetch_games() -> list[dict]:
    """Return all active games, ordered by id."""
    try:
        result = (
            get_client()
            .table("games")
            .select("id, name, is_active")
            .order("id")
            .execute()
        )
        active = [g for g in (result.data or []) if g.get("is_active")]
        logger.debug("Active games are: %s", ", ".join(game["name"] for game in active))
        return active
    except Exception as e:
        logger.warning("Failed to fetch games list: %s", e)
        return []
