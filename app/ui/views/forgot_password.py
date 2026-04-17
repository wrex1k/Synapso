"""ForgotPassword view manages the multi-step password reset UI, including email submission, OTP verification, and password update.
It provides signals for user actions that the ForgotPasswordController connects to, and methods to update the
UI based on the controller's responses (e.g. showing success/error states and navigating between steps)."""

import re

from PySide6.QtCore import QEasingCurve, QEvent, QPoint, QPropertyAnimation, QRegularExpression, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QFont, QIcon, QRegularExpressionValidator
from PySide6.QtWidgets import QApplication, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.utils.validator import validate_email, validate_otp, validate_password, validate_passwords_match
from app.ui.components.back_button import BackButton
from app.ui.components.input_field import InputField
from app.utils.event_filters import context_menu_event_filter, enter_key_event_filter, password_event_filter
from app.utils.logger import get_logger
logger = get_logger(__name__)
from app.utils.ui_helpers import draw_background, update_button_state
from translations.translation import translate




class ForgotPassword(QWidget):
    send_reset_email_signal = Signal(str)
    verify_otp_signal = Signal(str, str)
    update_password_signal = Signal(str)
    back_to_login_signal = Signal()
    resend_code_back_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("forgotPassword")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(QSize(1000, 800))

        self.states = ["idle", "loading", "error"]
        self.state = "idle"
        self._animations_started = False

        self.current_step = "email"
        self.resend_timer_seconds = 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self._last_sent_email = None

        self._build_ui()
        self._setup_connections()
        self._retranslate_ui()
        self._show_email_step()

    def _build_ui(self):
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # back button
        self.backButton = BackButton(self)
        mainLayout.addWidget(self.backButton)

        contentWidget = QWidget(self)
        rootLayout = QVBoxLayout(contentWidget)
        rootLayout.setContentsMargins(0, 200, 120, 0)

        # main frame
        frame = QFrame(contentWidget)
        frame.setObjectName("frame")
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        frame.setMinimumSize(QSize(600, 500))
        frame.setFrameShape(QFrame.Shape.NoFrame)

        self.frameLayout = QVBoxLayout(frame)

        titleFrame = QFrame(frame)
        titleFrame.setObjectName("titleFrame")
        titleFrame.setFrameShape(QFrame.Shape.NoFrame)

        titleLayout = QHBoxLayout(titleFrame)
        titleLayout.setSpacing(8)
        titleLayout.setContentsMargins(0, 0, 0, 0)

        # title
        self.titleLeft = QLabel("", titleFrame)
        self.titleLeft.setObjectName("titleLeft")
        self.titleLeft.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.titleRight = QLabel("", titleFrame)
        self.titleRight.setObjectName("titleRight")
        self.titleRight.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        titleLayout.addStretch()
        titleLayout.addWidget(self.titleLeft)
        titleLayout.addWidget(self.titleRight)
        titleLayout.addStretch()

        self.frameLayout.addWidget(titleFrame)
        self.frameLayout.addSpacing(10)

        self.titleFrame = titleFrame

        # info
        self.descLabel = QLabel("", frame)
        self.descLabel.setObjectName("descLabel")
        self.descLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descLabel.setWordWrap(True)
        self.frameLayout.addWidget(self.descLabel)

        self.descOpacity = QGraphicsOpacityEffect(self.descLabel)
        self.descLabel.setGraphicsEffect(self.descOpacity)
        self.descOpacity.setOpacity(0)

        self.frameLayout.addSpacing(40)

        self.stepsContainer = QWidget(frame)
        self.stepsLayout = QVBoxLayout(self.stepsContainer)
        self.stepsLayout.setContentsMargins(0, 0, 0, 0)
        self.frameLayout.addWidget(self.stepsContainer)

        self.stepsOpacity = QGraphicsOpacityEffect(self.stepsContainer)
        self.stepsContainer.setGraphicsEffect(self.stepsOpacity)
        self.stepsOpacity.setOpacity(0)
        
        self.frameLayout.addSpacing(40)
        self.frameLayout.addStretch()

        self._build_email_step()
        self._build_otp_step()
        self._build_password_step()

        self.welcomeOpacity = QGraphicsOpacityEffect(self.titleLeft)
        self.titleLeft.setGraphicsEffect(self.welcomeOpacity)
        self.welcomeOpacity.setOpacity(0)

        self.logoOpacity = QGraphicsOpacityEffect(self.titleRight)
        self.titleRight.setGraphicsEffect(self.logoOpacity)
        self.logoOpacity.setOpacity(0)

        rootLayout.addWidget(frame, 0, Qt.AlignmentFlag.AlignHCenter)
        mainLayout.addWidget(contentWidget)

    def _start_welcome_animation(self):
        left_final_pos = self.titleLeft.pos()
        right_final_pos = self.titleRight.pos()
        offset = 90

        welcome_start_pos = QPoint(left_final_pos.x() - offset, left_final_pos.y())
        logo_start_pos = QPoint(right_final_pos.x() + offset, right_final_pos.y())

        self.titleLeft.move(welcome_start_pos)
        self.titleRight.move(logo_start_pos)

        self.welcomePosAnim = QPropertyAnimation(self.titleLeft, b"pos")
        self.welcomePosAnim.setDuration(700)
        self.welcomePosAnim.setStartValue(welcome_start_pos)
        self.welcomePosAnim.setEndValue(left_final_pos)
        self.welcomePosAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.logoPosAnim = QPropertyAnimation(self.titleRight, b"pos")
        self.logoPosAnim.setDuration(800)
        self.logoPosAnim.setStartValue(logo_start_pos)
        self.logoPosAnim.setEndValue(right_final_pos)
        self.logoPosAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.welcomeOpacityAnim = QPropertyAnimation(self.welcomeOpacity, b"opacity")
        self.welcomeOpacityAnim.setDuration(350)
        self.welcomeOpacityAnim.setStartValue(0.0)
        self.welcomeOpacityAnim.setEndValue(1.0)
        self.welcomeOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.logoOpacityAnim = QPropertyAnimation(self.logoOpacity, b"opacity")
        self.logoOpacityAnim.setDuration(350)
        self.logoOpacityAnim.setStartValue(0.0)
        self.logoOpacityAnim.setEndValue(1.0)
        self.logoOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.descOpacityAnim = QPropertyAnimation(self.descOpacity, b"opacity")
        self.descOpacityAnim.setDuration(500)
        self.descOpacityAnim.setStartValue(0.0)
        self.descOpacityAnim.setEndValue(1.0)
        self.descOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.stepsOpacityAnim = QPropertyAnimation(self.stepsOpacity, b"opacity")
        self.stepsOpacityAnim.setDuration(550)
        self.stepsOpacityAnim.setStartValue(0.0)
        self.stepsOpacityAnim.setEndValue(1.0)
        self.stepsOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.welcomePosAnim.start()
        self.logoPosAnim.start()
        QTimer.singleShot(80, self.welcomeOpacityAnim.start)
        QTimer.singleShot(160, self.logoOpacityAnim.start)
        QTimer.singleShot(260, self.descOpacityAnim.start)
        QTimer.singleShot(340, self.stepsOpacityAnim.start)

    def _build_email_step(self):
        self.emailStep = QWidget(self.stepsContainer)
        layout = QVBoxLayout(self.emailStep)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(50)

        self.emailField = InputField(
            label_text="",
            placeholder="",
            object_name="emailEdit")
        self.emailField.installEventFilter(self)
        self.emailEdit = self.emailField.line_edit

        layout.addWidget(self.emailField, 0, Qt.AlignmentFlag.AlignHCenter)

        self.sendButton = QPushButton("", self.emailStep)
        self.sendButton.setObjectName("primaryButton")
        self.sendButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(self.sendButton, 0, Qt.AlignmentFlag.AlignHCenter)
        self.stepsLayout.addWidget(self.emailStep)

    def _build_otp_step(self):
        self.otpStep = QWidget(self.stepsContainer)
        layout = QVBoxLayout(self.otpStep)
        layout.setSpacing(25)
        layout.setContentsMargins(0, 0, 0, 0)

        otpFrame = QFrame(self.otpStep)
        otpFrame.setObjectName("otpFrame")
        otpLayout = QHBoxLayout(otpFrame)
        otpLayout.setSpacing(15)
        otpLayout.setContentsMargins(0, 0, 0, 0)

        self.otpInputs = []
        digit_validator = QRegularExpressionValidator(QRegularExpression("[0-9]"))
        for i in range(6):
            otpEdit = QLineEdit(otpFrame)
            otpEdit.setObjectName(f"otpEdit{i}")
            otpEdit.setProperty("otpIndex", i)
            otpEdit.setMaxLength(1)
            otpEdit.setValidator(digit_validator)
            otpEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            otpEdit.setFixedSize(QSize(60, 70))
            otpEdit.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
            otpEdit.installEventFilter(self)
            self.otpInputs.append(otpEdit)

            idx = i
            otpEdit.textChanged.connect(lambda text, index=idx: self._on_otp_text_changed(text, index))
            otpLayout.addWidget(otpEdit)

        layout.addWidget(otpFrame, 0, Qt.AlignmentFlag.AlignHCenter)

        self.resendButton = QPushButton("", self.otpStep)
        self.resendButton.setObjectName("resendButton")
        self.resendButton.setEnabled(False)

        layout.addWidget(self.resendButton, 0, Qt.AlignmentFlag.AlignHCenter)

        self.approveButton = QPushButton("", self.otpStep)
        self.approveButton.setObjectName("primaryButton")
        self.approveButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(self.approveButton, 0, Qt.AlignmentFlag.AlignHCenter)
        self.stepsLayout.addWidget(self.otpStep)

    def _build_password_step(self):
        self.passwordStep = QWidget(self.stepsContainer)
        layout = QVBoxLayout(self.passwordStep)
        layout.setSpacing(30)
        layout.setContentsMargins(0, 0, 0, 0)

        self.passwordField = InputField(
            label_text="",
            placeholder="",
            object_name="passwordEdit",
            is_password=True,
            parent=self.passwordStep,
            password_strength=True,
        )
        self.passwordField.installEventFilter(self)

        self.copasswordField = InputField(
            label_text="",
            placeholder="",
            object_name="confirmPasswordEdit",
            is_password=True,
            parent=self.passwordStep,
            password_strength=False,
        )
        self.copasswordField.installEventFilter(self)

        layout.addWidget(self.passwordField, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.copasswordField, 0, Qt.AlignmentFlag.AlignHCenter)

        self.updateButton = QPushButton("", self.passwordStep)
        self.updateButton.setObjectName("primaryButton")
        self.updateButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(self.updateButton, 0, Qt.AlignmentFlag.AlignHCenter)
        self.stepsLayout.addWidget(self.passwordStep)

    def _setup_connections(self):
        self.backButton.clicked.connect(self._on_back_clicked)

        self.sendButton.clicked.connect(self.handle_send_reset_email)
        self.resendButton.clicked.connect(self._resend_code)
        self.approveButton.clicked.connect(self.handle_verify_otp)
        self.updateButton.clicked.connect(self.handle_update_password)

    # step 1 (email) → Step 2 (otp)
    def _show_email_step(self):
        self.current_step = "email"
        self.descLabel.setText(translate("ForgotPassword", "Enter your email address and we'll send you a code to reset your password."))

        self.emailStep.setVisible(True)
        self.otpStep.setVisible(False)
        self.passwordStep.setVisible(False)

        self.state = "idle"
        update_button_state(self.sendButton, "idle", idle_text=translate("ForgotPassword", "Send reset email"), loading_text=translate("ForgotPassword", "Sending…"))
        self.emailEdit.setFocus()

    # step 2 (otp) → Step 3 (password)
    def _show_otp_step(self):
        self.current_step = "otp"
        self.descLabel.setText(translate("ForgotPassword", "Check your email. You received a code."))

        self.emailStep.setVisible(False)
        self.otpStep.setVisible(True)
        self.passwordStep.setVisible(False)

        self.state = "idle"
        update_button_state(self.approveButton, "idle", idle_text=translate("ForgotPassword", "Approve Code"), loading_text=translate("ForgotPassword", "Verifying…"))

        self.resend_timer_seconds = 60
        self.resendButton.setEnabled(False)
        self.resendButton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.timer.start(1000)
        self._update_timer()

        for edit in self.otpInputs:
            edit.clear()
        self.otpInputs[0].setFocus()

    # switching when timers is active
    def _show_otp_step_resume(self):
        self.current_step = "otp"
        self.descLabel.setText(translate("ForgotPassword", "Check your email. You received a code."))

        self.emailStep.setVisible(False)
        self.otpStep.setVisible(True)
        self.passwordStep.setVisible(False)

        self.state = "idle"
        update_button_state(self.approveButton, "idle", idle_text=translate("ForgotPassword", "Approve Code"), loading_text=translate("ForgotPassword", "Verifying…"))

        for edit in self.otpInputs:
            edit.clear()
        self.otpInputs[0].setFocus()

    # step 3 (password) → done
    def _show_password_step(self):
        self.current_step = "password"
        self.descLabel.setText(translate("ForgotPassword", "Enter your new password"))

        self.emailStep.setVisible(False)
        self.otpStep.setVisible(False)
        self.passwordStep.setVisible(True)

        self.state = "idle"
        update_button_state(self.updateButton, "idle", idle_text=translate("ForgotPassword", "Update Password"), loading_text=translate("ForgotPassword", "Updating…"))
        self.passwordField.line_edit.setFocus()

    def _on_otp_text_changed(self, text: str, index: int):
        if text and index < 5:
            self.otpInputs[index + 1].setFocus()

    def _update_timer(self):
        if self.resend_timer_seconds > 0:
            self.resendButton.setText(translate('ForgotPassword', 'Resend code in') + f" {self.resend_timer_seconds}s")
            self.resendButton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.resend_timer_seconds -= 1
            return

        self.timer.stop()
        self.resendButton.setText(translate("ForgotPassword", "Resend code"))
        self.resendButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.resendButton.setEnabled(True)

    def _resend_code(self):
        email = self.emailEdit.text().strip()

        self.resend_timer_seconds = 60
        self.resendButton.setEnabled(False)
        self.resendButton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.timer.start(1000)
        self._update_timer()

        self.send_reset_email_signal.emit(email)

    def handle_send_reset_email(self):
        if self.state == "loading" or self.state == "error":
            logger.debug("Already sending or showing error, ignoring click")
            return

        email = self.emailEdit.text().strip()
        err = validate_email(email)
        if err:
            self.show_email_error(err)
            return

        if self.timer.isActive():
            if self._last_sent_email and email.lower() == self._last_sent_email.lower():
                self._show_otp_step_resume()
                return
            else:
                self.show_email_error(translate("ForgotPassword", "Please wait before sending another reset request"))
                return

        self.state = "loading"
        update_button_state(self.sendButton, "loading", 
                          idle_text=translate("ForgotPassword", "Send reset email"), 
                          loading_text=translate("ForgotPassword", "Sending…"))

        self.send_reset_email_signal.emit(email)

    def handle_verify_otp(self):
        if self.state == "loading" or self.state == "error":
            logger.debug("Already verifying OTP or showing error, ignoring request")
            return

        otp_code = "".join([edit.text() for edit in self.otpInputs])
        err = validate_otp(otp_code)
        if err:
            self.show_otp_error(err)
            return

        self.state = "loading"
        update_button_state(self.approveButton,
                            "loading",
                            idle_text=translate("ForgotPassword", "Approve Code"),
                            loading_text=translate("ForgotPassword", "Verifying…"))

        email = self.emailEdit.text().strip()
        self.verify_otp_signal.emit(email, otp_code)

    def handle_update_password(self):
        if self.state == "loading" or self.state == "error":
            logger.debug("Already updating password or showing error, ignoring click")
            return

        password = self.passwordField.text().strip()
        copassword = self.copasswordField.text().strip()

        err = validate_password(password)
        if err:
            self.show_password_error(err)
            return

        err = validate_passwords_match(password, copassword)
        if err:
            self.show_password_error(err)
            return

        self.state = "loading"
        update_button_state(
            self.updateButton,
            "loading",
            idle_text=translate("ForgotPassword", "Update Password"),
            loading_text=translate("ForgotPassword", "Updating…")
            )

        self.update_password_signal.emit(password)

    def show_email_sent_success(self):
        self._last_sent_email = self.emailEdit.text().strip()
        self.state = "idle"
        update_button_state(
            self.sendButton,
            "idle", idle_text="Send reset email",
            loading_text="Sending…"
            )
        self._show_otp_step()

    def show_email_error(self, message: str):
        self.state = "error"
        update_button_state(
            self.sendButton,
            "error",
            idle_text=translate("ForgotPassword", "Send reset email"),
            loading_text=translate("ForgotPassword", "Sending…"),
            error_text=message,
            auto_reset_ms=2000,
        )
        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def show_otp_verified_success(self):
        self.timer.stop()
        self.state = "idle"
        update_button_state(self.approveButton, "idle", idle_text=translate("ForgotPassword", "Approve Code"), loading_text=translate("ForgotPassword", "Verifying…"))
        self._show_password_step()

    def show_otp_error(self, message: str):
        self.state = "error"
        update_button_state(
            self.approveButton,
            "error",
            idle_text=translate("ForgotPassword", "Approve Code"),
            loading_text=translate("ForgotPassword", "Verifying…"),
            error_text=message,
            auto_reset_ms=2000,
        )
        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def show_password_updated_success(self):
        self.state = "idle"
        update_button_state(
            self.updateButton,
            "idle",
            idle_text=translate("ForgotPassword", "Password Updated!"),
            loading_text=translate("ForgotPassword", "Updating…"),
        )
        self.updateButton.setEnabled(False)
        
        QTimer.singleShot(2000, self._reset_and_go_to_login)
    
    def _reset_and_go_to_login(self):
        self.state = "idle"
        self.timer.stop()
        self._last_sent_email = None
        self.resend_timer_seconds = 60
        self.current_step = "email"
        
        for e in getattr(self, "otpInputs", []):
            e.clear()
        self.passwordField.setText("")
        self.copasswordField.setText("")
        
        self._show_email_step()
        self.back_to_login_signal.emit()

    def show_password_error(self, message: str):
        self.state = "error"
        update_button_state(
            self.updateButton,
            "error",
            idle_text=translate("ForgotPassword", "Update Password"),
            loading_text=translate("ForgotPassword", "Updating…"),
            error_text=message,
            auto_reset_ms=2000,
        )
        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def reset_view(self):
        self.state = "idle"
        self.timer.stop()
        for e in getattr(self, "otpInputs", []):
            e.clear()
        self.passwordField.setText("")
        self.copasswordField.setText("")
        self._show_email_step()

    def reset_ui(self):
        self.emailField.clear()

    def eventFilter(self, watched, event):
        if hasattr(self, "otpInputs") and watched in self.otpInputs:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    clipboard = QApplication.clipboard()
                    text = clipboard.text().strip()
                    if text.isdigit() and len(text) == 6:
                        for i, char in enumerate(text):
                            self.otpInputs[i].setText(char)
                        self.otpInputs[5].setFocus()
                    return True
                elif event.key() == Qt.Key.Key_Backspace:
                    idx = self.otpInputs.index(watched)
                    if watched.text() == "" and idx > 0:
                        self.otpInputs[idx - 1].setFocus()
                        self.otpInputs[idx - 1].clear()
                        return True

        if watched in (
            self.passwordField.line_edit,
            self.copasswordField.line_edit,
        ):
            if password_event_filter(self, watched, event):
                return True

        if enter_key_event_filter(self, watched, event, on_enter=self._handle_enter_key):
            return True

        if context_menu_event_filter(self, watched, event):
            return True

        return super().eventFilter(watched, event)

    def _handle_enter_key(self):
        if self.current_step == "email":
            self.handle_send_reset_email()
        elif self.current_step == "otp":
            self.handle_verify_otp()
        elif self.current_step == "password":
            self.handle_update_password()

    def _on_back_clicked(self):
        if self.current_step == "password":
            if self.timer.isActive():
                self._show_otp_step_resume()
            else:
                email = self.emailEdit.text().strip()
                self._show_otp_step()
                self.resend_code_back_signal.emit(email)
        elif self.current_step == "otp":
            self._show_email_step()
        else:
            self.back_to_login_signal.emit()

    def _retranslate_ui(self):
        self.titleLeft.setText(translate("ForgotPassword", "reset your"))
        self.titleRight.setText(translate("ForgotPassword", "Password"))
        
        self.emailField.setTitle(translate("ForgotPassword", "Email"))
        self.emailField.setPlaceholderText(translate("ForgotPassword", "john.doe@example.com"))
        
        self.sendButton.setText(translate("ForgotPassword", "Send reset email"))
        
        self.approveButton.setText(translate("ForgotPassword", "Approve Code"))
        
        self.passwordField.setTitle(translate("ForgotPassword", "New Password"))
        self.passwordField.setPlaceholderText("••••••••••••••••")
        
        self.copasswordField.setTitle(translate("ForgotPassword", "Confirm new password"))
        self.copasswordField.setPlaceholderText("••••••••••••••••")
        
        self.updateButton.setText(translate("ForgotPassword", "Update Password"))
        
        if self.current_step == "email":
            self.descLabel.setText(translate("ForgotPassword", "Enter your email address and we'll send you a code to reset your password."))
        elif self.current_step == "otp":
            self.descLabel.setText(translate("ForgotPassword", "Check your email. You received a code."))
        elif self.current_step == "password":
            self.descLabel.setText(translate("ForgotPassword", "Enter your new password"))

    def showEvent(self, event):
        super().showEvent(event)
        self._retranslate_ui()
        if not self._animations_started:
            self._animations_started = True
            QTimer.singleShot(40, self._start_welcome_animation)

    def paintEvent(self, event):
        draw_background(self, event)