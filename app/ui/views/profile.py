from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.user import User
from app.repository.activity_repository import get_time_played
from app.repository.user_repository import fetch_avatar
from app.utils.ui_helpers import image_to_rounded
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProfileView(QWidget):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setObjectName("profileView")
        self._user = user
        self._time_played_seconds: int = 0
        try:
            self._time_played_seconds = get_time_played(self._user.id) or 0
        except Exception:
            logger.warning("Could not fetch time_played for user_id: ..%s", self._user.id[-10:])
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 80)
        layout.setSpacing(40)

        title_widget = QWidget()
        title_widget.setObjectName("titleWidget")
        title_col = QVBoxLayout(title_widget)
        title_col.setSpacing(4)
        title_col.setContentsMargins(0, 0, 0, 0)

        page_title = QLabel("Profile")
        page_title.setObjectName("gameTitle")
        page_subtitle = QLabel("Your personal information and activity overview")
        page_subtitle.setObjectName("gameDescription")

        title_col.addWidget(page_title)
        title_col.addWidget(page_subtitle)
        layout.addWidget(title_widget)

        # header card – avatar + name
        layout.addWidget(self._build_header_card())

        # personal info card
        layout.addWidget(self._build_info_card())
        layout.addStretch()

    def _build_header_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("profileHeaderCard")
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setAutoFillBackground(True)

        h = QHBoxLayout(card)
        h.setContentsMargins(24, 24, 24, 24)
        h.setSpacing(20)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # avatar
        self.avatarLabel = QLabel(card)
        self.avatarLabel.setObjectName("profileAvatar")
        self.avatarLabel.setFixedSize(QSize(72, 72))
        self.avatarLabel.setScaledContents(True)
        self.avatarLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_avatar()
        h.addWidget(self.avatarLabel)

        # text colun
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        username_lbl = QLabel(self._user.username or "—")
        username_lbl.setObjectName("profileUsernameLabel")
        text_col.addWidget(username_lbl)

        handle_lbl = QLabel(f"@{self._user.username.lower()}" if self._user.username else "")
        handle_lbl.setObjectName("profileHandleLabel")
        text_col.addWidget(handle_lbl)

        try:
            created_at = self._user.created_at
            if isinstance(created_at, str):
                from datetime import datetime
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            joined = created_at.strftime("Member since %B %d, %Y") if created_at else "Member"
        except Exception:
            joined = "Member"
        member_lbl = QLabel(joined)
        member_lbl.setObjectName("profileMemberLabel")
        text_col.addWidget(member_lbl)

        h.addLayout(text_col)
        h.addStretch()
        return card

    def _build_info_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("profileInfoCard")
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setAutoFillBackground(True)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(0)

        section_title = QLabel("Personal Information")
        section_title.setObjectName("profileSectionTitle")
        v.addWidget(section_title)

        v.addSpacing(12)

        rows = [
            ("Username",      self._user.username or "—"),
            ("Email",         self._user.email or "—"),
            ("Age",           self._calculate_age()),
            ("Date of Birth", self._format_birthday()),
            ("Time Played",  self._format_hours_played()),
        ]

        for i, (key, value) in enumerate(rows):
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 12, 0, 12)
            row_l.setSpacing(0)

            key_lbl = QLabel(key)
            key_lbl.setObjectName("profileInfoKey")
            key_lbl.setFixedWidth(150)

            val_lbl = QLabel(value)
            val_lbl.setObjectName("profileInfoValue")

            if key == "Time Played":
                self._hours_played_lbl = val_lbl
            elif key == "Age":
                self._age_lbl = val_lbl

            row_l.addWidget(key_lbl)
            row_l.addWidget(val_lbl, 1)
            v.addWidget(row_w)

            if i < len(rows) - 1:
                divider = QFrame()
                divider.setObjectName("profileDivider")
                divider.setFrameShape(QFrame.Shape.HLine)
                v.addWidget(divider)

        return card

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self._time_played_seconds = get_time_played(self._user.id) or 0
        except Exception:
            logger.warning("Could not refresh time_played for user_id: ..%s", self._user.id[-10:])
        if hasattr(self, "_hours_played_lbl"):
            self._hours_played_lbl.setText(self._format_hours_played())
        if hasattr(self, "_age_lbl"):
            self._age_lbl.setText(self._calculate_age())

    def _load_avatar(self):
        if self._user.avatar_blob:
            pixmap = QPixmap()
            if pixmap.loadFromData(self._user.avatar_blob):
                self.avatarLabel.setPixmap(pixmap)
                image_to_rounded(self.avatarLabel)
                return

        if self._user.avatar_path:
            avatar_data = fetch_avatar(self._user.avatar_path)
            if avatar_data:
                pixmap = QPixmap()
                if pixmap.loadFromData(avatar_data):
                    self.avatarLabel.setPixmap(pixmap)
                    image_to_rounded(self.avatarLabel)
                    return

        pixmap = QPixmap(":/images/graphics/avatar.png")
        if not pixmap.isNull():
            logger.error("Using default avatar for user_id: ..%s", self._user.id[-10:])
            self.avatarLabel.setPixmap(pixmap)
            image_to_rounded(self.avatarLabel)

    def set_avatar_bytes(self, data: bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.avatarLabel.setPixmap(pixmap)
            self.avatarLabel.setScaledContents(True)
            image_to_rounded(self.avatarLabel)

    def _calculate_age(self) -> str:
        bd = self._user.birthday_date
        if not bd:
            return "—"
        try:
            from datetime import date
            if isinstance(bd, str):
                bd = date.fromisoformat(bd)
            today = date.today()
            age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            return str(age)
        except Exception:
            return "—"

    def _format_birthday(self) -> str:
        bd = self._user.birthday_date
        if not bd:
            return "—"
        try:
            if isinstance(bd, str):
                from datetime import date
                bd = date.fromisoformat(bd)
            return bd.strftime("%B %d, %Y")
        except Exception:
            return str(bd)

    def _format_hours_played(self) -> str:
        total_seconds = self._time_played_seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
