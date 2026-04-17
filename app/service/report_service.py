from app.utils.logger import get_logger
from app.repository.report_repository import save_report

logger = get_logger(__name__)

def submit_report(user_id: str, body: str) -> bool:
    """Submit a user report to the database."""
    if not body:
        logger.debug("Empty report skipped")
        return False

    try:
        response = save_report(user_id, body)
        if response:
            logger.info("Report saved via service")
        else:
            logger.warning("Report save failed via repository")
        return response

    except Exception as e:
        logger.exception("Report service exception: %s", e)
        return False
