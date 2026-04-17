"""Controller for handling logout UI actions and sign-out flow.
Provides a thin bridge between the authenticated UI state and the authentication service.
"""

from typing import Callable

from PySide6.QtCore import QObject

from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.service.auth_service import sign_out
from app.ui.views.login_auth import LoginAuth
from app.ui.views.register_personal import RegisterPersonal



class LogoutController(QObject):
    """Handle logout interactions and UI reset flow.

    This controller signs the user out, resets related authentication
    views and then forwards control via `on_logout`.
    """

    def __init__(
        self,
        view: tuple[LoginAuth, RegisterPersonal],
        on_logout: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.on_logout = on_logout

    def logout(self):
        """Sign the user out and reset authentication-related UI state.

        On success, both auth views are reset and the `on_logout`
        callback is invoked.
        """
        logger.info("User logout initiated.")

        try:
            sign_out()
            self.view[0].reset_ui()
            self.view[1].reset_ui()
            self.on_logout()
            logger.info("User logged out successfully.")
        except Exception as e:
            logger.exception("Logout failed: %s", e)
