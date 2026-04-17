from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget, QProgressBar
import re

from app.utils.logger import get_logger
logger = get_logger(__name__)


class InputField(QWidget):
    def __init__(
        self,
        label_text: str,
        placeholder: str = "",
        *,
        is_password: bool = False,
        object_name: str = "",
        min_width: int = 500,
        max_width: int | None = None,
        parent=None,
        password_strength: bool = False,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if min_width is not None:
            self.setMinimumWidth(min_width)
        if max_width is not None:
            self.setMaximumWidth(max_width)

        field_layout = QVBoxLayout(self)
        field_layout.setSpacing(9)
        field_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text, self)
        self.label.setObjectName("inputLabel")

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("inputEdit")
        self.line_edit.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        if placeholder:
            self.line_edit.setPlaceholderText(placeholder)

        if is_password:
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.password_strength = password_strength
        if self.password_strength:
            self.progressBar = QProgressBar(self)
            self.progressBar.setObjectName("progressBar")
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
            self.progressBar.setTextVisible(False)
            self.line_edit.textChanged.connect(self._on_password_changed)

        field_layout.addWidget(self.label)
        field_layout.addWidget(self.line_edit)

        if self.password_strength:
            field_layout.addWidget(self.progressBar)

    def text(self) -> str:
        return self.line_edit.text()
    
    def setTitle(self, text: str) -> None:
        self.label.setText(text)

    def setText(self, text: str) -> None:
        self.line_edit.setText(text)

    def setPlaceholderText(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)
    
    def clear(self) -> None:
        self.line_edit.clear()
    
    def setFocus(self) -> None:
        self.line_edit.setFocus()
    
    def installEventFilter(self, filter) -> None:
        self.line_edit.installEventFilter(filter)

    def _on_password_changed(self, text: str) -> None:
        score = self._evaluate_password_strength(text)
        self.progressBar.setValue(score)

        strength = "weak" if score < 34 else "mid" if score < 67 else "strong"

        self.progressBar.setProperty("strength", strength)
        self.progressBar.style().polish(self.progressBar)
        
    def _evaluate_password_strength(self, password: str) -> int:
        score = 0

        if len(re.sub(r'[^a-zA-Z0-9]', '', password)) >= 8:
            score += 1
        if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1

        return int((score / 3) * 100)