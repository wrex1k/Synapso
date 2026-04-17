import datetime

from PySide6.QtCore import QEasingCurve, QFileInfo, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QComboBox, QFileDialog, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.components.back_button import BackButton
from app.ui.components.input_field import InputField
from app.utils.avatar import qpixmap_to_webp_blob, rounded_pixmap, restore_webp_blob_avatar
from app.utils.event_filters import enter_key_event_filter
from app.utils.logger import get_logger
logger = get_logger(__name__)
from app.utils.ui_helpers import draw_background, update_button_state
from app.utils.validator import validate_email, validate_username, validate_birthdate
from translations.translation import translate

"""
RegisterPersonal is the first step of the registration flow where the user sets personal details.

It collects username, email, and birthdate, manages UI state (idle/loading/error),
and emits the submitted data on success. Includes fade-in animations on show.
"""


class RegisterPersonal(QWidget):
    personal_data_submit = Signal(str, str, datetime.date, object)
    back_to_login_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("registerPersonal")
        self.setWindowTitle("Synapso")
        self.setWindowIcon(QIcon(":/images/graphics/logo.png"))
        self.setMinimumSize(QSize(1000, 800))

        self.states = ["idle", "loading", "error"]
        self.state = "idle"

        self._animations_started = False

        self._avatar_original_path: str | None = None
        self._is_custom_avatar = False
        self._avatar_cached_blob: bytes | None = None

        self._build_ui()
        self._populate_date_fields()
        self._setup_connections()
        self._set_default_avatar()
        self._setup_animations()
        self._retranslate_ui()

    def _build_ui(self):
        self._create_main_layout()

        self._create_title_section()
        self._create_avatar_section()
        self._create_username_email_fields()
        self._create_birthdate_section()
        self._create_next_button_section()
        
    def _create_main_layout(self):
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        contentWidget = QWidget(self)
        content_layout = QVBoxLayout(contentWidget)
        content_layout.setContentsMargins(40, 0, 40, 0)

        main_layout.addWidget(contentWidget, 0, 0)

        # back button
        self.backButton = BackButton(self)
        main_layout.addWidget(self.backButton, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.backButton.raise_()

        # main frame
        frame = QWidget(contentWidget)
        frame.setObjectName("frame")

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 120, 0, 70)
        frame.setMaximumWidth(760)
        content_layout.addWidget(frame, 0, Qt.AlignmentFlag.AlignHCenter)

        self._frame = frame
        self._frame_layout = frame_layout

    def _create_title_section(self):
        titleFrame = QWidget(self._frame)
        titleFrame.setObjectName("title")
        titleFrame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        title_layout = QVBoxLayout(titleFrame)
        title_row = QHBoxLayout()

        # title
        self.title = QLabel("Let's set up your profile", titleFrame)
        self.title.setObjectName("titleLabel")
        self.title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        title_row.addWidget(self.title, 0, Qt.AlignmentFlag.AlignLeft)

        # info
        self.info = QLabel(
            "Share a bit about yourself! Add your name, email, and date of birth. "
            "Don't forget to upload your photo with the 'Upload Image' button.",
            titleFrame,
        )
        self.info.setObjectName("info")
        self.info.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.info.setWordWrap(True)

        title_layout.addLayout(title_row)
        title_layout.addWidget(self.info)
        self._frame_layout.addWidget(titleFrame)

        # setup opacity for title section
        self.titleOpacity = QGraphicsOpacityEffect(titleFrame)
        titleFrame.setGraphicsEffect(self.titleOpacity)
        self.titleOpacity.setOpacity(0)
        self.titleFrame = titleFrame

    def _create_avatar_section(self):
        uploadFrame = QWidget(self._frame)
        uploadFrame.setObjectName("uploadImage")
        uploadFrame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        upload_layout = QVBoxLayout(uploadFrame)
        upload_layout.setSpacing(9)
        upload_layout.setContentsMargins(0, 0, 0, 0)

        self.profilePicture = QLabel("Profile picture", uploadFrame)
        self.profilePicture.setObjectName("profilePicture")
        self.profilePicture.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        upload_layout.addWidget(self.profilePicture)

        # avatar and upload button row
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(20)
        avatar_row.setContentsMargins(0, 0, 0, 0)

        self.profilePixmap = QLabel(uploadFrame)
        self.profilePixmap.setObjectName("profilePixmap")
        self.profilePixmap.setMinimumSize(QSize(100, 100))
        self.profilePixmap.setMaximumSize(QSize(100, 100))
        self.profilePixmap.setScaledContents(True)
        avatar_row.addWidget(self.profilePixmap)

        upload_button_layout = QVBoxLayout()
        upload_button_layout.setSpacing(0)

        self.uploadImageButton = QPushButton("Upload Image", uploadFrame)
        self.uploadImageButton.setObjectName("uploadImageButton")
        self.uploadImageButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.uploadRestriction = QLabel(
            ".png, .jpg, .jpeg files up to 2MB, recomended size is 256x256px",
            uploadFrame,
        )
        self.uploadRestriction.setObjectName("uploadRestriction")
        self.uploadRestriction.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        upload_button_layout.addWidget(self.uploadImageButton)
        upload_button_layout.addWidget(self.uploadRestriction)

        avatar_row.addLayout(upload_button_layout)
        upload_layout.addLayout(avatar_row)
        self._frame_layout.addWidget(uploadFrame)

        # setup opacity for animation avatar upload section
        self.uploadOpacity = QGraphicsOpacityEffect(uploadFrame)
        uploadFrame.setGraphicsEffect(self.uploadOpacity)
        self.uploadOpacity.setOpacity(0)

    def _create_username_email_fields(self):
        self.usernameField = InputField(
            label_text="",
            placeholder="",
            object_name="usernameEdit",
            min_width=610,
            parent=self._frame,
        )
        self.usernameField.installEventFilter(self)
        self._frame_layout.addWidget(self.usernameField)
        self.usernameEdit = self.usernameField.line_edit

        # setup opacity for animation username field
        self.usernameOpacity = QGraphicsOpacityEffect(self.usernameField)
        self.usernameField.setGraphicsEffect(self.usernameOpacity)
        self.usernameOpacity.setOpacity(0)
        self.usernameFrame = self.usernameField

        self.emailField = InputField(
            label_text="",
            placeholder="",
            object_name="emailEdit",
            min_width=610,
            parent=self._frame,
        )
        self.emailField.installEventFilter(self)
        self._frame_layout.addWidget(self.emailField)
        self.emailEdit = self.emailField.line_edit

        # setup opacity for animation email field
        self.emailOpacity = QGraphicsOpacityEffect(self.emailField)
        self.emailField.setGraphicsEffect(self.emailOpacity)
        self.emailOpacity.setOpacity(0)
        self.emailFrame = self.emailField

    def _create_birthdate_section(self):
        birthDateFrame = QWidget(self._frame)
        birthDateFrame.setObjectName("BirthDate")
        birthDateFrame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        birthdate_layout = QHBoxLayout(birthDateFrame)
        birthdate_layout.setSpacing(20)
        birthdate_layout.setContentsMargins(0, 0, 0, 0)

        # month
        month_layout = QVBoxLayout()
        month_layout.setSpacing(9)
        month_layout.setContentsMargins(0, 0, 0, 0)

        self.birthMonthLabel = QLabel("Birth month", birthDateFrame)
        self.birthMonthLabel.setObjectName("birthMonth")
        self.birthMonthLabel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.birthMonthBox = QComboBox(birthDateFrame)
        self.birthMonthBox.setObjectName("birthMonthBox")
        self.birthMonthBox.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.birthMonthBox.setMaxVisibleItems(6)

        month_layout.addWidget(self.birthMonthLabel)
        month_layout.addWidget(self.birthMonthBox)
        birthdate_layout.addLayout(month_layout, 3)

        # day
        day_layout = QVBoxLayout()
        day_layout.setSpacing(9)
        day_layout.setContentsMargins(0, 0, 0, 0)

        self.dayLabel = QLabel("Day", birthDateFrame)
        self.dayLabel.setObjectName("day")
        self.dayLabel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.dayBox = QComboBox(birthDateFrame)
        self.dayBox.setObjectName("dayBox")
        self.dayBox.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.dayBox.setMaxVisibleItems(6)

        day_layout.addWidget(self.dayLabel)
        day_layout.addWidget(self.dayBox)
        birthdate_layout.addLayout(day_layout, 1)

        # year
        year_layout = QVBoxLayout()
        year_layout.setSpacing(9)
        year_layout.setContentsMargins(0, 0, 0, 0)

        self.yearLabel = QLabel("Year", birthDateFrame)
        self.yearLabel.setObjectName("year")
        self.yearLabel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.yearBox = QComboBox(birthDateFrame)
        self.yearBox.setObjectName("yearBox")
        self.yearBox.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.yearBox.setMaxVisibleItems(1)

        year_layout.addWidget(self.yearLabel)
        year_layout.addWidget(self.yearBox)
        birthdate_layout.addLayout(year_layout, 2)

        self._frame_layout.addWidget(birthDateFrame)

        # setup opacity for animation birthdate section
        self.birthDateOpacity = QGraphicsOpacityEffect(birthDateFrame)
        birthDateFrame.setGraphicsEffect(self.birthDateOpacity)
        self.birthDateOpacity.setOpacity(0)
        self.birthDateFrame = birthDateFrame

    def _create_next_button_section(self):
        nextFrame = QWidget(self._frame)
        nextFrame.setObjectName("nextFrame")
        nextFrame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        next_layout = QHBoxLayout(nextFrame)
        next_layout.setSpacing(0)
        next_layout.setContentsMargins(0, 20, 0, 0)

        self.nextButton = QPushButton("Let's take next step", nextFrame)
        self.nextButton.setObjectName("primaryButton")
        self.nextButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.nextButton.setDefault(True)

        next_layout.addWidget(self.nextButton, 0, Qt.AlignmentFlag.AlignRight)
        self._frame_layout.addWidget(nextFrame)

        # setup opacity for animation next button
        self.nextOpacity = QGraphicsOpacityEffect(nextFrame)
        nextFrame.setGraphicsEffect(self.nextOpacity)
        self.nextOpacity.setOpacity(0)
        self.nextFrame = nextFrame

    def _populate_date_fields(self):
        self.today = datetime.date.today()
        self.months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        self.birthMonthBox.addItems(self.months)
        self.dayBox.addItems([str(d) for d in range(1, 32)])
        self.yearBox.addItems([str(y) for y in range(self.today.year - 15, 1940, -1)])

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

            current_day = self.dayBox.currentText()

            self.dayBox.clear()
            self.dayBox.addItems([str(d) for d in range(1, max_days + 1)])

            if current_day and int(current_day) <= max_days:
                self.dayBox.setCurrentText(current_day)
        except (ValueError, AttributeError):
            pass

    def _setup_connections(self):
        self.uploadImageButton.clicked.connect(self._upload_image)
        self.nextButton.clicked.connect(self.handle_personal_register)

        self.backButton.clicked.connect(self.on_back_to_login)

        self.birthMonthBox.currentIndexChanged.connect(self._update_days_for_month)
        self.yearBox.currentTextChanged.connect(self._update_days_for_month)

    def _retranslate_ui(self):
        self.title.setText(
            translate("RegisterPersonal", "Let's set up your profile")
        )

        self.info.setText(
            translate(
                "RegisterPersonal",
                "Share a bit about yourself! Add your name, email, and date of birth. Don't forget to upload your photo with the 'Upload Image' button.",
            )
        )

        self.profilePicture.setText(translate("RegisterPersonal", "Profile picture"))

        self.uploadImageButton.setText(translate("RegisterPersonal", "Upload Image"))
        self.uploadRestriction.setText(
            translate(
                "RegisterPersonal",
                ".png, .jpg, .jpeg files up to 2MB",
            )
        )

        self.usernameField.setTitle(translate("RegisterPersonal", "Username"))
        self.usernameField.setPlaceholderText(translate("RegisterPersonal", "johndoe"))
        self.emailField.setTitle(translate("RegisterPersonal", "Email"))
        self.emailField.setPlaceholderText(translate("RegisterPersonal", "john.doe@example.com"))

        self.birthMonthLabel.setText(translate("RegisterPersonal", "Birth month"))
        self.dayLabel.setText(translate("RegisterPersonal", "Day"))
        self.yearLabel.setText(translate("RegisterPersonal", "Year"))

        months_translated = [
            translate("RegisterPersonal", "January"),
            translate("RegisterPersonal", "February"),
            translate("RegisterPersonal", "March"),
            translate("RegisterPersonal", "April"),
            translate("RegisterPersonal", "May"),
            translate("RegisterPersonal", "June"),
            translate("RegisterPersonal", "July"),
            translate("RegisterPersonal", "August"),
            translate("RegisterPersonal", "September"),
            translate("RegisterPersonal", "October"),
            translate("RegisterPersonal", "November"),
            translate("RegisterPersonal", "December"),
        ]

        try:
            current = self.birthMonthBox.currentText()
            self.birthMonthBox.clear()
            self.birthMonthBox.addItems(months_translated)
            if current:
                idx = self.birthMonthBox.findText(current)
                if idx != -1:
                    self.birthMonthBox.setCurrentIndex(idx)
        except Exception:
            pass

        self.nextButton.setText(translate("RegisterPersonal", "Let's take next step"))

    def on_back_to_login(self):
        self.reset_ui()
        self.back_to_login_signal.emit()

    def _setup_animations(self):
        pass

    def _set_default_avatar(self):
        size = self.profilePixmap.size()
        pixmap = QPixmap(":/images/graphics/avatar.png")

        if pixmap.isNull():
            logger.error("Failed to load default avatar image")
            return

        rounded = rounded_pixmap(pixmap, size)
        self.profilePixmap.setPixmap(rounded)

    def set_avatar_from_blob(self, avatar_blob: bytes):
        try:
            if restore_webp_blob_avatar(self.profilePixmap, avatar_blob):
                self._is_custom_avatar = True
                self._avatar_cached_blob = avatar_blob
            else:
                logger.warning("Failed to restore avatar from blob")
        except Exception as e:
            logger.error("Failed to restore avatar from blob: %s", e)

    def _upload_image(self):
        logger.debug("Upload image button clicked")

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp)")

        if not file_dialog.exec():
            return

        selected = file_dialog.selectedFiles()
        if not selected:
            logger.debug("No file selected")
            return
        logger.debug("Selected file: %s", selected[0])

        image_path = selected[0]

        if QFileInfo(image_path).size() > 2 * 1024 * 1024:
            update_button_state(
                self.uploadImageButton,
                state = self.state,
                idle_text=translate("RegisterPersonal", "Upload Image"),
                error_text=translate("RegisterPersonal", "File too large"),
                auto_reset_ms=3000,
            )
            logger.debug("Selected file too large")
            return

        self._avatar_original_path = image_path
        self._is_custom_avatar = True

        pixmap = QPixmap(image_path)
        size = self.profilePixmap.size()

        rounded = rounded_pixmap(pixmap, size)
        self.profilePixmap.setPixmap(rounded)


    def handle_personal_register(self):
        if self.state == "loading" or self.state == "error":
            logger.debug("Already submitting or showing error, ignoring click")
            return

        username = self.usernameEdit.text().strip()
        email = self.emailEdit.text().strip()

        error_msg  = validate_username(username)
        if error_msg:
            self.show_personal_error(error_msg)
            return
        
        error_msg = validate_email(email)
        if error_msg:
            self.show_personal_error(error_msg)
            return

        day = int(self.dayBox.currentText())
        month = self.birthMonthBox.currentIndex() + 1
        year = int(self.yearBox.currentText())
        birthday_date = datetime.date(year, month, day)

        error_msg = validate_birthdate(birthday_date, min_years=15, max_years=120)
        if error_msg:
            self.show_personal_error(error_msg)
            return

        blob = None
        if self._is_custom_avatar:
            # Check if we have a cached blob (from returned prefill) first
            if self._avatar_cached_blob:
                blob = self._avatar_cached_blob
            # Otherwise create blob from original path (fresh upload)
            elif self._avatar_original_path:
                pixmap = QPixmap(self._avatar_original_path)
                blob = qpixmap_to_webp_blob(pixmap) 

        self.state = "idle"
        update_button_state(
            self.nextButton,
            "idle",
            idle_text=translate("RegisterPersonal", "Let's take next step"),
            loading_text=translate("RegisterPersonal", "Continuing…"),
        )

        self.personal_data_submit.emit(username, email, birthday_date, blob)

    def show_personal_error(self, message: str):
        self.state = "error"

        update_button_state(
            self.nextButton,
            "error",
            idle_text=translate("RegisterPersonal", "Let's take next step"),
            loading_text=translate("RegisterPersonal", "Continuing…"),
            error_text=message,
            auto_reset_ms=2000,
        )

        QTimer.singleShot(2000, lambda: setattr(self, "state", "idle"))

    def show_checking_state(self):
        self.state = "loading"
        update_button_state(
            self.nextButton,
            "loading",
            idle_text=translate("RegisterPersonal", "Let's take next step"),
            loading_text=translate("RegisterPersonal", "Checking…"),
        )

    def reset_checking_state(self):
        self.state = "idle"
        update_button_state(
            self.nextButton,
            "idle",
            idle_text=translate("RegisterPersonal", "Let's take next step"),
            loading_text=translate("RegisterPersonal", "Checking…"),
        )

    def _setup_animations(self):
        # animation sequence
        self.titleAnim = QPropertyAnimation(self.titleOpacity, b"opacity")
        self.titleAnim.setDuration(800)
        self.titleAnim.setStartValue(0.0)
        self.titleAnim.setEndValue(1.0)
        self.titleAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # upload section fade-in
        self.uploadAnim = QPropertyAnimation(self.uploadOpacity, b"opacity")
        self.uploadAnim.setDuration(800)
        self.uploadAnim.setStartValue(0.0)
        self.uploadAnim.setEndValue(1.0)
        self.uploadAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # username field fade-in
        self.usernameAnim = QPropertyAnimation(self.usernameOpacity, b"opacity")
        self.usernameAnim.setDuration(800)
        self.usernameAnim.setStartValue(0.0)
        self.usernameAnim.setEndValue(1.0)
        self.usernameAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # email field fade-in
        self.emailAnim = QPropertyAnimation(self.emailOpacity, b"opacity")
        self.emailAnim.setDuration(800)
        self.emailAnim.setStartValue(0.0)
        self.emailAnim.setEndValue(1.0)
        self.emailAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # birthdate section fade-in
        self.birthDateAnim = QPropertyAnimation(self.birthDateOpacity, b"opacity")
        self.birthDateAnim.setDuration(800)
        self.birthDateAnim.setStartValue(0.0)
        self.birthDateAnim.setEndValue(1.0)
        self.birthDateAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # next button fade-in
        self.nextAnim = QPropertyAnimation(self.nextOpacity, b"opacity")
        self.nextAnim.setDuration(800)
        self.nextAnim.setStartValue(0.0)
        self.nextAnim.setEndValue(1.0)
        self.nextAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _start_animations(self):
        QTimer.singleShot(100, self.titleAnim.start)
        QTimer.singleShot(250, self.uploadAnim.start)
        QTimer.singleShot(400, self.usernameAnim.start)
        QTimer.singleShot(550, self.emailAnim.start)
        QTimer.singleShot(700, self.birthDateAnim.start)
        QTimer.singleShot(850, self.nextAnim.start)

    def reset_ui(self) -> None:
        self.state = "idle"
        self.usernameEdit.clear()
        self.emailEdit.clear()
        self.dayBox.setCurrentIndex(0)
        self.birthMonthBox.setCurrentIndex(0)
        self.yearBox.setCurrentIndex(0)
        self._avatar_original_path = None
        self._is_custom_avatar = False
        self._avatar_cached_blob = None
        self._set_default_avatar()

        update_button_state(
            self.nextButton,
            "idle",
            idle_text=translate("RegisterPersonal", "Let's take next step"),
            loading_text=translate("RegisterPersonal", "Continuing…"),
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._retranslate_ui()
        if not self._animations_started:
            self._animations_started = True
            self._start_animations()

    def eventFilter(self, watched, event):
        if enter_key_event_filter(self, watched, event, on_enter=self.handle_personal_register):
            return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event) -> None:
        draw_background(self, event)