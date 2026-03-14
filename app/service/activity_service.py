from datetime import datetime

from PySide6.QtCore import QRunnable, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from app.repository.activity_repository import send_heartbeat, update_time_played
from app.utils.logger import get_logger

"""
ActivityService manages the user activity heartbeats to update the last seen attribute in the database.
"""

_heartbeat_timer: QTimer | None = None
_thread_pool = QThreadPool.globalInstance()
_current_user_id: str | None = None

logger = get_logger(__name__)

class HeartbeatWorker(QRunnable):
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self.setAutoDelete(True)
    
    def run(self):
        send_heartbeat(self.user_id)

def _send_heartbeat_async(user_id: str):
    worker = HeartbeatWorker(user_id)
    _thread_pool.start(worker)
    logger.info("Heartbeat sent for user_id: ..%s", user_id[-10:])

def start_heartbeat(user_id: str):
    if not user_id:
        logger.warning("Heartbeat not started: empty user_id")
        return
    
    global _heartbeat_timer, _time_played, _current_user_id
    _current_user_id = user_id
    _time_played = datetime.now()

    try:
        app_instance = QApplication.instance()
        if app_instance is None:
            logger.warning("QApplication not available for heartbeat (user_id: ..%s)", user_id[-10:])
            return
    except Exception as e:
        logger.warning("Failed to check QApplication instance: %s", e)
        return

    try:
        _heartbeat_timer = QTimer()
        _heartbeat_timer.timeout.connect(lambda: _send_heartbeat_async(user_id))
        
        _send_heartbeat_async(user_id)
        logger.debug("Initial heartbeat sent")

        _heartbeat_timer.start(2000)
        logger.info("Heartbeat started for user (user_id: ..%s)", user_id[-10:])
        
    except Exception as e:
        logger.error("Failed to start heartbeat timer: %s", e)
        _heartbeat_timer = None

def stop_heartbeat():
    global _heartbeat_timer, _current_user_id
    if _heartbeat_timer and _heartbeat_timer.isActive() and _current_user_id:
        elapsed_seconds = int((datetime.now() - _time_played).total_seconds())
        update_time_played(_current_user_id, elapsed_seconds)
        _heartbeat_timer.stop()
        logger.debug("Heartbeat stopped for last user")
    _heartbeat_timer = None
    _current_user_id = None