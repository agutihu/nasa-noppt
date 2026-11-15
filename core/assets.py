"""Asset loading with graceful fallbacks.

Every loader returns something usable: if a file is missing we return ``None`` and the
caller draws a primitive instead. The game must run with an empty ``assets/`` folder.
"""

from __future__ import annotations

import pygame

from core import settings

_font_cache: dict[tuple[int, str], pygame.font.Font] = {}
_image_cache: dict[tuple[str, int | None], pygame.Surface | None] = {}

_SYSTEM_FALLBACK = "consolas,couriernew,dejavusansmono,monospace"


def path(*parts: str) -> str:
    """Resolve a path under ``assets/``. Returns ``""`` when the file is missing."""
    candidate = settings.ASSETS.joinpath(*parts)
    return str(candidate) if candidate.exists() else ""


def font(size: int, name: str | None = None) -> pygame.font.Font:
    size = max(8, int(size))
    name = name or settings.FONT_BODY
    key = (size, name)
    cached = _font_cache.get(key)
    if cached is not None:
        return cached

    loaded: pygame.font.Font | None = None
    source = settings.ASSETS / "fonts" / name
    if source.exists():
        try:
            loaded = pygame.font.Font(str(source), size)
        except (pygame.error, OSError):
            loaded = None
    if loaded is None:
        loaded = pygame.font.SysFont(_SYSTEM_FALLBACK, size)

    _font_cache[key] = loaded
    return loaded


def image(relative: str, scale: int | None = None) -> pygame.Surface | None:
    """Load an image from ``assets/images``. Returns ``None`` if unavailable."""
    key = (relative, scale)
    if key in _image_cache:
        return _image_cache[key]

    surface: pygame.Surface | None = None
    source = path("images", relative)
    if source:
        try:
            loaded = pygame.image.load(source)
            surface = loaded.convert_alpha()
            if scale:
                w, h = surface.get_size()
                surface = pygame.transform.smoothscale(
                    surface, (max(1, w * scale), max(1, h * scale))
                )
        except (pygame.error, OSError):
            surface = None

    _image_cache[key] = surface
    return surface


def portrait(size: int) -> pygame.Surface | None:
    """Laika's pixel-art portrait, scaled with nearest-neighbour to stay crisp.

    Returns ``None`` when the file is missing; every caller falls back to the
    procedural ``sprites.draw_laika`` hologram.
    """
    key = ("portrait", size)
    if key in _image_cache:
        return _image_cache[key]

    source = settings.ASSETS / "images" / settings.PORTRAIT
    surface: pygame.Surface | None = None
    if source.exists():
        try:
            loaded = pygame.image.load(str(source))
            if loaded.get_flags() & pygame.SRCALPHA:
                loaded = loaded.convert_alpha()
            else:
                loaded = loaded.convert()
            surface = pygame.transform.scale(loaded, (size, size))
        except (pygame.error, OSError, ValueError):
            surface = None

    _image_cache[key] = surface
    return surface


def clear_cache() -> None:
    _font_cache.clear()
    _image_cache.clear()
