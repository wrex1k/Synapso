import re
from typing import Callable

from email_validator import validate_email, EmailNotValidError

from PySide6.QtCore import QObject, Slot

from app.core.registry import registry
from app.service.auth_service import sign_in
from app.utils.logger import get_logger
from app.utils.validator import validate_password
from translations.translation import get_error_message
from app.ui.views.login_auth import LoginAuth

logger = get_logger(__name__)

class LoginController(QObject):
    def __init__(self, view: "LoginAuth", on_success: Callable[[str], None], parent=None):
        super().__init__(parent)
        self.view = view
        self.on_success = on_success

        self._operation = registry.operation("login")

        self.view.login_data_submit.connect(self.login)

    # log in the user with email and password
    def login(self, email: str, password: str):
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
            logger.debug("Login operation started for email: %s", email)
            return

    # process the result of the login attempt, handling success and failure cases
    @Slot(object)
    def _on_login_return(self, user):
        if not user:
            self.view.show_login_error(get_error_message("invalid_credentials"))  
            return

        logger.debug("Login success (user_id: ..%s)", user.id[-10:])
        self.on_success(user)