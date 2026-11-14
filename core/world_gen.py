"""Seeded world generation.

Turns a level's ``params`` into a full side-scrolling planet world: stepped terrain with
bottomless gaps, floating platforms, themed hazards, enemies, checkpoints, and the mission
goal (a labeled part on a pedestal plus the return pad). The same seed always rebuilds the
same world; difficulty scales gaps, enemy density and hazard pressure.
"""

from __future__ import annotations

import random

import pygame

from core import settings


def generate(level_id: str, params: dict, difficulty: str = "normal") -> dict:
    """Build the world layout for a level. Returns rects, specs and goal positions."""
    rng = random.Random(f"{level_id}:{params.get('seed', 1)}")
    length = int(params.get("world_length", 5200))
    ground_y = int(params.get("ground_y", 560))
    world_h = settings.HEIGHT + 60

    diff = {"easy": 0.8, "hard": 1.25}.get(difficulty, 1.0)

    platforms: list[pygame.Rect] = []
    hazards: list[dict] = []
    enemies: list[dict] = []
    checkpoints: list[int] = [60]

    hazard_types = list(params.get("hazard_types", []))
    gap_chance = float(params.get("gap_chance", 0.30)) * diff
    platform_chance = float(params.get("platform_chance", 0.55))
    enemy_density = float(params.get("enemy_density", 0.7)) * diff
    ufo_chance = float(params.get("ufo_chance", 0.30))
    hazard_density = float(params.get("hazard_density", 0.40)) * diff
    floaty = bool(params.get("floaty", False))  # gas giants: platforms over clouds

    def add_hazard(htype: str, x: int, y: int, width: int, seg_w: int) -> None:
        if htype in ("spikes", "acid_pool", "ice"):
            hazards.append({"type": htype, "x": x, "y": y, "w": rng.randint(70, 130)})
        elif htype in ("geyser", "lightning", "meteor_zone"):
            hazards.append(
                {
                    "type": htype,
                    "x": x,
                    "y": y,
                    "w": 44 if htype != "meteor_zone" else seg_w,
                    "cycle": rng.uniform(2.4, 3.6),
                    "offset": rng.uniform(0.0, 3.0),
                }
            )

    # starting pad: flat, safe, where the drop pod lands
    if not floaty:
        platforms.append(pygame.Rect(0, ground_y, 620, world_h - ground_y))
        x = 620
    else:
        platforms.append(pygame.Rect(0, ground_y - 40, 360, 26))
        x = 380
    top = ground_y
    checkpoint_every = length / 4.0
    next_checkpoint = checkpoint_every

    while x < length - 620:
        if floaty:
            # a cluster of floating platforms over the clouds
            base_y = ground_y - rng.randint(40, 170)
            first_top = None
            for _ in range(rng.randint(2, 3)):
                pw = rng.randint(140, 230)
                py = int(max(300, min(ground_y - 30, base_y + rng.randint(-90, 90))))
                platforms.append(pygame.Rect(int(x), py, pw, 26))
                if first_top is None:
                    first_top = py
                # hazards and UFOs live on/above the platforms
                if hazard_types and rng.random() < hazard_density * 0.8:
                    htype = rng.choice(hazard_types)
                    add_hazard(
                        htype,
                        int(x + pw // 2),
                        py,
                        pw,
                        pw,
                    )
                if rng.random() < enemy_density:
                    enemies.append(
                        {
                            "type": "ufo",
                            "x": int(x + pw // 2 + rng.randint(-40, 40)),
                            "y": py - rng.randint(120, 190),
                            "range": rng.randint(90, 150),
                        }
                    )
            if x >= next_checkpoint and first_top is not None:
                checkpoints.append(int(x + 60))
                next_checkpoint += checkpoint_every
            top = first_top or ground_y - 80
            x += rng.randint(210, 330)
            continue

        seg_w = rng.randint(280, 560)
        if rng.random() < 0.6:
            top = ground_y + rng.randint(-80, 30)
        top = max(350, min(ground_y + 30, top))
        plat = pygame.Rect(int(x), int(top), seg_w, world_h - top)
        platforms.append(plat)

        if x >= next_checkpoint:
            checkpoints.append(int(x + seg_w // 2))
            next_checkpoint += checkpoint_every

        # ground hazards on wide segments
        if hazard_types and seg_w >= 340 and rng.random() < hazard_density:
            htype = rng.choice(hazard_types)
            hx = int(x + rng.randint(50, max(60, seg_w - 150)))
            add_hazard(htype, hx, top, 130, seg_w)

        # enemies: ground walkers and hovering alien saucers
        if rng.random() < enemy_density:
            ex = int(x + seg_w // 2 + rng.randint(-70, 70))
            if rng.random() < ufo_chance:
                enemies.append(
                    {
                        "type": "ufo",
                        "x": ex,
                        "y": top - rng.randint(130, 210),
                        "range": rng.randint(90, 160),
                    }
                )
            else:
                enemies.append(
                    {
                        "type": "walker",
                        "x": ex,
                        "y": top - 16,
                        "range": rng.randint(70, 130),
                    }
                )

        # gap and optional floating stepping stone
        gap = 0
        if rng.random() < gap_chance:
            gap = rng.randint(
                int(params.get("gap_min", 90)), int(params.get("gap_max", 170))
            )
            if rng.random() < platform_chance:
                fx = int(x + seg_w + gap // 2 - 70)
                fy = int(min(top, ground_y) - rng.randint(90, 170))
                platforms.append(pygame.Rect(fx, fy, rng.randint(130, 190), 26))
        x += seg_w + gap

    # final plateau: part pedestal and the return pad
    final_w = int(length - x + 40)
    if floaty:
        final_top = ground_y - 60
        platforms.append(pygame.Rect(int(x), int(final_top), max(final_w, 400), 26))
        platforms.append(
            pygame.Rect(int(x), int(final_top + 26), max(final_w, 400), 40)
        )
    else:
        final_top = ground_y - 20
        platforms.append(
            pygame.Rect(int(x), int(final_top), final_w, world_h - final_top)
        )
    checkpoints.append(int(x + 60))

    part_x = length - 470
    pedestal_top = final_top - 110
    platforms.append(pygame.Rect(part_x - 95, int(pedestal_top), 190, 26))
    part_y = pedestal_top - 34

    # wind bands (Neptune-style headwinds) at fixed fractions of the world
    wind = params.get("wind")
    if wind:
        for frac in (0.30, 0.52, 0.74):
            hazards.append(
                {
                    "type": "wind",
                    "x": int(length * frac),
                    "w": 300,
                    "y": 0,
                    "strength": float(wind[0]),
                    "cycle": 4.2,
                    "offset": frac * 3.1,
                }
            )

    return {
        "platforms": platforms,
        "hazards": hazards,
        "enemies": enemies,
        "checkpoints": checkpoints,
        "start_pos": (90, 360),
        "part_pos": (part_x, part_y),
        "exit_pos": (length - 170, final_top - 44),
        "world_w": length,
        "world_h": world_h,
        "ground_y": ground_y,
    }


def default_theme() -> dict:
    """Fallback palette so a half-authored level still renders."""
    return {
        "sky_top": (7, 10, 24),
        "sky_bottom": (16, 24, 46),
        "ridge_far": (26, 36, 62),
        "ridge_near": (18, 26, 46),
        "ground": (30, 41, 66),
        "ground_top": (74, 98, 134),
        "ground_edge": (48, 64, 96),
        "accent": (94, 230, 208),
        "hazard": (255, 179, 71),
        "stars": True,
    }
