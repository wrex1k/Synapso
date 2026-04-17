from __future__ import annotations

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget)

from app.ui.styles.colors import FONT_PRIMARY
from app.ui.views.base_tutorial import BaseTutorialWidget
from app.utils.logger import get_logger
logger = get_logger(__name__)
from translations.translation import translate


_CELL_OFF = (169, 169, 169)
_CELL_ON = (62, 172, 145)
_CELL_RADIUS = 8
_CELL_GAP = 8


def _render_tutorial_grid(grid_size: int, highlight: set[int], cell_size: int = 50) -> QPixmap:
    """Render a small grid pixmap for the tutorial practice page."""
    total = grid_size * cell_size + (grid_size - 1) * _CELL_GAP
    surf = pygame.Surface((total, total), pygame.SRCALPHA)

    for row in range(grid_size):
        for col in range(grid_size):
            idx = row * grid_size + col
            x = col * (cell_size + _CELL_GAP)
            y = row * (cell_size + _CELL_GAP)
            color = _CELL_ON if idx in highlight else _CELL_OFF
            pygame.draw.rect(surf, color, (x, y, cell_size, cell_size), border_radius=_CELL_RADIUS)

    raw = pygame.image.tostring(surf, "RGBA")
    image = QImage(raw, surf.get_width(), surf.get_height(), QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())

class MemoryGridTutorial(BaseTutorialWidget):

    def _get_tutorial_steps(self) -> list[dict]:
        return [
            {
                "grid_size": 3,
                "highlight": {1, 2, 5},
                "cell_count": 3,
                "description": translate("MemoryGridTutorial", "Memorize the highlighted pattern!"),
            },
            {
                "grid_size": 3,
                "highlight": {1, 2},
                "cell_count": 2,
                "description": translate("MemoryGridTutorial", "Reproduce the pattern you memorized!"),
            },
        ]

    def _get_intro_title(self) -> str:
        return translate("MemoryGridTutorial", "Memory Grid")

    def _get_intro_subtitle(self) -> str:
        return translate("MemoryGridTutorial", "Train your spatial working memory and pattern recognition")

    def _get_card_intro_html(self) -> str:
        return translate(
            "MemoryGridTutorial",
            'Memorize the <span style="color:{color};">highlighted tiles</span> '
            'and <span style="color:{color};">reproduce the pattern</span>.<br>'
            'React as <span style="color:{color};">quickly</span> and '
            '<span style="color:{color};">accurately</span> as possible.',
        ).format(color=FONT_PRIMARY)

    def _build_card_bullets(self, bullets_layout: QVBoxLayout) -> None:
        b1 = QLabel(translate("MemoryGridTutorial", "• Memorize the highlighted tiles."))
        b1.setTextFormat(Qt.TextFormat.RichText)
        b1.setObjectName("tutorialBaseText")
        b1.setWordWrap(True)
        bullets_layout.addWidget(b1)

        b2 = QLabel(translate("MemoryGridTutorial", "• Click on the grid cells to select the ones you remember."))
        b2.setTextFormat(Qt.TextFormat.RichText)
        b2.setObjectName("tutorialBaseText")
        b2.setWordWrap(True)
        bullets_layout.addWidget(b2)

        b3 = QLabel(
            translate(
                "MemoryGridTutorial",
                '• Each response calculates difficulty'
                '<span style="color:{color};"> - response correct!</span>',
            ).format(color=FONT_PRIMARY)
        )
        b3.setTextFormat(Qt.TextFormat.RichText)
        b3.setObjectName("tutorialBaseText")
        b3.setWordWrap(True)
        bullets_layout.addWidget(b3)

        b4 = QLabel(
            translate(
                "MemoryGridTutorial",
                '• Complete <span style="color:#3EAC91;">20 grids</span> to finish the run.',
            )
        )
        b4.setTextFormat(Qt.TextFormat.RichText)
        b4.setObjectName("tutorialBaseText")
        b4.setWordWrap(True)
        bullets_layout.addWidget(b4)

    def _get_practice_subtitle_html(self) -> str:
        return translate(
            "MemoryGridTutorial",
            'Let\'s learn how the <span style="color:#3EAC91;">Memory Grid</span> works. Memorize the pattern!',
        )

    def _build_example_page(self, step: dict) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.addStretch(0)

        # Grid pixmap
        grid_label = QLabel()
        grid_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        pix = _render_tutorial_grid(step["grid_size"], step["highlight"])
        grid_label.setPixmap(pix)
        layout.addWidget(grid_label, 0, Qt.AlignmentFlag.AlignHCenter)

        # Answer row
        answer_wrap = QWidget()
        answer_wrap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row = QHBoxLayout(answer_wrap)
        answer_row.setSpacing(10)
        answer_row.setContentsMargins(100, 0, 100, 0)

        answer_label = QLabel()
        answer_label.setText(step["description"])
        answer_label.setObjectName("practiceTutorialAnswerLabel")
        answer_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row.addWidget(answer_label, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addWidget(answer_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        return page
