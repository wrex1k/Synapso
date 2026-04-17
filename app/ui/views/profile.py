from __future__ import annotations

from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODevice, QSize, Qt, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDialog, QFileDialog, QFrame, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.models.user import User
from app.repository.user_repository import fetch_avatar
from app.utils.ui_helpers import image_to_rounded, build_header
from app.utils.event_filters import password_event_filter
from translations.translation import translate


class _DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("deleteConfirmDialog")
        self.setFixedWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 28)
        layout.setSpacing(0)

        title = QLabel(translate("ProfileView", "Delete Account"))
        title.setObjectName("deleteDialogTitle")
        layout.addWidget(title)

        layout.addSpacing(12)

        desc = QLabel(
            translate(
                "ProfileView",
                "Are you sure you want to delete your account?\nAll your data will be permanently removed. This action cannot be undone."
            )
        )
        desc.setObjectName("deleteDialogDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(28)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 0, 0, 0)

        cancel_btn = QPushButton(translate("ProfileView", "Cancel"))
        cancel_btn.setObjectName("deleteDialogCancelBtn")
        cancel_btn.setFixedHeight(42)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton(translate("ProfileView", "Delete account"))
        confirm_btn.setObjectName("deleteDialogConfirmBtn")
        confirm_btn.setFixedHeight(42)
        confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().window().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)


class ProfileView(QWidget):
    save_profile_requested = Signal(str, object)
    change_password_requested = Signal(str, str, str)
    delete_account_requested = Signal()
    upload_avatar_requested = Signal(bytes)
    avatar_upload_succeeded = Signal(bytes)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setObjectName("profileView")
        self._user = user
        self._profile_feedback_timer = None
        self._password_feedback_timer = None
        self._initial_username = ""
        self._initial_birthday = None
        self._build_ui()
        self._fill_user_data()
        self._capture_initial_profile_state()
        self._update_save_button_state()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 60)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            translate("ProfileView", "Profile"),
            translate("ProfileView", "Manage your profile details and account security")
        )
        root.addWidget(header)
        root.addWidget(self._build_hero_card())

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.setContentsMargins(0, 0, 0, 0)

        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.addWidget(self._build_personal_info_card(), 1)
        left_column.addWidget(self._build_danger_panel())

        right_column = QVBoxLayout()
        right_column.setSpacing(0)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.addWidget(self._build_change_password_card(), 1)

        content_row.addLayout(left_column, 1)
        content_row.addLayout(right_column, 1)

        root.addLayout(content_row, 1)

    def _build_hero_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("profileHeroCard")
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(18)

        self.avatarLabel = QLabel(card)
        self.avatarLabel.setObjectName("profileAvatar")
        self.avatarLabel.setFixedSize(QSize(84, 84))
        self.avatarLabel.setScaledContents(True)
        self.avatarLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatarLabel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.avatarLabel.setToolTip(translate("ProfileView", "Click to change profile photo"))
        self.avatarLabel.mousePressEvent = lambda event: self._on_avatar_clicked() if event.button() == Qt.MouseButton.LeftButton else None
        self._load_avatar()

        layout.addWidget(self.avatarLabel)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 0, 0, 0)

        self._username_preview_lbl = QLabel(self._user.username or "—")
        self._username_preview_lbl.setObjectName("profileUsernameLabel")

        self._handle_preview_lbl = QLabel(
            f"@{self._user.username.lower()}" if self._user.username else ""
        )
        self._handle_preview_lbl.setObjectName("profileHandleLabel")

        self._member_lbl = QLabel(self._format_member_since())
        self._member_lbl.setObjectName("profileMemberLabel")

        text_col.addWidget(self._username_preview_lbl)
        text_col.addWidget(self._handle_preview_lbl)
        text_col.addWidget(self._member_lbl)

        layout.addLayout(text_col)
        layout.addStretch()

        return card

    def _build_personal_info_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("profileMainCard")
        card.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(0)

        title = QLabel(translate("ProfileView", "Personal Information"))
        title.setObjectName("profileSectionTitle")
        layout.addWidget(title)
        layout.addSpacing(18)

        layout.addWidget(self._build_input_block(translate("ProfileView", "Username"), self._build_username_input()))
        layout.addSpacing(14)
        layout.addWidget(self._build_input_block(translate("ProfileView", "Email"), self._build_email_value()))
        layout.addSpacing(14)
        layout.addWidget(self._build_input_block(translate("ProfileView", "Date of Birth"), self._build_birthday_input()))
        layout.addSpacing(30)

        self._profile_feedback_lbl = QLabel("")
        self._profile_feedback_lbl.setObjectName("profileFeedbackLabel")
        self._profile_feedback_lbl.hide()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        self._profile_feedback_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_row.addWidget(self._profile_feedback_lbl, 1, Qt.AlignmentFlag.AlignVCenter)

        btn_row.addStretch()

        self._save_profile_btn = QPushButton(translate("ProfileView", "Save changes"))
        self._save_profile_btn.setObjectName("profilePrimaryButton")
        self._save_profile_btn.setFixedHeight(42)
        self._save_profile_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._save_profile_btn.setEnabled(False)
        self._save_profile_btn.clicked.connect(self._on_save_profile_clicked)

        btn_row.addWidget(self._save_profile_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(btn_row)
        layout.addStretch()

        return card

    def _build_change_password_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("profileMainCard")
        card.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(0)

        title = QLabel(translate("ProfileView", "Change Password"))
        title.setObjectName("profileSectionTitle")
        layout.addWidget(title)
        layout.addSpacing(18)

        layout.addWidget(
            self._build_input_block(
                translate("ProfileView", "Current Password"),
                self._build_password_input(
                    translate("ProfileView", "Enter current password"),
                    "_current_password_input",
                ),
            )
        )
        layout.addSpacing(14)
        layout.addWidget(
            self._build_input_block(
                translate("ProfileView", "New Password"),
                self._build_password_input(
                    translate("ProfileView", "Enter new password"),
                    "_new_password_input",
                ),
            )
        )
        layout.addSpacing(14)
        layout.addWidget(
            self._build_input_block(
                translate("ProfileView", "Confirm Password"),
                self._build_password_input(
                    translate("ProfileView", "Confirm new password"),
                    "_confirm_password_input",
                ),
            )
        )
        layout.addSpacing(30)

        self._password_feedback_lbl = QLabel("")
        self._password_feedback_lbl.setObjectName("profileFeedbackLabel")
        self._password_feedback_lbl.hide()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        self._password_feedback_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_row.addWidget(self._password_feedback_lbl, 1, Qt.AlignmentFlag.AlignVCenter)

        btn_row.addStretch()

        self._change_password_btn = QPushButton(translate("ProfileView", "Change password"))
        self._change_password_btn.setObjectName("profilePrimaryButton")
        self._change_password_btn.setFixedHeight(42)
        self._change_password_btn.clicked.connect(self._on_change_password_clicked)

        btn_row.addWidget(self._change_password_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(btn_row)
        layout.addStretch()

        return card

    def _build_danger_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("profileMainCard")
        panel.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(8)

        title = QLabel(translate("ProfileView", "Delete Account"))
        title.setObjectName("profileDangerTitle")

        desc = QLabel(translate("ProfileView", "This action is permanent and cannot be undone."))
        desc.setObjectName("profileDangerDescription")

        self._delete_account_btn = QPushButton(translate("ProfileView", "Delete account"))
        self._delete_account_btn.setObjectName("profileDangerButton")
        self._delete_account_btn.setFixedHeight(42)
        self._delete_account_btn.clicked.connect(self._on_delete_account_clicked)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(20)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(title)
        text_col.addWidget(desc)
        row.addLayout(text_col)
        row.addStretch()
        row.addWidget(self._delete_account_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(row)

        return panel

    def _build_username_input(self) -> QWidget:
        self._username_input = QLineEdit()
        self._username_input.setObjectName("profileLineEdit")
        self._username_input.setPlaceholderText(translate("ProfileView", "Enter your username"))
        self._username_input.textChanged.connect(self._sync_preview)
        self._username_input.textChanged.connect(self._update_save_button_state)
        return self._username_input

    def _build_email_value(self) -> QWidget:
        self._email_value_lbl = QLabel(getattr(self._user, "email", None) or "—")
        self._email_value_lbl.setObjectName("profileReadonlyValue")
        self._email_value_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return self._email_value_lbl

    def _build_birthday_input(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        import datetime
        today = datetime.date.today()
        try:
            self._max_birthdate = datetime.date(today.year - 15, today.month, today.day)
        except ValueError:
            self._max_birthdate = datetime.date(today.year - 15, 2, 28)

        self._months = [
            translate("ProfileView", "January"),
            translate("ProfileView", "February"),
            translate("ProfileView", "March"),
            translate("ProfileView", "April"),
            translate("ProfileView", "May"),
            translate("ProfileView", "June"),
            translate("ProfileView", "July"),
            translate("ProfileView", "August"),
            translate("ProfileView", "September"),
            translate("ProfileView", "October"),
            translate("ProfileView", "November"),
            translate("ProfileView", "December"),
        ]

        self.birthMonthBox = QComboBox()
        self.birthMonthBox.setObjectName("profileBirthMonthBox")
        self.birthMonthBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.birthMonthBox.setMaxVisibleItems(1)

        self.dayBox = QComboBox()
        self.dayBox.setObjectName("profileDayBox")
        self.dayBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dayBox.setMaxVisibleItems(1)

        self.yearBox = QComboBox()
        self.yearBox.setObjectName("profileYearBox")
        self.yearBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.yearBox.setMaxVisibleItems(1)

        layout.addWidget(self.birthMonthBox, 3)
        layout.addWidget(self.dayBox, 1)
        layout.addWidget(self.yearBox, 2)

        self.yearBox.addItems([str(y) for y in range(self._max_birthdate.year, 1939, -1)])
        self._populate_months_for_year(self._max_birthdate.year)
        self._populate_days_for_month(self._max_birthdate.year, self._max_birthdate.month)
        self.dayBox.setCurrentText(str(self._max_birthdate.day))

        self.birthMonthBox.currentIndexChanged.connect(self._update_days_for_month)
        self.yearBox.currentTextChanged.connect(self._update_months_for_year)

        self.birthMonthBox.currentIndexChanged.connect(self._update_save_button_state)
        self.dayBox.currentTextChanged.connect(self._update_save_button_state)
        self.yearBox.currentTextChanged.connect(self._update_save_button_state)

        return wrapper

    def _build_password_input(self, placeholder: str, attr_name: str) -> QWidget:
        line = QLineEdit()
        line.setObjectName("profileLineEdit")
        line.setPlaceholderText(placeholder)
        line.setEchoMode(QLineEdit.EchoMode.Password)
        line.installEventFilter(self)
        setattr(self, attr_name, line)
        return line

    def _build_input_block(self, label_text: str, field_widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        label = QLabel(label_text)
        label.setObjectName("profileInputLabel")

        layout.addWidget(label)
        layout.addWidget(field_widget)

        return wrapper

    def _fill_user_data(self):
        self._username_input.setText(self._user.username or "")

        bd = getattr(self._user, "birthday_date", None)
        if bd:
            try:
                if isinstance(bd, str):
                    from datetime import date
                    bd = date.fromisoformat(bd)
                if bd > self._max_birthdate:
                    bd = self._max_birthdate
                self.yearBox.setCurrentText(str(bd.year))
                self._populate_months_for_year(bd.year)
                self._populate_days_for_month(bd.year, bd.month)
                self.dayBox.setCurrentText(str(bd.day))
            except Exception:
                self._reset_birthdate_to_max()
        else:
            self._reset_birthdate_to_max()

        self._sync_preview()

    def _get_current_birthday(self):
        from datetime import date
        try:
            year_text = self.yearBox.currentText()
            month_index = self.birthMonthBox.currentIndex()
            day_text = self.dayBox.currentText()

            if year_text and day_text and month_index >= 0:
                return date(int(year_text), month_index + 1, int(day_text))
        except Exception:
            pass
        return None

    def _capture_initial_profile_state(self):
        self._initial_username = self._username_input.text().strip()
        self._initial_birthday = self._get_current_birthday()

    def _has_profile_changed(self) -> bool:
        current_username = self._username_input.text().strip()
        current_birthday = self._get_current_birthday()
        return (
            current_username != self._initial_username
            or current_birthday != self._initial_birthday
        )

    def _update_save_button_state(self):
        if hasattr(self, "_save_profile_btn"):
            self._save_profile_btn.setEnabled(self._has_profile_changed())

    def _update_months_for_year(self):
        try:
            year_text = self.yearBox.currentText()
            if not year_text:
                return
            year = int(year_text)
            current_month_name = self.birthMonthBox.currentText()

            self.birthMonthBox.blockSignals(True)
            self.birthMonthBox.clear()
            if year == self._max_birthdate.year:
                allowed_months = self._months[: self._max_birthdate.month]
            else:
                allowed_months = self._months
            self.birthMonthBox.addItems(allowed_months)

            if current_month_name in allowed_months:
                self.birthMonthBox.setCurrentText(current_month_name)
            else:
                self.birthMonthBox.setCurrentIndex(len(allowed_months) - 1)
            self.birthMonthBox.blockSignals(False)
        finally:
            self._update_days_for_month()

    def _update_days_for_month(self):
        try:
            month = self.birthMonthBox.currentIndex() + 1
            year_text = self.yearBox.currentText()
            if not year_text:
                return
            year = int(year_text)

            if month == 2:
                is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                max_days = 29 if is_leap else 28
            elif month in [4, 6, 9, 11]:
                max_days = 30
            else:
                max_days = 31

            if year == self._max_birthdate.year and month == self._max_birthdate.month:
                max_days = min(max_days, self._max_birthdate.day)

            current_day = self.dayBox.currentText()

            self.dayBox.clear()
            self.dayBox.addItems([str(d) for d in range(1, max_days + 1)])

            if current_day and int(current_day) <= max_days:
                self.dayBox.setCurrentText(current_day)
            else:
                self.dayBox.setCurrentText(str(max_days))
        except (ValueError, AttributeError):
            pass

    def _populate_months_for_year(self, year: int):
        self.yearBox.setCurrentText(str(year))
        self._update_months_for_year()

    def _populate_days_for_month(self, year: int, month: int):
        self.birthMonthBox.setCurrentIndex(month - 1)
        self._update_days_for_month()

    def _reset_birthdate_to_max(self):
        self.yearBox.setCurrentText(str(self._max_birthdate.year))
        self._update_months_for_year()
        self.birthMonthBox.setCurrentIndex(self._max_birthdate.month - 1)
        self._update_days_for_month()
        self.dayBox.setCurrentText(str(self._max_birthdate.day))

    def _sync_preview(self):
        username = self._username_input.text().strip()
        self._username_preview_lbl.setText(username or "—")
        self._handle_preview_lbl.setText(f"@{username.lower()}" if username else "")

    def _on_avatar_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            translate("ProfileView", "Select Profile Photo"),
            "",
            translate("ProfileView", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"),
        )
        if not path:
            return
        img = QImage(path)
        if img.isNull():
            return
        size = min(img.width(), img.height())
        x = (img.width() - size) // 2
        y = (img.height() - size) // 2
        img = img.copy(x, y, size, size).scaled(
            256, 256,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        buf = QByteArray()
        buffer = QBuffer(buf)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buffer, "WEBP", 85)
        buffer.close()
        data = bytes(buf)
        if not data:
            return
        self.set_avatar_bytes(data)
        self.upload_avatar_requested.emit(data)

    def _on_delete_account_clicked(self):
        dlg = _DeleteConfirmDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.delete_account_requested.emit()

    def _on_save_profile_clicked(self):
        username = self._username_input.text().strip()
        birthday = self._get_current_birthday()

        self._profile_feedback_lbl.hide()
        self.save_profile_requested.emit(username, birthday)

    def _on_change_password_clicked(self):
        current_password = self._current_password_input.text()
        new_password = self._new_password_input.text()
        confirm_password = self._confirm_password_input.text()

        self._password_feedback_lbl.hide()
        self.change_password_requested.emit(current_password, new_password, confirm_password)

    def set_profile_feedback(self, text: str, is_error: bool = False):
        self._profile_feedback_lbl.setText(text)
        self._profile_feedback_lbl.setProperty("error", "true" if is_error else "false")
        self._profile_feedback_lbl.style().unpolish(self._profile_feedback_lbl)
        self._profile_feedback_lbl.style().polish(self._profile_feedback_lbl)
        self._profile_feedback_lbl.show()

        if not is_error:
            self._capture_initial_profile_state()
            self._update_save_button_state()

        if self._profile_feedback_timer is None:
            self._profile_feedback_timer = QTimer(self)
            self._profile_feedback_timer.setSingleShot(True)
            self._profile_feedback_timer.timeout.connect(self._profile_feedback_lbl.hide)
        self._profile_feedback_timer.start(3000)

    def set_password_feedback(self, text: str, is_error: bool = False):
        self._password_feedback_lbl.setText(text)
        self._password_feedback_lbl.setProperty("error", "true" if is_error else "false")
        self._password_feedback_lbl.style().unpolish(self._password_feedback_lbl)
        self._password_feedback_lbl.style().polish(self._password_feedback_lbl)
        self._password_feedback_lbl.show()
        if self._password_feedback_timer is None:
            self._password_feedback_timer = QTimer(self)
            self._password_feedback_timer.setSingleShot(True)
            self._password_feedback_timer.timeout.connect(self._password_feedback_lbl.hide)
        self._password_feedback_timer.start(3000)

    def clear_password_fields(self):
        self._current_password_input.clear()
        self._new_password_input.clear()
        self._confirm_password_input.clear()

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("ProfileView", "Profile"))
        self._page_subtitle_lbl.setText(translate("ProfileView", "Manage your profile details and account security"))
        self._save_profile_btn.setText(translate("ProfileView", "Save changes"))
        self._change_password_btn.setText(translate("ProfileView", "Change password"))
        self._delete_account_btn.setText(translate("ProfileView", "Delete account"))
        self._username_input.setPlaceholderText(translate("ProfileView", "Enter your username"))
        self._current_password_input.setPlaceholderText(translate("ProfileView", "Enter current password"))
        self._new_password_input.setPlaceholderText(translate("ProfileView", "Enter new password"))
        self._confirm_password_input.setPlaceholderText(translate("ProfileView", "Confirm new password"))
        self.avatarLabel.setToolTip(translate("ProfileView", "Click to change profile photo"))
        self._member_lbl.setText(self._format_member_since())

        section_titles = self.findChildren(QLabel, "profileSectionTitle")
        for lbl, key in zip(section_titles, ["Personal Information", "Change Password"]):
            lbl.setText(translate("ProfileView", key))

        danger_title = self.findChild(QLabel, "profileDangerTitle")
        if danger_title:
            danger_title.setText(translate("ProfileView", "Delete Account"))
        danger_desc = self.findChild(QLabel, "profileDangerDescription")
        if danger_desc:
            danger_desc.setText(translate("ProfileView", "This action is permanent and cannot be undone."))

        input_labels = self.findChildren(QLabel, "profileInputLabel")
        for lbl, key in zip(input_labels, ["Username", "Email", "Date of Birth", "Current Password", "New Password", "Confirm Password"]):
            lbl.setText(translate("ProfileView", key))

        current_month_idx = self.birthMonthBox.currentIndex()
        self._months = [
            translate("ProfileView", "January"),
            translate("ProfileView", "February"),
            translate("ProfileView", "March"),
            translate("ProfileView", "April"),
            translate("ProfileView", "May"),
            translate("ProfileView", "June"),
            translate("ProfileView", "July"),
            translate("ProfileView", "August"),
            translate("ProfileView", "September"),
            translate("ProfileView", "October"),
            translate("ProfileView", "November"),
            translate("ProfileView", "December"),
        ]
        year_text = self.yearBox.currentText()
        try:
            year = int(year_text)
        except (ValueError, TypeError):
            year = self._max_birthdate.year
        allowed_months = self._months[: self._max_birthdate.month] if year == self._max_birthdate.year else self._months
        self.birthMonthBox.blockSignals(True)
        self.birthMonthBox.clear()
        self.birthMonthBox.addItems(allowed_months)
        if 0 <= current_month_idx < len(allowed_months):
            self.birthMonthBox.setCurrentIndex(current_month_idx)
        self.birthMonthBox.blockSignals(False)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._retranslate_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_preview()
        self._update_save_button_state()

    def _load_avatar(self):
        if getattr(self._user, "avatar_blob", None):
            pixmap = QPixmap()
            if pixmap.loadFromData(self._user.avatar_blob):
                self.avatarLabel.setPixmap(pixmap)
                image_to_rounded(self.avatarLabel)
                return

        if getattr(self._user, "avatar_path", None):
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

    def eventFilter(self, watched, event):
        if isinstance(watched, QLineEdit):
            if password_event_filter(self, watched, event):
                return True
        return super().eventFilter(watched, event)

    def set_avatar_bytes(self, data: bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.avatarLabel.setPixmap(pixmap)
            self.avatarLabel.setScaledContents(True)
            image_to_rounded(self.avatarLabel)

    def _format_member_since(self) -> str:
        try:
            created_at = self._user.created_at
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return created_at.strftime(translate("ProfileView", "Member since %B %d, %Y")) if created_at else translate("ProfileView", "Member")
        except Exception:
            return translate("ProfileView", "Member")