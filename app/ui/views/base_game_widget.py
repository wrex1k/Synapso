from __future__ import annotations

import pygame
from PySide6.QtCore import QElapsedTimer, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.utils.logger import logger
from app.core.registry import registry
from app.service.game_service import GameService
from app.utils.ui_helpers import draw_background
from app.ui.styles.colors import FONT_PRIMARY, OFF_WHITE, PRIMARY_LIGHT, INCORRECT_COLOR
from app.ui.styles.fonts import GENERAL_SANS
from app.ui.styles.games import format_hud_infinite, format_hud_progress


_FONT_CACHE: dict[tuple[int, bool], pygame.font.Font] = {}


def _get_cached_font(size: int, bold: bool) -> pygame.font.Font:
    key = (size, bool(bold))
    font = _FONT_CACHE.get(key)
    if font is None:
        font = pygame.font.SysFont(GENERAL_SANS, size, bold=bold)
        _FONT_CACHE[key] = font
    return font


_IDLE = "idle"
_STIMULUS = "stimulus"


class BaseGameWidget(QWidget):
    session_done = Signal(bool)

    _object_name: str = ""
    _game_name: str = ""
    _hud_label_word: str = "Trial"
    _tick_interval: int = 8
    _feedback_font_size: int = 34
    _correct_color_hex: str = PRIMARY_LIGHT

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if self._object_name:
            self.setObjectName(self._object_name)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if not pygame.font.get_init():
            pygame.font.init()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        self._tick = QTimer(self)
        self._tick.setTimerType(Qt.TimerType.PreciseTimer)
        self._tick.setInterval(self._tick_interval)
        self._tick.timeout.connect(self._on_tick)

        self._elapsed = QElapsedTimer()
        self._stimulus_ms: int = 0

        self._game = None
        self._service: GameService | None = None
        self._runner = None
        self._mode = "training"
        self._state = _IDLE
        self._countdown_value: int = 0
        self._db_ready: bool = False
        self._countdown_done: bool = False
        self._trial_params: dict | None = None
        self._after_feedback: str | None = None
        self._threads: list = []

        self._build_ui()

    @staticmethod
    def _make_progress_bar(name: str, max_val: int) -> QProgressBar:
        bar = QProgressBar()
        bar.setObjectName(name)
        bar.setRange(0, max_val)
        bar.setValue(0 if max_val == 100 else max_val)
        bar.setTextVisible(False)
        return bar

    def _build_hud_header(
        self, title_name: str, margins: tuple = (130, 90, 130, 80)
    ) -> QVBoxLayout:
        root = QVBoxLayout(self)
        root.setContentsMargins(*margins)
        root.setSpacing(0)

        hud = QHBoxLayout()
        hud.setSpacing(20)

        self._lbl_trial = QLabel("")
        self._lbl_trial.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_trial.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_trial.setProperty("hud", "trial")
        self._lbl_trial.update()
        hud.addWidget(self._lbl_trial, 0)

        hud.addStretch()

        self._lbl_hud_title = QLabel(
            f'<span style="color:{OFF_WHITE};">Synapso</span>&nbsp;'
            f'<span style="color:{FONT_PRIMARY};">{title_name}</span>'
        )
        self._lbl_hud_title.setProperty("hud", "title")
        self._lbl_hud_title.update()
        self._lbl_hud_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_hud_title.setTextFormat(Qt.TextFormat.RichText)
        hud.addWidget(self._lbl_hud_title, 0)
        root.addLayout(hud)

        root.addSpacing(10)

        self._bar_trial = self._make_progress_bar("stroopTrialBar", 100)
        self._bar_timer = self._make_progress_bar("stroopAccuracyBar", 1000)
        root.addWidget(self._bar_trial)
        root.addSpacing(7)
        root.addWidget(self._bar_timer)

        return root

    def _build_hud_footer(self, root: QVBoxLayout, hint_html: str) -> None:
        self._lbl_hint = QLabel(hint_html)
        self._lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_hint.setProperty("hud", "hint")
        self._lbl_hint.update()
        root.addWidget(self._lbl_hint)
        root.addSpacing(40)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    def _render_feedback_pixmap(self, correct: bool) -> QPixmap:
        color_hex = self._correct_color_hex if correct else INCORRECT_COLOR
        color = self._hex_to_rgb(color_hex)
        symbol = "✓" if correct else "✗"
        text = "Correct" if correct else "Incorrect"
        size = self._feedback_font_size

        symbol_font = _get_cached_font(size, True)
        text_font = _get_cached_font(size, True)
        symbol_surface = symbol_font.render(symbol, True, color)
        text_surface = text_font.render(text, True, color)
        gap = 10
        width = symbol_surface.get_width() + gap + text_surface.get_width()
        height = max(symbol_surface.get_height(), text_surface.get_height())
        combined = pygame.Surface((width, height), pygame.SRCALPHA)
        combined.blit(symbol_surface, (0, (height - symbol_surface.get_height()) // 2))
        combined.blit(
            text_surface,
            (symbol_surface.get_width() + gap, (height - text_surface.get_height()) // 2),
        )
        raw = pygame.image.tostring(combined, "RGBA")
        image = QImage(raw, combined.get_width(), combined.get_height(), QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(image.copy())

    def paintEvent(self, event) -> None:
        draw_background(self, event)

    def start_tutorial(self, game, service: GameService, runner) -> None:
        self._game = game
        self._service = service
        self._runner = runner
        self._mode = "tutorial"
        self.setFocus()
        self._db_ready = False
        self._countdown_done = False
        self._show_countdown()
        if self._should_skip_tutorial_async_init():
            self._db_ready = True
            return
        self._start_tutorial_flow_async()

    def _should_skip_tutorial_async_init(self) -> bool:
        return False

    def start_play(self, game, service: GameService) -> None:
        self._game = game
        self._service = service
        self._runner = None
        self._mode = "training"
        self.setFocus()
        self._db_ready = False
        self._countdown_done = False
        self._show_countdown()
        self._start_play_flow_async()

    def _keep_thread(self, thread) -> None:
        self._threads.append(thread)
        thread.finished.connect(
            lambda t=thread: self._threads.remove(t) if t in self._threads else None
        )

    def _start_tutorial_flow_async(self) -> None:
        if self._service is None or self._runner is None:
            return

        def _task() -> bool:
            try:
                self._runner.configure()
                return True
            except Exception:
                logger.exception("Failed to initialize %s tutorial", self._game_name)
                return False

        self._keep_thread(registry.run_thread(_task, self._on_tutorial_init_done))

    def _on_tutorial_init_done(self, ok: bool) -> None:
        if not ok:
            self._finish_session(completed=False)
            return
        self._db_ready = True
        if self._countdown_done:
            self._begin_trial()

    def _start_play_flow_async(self) -> None:
        if self._service is None:
            return

        def _task() -> bool:
            try:
                self._service.start_run()
                return True
            except Exception:
                logger.exception("Failed to initialize %s training", self._game_name)
                return False

        self._keep_thread(registry.run_thread(_task, self._on_play_init_done))

    def _on_play_init_done(self, ok: bool) -> None:
        if not ok:
            self._finish_session(completed=False)
            return
        self._db_ready = True
        if self._countdown_done:
            self._begin_trial()

    def _hud_update(self, show_next_trial: bool = False) -> None:
        if self._game is None:
            return
        p = self._game.get_progress()
        total = int(p["total_trials"])
        current = int(p["current_trial"])
        n = min(total, current + 1) if show_next_trial else min(total, current)

        if self._mode == "tutorial":
            self._lbl_trial.setText(format_hud_infinite(self._hud_label_word))
            self._bar_trial.setValue(
                self._runner.get_progress_pct() if self._runner is not None else 0
            )
        else:
            self._lbl_trial.setText(
                format_hud_progress(self._hud_label_word, str(n), str(total))
            )
            self._bar_trial.setValue(
                int(p["current_trial"] / total * 100) if total else 0
            )


    def _check_trial_complete(self) -> bool:
        idx = self._game.current_trial_index
        total = self._game.total_trials
        if self._mode == "training" and idx >= total:
            self._finish_session(completed=True)
            return True
        if self._mode == "tutorial" and idx >= total:
            self._finish_session(completed=False)
            return True
        return False

    def _finish_session(self, completed: bool) -> None:
        if self._service:
            if self._mode == "training":
                if completed:
                    try:
                        self._service.finish_run(stage="training")
                    except Exception as exc:
                        logger.warning("Could not save %s run: %s", self._game_name, exc)
                else:
                    try:
                        self._service.abort_run()
                    except Exception as exc:
                        logger.warning("Could not abort %s run: %s", self._game_name, exc)
            elif self._mode == "tutorial":
                if completed:
                    try:
                        self._service.finish_run(stage="tutorial", status="completed")
                        if self._runner is not None:
                            self._service.complete_tutorial(self._runner)
                    except Exception as exc:
                        logger.warning(
                            "Could not save %s tutorial run: %s", self._game_name, exc
                        )
                else:
                    try:
                        self._service.abort_run()
                    except Exception as exc:
                        logger.warning(
                            "Could not abort %s tutorial run: %s", self._game_name, exc
                        )
        self._service = None
        self.session_done.emit(completed)

    def closeEvent(self, event) -> None:
        if self._service:
            self._timer.stop()
            self._tick.stop()
            try:
                self._service.abort_run()
            except Exception as exc:
                logger.warning("closeEvent abort failed for %s: %s", self._game_name, exc)
            self._service = None
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._timer.stop()
            self._tick.stop()
            self._state = _IDLE
            self._finish_session(completed=False)
            return
        super().keyPressEvent(event)


    def _on_tick(self) -> None:
        if self._state != _STIMULUS:
            return
        if self._stimulus_ms <= 0:
            return
        remaining = max(0, self._stimulus_ms - self._elapsed.elapsed())
        self._bar_timer.setValue(int(remaining / self._stimulus_ms * 1000))

    def _build_ui(self) -> None: ...
    def _show_countdown(self) -> None: ...
    def _begin_trial(self) -> None: ...
    def _on_timeout(self) -> None: ...
