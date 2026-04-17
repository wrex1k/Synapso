from typing import Callable, Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QLineEdit, QWidget

def password_event_filter(owner: QWidget, watched: QWidget, event: QEvent) -> bool:
    """Toggle password visibility on hover enter/leave events."""
    if event.type() == QEvent.Enter:
        if isinstance(watched, QLineEdit):
            watched.setEchoMode(QLineEdit.Normal)
        return True
    if event.type() == QEvent.Leave:
        if isinstance(watched, QLineEdit):
            watched.setEchoMode(QLineEdit.Password)
        return True
    return False

def enter_key_event_filter(
    owner: QWidget,
    watched: QWidget,
    event: QEvent,
    on_enter: Optional[Callable] = None,
) -> bool:
    """Block spaces in line edits and invoke callback on Enter key press."""
    if event.type() == QEvent.KeyPress:
        key = event.key()
        if isinstance(watched, QLineEdit) and key == Qt.Key_Space:
            return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if on_enter is not None:
                on_enter()
            return True
    return False


def context_menu_event_filter(owner: QWidget, watched: QWidget, event: QEvent) -> bool:
    """Suppress the right-click context menu on a widget."""
    if event.type() == QEvent.ContextMenu:
        return True
    return False
