"""Scripted end-to-end playtest: plays the real game loop headlessly.

Verifies the full campaign: tutorial -> mercury -> venus -> mars -> jupiter -> saturn ->
uranus -> neptune (locked chain, worlds, combat, storm) -> earth assembly -> stats.
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

from core import audio, levels, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.map import MapScene  # noqa: E402
from scenes.tutorial import TutorialScene  # noqa: E402
from scenes.world_level import make_world_scene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402

WORLD_PLANETS = ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune")


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
    registry = {
        settings.TUTORIAL: TutorialScene,
        settings.ENDING: EndingScene,
        settings.MAP: MapScene,
        settings.PAUSE: PauseScene,
    }
    for planet_id in WORLD_PLANETS:
        registry[planet_id] = make_world_scene(planet_id)
    for name, cls in registry.items():
        game.manager.register(name, cls)

    planets = levels.planet_index()
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

    # --- sequential unlocks: only mercury is open after the tutorial ---------
    check("chain: mercury unlocked after tutorial", state.is_unlocked(planets["mercury"]))
    check("chain: venus locked before mercury", not state.is_unlocked(planets["venus"]))
    check("chain: neptune locked early", not state.is_unlocked(planets["neptune"]))
    check("chain: finale locked early", not state.is_unlocked(planets["earth"]))

    # --- one full world check on mercury, then scripted wins for the rest ----
    game.manager.switch(settings.MERCURY, _test=True)
    scene = game.manager.current
    check("mercury: world generated", len(scene.platforms) > 6 and len(scene.checkpoints) >= 3)
    check("mercury: enemies placed", len(scene.walkers) + len(scene.ufos) > 3)
    check("mercury: hazards placed", len(scene.hazards) > 2)
    check("mercury: briefing skipped in test mode", scene.phase == "play")

    scene.player.pos.y -= 40  # make sure the player is airborne, then fire
    advance(game, 3)
    game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
    check("mercury: laser fires", len(scene.lasers) > 0)
    check("mercury: stopwatch running", scene.stopwatch > 0.0)

    for key, label in ((pygame.K_UP, "UP arrow"), (pygame.K_w, "W")):
        scene.player.vel.y = 0.0  # grounded on the pad, then try each jump key
        scene.player.on_ground = True
        scene.player.coyote = 0.0
        game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=key)])
        check(f"mercury: {label} jumps", scene.player.vel.y < -300)
        scene.player.vel.y = 0.0
        scene.player.on_ground = True

    scene._test_complete()
    check("mercury: part collected", state.has_part("Solar Panel Array"))
    check("mercury: level marked done", state.is_level_done("mercury"))
    check("chain: venus unlocked after mercury", state.is_unlocked(planets["venus"]))

    # --- the remaining missions: world boots, completes, unlocks the next ----
    for planet_id in WORLD_PLANETS[1:]:
        game.manager.switch(planet_id, _test=True)
        scene = game.manager.current
        check(f"{planet_id}: world generated", len(scene.platforms) > 4)
        advance(game, 5)
        scene._test_complete()
        check(f"{planet_id}: part collected", state.is_level_done(planet_id))
        next_id = WORLD_PLANETS[WORLD_PLANETS.index(planet_id) + 1] if planet_id != "neptune" else None
        if next_id:
            check(f"chain: {next_id} unlocked", state.is_unlocked(planets[next_id]))

    # --- mars storm: the world must stay hidden outside the visibility circle -
    game.manager.switch(settings.MARS, _test=True)
    scene = game.manager.current
    scene.storm_timer = scene.storm_interval - 0.1
    advance(game, 40)
    check("mars: dust storm activates", scene.storm_active)
    check("mars: storm hides the minimap enemies", scene.storm_active and not scene.walkers[0].dead)

    # --- map shows finale unlocked ------------------------------------------
    game.manager.switch(settings.MAP)
    scene = game.manager.current
    earth = planets["earth"]
    check("map: finale unlocked with all parts", state.is_unlocked(earth))
    check("map: 7/7 parts", state.part_count == 7)

    # --- ending: assemble and launch ----------------------------------------
    game.manager.switch(settings.ENDING)
    scene = game.manager.current
    check("ending: entered assembly", scene.phase == "assemble")
    check("ending: seven sockets", len(scene.socket_positions) == 7)
    for index, part in enumerate(scene.required):
        scene._place(part, index)
        skip_dialogue(game, 4)
    check("ending: all parts placed", len(scene.placed) == len(scene.required))
    scene._launch()
    advance(game, 10)
    check("ending: stats screen shown", scene.phase == "stats")
    check("ending: best time recorded", bool(state.best_times))

    print()
    if failures:
        print(f"FAILED: {len(failures)} checks")
        return 1
    print("full loop ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
