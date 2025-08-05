import re, datetime
import bcrypt
from PySide6.QtWidgets import QWidget, QLineEdit, QMainWindow
from PySide6.QtCore import QObject, QEvent
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt 
from PySide6.QtGui import QPainter, QPixmap
from app.ui.authPage_ui import Ui_authPage  
from PySide6.QtCore import QUrl
from app.db.connection import get_connection


class AuthPage(QWidget):
    login_success = Signal(str)

    def __init__(self):
        super().__init__()

        self.ui = Ui_authPage()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")
        
        self.ui.loginUsername.setPlaceholderText("Používateľské meno")
        self.ui.loginPassword.setPlaceholderText("Heslo")
        self.ui.registerUsername.setPlaceholderText("Používateľské meno")
        self.ui.registerEmail.setPlaceholderText("Email")
        self.ui.registerPassword.setPlaceholderText("Heslo")
        self.ui.registerRePassword.setPlaceholderText("Potvrď heslo")

        self.ui.loginPassword.setEchoMode(QLineEdit.Password)
        self.ui.registerPassword.setEchoMode(QLineEdit.Password)
        self.ui.registerRePassword.setEchoMode(QLineEdit.Password)

        self.ui.btnLogin.clicked.connect(self.handle_login)
        self.ui.btnRegister.clicked.connect(self.handle_register)

        self.ui.btnSwitchToRegister.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.registerPage))
        self.ui.btnSwitchToLogin.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.loginPage))


        self.ui.loginPassword.installEventFilter(self)
        self.ui.registerPassword.installEventFilter(self)
        self.ui.registerRePassword.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Enter:
            if isinstance(watched, QLineEdit):
                watched.setEchoMode(QLineEdit.Normal)
            return True 
        elif event.type() == QEvent.Leave:
            if isinstance(watched, QLineEdit):
                watched.setEchoMode(QLineEdit.Password)
            return True

        return super().eventFilter(watched, event)
        
    def handle_login(self):
        username = self.ui.loginUsername.text().strip()
        password = self.ui.loginPassword.text().strip()
        self.ui.loginStatus.setText("")
        if not username or not password:
            self.ui.loginStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")
            self.ui.loginStatus.setText("Zadaj meno a heslo.")
            return

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cursor: 
                cursor.execute("SELECT username, email, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    cursor.execute(
                        "UPDATE users SET last_login = %s, active = %s WHERE username = %s",
                        (datetime.datetime.now(), True, username)
                    )
                    self.ui.loginStatus.setStyleSheet("color: #3CB371; font: 11pt; font-weight: 400;")
                    self.ui.loginStatus.setText(f"Prihlásenie úspešné!")
                    self.login_success.emit(username)
                else:
                    self.ui.loginStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")
                    self.ui.loginStatus.setText("Nesprávne meno alebo heslo.")
        except Exception as e:
            self.ui.loginStatus.setText(f"Chyba: {e}")
        finally:
            if conn:
                conn.close()

    def handle_register(self):
        username = self.ui.registerUsername.text().strip()
        email = self.ui.registerEmail.text().strip()
        password = self.ui.registerPassword.text().strip()
        re_password = self.ui.registerRePassword.text().strip()
        self.ui.registerStatus.setText("")
        self.ui.registerStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")

        if not username:
            self.ui.registerStatus.setText("Zadaj používateľské meno.")
            return
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not email or not re.match(email_regex, email):
            self.ui.registerStatus.setText("Zadaj platný email.")
            return
        if not password or not re_password:
            self.ui.registerStatus.setText("Zadaj heslo aj potvrdenie hesla.")
            return
        if password != re_password:
            self.ui.registerStatus.setText("Heslá sa nezhodujú.")
            return
        if len(password) < 8:
            self.ui.registerStatus.setText("Heslo musí mať aspoň 8 znakov.")
            return
        if not re.search(r'[A-Z]', password):
            self.ui.registerStatus.setText("Heslo musí obsahovať aspoň jedno veľké písmeno.")
            return

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cursor: 
                cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    self.ui.registerStatus.setText("Používateľ alebo email už existuje.")
                    return
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_pw.decode('utf-8'))
                )
                conn.commit()
                self.ui.registerStatus.setStyleSheet("color: #3CB371; font: 11pt; font-weight: 400;")
                self.ui.registerStatus.setText("Registrácia úspešná! Prosím prihlás sa.")
                self.ui.stackedWidget.setCurrentWidget(self.ui.loginPage)
        except Exception as e:
            self.ui.registerStatus.setText(f"Chyba: {e}")
        finally:
            if conn:
                conn.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(":/images/backgrounds/bg.png")
        painter.drawPixmap(self.rect(), pixmap)
        super().paintEvent(event)
