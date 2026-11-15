"""Scratch probe #2 (not a test): drive every scene with synthetic input."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *  # noqa

init_pygame()
game = make_game()

names = [
    settings.BOOT, settings.MENU, settings.MAP, settings.TUTORIAL,
    *WORLD_PLANETS, settings.ENDING, settings.PAUSE,
    settings.LEVEL1, settings.LEVEL2, settings.LEVEL3, settings.LEVEL4,
]

EVENT_SETS = {
    "keys": all_key_events(),
    "clicks": all_click_events(),
    "quit": [quit_event()],
}

for name in names:
    for label, evs in EVENT_SETS.items():
        try:
            game.manager.switch(name)
            run_frames(game, 120, events=evs)
            print(f"ok    {name} [{label}]")
        except Exception as exc:
            print(f"FAIL  {name} [{label}]: {type(exc).__name__}: {exc}")
            traceback.print_exc()
