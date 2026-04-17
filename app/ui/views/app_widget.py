"""Main application widget managing navigation, pages and user profile display."""

from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget
from app.models.user import User

from app.controller.profile_controller import ProfileController
from app.ui.components.navbar import NavbarWidget
from app.ui.components.sidebar import SidebarWidget
from app.ui.views.dashboard import DashboardView
from app.ui.views.profile import ProfileView
from app.ui.views.games import GamesView
from app.ui.views.statistics import StatisticsView
from app.ui.views.about import AboutView
from app.ui.views.settings import SettingsView
from app.utils.ui_helpers import draw_background
from app.utils.logger import get_logger
from app.utils.breadcrumbs import add_breadcrumb
from app.utils.crash_handler import set_active_view
from app.service.activity_service import flush_heartbeat

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

    def _build_ui(self):
        self._root_stack = QStackedWidget(self)
        self._root_stack.setAutoFillBackground(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._root_stack)

        self._main_widget = QWidget()
        self._main_widget.setAutoFillBackground(False)
        self._root_stack.addWidget(self._main_widget)

        self.rootLayout = QHBoxLayout(self._main_widget)
        self.rootLayout.setContentsMargins(50, 25, 50, 25)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.rootLayout.addLayout(self.mainLayout)

        self.navbarWidget = NavbarWidget(self._user.username, self._user.avatar_path)
        self.mainLayout.addWidget(self.navbarWidget)

        self.bodyLayout = QHBoxLayout()
        self.bodyLayout.setSpacing(20)
        self.bodyLayout.setContentsMargins(10, 0, 0, 0)
        self.mainLayout.addLayout(self.bodyLayout, 0)

        self.sidebarWidget = SidebarWidget(self)
        self.dashboardButton = self.sidebarWidget.dashboardButton
        self.gamesButton = self.sidebarWidget.gamesButton
        self.statisticsButton = self.sidebarWidget.statisticsButton
        self.settingsButton = self.sidebarWidget.settingsButton
        self.infoButton = self.sidebarWidget.infoButton
        self.logoutButton = self.sidebarWidget.logoutButton

        self.bodyLayout.addWidget(self.sidebarWidget)

        self.contentWidget = QStackedWidget(self._main_widget)
        self.contentWidget.setObjectName("contentWidget")
        self.bodyLayout.addWidget(self.contentWidget, 1)

        self._root_stack.addWidget(QWidget())

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
        self._page_factories = {
            "dashboard": lambda: DashboardView(user=self._user),
            "games": lambda: GamesView(user_id=self._user.id),
            "statistics": lambda: StatisticsView(user_id=self._user.id),
            "settings": lambda: SettingsView(),
            "info": lambda: AboutView(user_id=self._user.id),
        }
        self._page_instances: dict[str, QWidget] = {}

        self.profile_page = ProfileView(user=self._user)
        self.profile_controller = ProfileController(
            view=self.profile_page,
            user=self._user,
            navbar=self.navbarWidget,
            on_logout=self._emit_logout,
        )
        self.contentWidget.addWidget(self.profile_page)

        self.pages = {
            "dashboard": self.dashboardButton,
            "games": self.gamesButton,
            "statistics": self.statisticsButton,
            "settings": self.settingsButton,
            "info": self.infoButton,
        }

    def _get_or_create_page(self, name: str) -> QWidget:
        if name not in self._page_instances:
            page = self._page_factories[name]()
            self._page_instances[name] = page
            self.contentWidget.addWidget(page)
            if name == "games":
                page.launch_game_requested.connect(self._show_fullscreen_game)
                if "dashboard" in self._page_instances:
                    dashboard = self._page_instances["dashboard"]
                    try:
                        dashboard.continue_game_requested.connect(lambda slug, g=page: g._launch_play(slug))
                    except Exception:
                        logger.exception("Failed to connect dashboard continue signal to games launcher")
            elif name == "dashboard":
                if "games" in self._page_instances:
                    games = self._page_instances["games"]
                    try:
                        page.continue_game_requested.connect(lambda slug, g=games: g._launch_play(slug))
                    except Exception:
                        logger.exception("Failed to connect dashboard continue signal to games launcher")
        return self._page_instances[name]

    def _connect_signals(self):
        self.logoutButton.clicked.connect(self._on_logout_clicked)
        self.navbarWidget.profile_clicked.connect(self._go_to_profile)
        for name, btn in self.pages.items():
            btn.clicked.connect(lambda _, n=name: self.on_page_clicked(n))
        self.profile_page.avatar_upload_succeeded.connect(self._on_avatar_updated)

    def _on_avatar_updated(self, data: bytes) -> None:
        games = self._page_instances.get("games")
        if games:
            games.refresh_user_avatar(self._user.avatar_path, data)

    def on_page_clicked(self, page_name: str):
        logger.info("User navigated to %s", page_name)
        set_active_view(page_name)
        add_breadcrumb("nav", f"Navigated to {page_name}")
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
            self._get_or_create_page(page_name)
        )

    def _go_to_profile(self):
        logger.info("User opened profile")
        set_active_view("profile")
        add_breadcrumb("nav", "Opened profile")
        for name, button in self.pages.items():
            icon = QIcon(f":/images/icons/{name}-unselected.png")
            if icon.isNull():
                icon = QIcon(f":/images/icons/{name}.png")
            button.setIcon(icon)
            button.setProperty("selected", "false")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
        self.contentWidget.setCurrentWidget(self.profile_page)

    def _on_logout_clicked(self, checked: bool = False):
        logger.info("User initiated logout")
        add_breadcrumb("auth", "Logout initiated")
        self.logoutButton.setEnabled(False)
        self.logout_requested.emit()

    def _emit_logout(self):
        self.logout_requested.emit()

    def _show_fullscreen_game(self, widget):
        logger.info("Game session started: %s", widget.__class__.__name__)
        add_breadcrumb("game", "Game session started", widget=widget.__class__.__name__)
        set_active_view(f"game:{widget.__class__.__name__}")
        flush_heartbeat()
        widget.session_done.connect(self._hide_fullscreen_game)

        old = self._root_stack.widget(1)
        self._root_stack.insertWidget(1, widget)
        self._root_stack.setCurrentIndex(1)
        self._root_stack.removeWidget(old)
        old.deleteLater()
        widget.setFocus()

    def _hide_fullscreen_game(self):
        flush_heartbeat()
        self._root_stack.setCurrentIndex(0)
        old = self._root_stack.widget(1)
        self._root_stack.removeWidget(old)
        old.deleteLater()
        self._root_stack.insertWidget(1, QWidget())

    def paintEvent(self, event):
        draw_background(self, event)
