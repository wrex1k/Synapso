import re, datetime, io
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QWidget
from dateutil.relativedelta import relativedelta
from PySide6.QtGui import QPainter, QPixmap, QPainterPath
from PySide6.QtCore import Qt, Signal, QBuffer, QIODevice
from app.utils import show_error, draw_background
from app.ui.register_personal_ui import Ui_registerPersonal
from PIL import Image


class RegisterPersonal(QWidget):
    # define signal for registration data and back request
    personal_data = Signal(str, str, datetime.date, bytes)
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        # initialize UI and set window title
        self.ui = Ui_registerPersonal()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # insert data into birth fields
        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.ui.birthMonthBox.addItems(self.months)
        self.ui.dayBox.addItems([str(day) for day in range(1, 32)])
        self.ui.yearBox.addItems([str(year) for year in range(2024, 1900, -1)])

        # set default avatar for registration
        self._set_default_avatar()
        self._custom_avatar_selected = False

        # connect upload, next, back buttons
        self.ui.uploadImageButton.clicked.connect(self.upload_image)
        self.ui.next.clicked.connect(self.handle_personal_register)
        self.ui.back.clicked.connect(self.back_requested.emit)

    # upload and process profile image
    def upload_image(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]

                if QtCore.QFileInfo(image_path).size() > 2 * 1024 * 1024:
                    show_error(self.ui.uploadImageButton, "File too large")
                    return

                pixmap = QPixmap(image_path)
                size = self.ui.profilePixmap.size()
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                rounded = QPixmap(size)
                rounded.fill(Qt.transparent)

                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, size.width(), size.height(), 20, 20)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()

                self.ui.profilePixmap.setPixmap(rounded)
                self._custom_avatar_selected = True

    # handle personal registration data
    def handle_personal_register(self):
        username = self.ui.usernameEdit.text().strip()
        email = self.ui.emailEdit.text().strip()

        # birthday parsing
        try:
            day = int(self.ui.dayBox.currentText())
            month = self.ui.birthMonthBox.currentIndex() + 1
            year = int(self.ui.yearBox.currentText())
            birthday_date = datetime.date(year, month, day)
        except Exception:
            show_error(self.ui.next, "Invalid date format")
            return

        # avatar compression and validation
        pixmap = self.ui.profilePixmap.pixmap()
        blob = None
        if pixmap and not pixmap.isNull():
            try:
                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)

                pixmap.toImage().save(buffer, "PNG")

                raw_bytes = buffer.data()
                buffer.close()

                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                img.thumbnail((256, 256))
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=80, method=6)
                blob = output.getvalue()

                if len(blob) > 2 * 1024 * 1024:
                    show_error(self.ui.next, "Compressed image exceeds 2 MB limit.")
                    return

            except Exception as e:
                show_error(self.ui.next, f"Error processing avatar: {e}")
                return

        # email regex and age limits
        email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        today = datetime.date.today()
        too_young = birthday_date > today - relativedelta(years=13)
        too_old = birthday_date < today - relativedelta(years=120)
       
        # username validation
        if not username:
            show_error(self.ui.next, "Insert username")
            return
        if len(username) < 3:
            show_error(self.ui.next, "Username must be at least 3 characters")
            return
        if len(username) > 20:
            show_error(self.ui.next, "Username must be less than 20 characters")
            return
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            show_error(self.ui.next, "Username can only contain letters, numbers and underscores")
            return
        if any(bad in username.lower() for bad in ['admin', 'root', 'user', 'null', 'undefined', 'system', 'test']):
            show_error(self.ui.next, "This username is reserved")
            return

        # email validation
        if not email or not re.match(email_regex, email):
            show_error(self.ui.next, "Insert valid email")
            return

        # age validation
        if birthday_date > too_young:
            show_error(self.ui.next, "You must be at least 13 years old to register")
            return
        if birthday_date < too_old:
            show_error(self.ui.next, "Invalid birth date - too old")
            return

        self.personal_data.emit(username, email, birthday_date, blob)

    # set default avatar for registration
    def _set_default_avatar(self):
        size = self.ui.profilePixmap.size()
        default_pixmap = QPixmap(":/images/graphics/avatar.png")
        if default_pixmap.isNull():
            print("[WARN] Default avatar image not found.")
            return

        pixmap = default_pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rounded = QPixmap(size)
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size.width(), size.height(), 20, 20)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self.ui.profilePixmap.setPixmap(rounded)

    # paint event for custom background
    def paintEvent(self, event):
        draw_background(self, event)