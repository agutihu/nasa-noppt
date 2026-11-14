"""Procedural characters, ships and icons. No image files required."""

from __future__ import annotations

import math

import pygame

from core import settings


def _poly(surface, color, points, width=0):
    pygame.draw.polygon(surface, color, points, width)


def draw_astronaut(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    moving: bool = False,
    facing: int = 1,
    hurt: float = 0.0,
    scale: float = 1.0,
) -> None:
    cx, cy = center
    s = scale
    bob = math.sin(t * 6.0) * (1.5 if moving else 0.6) * s

    # thruster flame
    if moving:
        flicker = 3 + int((math.sin(t * 34.0) + 1) * 3)
        flame_color = (255, 190, 110) if facing >= 0 else (150, 220, 255)
        _poly(
            surface,
            flame_color,
            [
                (cx - 5 * s, cy + 14 * s + bob),
                (cx + 5 * s, cy + 14 * s + bob),
                (cx, cy + (18 + flicker) * s + bob),
            ],
        )

    body_color = (226, 234, 246)
    if hurt > 0:
        body_color = (255, 150, 165)

    # backpack
    pygame.draw.rect(
        surface,
        (120, 140, 175),
        pygame.Rect(int(cx - 13 * s), int(cy - 8 * s + bob), int(26 * s), int(17 * s)),
        border_radius=max(1, int(4 * s)),
    )
    # torso
    pygame.draw.rect(
        surface,
        body_color,
        pygame.Rect(int(cx - 9 * s), int(cy - 6 * s + bob), int(18 * s), int(18 * s)),
        border_radius=max(2, int(6 * s)),
    )
    # legs
    pygame.draw.rect(
        surface, (198, 210, 228), pygame.Rect(int(cx - 8 * s), int(cy + 11 * s + bob), int(7 * s), int(7 * s))
    )
    pygame.draw.rect(
        surface, (198, 210, 228), pygame.Rect(int(cx + 1 * s), int(cy + 11 * s + bob), int(7 * s), int(7 * s))
    )
    # arms
    pygame.draw.rect(
        surface, (208, 220, 238), pygame.Rect(int(cx - 14 * s), int(cy - 4 * s + bob), int(6 * s), int(12 * s))
    )
    pygame.draw.rect(
        surface, (208, 220, 238), pygame.Rect(int(cx + 8 * s), int(cy - 4 * s + bob), int(6 * s), int(12 * s))
    )
    # helmet
    pygame.draw.circle(surface, body_color, (int(cx), int(cy - 12 * s + bob)), int(10 * s))
    pygame.draw.circle(surface, (34, 52, 78), (int(cx + 2 * s * facing), int(cy - 12 * s + bob)), int(7 * s))
    pygame.draw.circle(surface, settings.ACCENT, (int(cx + 3 * s * facing), int(cy - 13 * s + bob)), int(3 * s))

    if hurt > 0:
        flash = pygame.Surface((int(34 * s), int(44 * s)), pygame.SRCALPHA)
        flash.fill((255, 80, 110, 60))
        surface.blit(flash, (int(cx - 17 * s), int(cy - 24 * s)))


def draw_laila(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    scale: float = 1.0,
    talking: bool = False,
    alpha: int = 220,
) -> None:
    """Laila: a small holographic companion. Drawn on its own layer for the glow."""
    s = scale
    bob = math.sin(t * 2.2) * 3 * s
    size = int(96 * s)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    # projection cone and base
    pygame.draw.polygon(
        layer,
        (*settings.ACCENT, 26),
        [(cx - 14 * s, size - 4), (cx + 14 * s, size - 4), (cx + 8 * s, cy + 14 * s + bob), (cx - 8 * s, cy + 14 * s + bob)],
    )
    pygame.draw.ellipse(
        layer, (*settings.ACCENT, 70), pygame.Rect(int(cx - 22 * s), int(size - 12), int(44 * s), int(9 * s))
    )

    # hologram rings
    for index in range(3):
        radius = int((30 + index * 7) * s)
        ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*settings.ACCENT, 26), (radius, radius), radius, 1)
        layer.blit(ring, (cx - radius, int(cy - 6 * s + bob) - radius))

    head = (cx, int(cy - 8 * s + bob))
    # ears
    _poly(
        layer,
        (*settings.ACCENT, 190),
        [
            (head[0] - 14 * s, head[1] - 10 * s),
            (head[0] - 20 * s, head[1] - 26 * s),
            (head[0] - 5 * s, head[1] - 16 * s),
        ],
    )
    _poly(
        layer,
        (*settings.ACCENT, 190),
        [
            (head[0] + 14 * s, head[1] - 10 * s),
            (head[0] + 20 * s, head[1] - 26 * s),
            (head[0] + 5 * s, head[1] - 16 * s),
        ],
    )
    # head + snout
    pygame.draw.circle(layer, (*settings.ACCENT, 150), head, int(15 * s))
    pygame.draw.circle(layer, (*settings.ACCENT, 220), head, int(15 * s), max(1, int(2 * s)))
    pygame.draw.ellipse(
        layer,
        (*settings.ACCENT, 170),
        pygame.Rect(int(head[0] - 7 * s), int(head[1] + 4 * s), int(14 * s), int(10 * s)),
    )
    # visor + eyes
    pygame.draw.rect(
        layer,
        (6, 20, 26, 220),
        pygame.Rect(int(head[0] - 11 * s), int(head[1] - 5 * s), int(22 * s), int(8 * s)),
        border_radius=max(1, int(3 * s)),
    )
    blink = int((math.sin(t * 1.7) + 1) * 0.5) < 4
    if blink:
        pygame.draw.circle(layer, settings.ACCENT, (int(head[0] - 5 * s), int(head[1] - 1 * s)), max(1, int(2 * s)))
        pygame.draw.circle(layer, settings.ACCENT, (int(head[0] + 5 * s), int(head[1] - 1 * s)), max(1, int(2 * s)))

    # speaker pulse
    if talking:
        pulse = int(8 + 4 * math.sin(t * 12.0))
        pygame.draw.circle(layer, (*settings.ACCENT, 120), (int(head[0]), int(head[1] + 9 * s)), pulse, 1)

    # scanline flicker
    for y in range(0, size, 4):
        pygame.draw.line(layer, (0, 0, 0, 22), (0, y), (size, y))

    flicker = int(alpha + 18 * math.sin(t * 9.0) + 8 * math.sin(t * 23.0))
    layer.set_alpha(max(90, min(255, flicker)))
    surface.blit(layer, (center[0] - size // 2, center[1] - size // 2))


def draw_ship(
    surface: pygame.Surface,
    center: tuple[int, int],
    scale: float = 1.0,
    t: float = 0.0,
    *,
    damaged: bool = False,
    thrust: bool = True,
) -> None:
    s = scale
    cx, cy = center

    if thrust:
        flicker = 4 + int((math.sin(t * 30.0) + 1) * 3)
        _poly(
            surface,
            (120, 210, 255),
            [(cx - 7 * s, cy + 26 * s), (cx + 7 * s, cy + 26 * s), (cx, cy + (30 + flicker) * s)],
        )
        _poly(
            surface,
            (255, 255, 230),
            [(cx - 3 * s, cy + 26 * s), (cx + 3 * s, cy + 26 * s), (cx, cy + (34 + flicker) * s)],
        )

    hull = (206, 220, 240) if not damaged else (180, 150, 150)
    _poly(
        surface,
        (96, 112, 140),
        [(cx - 20 * s, cy + 18 * s), (cx + 20 * s, cy + 18 * s), (cx + 12 * s, cy + 28 * s), (cx - 12 * s, cy + 28 * s)],
    )
    _poly(
        surface,
        hull,
        [(cx, cy - 30 * s), (cx + 13 * s, cy + 4 * s), (cx + 20 * s, cy + 17 * s), (cx - 20 * s, cy + 17 * s), (cx - 13 * s, cy + 4 * s)],
    )
    _poly(
        surface,
        (150, 168, 196),
        [(cx - 5 * s, cy - 6 * s), (cx + 5 * s, cy - 6 * s), (cx + 9 * s, cy + 16 * s), (cx - 9 * s, cy + 16 * s)],
    )
    pygame.draw.circle(surface, (44, 66, 96), (int(cx), int(cy - 12 * s)), int(6 * s))
    pygame.draw.circle(surface, settings.ACCENT, (int(cx), int(cy - 12 * s)), int(3 * s))

    if damaged:
        pygame.draw.line(surface, (60, 40, 40), (cx - 12 * s, cy - 2 * s), (cx - 2 * s, cy + 10 * s), max(1, int(2 * s)))


def draw_drone(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    radius: int = 12,
    hostile: bool = True,
) -> None:
    cx, cy = center
    spin = t * 6.0
    for index in range(3):
        angle = spin + index * math.tau / 3
        arm_end = (cx + math.cos(angle) * radius * 1.7, cy + math.sin(angle) * radius * 1.7)
        pygame.draw.line(surface, (90, 104, 128), (cx, cy), arm_end, 2)
        pygame.draw.circle(surface, (140, 155, 180), (int(arm_end[0]), int(arm_end[1])), max(2, radius // 4))

    pygame.draw.circle(surface, (58, 70, 92), (cx, cy), radius)
    pygame.draw.circle(surface, (120, 136, 162), (cx, cy), radius, 2)
    eye = settings.DANGER if hostile else settings.ACCENT
    pygame.draw.circle(surface, eye, (cx, cy), max(2, radius // 3))
    pygame.draw.circle(surface, (255, 255, 255), (cx - 1, cy - 1), max(1, radius // 6))


def draw_part(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int = 14,
    color: tuple[int, int, int] = settings.ACCENT,
    t: float = 0.0,
    *,
    glow: bool = True,
) -> None:
    cx, cy = center
    points = [
        (cx, cy - radius),
        (cx + radius, cy - radius // 2),
        (cx + radius, cy + radius // 2),
        (cx, cy + radius),
        (cx - radius, cy + radius // 2),
        (cx - radius, cy - radius // 2),
    ]
    if glow:
        halo = radius + int(4 + 3 * math.sin(t * 4.0))
        pygame.draw.circle(surface, (20, 30, 40), (cx, cy), halo)
        pygame.draw.circle(surface, color, (cx, cy), halo, 1)
    _poly(surface, color, points)
    _poly(surface, (12, 20, 30), points, 2)
    pygame.draw.line(surface, (12, 20, 30), (cx - radius // 3, cy), (cx + radius // 3, cy), 2)
    pygame.draw.line(surface, (12, 20, 30), (cx, cy - radius // 3), (cx, cy + radius // 3), 2)


def draw_heart(surface: pygame.Surface, center: tuple[int, int], size: int, filled: bool = True) -> None:
    cx, cy = center
    r = max(2, size // 2)
    color = settings.DANGER if filled else (52, 66, 92)
    pygame.draw.circle(surface, color, (cx - r // 2, cy - r // 3), max(2, r // 2))
    pygame.draw.circle(surface, color, (cx + r // 2, cy - r // 3), max(2, r // 2))
    _poly(
        surface,
        color,
        [(cx - r, cy - r // 4), (cx + r, cy - r // 4), (cx, cy + r)],
    )
