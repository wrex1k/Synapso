import re, datetime
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget
from app.utils import show_error, draw_background, set_default_avatar
from PySide6.QtGui import QPainter, QPixmap, QPainterPath
from app.ui.register_personal_ui import Ui_registerPersonal
from PySide6.QtCore import QEvent, Qt, Signal, QBuffer, QIODevice

class RegisterPersonal(QWidget):
    personal_data = Signal(str, str, datetime.date, bytes)
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        self.ui = Ui_registerPersonal()
        self.ui.setupUi(self)
        self.setWindowTitle("Synapso")

        # insert data into birth fields
        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.ui.birthMonthBox.addItems(self.months)
        self.ui.dayBox.addItems([str(day) for day in range(1, 32)])
        self.ui.yearBox.addItems([str(year) for year in range(2024, 1900, -1)])

        # set default avatar
        set_default_avatar(self.ui.profilePixmap)

        # connect upload image
        self.ui.uploadImageButton.clicked.connect(self.upload_image)
        # connect next button
        self.ui.next.clicked.connect(self.handle_personal_register)
        # connect back button if exists
        if hasattr(self.ui, 'back'):
            self.ui.back.clicked.connect(self.back_requested.emit)

    def upload_image(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
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

    def handle_personal_register(self):
        username = self.ui.usernameEdit.text().strip()
        email = self.ui.emailEdit.text().strip()
        birthday_day = int(self.ui.dayBox.currentText())
        birthday_month = self.ui.birthMonthBox.currentIndex() + 1
        birthday_year = int(self.ui.yearBox.currentText())
        birthday_date = datetime.date(birthday_year, birthday_month, birthday_day)

        pixmap = self.ui.profilePixmap.pixmap()
        if pixmap and not pixmap.isNull():
            image = pixmap.toImage()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            blob = buffer.data().data()
            buffer.close()

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        today = datetime.date.today()
        min_birth_date = today.replace(year=today.year - 13)

        if not username:
            show_error(self.ui.next, "Insert username")
            return
        if not email or not re.match(email_regex, email):
            show_error(self.ui.next, "Insert valid email")
            return
        if birthday_date > min_birth_date:
            show_error(self.ui.next, "You must be at least 13 years old to register")
            return

        self.personal_data.emit(username, email, birthday_date, blob if blob else None)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.handle_personal_register()
            return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        draw_background(self, event)
        super().paintEvent(event)