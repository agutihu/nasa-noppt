"""Procedural planet rendering: discs, bands, craters, rings and the sun."""

from __future__ import annotations

import math
import random

import pygame


def _disc(size: int) -> tuple[pygame.Surface, pygame.Surface]:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    return surface, mask


def _apply_mask(layer: pygame.Surface, mask: pygame.Surface) -> pygame.Surface:
    masked = layer.copy()
    masked.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return masked


def planet_surface(
    radius: int,
    color: tuple[int, int, int],
    *,
    band_color: tuple[int, int, int] | None = None,
    bands: int = 0,
    craters: int = 0,
    seed: int = 1,
    shade: bool = True,
) -> pygame.Surface:
    """Render a planet once and cache-friendly reuse the surface."""
    radius = max(4, int(radius))
    size = radius * 2
    disc, mask = _disc(size)
    pygame.draw.circle(disc, color, (radius, radius), radius)

    rng = random.Random(seed)

    if bands and band_color:
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        for index in range(bands):
            y = radius * 0.25 + index * (radius * 1.5 / max(1, bands))
            height = rng.randint(max(2, radius // 7), max(3, radius // 4))
            width = int(radius * 2.1)
            rect = pygame.Rect(radius - width // 2, int(y), width, height)
            pygame.draw.ellipse(layer, (*band_color, 190), rect)
        disc.blit(_apply_mask(layer, mask), (0, 0))

    if craters:
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        for _ in range(craters):
            angle = rng.uniform(0, math.tau)
            dist = rng.uniform(0, radius * 0.7)
            cx = int(radius + math.cos(angle) * dist)
            cy = int(radius + math.sin(angle) * dist)
            crater_r = rng.randint(max(2, radius // 9), max(3, radius // 5))
            pygame.draw.circle(layer, (0, 0, 0, 70), (cx, cy), crater_r)
            pygame.draw.circle(layer, (255, 255, 255, 26), (cx - 1, cy - 1), max(1, crater_r - 2))
        disc.blit(_apply_mask(layer, mask), (0, 0))

    if shade:
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            layer, (0, 0, 10, 165), (int(radius * 1.42), int(radius * 1.32)), radius
        )
        pygame.draw.circle(layer, (255, 255, 255, 40), (int(radius * 0.62), int(radius * 0.58)), int(radius * 0.42))
        disc.blit(_apply_mask(layer, mask), (0, 0))

    return disc


_planet_cache: dict[tuple, pygame.Surface] = {}


def draw_planet(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    *,
    band_color: tuple[int, int, int] | None = None,
    bands: int = 0,
    craters: int = 0,
    seed: int = 1,
    ring: bool = False,
    ring_color: tuple[int, int, int] = (210, 200, 170),
) -> None:
    key = (radius, color, band_color, bands, craters, seed)
    disc = _planet_cache.get(key)
    if disc is None:
        disc = planet_surface(
            radius, color, band_color=band_color, bands=bands, craters=craters, seed=seed
        )
        if len(_planet_cache) > 64:
            _planet_cache.clear()
        _planet_cache[key] = disc

    if ring:
        pygame.draw.ellipse(
            surface,
            ring_color,
            pygame.Rect(
                center[0] - int(radius * 2.0),
                center[1] - int(radius * 0.55),
                int(radius * 4.0),
                int(radius * 1.1),
            ),
            2,
        )

    surface.blit(disc, (center[0] - radius, center[1] - radius))

    if ring:
        # front half of the ring drawn over the disc
        clip = pygame.Rect(
            center[0] - int(radius * 2.0),
            center[1],
            int(radius * 4.0),
            int(radius * 0.6) + 2,
        )
        previous = surface.get_clip()
        surface.set_clip(clip)
        pygame.draw.ellipse(
            surface,
            ring_color,
            pygame.Rect(
                center[0] - int(radius * 2.0),
                center[1] - int(radius * 0.55),
                int(radius * 4.0),
                int(radius * 1.1),
            ),
            2,
        )
        surface.set_clip(previous)


def draw_sun(surface: pygame.Surface, center: tuple[int, int], radius: int, t: float = 0.0) -> None:
    cx, cy = center
    pulse = 1.0 + 0.04 * math.sin(t * 2.1)
    r = max(3, int(radius * pulse))

    halo_size = int(r * 2.6)
    halo = pygame.Surface((halo_size, halo_size), pygame.SRCALPHA)
    for index in range(10, 0, -1):
        alpha = 8 + (10 - index) * 4
        pygame.draw.circle(
            halo, (255, 176, 74, alpha), (halo_size // 2, halo_size // 2), int(r * index / 8)
        )
    surface.blit(halo, (cx - halo_size // 2, cy - halo_size // 2))

    pygame.draw.circle(surface, (255, 186, 84), (cx, cy), r)
    pygame.draw.circle(surface, (255, 236, 180), (cx, cy), int(r * 0.72))
    pygame.draw.circle(surface, (255, 252, 226), (cx, cy), max(1, int(r * 0.42)))


def draw_orbit(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int] = (40, 60, 96),
    dashed: int = 0,
) -> None:
    if dashed <= 0:
        pygame.draw.circle(surface, color, center, radius, 1)
        return
    steps = max(24, int(math.tau * radius / 26))
    for index in range(steps):
        if index % 2:
            continue
        a0 = math.tau * index / steps
        a1 = math.tau * (index + 0.7) / steps
        p0 = (center[0] + math.cos(a0) * radius, center[1] + math.sin(a0) * radius)
        p1 = (center[0] + math.cos(a1) * radius, center[1] + math.sin(a1) * radius)
        pygame.draw.line(surface, color, p0, p1, 1)
