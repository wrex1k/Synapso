from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget)

from app.ui.components.key_widget import KeyWidget
from app.ui.styles.colors import FONT_PRIMARY
from app.ui.views.base_tutorial import BaseTutorialWidget
from app.games.stroop.config import COLOR_MAP
from app.utils.logger import get_logger
from translations.translation import translate

logger = get_logger(__name__)


class StroopTutorial(BaseTutorialWidget):

    def _get_tutorial_steps(self) -> list[dict]:
        return [
            {
                "word": "RED",
                "word_color": f"rgb{COLOR_MAP['red']}",
                "answer_key": "R",
                "answer_text": "RED",
                "answer_color": f"rgb{COLOR_MAP['red']}",
            },
            {
                "word": "CLOUD",
                "word_color": f"rgb{COLOR_MAP['blue']}",
                "answer_key": "B",
                "answer_text": "BLUE",
                "answer_color": f"rgb{COLOR_MAP['blue']}",
            },
            {
                "word": "ORANGE",
                "word_color": f"rgb{COLOR_MAP['yellow']}",
                "answer_key": "Y",
                "answer_text": "yellow",
                "answer_color": f"rgb{COLOR_MAP['yellow']}",
            },
        ]

    def _get_intro_title(self) -> str:
        return translate("StroopTutorial", "Stroop color and word test")

    def _get_intro_subtitle(self) -> str:
        return translate("StroopTutorial", "Train your cognitive control and selective attention")

    def _get_card_intro_html(self) -> str:
        return translate(
            "StroopTutorial",
            'Match the <span style="color:{color};">ink color</span> of each word, '
            'not what the word says.<br>'
            'React as <span style="color:{color};">quickly</span> and '
            '<span style="color:{color};">accurately</span> as possible.',
        ).format(color=FONT_PRIMARY)

    def _build_card_bullets(self, bullets_layout: QVBoxLayout) -> None:
        controls_row = QWidget()
        controls_row_layout = QHBoxLayout(controls_row)
        controls_row_layout.setContentsMargins(0, 0, 0, 0)
        controls_row_layout.setSpacing(6)


        controls_row_colors = QWidget()
        controls_row_colors_layout = QHBoxLayout(controls_row_colors)
        controls_row_colors_layout.setContentsMargins(0, 0, 0, 0)
        controls_row_colors_layout.setSpacing(6)

        bullet_press = QLabel(translate("StroopTutorial", "• Press"))
        bullet_press.setObjectName("tutorialBaseText")
        controls_row_colors_layout.addWidget(bullet_press)

        key_r = KeyWidget("R")
        key_r.setProperty("compact", True)
        controls_row_colors_layout.addWidget(key_r)

        for_red = QLabel(translate("StroopTutorial", "for RED,"))
        for_red.setObjectName("tutorialBaseText")
        controls_row_colors_layout.addWidget(for_red)

        key_g = KeyWidget("G")
        key_g.setProperty("compact", True)
        controls_row_colors_layout.addWidget(key_g)

        for_green = QLabel(translate("StroopTutorial", "for GREEN,"))
        for_green.setObjectName("tutorialBaseText")
        controls_row_colors_layout.addWidget(for_green)

        key_b2 = KeyWidget("B")
        key_b2.setProperty("compact", True)
        controls_row_colors_layout.addWidget(key_b2)

        for_blue = QLabel(translate("StroopTutorial", "for BLUE."))
        for_blue.setObjectName("tutorialBaseText")
        controls_row_colors_layout.addWidget(for_blue)
        controls_row_colors_layout.addStretch(1)

        bullets_layout.addWidget(controls_row_colors)
        bullet_press_2 = QLabel(translate("StroopTutorial", "• Press"))
        bullet_press_2.setObjectName("tutorialBaseText")
        controls_row_layout.addWidget(bullet_press_2)

        key_y = KeyWidget("Y")
        key_y.setProperty("compact", True)
        controls_row_layout.addWidget(key_y)

        for_yellow = QLabel(translate("StroopTutorial", "for YELLOW,"))
        for_yellow.setObjectName("tutorialBaseText")
        controls_row_layout.addWidget(for_yellow)

        key_o = KeyWidget("O")
        key_o.setProperty("compact", True)
        controls_row_layout.addWidget(key_o)

        for_orange = QLabel(translate("StroopTutorial", "for ORANGE,"))
        for_orange.setObjectName("tutorialBaseText")
        controls_row_layout.addWidget(for_orange)

        key_p = KeyWidget("P")
        key_p.setProperty("compact", True)
        controls_row_layout.addWidget(key_p)

        for_purple = QLabel(translate("StroopTutorial", "for PURPLE."))
        for_purple.setObjectName("tutorialBaseText")
        controls_row_layout.addWidget(for_purple)
        controls_row_layout.addStretch(1)

        bullets_layout.addWidget(controls_row)

        bullet_difficulty = QLabel(
            translate(
                "StroopTutorial",
                '• Each response calculates difficulty'
                '<span style="color:{color};"> - response correct!</span>',
            ).format(color=FONT_PRIMARY)
        )
        bullet_difficulty.setTextFormat(Qt.TextFormat.RichText)
        bullet_difficulty.setObjectName("tutorialBaseText")
        bullet_difficulty.setWordWrap(True)
        bullets_layout.addWidget(bullet_difficulty)

        bullet_trials = QLabel(
            translate(
                "StroopTutorial",
                '• Complete <span style="color:#3EAC91;">20 trials</span> to finish the run.',
            )
        )
        bullet_trials.setTextFormat(Qt.TextFormat.RichText)
        bullet_trials.setObjectName("tutorialBaseText")
        bullet_trials.setWordWrap(True)
        bullets_layout.addWidget(bullet_trials)

    def _get_practice_subtitle_html(self) -> str:
        return translate(
            "StroopTutorial",
            'Let\'s learn how the <span style="color:#3EAC91;">Stroop</span> test works. This will only take a minute!',
        )

    def _build_example_page(self, step: dict[str, str]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 60, 30, 60)
        layout.addStretch(0)

        word_label = QLabel(step["word"])
        word_label.setObjectName("practiceTutorialStimul")
        word_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        word_label.setStyleSheet(
            f"color: {step['word_color']};"
            "background: transparent;"
        )
        layout.addWidget(word_label, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        answer_wrap = QWidget()
        answer_wrap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row = QHBoxLayout(answer_wrap)
        answer_row.setSpacing(10)
        answer_row.setContentsMargins(150, 0, 150, 0)

        answer_label = QLabel(translate("StroopTutorial", "Correct answer:"))
        answer_label.setObjectName("practiceTutorialAnswerLabel")
        answer_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        answer_row.addWidget(answer_label, 0, Qt.AlignmentFlag.AlignHCenter)

        if step["answer_key"]:
            key_wrap = KeyWidget(step["answer_key"])
            key_wrap.setProperty("compact", True)
            answer_row.addWidget(key_wrap, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

            answer_text = QLabel(f"({step['answer_text']})")
            answer_text.setObjectName("practiceTutorialAnswerText")
            answer_text.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            answer_text.setStyleSheet(
                f"color: {step['answer_color']};"
                "background: transparent;"
            )
            answer_row.addWidget(answer_text, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        else:
            answer_text = QLabel(step["answer_text"])
            answer_text.setObjectName("practiceTutorialAnswerText")
            answer_text.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            answer_text.setStyleSheet(
                f"color: {step['answer_color']};"
                "background: transparent;"
            )
            answer_row.addWidget(answer_text, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(answer_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        return page
