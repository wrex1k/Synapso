"""Stroop-specific pygame renderer."""

from __future__ import annotations

import pygame

from app.games.core.renderer import (
    GameConfig,
    GameRenderer,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from app.games.stroop.config import COLORS, ColorDef


class StroopConfig(GameConfig):
    KEY_MAP: dict[int, str] = {
        pygame.K_r: "r",
        pygame.K_y: "y",
        pygame.K_g: "g",
        pygame.K_b: "b",
        pygame.K_p: "p",
    }

    def get_key_map(self) -> dict[int, str]:
        return self.KEY_MAP

    def get_available_keys_legend(self, available_keys: list[str]) -> list[tuple[str, tuple]]:
        key_color_map = self._get_key_color_map()
        legend = []
        for key in available_keys:
            if key in key_color_map:
                color_def = key_color_map[key]
                legend.append((key, color_def.rgb))
        return legend

    def get_key_color(self, key: str) -> tuple[int, int, int] | None:
        color_map = self._get_key_color_map()
        if key in color_map:
            return color_map[key].rgb
        return None

    @staticmethod
    def _get_key_color_map() -> dict[str, ColorDef]:
        return {c.key: c for c in COLORS}


class StroopRenderer(GameRenderer):
    def __init__(self, game):
        super().__init__(game, StroopConfig())

    def _show_stimulus_and_wait(self, params: dict, hud_extra: str | None = None) -> tuple[str | None, float]:
        stimulus_duration = params["stimulus_duration"]
        word = params["word"]
        ink_rgb = tuple(params["ink_color_rgb"])
        available_keys = params.get("available_keys", [c.key for c in COLORS])

        key_map = self.config.get_key_map()
        start_ticks = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - start_ticks

            if elapsed >= stimulus_duration:
                return None, float(stimulus_duration)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_requested = True
                    return None, float(elapsed)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._quit_requested = True
                        return None, float(elapsed)

                    key = key_map.get(event.key)
                    if key and key in available_keys:
                        return key, float(elapsed)

            self._draw_background()
            self._draw_main_panel()
            self._draw_centered_text(word, self.font_stimulus, ink_rgb, dy=-20)
            self._draw_key_legend(available_keys)
            self._draw_hud(hud_extra=hud_extra)
            self._draw_timer_bar(1.0 - elapsed / stimulus_duration)
            pygame.display.flip()
            self.clock.tick(60)
