"""
Generic Pygame renderer for cognitive games.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from app.ui.styles.fonts import GENERAL_SANS
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.games.core.base_game import BaseGame

logger = get_logger(__name__)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BG_COLOR = (30, 30, 30)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (150, 150, 150)
TEXT_CORRECT = (50, 200, 100)
TEXT_INCORRECT = (200, 50, 50)
ACCENT_PRIMARY = (62, 172, 145)
ACCENT_DIM = (43, 82, 76)
PANEL_BG = (21, 36, 35, 170)
PANEL_BORDER = (86, 134, 124, 210)

FIXATION_MS = 500
FEEDBACK_MS = 800
INTER_TRIAL_MS = 300


class GameConfig(ABC):
    @abstractmethod
    def get_key_map(self) -> dict[int, str]:
        """Return Pygame key -> response key mapping."""

    @abstractmethod
    def get_available_keys_legend(self, available_keys: list[str]) -> list[tuple[str, tuple]]:
        """Return list of (key_label, rgb_color) tuples for legend display."""

class GameRenderer(ABC):
    def __init__(self, game: "BaseGame", config: GameConfig):
        self.game = game
        self.config = config
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.font_stimulus: pygame.font.Font | None = None
        self.font_ui: pygame.font.Font | None = None
        self.font_feedback: pygame.font.Font | None = None
        self.font_title: pygame.font.Font | None = None
        self._quit_requested = False
        self._bg_surface: pygame.Surface | None = None

    def _init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_stimulus = pygame.font.SysFont(GENERAL_SANS, 72, bold=True)
        self.font_feedback = pygame.font.SysFont(GENERAL_SANS, 48, bold=True)
        self.font_ui = pygame.font.SysFont(GENERAL_SANS, 24)
        self.font_title = pygame.font.SysFont(GENERAL_SANS, 30, bold=True)
        self._bg_surface = self._build_background_surface()

    def _quit_pygame(self):
        pygame.quit()

    def run_all_trials(self) -> bool:
        self._init_pygame()
        try:
            while self.game.current_trial_index < self.game.total_trials:
                if self._quit_requested:
                    return False

                trial_params = self.game.start_trial()
                result = self._run_single_trial(trial_params)

                if result is None:
                    return False

            return True
        finally:
            self._quit_pygame()

    def run_tutorial_trials(self, runner) -> bool:
        self._init_pygame()
        try:
            while True:
                if self._quit_requested:
                    return False

                trial_params = self.game.start_trial()
                result = self._run_single_trial(trial_params, hud_extra=runner.get_progress_text())

                if result is None:
                    return False

                if runner.check_after_trial():
                    self._show_tutorial_passed()
                    return True

        finally:
            self._quit_pygame()

    def _run_single_trial(self, trial_params: dict, hud_extra: str | None = None):
        if not self._show_fixation(FIXATION_MS, hud_extra=hud_extra):
            return None

        response, reaction_time_ms = self._show_stimulus_and_wait(trial_params, hud_extra=hud_extra)
        if self._quit_requested:
            return None

        result = self.game.evaluate_trial(trial_params, response, reaction_time_ms)

        if not self._show_feedback(result.is_correct, reaction_time_ms, hud_extra=hud_extra):
            return None

        if not self._wait(INTER_TRIAL_MS, hud_extra=hud_extra):
            return None

        return result

    def _show_fixation(self, duration_ms: int, hud_extra: str | None = None) -> bool:
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < duration_ms:
            if not self._pump_events():
                return False
            self._draw_background()
            self._draw_main_panel()
            self._draw_centered_text("+", self.font_stimulus, TEXT_WHITE, dy=-20)
            self._draw_hud(hud_extra=hud_extra)
            pygame.display.flip()
            self.clock.tick(60)
        return True

    @abstractmethod
    def _show_stimulus_and_wait(self, params: dict, hud_extra: str | None = None) -> tuple[str | None, float]:
        """Display stimulus and wait for response or timeout."""

    def _show_feedback(self, is_correct: bool, reaction_time_ms: float, hud_extra: str | None = None) -> bool:
        color = TEXT_CORRECT if is_correct else TEXT_INCORRECT
        label = "\u2713 Correct!!!!!!" if is_correct else "\u2717 Incorrect!!!!!"
        rt_text = f"{reaction_time_ms:.0f} ms"

        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < FEEDBACK_MS:
            if not self._pump_events():
                return False
            self._draw_background()
            self._draw_main_panel()
            self._draw_centered_text(label, self.font_feedback, color, dy=-30)
            self._draw_centered_text(rt_text, self.font_ui, TEXT_GRAY, dy=20)
            self._draw_hud(hud_extra=hud_extra)
            pygame.display.flip()
            self.clock.tick(60)
        return True

    def _draw_hud(self, hud_extra: str | None = None):
        progress = self.game.get_progress()
        total_trials = int(progress.get("total_trials", 0) or 0)
        current_trial = int(progress.get("current_trial", 0) or 0)
        shown_trial = min(total_trials, current_trial + 1) if total_trials else current_trial + 1
        trial_text = f"Trial {shown_trial}"
        level_text = f"Level {progress['level']}"
        game_name = str(getattr(self.game, "game_slug", "Game")).replace("_", " ").title()

        title_left = self.font_title.render("Synapso", True, TEXT_WHITE)
        title_right = self.font_title.render(game_name, True, ACCENT_PRIMARY)
        self.screen.blit(title_left, (28, 20))
        self.screen.blit(title_right, (28 + title_left.get_width() + 10, 20))

        trial_surf = self.font_ui.render(trial_text, True, (190, 203, 200))
        level_surf = self.font_ui.render(level_text, True, (190, 203, 200))

        self.screen.blit(trial_surf, (28, 58))
        self.screen.blit(level_surf, (SCREEN_WIDTH - level_surf.get_width() - 28, 58))

        if hud_extra:
            extra_surf = self.font_ui.render(hud_extra, True, ACCENT_PRIMARY)
            x = (SCREEN_WIDTH - extra_surf.get_width()) // 2
            self.screen.blit(extra_surf, (x, 58))

    def _draw_timer_bar(self, progress: float):
        bar_w = SCREEN_WIDTH - 96
        bar_h = 10
        x, y = 48, SCREEN_HEIGHT - 34

        pygame.draw.rect(self.screen, (38, 61, 58), (x, y, bar_w, bar_h), border_radius=6)

        fill_w = int(bar_w * max(0.0, progress))
        bar_color = ACCENT_PRIMARY if progress > 0.3 else TEXT_INCORRECT
        if fill_w > 0:
            pygame.draw.rect(self.screen, bar_color, (x, y, fill_w, bar_h), border_radius=6)

    def _draw_key_legend(self, available_keys: list[str]):
        legend = self.config.get_available_keys_legend(available_keys)
        spacing = 88
        chip_w = 64
        chip_h = 34
        x_start = (SCREEN_WIDTH - len(legend) * spacing) // 2
        y = SCREEN_HEIGHT - 84

        for i, (label, rgb) in enumerate(legend):
            x = x_start + i * spacing
            chip = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
            pygame.draw.rect(chip, (26, 46, 43, 210), (0, 0, chip_w, chip_h), border_radius=10)
            pygame.draw.rect(chip, (66, 102, 96, 220), (0, 0, chip_w, chip_h), width=1, border_radius=10)
            self.screen.blit(chip, (x, y))

            surf = self.font_ui.render(label.upper(), True, rgb)
            self.screen.blit(surf, (x + (chip_w - surf.get_width()) // 2, y + (chip_h - surf.get_height()) // 2 - 1))

    def _draw_centered_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple,
        dx: int = 0,
        dy: int = 0,
    ):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2 + dx, SCREEN_HEIGHT // 2 + dy))
        shadow = font.render(text, True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(rect.centerx + 2, rect.centery + 2))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(surf, rect)

    def _build_background_surface(self) -> pygame.Surface:
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        top = (17, 27, 26)
        bottom = (31, 48, 46)
        for y in range(SCREEN_HEIGHT):
            t = y / max(1, SCREEN_HEIGHT - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(bg, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (62, 172, 145, 55), (SCREEN_WIDTH - 120, 100), 180)
        pygame.draw.circle(glow, (62, 172, 145, 35), (120, SCREEN_HEIGHT - 70), 160)
        bg.blit(glow, (0, 0))
        return bg

    def _draw_background(self):
        if self._bg_surface is None:
            self._bg_surface = self._build_background_surface()
        self.screen.blit(self._bg_surface, (0, 0))

    def _draw_main_panel(self):
        panel_w = SCREEN_WIDTH - 120
        panel_h = SCREEN_HEIGHT - 190
        x = (SCREEN_WIDTH - panel_w) // 2
        y = 110
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, PANEL_BG, (0, 0, panel_w, panel_h), border_radius=24)
        pygame.draw.rect(panel, PANEL_BORDER, (0, 0, panel_w, panel_h), width=1, border_radius=24)
        self.screen.blit(panel, (x, y))

    def _pump_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit_requested = True
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._quit_requested = True
                return False
        return True

    def _show_tutorial_passed(self):
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
            self._pump_events()
            self._draw_background()
            self._draw_main_panel()
            self._draw_centered_text("Tutorial Complete :)))!", self.font_feedback, TEXT_CORRECT, dy=-20)
            self._draw_centered_text("Get ready to play", self.font_ui, TEXT_GRAY, dy=30)
            pygame.display.flip()
            self.clock.tick(60)

    def _wait(self, duration_ms: int, hud_extra: str | None = None) -> bool:
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < duration_ms:
            if not self._pump_events():
                return False
            self._draw_background()
            self._draw_main_panel()
            self._draw_hud(hud_extra=hud_extra)
            pygame.display.flip()
            self.clock.tick(60)
        return True
