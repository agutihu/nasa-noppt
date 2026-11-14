"""Per-planet parallax backdrops for the world levels.

A baked sky (gradient, stars, gas bands, ring arcs, storm spots) plus two silhouette
ridge layers that scroll at different speeds, so the world reads as depth and distance.
"""

from __future__ import annotations

import math
import random

import pygame

from core import color as core_color, settings

hex_to_rgb = core_color.hex_to_rgb


def _color(value) -> tuple:
    """Accept hex strings or RGB tuples, return an RGB tuple."""
    if isinstance(value, str):
        return hex_to_rgb(value)
    return tuple(value)


def _gradient(width: int, height: int, top: tuple, bottom: tuple) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    for y in range(height):
        blend = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * blend) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


def _draw_sky_extras(sky: pygame.Surface, theme: dict, rng: random.Random) -> None:
    # gas bands (Jupiter / Saturn / Uranus / Neptune)
    for index in range(theme.get("bands", 0)):
        y = int(sky.get_height() * (0.12 + 0.7 * index / max(1, theme.get("bands", 1))))
        band_h = rng.randint(14, 42)
        band_colors = [_color(value) for value in theme.get("band_colors", [(0, 0, 0)])]
        color = band_colors[index % len(band_colors)]
        wave = pygame.Surface((sky.get_width(), band_h * 2), pygame.SRCALPHA)
        points = []
        for x in range(0, sky.get_width() + 40, 40):
            points.append((x, band_h + math.sin(x * 0.012 + index) * band_h * 0.35))
        pygame.draw.polygon(
            wave,
            (*color, 120),
            [(x, y) for x, y in points] + [(sky.get_width() + 40, band_h * 2), (0, band_h * 2)],
        )
        sky.blit(wave, (0, y - band_h))

    # ring arc crossing the sky (Saturn, Uranus)
    if theme.get("sky_ring"):
        ring_color = _color(theme.get("sky_ring_color", (220, 200, 160)))
        w, h = sky.get_width(), sky.get_height()
        for offset in range(-3, 4):
            width = 2 if abs(offset) != 2 else 4
            pygame.draw.ellipse(
                sky,
                ring_color,
                pygame.Rect(-w // 3, int(h * 0.18) + offset * 7, int(w * 1.5), int(h * 0.34)),
                width,
            )

    # great storm spot (Jupiter / Neptune)
    if theme.get("storm_spot"):
        cx, cy = int(sky.get_width() * 0.62), int(sky.get_height() * 0.55)
        color = _color(theme["storm_spot"])
        for radius, alpha in ((70, 70), (52, 110), (34, 160)):
            blob = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, (*color, alpha), (0, 0, radius * 2, int(radius * 1.4)))
            sky.blit(blob, (cx - radius, cy - radius // 1))

    # stars for airless / thin atmospheres
    if theme.get("stars"):
        for _ in range(90):
            x = rng.randint(0, sky.get_width() - 1)
            y = rng.randint(0, int(sky.get_height() * 0.7))
            brightness = rng.randint(90, 230)
            pygame.draw.circle(
                sky, (brightness, brightness, min(255, brightness + 20)), (x, y), rng.choice((1, 1, 1, 2))
            )


def _ridge_layer(width: int, height: int, color: tuple, seed: int, style: str) -> pygame.Surface:
    """A silhouette strip anchored to its bottom edge."""
    rng = random.Random(seed)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    base_y = height
    points = [(0, base_y)]
    x = 0
    while x < width:
        step = rng.randint(60, 150)
        if style == "craters":
            # mesas and crater rims: flat tops with sharp edges
            peak = height - rng.randint(20, height // 2)
            points.append((x + step // 2, peak))
            points.append((x + step, height - rng.randint(0, 30)))
        elif style == "dunes":
            peak = height - int(height * 0.25 * (1 + math.sin(x * 0.006 + seed)))
            points.append((x + step, peak))
        elif style == "clouds":
            peak = height - rng.randint(30, height - 10)
            points.append((x + step // 2, peak))
            points.append((x + step, height - rng.randint(10, 60)))
        else:  # shards (ice worlds)
            peak = height - rng.randint(20, height)
            points.append((x + step // 2, peak))
            points.append((x + step, height - rng.randint(0, 20)))
        x += step
    points.append((width, base_y))
    pygame.draw.polygon(surface, (*color, 255), points)

    if style == "craters":
        for _ in range(6):
            crater_x = rng.randint(20, width - 40)
            crater_y = rng.randint(height // 2, height - 12)
            crater_r = rng.randint(6, 18)
            pygame.draw.ellipse(surface, (*color, 255), (crater_x, crater_y, crater_r * 2, crater_r))
    return surface


def make_backdrop(theme: dict, seed: int) -> dict:
    """Bake sky + two parallax ridge layers for a planet theme."""
    rng = random.Random(seed)
    sky = _gradient(settings.WIDTH, settings.HEIGHT, theme["sky_top"], theme["sky_bottom"])
    _draw_sky_extras(sky, theme, rng)

    style = theme.get("ridge_style", "dunes")
    far = _ridge_layer(settings.WIDTH, 240, theme["ridge_far"], seed * 7 + 1, style)
    near = _ridge_layer(settings.WIDTH, 170, theme["ridge_near"], seed * 13 + 5, style)

    return {"sky": sky, "layers": [(far, 0.22), (near, 0.45)]}


def draw_backdrop(backdrop: dict, screen: pygame.Surface, camera_x: float) -> None:
    """Draw the baked sky and parallax ridges, sized for whatever surface they go on."""
    width, height = screen.get_size()
    sky = backdrop.get("sky_scaled")
    if sky is None or sky.get_size() != (width, height):
        sky = pygame.transform.scale(backdrop["sky"], (width, height))
        backdrop["sky_scaled"] = sky
    screen.blit(sky, (0, 0))
    for layer, factor in backdrop["layers"]:
        key = f"layer_{factor}"
        scaled = backdrop.get(key)
        if scaled is None or scaled.get_width() != width:
            scaled = pygame.transform.scale(layer, (width, layer.get_height()))
            backdrop[key] = scaled
        off = int(camera_x * factor) % width
        screen.blit(scaled, (-off, height - scaled.get_height()))
        screen.blit(scaled, (-off + width, height - scaled.get_height()))
