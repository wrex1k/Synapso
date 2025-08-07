# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'authPage.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLayout,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_authPage(object):
    def setupUi(self, authPage):
        if not authPage.objectName():
            authPage.setObjectName(u"authPage")
        authPage.setWindowModality(Qt.WindowModality.NonModal)
        authPage.resize(836, 800)
        authPage.setMinimumSize(QSize(800, 800))
        authPage.setStyleSheet(u"/* global */\n"
"QPushButton, QLineEdit {\n"
"font: 11pt;\n"
"font-weight: 400;\n"
"color: #fafafa;\n"
"}\n"
"\n"
"/* switchTo */\n"
"QPushButton#btnSwitchToRegister,\n"
"QPushButton#btnSwitchToLogin {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"}\n"
"QPushButton#btnSwitchToRegister:hover,\n"
"QPushButton#btnSwitchToLogin:hover {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"	color: #3c8573\n"
"}\n"
"\n"
"/* PushButton */\n"
"QPushButton  {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 35px;\n"
"    padding: 6px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"    font: 11pt;\n"
"	font-weight: 400;\n"
"	outline: none;\n"
"}\n"
"QPushButton:hover {\n"
"    border: 1px solid #93cabc;\n"
"    background-color: #181818;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #0f0f0f;\n"
"    border: 1px solid #6fb8a6;\n"
"}\n"
"\n"
"/* LineEdit */\n"
"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius:"
                        " 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.verticalLayout_3 = QVBoxLayout(authPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 9, -1, -1)
        self.spacer = QSpacerItem(20, 100, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.verticalLayout_3.addItem(self.spacer)

        self.logoLabel = QLabel(authPage)
        self.logoLabel.setObjectName(u"logoLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMaximumSize(QSize(16777215, 100))
        font = QFont()
        font.setFamilies([u"General Sans"])
        font.setPointSize(72)
        font.setWeight(QFont.DemiBold)
        font.setItalic(False)
        self.logoLabel.setFont(font)
        self.logoLabel.setStyleSheet(u"QLabel#logoLabel {\n"
"	color: #4BA690;\n"
"	font-size: 72pt;\n"
"	font-weight: 600;\n"
"}")
        self.logoLabel.setFrameShape(QFrame.Shape.NoFrame)
        self.logoLabel.setFrameShadow(QFrame.Shadow.Raised)
        self.logoLabel.setTextFormat(Qt.TextFormat.AutoText)

        self.verticalLayout_3.addWidget(self.logoLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        self.verticalSpacer = QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.stackedWidget = QStackedWidget(authPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.registerPage = QWidget()
        self.registerPage.setObjectName(u"registerPage")
        self.verticalLayout = QVBoxLayout(self.registerPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.register_input_fields_layout = QVBoxLayout()
        self.register_input_fields_layout.setSpacing(20)
        self.register_input_fields_layout.setObjectName(u"register_input_fields_layout")
        self.register_input_fields_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.register_input_fields_layout.setContentsMargins(-1, 0, -1, 0)
        self.registerUsername = QLineEdit(self.registerPage)
        self.registerUsername.setObjectName(u"registerUsername")
        self.registerUsername.setMinimumSize(QSize(600, 45))
        self.registerUsername.setMaximumSize(QSize(800, 45))
        self.registerUsername.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerUsername.setAutoFillBackground(False)
        self.registerUsername.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.register_input_fields_layout.addWidget(self.registerUsername, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerEmail = QLineEdit(self.registerPage)
        self.registerEmail.setObjectName(u"registerEmail")
        self.registerEmail.setMinimumSize(QSize(600, 45))
        self.registerEmail.setMaximumSize(QSize(800, 45))
        self.registerEmail.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerEmail.setAutoFillBackground(False)
        self.registerEmail.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.register_input_fields_layout.addWidget(self.registerEmail, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerPassword = QLineEdit(self.registerPage)
        self.registerPassword.setObjectName(u"registerPassword")
        self.registerPassword.setMinimumSize(QSize(600, 45))
        self.registerPassword.setMaximumSize(QSize(800, 45))
        self.registerPassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerPassword.setAutoFillBackground(False)
        self.registerPassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.register_input_fields_layout.addWidget(self.registerPassword, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerRePassword = QLineEdit(self.registerPage)
        self.registerRePassword.setObjectName(u"registerRePassword")
        self.registerRePassword.setMinimumSize(QSize(600, 45))
        self.registerRePassword.setMaximumSize(QSize(800, 45))
        self.registerRePassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerRePassword.setAutoFillBackground(False)
        self.registerRePassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.register_input_fields_layout.addWidget(self.registerRePassword, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout.addLayout(self.register_input_fields_layout)

        self.register_actions_layout = QVBoxLayout()
        self.register_actions_layout.setSpacing(20)
        self.register_actions_layout.setObjectName(u"register_actions_layout")
        self.registerStatus = QLabel(self.registerPage)
        self.registerStatus.setObjectName(u"registerStatus")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.registerStatus.sizePolicy().hasHeightForWidth())
        self.registerStatus.setSizePolicy(sizePolicy1)
        self.registerStatus.setMaximumSize(QSize(16777215, 40))
        self.registerStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.register_actions_layout.addWidget(self.registerStatus, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnRegister = QPushButton(self.registerPage)
        self.btnRegister.setObjectName(u"btnRegister")
        sizePolicy1.setHeightForWidth(self.btnRegister.sizePolicy().hasHeightForWidth())
        self.btnRegister.setSizePolicy(sizePolicy1)
        self.btnRegister.setMinimumSize(QSize(400, 80))
        self.btnRegister.setMaximumSize(QSize(400, 80))
        font1 = QFont()
        font1.setFamilies([u"General Sans"])
        font1.setPointSize(11)
        font1.setBold(False)
        font1.setItalic(False)
        self.btnRegister.setFont(font1)
        self.btnRegister.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.btnRegister.setMouseTracking(True)
        self.btnRegister.setCheckable(False)

        self.register_actions_layout.addWidget(self.btnRegister, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnSwitchToLogin = QPushButton(self.registerPage)
        self.btnSwitchToLogin.setObjectName(u"btnSwitchToLogin")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btnSwitchToLogin.sizePolicy().hasHeightForWidth())
        self.btnSwitchToLogin.setSizePolicy(sizePolicy2)
        self.btnSwitchToLogin.setMaximumSize(QSize(16777215, 50))
        self.btnSwitchToLogin.setFont(font1)
        self.btnSwitchToLogin.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnSwitchToLogin.setFlat(False)

        self.register_actions_layout.addWidget(self.btnSwitchToLogin, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout.addLayout(self.register_actions_layout)

        self.stackedWidget.addWidget(self.registerPage)
        self.loginPage = QWidget()
        self.loginPage.setObjectName(u"loginPage")
        self.verticalLayout_2 = QVBoxLayout(self.loginPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.login_input_fields_layout = QVBoxLayout()
        self.login_input_fields_layout.setSpacing(20)
        self.login_input_fields_layout.setObjectName(u"login_input_fields_layout")
        self.login_input_fields_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.login_input_fields_layout.setContentsMargins(-1, 0, -1, 0)
        self.loginUsername = QLineEdit(self.loginPage)
        self.loginUsername.setObjectName(u"loginUsername")
        self.loginUsername.setMinimumSize(QSize(600, 45))
        self.loginUsername.setMaximumSize(QSize(800, 45))
        self.loginUsername.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.loginUsername.setAutoFillBackground(False)
        self.loginUsername.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.login_input_fields_layout.addWidget(self.loginUsername, 0, Qt.AlignmentFlag.AlignHCenter)

        self.loginPassword = QLineEdit(self.loginPage)
        self.loginPassword.setObjectName(u"loginPassword")
        self.loginPassword.setMinimumSize(QSize(600, 45))
        self.loginPassword.setMaximumSize(QSize(800, 45))
        self.loginPassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.loginPassword.setAutoFillBackground(False)
        self.loginPassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.login_input_fields_layout.addWidget(self.loginPassword, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_2.addLayout(self.login_input_fields_layout)

        self.login_actions_layout = QVBoxLayout()
        self.login_actions_layout.setSpacing(20)
        self.login_actions_layout.setObjectName(u"login_actions_layout")
        self.loginStatus = QLabel(self.loginPage)
        self.loginStatus.setObjectName(u"loginStatus")
        self.loginStatus.setMaximumSize(QSize(16777215, 40))

        self.login_actions_layout.addWidget(self.loginStatus, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnLogin = QPushButton(self.loginPage)
        self.btnLogin.setObjectName(u"btnLogin")
        sizePolicy1.setHeightForWidth(self.btnLogin.sizePolicy().hasHeightForWidth())
        self.btnLogin.setSizePolicy(sizePolicy1)
        self.btnLogin.setMinimumSize(QSize(400, 80))
        self.btnLogin.setMaximumSize(QSize(400, 80))
        self.btnLogin.setFont(font1)
        self.btnLogin.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.btnLogin.setMouseTracking(True)
        self.btnLogin.setCheckable(False)

        self.login_actions_layout.addWidget(self.btnLogin, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnSwitchToRegister = QPushButton(self.loginPage)
        self.btnSwitchToRegister.setObjectName(u"btnSwitchToRegister")
        sizePolicy2.setHeightForWidth(self.btnSwitchToRegister.sizePolicy().hasHeightForWidth())
        self.btnSwitchToRegister.setSizePolicy(sizePolicy2)
        self.btnSwitchToRegister.setMaximumSize(QSize(16777215, 50))
        self.btnSwitchToRegister.setFont(font1)
        self.btnSwitchToRegister.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnSwitchToRegister.setFlat(False)

        self.login_actions_layout.addWidget(self.btnSwitchToRegister, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_2.addLayout(self.login_actions_layout)

        self.stackedWidget.addWidget(self.loginPage)

        self.verticalLayout_3.addWidget(self.stackedWidget)


        self.retranslateUi(authPage)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(authPage)
    # setupUi

    def retranslateUi(self, authPage):
        authPage.setWindowTitle(QCoreApplication.translate("authPage", u"Form", None))
        self.logoLabel.setText(QCoreApplication.translate("authPage", u"Synapso", None))
        self.registerUsername.setText("")
        self.registerStatus.setText("")
#if QT_CONFIG(accessibility)
        self.btnRegister.setAccessibleDescription("")
#endif // QT_CONFIG(accessibility)
        self.btnRegister.setText(QCoreApplication.translate("authPage", u"Registrova\u0165", None))
        self.btnSwitchToLogin.setText(QCoreApplication.translate("authPage", u"Chcem sa prihl\u00e1si\u0165", None))
        self.loginPassword.setText("")
        self.loginStatus.setText("")
#if QT_CONFIG(accessibility)
        self.btnLogin.setAccessibleDescription("")
#endif // QT_CONFIG(accessibility)
        self.btnLogin.setText(QCoreApplication.translate("authPage", u"Prihl\u00e1si\u0165", None))
        self.btnSwitchToRegister.setText(QCoreApplication.translate("authPage", u"Chcem sa zaregistrova\u0165", None))
    # retranslateUi

