"""Player controller.

``Player`` holds health, damage and drawing. Movement is added by a small subclass so the
Mars platformer can reuse the same health/invulnerability rules without a rewrite.
"""

from __future__ import annotations

import math

import pygame

from art import sprites
from core import audio


class Player:
    BODY = (26, 34)

    def __init__(self, x: float, y: float, cfg: dict, state, hud=None) -> None:
        self.cfg = cfg or {}
        self.state = state
        self.hud = hud
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()
        self.rect = pygame.Rect(0, 0, *self.BODY)
        self.rect.center = (round(x), round(y))
        self.facing = 1
        self.t = 0.0
        self.moving = False
        self.max_health = max(1, int(state.hearts()))
        self.health = self.max_health
        self.invuln = 0.0
        self.dead = False
        self._sync_hud()

    # --- health -------------------------------------------------------------
    def _sync_hud(self) -> None:
        if self.hud is not None:
            self.hud.set_hearts(self.health, self.max_health)

    @property
    def invulnerable(self) -> bool:
        return self.invuln > 0.0

    def take_damage(self, amount: int = 1, *, flash: float = 1.0) -> bool:
        """Return True when this hit kills the player."""
        if self.dead or self.invulnerable or amount <= 0:
            return False
        self.health = max(0, self.health - amount)
        self.invuln = flash
        audio.play("hit")
        self._sync_hud()
        if self.health <= 0:
            self.dead = True
            audio.play("lose")
        return self.dead

    def heal(self, amount: int = 1) -> None:
        if self.dead or amount <= 0:
            return
        self.health = min(self.max_health, self.health + amount)
        self._sync_hud()

    def respawn(self, x: float, y: float, *, restore: bool = True) -> None:
        self.pos.update(x, y)
        self.vel.update(0, 0)
        self.rect.center = (round(x), round(y))
        self.invuln = 1.2
        self.dead = False
        if restore:
            self.health = self.max_health
        self._sync_hud()

    # --- shared update ------------------------------------------------------
    def tick(self, dt: float) -> None:
        self.t += dt
        self.invuln = max(0.0, self.invuln - dt)

    def apply_motion(
        self,
        direction: pygame.Vector2,
        speed: float,
        accel: float,
        friction: float,
        dt: float,
    ) -> None:
        """Velocity-based movement with acceleration, used by every controller."""
        if direction.length_squared() > 0:
            direction = direction.normalize()
            target = direction * speed
            blend = min(1.0, accel * dt / max(1.0, speed))
            self.vel += (target - self.vel) * blend
        else:
            drop = friction * dt
            if self.vel.length() <= drop:
                self.vel.update(0, 0)
            else:
                self.vel -= self.vel.normalize() * drop

        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.moving = self.vel.length_squared() > 400.0
        if abs(self.vel.x) > 20:
            self.facing = 1 if self.vel.x > 0 else -1

    def clamp_to(self, bounds: pygame.Rect) -> None:
        self.pos.x = max(bounds.left, min(bounds.right, self.pos.x))
        self.pos.y = max(bounds.top, min(bounds.bottom, self.pos.y))
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        flashing = self.invulnerable and int(self.invuln * 14) % 2 == 0
        sprites.draw_astronaut(
            screen,
            (round(self.pos.x), round(self.pos.y)),
            self.t,
            moving=self.moving,
            facing=self.facing,
            hurt=1.0 if flashing else 0.0,
        )


class TopDownPlayer(Player):
    """Eight-direction jetpack movement with drift, used by the tutorial and Mercury."""

    def __init__(self, x: float, y: float, cfg: dict, state, hud=None) -> None:
        super().__init__(x, y, cfg, state, hud)
        self.speed = float(cfg.get("move_speed", 260))
        self.accel = float(cfg.get("accel", 1150))
        self.friction = float(cfg.get("friction", 620))

    def update(self, dt: float, keys, bounds: pygame.Rect | None = None) -> None:
        self.tick(dt)
        if self.dead:
            return
        direction = pygame.Vector2(
            float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        speed = self.state.scale_speed(self.speed)
        self.apply_motion(direction, speed, self.accel, self.friction, dt)
        if bounds is not None:
            self.clamp_to(bounds)


class PlatformerPlayer(Player):
    """Side-on controller with gravity, variable jump height and coyote time.

    Gravity comes from the level JSON so Mars uses its real 3.71 m/s² feel.
    """

    def __init__(self, x: float, y: float, cfg: dict, state, hud=None) -> None:
        super().__init__(x, y, cfg, state, hud)
        self.speed = float(cfg.get("move_speed", 260))
        self.accel = float(cfg.get("accel", 1800))
        self.friction = float(cfg.get("friction", 2200))
        self.gravity = float(cfg.get("gravity_px", 900))
        self.jump_speed = float(cfg.get("jump_speed", 520))
        self.hold_boost = float(cfg.get("hold_boost", 0.55))
        self.on_ground = False
        self.coyote = 0.0
        self.jump_held = 0.0

    def jump(self) -> None:
        if self.on_ground or self.coyote > 0.0:
            self.vel.y = -self.jump_speed
            self.on_ground = False
            self.coyote = 0.0
            self.jump_held = 0.22
            audio.play("jump")

    def update(self, dt: float, keys, bounds: pygame.Rect | None = None, solids=None) -> None:
        self.tick(dt)
        if self.dead:
            return

        direction = pygame.Vector2(
            float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            0,
        )
        speed = self.state.scale_speed(self.speed)
        if direction.length_squared() > 0:
            self.vel.x += direction.x * self.accel * dt
            self.vel.x = max(-speed, min(speed, self.vel.x))
        else:
            drop = self.friction * dt
            if abs(self.vel.x) <= drop:
                self.vel.x = 0.0
            else:
                self.vel.x -= math.copysign(drop, self.vel.x)

        # higher jump while the key is held
        if self.jump_held > 0.0:
            self.jump_held = max(0.0, self.jump_held - dt)
            if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel.y -= self.gravity * self.hold_boost * dt

        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt

        if bounds is not None:
            self.clamp_to(bounds)
        if solids:
            self._resolve_platforms(solids)

        if self.on_ground:
            self.coyote = 0.12
        else:
            self.coyote = max(0.0, self.coyote - dt)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.moving = abs(self.vel.x) > 20 or not self.on_ground
        if abs(self.vel.x) > 20:
            self.facing = 1 if self.vel.x > 0 else -1

    def _resolve_platforms(self, solids) -> None:
        was_ground = False
        for solid in solids:
            if not self.rect.colliderect(solid):
                continue
            if self.vel.y > 0 and self.rect.bottom - self.vel.y * 0.0 <= solid.top + 18:
                self.rect.bottom = solid.top
                self.pos.y = self.rect.centery
                self.vel.y = 0.0
                was_ground = True
            elif self.vel.y < 0 and self.rect.top >= solid.top:
                self.rect.top = solid.bottom
                self.pos.y = self.rect.centery
                self.vel.y = 0.0
        self.on_ground = was_ground
