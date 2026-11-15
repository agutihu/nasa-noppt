"""Shared headless setup for the DATA + ART validation suite.

Rules enforced here:
  * SDL dummy video/audio drivers are set BEFORE pygame is imported.
  * ``E:\\nasa`` is put on ``sys.path`` so ``import core`` / ``import art`` work.
  * pygame is initialised exactly once per session (display + font).
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = r"E:\nasa"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402  (must come after the SDL env vars)

DATA = os.path.join(ROOT, "data")
ART = os.path.join(ROOT, "art")

_LEVELS_DIR = os.path.join(DATA, "levels")
_DIALOGUE_DIR = os.path.join(DATA, "dialogue")
_CACHE_DIR = os.path.join(DATA, "cache")

#: The seven parts the game requires, spelled exactly as the game stores them.
REQUIRED_PARTS = (
    "Solar Panel Array",
    "Hull Plating",
    "Navigation Module",
    "Shield Generator",
    "Fuel Cells",
    "Thermal Regulator",
    "Signal Antenna",
)

#: The seven playable planets, in campaign order.
PLANET_IDS = (
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
)

#: Level files that describe a full world level (scenes/world_level.py).
WORLD_LEVEL_IDS = PLANET_IDS


def _init_pygame() -> None:
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()


_init_pygame()


def pytest_report_header(config):  # pragma: no cover - cosmetic
    return f"pygame-ce {pygame.version.ver} / SDL {pygame.version.SDL} / root={ROOT}"
