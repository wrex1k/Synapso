import datetime
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot
from translations.translation import get_error_message

from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.core.registry import registry

from app.repository.user_repository import check_username_exists
from app.utils.validator import validate_password, validate_email, validate_username, validate_birthdate
from app.service.auth_service import sign_up
from app.service.user_service import complete_registration
from app.ui.views.register_auth import RegisterAuth
from app.ui.views.register_personal import RegisterPersonal
from app.models.user import User
from app.utils.error_codes import AuthError



class RegistrationController(QObject):
    """Controller responsible for managing the two-step user registration flow."""

    register_success = Signal(object)
    register_failed = Signal(str)
    register_personal_error = Signal(str)
    personal_check_passed = Signal()
    personal_check_failed = Signal(str)

    def __init__(
        self,
        view: tuple[RegisterPersonal, RegisterAuth],
        on_complete: Callable[[User], None],
        on_back_to_login: Callable[[], None],
        on_back_to_personal: Callable[[], None],
        on_next_to_auth: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self._personal_view, self._auth_view = view
        self.on_complete = on_complete
        self.on_back_to_login = on_back_to_login
        self.on_back_to_personal = on_back_to_personal
        self.on_next_to_auth = on_next_to_auth

        self._operation = registry.operation("registration")
        self._check_operation = registry.operation("username-check")

        self.register_success.connect(self._finish_success)
        self.register_failed.connect(self._finish_error)
        self.register_personal_error.connect(self._finish_personal_error)
        self.personal_check_passed.connect(self._on_personal_check_passed)
        self.personal_check_failed.connect(self._on_personal_check_failed)

        self._draft = User()

        self._connect_signals()

    def _connect_signals(self):
        """Connect registration view signals to controller handlers."""
        self._personal_view.back_to_login_signal.connect(self._back_to_login)
        self._auth_view.back_to_personal_signal.connect(self._back_to_personal)

        self._personal_view.personal_data_submit.connect(self._on_personal_data)
        self._auth_view.auth_data_submit.connect(self._on_auth_data)

    def _on_personal_data(
        self,
        username: str,
        email: str,
        birthday_date: datetime.date,
        avatar_blob: bytes,
    ):
        """Validate personal data and start async username availability check."""
        logger.debug(
            "User submitting personal data during registration (username: %s)",
            username,
        )

        err = validate_username(username)
        if err:
            self._personal_view.show_personal_error(err)
            return

        err = validate_email(email)
        if err:
            self._personal_view.show_personal_error(err)
            return

        err = validate_birthdate(birthday_date)
        if err:
            self._personal_view.show_personal_error(err)
            return

        started = self._check_operation.start(
            registry.run_thread,
            lambda: self._check_and_advance(
                username,
                email,
                birthday_date,
                avatar_blob,
            ),
            name="username-check-thread",
        )

        if not started:
            logger.warning("Username check operation already running, ignoring request")
            return

        self._personal_view.show_checking_state()

    def _check_and_advance(
        self,
        username: str,
        email: str,
        birthday_date: datetime.date,
        avatar_blob: bytes,
    ):
        """Check username uniqueness and store personal data draft."""
        try:
            if check_username_exists(username):
                self.personal_check_failed.emit(
                    get_error_message("username_already_taken")
                )
                return
        except Exception as e:
            logger.error("Username check error: %s", e)
            self.personal_check_failed.emit(
                "Could not verify username, please try again"
            )
            return

        self._draft.username = username
        self._draft.email = email
        self._draft.birthday_date = birthday_date
        self._draft.avatar_blob = avatar_blob
        self.personal_check_passed.emit()

    def _on_auth_data(self, password: str):
        """Start async registration after auth data submission."""
        logger.debug("User submitting auth data during registration")

        started = self._operation.start(
            registry.run_thread,
            lambda: self._do_register(password),
            name="registration-thread",
        )

        if not started:
            logger.warning("Registration operation already running, ignoring request")

    def _do_register(self, password: str):
        """Validate credentials, sign the user up and persist profile data."""
        password = password.strip()
        err = validate_password(password)
        if err:
            self.register_failed.emit(err)
            return

        try:
            auth_user = sign_up(self._draft.email.strip(), password)
            
            completed_user = complete_registration(
                self._draft,
                auth_user.id,
                self._draft.avatar_blob
            )
            
            self.register_success.emit(completed_user)

        except Exception as e:
            error_str = str(e)
            logger.error("Registration error: %s", e)

            if error_str == AuthError.USER_ALREADY_REGISTERED:
                self.register_personal_error.emit(
                    get_error_message("user_already_registered")
                )
                return
            
            if error_str == AuthError.EMAIL_ALREADY_IN_USE:
                self.register_personal_error.emit(
                    get_error_message("email_already_in_use")
                )
                return
            
            if error_str == AuthError.USERNAME_ALREADY_TAKEN:
                self.register_personal_error.emit(
                    get_error_message("username_already_taken")
                )
                return
            
            error_lower = error_str.lower()
            if (
                "duplicate" in error_lower
                or "already exists" in error_lower
                or "unique constraint" in error_lower
            ):
                if "email" in error_lower:
                    self.register_personal_error.emit(
                        get_error_message("email_already_in_use")
                    )
                else:
                    self.register_personal_error.emit(
                        get_error_message("username_already_taken")
                    )
                return

            logger.error("Unexpected registration error: %s", e)
            self.register_failed.emit(error_str)

    @Slot(object)
    def _finish_success(self, user: User):
        """Finalize successful registration and continue app flow."""
        logger.info("Registration process completed (user_id: ..%s)", user.id[-10:])
        self.on_complete(user)
        self._auth_view.reset_ui()

    @Slot(str)
    def _finish_error(self, msg: str):
        """Show registration error on the auth step view."""
        self._auth_view.reset_ui()
        self._auth_view.show_auth_error(msg)

    @Slot(str)
    def _finish_personal_error(self, msg: str):
        """Navigate back to personal step and show a user-friendly error."""
        self._auth_view.reset_ui()
        self.on_back_to_personal()
        self._personal_view.show_personal_error(msg)

    @Slot()
    def _on_personal_check_passed(self):
        """Advance to auth step after successful personal data validation."""
        self._personal_view.reset_checking_state()
        self.on_next_to_auth()

    @Slot(str)
    def _on_personal_check_failed(self, error: str):
        """Show personal step validation / availability error."""
        self._personal_view.reset_checking_state()
        self._personal_view.show_personal_error(error)

    def _back_to_login(self):
        """Return from registration flow back to the login screen."""
        logger.debug("User returning to login screen.")
        self._personal_view.reset_ui()
        self._auth_view.reset_ui()
        self.on_back_to_login()

    def _back_to_personal(self):
        """Return from auth step back to personal data step."""
        self._personal_view.reset_ui()
        self._prefill_personal()
        self.on_back_to_personal()

    def _prefill_personal(self):
        """Restore previously entered personal data into the personal step UI."""
        try:
            self._personal_view.usernameEdit.setText(self._draft.username)
            self._personal_view.emailEdit.setText(self._draft.email)

            birthday_date = self._draft.birthday_date
            if birthday_date and hasattr(birthday_date, "year"):
                self._personal_view.yearBox.setCurrentText(str(birthday_date.year))
                self._personal_view.birthMonthBox.setCurrentIndex(
                    birthday_date.month - 1
                )
                self._personal_view.dayBox.setCurrentText(str(birthday_date.day))

            if self._draft.avatar_blob:
                self._personal_view.set_avatar_from_blob(self._draft.avatar_blob)
        except Exception as e:
            logger.error("Failed to prefill personal data: %s", e)

    def cleanup(self) -> None:
        """Cancel any running registration or username check operations."""
        self._operation.cancel()
        self._check_operation.cancel()
