"""Generic value meter: heat, pressure, fuel, radiation."""

from __future__ import annotations

import math

import pygame

from core import settings, text


class Meter:
    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        color: tuple[int, int, int] = settings.WARN,
        max_value: float = 100.0,
        *,
        danger_at: float = 0.75,
        critical_at: float = 0.92,
        show_value: bool = False,
        unit: str = "",
        real_min: float | None = None,
        real_max: float | None = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.max_value = max(1.0, float(max_value))
        self.value = 0.0
        self.danger_at = danger_at
        self.critical_at = critical_at
        self.show_value = show_value
        self.unit = unit
        self.real_min = real_min
        self.real_max = real_max
        self.t = 0.0

    @property
    def display_value(self) -> str:
        """Show the meter in real-world units when a range is provided."""
        if self.real_min is None or self.real_max is None:
            number = f"{self.value:.0f}"
        else:
            mapped = self.real_min + self.ratio * (self.real_max - self.real_min)
            number = f"{mapped:+.0f}" if self.real_min < 0 else f"{mapped:.0f}"
        return f"{number}{self.unit}"

    # --- data ---------------------------------------------------------------
    def set(self, value: float) -> None:
        self.value = max(0.0, min(self.max_value, float(value)))

    def add(self, delta: float) -> None:
        self.set(self.value + delta)

    @property
    def ratio(self) -> float:
        return self.value / self.max_value

    def update(self, dt: float) -> None:
        self.t += dt

    # --- drawing ------------------------------------------------------------
    def _current_color(self) -> tuple[int, int, int]:
        ratio = self.ratio
        if ratio >= self.critical_at:
            pulse = (math.sin(self.t * 12.0) + 1) * 0.5
            return tuple(
                int(a + (b - a) * pulse) for a, b in zip(settings.DANGER, (255, 220, 230))
            )
        if ratio >= self.danger_at:
            return settings.DANGER
        return self.color

    def draw(self, surface: pygame.Surface) -> None:
        rect = self.rect
        color = self._current_color()

        text.draw(surface, self.label, (rect.x, rect.y), 18, settings.DIM, shadow=False)

        track = pygame.Rect(rect.x, rect.y + 22, rect.width, 14)
        pygame.draw.rect(surface, (10, 16, 30), track, border_radius=6)
        pygame.draw.rect(surface, settings.PANEL_EDGE, track, 1, border_radius=6)

        fill_width = int(track.width * self.ratio)
        if fill_width > 2:
            fill = pygame.Rect(track.x + 1, track.y + 1, fill_width - 2, track.height - 2)
            pygame.draw.rect(surface, color, fill, border_radius=5)
            highlight = pygame.Rect(fill.x, fill.y, fill.width, max(1, fill.height // 3))
            pygame.draw.rect(
                surface,
                tuple(min(255, channel + 40) for channel in color),
                highlight,
                border_radius=3,
            )

        # threshold tick
        tick_x = track.x + int(track.width * self.danger_at)
        pygame.draw.line(surface, settings.FAINT, (tick_x, track.y - 2), (tick_x, track.bottom + 2), 1)

        if self.show_value:
            text.draw(
                surface,
                self.display_value,
                (track.right, rect.y),
                18,
                color,
                right=True,
                shadow=False,
            )
