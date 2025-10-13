from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from app.ui.app_widget_ui import Ui_appWidget
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, Qt
from app.utils import draw_background, image_to_rounded
from app.store.supabase_store import fetch_avatar

class AppWidget(QWidget):
    logout_requested = Signal()

    def __init__(self, user_data: dict = None):
        super().__init__()

        self.ui = Ui_appWidget()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        self.ui.logoutButton.clicked.connect(self._on_logout_clicked)
        
        if user_data:
            self.ui.usernameLabel.setText(user_data.get("username", ""))
            avatar = fetch_avatar(user_data.get("avatar_path"))
            if avatar:
                self._set_avatar_from_bytes(avatar)

    def _set_avatar_from_bytes(self, data: bytes):
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            print("[WARN] QPixmap failed to load from data")
            return
        self.ui.avatarIcon.setPixmap(pixmap)
        self.ui.avatarIcon.setScaledContents(True)
        image_to_rounded(self.ui.avatarIcon)

    def _on_logout_clicked(self, checked: bool=False):
        if hasattr(self.ui, 'logoutButton'):
            self.ui.logoutButton.setEnabled(False)
        self.logout_requested.emit()

    def paintEvent(self, event):
        draw_background(self, event)
