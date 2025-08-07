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
    QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout,
    QWidget)
import resources_rc

class Ui_appWidget(object):
    def setupUi(self, appWidget):
        if not appWidget.objectName():
            appWidget.setObjectName(u"appWidget")
        appWidget.resize(914, 864)
        appWidget.setStyleSheet(u"font-family: \"General Sans\";\n"
"font-weight: 500;")
        self.mainVerticalLayout = QVBoxLayout(appWidget)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.navigationAndContentLayout = QVBoxLayout()
        self.navigationAndContentLayout.setObjectName(u"navigationAndContentLayout")
        self.topNavigationBar = QWidget(appWidget)
        self.topNavigationBar.setObjectName(u"topNavigationBar")
        self.topNavigationBar.setStyleSheet(u"QWidget #cieStatusWidget,\n"
"QWidget #notificationWidget,\n"
"QWidget #userProfileWidget {\n"
"	background-color: #213D3B;\n"
"	border: none;\n"
"	border-radius: 21px;\n"
"}")
        self.navigationBarLayout = QHBoxLayout(self.topNavigationBar)
        self.navigationBarLayout.setObjectName(u"navigationBarLayout")
        self.navigationBarLayout.setContentsMargins(20, 10, 10, 10)
        self.applicationTitleLabel = QLabel(self.topNavigationBar)
        self.applicationTitleLabel.setObjectName(u"applicationTitleLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.applicationTitleLabel.sizePolicy().hasHeightForWidth())
        self.applicationTitleLabel.setSizePolicy(sizePolicy)
        self.applicationTitleLabel.setStyleSheet(u"font: 27pt;\n"
"color: #3EAC91;\n"
"font-weight: 500;")

        self.navigationBarLayout.addWidget(self.applicationTitleLabel)

        self.cieStatusWidget = QWidget(self.topNavigationBar)
        self.cieStatusWidget.setObjectName(u"cieStatusWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cieStatusWidget.sizePolicy().hasHeightForWidth())
        self.cieStatusWidget.setSizePolicy(sizePolicy1)
        self.cieStatusWidget.setStyleSheet(u"")
        self.cieStatusLayout = QHBoxLayout(self.cieStatusWidget)
        self.cieStatusLayout.setSpacing(20)
        self.cieStatusLayout.setObjectName(u"cieStatusLayout")
        self.cieStatusLayout.setContentsMargins(20, -1, 20, -1)
        self.cieLabel = QLabel(self.cieStatusWidget)
        self.cieLabel.setObjectName(u"cieLabel")

        self.cieStatusLayout.addWidget(self.cieLabel)

        self.cieValueLabel = QLabel(self.cieStatusWidget)
        self.cieValueLabel.setObjectName(u"cieValueLabel")

        self.cieStatusLayout.addWidget(self.cieValueLabel)


        self.navigationBarLayout.addWidget(self.cieStatusWidget)

        self.notificationWidget = QWidget(self.topNavigationBar)
        self.notificationWidget.setObjectName(u"notificationWidget")
        sizePolicy1.setHeightForWidth(self.notificationWidget.sizePolicy().hasHeightForWidth())
        self.notificationWidget.setSizePolicy(sizePolicy1)
        self.notificationWidget.setStyleSheet(u"QWidget#notificationWidget {\n"
"	background-color: #213D3B;\n"
"	border-radius: 21px;\n"
"}")
        self.notificationLayout = QHBoxLayout(self.notificationWidget)
        self.notificationLayout.setObjectName(u"notificationLayout")
        self.notificationIconLabel = QLabel(self.notificationWidget)
        self.notificationIconLabel.setObjectName(u"notificationIconLabel")
        sizePolicy.setHeightForWidth(self.notificationIconLabel.sizePolicy().hasHeightForWidth())
        self.notificationIconLabel.setSizePolicy(sizePolicy)
        self.notificationIconLabel.setMaximumSize(QSize(24, 24))
        self.notificationIconLabel.setStyleSheet(u"")
        self.notificationIconLabel.setPixmap(QPixmap(u":/images/icons/bell.png"))
        self.notificationIconLabel.setScaledContents(True)

        self.notificationLayout.addWidget(self.notificationIconLabel)


        self.navigationBarLayout.addWidget(self.notificationWidget)

        self.userProfileWidget = QWidget(self.topNavigationBar)
        self.userProfileWidget.setObjectName(u"userProfileWidget")
        sizePolicy1.setHeightForWidth(self.userProfileWidget.sizePolicy().hasHeightForWidth())
        self.userProfileWidget.setSizePolicy(sizePolicy1)
        self.userProfileWidget.setStyleSheet(u"")
        self.userProfileLayout = QHBoxLayout(self.userProfileWidget)
        self.userProfileLayout.setSpacing(20)
        self.userProfileLayout.setObjectName(u"userProfileLayout")
        self.userProfileLayout.setContentsMargins(10, 0, 10, 2)
        self.userAvatarLabel = QLabel(self.userProfileWidget)
        self.userAvatarLabel.setObjectName(u"userAvatarLabel")
        self.userAvatarLabel.setMinimumSize(QSize(40, 40))
        self.userAvatarLabel.setMaximumSize(QSize(40, 40))
        self.userAvatarLabel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.userAvatarLabel.setStyleSheet(u"")
        self.userAvatarLabel.setFrameShape(QFrame.Shape.NoFrame)
        self.userAvatarLabel.setTextFormat(Qt.TextFormat.AutoText)
        self.userAvatarLabel.setPixmap(QPixmap(u":/images/graphics/default.png"))
        self.userAvatarLabel.setScaledContents(True)
        self.userAvatarLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.userAvatarLabel.setWordWrap(False)
        self.userAvatarLabel.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.userProfileLayout.addWidget(self.userAvatarLabel, 0, Qt.AlignmentFlag.AlignBottom)

        self.usernameLabel = QLabel(self.userProfileWidget)
        self.usernameLabel.setObjectName(u"usernameLabel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.usernameLabel.sizePolicy().hasHeightForWidth())
        self.usernameLabel.setSizePolicy(sizePolicy2)
        self.usernameLabel.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        self.userProfileLayout.addWidget(self.usernameLabel)

        self.dropdownArrowLabel = QLabel(self.userProfileWidget)
        self.dropdownArrowLabel.setObjectName(u"dropdownArrowLabel")
        self.dropdownArrowLabel.setMinimumSize(QSize(20, 20))
        self.dropdownArrowLabel.setMaximumSize(QSize(20, 20))
        self.dropdownArrowLabel.setPixmap(QPixmap(u":/images/icons/arrow-down.png"))
        self.dropdownArrowLabel.setScaledContents(True)

        self.userProfileLayout.addWidget(self.dropdownArrowLabel, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.navigationBarLayout.addWidget(self.userProfileWidget)


        self.navigationAndContentLayout.addWidget(self.topNavigationBar)

        self.sidebarAndContentLayout = QHBoxLayout()
        self.sidebarAndContentLayout.setSpacing(20)
        self.sidebarAndContentLayout.setObjectName(u"sidebarAndContentLayout")
        self.sidebarAndContentLayout.setContentsMargins(10, -1, -1, -1)
        self.navigationSidebar = QWidget(appWidget)
        self.navigationSidebar.setObjectName(u"navigationSidebar")
        sizePolicy1.setHeightForWidth(self.navigationSidebar.sizePolicy().hasHeightForWidth())
        self.navigationSidebar.setSizePolicy(sizePolicy1)
        self.navigationSidebar.setStyleSheet(u"QPushButton {\n"
"    border-radius: 27px;\n"
"    padding: 15px;\n"
"    outline: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1e3735;\n"
"}\n"
"\n"
"QWidget#primaryNavigationContainer,\n"
"QWidget#secondaryNavigationContainer,\n"
"QPushButton#btnLogout {\n"
"    background-color: #213D3B;\n"
"    border-radius: 27px;\n"
"}\n"
"\n"
"QPushButton#btnLogout:hover {\n"
"    background-color: #1e1e1e;\n"
"}")
        self.sidebarLayout = QVBoxLayout(self.navigationSidebar)
        self.sidebarLayout.setSpacing(60)
        self.sidebarLayout.setObjectName(u"sidebarLayout")
        self.sidebarLayout.setContentsMargins(0, 20, 0, 20)
        self.primaryNavigationContainer = QWidget(self.navigationSidebar)
        self.primaryNavigationContainer.setObjectName(u"primaryNavigationContainer")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.primaryNavigationContainer.sizePolicy().hasHeightForWidth())
        self.primaryNavigationContainer.setSizePolicy(sizePolicy3)
        self.primaryNavigationContainer.setAutoFillBackground(False)
        self.primaryNavigationLayout = QVBoxLayout(self.primaryNavigationContainer)
        self.primaryNavigationLayout.setSpacing(15)
        self.primaryNavigationLayout.setObjectName(u"primaryNavigationLayout")
        self.primaryNavigationLayout.setContentsMargins(0, 10, 0, 10)
        self.btnDashboard = QPushButton(self.primaryNavigationContainer)
        self.btnDashboard.setObjectName(u"btnDashboard")
        self.btnDashboard.setStyleSheet(u"")
        icon = QIcon()
        icon.addFile(u":/images/icons/dashboard.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnDashboard.setIcon(icon)
        self.btnDashboard.setIconSize(QSize(24, 24))

        self.primaryNavigationLayout.addWidget(self.btnDashboard)

        self.btnGames = QPushButton(self.primaryNavigationContainer)
        self.btnGames.setObjectName(u"btnGames")
        self.btnGames.setStyleSheet(u"")
        icon1 = QIcon()
        icon1.addFile(u":/images/icons/games.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnGames.setIcon(icon1)
        self.btnGames.setIconSize(QSize(24, 24))

        self.primaryNavigationLayout.addWidget(self.btnGames)

        self.btnAchievements = QPushButton(self.primaryNavigationContainer)
        self.btnAchievements.setObjectName(u"btnAchievements")
        self.btnAchievements.setStyleSheet(u"")
        icon2 = QIcon()
        icon2.addFile(u":/images/icons/achievements.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnAchievements.setIcon(icon2)
        self.btnAchievements.setIconSize(QSize(24, 24))

        self.primaryNavigationLayout.addWidget(self.btnAchievements)

        self.btnStatistics = QPushButton(self.primaryNavigationContainer)
        self.btnStatistics.setObjectName(u"btnStatistics")
        self.btnStatistics.setStyleSheet(u"")
        icon3 = QIcon()
        icon3.addFile(u":/images/icons/statistics.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnStatistics.setIcon(icon3)
        self.btnStatistics.setIconSize(QSize(24, 24))

        self.primaryNavigationLayout.addWidget(self.btnStatistics)


        self.sidebarLayout.addWidget(self.primaryNavigationContainer)

        self.secondaryNavigationContainer = QWidget(self.navigationSidebar)
        self.secondaryNavigationContainer.setObjectName(u"secondaryNavigationContainer")
        sizePolicy3.setHeightForWidth(self.secondaryNavigationContainer.sizePolicy().hasHeightForWidth())
        self.secondaryNavigationContainer.setSizePolicy(sizePolicy3)
        self.secondaryNavigationContainer.setStyleSheet(u"")
        self.secondaryNavigationLayout = QVBoxLayout(self.secondaryNavigationContainer)
        self.secondaryNavigationLayout.setSpacing(15)
        self.secondaryNavigationLayout.setObjectName(u"secondaryNavigationLayout")
        self.secondaryNavigationLayout.setContentsMargins(0, 10, 0, 10)
        self.btnInfo = QPushButton(self.secondaryNavigationContainer)
        self.btnInfo.setObjectName(u"btnInfo")
        self.btnInfo.setStyleSheet(u"border-radius: 27px; padding: 15px")
        icon4 = QIcon()
        icon4.addFile(u":/images/icons/info.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnInfo.setIcon(icon4)
        self.btnInfo.setIconSize(QSize(24, 24))

        self.secondaryNavigationLayout.addWidget(self.btnInfo)

        self.btnSettings = QPushButton(self.secondaryNavigationContainer)
        self.btnSettings.setObjectName(u"btnSettings")
        self.btnSettings.setStyleSheet(u"border-radius: 27px; \n"
"padding: 15px;\n"
"outline: none;")
        icon5 = QIcon()
        icon5.addFile(u":/images/icons/settings.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnSettings.setIcon(icon5)
        self.btnSettings.setIconSize(QSize(24, 24))

        self.secondaryNavigationLayout.addWidget(self.btnSettings)


        self.sidebarLayout.addWidget(self.secondaryNavigationContainer)

        self.btnLogout = QPushButton(self.navigationSidebar)
        self.btnLogout.setObjectName(u"btnLogout")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btnLogout.sizePolicy().hasHeightForWidth())
        self.btnLogout.setSizePolicy(sizePolicy4)
        icon6 = QIcon()
        icon6.addFile(u":/images/icons/logout.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnLogout.setIcon(icon6)
        self.btnLogout.setIconSize(QSize(24, 24))

        self.sidebarLayout.addWidget(self.btnLogout)

        self.sidebarLayout.setStretch(0, 1)
        self.sidebarLayout.setStretch(1, 1)
        self.secondaryNavigationContainer.raise_()
        self.primaryNavigationContainer.raise_()
        self.btnLogout.raise_()

        self.sidebarAndContentLayout.addWidget(self.navigationSidebar)

        self.contentStackedWidget = QStackedWidget(appWidget)
        self.contentStackedWidget.setObjectName(u"contentStackedWidget")
        self.dashboardPage = QWidget()
        self.dashboardPage.setObjectName(u"dashboardPage")
        self.contentStackedWidget.addWidget(self.dashboardPage)
        self.achievementsPage = QWidget()
        self.achievementsPage.setObjectName(u"achievementsPage")
        self.contentStackedWidget.addWidget(self.achievementsPage)
        self.statisticsPage = QWidget()
        self.statisticsPage.setObjectName(u"statisticsPage")
        self.contentStackedWidget.addWidget(self.statisticsPage)
        self.infoPage = QWidget()
        self.infoPage.setObjectName(u"infoPage")
        self.contentStackedWidget.addWidget(self.infoPage)
        self.settingsPage = QWidget()
        self.settingsPage.setObjectName(u"settingsPage")
        self.contentStackedWidget.addWidget(self.settingsPage)
        self.profilePage = QWidget()
        self.profilePage.setObjectName(u"profilePage")
        self.contentStackedWidget.addWidget(self.profilePage)
        self.gamesPage = QWidget()
        self.gamesPage.setObjectName(u"gamesPage")
        self.contentStackedWidget.addWidget(self.gamesPage)

        self.sidebarAndContentLayout.addWidget(self.contentStackedWidget)


        self.navigationAndContentLayout.addLayout(self.sidebarAndContentLayout)

        self.navigationAndContentLayout.setStretch(1, 1)

        self.mainVerticalLayout.addLayout(self.navigationAndContentLayout)


        self.retranslateUi(appWidget)

        self.contentStackedWidget.setCurrentIndex(4)


        QMetaObject.connectSlotsByName(appWidget)
    # setupUi

    def retranslateUi(self, appWidget):
        appWidget.setWindowTitle(QCoreApplication.translate("appWidget", u"Synapso - Main Window", None))
        self.applicationTitleLabel.setText(QCoreApplication.translate("appWidget", u"Synapso", None))
        self.cieLabel.setText(QCoreApplication.translate("appWidget", u"CIE", None))
        self.cieValueLabel.setText(QCoreApplication.translate("appWidget", u"1458", None))
        self.notificationIconLabel.setText("")
        self.userAvatarLabel.setText("")
        self.usernameLabel.setText(QCoreApplication.translate("appWidget", u"wrexik", None))
        self.dropdownArrowLabel.setText("")
        self.btnDashboard.setText("")
        self.btnGames.setText("")
        self.btnAchievements.setText("")
        self.btnStatistics.setText("")
        self.btnInfo.setText("")
        self.btnSettings.setText("")
        self.btnLogout.setText("")
    # retranslateUi

