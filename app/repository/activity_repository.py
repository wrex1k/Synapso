from datetime import datetime, timezone

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

"""
ActivityRepository provides functions to manage user activity heartbeats to update last seen attribute:
- send_heartbeat: updates the last seen timestamp for a user in the database,
- get_user_activity: checks if the user is currently active based on the last seen timestamp.
"""

logger = get_logger(__name__)

def send_heartbeat(user_id: str, elapsed_seconds: int):
    if not user_id:
        logger.warning("Heartbeat skipped: no user_id provided")
        return

    try:
        data = {
            "user_id": user_id,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "time_played": get_time_played(user_id) + elapsed_seconds,
        }
        
        result = get_client().table("user_activity").upsert(
            data,
            on_conflict="user_id",
        ).execute()
        
        if result.data:
            logger.debug("Heartbeat sent successfully (user_id: ..%s)", user_id[-10:])
        else:
            logger.debug("Heartbeat upsert executed (user_id: ..%s)", user_id[-10:])

    except Exception as e:
        logger.exception("Failed to send heartbeat (user_id: ..%s): %s", user_id[-10:], str(e))


def get_user_activity(user_id: str) -> bool:
    if not user_id:
        logger.debug("Activity check skipped: empty user_id")
        return False

    data = (
        get_client().table("user_activity")
        .select("last_seen")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not data.data:
        logger.debug("No activity row for user_id=%s", user_id[-10:])
        return False

    try:
        last_seen = datetime.fromisoformat(data.data[0]["last_seen"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        is_active = (now - last_seen).total_seconds() < 30
    except Exception:
        logger.warning("Failed to parse last_seen (user_id=%s)", user_id[-10:])
        return False

    return is_active

def get_time_played(user_id: str) -> int:
    data = (
        get_client().table("user_activity")
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

def update_time_played(user_id: str, seconds: int):
    try:
        current_time_played = get_time_played(user_id)
        new_time_played = current_time_played + seconds

        result = get_client().table("user_activity").upsert(
            {
                "user_id": user_id,
                "time_played": new_time_played,
            },
            on_conflict="user_id",
        ).execute()

        if result.data:
            logger.info("Updated time_played to %s for user_id=%s", new_time_played, user_id[-10:])
        else:
            logger.debug("Time played upsert executed (user_id: ..%s)", user_id[-10:])

    except Exception as e:
        logger.exception("Failed to update time_played (user_id=%s): %s", user_id[-10:], str(e))