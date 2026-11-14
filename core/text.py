"""Text helpers: cached wrapping plus a shadowed draw call used by every screen."""

from __future__ import annotations

import pygame

from core import assets, settings

_wrap_cache: dict[tuple[str, int, int, bool], list[str]] = {}
_scale: float = 1.0


def set_scale(value: float) -> None:
    """Accessibility: global text size (1.0 = normal, 1.25 = large)."""
    global _scale
    _scale = max(0.8, min(1.6, float(value)))
    _wrap_cache.clear()


def get_scale() -> float:
    return _scale


def font(size: int, display: bool = False) -> pygame.font.Font:
    size = int(round(size * _scale))
    name = settings.FONT_DISPLAY if display else settings.FONT_BODY
    return assets.font(size, name)


def wrap(text: str, size: int, max_width: int, display: bool = False) -> list[str]:
    key = (text, size, max_width, display)
    cached = _wrap_cache.get(key)
    if cached is not None:
        return cached

    fnt = font(size, display)
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = f"{line} {word}"
            if fnt.size(trial)[0] <= max_width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)

    _wrap_cache[key] = lines
    return lines


def measure(text: str, size: int, display: bool = False) -> tuple[int, int]:
    return font(size, display).size(text)


def draw(
    surface: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    size: int = 22,
    color: tuple[int, int, int] = settings.INK,
    *,
    display: bool = False,
    center: bool = False,
    right: bool = False,
    middle: bool = False,
    shadow: bool = True,
    max_width: int | None = None,
    line_gap: int = 2,
    alpha: int = 255,
) -> pygame.Rect:
    """Draw text (wrapped when ``max_width`` is given) and return its bounding box."""
    fnt = font(size, display)
    lines = wrap(text, size, max_width, display) if max_width else text.split("\n")
    line_h = fnt.get_linesize() + line_gap
    total_h = line_h * len(lines) - line_gap

    x, y = pos
    if center:
        x -= max((fnt.size(line)[0] for line in lines), default=0) // 2
    if right:
        x -= max((fnt.size(line)[0] for line in lines), default=0)
    if middle:
        y -= total_h // 2

    bounds = pygame.Rect(x, y, 0, total_h)
    for index, line in enumerate(lines):
        rendered = fnt.render(line, True, color)
        if alpha < 255:
            rendered = rendered.copy()
            rendered.set_alpha(alpha)
        line_pos = (x, y + index * line_h)
        if shadow:
            shadow_img = fnt.render(line, True, (0, 0, 0))
            if alpha < 255:
                shadow_img = shadow_img.copy()
                shadow_img.set_alpha(min(alpha, 120))
            surface.blit(shadow_img, (line_pos[0] + 2, line_pos[1] + 2))
        surface.blit(rendered, line_pos)
        bounds.width = max(bounds.width, rendered.get_width())

    return bounds


def draw_centered(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    size: int = 22,
    color: tuple[int, int, int] = settings.INK,
    *,
    display: bool = False,
    max_width: int | None = None,
    shadow: bool = True,
    alpha: int = 255,
) -> pygame.Rect:
    fnt = font(size, display)
    lines = wrap(text, size, max_width, display) if max_width else text.split("\n")
    line_h = fnt.get_linesize() + 2
    total_h = line_h * len(lines) - 2
    top = center[1] - total_h // 2
    widest = max((fnt.size(line)[0] for line in lines), default=0)
    left = center[0] - widest // 2
    return draw(
        surface,
        text,
        (left, top),
        size,
        color,
        display=display,
        shadow=shadow,
        max_width=max_width,
        alpha=alpha,
    )
