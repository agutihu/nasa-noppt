"""Ambient per-planet weather: rain, dust, snow, shimmer and lightning.

Weather is screen-space: it drifts with the wind and parallaxes a little against the
camera, so a planet feels like a place with an atmosphere rather than a static level.
Damage still comes from the world's hazards; this layer is atmosphere only.
"""

from __future__ import annotations

import math
import random

import pygame

from core import audio, settings


class Weather:
    """Particle weather + haze overlay, configured from the level JSON ``weather`` key."""

    def __init__(self, config: dict | None) -> None:
        cfg = config or {}
        self.kind = str(cfg.get("type", "none"))
        self.density = int(cfg.get("density", 0))
        self.wind = tuple(cfg.get("wind", (0.0, 0.0)))
        self.color = tuple(cfg.get("color", (255, 255, 255, 120)))
        self.haze = tuple(cfg.get("haze", (0, 0, 0, 0)))
        self.lightning = bool(cfg.get("lightning", False))
        self.meteors = bool(cfg.get("meteors", False))

        self.t = 0.0
        self.flash = 0.0
        self.flash_timer = random.uniform(4.0, 9.0)
        self.particles: list[dict] = []
        self.meteor_streaks: list[dict] = []

        rng = random.Random(hash(self.kind) & 0xFFFF)
        for _ in range(self.density):
            self.particles.append(self._spawn(rng, random_y=True))

    # --- particles ----------------------------------------------------------
    def _spawn(self, rng: random.Random, *, random_y: bool) -> dict:
        vx, vy = self.wind
        if self.kind in ("acid_rain", "storm_rain", "wind_rain"):
            return {
                "x": rng.uniform(0, settings.WIDTH),
                "y": rng.uniform(-40, settings.HEIGHT) if random_y else -20,
                "vx": vx * rng.uniform(0.7, 1.3),
                "vy": max(180.0, abs(vy) + 240.0) * rng.uniform(0.8, 1.3),
                "size": rng.uniform(6, 16),
            }
        if self.kind in ("snow", "ice_glitter"):
            return {
                "x": rng.uniform(0, settings.WIDTH),
                "y": rng.uniform(0, settings.HEIGHT) if random_y else -10,
                "vx": vx * rng.uniform(0.4, 1.0),
                "vy": rng.uniform(28, 70),
                "size": rng.uniform(1.5, 3.4),
                "phase": rng.uniform(0, math.tau),
            }
        if self.kind == "heat":
            return {
                "x": rng.uniform(0, settings.WIDTH),
                "y": rng.uniform(0, settings.HEIGHT) if random_y else settings.HEIGHT + 10,
                "vx": rng.uniform(-8, 8),
                "vy": -rng.uniform(40, 90),
                "size": rng.uniform(10, 26),
                "phase": rng.uniform(0, math.tau),
            }
        # dust and fallback
        return {
            "x": rng.uniform(0, settings.WIDTH),
            "y": rng.uniform(0, settings.HEIGHT) if random_y else rng.uniform(0, settings.HEIGHT),
            "vx": vx * rng.uniform(0.6, 1.4),
            "vy": vy * rng.uniform(0.4, 1.2) + rng.uniform(-6, 6),
            "size": rng.uniform(1.5, 4.0),
        }

    # --- update -------------------------------------------------------------
    def update(self, dt: float, camera_dx: float = 0.0) -> None:
        self.t += dt
        parallax = camera_dx * 0.25

        if self.lightning:
            self.flash = max(0.0, self.flash - dt * 2.2)
            self.flash_timer -= dt
            if self.flash_timer <= 0.0:
                self.flash_timer = random.uniform(3.5, 8.0)
                self.flash = 1.0
                if self.flash > 0:
                    audio.play("boom", 0.22)

        if self.meteors:
            if random.random() < dt * 0.5:
                self.meteor_streaks.append(
                    {
                        "x": random.uniform(0, settings.WIDTH),
                        "y": random.uniform(0, 180),
                        "vx": -random.uniform(320, 520),
                        "vy": random.uniform(120, 220),
                        "life": 0.9,
                    }
                )
            for streak in self.meteor_streaks:
                streak["x"] += streak["vx"] * dt
                streak["y"] += streak["vy"] * dt
                streak["life"] -= dt
            self.meteor_streaks = [s for s in self.meteor_streaks if s["life"] > 0]

        for particle in self.particles:
            particle["x"] += (particle["vx"] - parallax) * dt
            particle["y"] += particle["vy"] * dt
            if "phase" in particle:
                particle["phase"] += dt * 3.0

            margin = 60
            if particle["x"] < -margin:
                particle["x"] += settings.WIDTH + margin * 2
            elif particle["x"] > settings.WIDTH + margin:
                particle["x"] -= settings.WIDTH + margin * 2
            if particle["y"] > settings.HEIGHT + margin:
                particle["y"] = -margin
                particle["x"] = random.uniform(0, settings.WIDTH)
            elif particle["y"] < -margin and self.kind == "heat":
                particle["y"] = settings.HEIGHT + 10
                particle["x"] = random.uniform(0, settings.WIDTH)

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        if self.kind == "none" or not self.particles:
            return

        if self.kind in ("acid_rain", "storm_rain", "wind_rain"):
            color = self.color[:3]
            alpha = self.color[3] if len(self.color) > 3 else 120
            layer = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            for particle in self.particles:
                end_x = particle["x"] - particle["vx"] * 0.06
                end_y = particle["y"] - particle["size"]
                pygame.draw.line(
                    layer,
                    (*color, alpha),
                    (particle["x"], particle["y"]),
                    (end_x, end_y),
                    1,
                )
            screen.blit(layer, (0, 0))
        elif self.kind in ("snow", "ice_glitter"):
            layer = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            color = self.color[:3]
            base_alpha = self.color[3] if len(self.color) > 3 else 150
            for particle in self.particles:
                twinkle = 0.55 + 0.45 * abs(math.sin(particle.get("phase", 0.0)))
                wobble = math.sin(particle.get("phase", 0.0)) * 6
                alpha = int(base_alpha * twinkle)
                pygame.draw.circle(
                    layer,
                    (*color, alpha),
                    (int(particle["x"] + wobble), int(particle["y"])),
                    max(1, int(particle["size"])),
                )
            screen.blit(layer, (0, 0))
        elif self.kind == "heat":
            layer = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            color = self.color[:3] or (255, 140, 60)
            for particle in self.particles:
                wobble = math.sin(particle.get("phase", 0.0)) * 8
                rect = pygame.Rect(
                    int(particle["x"] + wobble),
                    int(particle["y"]),
                    int(particle["size"]),
                    int(particle["size"] * 0.5),
                )
                pygame.draw.ellipse(layer, (*color, 40), rect)
            screen.blit(layer, (0, 0))
            for streak in self.meteor_streaks:
                tail = (streak["x"] - streak["vx"] * 0.08, streak["y"] - streak["vy"] * 0.08)
                pygame.draw.line(screen, (255, 220, 170), (streak["x"], streak["y"]), tail, 2)
        else:  # dust
            layer = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            color = self.color[:3]
            alpha = self.color[3] if len(self.color) > 3 else 90
            for particle in self.particles:
                pygame.draw.circle(
                    layer,
                    (*color, alpha),
                    (int(particle["x"]), int(particle["y"])),
                    max(1, int(particle["size"])),
                )
            screen.blit(layer, (0, 0))

        # haze is drawn separately via draw_haze() so it tints the world softly
        if self.flash > 0:
            flash_layer = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            flash_layer.fill((235, 240, 255, int(120 * self.flash)))
            screen.blit(flash_layer, (0, 0))

    def draw_haze(self, screen: pygame.Surface) -> None:
        """Translucent tint over the world — the planet's atmosphere."""
        if len(self.haze) == 4 and self.haze[3] > 0:
            veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            veil.fill(self.haze)
            screen.blit(veil, (0, 0))
