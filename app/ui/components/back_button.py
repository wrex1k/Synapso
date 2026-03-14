from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

class BackButton(QWidget):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("backButtonContainer")
        self.setFixedWidth(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn = QPushButton("←", self)
        self._btn.setObjectName("back")
        self._btn.setFixedSize(QSize(80, 150))
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._btn)

        self._hover_dx = 12
        self._anim: QPropertyAnimation | None = None
        self._fly_anim: QPropertyAnimation | None = None

        self._btn.clicked.connect(self._on_click)
        self._btn.installEventFilter(self)

    def _stop_anims(self):
        for anim in (self._anim, self._fly_anim):
            if anim and anim.state() == QPropertyAnimation.State.Running:
                anim.stop()

    def _animate_geometry(self, end_rect: QRect, duration: int, easing: QEasingCurve.Type):
        self._stop_anims()
        self._anim = QPropertyAnimation(self._btn, b"geometry", self)
        self._anim.setDuration(duration)
        self._anim.setEasingCurve(easing)
        self._anim.setStartValue(self._btn.geometry())
        self._anim.setEndValue(end_rect)
        self._anim.start()

    def eventFilter(self, obj, event):
        if obj is self._btn:
            if event.type() == QEvent.Type.Enter:
                base = self._btn.geometry()
                target = QRect(
                    base.x() + self._hover_dx, base.y(),
                    base.width(), base.height()
                )
                self._animate_geometry(target, 200, QEasingCurve.Type.OutCubic)
                return False

            if event.type() == QEvent.Type.Leave:
                base = self._btn.geometry()
                target = QRect(
                    base.x() - self._hover_dx, base.y(),
                    base.width(), base.height()
                )
                self._animate_geometry(target, 300, QEasingCurve.Type.OutCubic)
                return False

        return super().eventFilter(obj, event)

    def _on_click(self):
        self.clicked.emit()