"""Controller for handling the login UI actions and auth flow.
Provides a thin bridge between the `LoginAuth` view and the authentication service.
"""

from typing import Callable

from email_validator import validate_email, EmailNotValidError
from PySide6.QtCore import QObject, Slot

from app.core.registry import registry
from app.utils.logger import logger

from app.service.auth_service import sign_in
from app.utils.validator import validate_password
from translations.translation import get_error_message
from app.ui.views.login_auth import LoginAuth



# pylint: disable=too-few-public-methods
class LoginController(QObject):
    """Handle login interactions from the `LoginAuth` view.

    This controller validates input, performs sign-in on a background
    thread and forwards the result via `on_success`.
    """

    def __init__(self, view: "LoginAuth", on_success: Callable[[str], None], parent=None):
        super().__init__(parent)
        self.view = view
        self.on_success = on_success

        self._operation = registry.operation("login")

        self.view.login_data_submit.connect(self.login)

    def login(self, email: str, password: str):
        """Validate credentials and start background sign-in.

        Displays localized error messages via the view on validation
        or authentication failure.
        """
        try:
            email = validate_email(email.strip(), check_deliverability=False).normalized
        except EmailNotValidError:
            logger.error("Invalid email format: %s", email)
            self.view.show_login_error(get_error_message("invalid_email_format"))
            return

        try:
            validate_password(password)
        except ValueError as e:
            logger.error("Invalid password: %s", e)
            self.view.show_login_error(get_error_message("invalid_password"))
            return

        started = self._operation.start(
            registry.run_thread,
            lambda: sign_in(email, password),
            self._on_login_return,
            name="login-thread",
        )

        if started:
            logger.info("User attempting login with email: %s", email)
            return

    # Handle the authentication result returned from the background thread.
    @Slot(object)
    def _on_login_return(self, user):
        if not user:
            self.view.show_login_error(get_error_message("invalid_credentials"))
            return

        logger.info("User logged in successfully (user_id: ..%s)", user.id[-10:])
        self.on_success(user)
