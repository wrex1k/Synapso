"""RegisterAuth is the second step of the registration flow where the user sets a password. It validates password rules and matching confirmation, manages UI state (idle/loading/error), and emits the submitted password on success. Includes fade-in animations on show."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.components.back_button import BackButton
from app.ui.components.input_field import InputField
from app.utils.logger import logger
from app.utils.event_filters import context_menu_event_filter, enter_key_event_filter, password_event_filter
from app.utils.ui_helpers import draw_background, update_button_state
from app.utils.validator import validate_password, validate_passwords_match
from translations.translation import translate, get_translation_manager


class RegisterAuth(QWidget):
    auth_data_submit = Signal(str)
    back_to_personal_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("registerAuth")
        self.setWindowTitle("Synapso")
        self.setWindowIcon(QIcon(":/images/graphics/logo.png"))

        self.states = ["idle", "loading", "error"]
        self.state = "idle"

        self._animations_started = False

        self._build_ui()
        self._setup_connections()
        self._setup_animations()
        self._retranslate_ui()

    def _build_ui(self):
        self._create_main_layout()

        self._create_frame_and_title(self._contentWidget)
        self._create_password_section(self._frame)
        self._create_confirm_password_section(self._frame)
        self._create_button_section(self._frame)

    def _create_main_layout(self):
        mainLayout = QGridLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        contentWidget = QWidget(self)
        rootLayout = QVBoxLayout(contentWidget)
        rootLayout.setContentsMargins(0, 0, 0, 0)

        mainLayout.addWidget(contentWidget, 0, 0)

        # back button
        self.backButton = BackButton(self)
        mainLayout.addWidget(self.backButton, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.backButton.raise_()

        self._contentWidget = contentWidget
        self._rootLayout = rootLayout

        # main frame
        frame = QWidget(contentWidget)
        frame.setObjectName("frame")
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        frame.setMinimumSize(QSize(600, 800))

        frameLayout = QVBoxLayout(frame)
        frameLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        frameLayout.setContentsMargins(0, 150, 0, 70)
        frameLayout.setSpacing(60)

        self._frame = frame
        self._frameLayout = frameLayout

        rootLayout.addStretch()
        rootLayout.addWidget(frame, 0, Qt.AlignmentFlag.AlignHCenter)
        rootLayout.addStretch()

    def _create_frame_and_title(self, frame_parent):
        titleFrame = QWidget(frame_parent)
        titleFrame.setObjectName("title")
        titleFrame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        titleLayout = QVBoxLayout(titleFrame)
        titleLayout.setSpacing(0)
        titleLayout.setContentsMargins(0, 0, 0, 0)
        titleLayout.setSpacing(30)

        # title
        titleRow = QHBoxLayout()
        self.titleLabel = QLabel("Let's set up your password", titleFrame)
        self.titleLabel.setObjectName("titleLabel")

        titleRow.addWidget(self.titleLabel)

        # info
        self.info = QLabel(
            "Next step is to make a password. Make sure it's strong and secure. "
            "Your password should be at least 8 characters, include at least one uppercase letter and one number.",
            titleFrame,
        )
        self.info.setObjectName("info")
        self.info.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.info.setWordWrap(True)

        titleLayout.addLayout(titleRow)
        titleLayout.addWidget(self.info)
        self._frameLayout.addWidget(titleFrame)

        # setup opacity for title section
        self.titleOpacity = QGraphicsOpacityEffect(titleFrame)
        titleFrame.setGraphicsEffect(self.titleOpacity)
        self.titleOpacity.setOpacity(0)
        self.titleFrame = titleFrame

    def _create_password_section(self, frame):
        passwordFrame = QWidget(frame)
        passwordFrame.setObjectName("passwordFrame")
        passwordFrame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        passwordLayout = QVBoxLayout(passwordFrame)
        passwordLayout.setSpacing(9)
        passwordLayout.setContentsMargins(0, 0, 0, 0)

        # password field
        self.passwordField = InputField(label_text="", placeholder="", is_password=True, object_name="passwordEdit", parent=passwordFrame, password_strength=True)
        self.passwordField.installEventFilter(self)
        self.passwordEdit = self.passwordField.line_edit

        passwordLayout.addWidget(self.passwordField)
        self._frameLayout.addWidget(passwordFrame)

        # setup opacity for animation password section
        self.passwordOpacity = QGraphicsOpacityEffect(passwordFrame)
        passwordFrame.setGraphicsEffect(self.passwordOpacity)
        self.passwordOpacity.setOpacity(0)
        self.passwordFrame = passwordFrame

    def _create_confirm_password_section(self, frame):
        copasswordFrame = QWidget(frame)
        copasswordFrame.setObjectName("copasswordFrame")
        copasswordFrame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        copasswordLayout = QVBoxLayout(copasswordFrame)
        copasswordLayout.setContentsMargins(0, 0, 0, 0)
        copasswordLayout.setSpacing(0)

        # confirm password field
        self.copasswordField = InputField(label_text="", placeholder="", is_password=True, object_name="copasswordEdit", parent=copasswordFrame)
        self.copasswordField.installEventFilter(self)
        self.copasswordEdit = self.copasswordField.line_edit

        copasswordLayout.addWidget(self.copasswordField)
        copasswordLayout.setSpacing(10)

        self.privacyLabel = QPushButton("")
        self.privacyLabel.setObjectName("privacyNotice")
        self.privacyLabel.setFlat(True)
        self.privacyLabel.setCursor(Qt.CursorShape.PointingHandCursor)

        copasswordLayout.addWidget(self.privacyLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self._frameLayout.addWidget(copasswordFrame)

        # setup opacity for animation confirm password section
        self.copasswordOpacity = QGraphicsOpacityEffect(copasswordFrame)
        copasswordFrame.setGraphicsEffect(self.copasswordOpacity)
        self.copasswordOpacity.setOpacity(0)
        self.copasswordFrame = copasswordFrame

    def _create_button_section(self, frame):
        buttonFrame = QWidget(frame)
        buttonFrame.setObjectName("frameButton")
        buttonFrame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        buttonLayout = QHBoxLayout(buttonFrame)
        buttonLayout.setContentsMargins(0, 0, 0, 0)

        buttonRow = QHBoxLayout()

        # sign up button
        self.signUpButton = QPushButton("Finish the registration", buttonFrame)
        self.signUpButton.setObjectName("primaryButton")
        self.signUpButton.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        buttonRow.addWidget(self.signUpButton, 0, Qt.AlignmentFlag.AlignRight)

        buttonLayout.addStretch()
        buttonLayout.addLayout(buttonRow)
        self._frameLayout.addWidget(buttonFrame)

        # setup opacity for animation button section
        self.buttonOpacity = QGraphicsOpacityEffect(buttonFrame)
        buttonFrame.setGraphicsEffect(self.buttonOpacity)
        self.buttonOpacity.setOpacity(0)
        self.buttonFrame = buttonFrame

    def _setup_connections(self):
        self.signUpButton.clicked.connect(self.handle_auth_register)
        self.backButton.clicked.connect(self.back_to_personal_signal.emit)
        self.privacyLabel.clicked.connect(self._open_privacy_url)

    def _open_privacy_url(self):
        lang = get_translation_manager().current_language
        if lang == "sk":
            url = "https://synapso.world/zasady-ochrany-osobnych-udajov"
        else:
            url = "https://synapso.world/privacy-policy"
        QDesktopServices.openUrl(QUrl(url))

    def _setup_animations(self):
        self.titleAnim = QPropertyAnimation(self.titleOpacity, b"opacity")
        self.titleAnim.setDuration(800)
        self.titleAnim.setStartValue(0.0)
        self.titleAnim.setEndValue(1.0)
        self.titleAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.passwordAnim = QPropertyAnimation(self.passwordOpacity, b"opacity")
        self.passwordAnim.setDuration(800)
        self.passwordAnim.setStartValue(0.0)
        self.passwordAnim.setEndValue(1.0)
        self.passwordAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.copasswordAnim = QPropertyAnimation(self.copasswordOpacity, b"opacity")
        self.copasswordAnim.setDuration(800)
        self.copasswordAnim.setStartValue(0.0)
        self.copasswordAnim.setEndValue(1.0)
        self.copasswordAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.buttonAnim = QPropertyAnimation(self.buttonOpacity, b"opacity")
        self.buttonAnim.setDuration(800)
        self.buttonAnim.setStartValue(0.0)
        self.buttonAnim.setEndValue(1.0)
        self.buttonAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def handle_auth_register(self) -> None:
        if self.state == "loading" or self.state == "error":
            logger.info("Already submitting or showing error, ignoring click")
            return

        password = self.passwordEdit.text().strip()
        copassword = self.copasswordEdit.text().strip()

        err = validate_password(password, min_len=8)
        if err:
            self.show_auth_error(err)
            return

        err = validate_passwords_match(password, copassword)
        if err:
            self.show_auth_error(err)
            return

        self.state = "loading"
        update_button_state(
            self.signUpButton,
            state=self.state,
            idle_text=translate("RegisterAuth", "Finish the registration"),
            loading_text=translate("RegisterAuth", "Finishing registration..."))

        self.auth_data_submit.emit(password)

    def show_auth_error(self, message: str):
        self.state = "error"
        update_button_state(self.signUpButton, 
            state=self.state,
            idle_text=translate("RegisterAuth", "Finish the registration"),
            loading_text=translate("RegisterAuth", "Finishing registration..."),
            error_text=message,
            auto_reset_ms=2000)

        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def showEvent(self, event):
        super().showEvent(event)
        self._retranslate_ui()
        self.backButton.raise_()
        if not self._animations_started:
            self._animations_started = True
            self._start_animations()

    def _start_animations(self):
        QTimer.singleShot(100, self.titleAnim.start)
        QTimer.singleShot(300, self.passwordAnim.start)
        QTimer.singleShot(500, self.copasswordAnim.start)
        QTimer.singleShot(700, self.buttonAnim.start)

    def reset_ui(self):
        self.state = "idle"
        self.passwordEdit.clear()
        self.copasswordEdit.clear()
        if hasattr(self.passwordField, 'progressBar'):
            self.passwordField.progressBar.setValue(0)

        update_button_state(
            self.signUpButton,
            "idle",
            idle_text="Finish the registration",
            loading_text="Finishing registration...",
        )

    def _retranslate_ui(self):
        self.titleLabel.setText(translate("RegisterAuth", "Let's set up your password"))
        self.info.setText(translate("RegisterAuth", "Next step is to make a password. Make sure it's strong and secure. Your password should be at least 8 characters, include at least one uppercase letter and one number."))
        self.passwordField.label.setText(translate("RegisterAuth", "Password"))
        self.passwordField.line_edit.setPlaceholderText(translate("RegisterAuth", "••••••••••••••••"))
        self.copasswordField.label.setText(translate("RegisterAuth", "Confirm password"))
        self.copasswordField.line_edit.setPlaceholderText(translate("RegisterAuth", "••••••••••••••••"))
        self.privacyLabel.setText(translate("RegisterAuth", "By registering, you agree to the Privacy Policy."))
        update_button_state(
            self.signUpButton,
            state=self.state,
            idle_text=translate("RegisterAuth", "Finish the registration"),
            loading_text=translate("RegisterAuth", "Finishing registration..."),
        )

    def eventFilter(self, watched, event):
        if watched in (self.passwordEdit, self.copasswordEdit):
            if password_event_filter(self, watched, event):
                return True
        if enter_key_event_filter(self, watched, event, on_enter=self.handle_auth_register):
            return True
        if context_menu_event_filter(self, watched, event):
            return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        draw_background(self, event)