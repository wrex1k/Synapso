from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, Qt
from app.ui.appWidget_ui import Ui_appWidget

class AppWidget(QWidget):
    def __init__(self, username: str):
        super().__init__()

        self.ui = Ui_appWidget()
        self.ui.setupUi(self)

        self.ui.username.setText(username)
        original_pixmap = self.ui.image.pixmap()

        if original_pixmap:
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

            self.ui.image.setPixmap(rounded)
            self.ui.image.setScaledContents(True)
