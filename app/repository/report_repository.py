from datetime import datetime, timezone

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

def save_report(user_id: str, body: str) -> bool:
    """Save user report to database."""
    try:
        data = {
            "user_id": user_id,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        res = get_client().table("reports").insert(data).execute()
        if getattr(res, "error", None):
            logger.error("Failed to save report: %s", res.error)
            return False

        logger.info("Saved report")
        return True

    except Exception as exc:
        logger.exception("Exception while saving report: %s", exc)
        return False
