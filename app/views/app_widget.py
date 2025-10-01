from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from app.ui.app_widget_ui import Ui_appWidget
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, Qt
from app.utils import draw_background, image_to_rounded

class AppWidget(QWidget):
    logout_requested = Signal()

    def __init__(self, user_row: dict = None):
        super().__init__()

        self.ui = Ui_appWidget()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        self.ui.logoutButton.clicked.connect(self._on_logout_clicked)
        
        if user_row:
            self._populate_user_data(user_row)

    def _populate_user_data(self, user_row: dict):
        self.ui.usernameLabel.setText(user_row.get("username", ""))
        avatar_path = user_row.get("avatar_path")
        print(f" _populate_user_data received avatar_path={avatar_path}")
        if avatar_path:
            self._load_avatar(avatar_path)

    def _load_avatar(self, avatar_path: str):
        from app.auth import supabase_auth
        if not avatar_path:
            return
        try:
            storage = supabase_auth.supabase.storage.from_("avatars")
            data = storage.download(avatar_path)
            self._set_avatar_from_bytes(data)
        except Exception as e:
            print(f"[WARN] Failed to fetch avatar from path {avatar_path}: {e}")

    def _set_avatar_from_bytes(self, data: bytes):
        if not data:
            print("[WARN] Empty avatar data")
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            print("[WARN] QPixmap failed to load from data")
            return
        self.ui.avatarIcon.setPixmap(pixmap)
        self.ui.avatarIcon.setScaledContents(True)
        self._make_avatar_rounded()

    def _make_avatar_rounded(self):
        image_to_rounded(self)

    def _on_logout_clicked(self, checked: bool=False):
        if hasattr(self.ui, 'logoutButton'):
            self.ui.logoutButton.setEnabled(False)
        self.logout_requested.emit()

    def paintEvent(self, event):
        draw_background(self, event)
        super().paintEvent(event)
