import re
from PySide6.QtWidgets import QWidget, QLineEdit
from PySide6.QtCore import QEvent, Qt, Signal
from app.utils import show_error, draw_background
from app.ui.register_auth_ui import Ui_registerAuth

class RegisterAuth(QWidget):
    # define signal for registration data and back request
    auth_data = Signal(str)
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        
        # initialize UI and set window title
        self.ui = Ui_registerAuth()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # event filter for showing/hiding password
        self.ui.passwordEdit.installEventFilter(self)
        self.ui.copasswordEdit.installEventFilter(self)

        # set password fields to password mode
        self.ui.passwordEdit.setEchoMode(QLineEdit.Password)
        self.ui.copasswordEdit.setEchoMode(QLineEdit.Password)

        # dynamic progress bar
        self.ui.progressBar.setGeometry(50, 250, 300, 20)
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setTextVisible(False)

        # connect password strength bar
        self.ui.passwordEdit.textChanged.connect(self.update_password_strength_bar)

        # connect sign up button
        self.ui.signUpButton.clicked.connect(self.handle_auth_register)
        # connect back button
        if hasattr(self.ui, 'back'):
            self.ui.back.clicked.connect(self.back_requested.emit)

    # evaluate password strength
    def evaluate_password_strength(self, password):
        score = 0
        if len(password) >= 8:
            score += 1
        if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        return int((score / 3) * 100)

    # update password strength bar by evaluating password
    def update_password_strength_bar(self):
        password = self.ui.passwordEdit.text()
        score = self.evaluate_password_strength(password)
        self.ui.progressBar.setValue(score)

        if score < 34:
            color = "#9E3F3F"
        elif score < 67:
            color = "#C98532"
        else:
            color = "#3A9A8F"

        self.ui.progressBar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)

    # handle sign up button click
    def handle_auth_register(self):
        password = self.ui.passwordEdit.text().strip()
        copassword = self.ui.copasswordEdit.text().strip()

        if not password or not copassword:
            show_error(self.ui.signUpButton, "Please fill in all fields")
            return

        if password != copassword:
            show_error(self.ui.signUpButton, "Passwords do not match")
            return

        if len(password) < 8:
            show_error(self.ui.signUpButton, "Password must be at least 8 characters")
            return
        if not re.search(r"[A-Z]", password):
            show_error(self.ui.signUpButton, "Password must contain at least one uppercase letter")
            return
        if not re.search(r"[a-z]", password):
            show_error(self.ui.signUpButton, "Password must contain at least one lowercase letter")
            return
        if not re.search(r"[0-9]", password):
            show_error(self.ui.signUpButton, "Password must contain at least one digit")
            return
        self.auth_data.emit(password)

    
    # key press event to handle Enter key
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.handle_auth_register()
            
    # paint event for custom background
    def paintEvent(self, event):
        draw_background(self, event)