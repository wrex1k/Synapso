from PySide6.QtCore import Signal, QEvent
from PySide6.QtWidgets import QWidget, QLineEdit
from app.ui.login_auth_ui import Ui_loginAuth
from app.utils import show_error, draw_background, shared_event_filter
import re

class LoginAuth(QWidget):
    auth_login_data = Signal(str, str)
    switch_to_register_signal = Signal()

    def __init__(self):
        super().__init__()

        self.ui = Ui_loginAuth()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # event filter for showing/hiding password
        self.ui.passwordEdit.installEventFilter(self)
        self.ui.passwordEdit.setEchoMode(QLineEdit.Password)

        # connect signIn button
        self.ui.signInButton.clicked.connect(self.handle_auth_login)

        # connect switch to register button
        self.ui.switchToRegister.clicked.connect(self.switch_to_register_signal.emit)

    def handle_auth_login(self):
        email = self.ui.emailEdit.text().strip()
        password = self.ui.passwordEdit.text().strip()

        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            show_error(self.ui.signInButton, "Invalid email")
            return
        if not password:
            show_error(self.ui.signInButton, "Missing password")
            return

        self.auth_login_data.emit(email, password)

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        return shared_event_filter(self, watched, event)

    def paintEvent(self, event):
        draw_background(self, event)
        super().paintEvent(event)

