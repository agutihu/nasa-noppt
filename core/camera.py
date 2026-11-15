"""Small smooth camera for the scrolling levels."""

from __future__ import annotations

import pygame

from core import settings


class Camera:
    def __init__(self, world_w: int, world_h: int, view_w: int = settings.WIDTH, view_h: int = settings.HEIGHT) -> None:
        self.world_w = max(view_w, int(world_w))
        self.world_h = max(view_h, int(world_h))
        self.view_w = int(view_w)
        self.view_h = int(view_h)
        self.pos = pygame.Vector2(0, 0)

    @property
    def offset(self) -> tuple[int, int]:
        return int(self.pos.x), int(self.pos.y)

    def clamp(self, x: float, y: float) -> pygame.Vector2:
        return pygame.Vector2(
            max(0, min(self.world_w - self.view_w, x)),
            max(0, min(self.world_h - self.view_h, y)),
        )

    def snap(self, target: tuple[float, float]) -> None:
        self.pos = self.clamp(target[0] - self.view_w / 2, target[1] - self.view_h / 2)

    def follow(self, target: tuple[float, float], dt: float, *, lerp: float = 7.0) -> None:
        wanted = self.clamp(target[0] - self.view_w / 2, target[1] - self.view_h / 2)
        blend = min(1.0, max(0.0, lerp * dt))
        self.pos += (wanted - self.pos) * blend

    def to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        return int(point[0] - self.pos.x), int(point[1] - self.pos.y)

    def visible(self, rect: pygame.Rect) -> bool:
        return rect.colliderect(pygame.Rect(int(self.pos.x), int(self.pos.y), self.view_w, self.view_h))
