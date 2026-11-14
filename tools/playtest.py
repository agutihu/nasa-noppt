"""Scripted end-to-end playtest: plays the real game loop headlessly.

Verifies the full loop: tutorial win -> parts -> ending assembly -> stats.
Run: python tools/playtest.py
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
from scenes.tutorial import TutorialScene  # noqa: E402
from scenes.venus import VenusScene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402


class FakeKeys:
    def __init__(self) -> None:
        self.state: dict[int, bool] = {}

    def __getitem__(self, key: int) -> bool:
        return self.state.get(key, False)

    def hold(self, *names: str) -> None:
        self.state = {getattr(pygame, f"K_{name}"): True for name in names}


def advance(game: Game, frames: int = 1) -> None:
    clock = pygame.time.Clock()
    for _ in range(frames):
        game.manager.handle_events([])
        dt = min(clock.tick(60) / 1000.0, 0.05)
        game.manager.update(dt)
        game.manager.draw()


def skip_dialogue(game: Game, rounds: int = 12) -> None:
    """Send SPACE presses until every active dialogue box is gone."""
    for _ in range(rounds):
        scene = game.manager.current
        if not scene or not getattr(scene, "dlg", None):
            return
        if not scene.dlg.is_active():
            return
        advance(game, 6)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        game.manager.handle_events([event])


def main() -> int:
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    window = pygame.display.get_surface()
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))

    keys = FakeKeys()
    pygame.key.get_pressed = lambda: keys

    state = GameState()
    state.reset()
    game = Game(virtual, window, state)
    for name, cls in {
        settings.TUTORIAL: TutorialScene,
        settings.MARS: MarsScene,
        settings.MERCURY: MercuryScene,
        settings.VENUS: VenusScene,
        settings.ENDING: EndingScene,
        settings.MAP: MapScene,
        settings.PAUSE: PauseScene,
    }.items():
        game.manager.register(name, cls)

    failures: list[str] = []

    def check(label: str, condition: bool) -> None:
        status = "ok  " if condition else "FAIL"
        print(f"{status}  {label}")
        if not condition:
            failures.append(label)

    # --- tutorial -----------------------------------------------------------
    game.manager.switch(settings.TUTORIAL)
    advance(game, 10)
    skip_dialogue(game)
    check("tutorial: intro dialogue finished", game.manager.current.stage == "go_marker")

    scene = game.manager.current
    scene.player.pos.update(920, 290)  # teleport next to the beacon
    scene.player.rect.center = (920, 290)
    advance(game, 8)
    skip_dialogue(game)
    check("tutorial: reached beacon", scene.stage == "go_crate")

    scene.player.pos.update(508, 566)  # teleport onto the crate
    scene.player.rect.center = (508, 566)
    advance(game, 8)
    skip_dialogue(game)
    scene = game.manager.current
    check("tutorial: crate collected", scene.stage == "got_crate")

    game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)])
    advance(game, 5)
    skip_dialogue(game)
    advance(game, 5)
    skip_dialogue(game)
    check("tutorial: H task completes level", state.tutorial_done)
    check("tutorial: back on map", game.manager.current_name == settings.MAP)

    # --- mars: storm first (it freezes once the level is won) ---------------
    game.manager.switch(settings.MARS)
    scene = game.manager.current
    advance(game, 5)
    skip_dialogue(game)
    scene.storm_timer = 24.9
    advance(game, 40)
    check("mars: dust storm activates", scene.storm_active)

    part_pos = scene.params["part_pos"]
    scene.player.respawn(part_pos[0], part_pos[1])
    advance(game, 10)
    skip_dialogue(game)
    check("mars: part collected", state.has_part("Navigation Module"))

    # --- mercury: heat first, then the part ---------------------------------
    game.manager.switch(settings.MERCURY)
    scene = game.manager.current
    advance(game, 5)
    skip_dialogue(game)
    scene.player.pos.update(1600, 360)  # open ground, far right
    scene.player.rect.center = (1600, 360)
    scene.sun_x = 1400  # the terminator has passed the player: direct sunlight
    start_heat = scene.heat.value
    advance(game, 60)
    check("mercury: heat rises in sunlight", scene.heat.value > start_heat)

    part_pos = scene.params["part_pos"]
    scene.player.pos.update(part_pos[0], part_pos[1])
    scene.player.rect.center = (part_pos[0], part_pos[1])
    advance(game, 8)
    skip_dialogue(game)
    check("mercury: part collected", state.has_part("Solar Panel Array"))

    # --- venus: fragments then exit ----------------------------------------
    game.manager.switch(settings.VENUS)
    scene = game.manager.current
    advance(game, 5)
    skip_dialogue(game)
    for fragment in scene.fragments:
        scene.player.pos.update(fragment.pos)
        scene.player.rect.center = (round(fragment.pos.x), round(fragment.pos.y))
        advance(game, 3)
    check("venus: all fragments collected", scene.collected == scene.frag_needed)
    scene.player.pos.update(scene.exit_pos)
    scene.player.rect.center = (round(scene.exit_pos.x), round(scene.exit_pos.y))
    advance(game, 10)
    check("venus: escape triggers win", state.has_part("Hull Plating"))

    # --- map shows finale unlocked -----------------------------------------
    game.manager.switch(settings.MAP)
    scene = game.manager.current
    earth = next(p for p in scene.planets if p["id"] == "earth")
    check("map: finale unlocked with all parts", state.is_unlocked(earth))
    check("map: 3/3 parts", state.part_count == 3)

    # --- ending: assemble and launch ----------------------------------------
    game.manager.switch(settings.ENDING)
    scene = game.manager.current
    check("ending: entered assembly", scene.phase == "assemble")
    for index, part in enumerate(scene.required):
        scene._place(part, index)
        skip_dialogue(game, 4)
    check("ending: all parts placed", len(scene.placed) == len(scene.required))
    scene._launch()
    advance(game, 10)
    check("ending: stats screen shown", scene.phase == "stats")

    print()
    if failures:
        print(f"FAILED: {len(failures)} checks")
        return 1
    print("full loop ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
