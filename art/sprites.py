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


# --- Laika: portrait, holo companion and quadruped ---------------------------
def draw_laika_portrait(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int,
    t: float = 0.0,
    *,
    frame: bool = True,
    dim: bool = False,
) -> None:
    """The pixel-art portrait from ``assets/images/laika_happy.png``.

    Falls back to the hologram drawing when the image is missing, so the game
    never crashes on a fresh clone.
    """
    from core import assets  # local import keeps art import-light

    image = assets.portrait(size)
    if image is None:
        draw_laika(surface, center, t, scale=size / 96.0, talking=True)
        return

    if frame:
        halo = pygame.Surface((size + 18, size + 18), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*settings.ACCENT, 34), ((size + 18) // 2, (size + 18) // 2), (size + 18) // 2)
        surface.blit(halo, (center[0] - (size + 18) // 2, center[1] - (size + 18) // 2))
    surface.blit(image, (center[0] - size // 2, center[1] - size // 2))
    if dim:
        veil = pygame.Surface((size, size), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 120))
        surface.blit(veil, (center[0] - size // 2, center[1] - size // 2))


def draw_laika_dog(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    scale: float = 1.0,
    facing: int = 1,
    hopping: bool = False,
) -> None:
    """Small robot dog that trots beside the astronaut in the outpost."""
    s = scale
    f = 1 if facing >= 0 else -1
    cx, cy = center
    bob = math.sin(t * 7.0) * (3.0 if hopping else 1.2) * s
    cy += bob

    body = (196, 176, 160)
    dark = (92, 74, 68)
    accent = settings.ACCENT

    # legs
    for index in (-1, 1):
        for side in (-1, 1):
            leg_x = cx + index * 9 * s + side * 3 * s
            swing = math.sin(t * 10.0 + index * 1.6) * 3 * s if hopping else 0
            pygame.draw.line(
                surface, dark,
                (leg_x, cy + 6 * s),
                (leg_x + swing, cy + 14 * s),
                max(1, int(2 * s)),
            )

    # tail antenna
    pygame.draw.line(surface, dark, (cx - f * 15 * s, cy - 2 * s), (cx - f * 20 * s, cy - 12 * s), max(1, int(2 * s)))
    pygame.draw.circle(surface, accent, (int(cx - f * 20 * s), int(cy - 13 * s)), max(1, int(2 * s)))

    # body
    pygame.draw.ellipse(
        surface, body,
        pygame.Rect(int(cx - 15 * s), int(cy - 5 * s), int(30 * s), int(14 * s)),
    )
    pygame.draw.ellipse(
        surface, dark,
        pygame.Rect(int(cx - 15 * s), int(cy - 5 * s), int(30 * s), int(14 * s)), max(1, int(1.4 * s)),
    )
    # solar backpack
    pygame.draw.rect(surface, (48, 74, 96), pygame.Rect(int(cx - 9 * s), int(cy - 9 * s), int(18 * s), int(6 * s)), border_radius=max(1, int(2 * s)))
    for line_x in range(int(cx - 7 * s), int(cx + 8 * s), max(2, int(4 * s))):
        pygame.draw.line(surface, accent, (line_x, int(cy - 9 * s)), (line_x, int(cy - 4 * s)), max(1, int(1 * s)))

    # head
    head_x = cx + f * 17 * s
    pygame.draw.circle(surface, body, (int(head_x), int(cy - 6 * s)), int(9 * s))
    pygame.draw.circle(surface, dark, (int(head_x), int(cy - 6 * s)), int(9 * s), max(1, int(1.4 * s)))
    # ears
    pygame.draw.polygon(
        surface, (120, 96, 84),
        [(head_x - f * 4 * s, cy - 13 * s), (head_x + f * 1 * s, cy - 20 * s), (head_x + f * 4 * s, cy - 11 * s)],
    )
    # visor + eye
    pygame.draw.rect(
        surface, (28, 42, 54),
        pygame.Rect(int(head_x - 5 * s + f * 2 * s), int(cy - 9 * s), int(8 * s), int(5 * s)),
        border_radius=max(1, int(2 * s)),
    )
    pygame.draw.circle(surface, accent, (int(head_x + f * 3 * s), int(cy - 7 * s)), max(1, int(1.6 * s)))


# --- rover ------------------------------------------------------------------
def draw_rover_top(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    scale: float = 1.0,
    moving: bool = False,
    facing: int = 1,
    lights: bool = True,
) -> None:
    """Top-down rover used on the Martian surface level."""
    s = scale
    cx, cy = center
    body = (206, 214, 224)
    dark = (44, 52, 66)
    rust = (168, 86, 50)

    # wheels
    for offset_x in (-1, 0, 1):
        for offset_y in (-1, 1):
            wheel = pygame.Rect(int(cx + offset_x * 14 * s - 5 * s), int(cy + offset_y * 13 * s - 4 * s), int(10 * s), int(8 * s))
            pygame.draw.rect(surface, dark, wheel, border_radius=max(1, int(2 * s)))
            roll = int((t * 9.0) % 4) if moving else 0
            pygame.draw.line(
                surface, (120, 130, 146),
                (wheel.centerx - 3 * s + roll, wheel.centery),
                (wheel.centerx + 3 * s, wheel.centery),
                max(1, int(1 * s)),
            )

    # chassis
    chassis = pygame.Rect(int(cx - 18 * s), int(cy - 15 * s), int(36 * s), int(30 * s))
    pygame.draw.rect(surface, body, chassis, border_radius=max(2, int(6 * s)))
    pygame.draw.rect(surface, dark, chassis, max(1, int(1.6 * s)), border_radius=max(2, int(6 * s)))

    # solar deck
    deck = pygame.Rect(int(cx - 13 * s), int(cy - 10 * s), int(26 * s), int(14 * s))
    pygame.draw.rect(surface, (36, 62, 88), deck, border_radius=max(1, int(2 * s)))
    for gx in range(deck.x + 2, deck.right - 1, max(3, int(5 * s))):
        pygame.draw.line(surface, (94, 210, 200), (gx, deck.y + 2), (gx, deck.bottom - 2), 1)
    pygame.draw.line(surface, (94, 210, 200), (deck.x + 2, deck.centery), (deck.right - 2, deck.centery), 1)

    # camera mast + headlights (front is +x when facing right)
    mast_x = cx + facing * 4 * s
    pygame.draw.circle(surface, rust, (int(mast_x), int(cy + 2 * s)), max(2, int(3 * s)))
    pygame.draw.circle(surface, (28, 40, 52), (int(mast_x), int(cy + 2 * s)), max(1, int(1.6 * s)))

    if lights:
        for side in (-1, 1):
            lamp_x = cx + facing * 19 * s
            lamp_y = cy + side * 7 * s
            pygame.draw.circle(surface, (255, 240, 190), (int(lamp_x), int(lamp_y)), max(1, int(2 * s)))
            cone = pygame.Surface((int(46 * s), int(20 * s)), pygame.SRCALPHA)
            pygame.draw.polygon(cone, (255, 236, 170, 34), [(0, 8 * s), (46 * s, 0), (46 * s, 20 * s)])
            if facing < 0:
                cone = pygame.transform.flip(cone, True, False)
            surface.blit(cone, (int(lamp_x - (0 if facing > 0 else 46 * s)), int(lamp_y - 10 * s)))

    # antenna
    pygame.draw.line(surface, (150, 160, 176), (cx - facing * 12 * s, cy - 12 * s), (cx - facing * 16 * s, cy - 24 * s), max(1, int(1.4 * s)))
    blink = int(t * 3) % 2 == 0
    pygame.draw.circle(surface, settings.ACCENT if blink else (60, 80, 90), (int(cx - facing * 16 * s), int(cy - 25 * s)), max(1, int(2 * s)))


def draw_rover_side(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    scale: float = 1.0,
    facing: int = 1,
    moving: bool = False,
    jumping: bool = False,
) -> None:
    """Side-view rover for the lava-tunnel platforming level."""
    s = scale
    f = 1 if facing >= 0 else -1
    cx, cy = center
    dark = (40, 46, 60)
    body = (206, 214, 224)

    # six wheels, spinning
    for index, offset in enumerate((-18, 0, 18)):
        wheel_x = cx + offset * s
        wheel_y = cy + 14 * s
        pygame.draw.circle(surface, dark, (int(wheel_x), int(wheel_y)), max(3, int(7 * s)))
        pygame.draw.circle(surface, (86, 96, 112), (int(wheel_x), int(wheel_y)), max(3, int(7 * s)), max(1, int(2 * s)))
        spin = t * 10.0 + index
        for spoke in range(3):
            angle = spin + spoke * math.tau / 3
            pygame.draw.line(
                surface, (130, 142, 160),
                (wheel_x, wheel_y),
                (wheel_x + math.cos(angle) * 5 * s, wheel_y + math.sin(angle) * 5 * s),
                max(1, int(1 * s)),
            )

    # suspension
    for offset in (-18, 0, 18):
        pygame.draw.line(surface, (110, 120, 136), (cx + offset * s, cy + 7 * s), (cx + offset * s, cy + 12 * s), max(1, int(2 * s)))

    # body with a dog-ish snout on the leading edge
    body_rect = pygame.Rect(int(cx - 24 * s), int(cy - 10 * s), int(48 * s), int(20 * s))
    pygame.draw.rect(surface, body, body_rect, border_radius=max(2, int(6 * s)))
    pygame.draw.rect(surface, dark, body_rect, max(1, int(1.6 * s)), border_radius=max(2, int(6 * s)))
    snout = pygame.Rect(int(cx + f * 24 * s - (7 * s if f > 0 else 0)), int(cy - 4 * s), int(12 * s), int(11 * s))
    pygame.draw.rect(surface, body, snout, border_radius=max(1, int(3 * s)))
    pygame.draw.rect(surface, dark, snout, max(1, int(1.2 * s)), border_radius=max(1, int(3 * s)))

    # solar deck
    deck = pygame.Rect(int(cx - 16 * s), int(cy - 16 * s), int(32 * s), int(7 * s))
    pygame.draw.rect(surface, (36, 62, 88), deck, border_radius=max(1, int(2 * s)))
    for gx in range(deck.x + 2, deck.right - 1, max(3, int(5 * s))):
        pygame.draw.line(surface, (94, 210, 200), (gx, deck.y + 1), (gx, deck.bottom - 1), 1)

    # camera mast
    pygame.draw.line(surface, (150, 160, 176), (cx - f * 6 * s, cy - 16 * s), (cx - f * 10 * s, cy - 30 * s), max(1, int(1.4 * s)))
    pygame.draw.circle(surface, (28, 40, 52), (int(cx - f * 10 * s), int(cy - 31 * s)), max(2, int(3 * s)))
    pygame.draw.circle(surface, settings.ACCENT, (int(cx - f * 10 * s), int(cy - 31 * s)), max(1, int(1.5 * s)))

    # headlight + eye
    lamp_x = cx + f * 30 * s
    pygame.draw.circle(surface, (255, 240, 180), (int(lamp_x), int(cy + 1 * s)), max(1, int(2 * s)))
    pygame.draw.circle(surface, (36, 48, 62), (int(cx + f * 28 * s), int(cy - 12 * s)), max(1, int(2 * s)))
    pygame.draw.circle(surface, settings.ACCENT, (int(cx + f * 29 * s), int(cy - 12 * s)), max(1, int(1.2 * s)))

    if jumping:
        for side in (-1, 1):
            pygame.draw.line(
                surface, (255, 200, 120),
                (cx + side * 14 * s, cy + 18 * s),
                (cx + side * 14 * s, cy + 24 * s),
                max(1, int(2 * s)),
            )


# --- outpost props ----------------------------------------------------------
def draw_vending(surface: pygame.Surface, rect: pygame.Rect, t: float = 0.0, *, active: bool = False) -> None:
    pygame.draw.rect(surface, (46, 52, 66), rect, border_radius=10)
    pygame.draw.rect(surface, (26, 30, 40), rect.inflate(6, 6), 2, border_radius=12)
    pygame.draw.rect(surface, (62, 70, 88), (rect.x + 8, rect.y + 8, rect.width - 16, rect.height - 16), border_radius=8)

    glass = pygame.Rect(rect.x + 14, rect.y + 16, rect.width - 28, int(rect.height * 0.55))
    pygame.draw.rect(surface, (18, 34, 46), glass, border_radius=6)
    pygame.draw.rect(surface, (94, 210, 200), glass, 1, border_radius=6)
    for row in range(3):
        for col in range(3):
            item_x = glass.x + 16 + col * (glass.width - 32) // 3
            item_y = glass.y + 12 + row * (glass.height - 24) // 3
            shade = 130 + (row * 3 + col) * 8
            pygame.draw.rect(
                surface, (shade, shade - 30, 90),
                pygame.Rect(item_x, item_y, 12, 16), border_radius=2,
            )
    # reflection
    pygame.draw.line(surface, (150, 230, 240), (glass.x + 6, glass.bottom - 4), (glass.x + 20, glass.y + 4), 2)

    keypad = pygame.Rect(rect.x + 16, glass.bottom + 10, rect.width // 2 - 20, rect.height - glass.height - 40)
    pygame.draw.rect(surface, (28, 32, 42), keypad, border_radius=5)
    for index in range(9):
        key = pygame.Rect(keypad.x + 5 + (index % 3) * 14, keypad.y + 5 + (index // 3) * 12, 11, 9)
        pygame.draw.rect(surface, (70, 78, 94), key, border_radius=2)

    slot = pygame.Rect(rect.right - rect.width // 2 + 4, rect.bottom - 34, rect.width // 2 - 20, 16)
    pygame.draw.rect(surface, (14, 16, 22), slot, border_radius=3)
    pygame.draw.rect(surface, (90, 100, 120), slot, 1, border_radius=3)

    if active:
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow, (*settings.ACCENT, 34), (0, 0, rect.width, rect.height), border_radius=10)
        surface.blit(glow, rect.topleft)
        pygame.draw.rect(surface, settings.ACCENT, rect, 2, border_radius=10)


def draw_vent(surface: pygame.Surface, center: tuple[int, int], t: float = 0.0, *, active: bool = True, size: int = 46) -> None:
    rect = pygame.Rect(0, 0, size, size // 2)
    rect.center = center
    pygame.draw.rect(surface, (34, 38, 48), rect, border_radius=4)
    pygame.draw.rect(surface, (70, 76, 90), rect, 1, border_radius=4)
    for index in range(4):
        y = rect.y + 4 + index * (rect.height - 8) // 4
        pygame.draw.line(surface, (96, 104, 120), (rect.x + 5, y), (rect.right - 5, y), 2)
    if active:
        for index in range(3):
            phase = (t * 0.9 + index / 3.0) % 1.0
            alpha = int(120 * (1.0 - phase))
            puff = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(puff, (150, 230, 220, alpha), (5, 5), int(2 + phase * 4))
            surface.blit(puff, (rect.centerx - 5 + int(math.sin(t + index) * 4), rect.bottom + int(phase * 26)))


def draw_bed(surface: pygame.Surface, rect: pygame.Rect, t: float = 0.0, *, occupied: bool = False) -> None:
    pygame.draw.rect(surface, (40, 44, 58), rect, border_radius=8)
    pygame.draw.rect(surface, (78, 84, 102), rect, 1, border_radius=8)
    # sleeping bag strapped to the wall
    bag = rect.inflate(-14, -20)
    pygame.draw.rect(surface, (60, 96, 120), bag, border_radius=14)
    pygame.draw.rect(surface, (94, 216, 208), bag, 1, border_radius=14)
    pygame.draw.line(surface, (94, 216, 208), (bag.x + 8, bag.centery), (bag.right - 8, bag.centery), 1)
    if occupied:
        pygame.draw.ellipse(surface, (230, 214, 198), (bag.x + 6, bag.y + 6, bag.width - 12, 18))
        for index in range(3):
            zx = bag.centerx + 10 + index * 8
            zy = bag.y - 8 - index * 8 - int((math.sin(t * 2 + index) + 1) * 3)
            text = pygame.font.SysFont("consolas,monospace", 14 + index * 2)
            surface.blit(text.render("z", True, (180, 230, 224)), (zx, zy))


def draw_crumb(surface: pygame.Surface, center: tuple[int, int], t: float = 0.0) -> None:
    pulse = 0.7 + 0.3 * abs(math.sin(t * 3.0 + center[0] * 0.05))
    radius = max(2, int(4 * pulse))
    pygame.draw.circle(surface, (206, 150, 92), center, radius)
    pygame.draw.circle(surface, (150, 100, 56), center, radius, 1)


def draw_camera_station(surface: pygame.Surface, center: tuple[int, int], t: float = 0.0, *, taken: bool = False) -> None:
    cx, cy = center
    color = settings.GREEN if taken else settings.ACCENT
    radius = 26 + int(4 * math.sin(t * 3.0))
    pygame.draw.circle(surface, (*color, 60), center, radius, 1)
    pygame.draw.rect(surface, (26, 34, 44), (cx - 16, cy - 12, 32, 22), border_radius=5)
    pygame.draw.rect(surface, color, (cx - 16, cy - 12, 32, 22), 2, border_radius=5)
    pygame.draw.circle(surface, color, (cx, cy - 1), 7, 2)
    pygame.draw.circle(surface, (10, 16, 20), (cx, cy - 1), 4)
    pygame.draw.rect(surface, color, (cx - 5, cy - 17, 10, 5), border_radius=2)
    if taken:
        pygame.draw.line(surface, settings.GREEN, (cx - 12, cy + 16), (cx - 3, cy + 23), 3)
        pygame.draw.line(surface, settings.GREEN, (cx - 3, cy + 23), (cx + 14, cy + 6), 3)


def draw_sample_site(surface: pygame.Surface, center: tuple[int, int], t: float = 0.0, *, taken: bool = False) -> None:
    cx, cy = center
    color = (150, 130, 120) if taken else settings.GOLD
    pygame.draw.ellipse(surface, (86, 52, 36), (cx - 22, cy + 6, 44, 16))
    pygame.draw.circle(surface, (108, 82, 70), (cx, cy), 15)
    pygame.draw.circle(surface, (150, 120, 100), (cx - 5, cy - 4), 6)
    if taken:
        pygame.draw.line(surface, (70, 60, 58), (cx - 8, cy - 4), (cx + 8, cy + 6), 2)
    else:
        pulse = 0.5 + 0.5 * abs(math.sin(t * 2.4))
        pygame.draw.circle(surface, color, (cx, cy - 18), int(3 + 3 * pulse), 1)
        pygame.draw.circle(surface, color, (cx, cy - 18), 2)


def draw_terminal(
    surface: pygame.Surface,
    center: tuple[int, int],
    t: float = 0.0,
    *,
    kind: str = "sample",
    done: bool = False,
) -> None:
    cx, cy = center
    color = settings.GREEN if done else (settings.GOLD if kind == "sample" else settings.ACCENT)
    base = pygame.Rect(cx - 18, cy + 6, 36, 12)
    pygame.draw.rect(surface, (40, 36, 40), base, border_radius=4)
    pygame.draw.rect(surface, (90, 80, 80), base, 1, border_radius=4)
    pygame.draw.rect(surface, (26, 26, 32), (cx - 13, cy - 20, 26, 28), border_radius=4)
    pygame.draw.rect(surface, color, (cx - 13, cy - 20, 26, 28), 2, border_radius=4)

    if kind == "sample":
        pygame.draw.circle(surface, color, (cx, cy - 6), 5, 2)
        pygame.draw.line(surface, color, (cx, cy - 11), (cx, cy - 1), 1)
    else:
        pygame.draw.rect(surface, color, (cx - 7, cy - 12, 14, 10), 2, border_radius=2)
        pygame.draw.circle(surface, color, (cx, cy - 7), 3, 1)
        pygame.draw.rect(surface, color, (cx - 3, cy - 15, 6, 3), 2)

    if done:
        pygame.draw.line(surface, settings.GREEN, (cx - 8, cy + 1), (cx - 2, cy + 7), 2)
        pygame.draw.line(surface, settings.GREEN, (cx - 2, cy + 7), (cx + 9, cy - 6), 2)
    else:
        glow = pygame.Surface((54, 54), pygame.SRCALPHA)
        alpha = int(50 + 30 * abs(math.sin(t * 3)))
        pygame.draw.circle(glow, (*color, alpha), (27, 27), 20, 1)
        surface.blit(glow, (cx - 27, cy - 27))


def draw_rock_platform(
    surface: pygame.Surface,
    rect: pygame.Rect,
    t: float = 0.0,
    *,
    crumbling: float = 0.0,
    solid: bool = True,
) -> None:
    color = (96, 74, 66) if solid else (120, 100, 82)
    if crumbling > 0.0:
        color = (
            min(255, 96 + int(90 * (1.0 - crumbling))),
            74,
            66,
        )
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, (54, 40, 38), rect, 2, border_radius=6)
    pygame.draw.line(
        surface, (150, 120, 104),
        (rect.x + 6, rect.y + 4), (rect.right - 6, rect.y + 4), 2,
    )
    for index in range(3):
        crack_x = rect.x + 12 + index * rect.width // 4
        pygame.draw.line(
            surface, (54, 40, 38),
            (crack_x, rect.y + 8),
            (crack_x + 8, rect.centery),
            1,
        )
    # lava underglow
    glow = pygame.Surface((rect.width, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 120, 40, 30 + int(10 * math.sin(t * 3))), (0, 0, rect.width, 18))
    surface.blit(glow, (rect.x, rect.bottom - 6))


def draw_earth(surface: pygame.Surface, center: tuple[int, int], radius: int, t: float = 0.0) -> None:
    cx, cy = center
    pygame.draw.circle(surface, (36, 92, 156), (cx, cy), radius)
    pygame.draw.circle(surface, (64, 138, 196), (cx - radius // 4, cy - radius // 4), radius // 2)
    pygame.draw.ellipse(surface, (86, 168, 116), (cx - radius // 2, cy - radius // 3, radius, radius // 2))
    pygame.draw.ellipse(surface, (74, 150, 104), (cx, cy + radius // 5, radius // 2, radius // 3))
    pygame.draw.circle(surface, (180, 220, 255), (cx, cy), radius, 2)
    cloud = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for index in range(3):
        offset = int(math.sin(t * 0.6 + index) * radius * 0.4)
        pygame.draw.ellipse(
            cloud, (255, 255, 255, 60),
            (radius // 2 + offset, radius // 2 + index * radius // 3, radius, radius // 5),
        )
    surface.blit(cloud, (cx - radius, cy - radius))

