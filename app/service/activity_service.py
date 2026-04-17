from datetime import datetime

from PySide6.QtCore import QTimer

from app.core.registry import registry
from app.repository.activity_repository import send_heartbeat
from app.utils.logger import get_logger
from app.utils.breadcrumbs import add_breadcrumb

logger = get_logger(__name__)

"""
ActivityService manages the user activity heartbeats to update the last seen attribute in the database.
"""

_heartbeat_timer: QTimer | None = None
_current_user_id: str | None = None
_last_tick: datetime | None = None
_heartbeat_op = registry.operation("heartbeat")


def _tick(user_id: str):
    global _last_tick
    now = datetime.now()
    elapsed = int((now - _last_tick).total_seconds()) if _last_tick else 0
    _last_tick = now
    _heartbeat_op.start(registry.run_thread, lambda: send_heartbeat(user_id, elapsed), None)


def start_heartbeat(user_id: str):
    if not user_id:
        logger.warning("Heartbeat not started: empty user_id")
        return

    global _heartbeat_timer, _current_user_id, _last_tick
    _current_user_id = user_id
    _last_tick = datetime.now()

    try:
        _heartbeat_timer = QTimer()
        _heartbeat_timer.timeout.connect(lambda: _tick(user_id))

        send_heartbeat(user_id, 0)

        # Start timer to send heartbeat every 30 seconds
        _heartbeat_timer.start(30000)
        logger.info("Heartbeat started for user (user_id: ..%s)", user_id[-10:])
        add_breadcrumb("heartbeat", "Heartbeat started", user_id=user_id[-10:])

    except Exception as e:
        logger.error("Failed to start heartbeat timer: %s", e)
        _heartbeat_timer = None


def flush_heartbeat():
    """Force-send accumulated time immediately (e.g. at game boundaries)."""
    if _current_user_id:
        _tick(_current_user_id)


def stop_heartbeat():
    global _heartbeat_timer, _current_user_id, _last_tick
    if _heartbeat_timer and _heartbeat_timer.isActive() and _current_user_id:
        elapsed = int((datetime.now() - _last_tick).total_seconds()) if _last_tick else 0
        send_heartbeat(_current_user_id, elapsed)
        _heartbeat_timer.stop()
        logger.info("Heartbeat stopped")
        add_breadcrumb("heartbeat", "Heartbeat stopped")
    _heartbeat_timer = None
    _current_user_id = None
    _last_tick = None