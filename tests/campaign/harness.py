"""Headless harness for the campaign-progression test suite.

Mirrors ``E:\\nasa\\main.py`` exactly:

    pygame.init(); audio.init()
    window = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    state = GameState()
    game = Game(virtual, window, state)
    game.manager.register(...)   # every scene main.py registers

and adds helpers to synthesise pygame input events and to run frames.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(r"E:\nasa")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from core import audio, save, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.boot import BootScene  # noqa: E402
from scenes.menu import MenuScene  # noqa: E402
from scenes.map import MapScene  # noqa: E402
from scenes.tutorial import TutorialScene  # noqa: E402
from scenes.world_level import make_world_scene  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.briefing import BriefingScene, register_mission_scenes  # noqa: E402
from scenes.level1 import Level1Scene  # noqa: E402
from scenes.level2 import Level2Scene  # noqa: E402
from scenes.level3 import Level3Scene  # noqa: E402
from scenes.level4 import Level4Scene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402

WORLD_PLANETS = settings.PLANET_SCENES

#: every scene name main.py registers
ALL_SCENES = (
    settings.BOOT,
    settings.MENU,
    settings.MAP,
    settings.TUTORIAL,
    *WORLD_PLANETS,
    settings.ENDING,
    settings.PAUSE,
    settings.BRIEFING,
    settings.LEVEL1,
    settings.LEVEL2,
    settings.LEVEL3,
    settings.LEVEL4,
)

_initialised = False


def _isolate_save() -> None:
    """Redirect the save file so the tests never touch the real savegame.json."""
    target = Path(os.environ.get("TEMP", ".")) / "laika_campaign_test_save.json"
    settings.SAVE_FILE = target
    save.SAVE_FILE = target if hasattr(save, "SAVE_FILE") else settings.SAVE_FILE


def init_pygame() -> None:
    global _initialised
    if _initialised:
        return
    _isolate_save()
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    _initialised = True


def make_game(state: GameState | None = None) -> Game:
    """Build a Game exactly like main.py does (same registrations)."""
    init_pygame()
    window = pygame.display.get_surface()
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    state = state if state is not None else GameState()
    game = Game(virtual, window, state)

    game.manager.register(settings.BOOT, BootScene)
    game.manager.register(settings.MENU, MenuScene)
    game.manager.register(settings.MAP, MapScene)
    game.manager.register(settings.TUTORIAL, TutorialScene)
    for planet_id in WORLD_PLANETS:
        game.manager.register(planet_id, make_world_scene(planet_id))
    game.manager.register(settings.ENDING, EndingScene)
    game.manager.register(settings.PAUSE, PauseScene)
    register_mission_scenes(game.manager)
    game.manager.register(settings.LEVEL2, Level2Scene)
    game.manager.register(settings.LEVEL3, Level3Scene)
    game.manager.register(settings.LEVEL4, Level4Scene)
    return game


# ---------------------------------------------------------------------------
# event synthesis
# ---------------------------------------------------------------------------

def key(key: int, mod: int = 0, unicode: str = "") -> pygame.event.Event:
    return pygame.event.Event(
        pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": unicode, "scancode": 0}
    )


def keyup(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYUP, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def click(pos: tuple[int, int], button: int = 1) -> pygame.event.Event:
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button, "touch": False}
    )


def motion(pos: tuple[int, int]) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)})


# ---------------------------------------------------------------------------
# frame running
# ---------------------------------------------------------------------------

def run_frames(
    game: Game,
    frames: int = 120,
    dt: float = 1 / 60.0,
    events: list[pygame.event.Event] | None = None,
    feed_events_every: int = 1,
) -> None:
    """Run `frames` frames of handle_events/update/draw like main.py does."""
    for index in range(frames):
        if events:
            if feed_events_every <= 1 or index % feed_events_every == 0:
                game.manager.handle_events(list(events))
        else:
            game.manager.handle_events([])
        game.manager.update(dt)
        game.manager.draw()


def capture(fn, *args, **kwargs):
    """Run `fn` and return (ok, exception-or-None, traceback-string)."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001
        return False, exc, traceback.format_exc()
    return True, None, ""


def describe(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def tb_tail(tb: str, lines: int = 12) -> str:
    return "\n".join(tb.splitlines()[-lines:])
