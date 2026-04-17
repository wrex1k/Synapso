from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget,
)

from app.ui.styles.colors import FONT_PRIMARY
from app.utils.ui_helpers import draw_background
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseTutorialWidget(QWidget):

    session_done = Signal(bool)
    start_game_tutorial_requested = Signal()

    def __init__(self, parent: QWidget | None = None, allow_gameplay_tutorial: bool = True):
        super().__init__(parent)
        self.setObjectName("stroopTutorialIntroWidget")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._allow_gameplay_tutorial = allow_gameplay_tutorial
        self._tutorial_steps: list[dict] = self._get_tutorial_steps()
        self._tutorial_index = 0
        self._build_ui()

    def _get_tutorial_steps(self) -> list[dict]:
        raise NotImplementedError

    def _get_intro_title(self) -> str:
        raise NotImplementedError

    def _get_intro_subtitle(self) -> str:
        raise NotImplementedError

    def _get_card_intro_html(self) -> str:
        raise NotImplementedError

    def _build_card_bullets(self, layout: QVBoxLayout) -> None:
        raise NotImplementedError

    def _get_practice_subtitle_html(self) -> str:
        raise NotImplementedError

    def _build_example_page(self, step: dict) -> QWidget:
        raise NotImplementedError

    def _get_tip_text(self) -> str:
        return "Don't worry \u2013 a brief tutorial will guide you before starting."

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        self._main_stack = QStackedWidget()
        self._main_stack.setObjectName("tutorialMainStack")
        self._main_stack.addWidget(self._build_intro_tutorial_page())
        self._main_stack.addWidget(self._build_practice_tutorial_page())
        root.addWidget(self._main_stack)

    def _build_intro_tutorial_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addStretch(1)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        title = QLabel(self._get_intro_title())
        title.setObjectName("stroopTutorialTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        center_layout.addWidget(title)

        center_layout.addSpacing(15)

        subtitle = QLabel(self._get_intro_subtitle())
        subtitle.setObjectName("stroopTutorialSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        center_layout.addWidget(subtitle)

        center_layout.addSpacing(40)

        card = QWidget()
        card.setObjectName("stroopTutorialCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        card.setMinimumWidth(1000)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(50, 45, 0, 30)
        card_layout.setSpacing(10)

        icon = QLabel()
        pix = QPixmap(":/images/icons/info-tutorial.png")
        if not pix.isNull():
            icon.setPixmap(
                pix.scaled(
                    24,
                    24,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        icon.setObjectName("stroopTutorialIcon")
        card_layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(20)

        intro = QLabel(self._get_card_intro_html())
        intro.setObjectName("stroopTutorialIntro")
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setWordWrap(True)
        text_col.addWidget(intro)

        how = QLabel("How to play")
        how.setObjectName("stroopTutorialHow")
        text_col.addWidget(how)

        bullets_wrap = QWidget()
        bullets_layout = QVBoxLayout(bullets_wrap)
        bullets_layout.setContentsMargins(0, 0, 0, 0)
        bullets_layout.setSpacing(8)

        self._build_card_bullets(bullets_layout)

        text_col.addWidget(bullets_wrap)

        text_col.addSpacing(16)

        tip = QLabel(self._get_tip_text())
        tip.setObjectName("stroopTutorialTip")
        tip.setTextFormat(Qt.TextFormat.RichText)
        tip.setWordWrap(True)
        text_col.addWidget(tip)

        card_layout.addLayout(text_col, 1)
        center_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)

        center_layout.addSpacing(30)

        start_btn = QPushButton("Practice Tutorial")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setFixedSize(182, 48)
        start_btn.setObjectName("transparentButton")
        start_btn.clicked.connect(self._show_tutorial_page)
        center_layout.addWidget(start_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        root.addWidget(center, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)
        return page

    def _build_practice_tutorial_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("practiceTutorial")

        root = QHBoxLayout(page)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setObjectName("tutorialCard")

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(30)
        card_layout.setContentsMargins(40, 50, 40, 40)

        top_wrap = QVBoxLayout()
        top_wrap.setSpacing(40)

        header = QVBoxLayout()
        header.setSpacing(4)

        self._step_title = QLabel("Practice Tutorial")
        self._step_title.setObjectName("practiceTutorialTitle")
        header.addWidget(self._step_title)

        self._step_counter = QLabel("")
        self._step_counter.setObjectName("practiceTutorialStep")
        header.addWidget(self._step_counter)
        top_wrap.addLayout(header)

        subtitle = QLabel(self._get_practice_subtitle_html())
        subtitle.setObjectName("practiceTutorialAdvice")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setTextFormat(Qt.TextFormat.RichText)
        top_wrap.addWidget(subtitle)
        card_layout.addLayout(top_wrap)

        middle_wrap = QVBoxLayout()
        middle_wrap.setSpacing(5)
        middle_wrap.setContentsMargins(60, 0, 60, 0)

        self._example_stack = QStackedWidget()
        self._example_stack.setObjectName("practiceTutorialPages")
        for step in self._tutorial_steps:
            self._example_stack.addWidget(self._build_example_page(step))
        middle_wrap.addWidget(self._example_stack)

        dots_wrap = QWidget()
        dots_wrap_row = QHBoxLayout(dots_wrap)
        dots_wrap_row.setSpacing(0)
        dots_wrap_row.setContentsMargins(0, 0, 0, 0)

        self._dots: list[QPushButton] = []
        dots_row = QHBoxLayout()
        dots_row.setSpacing(5)
        dots_row.setContentsMargins(240, 30, 240, 0)
        for _ in self._tutorial_steps:
            dot = QPushButton("")
            dot.setObjectName("tutorialDot")
            dot.setProperty("active", False)
            dot.setEnabled(False)
            dot.setFixedSize(8, 8)
            self._dots.append(dot)
            dots_row.addWidget(dot)
        dots_wrap_row.addLayout(dots_row)
        middle_wrap.addWidget(dots_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        card_layout.addLayout(middle_wrap)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)

        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("practiceTutorialButton")
        self._next_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._next_btn.clicked.connect(self._on_tutorial_next)

        bottom_row.addStretch(1)
        bottom_row.addWidget(self._next_btn)
        card_layout.addLayout(bottom_row)

        root.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        self._update_tutorial_state()
        return page

    def _show_tutorial_page(self):
        self._tutorial_index = 0
        self._update_tutorial_state()
        self._main_stack.setCurrentIndex(1)

    def _update_tutorial_state(self):
        total = len(self._tutorial_steps)
        self._example_stack.setCurrentIndex(self._tutorial_index)
        self._step_counter.setText(f"Step {self._tutorial_index + 1} of {total}")
        is_last = self._tutorial_index == (total - 1)
        if is_last:
            self._next_btn.setText("Start" if self._allow_gameplay_tutorial else "Back")
        else:
            self._next_btn.setText("Next")

        for idx, dot in enumerate(self._dots):
            if idx == self._tutorial_index:
                dot.setFixedSize(30, 8)
                dot.setProperty("active", True)
            else:
                dot.setFixedSize(8, 8)
                dot.setProperty("active", False)
            dot.style().unpolish(dot)
            dot.style().polish(dot)
            dot.update()

    def _on_tutorial_next(self):
        if self._tutorial_index < len(self._tutorial_steps) - 1:
            self._tutorial_index += 1
            self._update_tutorial_state()
            return

        if self._allow_gameplay_tutorial:
            self.start_game_tutorial_requested.emit()
            return

        self.session_done.emit(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.session_done.emit(False)
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        draw_background(self, event)
