from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.input_field import InputField
from app.utils.event_filters import context_menu_event_filter, enter_key_event_filter, password_event_filter
from app.utils.logger import get_logger
logger = get_logger(__name__)
from app.utils.settings import get_language, set_language
from app.utils.ui_helpers import draw_background, update_button_state
from translations.translation import get_translation_manager, translate

"""
LoginAuth view manages the login screen, including the welcome animation, form input,
and error display. It emits signals for login attempts and navigation to registration and forgot password views.
"""


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

        self._title_anim_offset = 120
        self._title_spacing = 30

        self._build_ui()
        self._setup_connections()
        self._retranslate_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._create_language_section(), 0, Qt.AlignmentFlag.AlignLeft)

        contentFrame = QWidget(self)
        contentFrame.setObjectName("contentFrame")
        contentFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        contentLayout = QVBoxLayout(contentFrame)
        contentLayout.setSpacing(0)

        contentLayout.addStretch()
        contentLayout.addWidget(self._create_welcome_section(), 0, Qt.AlignmentFlag.AlignHCenter)
        contentLayout.addSpacing(100)
        contentLayout.addWidget(self._create_input_fields(), 0, Qt.AlignmentFlag.AlignHCenter)
        contentLayout.addSpacing(50)
        contentLayout.addWidget(self._create_switch_section(), 0, Qt.AlignmentFlag.AlignHCenter)
        contentLayout.addStretch()

        layout.addWidget(contentFrame)

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

    def _create_welcome_section(self) -> QWidget:
        frame = QWidget(self)
        frame.setObjectName("welcomeFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.animCanvas = QWidget(frame)
        self.animCanvas.setObjectName("animCanvas")
        self.animCanvas.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.titleLabelLeft = QLabel(self.animCanvas)
        self.titleLabelLeft.setObjectName("titleLabelLeft")
        self.titleLabelLeft.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.titleLabelLeft.setMaximumSize(QSize(16777215, 100))

        self.titleLabelRight = QLabel(self.animCanvas)
        self.titleLabelRight.setObjectName("titleLabelRight")
        self.titleLabelRight.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.titleLabelRight.setMaximumSize(QSize(16777215, 100))

        layout.addWidget(self.animCanvas)

        self.welcomeOpacity = QGraphicsOpacityEffect(self.titleLabelLeft)
        self.titleLabelLeft.setGraphicsEffect(self.welcomeOpacity)
        self.welcomeOpacity.setOpacity(0)

        self.logoOpacity = QGraphicsOpacityEffect(self.titleLabelRight)
        self.titleLabelRight.setGraphicsEffect(self.logoOpacity)
        self.logoOpacity.setOpacity(0)

        self.welcomeFrame = frame
        return frame

    def _update_welcome_layout_geometry(self):
        self.titleLabelLeft.adjustSize()
        self.titleLabelRight.adjustSize()

        offset = self._title_anim_offset
        spacing = self._title_spacing

        left_w = self.titleLabelLeft.sizeHint().width()
        left_h = self.titleLabelLeft.sizeHint().height()
        right_w = self.titleLabelRight.sizeHint().width()
        right_h = self.titleLabelRight.sizeHint().height()

        canvas_h = max(left_h, right_h, 100)
        canvas_w = left_w + right_w + spacing + (offset * 2)

        self.animCanvas.setFixedSize(canvas_w, canvas_h)

        left_y = (canvas_h - left_h) // 2
        right_y = (canvas_h - right_h) // 2

        self._left_final_pos = QPoint(offset, left_y)
        self._right_final_pos = QPoint(offset + left_w + spacing, right_y)

        self.titleLabelLeft.resize(left_w, left_h)
        self.titleLabelRight.resize(right_w, right_h)

        self.titleLabelLeft.move(self._left_final_pos)
        self.titleLabelRight.move(self._right_final_pos)

    def _create_input_fields(self) -> QWidget:
        frame = QWidget(self)
        frame.setObjectName("frame")
        frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        frame.setMaximumWidth(720)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.emailField = InputField(label_text="", placeholder="", object_name="emailEdit", parent=frame)
        self.emailField.installEventFilter(self)
        layout.addWidget(self.emailField, 0, Qt.AlignmentFlag.AlignHCenter)
        self.emailEdit = self.emailField.line_edit

        layout.addSpacing(25)

        self.passwordField = InputField(
            label_text="",
            placeholder="",
            is_password=True,
            object_name="passwordEdit",
            parent=frame,
        )
        self.passwordField.installEventFilter(self)
        layout.addWidget(self.passwordField, 0, Qt.AlignmentFlag.AlignHCenter)
        self.passwordEdit = self.passwordField.line_edit

        layout.addSpacing(10)

        forgot_password_frame = self._create_forgot_password_link(frame)
        layout.addWidget(forgot_password_frame, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout.addSpacing(60)

        self._create_sign_in_button(frame)
        layout.addWidget(self.signInFrame, 0, Qt.AlignmentFlag.AlignHCenter)

        self.formOpacity = QGraphicsOpacityEffect(frame)
        frame.setGraphicsEffect(self.formOpacity)
        self.formOpacity.setOpacity(0)

        self.formFrame = frame
        return frame

    def _create_sign_in_button(self, parent: QWidget) -> QWidget:
        frame = QWidget(parent)
        frame.setObjectName("singInFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        frame.setMaximumWidth(720)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.signInButton = QPushButton(translate("LoginAuth", "Sign in"), frame)
        self.signInButton.setObjectName("primaryButton")
        self.signInButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.signInButton.setMinimumSize(QSize(130, 0))
        self.signInButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.signInButton, 0, Qt.AlignmentFlag.AlignHCenter)

        self.signInFrame = frame
        return frame

    def _create_forgot_password_link(self, frame: QWidget) -> QWidget:
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

    def _create_switch_section(self) -> QWidget:
        frame = QWidget(self)
        frame.setObjectName("switchToFrame")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(frame)

        self.startRegistration = QPushButton(translate("LoginAuth", "Don't have an account? Sign up"), frame)
        self.startRegistration.setObjectName("startRegistration")
        self.startRegistration.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.startRegistration)

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
        self._update_welcome_layout_geometry()

        left_final_pos = self._left_final_pos
        right_final_pos = self._right_final_pos
        offset = self._title_anim_offset

        left_start_pos = QPoint(left_final_pos.x() - offset, left_final_pos.y())
        right_start_pos = QPoint(right_final_pos.x() + offset, right_final_pos.y())

        self.titleLabelLeft.move(left_start_pos)
        self.titleLabelRight.move(right_start_pos)

        self.welcomePosAnim = QPropertyAnimation(self.titleLabelLeft, b"pos")
        self.welcomePosAnim.setDuration(900)
        self.welcomePosAnim.setStartValue(left_start_pos)
        self.welcomePosAnim.setEndValue(left_final_pos)
        self.welcomePosAnim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.welcomeOpacityAnim = QPropertyAnimation(self.welcomeOpacity, b"opacity")
        self.welcomeOpacityAnim.setDuration(350)
        self.welcomeOpacityAnim.setStartValue(0.0)
        self.welcomeOpacityAnim.setEndValue(1.0)
        self.welcomeOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.logoPosAnim = QPropertyAnimation(self.titleLabelRight, b"pos")
        self.logoPosAnim.setDuration(1000)
        self.logoPosAnim.setStartValue(right_start_pos)
        self.logoPosAnim.setEndValue(right_final_pos)
        self.logoPosAnim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.logoOpacityAnim = QPropertyAnimation(self.logoOpacity, b"opacity")
        self.logoOpacityAnim.setDuration(350)
        self.logoOpacityAnim.setStartValue(0.0)
        self.logoOpacityAnim.setEndValue(1.0)
        self.logoOpacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.formAnim = QPropertyAnimation(self.formOpacity, b"opacity")
        self.formAnim.setDuration(700)
        self.formAnim.setStartValue(0.0)
        self.formAnim.setEndValue(1.0)
        self.formAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.switchAnim = QPropertyAnimation(self.switchOpacity, b"opacity")
        self.switchAnim.setDuration(600)
        self.switchAnim.setStartValue(0.0)
        self.switchAnim.setEndValue(1.0)
        self.switchAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.welcomePosAnim.start()
        QTimer.singleShot(100, self.welcomeOpacityAnim.start)

        QTimer.singleShot(150, self.logoPosAnim.start)
        QTimer.singleShot(250, self.logoOpacityAnim.start)

        QTimer.singleShot(1250, self.formAnim.start)
        QTimer.singleShot(1750, self.switchAnim.start)

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

        current_lang = get_language()
        self.langSkBtn.setProperty("selected", current_lang == "sk")
        self.langEnBtn.setProperty("selected", current_lang == "en")
        self.langSkBtn.style().unpolish(self.langSkBtn)
        self.langSkBtn.style().polish(self.langSkBtn)
        self.langEnBtn.style().unpolish(self.langEnBtn)
        self.langEnBtn.style().polish(self.langEnBtn)

        self._update_welcome_layout_geometry()

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
            self.formOpacity.setOpacity(0)
            self.switchOpacity.setOpacity(0)
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