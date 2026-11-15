"""Small colour helpers so JSON can carry hex strings."""

from __future__ import annotations


def hex_to_rgb(value: str, fallback: tuple[int, int, int] = (200, 200, 200)) -> tuple[int, int, int]:
    if not value:
        return fallback
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    if len(value) != 6:
        return fallback
    try:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return fallback


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))  # type: ignore[return-value]


def scale(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)  # type: ignore[return-value]


def blend_over(color: tuple[int, int, int], background: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    return mix(background, color, alpha)
