import re, bcrypt, datetime, uuid
from PySide6.QtWidgets import QWidget, QLineEdit, QDateEdit
from PySide6 import QtWidgets
from PySide6.QtCore import QEvent, Qt, Signal, QDate
from PySide6.QtGui import QPainter, QPixmap
from app.ui.gen.authPage_ui import Ui_authPage  
from app.db.connection import query

class AuthPage(QWidget):
    login_success = Signal(str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_authPage()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # set placeholders
        self.ui.loginIdentifier.setPlaceholderText("Používateľské meno alebo email")
        self.ui.loginPassword.setPlaceholderText("Heslo")
        self.ui.registerUsername.setPlaceholderText("Používateľské meno")
        self.ui.registerEmail.setPlaceholderText("Email")
        self.ui.registerPassword.setPlaceholderText("Heslo")
        self.ui.registerRePassword.setPlaceholderText("Potvrď heslo")
        
        # deleted switchdate buttons from date field
        self.ui.registerDate.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.ui.registerDate.setMinimumDate(QDate(1900, 1, 1)) 
        self.ui.registerDate.setMaximumDate(QDate.currentDate())
        self.ui.registerDate.setDate(QDate.currentDate())

        # set echo modes for password fields
        self.ui.loginPassword.setEchoMode(QLineEdit.Password)
        self.ui.registerPassword.setEchoMode(QLineEdit.Password)
        self.ui.registerRePassword.setEchoMode(QLineEdit.Password)

        # connect buttons (login, register, both switches)
        self.ui.btnLogin.clicked.connect(self.handle_login)
        self.ui.btnRegister.clicked.connect(self.handle_register)
        self.ui.btnSwitchToRegister.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.registerPage))
        self.ui.btnSwitchToLogin.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.loginPage))

        # install event filters for showing/hiding password on hover
        self.ui.loginPassword.installEventFilter(self)
        self.ui.registerPassword.installEventFilter(self)
        self.ui.registerRePassword.installEventFilter(self)

    def eventFilter(self, watched: QWidget, event: QEvent):
        # show password on hover, hide on leave
        if event.type() == QEvent.Enter:    
            if isinstance(watched, (QLineEdit, QDateEdit)):
                watched.setEchoMode(QLineEdit.Normal)
            return True 
        elif event.type() == QEvent.Leave:
            if isinstance(watched, (QLineEdit, QDateEdit)):
                watched.setEchoMode(QLineEdit.Password)
            return True
        return super().eventFilter(watched, event)
        
    def handle_login(self):
        # get login data
        identifier  = self.ui.loginIdentifier.text().strip()
        password = self.ui.loginPassword.text().strip()
        self.ui.loginStatus.setText("")
        
        self.ui.loginStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")
        if not identifier:
            self.ui.loginStatus.setText("Zadaj meno alebo email.")
        if not password:
            self.ui.loginStatus.setText("Zadaj heslo.")
            return

        # choose query by email or username
        if "@" in identifier:
            result = query("SELECT id, username, email, password FROM users WHERE email=%s;", (identifier,))
            print("Email login attempt.")
        else:
            result = query("SELECT id, username, email, password FROM users WHERE username=%s;", (identifier,))
            print("Username login attempt.")

        # verify password
        if result:
            user = result[0]
            print(f"User found: {user}")
            if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                query(
                    "UPDATE users SET last_login=%s WHERE id=%s;",
                    (datetime.datetime.now(), user[0])
                )
                self.ui.loginStatus.setStyleSheet("color: #3CB371; font: 11pt; font-weight: 400;")
                self.login_success.emit(user[0])
                self.ui.loginStatus.setText("Prihlásenie úspešné!")
                self.clearLoginFields()
                return

        self.ui.loginStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")
        self.ui.loginStatus.setText("Nesprávne meno alebo heslo.")

    def handle_register(self):
        # get registration data
        username = self.ui.registerUsername.text().strip()
        email = self.ui.registerEmail.text().strip()
        password = self.ui.registerPassword.text().strip()
        re_password = self.ui.registerRePassword.text().strip()
        birthday_date = self.ui.registerDate.date().toPython()

        self.ui.registerStatus.setText("")
        self.ui.registerStatus.setStyleSheet("color: #E94B3C; font: 11pt; font-weight: 400;")

        # validate registration data
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

        # check age >= 13
        today = datetime.date.today()
        min_birth_date = today.replace(year=today.year - 13)
        if birthday_date > min_birth_date:
            self.ui.registerStatus.setText("Musíš mať aspoň 13 rokov.")
            return

        # check if user/email exists
        existing_user = query(
            "SELECT id FROM users WHERE username=%s OR email=%s;",
            (username, email)
        )
        if existing_user:
            self.ui.registerStatus.setText("Používateľ alebo email už existuje.")
            return

        # hash password and insert new user
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = str(uuid.uuid4())
        now = datetime.datetime.now()

        query(
            """
            INSERT INTO users (id, username, email, password, birthday, last_login, last_active)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (user_id, username, email, hashed_pw, birthday_date, now, now)
        )

        # success message
        self.ui.registerStatus.setStyleSheet("color: #3CB371; font: 11pt; font-weight: 400;")
        self.ui.registerStatus.setText("Registrácia úspešná! Prosím prihlás sa.")
        self.ui.stackedWidget.setCurrentWidget(self.ui.loginPage)
        self.clearRegisterFields()

    # draw background image 
    #! TODO: move function to proper file 
    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(":/images/backgrounds/bg.png")
        painter.drawPixmap(self.rect(), pixmap)
        super().paintEvent(event)

    # handle Enter key for login/register
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_widget = self.ui.stackedWidget.currentWidget()
            if current_widget == self.ui.loginPage:
                self.handle_login()
            elif current_widget == self.ui.registerPage:
                self.handle_register()

    # clear registration fields
    def clearRegisterFields(self):
        self.ui.registerUsername.clear()
        self.ui.registerEmail.clear()
        self.ui.registerPassword.clear()
        self.ui.registerRePassword.clear()
        self.ui.registerStatus.setText("")

    # clear login fields
    def clearLoginFields(self):
        self.ui.loginIdentifier.clear()
        self.ui.loginPassword.clear()
        self.ui.loginStatus.setText("")