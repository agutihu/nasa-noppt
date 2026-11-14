"""Collectibles: ship parts, crates, health, cooling canisters."""

from __future__ import annotations

import math

import pygame

from art import sprites
from core import settings


class Pickup:
    def __init__(
        self,
        pos: tuple[float, float],
        kind: str = "part",
        *,
        color: tuple[int, int, int] = settings.ACCENT,
        payload: str | None = None,
        radius: int = 14,
        label: str = "",
    ) -> None:
        self.pos = pygame.Vector2(pos)
        self.kind = kind
        self.color = color
        self.payload = payload
        self.radius = radius
        self.label = label
        self.taken = False
        self.t = 0.0
        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self._sync_rect()

    def _sync_rect(self) -> None:
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self, dt: float) -> None:
        self.t += dt

    def collides(self, rect: pygame.Rect) -> bool:
        return not self.taken and self.rect.colliderect(rect)

    @property
    def center(self) -> tuple[int, int]:
        return (round(self.pos.x), round(self.pos.y))

    def draw(self, surface: pygame.Surface) -> None:
        if self.taken:
            return
        bob = math.sin(self.t * 3.0) * 3
        center = (self.center[0], int(self.center[1] + bob))

        if self.kind == "crate":
            size = self.radius
            rect = pygame.Rect(0, 0, size, size)
            rect.center = center
            pygame.draw.rect(surface, (92, 74, 58), rect, border_radius=3)
            pygame.draw.rect(surface, (170, 140, 104), rect, 1, border_radius=3)
            pygame.draw.line(surface, (170, 140, 104), (rect.left + 3, rect.centery), (rect.right - 3, rect.centery), 1)
            pygame.draw.line(surface, (170, 140, 104), (rect.centerx, rect.top + 3), (rect.centerx, rect.bottom - 3), 1)
        elif self.kind == "health":
            sprites.draw_heart(surface, center, self.radius * 2, filled=True)
        else:
            sprites.draw_part(surface, center, self.radius, self.color, self.t)

        if self.label:
            shadow = self.radius + 12
            pygame.draw.circle(surface, (10, 16, 28), center, shadow, 1)
