""" ForgotPasswordController manages the multi-step password reset flow, including email submission,
OTP verification, and password update. It also handles async operations, validation feedback,
and navigation back to login.
"""

from typing import Callable

from PySide6.QtCore import QObject, Signal, QTimer

from translations.translation import get_error_message
from app.core.registry import registry
from app.service.auth_service import send_password_reset_email, verify_otp_code, update_password_with_token
from app.utils.logger import get_logger
from app.ui.views.forgot_password import ForgotPassword


logger = get_logger(__name__)

class ForgotPasswordController(QObject):
    """Handle forgot-password interactions across all reset steps."""

    email_sent = Signal()
    otp_verified = Signal()
    password_updated = Signal()
    email_failed = Signal(str)
    otp_failed = Signal(str)
    password_failed = Signal(str)

    def __init__(
        self,
        view: ForgotPassword,
        on_success: Callable[[], None],
        on_back: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.on_success = on_success
        self.on_back = on_back

        self._operation = registry.operation("forgot_password")
        self._email = ""

        self._connect_signals()

        self.email_sent.connect(self.view.show_email_sent_success)
        self.otp_verified.connect(self.view.show_otp_verified_success)
        self.email_failed.connect(self.view.show_email_error)
        self.otp_failed.connect(self.view.show_otp_error)
        self.password_failed.connect(self.view.show_password_error)

        def _after_password_updated():
            self.view.show_password_updated_success()
            QTimer.singleShot(1500, self.on_success)

        self.password_updated.connect(_after_password_updated)

    def _connect_signals(self):
        """Connect forgot-password view signals to controller handlers."""
        self.view.send_reset_email_signal.connect(self.send_reset_email)
        self.view.verify_otp_signal.connect(self.verify_otp)
        self.view.update_password_signal.connect(self.update_password)
        self.view.back_to_login_signal.connect(self._back_to_login)
        self.view.resend_code_back_signal.connect(self._resend_code_silently)

    def send_reset_email(self, email: str):
        """Start the password reset flow by sending a reset email."""
        logger.info("User requesting password reset for: %s..", email)
        self._email = (email or "").strip()

        started = self._operation.start(
            registry.run_thread,
            lambda: send_password_reset_email(self._email),
            on_finished=self._on_send_email_result,
            name="send-reset-email-thread",
        )

        if not started:
            logger.debug("Forgot password operation already running")

    def _on_send_email_result(self, result):
        """Handle the result of the reset email sending step."""
        try:
            success, error = result

            if success:
                self.email_sent.emit()
                logger.debug(
                    "Password reset email sent successfully to: %s",
                    self._email,
                )
                return

            if error and (
                "rate limit" in error.lower() or "too many" in error.lower()
            ):
                self.email_failed.emit(
                    "Too many reset requests. Please wait a bit and try again."
                )
            else:
                self.email_failed.emit(error or "Unable to send reset email")

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.exception("send_reset_email failed: %s", e)
            self.email_failed.emit("Unexpected error")

    def verify_otp(self, email: str, otp_code: str):
        """Verify the OTP code and advance to the password update step."""
        logger.info("User verifying OTP for password reset: %s..", email)
        self._email = (email or self._email or "").strip()

        started = self._operation.start(
            registry.run_thread,
            lambda: verify_otp_code(self._email, otp_code),
            on_finished=self._on_verify_otp_result,
            name="verify-otp-thread",
        )

        if not started:
            logger.debug("Forgot password operation already running")

    def _on_verify_otp_result(self, result):
        """Handle the result of the OTP verification step."""
        if isinstance(result, tuple):
            success = bool(result[0]) if len(result) > 0 else False
            error = result[1] if len(result) > 1 else None
        else:
            success = bool(result)
            error = None

        if success:
            self.otp_verified.emit()
            return

        if error == "token_expired":
            error_message = get_error_message("token_expired")
        elif error and (
            "expired" in error.lower()
            or "invalid" in error.lower()
            or "token" in error.lower()
        ):
            error_message = get_error_message("token_expired")
        else:
            error_message = error or get_error_message("token_expired")

        self.otp_failed.emit(error_message)

    def update_password(self, new_password: str):
        """Update the password after successful OTP verification."""
        logger.info("User updating password after reset for email: %s..", self._email)
        new_password = (new_password or "").strip()

        started = self._operation.start(
            registry.run_thread,
            lambda: update_password_with_token(new_password),
            on_finished=self._on_update_password_result,
            name="update-password-thread",
        )

        if not started:
            logger.debug("Forgot password operation already running")

    def _on_update_password_result(self, result):
        """Handle the result of the password update step."""
        try:
            success, error = result

            if success:
                self.password_updated.emit()
                logger.debug("Password updated for email: %s", self._email)
                return

            if error == "password_same_as_old":
                error = get_error_message("password_same_as_old")

            self.password_failed.emit(error or "Unable to update password")

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.exception("update_password failed: %s", e)
            self.password_failed.emit("Unexpected error")

    def _back_to_login(self):
        """Reset the forgot-password view and navigate back to login."""
        self.view.reset_ui()
        self.on_back()

    def _resend_code_silently(self, email: str):
        """Silently resend the reset code when returning from password step."""
        email = (email or self._email or "").strip()
        if email:
            self._email = email

        started = self._operation.start(
            registry.run_thread,
            lambda: send_password_reset_email(email),
            on_finished=self._on_silent_resend_result,
            name="silent-resend-thread",
        )

        if not started:
            logger.debug(
                "Forgot password operation already running, skipping silent resend"
            )

    def _on_silent_resend_result(self, result):
        """Handle the result of a silent resend request."""
        try:
            success, error = result

            if success:
                logger.debug(
                    "Silent resend of reset email succeeded for: %s",
                    self._email,
                )
                return

            logger.warning("Silent resend failed: %s", error)

        except Exception as e:
            logger.exception("Silent resend error: %s", e)
