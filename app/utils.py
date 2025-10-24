from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, QFontDatabase, QFont, QTransform
from PySide6.QtWidgets import QWidget, QLineEdit

from PySide6.QtGui import QFontDatabase, QFont
from typing import Optional

def load_fonts():
    font_db = QFontDatabase()
    
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Regular.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Bold.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Medium.otf")
    font_db.addApplicationFont(":/font/GeneralSans_Complete/Fonts/OTF/GeneralSans-Light.otf")

# get Clash Grotesk font
def get_clash_grotesk(size=10):
    font = QFont("Clash Grotesk")
    font.setPointSize(size)
    return font 

# show error message on button and reset after delay
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
            elif "upload" in btn_name:
                button.setText("Upload Image")
                button.setStyleSheet("background-color: transparent;")
        except RuntimeError:
            return
    QTimer.singleShot(2000, reset)

def password_event_filter(owner: QWidget, watched: QWidget, event: QEvent):
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

    return QWidget.eventFilter(owner, watched, event)

# enter key event filter to handle Enter/Return key presses
def enter_key_event_filter(owner: QWidget, watched: QWidget, event: QEvent):
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
                elif hasattr(owner, 'handle_personal_register'):
                    owner.handle_personal_register()
                return True

    return QWidget.eventFilter(owner, watched, event)

# context menu event filter to disable context menus
def context_menu_event_filter(owner: QWidget, watched: QWidget, event: QEvent):
    if event.type() == QEvent.ContextMenu:
        return True

    return QWidget.eventFilter(owner, watched, event)

# paint event for custom background
def draw_background(widget: QWidget, event: QEvent):
    painter = QPainter(widget)
    pixmap = QPixmap(":/images/graphics/bg.png")
    painter.drawPixmap(widget.rect(), pixmap)
    painter.end()

# convert image in widget to rounded pixmap
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

# resize window to specified dimensions with screen bounds checking
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


# safely replace the current central widget and resize the window
def set_central_widget(main_window, widget, width=None, height=None):
    old_widget = main_window.centralWidget()

    if old_widget and old_widget is not widget:
        old_widget.setParent(None)

    main_window.setCentralWidget(widget)

    if width and height:
        main_window.resize(width, height)

# safely enable/disable a widget if it exists and supports setEnabled()
def set_enabled_safe(widget: Optional[QWidget], enabled: bool = True):
    if widget and hasattr(widget, "setEnabled"):
        try:
            widget.setEnabled(enabled)
        except Exception:
            pass