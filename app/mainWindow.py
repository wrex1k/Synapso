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

        self.auth_page = AuthPage()
        self.auth_page.login_success.connect(self.on_login_success)
        self.stack.addWidget(self.auth_page)

        if skip_login:
            self.on_login_success("Username")
        else:
            self.stack.setCurrentWidget(self.auth_page)

    def on_login_success(self, username: str):
        self.app_widget = AppWidget(username)
        self.app_widget.logout_requested.connect(self.handle_logout)

        if self.stack.indexOf(self.app_widget) == -1:
            self.stack.addWidget(self.app_widget)

        self.stack.setCurrentWidget(self.app_widget)

    def handle_logout(self):
        # set active false in db
        self.stack.setCurrentWidget(self.auth_page)
