from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.styles.colors import *
from app.utils.scaling import get_dpi_scale


_BASE_ICON = 24


class SidebarWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("sidebarWidget")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(30)
        self.mainLayout.setContentsMargins(0, 30, 0, 20)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.primarySidebarWidget = QWidget(self)
        self.primarySidebarWidget.setObjectName("primarySidebarWidget")
        self.primaryLayout = QVBoxLayout(self.primarySidebarWidget)
        self.primaryLayout.setSpacing(30)
        self.primaryLayout.setContentsMargins(0, 10, 0, 10)

        self.dashboardButton = self._nav_button(self.primarySidebarWidget, "dashboard")
        self.gamesButton = self._nav_button(self.primarySidebarWidget, "games")
        self.statisticsButton = self._nav_button(self.primarySidebarWidget, "statistics")

        self.primaryLayout.addWidget(self.dashboardButton)
        self.primaryLayout.addWidget(self.gamesButton)
        self.primaryLayout.addWidget(self.statisticsButton)

        self.secondarySidebarWidget = QWidget(self)
        self.secondarySidebarWidget.setObjectName("secondarySidebarWidget")
        self.secondaryLayout = QVBoxLayout(self.secondarySidebarWidget)
        self.secondaryLayout.setSpacing(15)
        self.secondaryLayout.setContentsMargins(0, 10, 0, 10)

        self.settingsButton = self._nav_button(self.secondarySidebarWidget, "settings")
        self.infoButton = self._nav_button(self.secondarySidebarWidget, "info")

        self.secondaryLayout.addWidget(self.settingsButton)
        self.secondaryLayout.addWidget(self.infoButton)

        self.logoutButton = QPushButton(self)
        self.logoutButton.setObjectName("logoutButton")
        self.logoutButton.setText("")
        self.logoutButton.setIcon(QIcon(":/images/icons/logout.png"))
        self.logoutButton.setIconSize(QSize(24, 24))

        self.mainLayout.addWidget(self.primarySidebarWidget)
        self.mainLayout.addWidget(self.secondarySidebarWidget)
        self.mainLayout.addWidget(self.logoutButton)

        self._all_buttons = [
            self.dashboardButton, self.gamesButton, self.statisticsButton,
            self.settingsButton, self.infoButton, self.logoutButton,
        ]

    def update_icon_sizes(self) -> None:
        s = max(20, int(_BASE_ICON * get_dpi_scale()))
        size = QSize(s, s)
        for btn in self._all_buttons:
            btn.setIconSize(size)

    def _nav_button(self, parent: QWidget, name: str) -> QPushButton:
        b = QPushButton(parent)
        b.setObjectName(f"{name}Button")
        b.setText("")
        b.setProperty("selected", "false")

        icon = QIcon(f":/images/icons/{name}-unselected.png")
        if icon.isNull():
            icon = QIcon(f":/images/icons/{name}.png")

        b.setIcon(icon)
        b.setIconSize(QSize(24, 24))
        return b
