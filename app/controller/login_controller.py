from typing import Callable

from email_validator import validate_email, EmailNotValidError
from PySide6.QtCore import QObject, Slot

from app.core.registry import registry
from app.utils.logger import get_logger

logger = get_logger(__name__)

from app.service.auth_service import sign_in
from app.utils.validator import validate_password
from translations.translation import get_error_message
from app.ui.views.login_auth import LoginAuth

class LoginController(QObject):
    """Controller responsible for managing user login and authentication."""

    def __init__(self, view: "LoginAuth", on_success: Callable[[str], None], parent=None):
        super().__init__(parent)
        self.view = view
        self.on_success = on_success

        self._operation = registry.operation("login")

        self.view.login_data_submit.connect(self.login)

    def login(self, email: str, password: str):
        """Validate credentials and start background sign-in if no operation is running."""
        try:
            email = validate_email(email.strip(), check_deliverability=False).normalized
        except EmailNotValidError:
            logger.error("Invalid email format: %s", email)
            self.view.show_login_error(get_error_message("invalid_email_format"))
            return

        err = validate_password(password)
        if err:
            self.view.show_login_error(err)
            return

        started = self._operation.start(
            registry.run_thread,
            lambda: sign_in(email, password),
            self._on_login_return,
            name="login-thread",
        )

        if started:
            logger.info("User attempting login with email: %s", email)
        else:
            logger.warning("Login operation already running, ignoring request for email: %s", email)

    @Slot(object)
    def _on_login_return(self, user):
        """Handle sign-in result and invoke success callback or display error."""
        if not user:
            self.view.show_login_error(get_error_message("invalid_credentials"))
            return

        logger.info("User logged in successfully (user_id: ..%s)", user.id[-10:])
        self.on_success(user)

    def cleanup(self) -> None:
        """Cancel any running login operation."""
        self._operation.cancel()
