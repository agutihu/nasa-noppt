"""Temporary probe: is the inter-level BriefingScene usable at all?"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from core import audio, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.briefing import BriefingScene  # noqa: E402


def main() -> int:
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    window = pygame.display.get_surface()
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))

    state = GameState()
    game = Game(virtual, window, state)
    game.manager.register(settings.BRIEFING, BriefingScene)

    print("--- 1. construct BriefingScene through the manager ---")
    try:
        scene = game.manager.switch(settings.BRIEFING, level_id="outpost")
        print("OK constructed:", scene)
    except Exception as exc:  # noqa: BLE001
        print("CRASH:", type(exc).__name__, exc)
        traceback.print_exc()

    print("--- 2. press a key on the briefing (should advance to level 2) ---")
    try:
        for _ in range(5):
            game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
            game.manager.update(1 / 60.0)
        print("current scene:", game.manager.current_name)
    except Exception as exc:  # noqa: BLE001
        print("CRASH:", type(exc).__name__, exc)
        traceback.print_exc()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
