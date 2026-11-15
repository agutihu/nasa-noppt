"""Baked environment art: Mars outpost interior, Martian surface and lava tunnel.

Everything is procedural so the game still runs with an empty ``assets/`` folder.
Only the structural layer is baked; animated details (vents, rover, dust) are drawn
by the scenes on top.
"""

from __future__ import annotations

import math
import random

import pygame

from core import settings


def _gradient(width: int, height: int, top: tuple, bottom: tuple) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    for y in range(height):
        blend = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * blend) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


# --- outpost ----------------------------------------------------------------
def outpost_room(width: int = settings.WIDTH, height: int = settings.HEIGHT) -> pygame.Surface:
    """Interior of the Mars outpost: metal walls, a viewport, floor plates."""
    surface = _gradient(width, height, (26, 22, 30), (16, 14, 20))

    # wall band
    wall_h = 128
    pygame.draw.rect(surface, (44, 40, 50), (0, 0, width, wall_h))
    pygame.draw.rect(surface, (30, 28, 36), (0, 0, width, wall_h - 8))
    for x in range(0, width, 64):
        pygame.draw.line(surface, (54, 50, 62), (x, 0), (x, wall_h - 8), 1)
        pygame.draw.circle(surface, (66, 60, 72), (x + 8, 14), 2)
        pygame.draw.circle(surface, (66, 60, 72), (x + 8, wall_h - 20), 2)

    # viewport with a slice of Mars
    window = pygame.Rect(width // 2 - 170, 18, 340, 94)
    pygame.draw.rect(surface, (16, 14, 22), window.inflate(14, 14), border_radius=14)
    pygame.draw.rect(surface, (96, 84, 80), window.inflate(14, 14), 2, border_radius=14)
    sky = _gradient(window.width, window.height, (58, 28, 24), (150, 74, 44))
    surface.blit(sky, window.topleft)
    pygame.draw.circle(surface, (236, 190, 150), (window.x + 246, window.y + 34), 13)
    pygame.draw.polygon(
        surface,
        (176, 84, 48),
        [
            (window.x, window.bottom),
            (window.x + 40, window.y + 62),
            (window.x + 110, window.y + 76),
            (window.x + 190, window.y + 58),
            (window.x + 280, window.y + 72),
            (window.right, window.y + 64),
            (window.right, window.bottom),
        ],
    )
    pygame.draw.line(surface, (216, 150, 110), (window.x, window.bottom - 4), (window.right, window.bottom - 4), 2)

    # floor plates, slightly irregular so the room reads as built, not printed
    rng = random.Random(4)
    plate = 80
    for row, y in enumerate(range(wall_h, height, plate)):
        for col, x in enumerate(range(0, width, plate)):
            shade = 34 + (row + col) % 2 * 4 + rng.randint(-2, 2)
            pygame.draw.rect(surface, (shade, shade - 4, shade + 2), (x, y, plate, plate))
            pygame.draw.rect(surface, (20, 18, 24), (x, y, plate, plate), 1)
    for _ in range(260):
        x = rng.randrange(width)
        y = rng.randrange(wall_h, height)
        value = rng.randrange(24, 44)
        pygame.draw.circle(surface, (value, value - 3, value + 1), (x, y), rng.choice((1, 1, 2)))

    # safety stripe along the wall base
    for x in range(0, width, 48):
        pygame.draw.polygon(
            surface,
            settings.WARN if (x // 48) % 2 == 0 else (38, 32, 34),
            [(x, wall_h - 10), (x + 24, wall_h - 10), (x + 12, wall_h), (x - 12, wall_h)],
        )

    # overhead conduit + lights
    pygame.draw.line(surface, (70, 64, 74), (0, 6), (width, 6), 4)
    for x in range(90, width, 220):
        pygame.draw.rect(surface, (60, 56, 66), (x, 0, 44, 10), border_radius=3)
        glow = pygame.Surface((70, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 226, 180, 34), (0, 0, 70, 26))
        surface.blit(glow, (x - 13, 8))

    return surface


# --- martian surface --------------------------------------------------------
def mars_surface(
    width: int,
    height: int,
    *,
    seed: int = 11,
    boulders: int = 46,
    avoid: list[tuple[float, float, float]] | None = None,
) -> tuple[pygame.Surface, list[dict]]:
    """Top-down Martian ground with craters, dust streaks and boulders.

    Returns the baked surface and the boulder list so the scene can collide with
    exactly what the player sees.
    """
    rng = random.Random(seed)
    surface = _gradient(width, height, (146, 70, 44), (110, 48, 30))

    # broad dust patches
    for _ in range(70):
        cx = rng.randrange(width)
        cy = rng.randrange(height)
        radius = rng.randrange(120, 380)
        tint = rng.choice(((160, 88, 54), (128, 58, 36), (176, 104, 64)))
        patch = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(patch, (*tint, 26), (0, 0, radius * 2, int(radius * 1.3)))
        surface.blit(patch, (cx - radius, cy - int(radius * 0.65)))

    # wind streaks
    for _ in range(140):
        x = rng.randrange(width)
        y = rng.randrange(height)
        length = rng.randrange(30, 150)
        shade = rng.choice(((180, 104, 66, 40), (96, 40, 26, 40)))
        streak = pygame.Surface((length, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(streak, shade, (0, 0, length, 6))
        surface.blit(streak, (x, y))

    # craters
    for _ in range(26):
        cx = rng.randrange(80, width - 80)
        cy = rng.randrange(80, height - 80)
        radius = rng.randrange(26, 90)
        pygame.draw.ellipse(surface, (96, 42, 28), (cx - radius, cy - radius // 2, radius * 2, radius))
        pygame.draw.ellipse(surface, (72, 30, 20), (cx - radius, cy - radius // 2, radius * 2, radius), 3)
        pygame.draw.ellipse(
            surface,
            (176, 100, 62),
            (cx - radius + 6, cy - radius // 2 + 4, radius * 2 - 12, radius - 8),
            1,
        )

    # small pebbles
    for _ in range(700):
        x = rng.randrange(width)
        y = rng.randrange(height)
        shade = rng.randrange(70, 150)
        pygame.draw.circle(surface, (shade, shade // 2, shade // 3), (x, y), rng.choice((1, 1, 2)))

    # boulders (the only collision in the level)
    keep_clear = avoid or []
    rocks: list[dict] = []
    attempts = 0
    while len(rocks) < boulders and attempts < boulders * 40:
        attempts += 1
        radius = rng.randint(20, 46)
        x = rng.randrange(radius + 40, width - radius - 40)
        y = rng.randrange(radius + 40, height - radius - 40)
        if any(math.hypot(x - ax, y - ay) < ar + radius + 90 for ax, ay, ar in keep_clear):
            continue
        if any(math.hypot(x - r["x"], y - r["y"]) < r["r"] + radius + 40 for r in rocks):
            continue
        base = rng.choice(((74, 52, 46), (92, 62, 50), (60, 44, 42)))
        pygame.draw.ellipse(
            surface,
            (70, 34, 24),
            (x - radius, y + radius // 3, radius * 2, radius // 2),
        )
        pygame.draw.circle(surface, base, (x, y), radius)
        pygame.draw.circle(surface, tuple(min(255, c + 24) for c in base), (x - radius // 4, y - radius // 4), radius // 2)
        pygame.draw.circle(surface, tuple(max(0, c - 22) for c in base), (x, y), radius, 2)
        rocks.append({"x": x, "y": y, "r": radius})

    # scattered dust ridges at the edges
    for _ in range(90):
        x = rng.randrange(width)
        y = rng.randrange(height)
        pygame.draw.circle(surface, (120, 55, 34), (x, y), rng.choice((3, 4, 5)), 1)

    return surface, rocks


# --- lava tunnel ------------------------------------------------------------
def tunnel_backdrop(width: int, height: int, *, seed: int = 3) -> pygame.Surface:
    """Side-view cave backdrop with a lava glow along the floor."""
    rng = random.Random(seed)
    surface = _gradient(width, height, (18, 12, 16), (34, 16, 14))

    # distant basalt layers
    for layer in range(3):
        shade = 26 + layer * 8
        points = [(0, height)]
        x = 0
        while x < width:
            step = rng.randint(120, 260)
            peak = height - rng.randint(80, 220 + layer * 40)
            points.append((x + step // 2, peak))
            points.append((x + step, height - rng.randint(20, 90)))
            x += step
        points.append((width, height))
        pygame.draw.polygon(surface, (shade, shade - 8, shade - 6), points)

    # ceiling stalactites
    for _ in range(60):
        x = rng.randrange(width)
        length = rng.randint(30, 110)
        width_ = rng.randint(8, 22)
        pygame.draw.polygon(
            surface,
            (12, 9, 12),
            [(x, 0), (x + width_, 0), (x + width_ // 2, length)],
        )

    # lava fissures along the bottom
    glow = pygame.Surface((width, 180), pygame.SRCALPHA)
    for y in range(180):
        alpha = int(90 * (y / 180) ** 2)
        pygame.draw.line(glow, (255, 120, 40, alpha), (0, y), (width, y))
    surface.blit(glow, (0, height - 180))
    for _ in range(40):
        x = rng.randrange(width)
        y = height - rng.randint(10, 60)
        pygame.draw.line(surface, (255, 170, 70), (x, y), (x + rng.randint(20, 70), y - 2), 2)

    return surface


def light_mask(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    *,
    darkness: int = 236,
) -> None:
    """Overlay darkness with a soft circular hole (cheap flashlight)."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, darkness))
    light = _light_sprite(max(8, int(radius)))
    overlay.blit(
        light,
        (int(center[0] - radius), int(center[1] - radius)),
        special_flags=pygame.BLEND_RGBA_SUB,
    )
    surface.blit(overlay, (0, 0))


_light_cache: dict[int, pygame.Surface] = {}


def _light_sprite(radius: int) -> pygame.Surface:
    cached = _light_cache.get(radius)
    if cached is not None:
        return cached
    size = radius * 2
    light = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 14
    for index in range(steps, 0, -1):
        r = max(1, int(radius * index / steps))
        alpha = int(255 * (1.0 - index / steps) ** 0.75)
        pygame.draw.circle(light, (255, 255, 255, alpha), (radius, radius), r)
    pygame.draw.circle(light, (255, 255, 255, 255), (radius, radius), max(1, radius // 4))
    _light_cache[radius] = light
    return light
