"""Mental Rotation pygame renderer."""

from __future__ import annotations

import pygame

from app.games.core.renderer import (
    GameConfig,
    GameRenderer,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

_BLOCK_COLOR = (62, 172, 145)
_KEY_COLOR_F = (200, 130, 50)   # F = Mirrored (left hand)
_KEY_COLOR_K = (62, 172, 145)   # K = Same (right hand)


class MentalRotationConfig(GameConfig):
    KEY_MAP: dict[int, str] = {
        pygame.K_k: "k",
        pygame.K_f: "f",
    }

    def get_key_map(self) -> dict[int, str]:
        return self.KEY_MAP

    def get_available_keys_legend(self, available_keys: list[str]) -> list[tuple[str, tuple]]:
        return [
            ("F  Mirrored", _KEY_COLOR_F),
            ("K  Same", _KEY_COLOR_K),
        ]

    def get_key_color(self, key: str) -> tuple[int, int, int] | None:
        return {"k": _KEY_COLOR_K, "f": _KEY_COLOR_F}.get(key)


class MentalRotationRenderer(GameRenderer):
    def __init__(self, game):
        super().__init__(game, MentalRotationConfig())

    # ── shape drawing ──────────────────────────────────────────────────────────

    def _draw_shape(
        self,
        blocks: list[tuple[int, int]],
        rotation: float,
        mirrored: bool,
    ) -> None:
        """Render a block-based shape, rotated and optionally mirrored."""
        CELL = 36
        GAP = 3
        RADIUS = 5

        xs = [p[0] for p in blocks]
        ys = [p[1] for p in blocks]
        cols = max(xs) - min(xs) + 1
        rows = max(ys) - min(ys) + 1
        min_x, min_y = min(xs), min(ys)

        pad = CELL
        surf_w = cols * (CELL + GAP) - GAP + pad * 2
        surf_h = rows * (CELL + GAP) - GAP + pad * 2
        surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        for bx, by in blocks:
            rx = (bx - min_x) * (CELL + GAP) + pad
            ry = (by - min_y) * (CELL + GAP) + pad
            pygame.draw.rect(surf, _BLOCK_COLOR, (rx, ry, CELL, CELL), border_radius=RADIUS)

        if mirrored:
            surf = pygame.transform.flip(surf, True, False)

        rotated = pygame.transform.rotate(surf, -rotation)
        rx = SCREEN_WIDTH // 2 - rotated.get_width() // 2
        ry = SCREEN_HEIGHT // 2 - rotated.get_height() // 2 - 20
        self.screen.blit(rotated, (rx, ry))

    # ── stimulus ───────────────────────────────────────────────────────────────

    def _show_stimulus_and_wait(
        self, params: dict, hud_extra: str | None = None
    ) -> tuple[str | None, float]:
        blocks: list[tuple[int, int]] = params["shape_blocks"]
        rotation: float = float(params["rotation_angle"])
        mirrored: bool = bool(params["mirrored"])
        duration: int = params["stimulus_duration"]
        available_keys: list[str] = params.get("available_keys", ["c", "i"])

        key_map = self.config.get_key_map()
        start_ticks = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - start_ticks

            if elapsed >= duration:
                return None, float(duration)

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
            self._draw_shape(blocks, rotation, mirrored)
            self._draw_key_legend(available_keys)
            self._draw_hud(hud_extra=hud_extra)
            self._draw_timer_bar(1.0 - elapsed / duration)
            pygame.display.flip()
            self.clock.tick(60)
