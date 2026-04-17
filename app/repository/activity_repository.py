from datetime import datetime, timezone

from app.repository.supabase_client import get_client, with_retry, refresh_session
from app.utils.logger import get_logger

logger = get_logger(__name__)

def send_heartbeat(user_id: str, elapsed_seconds: int):
    """Send user activity heartbeat to update last seen and time played."""
    if not user_id:
        logger.warning("Heartbeat skipped: no user_id provided")
        return

    try:
        refresh_session()

        def _do_heartbeat():
            """Execute heartbeat upsert operation."""
            data = {
                "user_id": user_id,
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "time_played": get_time_played(user_id) + elapsed_seconds,
            }
            return get_client().table("user_activity").upsert(
                data,
                on_conflict="user_id",
            ).execute()

        result = with_retry(_do_heartbeat)
        
        if result.data:
            logger.debug("Heartbeat sent successfully (user_id: ..%s)", user_id[-10:])
        else:
            logger.debug("Heartbeat upsert executed (user_id: ..%s)", user_id[-10:])

    except Exception as e:
        logger.exception("Failed to send heartbeat (user_id: ..%s): %s", user_id[-10:], str(e))

def get_time_played(user_id: str) -> int:
    """Retrieve total time played for user."""
    data = with_retry(
        lambda: get_client().table("user_activity")
        .select("time_played")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    try:
        time_played = data.data[0]["time_played"]
        if time_played is None:
            time_played = 0
        logger.debug("Retrieved time_played=%s for user_id=%s", time_played, user_id[-10:])
    except Exception:
        logger.warning("Failed to parse time_played (user_id=%s)", user_id[-10:])
        return 0
    return time_played