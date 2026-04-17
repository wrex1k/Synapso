from __future__ import annotations

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

from app.games.stroop.game import COLORS
from app.core.registry import registry
from app.utils.logger import logger
from app.ui.styles.colors import PRIMARY_LIGHT, INCORRECT_COLOR, OFF_WHITE, FONT_PRIMARY
from app.ui.views.base_game_widget import BaseGameWidget, _get_cached_font



_FEEDBACK_MS = 800
_RESULT_MS = 2000

_KEY_MAP: dict[int, str] = {
    Qt.Key.Key_R: "r",
    Qt.Key.Key_Y: "y",
    Qt.Key.Key_G: "g",
    Qt.Key.Key_B: "b",
    Qt.Key.Key_P: "p",
}

_IDLE = "idle"
_COUNTDOWN = "countdown"
_STIMULUS = "stimulus"
_FEEDBACK = "feedback"
_RESULT = "result"
_FAILED = "failed"

_COUNTDOWN_MS = 900


class StroopWidget(BaseGameWidget):
    _object_name = "stroopWidget"
    _game_name = "stroop"
    _hud_label_word = "Trial"
    _tick_interval = 16
    _feedback_font_size = 38

    def _should_skip_tutorial_async_init(self) -> bool:
        return bool(getattr(self._service, "_run_id", None))

    def _build_ui(self) -> None:
        root = self._build_hud_header("SCWT", margins=(150, 100, 150, 80))
        root.addStretch(2)

        centre_box = QVBoxLayout()
        centre_box.setSpacing(12)
        centre_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_feedback = QLabel()
        self._lbl_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_feedback.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_feedback.setStyleSheet("background: transparent;")
        self._lbl_feedback.setMinimumHeight(50)
        centre_box.addWidget(self._lbl_feedback)

        self._lbl_main = QLabel()
        self._lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_main.setMinimumHeight(86)
        centre_box.addWidget(self._lbl_main)

        root.addLayout(centre_box)
        root.addStretch(2)

        self._build_hud_footer(
            root,
            f'Press the key matching the <span style="color:{FONT_PRIMARY};">ink color</span>',
        )

    def _render_text_pixmap(
        self, text: str, rgb: tuple[int, int, int], size: int, weight: int = 700
    ) -> QPixmap:
        font = _get_cached_font(size, weight >= 600)
        surface = font.render(text, True, rgb)
        raw = pygame.image.tostring(surface, "RGBA")
        image = QImage(raw, surface.get_width(), surface.get_height(), QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(image.copy())

    def _set_main_text(
        self, text: str, rgb: tuple[int, int, int], size: int = 68, weight: int = 700
    ) -> None:
        self._lbl_main.setText("")
        self._lbl_main.setPixmap(self._render_text_pixmap(text, rgb, size, weight))

    def _clear_main_text(self) -> None:
        self._lbl_main.clear()

    def _clear_feedback(self) -> None:
        self._lbl_feedback.clear()

    def _show_feedback(self, correct: bool) -> None:
        color = PRIMARY_LIGHT if correct else INCORRECT_COLOR
        symbol = "✓" if correct else "✗"
        text = "Correct" if correct else "Incorrect"
        self._lbl_feedback.setText(
            f'<span style="color:{color}; font-size:38px; font-weight:600;">{symbol} {text}</span>'
        )

    def _show_countdown(self) -> None:
        self._countdown_value = 3
        self._hud_update(show_next_trial=True)
        self._go(_COUNTDOWN)

    def _begin_trial(self) -> None:
        assert self._game is not None

        idx = self._game.current_trial_index
        total = self._game.total_trials
        logger.debug("_begin_trial: idx=%s, total=%s, mode=%s", idx, total, self._mode)

        if self._check_trial_complete():
            if self._mode == "training":
                logger.info("Training complete: reached total trials")
            else:
                logger.warning("Tutorial safety limit reached (%d trials)", total)
            return

        self._trial_params = self._game.start_trial()
        self._after_feedback = None
        logger.debug(
            "Started trial %s/%s, trial_params keys: %s",
            idx + 1,
            total,
            self._trial_params.keys() if self._trial_params else "None",
        )
        self._hud_update(show_next_trial=True)
        self._go(_STIMULUS)

    def _go(self, state: str) -> None:
        self._state = state
        self._timer.stop()

        if state == _STIMULUS:
            self._clear_feedback()
            p = self._trial_params
            r, g, b = p["ink_color_rgb"]
            self._set_main_text(p["word"], (r, g, b), 68, 700)
            self._stimulus_ms = p["stimulus_duration"]
            self._bar_timer.setValue(1000)
            self._elapsed.start()
            self._tick.start()
            self._timer.start(self._stimulus_ms)

        elif state == _FEEDBACK:
            self._tick.stop()
            self._bar_timer.setValue(0)
            self._timer.start(_FEEDBACK_MS)

        elif state == _RESULT:
            self._clear_feedback()
            self._set_main_text("Tutorial Complete!", self._hex_to_rgb(PRIMARY_LIGHT), 46, 700)
            self._timer.start(_RESULT_MS)

        elif state == _COUNTDOWN:
            self._clear_feedback()
            self._set_main_text(str(self._countdown_value), self._hex_to_rgb(OFF_WHITE), 80, 700)
            self._bar_timer.setValue(0)
            self._timer.start(_COUNTDOWN_MS)

        elif state == _FAILED:
            self._clear_feedback()
            self._set_main_text("Tutorial Failed", self._hex_to_rgb(INCORRECT_COLOR), 46, 700)
            self._timer.start(_RESULT_MS)

    def _on_timeout(self) -> None:
        logger.debug("_on_timeout: state=%s", self._state)

        if self._state == _STIMULUS:
            self._tick.stop()
            self._bar_timer.setValue(0)
            self._evaluate(None, float(self._trial_params["stimulus_duration"]))

        elif self._state == _FEEDBACK:
            logger.debug("_on_timeout FEEDBACK: after_feedback=%s", self._after_feedback)
            if self._mode == "tutorial" and self._runner is not None and self._runner.failed:
                logger.info("Tutorial failed - showing failure message")
                self._go(_FAILED)
                return
            nxt = self._after_feedback
            self._after_feedback = None
            if nxt:
                logger.debug("Going to state: %s", nxt)
                self._go(nxt)
            else:
                logger.debug("Going to next trial")
                self._begin_trial()

        elif self._state == _COUNTDOWN:
            self._countdown_value -= 1
            if self._countdown_value > 0:
                self._go(_COUNTDOWN)
            else:
                self._clear_main_text()
                self._countdown_done = True
                if self._db_ready:
                    self._begin_trial()

        elif self._state == _RESULT:
            self._finish_session(completed=True)

        elif self._state == _FAILED:
            self._finish_session(completed=False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._state == _STIMULUS and self._trial_params is not None:
            response = _KEY_MAP.get(event.key())
            if response in self._trial_params.get("available_keys", [c.key for c in COLORS]):
                self._timer.stop()
                self._tick.stop()
                self._evaluate(response, float(self._elapsed.elapsed()))
                return
        super().keyPressEvent(event)

    def _evaluate(self, response: str | None, reaction_time_ms: float) -> None:
        logger.debug("_evaluate: response=%s, rt=%.0fms", response, reaction_time_ms)
        result = self._game.evaluate_trial(self._trial_params, response, reaction_time_ms)
        logger.debug("Result: is_correct=%s", result.is_correct)

        self._show_feedback(result.is_correct)
        self._clear_main_text()

        if self._mode == "tutorial" and self._runner is not None:
            if self._runner.check_after_trial():
                if self._service:
                    _svc = self._service
                    _runner = self._runner

                    def _save_tutorial(svc=_svc):
                        svc.start_run(stage="tutorial", initialize_game=False)

                    self._keep_thread(registry.run_thread(_save_tutorial, lambda _: None))
                self._after_feedback = _RESULT
                logger.debug("Tutorial complete after this feedback")

        self._hud_update(show_next_trial=False)
        logger.debug("Going to FEEDBACK state, after_feedback=%s", self._after_feedback)
        self._go(_FEEDBACK)
