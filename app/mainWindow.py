from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import QTimer
from app.pages.authPage import AuthPage
from app.shell.appWidget import AppWidget
from app.shell.appSession import AppSession
from app.db.connection import query

# Skip login for testing purposes
skip_login = True
admin_id = "6664a0be-4540-4a97-8756-8a5c3b6e30ba"
admin_username = "admin"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapso")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(60000)

        if skip_login:
            self.on_login_success(admin_id)
        else:
            self.auth_page = AuthPage()
            self.stack.addWidget(self.auth_page)
            self.stack.setCurrentWidget(self.auth_page)
            self.auth_page.login_success.connect(self.on_login_success)

    def on_login_success(self, user_id=None):
        result = query("SELECT username FROM users WHERE id = %s", (str(user_id),))
        user_id = user_id
        username = result[0][0]

        AppSession.current_user_id = user_id
        AppSession.current_username = username
        print(f"Session for {username} with UUID {user_id} started.")

        self.app = AppWidget()
        self.stack.addWidget(self.app)
        self.stack.setCurrentWidget(self.app)
        self.app.logout_requested.connect(self.handle_logout)

    def handle_logout(self):
        AppSession.current_user_id = None
        self.stack.setCurrentWidget(self.auth_page)

    def send_heartbeat(self):
        if AppSession.current_user_id is not None:
            sql = "UPDATE users SET last_active = NOW() WHERE id = %s"
            query(sql, (AppSession.current_user_id,))
