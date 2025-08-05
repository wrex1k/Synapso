from PySide6.QtWidgets import QMainWindow, QStackedWidget
from app.pages.authPage import AuthPage
from app.shell.appWidget import AppWidget

skip_login = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapso")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        if skip_login:
            self.on_login_success("Username")
        else:
            self.auth_page = AuthPage()
            self.stack.addWidget(self.auth_page)
            self.auth_page.login_success.connect(self.on_login_success)

    def on_login_success(self, username: str):
        self.app_widget = AppWidget(username)
        self.stack.addWidget(self.app_widget)
        self.stack.setCurrentWidget(self.app_widget)

