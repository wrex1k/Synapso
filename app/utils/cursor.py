from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPixmap

from app.ui.styles.colors import PRIMARY, CURSOR_COLOR

def create_custom_cursor():
    """Create a custom circular cursor used throughout the application."""
    cursor_size = 16
    pixmap = QPixmap(cursor_size, cursor_size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(CURSOR_COLOR))
    painter.setPen(QColor(PRIMARY))
    
    dot_radius = 5
    center = cursor_size // 2
    painter.drawEllipse(center - dot_radius, center - dot_radius, 
                       dot_radius * 2, dot_radius * 2)
    painter.end()
    
    return QCursor(pixmap, center, center)
