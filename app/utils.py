from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, QFontDatabase, QFont, QTransform
from PySide6.QtWidgets import QWidget, QLineEdit

from PySide6.QtGui import QFontDatabase, QFont

def load_fonts():
    font_db = QFontDatabase()
    
    font_db.addApplicationFont(":/font/ClashGrotesk_Complete/Fonts/TTF/ClashGrotesk-Variable.ttf")
    
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Regular.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Bold.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Medium.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Light.otf")

def get_clash_grotesk(size=10, weight="regular"):
    font = QFont("Clash Grotesk")
    font.setPointSize(size)
    
    if weight.lower() == "bold":
        font.setBold(True)
    elif weight.lower() == "light":
        font.setWeight(QFont.Weight.Light)
    elif weight.lower() == "medium":
        font.setWeight(QFont.Weight.Medium)
    else:
        font.setWeight(QFont.Weight.Normal)
    
    return font

def show_error(button, message: str):
    button.setEnabled(False)
    button.setStyleSheet("background-color: #9E3F3F;")
    button.setText(message)
    def reset():
        try:
            if button is None:
                return
            btn_name = button.objectName().lower()
            btn_style = ("background-color: #3A9A8F; color: white;")
            button.setEnabled(True)
            if "next" in btn_name:
                button.setText("Let's take next step")
                button.setStyleSheet(btn_style)
            elif "signup" in btn_name:
                button.setText("Finish registration")
                button.setStyleSheet(btn_style)
            elif "signin" in btn_name:
                button.setText("Sign In")
                button.setStyleSheet(btn_style)
        except RuntimeError:
            return
    QTimer.singleShot(2000, reset)

def shared_event_filter(owner: QWidget, watched: QWidget, event: QEvent) -> bool:
    # show password on hover
    if event.type() == QEvent.Enter:
        if isinstance(watched, QLineEdit):
            watched.setEchoMode(QLineEdit.Normal)
        return True
    # hide password when not hovering
    if event.type() == QEvent.Leave:
        if isinstance(watched, QLineEdit):
            watched.setEchoMode(QLineEdit.Password)
        return True
    # key press handling
    if event.type() == QEvent.KeyPress:
        key = event.key()
        if isinstance(watched, QLineEdit):
            if key == Qt.Key_Space:
                return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if hasattr(owner, 'handle_auth_register'):
                owner.handle_auth_register()
            elif hasattr(owner, 'handle_auth_login'):
                owner.handle_auth_login()
            return True
    # disable right-click context menu
    if event.type() == QEvent.ContextMenu:
        return True
    # fallback to default implementation
    try:
        return QWidget.eventFilter(owner, watched, event)
    except Exception:
        return False

def draw_background(widget, event):
    painter = QPainter(widget)
    pixmap = QPixmap(":/images/graphics/bg.png")
    painter.drawPixmap(widget.rect(), pixmap)
    painter.end()

def image_to_rounded(widget):
    original_pixmap = widget.pixmap()
    if not original_pixmap:
        return

    size = min(widget.width(), widget.height(), original_pixmap.width(), original_pixmap.height(), 200)
    scaled_pixmap = original_pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    painter.drawPixmap(0, 0, scaled_pixmap)
    painter.end()

    widget.setPixmap(rounded)

def window_resize(window: QWidget, width: int=1000, height: int=800):
    screen = window.screen()
    if screen:
        screen_size = screen.size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        new_width = min(width, screen_width - 100)
        new_height = min(height, screen_height - 100)

        window.setMinimumSize(0, 0)
        window.resize(new_width, new_height)
        window.setMinimumSize(new_width, new_height)
        window.move((screen_width - new_width) // 2, (screen_height - new_height) // 2)

def set_default_avatar(label_widget):
    size = label_widget.size()
    
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

    label_widget.setPixmap(rounded)
