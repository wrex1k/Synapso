from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QLineEdit
from app.ui.login_auth_ui import Ui_loginAuth
from app.utils import show_error, draw_background, password_event_filter, enter_key_event_filter, context_menu_event_filter
import re

class LoginAuth(QWidget):
    # define signals for login data and switching to register
    auth_login_data = Signal(str, str)
    switch_to_register_signal = Signal()

    def __init__(self):
        super().__init__()

        # initialize UI and set window title
        self.ui = Ui_loginAuth()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # event filter for showing/hiding password
        self.ui.passwordEdit.installEventFilter(self)
        self.ui.emailEdit.installEventFilter(self)
        self.ui.passwordEdit.setEchoMode(QLineEdit.Password)

        # connect signIn button
        self.ui.signInButton.clicked.connect(self.handle_auth_login)

        # connect switch to register button
        self.ui.switchToRegister.clicked.connect(self.switch_to_register_signal.emit)

    # handle login button click
    def handle_auth_login(self):
        email = self.ui.emailEdit.text().strip()
        password = self.ui.passwordEdit.text().strip()
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not email:
            show_error(self.ui.signInButton, "Missing email")
            return
        if not re.match(email_regex, email):
            show_error(self.ui.signInButton, "Invalid email")
            return
        if not password:
            show_error(self.ui.signInButton, "Missing password")
            return

        self.auth_login_data.emit(email, password)

    def eventFilter(self, watched, event):
        if watched == self.ui.passwordEdit:
            if password_event_filter(self, watched, event):
                return True
        if enter_key_event_filter(self, watched, event):
            return True
        if context_menu_event_filter(self, watched, event):
            return True
        return super().eventFilter(watched, event)

    # paint event for custom background
    def paintEvent(self, event):
        draw_background(self, event)
