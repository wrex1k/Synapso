from __future__ import annotations

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel

from app.core.registry import registry
from app.utils.logger import get_logger
logger = get_logger(__name__)
from app.ui.styles.colors import *
from app.ui.styles.games import get_memory_grid_counter_style, get_memory_grid_phase_style, format_ratio_counter
from app.ui.views.base_game_widget import BaseGameWidget
from translations.translation import translate



_GRID_CELL_OFF = (169, 169, 169)
_GRID_CELL_ON = (62, 172, 145)
_GRID_CELL_SELECTED = (75, 166, 144)
_GRID_CELL_WRONG = (240, 66, 66)
_GRID_CELL_RADIUS = 12
_GRID_GAP = 8


def _render_grid_pixmap(
    grid_size: int,
    highlight: set[int],
    selected: set[int],
    wrong: set[int],
    cell_size: int = 42,
) -> QPixmap:
    """Render the full grid via pygame Surface → QPixmap."""
    if not pygame.get_init():
        pygame.init()

    total = grid_size * cell_size + (grid_size - 1) * _GRID_GAP
    surf = pygame.Surface((total, total), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    for row in range(grid_size):
        for col in range(grid_size):
            idx = row * grid_size + col
            x = col * (cell_size + _GRID_GAP)
            y = row * (cell_size + _GRID_GAP)

            if idx in wrong:
                color = _GRID_CELL_WRONG
            elif idx in highlight:
                color = _GRID_CELL_ON
            elif idx in selected:
                color = _GRID_CELL_SELECTED
            else:
                color = _GRID_CELL_OFF

            pygame.draw.rect(surf, color, (x, y, cell_size, cell_size), border_radius=_GRID_CELL_RADIUS)

    raw = pygame.image.tostring(surf, "RGBA")
    image = QImage(raw, surf.get_width(), surf.get_height(), QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())

_FEEDBACK_MS = 1500
_RESULT_MS = 1800

_IDLE = "idle"
_COUNTDOWN = "countdown"
_MEMORIZE = "memorize"
_RECALL = "recall"
_FEEDBACK = "feedback"
_RESULT = "result"
_FAILED = "failed"

_COUNTDOWN_MS = 900


class MemoryGridWidget(BaseGameWidget):
    _object_name = "memoryGridWidget"
    _game_name = "memory-grid"
    _hud_label_word = "Grid"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_positions: set[int] = set()
        self._selected_positions: set[int] = set()
        self._wrong_positions: set[int] = set()
        self._grid_size = 3
        self._cell_size = 42
        self._response_ms = 0

    def _build_ui(self) -> None:
        root = self._build_hud_header("Memory Grid", margins=(130, 90, 130, 80))
        root.addStretch(1)
        root.addSpacing(30)

        self._lbl_phase = QLabel("")
        self._lbl_phase.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_phase.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(OFF_WHITE, 30, 500))
        self._lbl_phase.setFixedHeight(52)
        root.addWidget(self._lbl_phase)
        root.addSpacing(16)

        self._lbl_counter = QLabel("")
        self._lbl_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_counter.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_counter.setStyleSheet(get_memory_grid_counter_style())
        self._lbl_counter.setFixedHeight(34)
        root.addWidget(self._lbl_counter)

        root.addSpacing(18)

        self._lbl_grid = QLabel()
        self._lbl_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_grid.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lbl_grid.mousePressEvent = self._on_grid_clicked
        root.addWidget(self._lbl_grid, 0, Qt.AlignmentFlag.AlignHCenter)

        root.addStretch(1)

        _word = f'<span style="color:{FONT_PRIMARY};">{translate("MemoryGridWidget", "grid squares")}</span>'
        self._build_hud_footer(
            root,
            translate("MemoryGridWidget", "Select the {word} you remember").format(word=_word),
        )

    def _show_countdown(self):
        self._countdown_value = 3
        self._state = _COUNTDOWN
        self._hud_update(show_next_trial=True)
        self._bar_timer.setValue(0)
        self._lbl_phase.setMaximumHeight(16777215)
        self._lbl_phase.setMinimumHeight(0)
        self._lbl_phase.setText(
            f'<span style="color:{OFF_WHITE};">{self._countdown_value}</span>'
        )
        self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(OFF_WHITE, 80, 700))
        self._lbl_counter.hide()
        self._lbl_grid.hide()
        self._timer.start(_COUNTDOWN_MS)

    def _begin_trial(self) -> None:
        assert self._game is not None
        if self._check_trial_complete():
            return

        self._trial_params = self._game.start_trial()
        self._target_positions = set(self._trial_params.get("pattern_positions", []))
        self._selected_positions = set()
        self._wrong_positions = set()
        self._grid_size = int(self._trial_params.get("grid_size", 3))
        self._response_ms = int(self._trial_params.get("response_duration", 3500))
        self._after_feedback = None

        cell_size_by_grid = {3: 82, 4: 66, 5: 70, 6: 60, 7: 52, 8: 46}
        self._cell_size = cell_size_by_grid.get(self._grid_size, 42)

        self._hud_update(show_next_trial=True)
        self._enter_memorize_phase()

    def _refresh_grid(self):
        """Re-render grid via pygame and update the label."""
        highlight = set()
        selected = set()
        wrong = set()

        if self._state == _MEMORIZE:
            highlight = self._target_positions
        elif self._state == _RECALL:
            selected = self._selected_positions
        elif self._state == _FEEDBACK:
            highlight = self._target_positions
            wrong = self._wrong_positions

        pix = _render_grid_pixmap(
            self._grid_size,
            highlight=highlight,
            selected=selected,
            wrong=wrong,
            cell_size=self._cell_size,
        )
        self._lbl_grid.setPixmap(pix)

    def _pos_to_cell(self, pos_x: int, pos_y: int) -> int | None:
        """Map a click position on the label to a cell index."""
        pix = self._lbl_grid.pixmap()
        if pix is None:
            return None

        lbl_w = self._lbl_grid.width()
        lbl_h = self._lbl_grid.height()
        pix_w = pix.width()
        pix_h = pix.height()
        off_x = (lbl_w - pix_w) // 2
        off_y = (lbl_h - pix_h) // 2

        x = pos_x - off_x
        y = pos_y - off_y
        if x < 0 or y < 0 or x >= pix_w or y >= pix_h:
            return None

        stride = self._cell_size + _GRID_GAP
        col = x // stride
        row = y // stride
        if x % stride >= self._cell_size or y % stride >= self._cell_size:
            return None
        if 0 <= row < self._grid_size and 0 <= col < self._grid_size:
            return row * self._grid_size + col
        return None

    def _on_grid_clicked(self, event: QMouseEvent):
        if self._state != _RECALL:
            return

        idx = self._pos_to_cell(event.pos().x(), event.pos().y())
        if idx is None:
            return

        target_count = int(self._trial_params.get("target_count", 0))

        if idx in self._selected_positions:
            self._selected_positions.discard(idx)
        else:
            if len(self._selected_positions) >= target_count:
                return
            self._selected_positions.add(idx)

        self._refresh_grid()
        self._update_selection_counter()

        if len(self._selected_positions) == target_count:
            self._timer.stop()
            self._tick.stop()
            self._evaluate_response(float(self._elapsed.elapsed()))

    def _enter_memorize_phase(self):
        self._state = _MEMORIZE
        self._timer.stop()
        self._tick.stop()
        self._lbl_grid.show()
        self._lbl_counter.show()
        self._lbl_phase.setFixedHeight(52)

        self._lbl_phase.setText("")
        self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(OFF_WHITE, 30, 500))
        target_count = int(self._trial_params.get("target_count", 0))
        self._lbl_counter.setText(
            format_ratio_counter(
                0,
                target_count,
                primary_color="transparent",
                secondary_color="transparent",
            )
        )

        self._refresh_grid()

        stimulus_ms = int(self._trial_params.get("stimulus_duration", 1000))
        self._bar_timer.setValue(1000)
        self._elapsed.start()
        self._tick.start()
        self._timer.start(stimulus_ms)

    def _enter_recall_phase(self):
        self._state = _RECALL
        self._timer.stop()
        self._tick.stop()

        self._lbl_phase.setText("&nbsp;")
        self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(OFF_WHITE, 30, 500))

        self._selected_positions = set()
        self._refresh_grid()

        self._update_selection_counter()

        self._bar_timer.setValue(1000)
        self._elapsed.start()
        self._tick.start()
        self._timer.start(self._response_ms)

    def _update_selection_counter(self):
        target_count = int(self._trial_params.get("target_count", 0))
        selected = len(self._selected_positions)
        self._lbl_counter.setText(format_ratio_counter(selected, target_count))

    def _evaluate_response(self, reaction_time_ms: float) -> None:
        response = ",".join(str(p) for p in sorted(self._selected_positions))
        result = self._game.evaluate_trial(self._trial_params, response, reaction_time_ms)

        self._state = _FEEDBACK
        color = PRIMARY_LIGHT if result.is_correct else INCORRECT_COLOR
        symbol = "✓" if result.is_correct else "✗"
        text = translate("MemoryGridWidget", "Correct") if result.is_correct else translate("MemoryGridWidget", "Incorrect")
        self._lbl_phase.setText(
            f'<span style="color:{color}; font-size:30px; font-weight:600;">{symbol} {text}</span>'
        )

        hits = int(result.stimulus_params.get("hits", 0))
        target_count = int(result.stimulus_params.get("target_count", 0))
        self._lbl_counter.setText(format_ratio_counter(hits, target_count))

        self._wrong_positions = self._selected_positions - self._target_positions
        self._refresh_grid()

        if self._mode == "tutorial" and self._runner is not None:
            if self._runner.check_after_trial():
                if self._service:
                    _svc = self._service
                    _runner = self._runner

                    def _save_tutorial(svc=_svc):
                        svc.start_run(stage="tutorial", initialize_game=False)

                    self._keep_thread(registry.run_thread(_save_tutorial, lambda _: None))
                self._after_feedback = _RESULT

        self._hud_update(show_next_trial=False)

        self._timer.start(_FEEDBACK_MS)

    def _on_tick(self):
        if self._state not in {_MEMORIZE, _RECALL}:
            return

        phase_ms = int(self._trial_params.get("stimulus_duration", 1000)) if self._state == _MEMORIZE else self._response_ms
        if phase_ms <= 0:
            return

        remaining = max(0, phase_ms - self._elapsed.elapsed())
        self._bar_timer.setValue(int(remaining / phase_ms * 1000))

    def _on_timeout(self) -> None:
        if self._state == _COUNTDOWN:
            self._countdown_value -= 1
            if self._countdown_value > 0:
                self._lbl_phase.setText(
                    f'<span style="color:{OFF_WHITE};">{self._countdown_value}</span>'
                )
                self._timer.start(_COUNTDOWN_MS)
            else:
                self._countdown_done = True
                if self._db_ready:
                    self._begin_trial()
            return

        if self._state == _MEMORIZE:
            self._enter_recall_phase()
            return

        if self._state == _RECALL:
            self._tick.stop()
            self._evaluate_response(float(self._response_ms))
            return

        if self._state == _FEEDBACK:
            if self._mode == "tutorial" and self._runner is not None and getattr(self._runner, "failed", False):
                self._state = _FAILED
                self._lbl_phase.setText("Tutorial Failed")
                self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(INCORRECT_COLOR, 46, 700))
                self._lbl_counter.hide()
                self._timer.start(_RESULT_MS)
                return
            nxt = self._after_feedback
            self._after_feedback = None
            if nxt == _RESULT:
                self._state = _RESULT
                self._lbl_phase.setText("Tutorial Complete!")
                self._lbl_phase.setStyleSheet(get_memory_grid_phase_style(PRIMARY_LIGHT, 46, 700))
                self._lbl_counter.hide()
                self._timer.start(_RESULT_MS)
            else:
                self._begin_trial()
            return

        if self._state == _RESULT:
            self._finish_session(completed=True)

        if self._state == _FAILED:
            self._finish_session(completed=False)
