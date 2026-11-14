"""Headless smoke test: boots every scene and runs frames without a display.

Run from the project root::

    python tools/smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from core import audio, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.map import MapScene  # noqa: E402

from scenes.mars import MarsScene  # noqa: E402
from scenes.mercury import MercuryScene  # noqa: E402
from scenes.menu import MenuScene  # noqa: E402
from scenes.tutorial import TutorialScene  # noqa: E402
from scenes.venus import VenusScene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402


def run_scene(game: Game, name: str, frames: int = 30) -> None:
    game.manager.switch(name)
    clock = pygame.time.Clock()
    for _ in range(frames):
        game.manager.handle_events([])
        dt = min(clock.tick(60) / 1000.0, 0.05)
        game.manager.update(dt)
        game.manager.draw()


def main() -> int:
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    window = pygame.display.get_surface()
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))

    state = GameState()
    game = Game(virtual, window, state)

    registry = {
        settings.TUTORIAL: TutorialScene,
        settings.MARS: MarsScene,
        settings.MERCURY: MercuryScene,
        settings.VENUS: VenusScene,
        settings.ENDING: EndingScene,
        settings.MENU: MenuScene,
        settings.MAP: MapScene,
        settings.PAUSE: PauseScene,
    }
    for name, cls in registry.items():
        game.manager.register(name, cls)

    failures = []

    for name in (
        settings.TUTORIAL,
        settings.MARS,
        settings.MERCURY,
        settings.VENUS,
        settings.MENU,
        settings.MAP,
        settings.PAUSE,
    ):
        try:
            run_scene(game, name)
            print(f"ok    {name}")
        except Exception as exc:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            failures.append(name)
            print(f"FAIL  {name}: {exc}")

    # ending requires all parts; force them for the test
    for part in state.required_parts():
        state.add_part(part)
    try:
        run_scene(game, settings.ENDING)
        print("ok    ending")
    except Exception as exc:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        failures.append(settings.ENDING)
        print(f"FAIL  ending: {exc}")

    pygame.quit()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("all scenes ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
