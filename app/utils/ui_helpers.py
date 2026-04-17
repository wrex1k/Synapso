from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

def update_button_state(button, state: str, *, idle_text: str, error_text: str | None = None, auto_reset_ms: int | None = 2000, loading_text: str = "Loading…",):
    """Update a button's text, enabled state and style for idle/loading/error states."""
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

def draw_background(widget: QWidget, event):
    """Paint the application background image onto a widget."""
    painter = QPainter(widget)
    pixmap = QPixmap(":/images/graphics/background.png")
    painter.drawPixmap(widget.rect(), pixmap)
    painter.end()


def image_to_rounded(widget: QWidget):
    """Clip the pixmap of a QLabel into a circular shape."""
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
    
def build_header(title: str, subtitle: str):
    """Build a header widget with a title and subtitle label."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    page_title_lbl = QLabel(title)
    page_title_lbl.setObjectName("pageTitleLabel")

    page_subtitle_lbl = QLabel(subtitle)
    page_subtitle_lbl.setObjectName("pageSubtitleLabel")

    layout.addWidget(page_title_lbl)
    layout.addWidget(page_subtitle_lbl)

    return container, page_title_lbl, page_subtitle_lbl