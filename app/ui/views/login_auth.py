from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QFont, QIcon
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.components.input_field import InputField
from app.utils.event_filters import context_menu_event_filter, enter_key_event_filter, password_event_filter
from app.utils.logger import get_logger
from app.utils.ui_helpers import draw_background, update_button_state
from app.utils.settings import set_language, get_language
from translations.translation import get_translation_manager, translate

"""
LoginAuth view manages the login screen, including the welcome animation, form input,
and error display. It emits signals for login attempts and navigation to registration and forgot password views.
"""

logger = get_logger(__name__)


class LoginAuth(QWidget):
    login_data_submit = Signal(str, str)
    start_registration = Signal()
    forgot_password_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginAuth")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowTitle("Synapso")
        self.setWindowIcon(QIcon(":/images/graphics/logo.png"))
        self.setMinimumSize(QSize(1000, 800))

        self.states = ["idle", "loading", "error"]
        self.state = "idle"

        self.is_logging_in = False
        self._animations_started = False

        self._build_ui()
        self._setup_connections()

        self._retranslate_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        contentFrame = QWidget(self)
        contentFrame.setObjectName("contentFrame")
        contentFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        contentLayout = QVBoxLayout(contentFrame)
        contentLayout.setSpacing(0)

        contentLayout.addStretch()

        layout.addWidget(self._create_language_section(), 0, Qt.AlignmentFlag.AlignLeft)
        contentLayout.addWidget(self._create_welcome_section(), 0, Qt.AlignmentFlag.AlignHCenter)
        contentLayout.addSpacing(100)
        contentLayout.addWidget(self._create_input_fields(), 0, Qt.AlignmentFlag.AlignHCenter)
        contentLayout.addSpacing(50)
        contentLayout.addWidget(self._create_switch_section(), 0, Qt.AlignmentFlag.AlignHCenter)

        contentLayout.addStretch()

        layout.addWidget(contentFrame)

    """ Language switching """
    def _create_language_section(self) -> QWidget:
        widget = QWidget(self)
        widget.setObjectName("languageWidget")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(70, 70, 0, 0)

        self.langSkBtn = QPushButton("sk", widget)
        self.langSkBtn.setObjectName("langSkBtn")
        self.langSkBtn.setMaximumWidth(40)

        self.langEnBtn = QPushButton("en", widget)
        self.langEnBtn.setObjectName("langEnBtn")
        self.langEnBtn.setMaximumWidth(40)

        layout.addWidget(self.langSkBtn)
        layout.addWidget(self.langEnBtn)

        current_lang = get_language()
        self.langSkBtn.setProperty("selected", current_lang == "sk")
        self.langEnBtn.setProperty("selected", current_lang == "en")

        return widget

    def _create_welcome_section(self) -> QFrame:
        frame = QWidget(self)
        frame.setObjectName("welcomeFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(frame)
        layout.setSpacing(30)
        layout.setContentsMargins(0, 0, 0, 0)

        self.titleLabelLeft = QLabel(frame)
        self.titleLabelLeft.setObjectName("titleLabelLeft")
        self.titleLabelLeft.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.titleLabelLeft.setMaximumSize(QSize(16777215, 100))

        self.titleLabelRight = QLabel(frame)
        self.titleLabelRight.setObjectName("titleLabelRight")
        self.titleLabelRight.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.titleLabelRight.setMaximumSize(QSize(16777215, 100))

        layout.addWidget(self.titleLabelLeft, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.titleLabelRight, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.welcomeOpacity = QGraphicsOpacityEffect(self.titleLabelLeft)
        self.titleLabelLeft.setGraphicsEffect(self.welcomeOpacity)
        self.welcomeOpacity.setOpacity(0)

        self.logoOpacity = QGraphicsOpacityEffect(self.titleLabelRight)
        self.titleLabelRight.setGraphicsEffect(self.logoOpacity)
        self.logoOpacity.setOpacity(0)

        self.welcomeFrame = frame
        return frame

    def _create_input_fields(self) -> QFrame:
        frame = QWidget(self)
        frame.setObjectName("frame")
        frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        frame.setMaximumWidth(720)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # email field
        self.emailField = InputField(label_text="", placeholder="", object_name="emailEdit", parent=frame)
        self.emailField.installEventFilter(self)
        layout.addWidget(self.emailField, 0, Qt.AlignmentFlag.AlignHCenter)

        self.emailEdit = self.emailField.line_edit


        layout.addSpacing(25)
        # password field
        self.passwordField = InputField(label_text="", placeholder="", is_password=True, object_name="passwordEdit", parent=frame)
        self.passwordField.installEventFilter(self)
        layout.addWidget(self.passwordField, 0, Qt.AlignmentFlag.AlignHCenter)

        self.passwordEdit = self.passwordField.line_edit

        layout.addSpacing(10)
        self._create_forgot_password_link(frame)
        layout.addWidget(self.forgotPasswordLink, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout.addSpacing(60)        
        self._create_sign_in_button(frame)
        layout.addWidget(self.signInFrame, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.formFrame = frame
        return frame

    def _create_sign_in_button(self, frame: QFrame) -> QPushButton:
        frame = QWidget(self)
        frame.setObjectName("singInFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        frame.setMaximumWidth(720)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # sign in button
        self.signInButton = QPushButton(translate("LoginAuth", "Sign in"), frame)
        self.signInButton.setObjectName("primaryButton")
        self.signInButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.signInButton.setMinimumSize(QSize(130, 0))
        self.signInButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.signInButton, 0, Qt.AlignmentFlag.AlignHCenter)

        # opacity for animation sign in section
        self.signInOpacity = QGraphicsOpacityEffect(frame)
        frame.setGraphicsEffect(self.signInOpacity)
        self.signInOpacity.setOpacity(0)

        self.signInFrame = frame
        return frame

    def _create_forgot_password_link(self, frame: QFrame) -> QFrame:
        # forgot password link button
        self.forgotPasswordLink = QPushButton(translate("LoginAuth", "Forgot your password? Click here"), frame)
        self.forgotPasswordLink.setObjectName("forgotPasswordLink")
        self.forgotPasswordLink.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.forgotPasswordLink.setFlat(True)

        forgotPasswordFrame = QWidget(frame)
        forgotPasswordFrame.setObjectName("forgotPasswordFrame")
        forgotPasswordFrame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        forgotPasswordFrame.setMaximumWidth(600)

        forgotPasswordLayout = QHBoxLayout(forgotPasswordFrame)
        forgotPasswordLayout.setContentsMargins(0, 0, 0, 0)
        forgotPasswordLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        forgotPasswordLayout.addWidget(self.forgotPasswordLink)
        return forgotPasswordFrame

    def _create_switch_section(self) -> QFrame:
        frame = QWidget(self)
        frame.setObjectName("switchToFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(frame)

        # switch to registration button
        self.startRegistration = QPushButton(translate("LoginAuth", "Don't have an account? Sign up"), frame)
        self.startRegistration.setObjectName("startRegistration")
        self.startRegistration.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(self.startRegistration)

        # setup opacity for animation
        self.switchOpacity = QGraphicsOpacityEffect(frame)
        frame.setGraphicsEffect(self.switchOpacity)
        self.switchOpacity.setOpacity(0)

        self.switchFrame = frame
        return frame

    def _setup_connections(self):
        self.passwordEdit.installEventFilter(self)
        self.emailEdit.installEventFilter(self)

        self.signInButton.clicked.connect(self.handle_auth_login)
        self.startRegistration.clicked.connect(self.start_registration.emit)
        self.forgotPasswordLink.clicked.connect(self.forgot_password_signal.emit)

        self.langSkBtn.clicked.connect(lambda: self._change_language(self.langSkBtn, "sk"))
        self.langEnBtn.clicked.connect(lambda: self._change_language(self.langEnBtn, "en"))

    def _start_welcome_animation(self):
        left_final_pos = self.titleLabelLeft.pos()
        right_final_pos = self.titleLabelRight.pos()
        offset = 120
        welcome_start_pos = QPoint(left_final_pos.x() - offset, left_final_pos.y())
        logo_start_pos = QPoint(right_final_pos.x() + offset, right_final_pos.y())

        self.titleLabelLeft.move(welcome_start_pos)
        self.titleLabelRight.move(logo_start_pos)

        self.welcomePosAnim = QPropertyAnimation(self.titleLabelLeft, b"pos")
        self.welcomePosAnim.setDuration(1000)
        self.welcomePosAnim.setStartValue(welcome_start_pos)
        self.welcomePosAnim.setEndValue(left_final_pos)
        self.welcomePosAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.welcomeOpacityAnim = QPropertyAnimation(self.welcomeOpacity, b"opacity")
        self.welcomeOpacityAnim.setDuration(400)
        self.welcomeOpacityAnim.setStartValue(0.0)
        self.welcomeOpacityAnim.setEndValue(1.0)
        self.welcomeOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.logoPosAnim = QPropertyAnimation(self.titleLabelRight, b"pos")
        self.logoPosAnim.setDuration(1200)
        self.logoPosAnim.setStartValue(logo_start_pos)
        self.logoPosAnim.setEndValue(right_final_pos)
        self.logoPosAnim.setEasingCurve(QEasingCurve.Type.OutElastic)

        self.logoOpacityAnim = QPropertyAnimation(self.logoOpacity, b"opacity")
        self.logoOpacityAnim.setDuration(400)
        self.logoOpacityAnim.setStartValue(0.0)
        self.logoOpacityAnim.setEndValue(1.0)
        self.logoOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.formAnim = QPropertyAnimation(self.signInOpacity, b"opacity")
        self.formAnim.setDuration(1000)
        self.formAnim.setStartValue(0.0)
        self.formAnim.setEndValue(1.0)
        self.formAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.switchAnim = QPropertyAnimation(self.switchOpacity, b"opacity")
        self.switchAnim.setDuration(800)
        self.switchAnim.setStartValue(0.0)
        self.switchAnim.setEndValue(1.0)
        self.switchAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.welcomePosAnim.start()
        QTimer.singleShot(120, self.welcomeOpacityAnim.start)

        QTimer.singleShot(200, self.logoPosAnim.start)
        QTimer.singleShot(320, self.logoOpacityAnim.start)

        QTimer.singleShot(800, self.formAnim.start)
        QTimer.singleShot(1200, self.switchAnim.start)

    def show_login_error(self, message: str):
        self.state = "error"
        self.is_logging_in = False

        update_button_state(
            self.signInButton,
            "error",
            idle_text=translate("LoginAuth", "Sign in"),
            loading_text=translate("LoginAuth", "Signing in…"),
            error_text=message,
            auto_reset_ms=2000,
        )

        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def handle_auth_login(self):
        if self.state == "loading" or self.state == "error":
            logger.debug("Already logging in or showing error, ignoring click")
            return

        email = self.emailEdit.text().strip()
        password = self.passwordEdit.text().strip()

        if not email or not password:
            self.show_login_error(translate("LoginAuth", "Please enter email and password"))
            return

        self.state = "loading"
        self.is_logging_in = True

        update_button_state(
            self.signInButton,
            "loading",
            idle_text=translate("LoginAuth", "Sign in"),
            loading_text=translate("LoginAuth", "Signing in…"),
        )

        self.login_data_submit.emit(email, password)

    def reset_ui(self):
        self.emailEdit.clear()
        self.passwordEdit.clear()
        self.state = "idle"
        self.is_logging_in = False

        update_button_state(
        self.signInButton,
        "idle",
        idle_text=translate("LoginAuth", "Sign in"),
        loading_text=translate("LoginAuth", "Signing in…"),
        auto_reset_ms=None,
    )
        
    def _retranslate_ui(self):
        self.titleLabelLeft.setText(translate("LoginAuth", "welcome in"))
        self.titleLabelRight.setText(translate("LoginAuth", "Synapso"))

        self.emailField.setTitle(translate("LoginAuth", "Email"))
        self.emailField.setPlaceholderText(translate("LoginAuth", "john.doe@example.com"))
        
        self.passwordField.setTitle(translate("LoginAuth", "Password"))
        self.passwordField.setPlaceholderText("••••••••••••••")

        self.signInButton.setText(translate("LoginAuth", "Sign in"))
        self.forgotPasswordLink.setText(translate("LoginAuth", "Forgot your password? Click here"))
        self.startRegistration.setText(translate("LoginAuth", "Don't have an account? Sign up"))

    def _change_language(self, button: QPushButton, lang: str):
        other = self.langEnBtn if button is self.langSkBtn else self.langSkBtn
        other.setProperty("selected", False)
        other.style().unpolish(other)
        other.style().polish(other)

        button.setProperty("selected", True)
        button.style().unpolish(button)
        button.style().polish(button)

        set_language(lang)
        get_translation_manager().switch_language(lang)
        self._retranslate_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._retranslate_ui()
        if not self._animations_started:
            self._animations_started = True
            QTimer.singleShot(50, self._start_welcome_animation)

    def eventFilter(self, watched, event):
        if watched == self.passwordEdit:
            if password_event_filter(self, watched, event):
                return True

        if enter_key_event_filter(self, watched, event, on_enter=self.handle_auth_login):
            return True

        if context_menu_event_filter(self, watched, event):
            return True

        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        draw_background(self, event)