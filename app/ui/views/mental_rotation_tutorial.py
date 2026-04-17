from __future__ import annotations

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget)

from app.ui.components.key_widget import KeyWidget
from app.ui.styles.colors import FONT_PRIMARY
from app.ui.views.base_tutorial import BaseTutorialWidget
from app.games.mental_rotation.config import SHAPES
from app.utils.logger import get_logger
logger = get_logger(__name__)
from translations.translation import translate


_BLOCK_COLOR = (62, 172, 145)
_CELL = 38
_GAP = 4
_RADIUS = 6
_SUPERSAMPLE = 3


def _render_shape(blocks: list[tuple[int, int]], rotation: float, mirrored: bool) -> QPixmap:
    """Render a single block shape (rotated, optionally mirrored) for the tutorial."""
    if not pygame.get_init():
        pygame.init()

    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    cols = max(xs) - min(xs) + 1
    rows = max(ys) - min(ys) + 1
    min_x, min_y = min(xs), min(ys)

    s = _SUPERSAMPLE
    cell = _CELL * s
    gap = _GAP * s
    pad = cell
    radius = _RADIUS * s

    surf_w = cols * (cell + gap) - gap + pad * 2
    surf_h = rows * (cell + gap) - gap + pad * 2
    surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

    for bx, by in blocks:
        rx = (bx - min_x) * (cell + gap) + pad
        ry = (by - min_y) * (cell + gap) + pad
        pygame.draw.rect(surf, _BLOCK_COLOR, (rx, ry, cell, cell), border_radius=radius)

    if mirrored:
        surf = pygame.transform.flip(surf, True, False)
    rotated = pygame.transform.rotozoom(surf, -rotation, 1.0)

    final_w = rotated.get_width() // s
    final_h = rotated.get_height() // s
    final = pygame.transform.smoothscale(rotated, (final_w, final_h))

    raw = pygame.image.tostring(final, "RGBA")
    image = QImage(raw, final.get_width(), final.get_height(), QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())

class MentalRotationTutorial(BaseTutorialWidget):

    def _get_tutorial_steps(self) -> list[dict]:
        return [
            {
                "shape_id": "T2",
                "rotation": 30,
                "mirrored": False,
                "answer_key": "K",
                "answer_text": translate("MentalRotationTutorial", "(same)"),
            },
            {
                "shape_id": "T2",
                "rotation": 45,
                "mirrored": True,
                "answer_key": "F",
                "answer_text": translate("MentalRotationTutorial", "(mirrored)"),
            },
        ]

    def _get_intro_title(self) -> str:
        return translate("MentalRotationTutorial", "Mental Rotation")

    def _get_intro_subtitle(self) -> str:
        return translate("MentalRotationTutorial", "Train your spatial reasoning and mental transformation skills")

    def _get_card_intro_html(self) -> str:
        return translate(
            "MentalRotationTutorial",
            'Compare the <span style="color:{color};">shapes</span> and decide if they are the '
            '<span style="color:{color};">same</span> or '
            '<span style="color:{color};">mirrored</span>.<br>'
            '<span style="color:{color};">Rotate</span> them mentally to find out.',
        ).format(color=FONT_PRIMARY)

    def _build_card_bullets(self, bullets_layout: QVBoxLayout) -> None:
        b1 = QLabel(translate("MentalRotationTutorial", "• Two shapes appear - the original and a rotated or mirrored version."))
        b1.setObjectName("tutorialBaseText")
        b1.setWordWrap(True)
        bullets_layout.addWidget(b1)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        lbl_press = QLabel(translate("MentalRotationTutorial", "• Press"))
        lbl_press.setObjectName("tutorialBaseText")
        row_layout.addWidget(lbl_press)

        key_k = KeyWidget("K")
        key_k.setProperty("compact", True)
        row_layout.addWidget(key_k)

        lbl_same = QLabel(translate("MentalRotationTutorial", "if the shapes are same,"))
        lbl_same.setObjectName("tutorialBaseText")
        row_layout.addWidget(lbl_same)

        key_f = KeyWidget("F")
        key_f.setProperty("compact", True)
        row_layout.addWidget(key_f)

        lbl_diff = QLabel(translate("MentalRotationTutorial", "if one is mirrored."))
        lbl_diff.setObjectName("tutorialBaseText")
        row_layout.addWidget(lbl_diff)
        row_layout.addStretch(1)

        bullets_layout.addWidget(row)

        b3 = QLabel(
            translate(
                "MentalRotationTutorial",
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
                "MentalRotationTutorial",
                '• Complete <span style="color:#3EAC91;">20 shapes</span> to finish the run.',
            )
        )
        b4.setTextFormat(Qt.TextFormat.RichText)
        b4.setObjectName("tutorialBaseText")
        b4.setWordWrap(True)
        bullets_layout.addWidget(b4)

    def _get_practice_subtitle_html(self) -> str:
        return translate(
            "MentalRotationTutorial",
            'Let\'s learn how the <span style="color:#3EAC91;">Mental Rotation</span> works. Compare both shapes!',
        )

    def _build_example_page(self, step: dict) -> QWidget:
        blocks = SHAPES[step["shape_id"]]
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 30, 30, 30)

        # Two shapes side-by-side
        shapes_row = QHBoxLayout()
        shapes_row.setSpacing(40)
        shapes_row.setContentsMargins(0, 0, 0, 0)

        # Original shape (no rotation)
        original_lbl = QLabel()
        original_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        original_lbl.setPixmap(_render_shape(blocks, 0, False))
        shapes_row.addWidget(original_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        # Transformed shape (rotated and possibly mirrored)
        transformed_lbl = QLabel()
        transformed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        transformed_lbl.setPixmap(_render_shape(blocks, step["rotation"], step["mirrored"]))
        shapes_row.addWidget(transformed_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(shapes_row)

        # Answer row
        answer_wrap = QWidget()
        answer_wrap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row = QHBoxLayout(answer_wrap)
        answer_row.setSpacing(10)
        answer_row.setContentsMargins(100, 0, 100, 0)

        answer_label = QLabel(translate("MentalRotationTutorial", "Correct answer:"))
        answer_label.setObjectName("practiceTutorialAnswerLabel")
        answer_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row.addWidget(answer_label, 0, Qt.AlignmentFlag.AlignHCenter)

        key_widget = KeyWidget(step["answer_key"])
        key_widget.setProperty("compact", True)
        answer_row.addWidget(key_widget, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        answer_text = QLabel(step["answer_text"])
        answer_text.setObjectName("practiceTutorialAnswerText")
        answer_text.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_text.setStyleSheet(f"color: #B5B5B5; background: transparent;")
        answer_row.addWidget(answer_text, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(answer_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        return page
