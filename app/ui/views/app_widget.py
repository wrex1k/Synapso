from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget
from supabase_auth import User

from app.ui.components.navbar import NavbarWidget
from app.ui.components.sidebar import SidebarWidget
from app.utils.ui_helpers import draw_background
from app.utils.logger import get_logger

"""
Main application widget managing navigation, pages and user profile display.
"""

logger = get_logger(__name__)

class AppWidget(QWidget):
    logout_requested = Signal()

    def __init__(self, user: User, parent=None):
        super().__init__(parent)

        self._user = user

        self.setObjectName("appWidget")
        self.setWindowTitle("Synapso")

        self._build_ui()
        self._init_pages()
        self._connect_signals()

        self.on_page_clicked("dashboard")

        logger.debug("Initializing AppWidget (user_id: ..%s)", self._user.id[-10:])

    def _build_ui(self):
        self.rootLayout = QHBoxLayout(self)
        self.rootLayout.setContentsMargins(20, 20, 20, 20)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.rootLayout.addLayout(self.mainLayout)

        self.navbarWidget = NavbarWidget(self._user.username, self._user.avatar_path)
        self.mainLayout.addWidget(self.navbarWidget)

        self.bodyLayout = QHBoxLayout()
        self.bodyLayout.setSpacing(20)
        self.bodyLayout.setContentsMargins(10, 0, 0, 0)
        self.mainLayout.addLayout(self.bodyLayout, 1)

        self.sidebarWidget = SidebarWidget(self)
        self.dashboardButton = self.sidebarWidget.dashboardButton
        self.gamesButton = self.sidebarWidget.gamesButton
        self.leaderboardButton = self.sidebarWidget.leaderboardButton
        self.settingsButton = self.sidebarWidget.settingsButton
        self.infoButton = self.sidebarWidget.infoButton
        self.logoutButton = self.sidebarWidget.logoutButton

        self.bodyLayout.addWidget(self.sidebarWidget)

        self.contentWidget = QStackedWidget(self)
        self.contentWidget.setObjectName("contentWidget")
        self.bodyLayout.addWidget(self.contentWidget, 1)

    def _nav_button(self, parent: QWidget, name: str) -> QPushButton:
        b = QPushButton(parent)
        b.setObjectName(f"{name}Button")
        b.setText("")
        b.setProperty("selected", False)
        icon = QIcon(f":/images/icons/{name}-unselected.png")
        if icon.isNull():
            icon = QIcon(f":/images/icons/{name}.png")
        b.setIcon(icon)
        b.setIconSize(QSize(24, 24))
        return b

    def _init_pages(self):
        self.dashboard_page = QWidget()
        self.games_page = QWidget()
        self.leaderboard_page = QWidget()
        
        self.settings_page = QWidget()
        self.info_page = QWidget()

        for page in (
            self.dashboard_page,
            self.games_page,
            self.leaderboard_page,
            self.settings_page,
            self.info_page,
        ):
            self.contentWidget.addWidget(page)

        self.pages = {
            "dashboard": self.dashboardButton,
            "games": self.gamesButton,
            "leaderboard": self.leaderboardButton,
            "settings": self.settingsButton,
            "info": self.infoButton,
        }
        self.page_map = {
            "dashboard": self.dashboard_page,
            "games": self.games_page,
            "leaderboard": self.leaderboard_page,
            "settings": self.settings_page,
            "info": self.info_page,
        }

    def _connect_signals(self):
        self.logoutButton.clicked.connect(self._on_logout_clicked)
        for name, btn in self.pages.items():
            btn.clicked.connect(lambda _, n=name: self.on_page_clicked(n))

    def on_page_clicked(self, page_name: str):
        for name, button in self.pages.items():
            selected = (name == page_name)
            suffix = "selected" if selected else "unselected"
            icon = QIcon(f":/images/icons/{name}-{suffix}.png")
            if icon.isNull() and not selected:
                icon = QIcon(f":/images/icons/{name}.png")
            button.setIcon(icon)
            button.setProperty("selected", "true" if selected else "false")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

        self.contentWidget.setCurrentWidget(
            self.page_map.get(page_name, self.dashboard_page)
        )

    def _on_logout_clicked(self, checked: bool = False):
        self.logoutButton.setEnabled(False)
        self.logout_requested.emit()

    def paintEvent(self, event):
        draw_background(self, event)
