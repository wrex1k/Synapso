from typing import Callable

from PySide6.QtCore import QObject, Signal

from app.core.registry import registry
from translations.translation import get_error_message
from app.service.auth_service import send_password_reset_email, verify_otp_code, update_password_with_token

from app.ui.views.forgot_password import ForgotPassword
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.utils.error_codes import AuthError


class ForgotPasswordController(QObject):
    """Controller responsible for managing the multi-step password reset flow."""

    email_sent = Signal()
    otp_verified = Signal()
    password_updated = Signal()
    email_failed = Signal(str)
    otp_failed = Signal(str)
    password_failed = Signal(str)

    def __init__(
        self,
        view: ForgotPassword,
        on_back: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.on_back = on_back

        self._operation = registry.operation("forgot_password")
        self._email = ""

        self._connect_signals()

        self.email_sent.connect(self.view.show_email_sent_success)
        self.otp_verified.connect(self.view.show_otp_verified_success)
        self.password_updated.connect(self.view.show_password_updated_success)
        self.email_failed.connect(self.view.show_email_error)
        self.otp_failed.connect(self.view.show_otp_error)
        self.password_failed.connect(self.view.show_password_error)

    def _connect_signals(self):
        """Connect view signals to controller action handlers."""
        self.view.send_reset_email_signal.connect(self.send_reset_email)
        self.view.verify_otp_signal.connect(self.verify_otp)
        self.view.update_password_signal.connect(self.update_password)
        self.view.back_to_login_signal.connect(self._back_to_login)
        self.view.resend_code_back_signal.connect(self._resend_code_silently)

    def _normalize_email(self, email: str) -> str:
        """Normalize and store the email address, returning the cleaned value."""
        normalized = (email or self._email or "").strip()
        if normalized:
            self._email = normalized
        return normalized

    def send_reset_email(self, email: str):
        """Start asynchronous password reset email sending if no operation is running."""
        email = self._normalize_email(email)
        logger.info("Requesting password reset for: %s", email)

        started = self._operation.start(
            registry.run_thread,
            lambda: send_password_reset_email(email),
            on_finished=self._on_send_email_result,
            name="send-reset-email-thread",
        )

        if not started:
            logger.debug("Operation already running")

    def _on_send_email_result(self, result):
        """Emit success signal or show error message based on email sending result."""
        success, error = result

        if success:
            self.email_sent.emit()
            logger.debug("Reset email sent to: %s", self._email)
            return

        if error and ("rate limit" in error.lower() or "too many" in error.lower()):
            self.email_failed.emit(
                "Too many reset requests. Please wait a bit and try again."
            )
        else:
            self.email_failed.emit(error or "Unable to send reset email")

    def verify_otp(self, email: str, otp_code: str):
        """Start asynchronous OTP verification if no operation is running."""
        email = self._normalize_email(email)
        logger.info("Verifying OTP for: %s", email)

        started = self._operation.start(
            registry.run_thread,
            lambda: verify_otp_code(email, otp_code),
            on_finished=self._on_verify_otp_result,
            name="verify-otp-thread",
        )

        if not started:
            logger.debug("Operation already running")

    def _on_verify_otp_result(self, result):
        """Emit success signal or show error message based on OTP verification result."""
        success, error = result

        if success:
            self.otp_verified.emit()
            return

        if error == AuthError.TOKEN_EXPIRED or (
            error and any(kw in error.lower() for kw in ["expired", "invalid", "token"])
        ):
            error = get_error_message("token_expired")

        self.otp_failed.emit(error or get_error_message("token_expired"))

    def update_password(self, new_password: str):
        """Start asynchronous password update if no operation is running."""
        new_password = (new_password or "").strip()
        logger.info("Updating password for: %s", self._email)

        started = self._operation.start(
            registry.run_thread,
            lambda: update_password_with_token(new_password),
            on_finished=self._on_update_password_result,
            name="update-password-thread",
        )

        if not started:
            logger.debug("Operation already running")

    def _on_update_password_result(self, result):
        """Emit success signal or show error message based on password update result."""
        success, error = result

        if success:
            self.password_updated.emit()
            logger.debug("Password updated for: %s", self._email)
            return

        if error == AuthError.PASSWORD_SAME_AS_OLD:
            error = get_error_message("password_same_as_old")

        self.password_failed.emit(error or "Unable to update password")

    def _back_to_login(self):
        """Reset the view state and navigate back to login screen."""
        self.view.reset_ui()
        self.on_back()

    def _resend_code_silently(self, email: str):
        """Resend the password reset email without showing UI feedback to the user."""
        email = self._normalize_email(email)

        started = self._operation.start(
            registry.run_thread,
            lambda: send_password_reset_email(email),
            on_finished=self._on_silent_resend_result,
            name="silent-resend-thread",
        )

        if not started:
            logger.debug("Operation already running, skipping silent resend")

    def _on_silent_resend_result(self, result):
        """Log the silent resend result without notifying the UI."""
        success, error = result

        if success:
            logger.debug("Silent resend succeeded for: %s", self._email)
        else:
            logger.warning("Silent resend failed: %s", error)

    def cleanup(self) -> None:
        """Cancel any running forgot password operation."""
        self._operation.cancel()
