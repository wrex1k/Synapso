from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QPushButton, QWidget

"""Provide UI helper utilities, such as:
- _get_button_original_text: internal helper to cache the original text of a button
- update_button_state: set button state and text for idle/loading/error
- reset_button: restore a button to its original text and enabled state
- draw_background: draw a custom background image in a widget's paintEvent
- image_to_rounded: convert a widget's pixmap to a rounded avatar-style QPixmap
"""

# internal helper to get and cache the original text of a button for error display
def _get_button_original_text(button: QPushButton) -> str:
    original = button.property("original_text")
    if original is None:
        original = button.text()
        button.setProperty("original_text", original)
    return original

# update button state with predefined styles for idle, loading and error states
def update_button_state(button, state: str, *, idle_text: str, error_text: str | None = None, auto_reset_ms: int | None = 2000, loading_text: str = "Loading…",):
    button.setProperty("state", state)

    if state == "idle":
        button.setEnabled(True)
        button.setText(idle_text)

    elif state == "loading":
        button.setEnabled(False)
        button.setText(loading_text)

    elif state == "error":
        button.setText(error_text or idle_text)
        button.setEnabled(False)

        if auto_reset_ms:
            QTimer.singleShot(auto_reset_ms, lambda: update_button_state(
                button,
                "idle",
                idle_text=idle_text,
                loading_text=loading_text,
                error_text=error_text,
                auto_reset_ms=None,
            ))

    button.style().polish(button)

# reset button to primary state
def reset_button(button: QPushButton):
    original_text = _get_button_original_text(button)
    button.setEnabled(True)
    button.setText(original_text)

# draw a custom background image for a widget in its paintEvent
def draw_background(widget: QWidget, event):
    painter = QPainter(widget)
    pixmap = QPixmap(":/images/graphics/background.png")
    painter.drawPixmap(widget.rect(), pixmap)
    painter.end()


# convert the pixmap of a QLabel to a rounded version, keeping aspect ratio and filling the label
def image_to_rounded(widget: QWidget):
    original_pixmap = widget.pixmap()
    if not original_pixmap:
        return

    size = min(
        widget.width(),
        widget.height(),
        original_pixmap.width(),
        original_pixmap.height(),
        200,
    )
    scaled = original_pixmap.scaled(
        size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
    )

    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    widget.setPixmap(rounded)
