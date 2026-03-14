import threading
from typing import Callable

from PySide6.QtCore import QObject

from app.service.auth_service import sign_out
from app.utils.logger import get_logger
from app.ui.views.register_personal import RegisterPersonal
from app.ui.views.login_auth import LoginAuth

logger = get_logger(__name__)

class LogoutController(QObject):
    
    def __init__(self, view: tuple[LoginAuth, RegisterPersonal], on_logout: Callable, parent=None):
        super().__init__(parent)
        self.view = view
        self.on_logout = on_logout
            
    def logout(self):
        try:
            sign_out()
            self.view[0].reset_ui()
            self.view[1].reset_ui()
            self.on_logout()
            logger.info("Logout successful")
        except Exception as e:
            logger.error("Logout failed: %s", e)