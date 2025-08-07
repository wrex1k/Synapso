from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, Qt, QIcon
from PySide6.QtCore import Signal
from app.ui.appWidget_ui import Ui_appWidget

class AppWidget(QWidget):
    logout_requested = Signal()

    def __init__(self, username: str):
        super().__init__()

        self.ui = Ui_appWidget()
        self.ui.setupUi(self)

        self.ui.usernameLabel.setText(username)
        self.ui.btnLogout.clicked.connect(self.logout_requested.emit)

        self.pages = {
            self.ui.btnDashboard: self.ui.dashboardPage,
            self.ui.btnGames: self.ui.gamesPage,
            self.ui.btnAchievements: self.ui.achievementsPage,
            self.ui.btnStatistics: self.ui.statisticsPage,
            self.ui.btnInfo: self.ui.infoPage,
            self.ui.btnSettings: self.ui.settingsPage,
        }

        for btn in self.pages:
            btn.clicked.connect(lambda _, b=btn: self.switch_page(self.pages[b], b))

        self._make_profile_picture_rounded()

    def _make_profile_picture_rounded(self):
        original_pixmap = self.ui.userAvatarLabel.pixmap()
        if not original_pixmap:
            return

        size = min(original_pixmap.width(), original_pixmap.height())
        rounded = QPixmap(size, size)
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, original_pixmap)
        painter.end()

        self.ui.userAvatarLabel.setPixmap(rounded)
        self.ui.userAvatarLabel.setScaledContents(True)

    def switch_page(self, target_widget, clicked_button):
        self.ui.contentStackedWidget.setCurrentWidget(target_widget)

        for btn, page in self.pages.items():
            base_name = page.objectName().replace("Page", "")
            is_active = btn == clicked_button

            if is_active:
                style += " background-color: #ffffff;"
                icon_path = f":/images/icons/{base_name}-selected.png"
            else:
                icon_path = f":/images/icons/{base_name}.png"

            btn.setStyleSheet("border-radius: 27px; padding: 15px;")
            btn.setIcon(QIcon(icon_path))

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(":/images/backgrounds/bg.png")
        painter.drawPixmap(self.rect(), pixmap)
        super().paintEvent(event)
