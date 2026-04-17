from __future__ import annotations

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.registry import registry
from app.utils.logger import logger
from app.ui.styles.colors import CORRECT_COLOR, INCORRECT_COLOR, FONT_PRIMARY, OFF_WHITE, PRIMARY_LIGHT
from app.ui.views.base_game_widget import BaseGameWidget


_SHAPE_CELL = 72
_SHAPE_GAP = 8
_SHAPE_RADIUS = 10
_SHAPE_COLOR = (62, 172, 145)
_SUPERSAMPLE = 3


def _render_shape_pixmap(
    blocks: list[tuple[int, int]],
    rotation: float,
    mirrored: bool,
) -> QPixmap:
    """Render a block shape (rotated, optionally mirrored) via pygame → QPixmap."""
    if not pygame.get_init():
        pygame.init()

    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    cols = max(xs) - min(xs) + 1
    rows = max(ys) - min(ys) + 1
    min_x, min_y = min(xs), min(ys)
    
    s = _SUPERSAMPLE
    cell = _SHAPE_CELL * s
    gap = _SHAPE_GAP * s
    pad = cell
    radius = _SHAPE_RADIUS * s

    surf_w = cols * (cell + gap) - gap + pad * 2
    surf_h = rows * (cell + gap) - gap + pad * 2
    surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

    for bx, by in blocks:
        rx = (bx - min_x) * (cell + gap) + pad
        ry = (by - min_y) * (cell + gap) + pad
        pygame.draw.rect(surf, _SHAPE_COLOR, (rx, ry, cell, cell), border_radius=radius)

    if mirrored:
        surf = pygame.transform.flip(surf, True, False)
    rotated = pygame.transform.rotozoom(surf, -rotation, 1.0)

    final_w = rotated.get_width() // s
    final_h = rotated.get_height() // s
    final = pygame.transform.smoothscale(rotated, (final_w, final_h))

    raw = pygame.image.tostring(final, "RGBA")
    image = QImage(raw, final.get_width(), final.get_height(), QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())

_IDLE = "idle"
_COUNTDOWN = "countdown"
_STIMULUS = "stimulus"
_FEEDBACK = "feedback"
_RESULT = "result"

_FEEDBACK_MS = 800
_RESULT_MS = 1800
_COUNTDOWN_MS = 900

_KEY_MAP = {
    Qt.Key.Key_K: "k",
    Qt.Key.Key_F: "f",
}


class ShapePreview(QLabel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(390, 390)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._blocks: list[tuple[int, int]] = []
        self._rotation: float = 0.0
        self._mirrored: bool = False

    def set_shape(self, blocks: list[tuple[int, int]], rotation: float, mirrored: bool):
        self._blocks = blocks or []
        self._rotation = rotation
        self._mirrored = mirrored
        self._refresh()

    def _refresh(self):
        if not self._blocks:
            self.setPixmap(QPixmap())
            return
        pix = _render_shape_pixmap(self._blocks, self._rotation, self._mirrored)
        self.setPixmap(pix)


class MentalRotationWidget(BaseGameWidget):
    _object_name = "mentalRotationWidget"
    _game_name = "mental-rotation"
    _hud_label_word = "Shape"
    _feedback_font_size = 28
    _correct_color_hex = CORRECT_COLOR

    def _build_ui(self) -> None:
        root = self._build_hud_header("Mental Rotation", margins=(110, 90, 110, 80))
        root.addStretch(1)

        self._lbl_feedback = QLabel("")
        self._lbl_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_feedback.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_feedback.setStyleSheet("background: transparent;")
        root.addWidget(self._lbl_feedback)

        root.addSpacing(16)

        shape_row = QHBoxLayout()
        shape_row.setSpacing(120)
        shape_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._left_shape = ShapePreview()
        self._right_shape = ShapePreview()
        shape_row.addWidget(self._left_shape)
        shape_row.addWidget(self._right_shape)
        root.addLayout(shape_row)

        root.addStretch(1)

        self._build_hud_footer(
            root,
            f'Press the key if the <span style="color:{FONT_PRIMARY};">shapes are the same</span>',
        )

    def _show_countdown(self):
        self._countdown_value = 3
        self._state = _COUNTDOWN
        self._hud_update(show_next_trial=True)
        self._bar_timer.setValue(0)
        self._left_shape.set_shape([], 0.0, False)
        self._right_shape.set_shape([], 0.0, False)
        self._lbl_feedback.setText(
            f'<span style="color:{OFF_WHITE}; font-size:80px; font-weight:700;">{self._countdown_value}</span>'
        )
        self._timer.start(_COUNTDOWN_MS)

    def _begin_trial(self) -> None:
        assert self._game is not None
        if self._check_trial_complete():
            return

        self._trial_params = self._game.start_trial()
        self._stimulus_ms = int(self._trial_params.get("stimulus_duration", 2000))
        self._after_feedback = None

        self._hud_update(show_next_trial=True)
        self._go(_STIMULUS)

    def _go(self, state: str):
        self._state = state
        self._timer.stop()

        if state == _STIMULUS:
            p = self._trial_params
            blocks = p.get("shape_blocks", [])
            angle = float(p.get("rotation_angle", 0))
            mirrored = bool(p.get("mirrored", False))

            self._left_shape.set_shape(blocks, rotation=0.0, mirrored=False)
            self._right_shape.set_shape(blocks, rotation=angle, mirrored=mirrored)

            self._lbl_feedback.setText("")

            self._bar_timer.setValue(1000)
            self._elapsed.start()
            self._tick.start()
            self._timer.start(self._stimulus_ms)

        elif state == _FEEDBACK:
            self._tick.stop()
            self._bar_timer.setValue(0)
            self._timer.start(_FEEDBACK_MS)

        elif state == _RESULT:
            self._lbl_feedback.setText(
                f'<span style="color:{PRIMARY_LIGHT}; font-size:32px; font-weight:700;">Tutorial Complete!</span>'
            )
            self._timer.start(_RESULT_MS)

    def _on_timeout(self) -> None:
        if self._state == _COUNTDOWN:
            self._countdown_value -= 1
            if self._countdown_value > 0:
                self._lbl_feedback.setText(
                    f'<span style="color:{OFF_WHITE}; font-size:80px; font-weight:700;">{self._countdown_value}</span>'
                )
                self._timer.start(_COUNTDOWN_MS)
            else:
                self._lbl_feedback.setText("")
                self._countdown_done = True
                if self._db_ready:
                    self._begin_trial()
            return

        if self._state == _STIMULUS:
            self._tick.stop()
            self._bar_timer.setValue(0)
            self._evaluate(None, float(self._stimulus_ms))
            return

        if self._state == _FEEDBACK:
            if self._mode == "tutorial" and self._runner is not None and getattr(self._runner, "failed", False):
                self._finish_session(completed=False)
                return
            nxt = self._after_feedback
            self._after_feedback = None
            if nxt:
                self._go(nxt)
            else:
                self._begin_trial()
            return

        if self._state == _RESULT:
            self._finish_session(completed=True)

    def keyPressEvent(self, event) -> None:
        if self._state == _STIMULUS and self._trial_params is not None:
            response = _KEY_MAP.get(event.key())
            if response in self._trial_params.get("available_keys", ["f", "j"]):
                self._timer.stop()
                self._tick.stop()
                self._evaluate(response, float(self._elapsed.elapsed()))
                return
        super().keyPressEvent(event)

    def _evaluate(self, response: str | None, reaction_time_ms: float) -> None:
        result = self._game.evaluate_trial(self._trial_params, response, reaction_time_ms)

        color = CORRECT_COLOR if result.is_correct else INCORRECT_COLOR
        symbol = "✓" if result.is_correct else "✗"
        text = "Correct" if result.is_correct else "Incorrect"
        self._lbl_feedback.setText(
            f'<span style="color:{color}; font-size:28px; font-weight:600;">{symbol} {text}</span>'
        )

        self._hud_update(show_next_trial=False)

        if self._mode == "tutorial" and self._runner is not None:
            if self._runner.check_after_trial():
                if self._service:
                    _svc = self._service
                    _runner = self._runner

                    def _save_tutorial(svc=_svc):
                        svc.start_run(stage="tutorial", initialize_game=False)

                    self._keep_thread(registry.run_thread(_save_tutorial, lambda _: None))
                self._after_feedback = _RESULT

        self._go(_FEEDBACK)


