from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPixmap

from app.ui.styles.colors import PRIMARY, CURSOR_COLOR

"""
Provide cursor customization utilities, such as:
- create_custom_cursor: create a small custom cursor pixmap and return a QCursor
- change_cursor_to_red: create and apply a red cursor pixmap for special states
"""

# creates a custom cursor dot that is used troughout the application
def create_custom_cursor():
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
