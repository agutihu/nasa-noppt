"""Synthesised sound effects.

We generate every effect in code so the project needs no audio files, then fall back to
silence when the mixer is unavailable (headless tests, locked audio devices, web builds).
"""

from __future__ import annotations

import math
from array import array

import pygame

_enabled = False
_muted = False
_volume = 0.8
_sounds: dict[str, pygame.mixer.Sound] = {}

SAMPLE_RATE = 44100
_MAX_AMP = 32767

# name -> (start_hz, end_hz, milliseconds, volume, waveform)
_RECIPES: dict[str, tuple[float, float, int, float, str]] = {
    "click": (880, 1180, 55, 0.30, "square"),
    "hover": (660, 660, 28, 0.12, "sine"),
    "dialogue": (520, 660, 34, 0.16, "square"),
    "pickup": (660, 1320, 160, 0.35, "sine"),
    "part": (440, 1760, 260, 0.40, "sine"),
    "jump": (320, 720, 130, 0.25, "sine"),
    "hit": (220, 90, 200, 0.40, "square"),
    "win": (520, 1040, 420, 0.35, "sine"),
    "lose": (300, 120, 420, 0.35, "square"),
    "back": (700, 380, 90, 0.25, "sine"),
    "laser": (1400, 320, 120, 0.22, "square"),
    "boom": (160, 40, 320, 0.45, "square"),
    # mission sounds
    "camera": (2400, 900, 70, 0.25, "square"),
    "alarm": (900, 480, 280, 0.28, "square"),
    "deny": (320, 170, 190, 0.28, "square"),
    "beep": (1000, 1000, 55, 0.18, "sine"),
    "confirm": (700, 1320, 150, 0.26, "sine"),
    "vacuum": (190, 260, 130, 0.16, "square"),
    "power_down": (760, 150, 460, 0.28, "sine"),
    "wind": (320, 110, 520, 0.22, "sine"),
    "step": (210, 140, 45, 0.12, "square"),
    "spark": (1300, 300, 90, 0.20, "square"),
    "radio": (620, 880, 110, 0.18, "sine"),
    "rumble": (90, 55, 420, 0.32, "sine"),
}


def init() -> None:
    """Initialise the mixer once. Safe to call repeatedly."""
    global _enabled
    if _enabled:
        return
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.mixer.init()
        _enabled = True
        _build_all()
    except (pygame.error, OSError):
        _enabled = False


def _build_all() -> None:
    for name, recipe in _RECIPES.items():
        try:
            _sounds[name] = _make_sound(*recipe)
        except (pygame.error, ValueError):
            continue


def _make_sound(
    start_hz: float, end_hz: float, ms: int, volume: float, wave: str
) -> pygame.mixer.Sound:
    frames = max(1, int(SAMPLE_RATE * ms / 1000))
    attack = max(1, int(frames * 0.08))
    release = max(1, int(frames * 0.35))
    samples = array("h")

    phase = 0.0
    for i in range(frames):
        progress = i / frames
        hz = start_hz + (end_hz - start_hz) * progress
        phase += 2.0 * math.pi * hz / SAMPLE_RATE

        if wave == "square":
            value = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            value = math.sin(phase)

        if i < attack:
            envelope = i / attack
        elif i > frames - release:
            envelope = (frames - i) / release
        else:
            envelope = 1.0

        samples.append(int(_MAX_AMP * volume * envelope * value))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def play(name: str, gain: float = 1.0) -> None:
    if not _enabled or _muted or _volume <= 0.0:
        return
    sound = _sounds.get(name)
    if sound is None:
        return
    try:
        sound.set_volume(max(0.0, min(1.0, _volume * gain)))
        sound.play()
    except pygame.error:
        pass


def set_volume(value: float) -> None:
    global _volume
    _volume = max(0.0, min(1.0, float(value)))


def get_volume() -> float:
    return _volume


def set_muted(value: bool) -> None:
    global _muted
    _muted = bool(value)


def is_muted() -> bool:
    return _muted or not _enabled
