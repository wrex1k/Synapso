from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class KeyWidget(QWidget):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("keyWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(8, 4, 8, 4)

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("keyLabel")
        layout.addWidget(self.label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)
