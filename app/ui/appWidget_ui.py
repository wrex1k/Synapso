# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'appWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)
import resources_rc

class Ui_appWidget(object):
    def setupUi(self, appWidget):
        if not appWidget.objectName():
            appWidget.setObjectName(u"appWidget")
        appWidget.resize(914, 864)
        appWidget.setStyleSheet(u"font-family: \"General Sans\";\n"
"font-weight: 500;")
        self.verticalLayout_5 = QVBoxLayout(appWidget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.navbar_sidebar_content = QVBoxLayout()
        self.navbar_sidebar_content.setObjectName(u"navbar_sidebar_content")
        self.navbar = QWidget(appWidget)
        self.navbar.setObjectName(u"navbar")
        self.horizontalLayout_2 = QHBoxLayout(self.navbar)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(20, 10, 10, 10)
        self.title_2 = QLabel(self.navbar)
        self.title_2.setObjectName(u"title_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_2.sizePolicy().hasHeightForWidth())
        self.title_2.setSizePolicy(sizePolicy)
        self.title_2.setStyleSheet(u"font: 27pt;\n"
"color: #3EAC91;\n"
"font-weight: 500;")

        self.horizontalLayout_2.addWidget(self.title_2)

        self.LPI = QFrame(self.navbar)
        self.LPI.setObjectName(u"LPI")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.LPI.sizePolicy().hasHeightForWidth())
        self.LPI.setSizePolicy(sizePolicy1)
        self.LPI.setStyleSheet(u"QFrame#LPI {\n"
"	background-color: #213D3B;\n"
"	border: none;\n"
"	border-radius: 21px;\n"
"}")
        self.LPI.setFrameShape(QFrame.Shape.StyledPanel)
        self.LPI.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.LPI)
        self.horizontalLayout_4.setSpacing(20)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(20, -1, 20, -1)
        self.lpi_title = QLabel(self.LPI)
        self.lpi_title.setObjectName(u"lpi_title")

        self.horizontalLayout_4.addWidget(self.lpi_title)

        self.number = QLabel(self.LPI)
        self.number.setObjectName(u"number")

        self.horizontalLayout_4.addWidget(self.number)


        self.horizontalLayout_2.addWidget(self.LPI)

        self.notifications = QWidget(self.navbar)
        self.notifications.setObjectName(u"notifications")
        sizePolicy1.setHeightForWidth(self.notifications.sizePolicy().hasHeightForWidth())
        self.notifications.setSizePolicy(sizePolicy1)
        self.notifications.setStyleSheet(u"QWidget#notifications {\n"
"	background-color: #213D3B;\n"
"	border-radius: 21px;\n"
"}")
        self.horizontalLayout = QHBoxLayout(self.notifications)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.notifications_image = QLabel(self.notifications)
        self.notifications_image.setObjectName(u"notifications_image")
        sizePolicy.setHeightForWidth(self.notifications_image.sizePolicy().hasHeightForWidth())
        self.notifications_image.setSizePolicy(sizePolicy)
        self.notifications_image.setMaximumSize(QSize(24, 24))
        self.notifications_image.setStyleSheet(u"")
        self.notifications_image.setPixmap(QPixmap(u":/images/icons/bell.png"))
        self.notifications_image.setScaledContents(True)

        self.horizontalLayout.addWidget(self.notifications_image)


        self.horizontalLayout_2.addWidget(self.notifications)

        self.profile_frame = QFrame(self.navbar)
        self.profile_frame.setObjectName(u"profile_frame")
        sizePolicy1.setHeightForWidth(self.profile_frame.sizePolicy().hasHeightForWidth())
        self.profile_frame.setSizePolicy(sizePolicy1)
        self.profile_frame.setStyleSheet(u"QFrame#profile_frame {\n"
"	background-color: #213D3B;\n"
"	border-radius: 21px;\n"
"}")
        self.profile_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.profile_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.profile_frame.setLineWidth(1)
        self.horizontalLayout_3 = QHBoxLayout(self.profile_frame)
        self.horizontalLayout_3.setSpacing(20)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(10, 0, 10, 2)
        self.image = QLabel(self.profile_frame)
        self.image.setObjectName(u"image")
        self.image.setMinimumSize(QSize(40, 40))
        self.image.setMaximumSize(QSize(40, 40))
        self.image.setStyleSheet(u"")
        self.image.setFrameShape(QFrame.Shape.NoFrame)
        self.image.setTextFormat(Qt.TextFormat.AutoText)
        self.image.setPixmap(QPixmap(u":/images/graphics/default.png"))
        self.image.setScaledContents(True)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setWordWrap(False)
        self.image.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.horizontalLayout_3.addWidget(self.image)

        self.username = QLabel(self.profile_frame)
        self.username.setObjectName(u"username")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy2)
        self.username.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.horizontalLayout_3.addWidget(self.username)

        self.arrowdown = QLabel(self.profile_frame)
        self.arrowdown.setObjectName(u"arrowdown")
        self.arrowdown.setMinimumSize(QSize(20, 20))
        self.arrowdown.setMaximumSize(QSize(20, 20))
        self.arrowdown.setPixmap(QPixmap(u":/images/icons/arrow-down.png"))
        self.arrowdown.setScaledContents(True)

        self.horizontalLayout_3.addWidget(self.arrowdown, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.horizontalLayout_2.addWidget(self.profile_frame)


        self.navbar_sidebar_content.addWidget(self.navbar)

        self.sidebar_content = QHBoxLayout()
        self.sidebar_content.setSpacing(20)
        self.sidebar_content.setObjectName(u"sidebar_content")
        self.sidebar_content.setContentsMargins(10, -1, -1, -1)
        self.sidebar = QWidget(appWidget)
        self.sidebar.setObjectName(u"sidebar")
        sizePolicy1.setHeightForWidth(self.sidebar.sizePolicy().hasHeightForWidth())
        self.sidebar.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.sidebar)
        self.verticalLayout_2.setSpacing(60)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 20, 0, 20)
        self.top_sidebar = QWidget(self.sidebar)
        self.top_sidebar.setObjectName(u"top_sidebar")
        self.top_sidebar.setAutoFillBackground(False)
        self.top_sidebar.setStyleSheet(u"background-color: #20302f; border-radius: 27px")
        self.verticalLayout_3 = QVBoxLayout(self.top_sidebar)
        self.verticalLayout_3.setSpacing(15)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 10, 0, 10)
        self.dashboard = QLabel(self.top_sidebar)
        self.dashboard.setObjectName(u"dashboard")
        sizePolicy.setHeightForWidth(self.dashboard.sizePolicy().hasHeightForWidth())
        self.dashboard.setSizePolicy(sizePolicy)
        self.dashboard.setStyleSheet(u"background-color: white; border-radius: 25px; padding: 15px")
        self.dashboard.setPixmap(QPixmap(u":/images/icons/dashboard-selected.png"))
        self.dashboard.setScaledContents(False)

        self.verticalLayout_3.addWidget(self.dashboard)

        self.games = QLabel(self.top_sidebar)
        self.games.setObjectName(u"games")
        self.games.setStyleSheet(u"padding: 15px")
        self.games.setPixmap(QPixmap(u":/images/icons/controller.png"))

        self.verticalLayout_3.addWidget(self.games, 0, Qt.AlignmentFlag.AlignHCenter)

        self.profile = QLabel(self.top_sidebar)
        self.profile.setObjectName(u"profile")
        self.profile.setStyleSheet(u"padding: 15px;")
        self.profile.setPixmap(QPixmap(u":/images/icons/trophy.png"))

        self.verticalLayout_3.addWidget(self.profile, 0, Qt.AlignmentFlag.AlignHCenter)

        self.statistics = QLabel(self.top_sidebar)
        self.statistics.setObjectName(u"statistics")
        self.statistics.setStyleSheet(u"padding: 15px;")
        self.statistics.setPixmap(QPixmap(u":/images/icons/analytics.png"))

        self.verticalLayout_3.addWidget(self.statistics, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_2.addWidget(self.top_sidebar)

        self.bottom_sidebar = QWidget(self.sidebar)
        self.bottom_sidebar.setObjectName(u"bottom_sidebar")
        self.bottom_sidebar.setStyleSheet(u"background-color: #20302f; border-radius: 27px")
        self.verticalLayout_4 = QVBoxLayout(self.bottom_sidebar)
        self.verticalLayout_4.setSpacing(15)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 10, 0, 10)
        self.settings = QLabel(self.bottom_sidebar)
        self.settings.setObjectName(u"settings")
        self.settings.setStyleSheet(u"border-radius: 10px;")
        self.settings.setPixmap(QPixmap(u":/images/icons/settings.png"))

        self.verticalLayout_4.addWidget(self.settings, 0, Qt.AlignmentFlag.AlignHCenter)

        self.info = QLabel(self.bottom_sidebar)
        self.info.setObjectName(u"info")
        self.info.setStyleSheet(u"padding: 15px; border-radius: 10px;")
        self.info.setPixmap(QPixmap(u":/images/icons/info.png"))

        self.verticalLayout_4.addWidget(self.info, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_2.addWidget(self.bottom_sidebar)

        self.logout = QLabel(self.sidebar)
        self.logout.setObjectName(u"logout")
        self.logout.setStyleSheet(u"background-color: #20302f; border-radius: 27px; padding: 15px;")
        self.logout.setPixmap(QPixmap(u":/images/icons/logout.png"))

        self.verticalLayout_2.addWidget(self.logout, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 1)
        self.bottom_sidebar.raise_()
        self.top_sidebar.raise_()
        self.logout.raise_()

        self.sidebar_content.addWidget(self.sidebar, 0, Qt.AlignmentFlag.AlignTop)

        self.stackedWidget = QStackedWidget(appWidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.stackedWidget.addWidget(self.page_2)

        self.sidebar_content.addWidget(self.stackedWidget)

        self.sidebar_content.setStretch(0, 1)

        self.navbar_sidebar_content.addLayout(self.sidebar_content)

        self.navbar_sidebar_content.setStretch(1, 1)

        self.verticalLayout_5.addLayout(self.navbar_sidebar_content)


        self.retranslateUi(appWidget)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(appWidget)
    # setupUi

    def retranslateUi(self, appWidget):
        appWidget.setWindowTitle(QCoreApplication.translate("appWidget", u"MainWindow", None))
        self.title_2.setText(QCoreApplication.translate("appWidget", u"Synapso", None))
        self.lpi_title.setText(QCoreApplication.translate("appWidget", u"LPI", None))
        self.number.setText(QCoreApplication.translate("appWidget", u"1458", None))
        self.notifications_image.setText("")
        self.image.setText("")
        self.username.setText(QCoreApplication.translate("appWidget", u"wrexik", None))
        self.arrowdown.setText("")
        self.dashboard.setText("")
        self.games.setText("")
        self.profile.setText("")
        self.statistics.setText("")
        self.settings.setText("")
        self.info.setText("")
        self.logout.setText("")
    # retranslateUi

