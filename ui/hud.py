"""Heads-up display: hearts, part inventory, objective and timer."""

from __future__ import annotations

import pygame

from art import sprites
from core import color, levels, settings, text


class HUD:
    def __init__(self, state, cfg: dict | None = None) -> None:
        self.state = state
        self.cfg = cfg or {}
        self.hearts_current: int | None = None
        self.hearts_max: int | None = None
        self.timer: float | None = None
        self.objective: str = self.cfg.get("objective", "")
        self.hint_prompt = False
        self.t = 0.0
        self.target: tuple[str, tuple[int, int, int]] | None = None
        self._planet_colors: dict[str, tuple[int, int, int]] = {}
        for planet in levels.load_planets()["planets"]:
            part = planet.get("part")
            if part:
                self._planet_colors[part] = color.hex_to_rgb(planet.get("color", "#8fa3c8"))

    # --- data ---------------------------------------------------------------
    def set_hearts(self, current: int | None, maximum: int | None) -> None:
        self.hearts_current = current
        self.hearts_max = maximum

    def set_timer(self, seconds: float | None) -> None:
        self.timer = seconds

    def set_objective(self, value: str) -> None:
        self.objective = value

    def set_target(self, name: str, color: tuple[int, int, int]) -> None:
        """Show the labeled part this level is about, right in the top bar."""
        self.target = (name, color)

    def update(self, dt: float) -> None:
        self.t += dt

    # --- drawing ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        bar = pygame.Surface((settings.WIDTH, 56), pygame.SRCALPHA)
        bar.fill((4, 8, 18, 205))
        surface.blit(bar, (0, 0))
        pygame.draw.line(surface, settings.PANEL_EDGE, (0, 56), (settings.WIDTH, 56), 1)

        x = 24
        if self.hearts_max:
            for index in range(self.hearts_max):
                filled = self.hearts_current is not None and index < self.hearts_current
                sprites.draw_heart(surface, (x + 10, 28), 18, filled=filled)
                x += 26
            x += 12

        # part inventory
        text.draw(surface, "PARTS", (x, 20), 16, settings.DIM, shadow=False)
        x += 56
        collected = 0
        for part, part_color in self._planet_colors.items():
            owned = self.state.has_part(part)
            center = (x + 10, 28)
            if owned:
                sprites.draw_part(surface, center, 10, part_color, self.t, glow=False)
                collected += 1
            else:
                pygame.draw.circle(surface, settings.PANEL_EDGE, center, 10, 1)
                pygame.draw.circle(surface, (20, 30, 48), center, 8)
            x += 30

        if self._planet_colors:
            text.draw(
                surface,
                f"{collected}/{len(self._planet_colors)}",
                (x + 2, 20),
                16,
                settings.DIM,
                shadow=False,
            )
            x += 40

        # labeled mission target part
        if self.target:
            name, part_color = self.target
            owned = self.state.has_part(name)
            chip_w = text.measure(name, 15)[0] + 46
            rect = pygame.Rect(x, 12, chip_w, 30)
            pygame.draw.rect(surface, (8, 14, 26), rect, border_radius=15)
            pygame.draw.rect(surface, settings.GREEN if owned else part_color, rect, 1, border_radius=15)
            sprites.draw_part(surface, (rect.x + 16, rect.centery), 8, part_color, self.t, glow=False)
            text.draw(
                surface,
                name,
                (rect.x + 30, rect.centery),
                15,
                settings.DIM if owned else settings.INK,
                middle=True,
                shadow=False,
            )

        # timer
        if self.timer is not None:
            remaining = max(0.0, float(self.timer))
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            danger = remaining <= 15.0
            pulse = 1.0
            if danger:
                pulse = 0.65 + 0.35 * abs(pygame.math.Vector2(1, 0).rotate(self.t * 360).x)
            timer_color = settings.DANGER if danger else settings.INK
            text.draw(
                surface,
                f"{minutes:01d}:{seconds:02d}",
                (settings.WIDTH - 26, 12),
                26,
                timer_color,
                display=True,
                right=True,
                alpha=int(255 * pulse) if danger else 255,
            )

        # objective
        if self.objective:
            text.draw(
                surface,
                self.objective,
                (24, 66),
                20,
                settings.DIM,
                max_width=settings.WIDTH - 48,
                shadow=False,
            )

        if self.hint_prompt:
            label = "H  Laika hint"
            width = text.measure(label, 18)[0] + 24
            rect = pygame.Rect(settings.WIDTH - width - 22, settings.HEIGHT - 44, width, 26)
            pygame.draw.rect(surface, (8, 14, 26), rect, border_radius=13)
            pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 1, border_radius=13)
            text.draw(
                surface,
                label,
                (rect.centerx, rect.centery),
                18,
                settings.ACCENT,
                center=True,
                middle=True,
                shadow=False,
            )
