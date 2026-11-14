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
    airborne: bool = False,
    firing: float = 0.0,
) -> None:
    """The player: a detailed explorer suit with animated legs, blaster and jetpack."""
    cx, cy = center
    s = scale
    f = 1 if facing >= 0 else -1
    bob = math.sin(t * 6.0) * (1.5 if moving else 0.6) * s
    step = math.sin(t * 11.0) * 3.5 * s if moving else 0.0

    suit = (232, 238, 248)
    shade = (198, 208, 226)
    stripe = (240, 130, 60)
    dark = (46, 58, 84)
    if hurt > 0:
        suit = (255, 150, 165)
        shade = (222, 120, 138)

    # jetpack flame while airborne
    if airborne:
        flicker = 4 + int((math.sin(t * 34.0) + 1) * 3)
        flame = (255, 190, 110)
        _poly(
            surface,
            flame,
            [
                (cx - 9 * s - f * 2 * s, cy + 6 * s + bob),
                (cx - 3 * s - f * 2 * s, cy + 6 * s + bob),
                (cx - 6 * s - f * 2 * s, cy + (12 + flicker) * s + bob),
            ],
        )

    # backpack (behind the body)
    pygame.draw.rect(
        surface,
        (110, 128, 158),
        pygame.Rect(int(cx - f * 15 * s - 5 * s), int(cy - 8 * s + bob), int(11 * s), int(16 * s)),
        border_radius=max(1, int(3 * s)),
    )
    # backpack antenna with a blinking light
    pygame.draw.line(
        surface,
        (150, 165, 190),
        (cx - f * 10 * s, cy - 8 * s + bob),
        (cx - f * 12 * s, cy - 18 * s + bob),
        max(1, int(s)),
    )
    blink = int(t * 3.0) % 2 == 0
    if blink:
        pygame.draw.circle(surface, settings.ACCENT, (int(cx - f * 12 * s), int(cy - 19 * s + bob)), max(1, int(1.6 * s)))

    # legs (animated walk cycle) and boots stay planted on the ground line
    ground = cy + 17 * s
    for index in (-1, 1):
        swing = step * index if moving else index * 1.2 * s
        leg_h = 9 * s + abs(swing) * 0.2
        hip_x = cx + index * 4 * s
        leg = pygame.Rect(
            int(hip_x - 3 * s + swing * 0.4),
            int(ground - leg_h),
            int(6 * s),
            int(leg_h),
        )
        pygame.draw.rect(surface, shade, leg, border_radius=max(1, int(2 * s)))
        boot = pygame.Rect(leg.x - int(1 * s), ground - int(3 * s), leg.width + int(3 * s), int(3 * s))
        pygame.draw.rect(surface, dark, boot, border_radius=max(1, int(1 * s)))

    # torso with chest stripe + suit light
    torso = pygame.Rect(int(cx - 9 * s), int(cy - 7 * s + bob), int(18 * s), int(17 * s))
    pygame.draw.rect(surface, suit, torso, border_radius=max(2, int(5 * s)))
    pygame.draw.rect(
        surface,
        stripe,
        pygame.Rect(torso.x, torso.y + int(7 * s), torso.width, int(3 * s)),
        border_radius=max(1, int(1 * s)),
    )
    pygame.draw.circle(surface, settings.ACCENT, (int(cx - f * 4 * s), int(cy - 2 * s + bob)), max(1, int(2 * s)))

    # back arm
    pygame.draw.rect(
        surface,
        shade,
        pygame.Rect(int(cx - f * 11 * s - 3 * s), int(cy - 3 * s + bob), int(6 * s), int(11 * s)),
        border_radius=max(1, int(2 * s)),
    )

    # front arm + blaster
    arm_y = cy - 1 * s + bob
    pygame.draw.rect(
        surface,
        suit,
        pygame.Rect(int(cx + f * 6 * s), int(arm_y), int(10 * s), int(5 * s)),
        border_radius=max(1, int(2 * s)),
    )
    gun_x = cx + f * 14 * s
    pygame.draw.rect(
        surface,
        (70, 84, 110),
        pygame.Rect(int(gun_x - 3 * s), int(arm_y - 2 * s), int(10 * s), int(5 * s)),
        border_radius=max(1, int(1 * s)),
    )
    pygame.draw.circle(surface, settings.ACCENT, (int(gun_x + f * 6 * s), int(arm_y)), max(1, int(1.6 * s)))
    if firing > 0:
        flash_len = 8 + 6 * firing
        pygame.draw.circle(
            surface,
            (255, 255, 200),
            (int(gun_x + f * (8 + flash_len * 0.4) * s), int(arm_y)),
            max(2, int(3 * s * firing + 2)),
        )

    # helmet + visor
    helmet_y = cy - 13 * s + bob
    pygame.draw.circle(surface, suit, (int(cx), int(helmet_y)), int(10 * s))
    pygame.draw.circle(surface, (150, 162, 186), (int(cx), int(helmet_y)), int(10 * s), max(1, int(1.4 * s)))
    visor = pygame.Rect(int(cx - 6 * s + f * 2 * s), int(helmet_y - 5 * s), int(11 * s), int(8 * s))
    pygame.draw.rect(surface, (24, 34, 56), visor, border_radius=max(1, int(3 * s)))
    pygame.draw.rect(surface, (64, 140, 190), visor, max(1, int(1 * s)), border_radius=max(1, int(3 * s)))
    glint_x = visor.x + int(3 * s) + (2 * s if f > 0 else 0)
    pygame.draw.circle(surface, (140, 220, 255), (int(glint_x), int(helmet_y - 3 * s + bob)), max(1, int(1.5 * s)))

    if hurt > 0:
        flash = pygame.Surface((int(40 * s), int(48 * s)), pygame.SRCALPHA)
        flash.fill((255, 80, 110, 60))
        surface.blit(flash, (int(cx - 20 * s), int(cy - 26 * s)))


def draw_alien(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    color: tuple[int, int, int] = (96, 200, 120),
    radius: int = 12,
    facing: int = 1,
    moving: bool = False,
) -> None:
    """Ground alien: wobbling blob with legs, spikes and glowing eyes."""
    cx, cy = center
    wobble = math.sin(t * 9.0) * (1.0 if moving else 0.4)
    body_w = radius * 1.7
    body_h = radius * 1.3 + wobble

    # legs
    for index in (-1, 0, 1):
        leg_x = cx + index * radius * 0.75
        swing = math.sin(t * 12.0 + index * 2.0) * (3 if moving else 1)
        pygame.draw.line(
            surface,
            tuple(max(0, channel - 40) for channel in color),
            (leg_x, cy + body_h * 0.5),
            (leg_x + swing, cy + body_h * 0.5 + 5),
            2,
        )
        pygame.draw.circle(surface, tuple(max(0, channel - 60) for channel in color), (int(leg_x + swing), int(cy + body_h * 0.5 + 6)), 2)

    # spikes on the back
    for index in range(3):
        spike_x = cx - body_w * 0.4 + index * body_w * 0.4
        pygame.draw.polygon(
            surface,
            tuple(max(0, channel - 30) for channel in color),
            [
                (spike_x - 3, cy - body_h * 0.5),
                (spike_x + 3, cy - body_h * 0.5),
                (spike_x, cy - body_h * 0.5 - 6),
            ],
        )

    # body
    pygame.draw.ellipse(surface, color, pygame.Rect(int(cx - body_w / 2), int(cy - body_h / 2), int(body_w), int(body_h)))
    pygame.draw.ellipse(
        surface,
        tuple(max(0, channel - 50) for channel in color),
        pygame.Rect(int(cx - body_w / 2), int(cy - body_h / 2), int(body_w), int(body_h)),
        2,
    )

    # eyes facing the player
    eye_y = cy - body_h * 0.1
    for eye_index in (-1, 1):
        eye_x = cx + eye_index * 3 + facing * 2
        pygame.draw.circle(surface, (255, 230, 120), (int(eye_x), int(eye_y)), 2)
        pygame.draw.circle(surface, (30, 30, 10), (int(eye_x + facing), int(eye_y)), 1)
    pygame.draw.line(surface, (20, 30, 16), (cx - 3 + facing, cy + body_h * 0.22), (cx + 3 + facing, cy + body_h * 0.22), 1)


def draw_ufo(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    color: tuple[int, int, int] = (150, 170, 200),
    radius: int = 16,
    charging: float = 0.0,
) -> None:
    """Alien saucer: metal hull, glass dome with a pilot, blinking rim lights."""
    cx, cy = center
    tilt = math.sin(t * 2.4) * 0.06
    hull_w = radius * 2.4
    hull_h = int(radius * 0.7)

    # under glow
    glow = pygame.Surface((int(hull_w), int(hull_h * 3)), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*settings.DANGER, 60), (0, 0, int(hull_w), int(hull_h * 1.6)))
    surface.blit(glow, (int(cx - hull_w / 2), int(cy - hull_h * 0.6)))

    # dome + alien pilot
    dome_r = int(radius * 0.85)
    pygame.draw.circle(surface, (120, 200, 210), (cx, cy - hull_h), dome_r)
    pygame.draw.circle(surface, (170, 230, 235), (cx, cy - hull_h), dome_r, 1)
    head_r = max(3, dome_r // 2)
    pygame.draw.circle(surface, (110, 210, 130), (cx, cy - hull_h), head_r)
    for eye_index in (-1, 1):
        pygame.draw.ellipse(
            surface,
            (12, 16, 20),
            pygame.Rect(int(cx + eye_index * head_r * 0.5 - 2), int(cy - hull_h - 2), 4, 5),
        )

    # hull
    hull_points = [
        (cx - hull_w / 2, cy + tilt * 10),
        (cx - hull_w * 0.2, cy - hull_h + 2),
        (cx + hull_w * 0.2, cy - hull_h + 2),
        (cx + hull_w / 2, cy + tilt * 10),
        (cx + hull_w * 0.3, cy + hull_h * 0.5),
        (cx - hull_w * 0.3, cy + hull_h * 0.5),
    ]
    pygame.draw.polygon(surface, color, hull_points)
    pygame.draw.polygon(surface, tuple(max(0, channel - 60) for channel in color), hull_points, 1)

    # blinking rim lights
    for index in range(4):
        light_x = cx - hull_w * 0.32 + index * hull_w * 0.213
        on = int(t * 5.0 + index) % 2 == 0
        pygame.draw.circle(
            surface,
            settings.ACCENT if on else (40, 60, 80),
            (int(light_x), int(cy + hull_h * 0.1)),
            2,
        )

    # charge glow when about to fire
    if charging > 0:
        charge_r = int(3 + 5 * charging)
        pygame.draw.circle(surface, settings.WARN, (cx, cy + hull_h), charge_r, 1)


def draw_laika(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    scale: float = 1.0,
    talking: bool = False,
    alpha: int = 220,
) -> None:
    """Laika: a small holographic companion. Drawn on its own layer for the glow."""
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
