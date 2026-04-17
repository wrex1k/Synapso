"""
TutorialRepository manages game tutorial completion state in Supabase:
- get_tutorial_completed: check if a user has completed the tutorial for a game
- set_tutorial_completed: mark the tutorial as completed
"""
from datetime import datetime, timezone

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.games.core.base_game import GAME_ID_MAP



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
    """Mark the tutorial as completed for the specified user and game."""
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
