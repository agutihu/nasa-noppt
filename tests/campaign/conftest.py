"""Shared fixtures for the campaign test-suite."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

from harness import make_game  # noqa: E402
from core.game_state import GameState  # noqa: E402


@pytest.fixture()
def state() -> GameState:
    """A fresh, save-isolated game state."""
    return GameState()


@pytest.fixture()
def game(state: GameState):
    """A Game built exactly like main.py builds it."""
    return make_game(state)
