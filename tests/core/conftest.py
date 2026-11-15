"""Shared fixtures for the core-module test suite.

Every test in this package runs headless: the SDL dummy video/audio drivers are
selected *before* pygame is imported, and the repository root is placed on
``sys.path`` so ``import core.*`` resolves to E:\\nasa\\core.
"""

from __future__ import annotations

import os

# --- headless setup (must happen before pygame is imported) --------------------
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
from pathlib import Path

REPO_ROOT = Path(r"E:\nasa")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
import pygame

from core import levels, save, settings


# --- session-wide pygame bring-up --------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    """Initialise pygame once (no video mode; the dummy driver is in use)."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def isolated_save(tmp_path, monkeypatch):
    """Point ``settings.SAVE_FILE`` at a throwaway file for every test.

    Without this the suite would rewrite the real ``E:\\nasa\\savegame.json``.
    """
    target = tmp_path / "savegame.json"
    monkeypatch.setattr(settings, "SAVE_FILE", target)
    yield target


@pytest.fixture(autouse=True)
def clear_parts_cache():
    """``levels.required_parts`` is lru_cached - reset it around every test."""
    levels._required_parts_cached.cache_clear()
    yield
    levels._required_parts_cached.cache_clear()


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Redirect ``settings.DATA`` to an empty scratch directory."""
    scratch = tmp_path / "data"
    scratch.mkdir()
    monkeypatch.setattr(settings, "DATA", scratch)
    yield scratch


@pytest.fixture
def save_file(isolated_save):
    """The temporary save path in use for the current test."""
    return isolated_save


@pytest.fixture
def game_state():
    """A fresh :class:`core.game_state.GameState` with no progress."""
    from core.game_state import GameState

    return GameState()
