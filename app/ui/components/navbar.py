from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from app.ui.styles.fonts import FONT_NAVBAR
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from app.repository.user_repository import fetch_avatar
from app.utils.ui_helpers import image_to_rounded

from app.ui.styles.colors import *


class NavbarWidget(QWidget):
    def __init__(self, username: str, avatar_path: str | None = None, parent=None):
        super().__init__(parent)
        self._username = username
        self._avatar_path = avatar_path
        self.setObjectName("navbarWidget")

        self.navbarLayout = QHBoxLayout(self)
        self.navbarLayout.setSpacing(12)

        self.logoWidget = QWidget(self)
        self.logoLayout = QHBoxLayout(self.logoWidget)
        self.logoLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLabel = QLabel("Synapso", self.logoWidget)
        self.titleLabel.setObjectName("titleNavbarLabel")
        self.titleLabel.setFont(FONT_NAVBAR)
        self.logoLayout.addWidget(self.titleLabel)

        self.navbarLayout.addWidget(self.logoWidget)

        self.navbarLayout.addStretch(1)

        # profile pill
        self.profileWidget = QWidget(self)
        self.profileWidget.setObjectName("profileWidget")
        self.profileWidget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self.profileLayout = QHBoxLayout(self.profileWidget)
        self.profileLayout.setSpacing(10)
        self.profileLayout.setContentsMargins(12, 9, 18, 9)

        self.avatarIcon = QLabel(self.profileWidget)
        self.avatarIcon.setObjectName("avatarIcon")
        self.avatarIcon.setFixedSize(QSize(35, 35))
        self.avatarIcon.setScaledContents(True)
        self.avatarIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profileLayout.addWidget(self.avatarIcon)

        self.usernameLabel = QLabel(self._username, self.profileWidget)
        self.usernameLabel.setObjectName("usernameLabel")
        self.profileLayout.addWidget(self.usernameLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        if self._avatar_path:
            avatar_data = fetch_avatar(self._avatar_path)
            if avatar_data:
                self.set_avatar_bytes(avatar_data)

        self.navbarLayout.addWidget(self.profileWidget)

    def set_avatar_bytes(self, data: bytes) -> None:
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.avatarIcon.setPixmap(pixmap)
            self.avatarIcon.setScaledContents(True)
            image_to_rounded(self.avatarIcon)
