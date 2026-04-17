from datetime import datetime, timezone

from app.repository.supabase_client import get_client, with_retry
from app.utils.logger import get_logger
from app.games.core.base_game import GAME_ID_MAP

logger = get_logger(__name__)


def get_tutorial_completed(user_id: str, game_slug: str) -> bool:
    """Check if user completed tutorial for game."""
    def _fetch():
        """Query tutorial completion status from database."""
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
    try:
        return with_retry(_fetch)
    except Exception as e:
        logger.warning("Failed to check tutorial status: %s", e)
        return False

def set_tutorial_completed(user_id: str, game_slug: str, run_id: str | None = None):
    """Mark tutorial as completed for user and game."""
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
