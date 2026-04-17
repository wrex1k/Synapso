import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainterPath, QRegion

from app.utils.cursor import create_custom_cursor

"""
This module provides a mixin class for creating frameless windows with custom
drag and resize behavior.

Features:
- rounded corners via setMask
- dragging the window
- resizing from window corners
- custom cursor on resize zones
- proper minimum size clamping
- live rounded-corner updates during resize with throttling
"""


class FramelessWindowMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._drag_pos = None
        self._resizing = False
        self._resize_direction = None
        self._corner_radius = 20
        self._resize_margin = 15
        self._start_geometry = None
        self._red_cursor = create_custom_cursor()
        self._cursor_active = False

        self._last_mask_update = 0.0
        self._mask_update_interval = 1 / 60

        self.setMouseTracking(True)

    def set_corner_radius(self, radius: int):
        self._corner_radius = radius
        self._apply_rounded_corners(force=True)

    def _raw_apply_rounded_corners(self):
        if self.isMaximized() or self.isFullScreen():
            self.clearMask()
            return

        if self.width() <= 0 or self.height() <= 0:
            return

        path = QPainterPath()
        path.addRoundedRect(
            QRect(0, 0, self.width(), self.height()),
            self._corner_radius,
            self._corner_radius,
        )
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _apply_rounded_corners(self, force: bool = False):
        now = time.monotonic()

        if force or (now - self._last_mask_update) >= self._mask_update_interval:
            self._raw_apply_rounded_corners()
            self._last_mask_update = now

    def _is_in_corner(self, pos: QPoint) -> str | None:
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
        self._apply_rounded_corners(force=True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            corner = self._is_in_corner(event.pos())

            if corner:
                self._resizing = True
                self._resize_direction = corner
                self._drag_pos = event.globalPosition().toPoint()
                self._start_geometry = self.geometry()
                event.accept()
                return

            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
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

                min_w = self.minimumWidth()
                min_h = self.minimumHeight()

                if rect.width() < min_w:
                    if "left" in self._resize_direction:
                        rect.setLeft(rect.right() - min_w + 1)
                    else:
                        rect.setWidth(min_w)

                if rect.height() < min_h:
                    if "top" in self._resize_direction:
                        rect.setTop(rect.bottom() - min_h + 1)
                    else:
                        rect.setHeight(min_h)

                self._update_cursor(True)
                self.setGeometry(rect)
                self._apply_rounded_corners()
                event.accept()
                return

            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return

        corner = self._is_in_corner(event.pos())
        self._update_cursor(corner is not None)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            self._resizing = False
            self._resize_direction = None

            self._update_cursor(False)
            self._apply_rounded_corners(force=True)

            event.accept()
            return

        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self._update_cursor(False)
        super().leaveEvent(event)