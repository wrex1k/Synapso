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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

class Ui_authPage(object):
    def setupUi(self, authPage):
        if not authPage.objectName():
            authPage.setObjectName(u"authPage")
        authPage.setWindowModality(Qt.WindowModality.NonModal)
        authPage.resize(816, 800)
        authPage.setMinimumSize(QSize(800, 800))
        self.horizontalLayout = QHBoxLayout(authPage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(50)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, -1)
        self.labelLayout = QHBoxLayout()
        self.labelLayout.setSpacing(0)
        self.labelLayout.setObjectName(u"labelLayout")
        self.labelLayout.setContentsMargins(-1, 75, -1, 50)
        self.logoLabel = QLabel(authPage)
        self.logoLabel.setObjectName(u"logoLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMaximumSize(QSize(16777215, 100))
        font = QFont()
        font.setFamilies([u"General Sans"])
        font.setPointSize(62)
        font.setWeight(QFont.DemiBold)
        font.setItalic(False)
        self.logoLabel.setFont(font)
        self.logoLabel.setStyleSheet(u"color: #4BA690;\n"
"font-size: 62pt;\n"
"font-weight: 600;")
        self.logoLabel.setFrameShape(QFrame.Shape.NoFrame)
        self.logoLabel.setFrameShadow(QFrame.Shadow.Raised)
        self.logoLabel.setTextFormat(Qt.TextFormat.AutoText)

        self.labelLayout.addWidget(self.logoLabel, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.verticalLayout.addLayout(self.labelLayout)

        self.stackedWidget = QStackedWidget(authPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.registerPage = QWidget()
        self.registerPage.setObjectName(u"registerPage")
        self.gridLayout = QGridLayout(self.registerPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.registerFormLayout = QVBoxLayout()
        self.registerFormLayout.setSpacing(0)
        self.registerFormLayout.setObjectName(u"registerFormLayout")
        self.registerInputLayout = QVBoxLayout()
        self.registerInputLayout.setSpacing(20)
        self.registerInputLayout.setObjectName(u"registerInputLayout")
        self.registerInputLayout.setContentsMargins(-1, 0, -1, 50)
        self.registerUsername = QLineEdit(self.registerPage)
        self.registerUsername.setObjectName(u"registerUsername")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.registerUsername.sizePolicy().hasHeightForWidth())
        self.registerUsername.setSizePolicy(sizePolicy1)
        self.registerUsername.setMinimumSize(QSize(600, 45))
        self.registerUsername.setMaximumSize(QSize(800, 45))
        self.registerUsername.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerUsername.setAutoFillBackground(False)
        self.registerUsername.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.registerUsername.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.registerInputLayout.addWidget(self.registerUsername, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerEmail = QLineEdit(self.registerPage)
        self.registerEmail.setObjectName(u"registerEmail")
        self.registerEmail.setMinimumSize(QSize(600, 45))
        self.registerEmail.setMaximumSize(QSize(800, 45))
        self.registerEmail.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerEmail.setAutoFillBackground(False)
        self.registerEmail.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.registerEmail.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.registerInputLayout.addWidget(self.registerEmail, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerPassword = QLineEdit(self.registerPage)
        self.registerPassword.setObjectName(u"registerPassword")
        self.registerPassword.setMinimumSize(QSize(600, 45))
        self.registerPassword.setMaximumSize(QSize(800, 45))
        self.registerPassword.setMouseTracking(True)
        self.registerPassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerPassword.setAutoFillBackground(False)
        self.registerPassword.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.registerPassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.registerInputLayout.addWidget(self.registerPassword, 0, Qt.AlignmentFlag.AlignHCenter)

        self.registerRePassword = QLineEdit(self.registerPage)
        self.registerRePassword.setObjectName(u"registerRePassword")
        self.registerRePassword.setMinimumSize(QSize(600, 45))
        self.registerRePassword.setMaximumSize(QSize(800, 45))
        self.registerRePassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.registerRePassword.setAutoFillBackground(False)
        self.registerRePassword.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.registerRePassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.registerInputLayout.addWidget(self.registerRePassword, 0, Qt.AlignmentFlag.AlignHCenter)


        self.registerFormLayout.addLayout(self.registerInputLayout)

        self.registerSumbitLayout = QVBoxLayout()
        self.registerSumbitLayout.setSpacing(25)
        self.registerSumbitLayout.setObjectName(u"registerSumbitLayout")
        self.registerSumbitLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.registerSumbitLayout.setContentsMargins(-1, -1, 0, -1)
        self.registerStatus = QLabel(self.registerPage)
        self.registerStatus.setObjectName(u"registerStatus")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.registerStatus.sizePolicy().hasHeightForWidth())
        self.registerStatus.setSizePolicy(sizePolicy2)
        self.registerStatus.setMaximumSize(QSize(16777215, 40))
        self.registerStatus.setStyleSheet(u"font: 11pt;\n"
"font-weight: 400;")
        self.registerStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.registerSumbitLayout.addWidget(self.registerStatus)

        self.btnRegister = QPushButton(self.registerPage)
        self.btnRegister.setObjectName(u"btnRegister")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btnRegister.sizePolicy().hasHeightForWidth())
        self.btnRegister.setSizePolicy(sizePolicy3)
        self.btnRegister.setMinimumSize(QSize(400, 70))
        self.btnRegister.setMaximumSize(QSize(800, 80))
        font1 = QFont()
        font1.setFamilies([u"General Sans"])
        font1.setPointSize(11)
        font1.setBold(False)
        font1.setItalic(False)
        self.btnRegister.setFont(font1)
        self.btnRegister.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.btnRegister.setMouseTracking(True)
        self.btnRegister.setStyleSheet(u"QPushButton#btnRegister {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 35px;\n"
"    padding: 6px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"    font: 11pt;\n"
"	font-weight: 400;\n"
"}\n"
"\n"
"QPushButton#btnRegister:hover {\n"
"    border: 1px solid #93cabc;\n"
"    background-color: #181818;\n"
"}\n"
"\n"
"QPushButton#btnRegister:pressed {\n"
"    background-color: #0f0f0f;\n"
"    border: 1px solid #6fb8a6;\n"
"}\n"
"")
        self.btnRegister.setCheckable(False)

        self.registerSumbitLayout.addWidget(self.btnRegister, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnSwitchToLogin = QPushButton(self.registerPage)
        self.btnSwitchToLogin.setObjectName(u"btnSwitchToLogin")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btnSwitchToLogin.sizePolicy().hasHeightForWidth())
        self.btnSwitchToLogin.setSizePolicy(sizePolicy4)
        self.btnSwitchToLogin.setMaximumSize(QSize(16777215, 50))
        self.btnSwitchToLogin.setFont(font1)
        self.btnSwitchToLogin.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnSwitchToLogin.setStyleSheet(u"QPushButton#btnSwitchToLogin {\n"
"    border: none;\n"
"    color: #fafafa;\n"
"    font: 11pt;\n"
"    font-weight: 400;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QPushButton#btnSwitchToLogin:hover {\n"
"    color: #3e8e7a;\n"
"}")
        self.btnSwitchToLogin.setFlat(False)

        self.registerSumbitLayout.addWidget(self.btnSwitchToLogin, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.registerFormLayout.addLayout(self.registerSumbitLayout)


        self.gridLayout.addLayout(self.registerFormLayout, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.registerPage)
        self.loginPage = QWidget()
        self.loginPage.setObjectName(u"loginPage")
        self.verticalLayout_3 = QVBoxLayout(self.loginPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.loginFormLayout = QVBoxLayout()
        self.loginFormLayout.setObjectName(u"loginFormLayout")
        self.loginInputLayout = QVBoxLayout()
        self.loginInputLayout.setSpacing(20)
        self.loginInputLayout.setObjectName(u"loginInputLayout")
        self.loginInputLayout.setContentsMargins(-1, 50, -1, 50)
        self.loginUsername = QLineEdit(self.loginPage)
        self.loginUsername.setObjectName(u"loginUsername")
        self.loginUsername.setMinimumSize(QSize(600, 45))
        self.loginUsername.setMaximumSize(QSize(800, 45))
        self.loginUsername.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.loginUsername.setAutoFillBackground(False)
        self.loginUsername.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.loginUsername.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.loginInputLayout.addWidget(self.loginUsername, 0, Qt.AlignmentFlag.AlignHCenter)

        self.loginPassword = QLineEdit(self.loginPage)
        self.loginPassword.setObjectName(u"loginPassword")
        self.loginPassword.setMinimumSize(QSize(600, 45))
        self.loginPassword.setMaximumSize(QSize(800, 45))
        self.loginPassword.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.loginPassword.setAutoFillBackground(False)
        self.loginPassword.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 25px;\n"
"    padding: 10px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"	font: 10pt;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #93cabc;\n"
"	color: #3c8573;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #6fb8a6;\n"
"    background-color: #191919;\n"
"}\n"
"")
        self.loginPassword.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.loginInputLayout.addWidget(self.loginPassword, 0, Qt.AlignmentFlag.AlignHCenter)


        self.loginFormLayout.addLayout(self.loginInputLayout)

        self.loginLayout = QVBoxLayout()
        self.loginLayout.setSpacing(25)
        self.loginLayout.setObjectName(u"loginLayout")
        self.loginLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.loginLayout.setContentsMargins(-1, -1, 0, -1)
        self.loginStatus = QLabel(self.loginPage)
        self.loginStatus.setObjectName(u"loginStatus")
        sizePolicy2.setHeightForWidth(self.loginStatus.sizePolicy().hasHeightForWidth())
        self.loginStatus.setSizePolicy(sizePolicy2)
        self.loginStatus.setMaximumSize(QSize(16777215, 40))
        self.loginStatus.setStyleSheet(u"font: 11pt;\n"
"font-weight: 400;")
        self.loginStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loginLayout.addWidget(self.loginStatus)

        self.btnLogin = QPushButton(self.loginPage)
        self.btnLogin.setObjectName(u"btnLogin")
        sizePolicy3.setHeightForWidth(self.btnLogin.sizePolicy().hasHeightForWidth())
        self.btnLogin.setSizePolicy(sizePolicy3)
        self.btnLogin.setMinimumSize(QSize(400, 70))
        self.btnLogin.setMaximumSize(QSize(800, 80))
        self.btnLogin.setFont(font1)
        self.btnLogin.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.btnLogin.setMouseTracking(True)
        self.btnLogin.setStyleSheet(u"QPushButton#btnLogin {\n"
"    border: 1px solid #3c8573;\n"
"    border-radius: 16px;\n"
"    height: 35px;\n"
"    padding: 6px 12px;\n"
"    background-color: #151515;\n"
"    color: #fafafa;\n"
"    font: 11pt;\n"
"	font-weight: 400;\n"
"}\n"
"\n"
"QPushButton#btnLogin:hover {\n"
"    border: 1px solid #93cabc;\n"
"    background-color: #181818;\n"
"}\n"
"\n"
"QPushButton#btnLogin:pressed {\n"
"    background-color: #0f0f0f;\n"
"    border: 1px solid #6fb8a6;\n"
"}\n"
"")
        self.btnLogin.setCheckable(False)

        self.loginLayout.addWidget(self.btnLogin, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btnSwitchToRegister = QPushButton(self.loginPage)
        self.btnSwitchToRegister.setObjectName(u"btnSwitchToRegister")
        sizePolicy.setHeightForWidth(self.btnSwitchToRegister.sizePolicy().hasHeightForWidth())
        self.btnSwitchToRegister.setSizePolicy(sizePolicy)
        self.btnSwitchToRegister.setMaximumSize(QSize(16777215, 50))
        self.btnSwitchToRegister.setFont(font1)
        self.btnSwitchToRegister.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btnSwitchToRegister.setStyleSheet(u"QPushButton#btnSwitchToRegister {\n"
"    border: none;\n"
"    color: #fafafa;\n"
"    font: 11pt;\n"
"    font-weight: 400;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QPushButton#btnSwitchToRegister:hover {\n"
"    color: #3e8e7a;\n"
"}")
        self.btnSwitchToRegister.setFlat(False)

        self.loginLayout.addWidget(self.btnSwitchToRegister, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.loginFormLayout.addLayout(self.loginLayout)


        self.verticalLayout_3.addLayout(self.loginFormLayout)

        self.stackedWidget.addWidget(self.loginPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.retranslateUi(authPage)

        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(authPage)
    # setupUi

    def retranslateUi(self, authPage):
        authPage.setWindowTitle(QCoreApplication.translate("authPage", u"Form", None))
        self.logoLabel.setText(QCoreApplication.translate("authPage", u"Synapso", None))
        self.registerUsername.setText("")
        self.registerPassword.setText("")
        self.registerRePassword.setText("")
        self.registerStatus.setText("")
#if QT_CONFIG(accessibility)
        self.btnRegister.setAccessibleDescription("")
#endif // QT_CONFIG(accessibility)
        self.btnRegister.setText(QCoreApplication.translate("authPage", u"Registrova\u0165", None))
        self.btnSwitchToLogin.setText(QCoreApplication.translate("authPage", u"Chcem sa prihl\u00e1si\u0165.", None))
        self.loginPassword.setText("")
        self.loginStatus.setText("")
#if QT_CONFIG(accessibility)
        self.btnLogin.setAccessibleDescription("")
#endif // QT_CONFIG(accessibility)
        self.btnLogin.setText(QCoreApplication.translate("authPage", u"Prihl\u00e1si\u0165", None))
        self.btnSwitchToRegister.setText(QCoreApplication.translate("authPage", u"Chcem sa zaregistrova\u0165.", None))
    # retranslateUi

