"""Shared enemies and projectiles for the platformer / shooter levels."""

from __future__ import annotations

import math

import pygame

from art import sprites
from core import audio, settings


class Chaser:
    """Slowly follows the player. Dies when stomped; hurts on touch."""

    def __init__(self, pos: tuple[float, float], cfg: dict, state) -> None:
        params = cfg.get("params", {})
        self.speed = state.scale_speed(float(params.get("chaser_speed", 40)))
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = pos
        self.pos = pygame.Vector2(pos)
        self.hp = 2
        self.dead = False
        self.t = 0.0

    def update(self, dt: float, player, bounds: pygame.Rect | None = None) -> None:
        if self.dead or player.dead:
            return
        self.t += dt
        direction = player.pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if bounds is not None:
            self.rect.clamp_ip(bounds)
            self.pos.x, self.pos.y = self.rect.center

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        if self.dead:
            return
        sprites.draw_drone(
            screen,
            (self.rect.x - camera[0], self.rect.y - camera[1]),
            self.t,
            radius=10,
            hostile=True,
        )

    def collides_player(self, player) -> bool:
        return not self.dead and self.rect.colliderect(player.rect)

    def stomped(self) -> None:
        self.hp -= 1
        audio.play("pickup", 0.6)
        if self.hp <= 0:
            self.dead = True
            audio.play("win")


class Patrol:
    """Walks a fixed path between two points; touching causes damage."""

    def __init__(
        self, a: tuple[float, float], b: tuple[float, float], cfg: dict, state
    ) -> None:
        params = cfg.get("params", {})
        self.speed = state.scale_speed(float(params.get("patrol_speed", 50)))
        self.a = pygame.Vector2(a)
        self.b = pygame.Vector2(b)
        self.pos = pygame.Vector2(a)
        self.target = self.b.copy()
        self.rect = pygame.Rect(0, 0, 20, 12)
        self.rect.center = a
        self.dead = False
        self.t = 0.0

    def update(self, dt: float, player) -> None:
        if self.dead:
            return
        self.t += dt
        direction = self.target - self.pos
        if direction.length_squared() > 1.0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt
        else:
            self.target = self.b if self.target == self.a else self.a
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        if self.dead:
            return
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        pygame.draw.line(screen, settings.DANGER, self.a - camera, self.b - camera, 1)
        sprites.draw_drone(screen, (cx, cy), self.t, radius=9, hostile=True)

    def collides_player(self, player) -> bool:
        return not self.dead and self.rect.colliderect(player.rect)


class Turret:
    """Stationary, fires a projectile every N seconds in a fixed direction."""

    def __init__(self, pos: tuple[float, float], direction, fire_interval: float = 2.4, speed: float = 170) -> None:
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction).normalize()
        self.fire_interval = max(0.4, float(fire_interval))
        self.speed = speed
        self.timer = 0.0
        self.dead = False
        self.rect = pygame.Rect(0, 0, 22, 14)
        self.rect.center = pos

    def update(self, dt: float, player_pos) -> Projectile | None:
        self.timer += dt
        if self.timer >= self.fire_interval:
            self.timer = 0.0
            return Projectile(self.pos, self.direction, self.speed)
        return None

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        pygame.draw.rect(screen, (92, 74, 58), self.rect.move(-camera[0], -camera[1]), border_radius=3)
        pygame.draw.rect(screen, (170, 140, 104), self.rect.move(-camera[0], -camera[1]), 1, border_radius=3)
        end = (int(cx + self.direction.x * 22), int(cy + self.direction.y * 22))
        pygame.draw.line(screen, settings.WARN, (cx, cy), end, 3)

    def collides_player(self, player) -> bool:
        return self.rect.colliderect(player.rect)


class Projectile:
    """Turret bullet: straight line, dies on leaving bounds or hitting player."""

    def __init__(self, pos, direction, speed=170, radius=4) -> None:
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(direction).normalize() * speed
        self.radius = radius
        self.dead = False
        self.t = 0.0
        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.rect.center = pos

    def update(self, dt: float, bounds: pygame.Rect) -> None:
        self.pos += self.vel * dt
        self.t += dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not bounds.contains(self.rect):
            self.dead = True

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        pygame.draw.circle(
            screen,
            settings.WARN,
            (self.rect.centerx - camera[0], self.rect.centery - camera[1]),
            self.radius,
        )

    def collides_player(self, player) -> bool:
        return self.rect.colliderect(player.rect)
