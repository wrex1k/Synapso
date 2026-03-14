from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainterPath, QRegion

from app.utils.cursor import create_custom_cursor

"""
This module provides a mixin class for creating frameless windows with custom drag and resize behavior:
- set_corner_radius: allows setting the corner radius for rounded corners,
- _apply_rounder_corners: applies the rounded corner mask to the window,
- _is_in_corner: checks if the mouse is in a corner area for resizing,
- _update_cursor: changes the cursor when hovering over corners,
- mousePressEvent, mouseMoveEvent, mouseReleaseEvent: handle dragging and resizing logic,
- resizeEvent and showEvent: ensure rounded corners are applied when the window is resized or shown
"""

class FramelessWindowMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_pos = None
        self._resizing = False
        self._corner_radius = 20
        self._resize_margin = 15
        self._start_geometry = None
        self._red_cursor = create_custom_cursor()
        self._cursor_active = False
        
        self.setMouseTracking(True)
    
    def set_corner_radius(self, radius: int):
        self._corner_radius = radius
        self._apply_rounded_corners()
    
    def _apply_rounded_corners(self):
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, self.width(), self.height()), 
                          self._corner_radius, self._corner_radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
    
    def _is_in_corner(self, pos: QPoint) -> str:
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = self._resize_margin
        
        if x < m and y < m:
            return "top-left"
        elif x > w - m and y < m:
            return "top-right"
        elif x < m and y > h - m:
            return "bottom-left"
        elif x > w - m and y > h - m:
            return "bottom-right"
        
        return None
    
    def _update_cursor(self, in_corner: bool):
        
        if in_corner:
            if not self._cursor_active:
                QApplication.setOverrideCursor(self._red_cursor)
                self._cursor_active = True
        else:
            if self._cursor_active:
                QApplication.restoreOverrideCursor()
                self._cursor_active = False
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_corners()
    
    def showEvent(self, event):
        super().showEvent(event)
        self._apply_rounded_corners()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            corner = self._is_in_corner(event.pos())
            
            if corner:
                self._resizing = True
                self._resize_direction = corner
                self._drag_pos = event.globalPosition().toPoint()
                self._start_geometry = self.geometry()
                event.accept()
            else:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            if self._resizing:
                global_pos = event.globalPosition().toPoint()
                delta = global_pos - self._drag_pos
                rect = QRect(self._start_geometry)
                
                if "left" in self._resize_direction:
                    rect.setLeft(rect.left() + delta.x())
                if "right" in self._resize_direction:
                    rect.setRight(rect.right() + delta.x())
                if "top" in self._resize_direction:
                    rect.setTop(rect.top() + delta.y())
                if "bottom" in self._resize_direction:
                    rect.setBottom(rect.bottom() + delta.y())

                self._update_cursor(True)
                
                if rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight():
                    self.setGeometry(rect)
                
                event.accept()
            else:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        else:
            corner = self._is_in_corner(event.pos())
            self._update_cursor(corner is not None)
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            if self._resizing:
                self._resizing = False
                self._resize_direction = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        self._update_cursor(False)
        super().leaveEvent(event)
