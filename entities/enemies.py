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
    """Enemy bolt: straight line, dies on leaving bounds or hitting the player."""

    def __init__(self, pos, direction, speed=170, radius=4, color=None) -> None:
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(direction).normalize() * speed
        self.radius = radius
        self.color = color or settings.WARN
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
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        trail = (int(cx - self.vel.x * 0.05), int(cy - self.vel.y * 0.05))
        pygame.draw.line(screen, self.color, trail, (cx, cy), 2)
        pygame.draw.circle(screen, self.color, (cx, cy), self.radius)

    def collides_player(self, player) -> bool:
        return self.rect.colliderect(player.rect)


class Walker:
    """Ground alien: patrols its home range and charges when the player gets close."""

    def __init__(self, spec: dict, cfg: dict, state, color=(96, 200, 120)) -> None:
        params = cfg.get("params", {})
        self.speed = state.scale_speed(float(params.get("walker_speed", 70)))
        self.charge_speed = state.scale_speed(float(params.get("walker_charge", 135)))
        self.home = pygame.Vector2(spec["x"], spec["y"])
        self.range = float(spec.get("range", 100))
        self.pos = pygame.Vector2(self.home)
        self.facing = 1
        self.color = color
        self.hp = 1
        self.dead = False
        self.t = 0.0
        self.charging = False
        self.rect = pygame.Rect(0, 0, 24, 18)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self, dt: float, player) -> None:
        if self.dead or player.dead:
            self.charging = False
            return
        self.t += dt
        near = (
            abs(player.pos.x - self.pos.x) < 240
            and abs(player.pos.y - self.pos.y) < 90
        )
        if near:
            direction = 1 if player.pos.x > self.pos.x else -1
            self.pos.x += direction * self.charge_speed * dt
            self.facing = direction
            self.charging = True
        else:
            offset = self.pos.x - self.home.x
            if offset > self.range:
                self.facing = -1
            elif offset < -self.range:
                self.facing = 1
            self.pos.x += self.facing * self.speed * dt
            self.charging = False
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        if self.dead:
            return
        sprites.draw_alien(
            screen,
            (int(self.rect.centerx - camera[0]), int(self.rect.centery - camera[1])),
            self.t,
            color=self.color,
            radius=11,
            facing=self.facing,
            moving=self.charging,
        )

    def collides_player(self, player) -> bool:
        return not self.dead and self.rect.colliderect(player.rect)

    def hit(self) -> bool:
        """One stomp or laser shot kills a walker. Returns True when it dies."""
        self.hp -= 1
        if self.hp <= 0:
            self.dead = True
            audio.play("boom", 0.7)
        else:
            audio.play("hit", 0.5)
        return self.dead


class UFO:
    """Alien saucer: patrols the sky, dives at the player's altitude and fires plasma."""

    def __init__(self, spec: dict, cfg: dict, state, color=(150, 170, 200)) -> None:
        params = cfg.get("params", {})
        self.speed = state.scale_speed(float(params.get("ufo_speed", 60)))
        self.fire_interval = max(1.0, float(params.get("ufo_fire_interval", 2.2)))
        self.plasma_speed = state.scale_speed(float(params.get("plasma_speed", 210)))
        self.home = pygame.Vector2(spec["x"], spec["y"])
        self.range = float(spec.get("range", 110))
        self.pos = pygame.Vector2(self.home)
        self.base_y = float(spec["y"])
        self.facing = 1
        self.color = color
        self.hp = 2
        self.dead = False
        self.t = 0.0
        self.timer = 0.0
        self.charge = 0.0
        self.rect = pygame.Rect(0, 0, 34, 16)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self, dt: float, player) -> Projectile | None:
        if self.dead:
            return None
        self.t += dt

        offset = self.pos.x - self.home.x
        if offset > self.range:
            self.facing = -1
        elif offset < -self.range:
            self.facing = 1
        self.pos.x += self.facing * self.speed * dt
        self.pos.y = self.base_y + math.sin(self.t * 2.2) * 12.0
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if player.dead:
            self.charge = 0.0
            return None
        distance = math.hypot(player.pos.x - self.pos.x, player.pos.y - self.pos.y)
        if distance > 460:
            self.charge = max(0.0, self.charge - dt * 0.8)
            return None

        self.timer += dt
        self.charge = min(1.0, self.timer / self.fire_interval)
        if self.timer >= self.fire_interval:
            self.timer = 0.0
            direction = pygame.Vector2(player.pos) - self.pos
            if direction.length_squared() > 0:
                audio.play("laser", 0.5)
                return Projectile(
                    self.pos + direction.normalize() * 14,
                    direction,
                    self.plasma_speed,
                    radius=4,
                    color=(255, 120, 90),
                )
        return None

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        if self.dead:
            return
        sprites.draw_ufo(
            screen,
            (int(self.rect.centerx - camera[0]), int(self.rect.centery - camera[1])),
            self.t,
            color=self.color,
            radius=15,
            charging=self.charge,
        )

    def collides_player(self, player) -> bool:
        return not self.dead and self.rect.colliderect(player.rect)

    def hit(self) -> bool:
        """Two laser shots kill a saucer; a stomp counts as two."""
        self.hp -= 2
        if self.hp <= 0:
            self.dead = True
            audio.play("boom", 0.8)
        else:
            audio.play("hit", 0.5)
        return self.dead


class LaserBolt(Projectile):
    """Player blaster shot: fast, glowing, short-lived."""

    def __init__(self, pos, direction, speed: float = 560) -> None:
        super().__init__(pos, direction, speed, radius=3, color=settings.ACCENT)
        self.life = 0.85

    def update(self, dt: float, bounds: pygame.Rect) -> None:
        super().update(dt, bounds)
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        trail = (int(cx - self.vel.x * 0.045), int(cy - self.vel.y * 0.045))
        pygame.draw.line(screen, (220, 255, 250), trail, (cx, cy), 2)
        pygame.draw.circle(screen, self.color, (cx, cy), self.radius + 1)
