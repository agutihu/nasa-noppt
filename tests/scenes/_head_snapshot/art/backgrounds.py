"""Procedural backgrounds: starfields, nebulae and screen overlays."""

from __future__ import annotations

import math
import random

import pygame

from core import settings

_field_cache: dict[tuple[int, int, int], pygame.Surface] = {}
_nebula_cache: dict[tuple[int, int, int], pygame.Surface] = {}


def starfield(width: int, height: int, seed: int = 7, density: float = 1.0) -> pygame.Surface:
    key = (width, height, seed)
    cached = _field_cache.get(key)
    if cached is not None:
        return cached

    rng = random.Random(seed)
    surface = pygame.Surface((width, height)).convert()
    surface.fill(settings.SPACE_DEEP)

    # soft vertical band of deep blue so the sky is not flat black
    for y in range(0, height, 4):
        shade = int(6 + 10 * math.sin(math.pi * y / max(1, height)))
        pygame.draw.rect(surface, (3, 6 + shade // 3, 14 + shade), (0, y, width, 4))

    count = int(170 * density)
    for _ in range(count):
        x = rng.randrange(width)
        y = rng.randrange(height)
        radius = rng.choice((1, 1, 1, 2, 2, 3))
        brightness = rng.randrange(90, 256)
        tint = rng.choice(((255, 255, 255), (200, 220, 255), (255, 230, 200), (170, 220, 255)))
        color = tuple(min(255, int(channel * brightness / 255)) for channel in tint)
        pygame.draw.circle(surface, color, (x, y), radius)

    _field_cache[key] = surface
    return surface


def nebula(width: int, height: int, seed: int = 3) -> pygame.Surface:
    key = (width, height, seed)
    cached = _nebula_cache.get(key)
    if cached is not None:
        return cached

    rng = random.Random(seed)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    tints = ((56, 92, 180), (120, 70, 180), (40, 150, 160), (180, 90, 120))
    for _ in range(11):
        tint = rng.choice(tints)
        cx = rng.randrange(-100, width + 100)
        cy = rng.randrange(-60, height + 60)
        base_radius = rng.randrange(90, 260)
        for layer in range(7):
            radius = int(base_radius * (1.0 - layer * 0.12))
            alpha = int(14 + layer * 4)
            pygame.draw.circle(surface, (*tint, alpha), (cx, cy), radius)

    _nebula_cache[key] = surface
    return surface


def vignette(width: int, height: int, strength: int = 150) -> pygame.Surface:
    """Darkened edges, built once at a low resolution and scaled up."""
    small_w, small_h = max(8, width // 8), max(8, height // 8)
    small = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
    cx, cy = small_w / 2, small_h / 2
    max_dist = math.hypot(cx, cy)
    for y in range(small_h):
        for x in range(small_w):
            dist = math.hypot(x - cx, y - cy) / max_dist
            alpha = int(max(0.0, dist - 0.55) * 2.2 * strength)
            if alpha > 0:
                small.set_at((x, y), (0, 0, 0, min(255, alpha)))
    return pygame.transform.smoothscale(small, (width, height))


def scanlines(width: int, height: int, alpha: int = 18) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, 3):
        pygame.draw.line(surface, (0, 0, 0, alpha), (0, y), (width, y))
    return surface


def glow(surface: pygame.Surface, center: tuple[int, int], radius: int, color, layers: int = 6) -> None:
    """Additive-ish halo made of concentric translucent circles."""
    halo = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for index in range(layers, 0, -1):
        alpha = int(16 + (layers - index) * 5)
        pygame.draw.circle(halo, (*color, alpha), (radius, radius), int(radius * index / layers))
    surface.blit(halo, (center[0] - radius, center[1] - radius))


def darken(surface: pygame.Surface, amount: int) -> None:
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, max(0, min(255, amount))))
    surface.blit(veil, (0, 0))
