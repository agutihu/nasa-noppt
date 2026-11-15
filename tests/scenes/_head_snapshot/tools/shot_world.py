"""One-off: render world-level screenshots for visual verification (headless)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from core import audio, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.map import MapScene  # noqa: E402
from scenes.tutorial import TutorialScene  # noqa: E402
from scenes.world_level import make_world_scene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402

OUT = Path(__file__).resolve().parent / "shots"
OUT.mkdir(exist_ok=True)

WORLD_PLANETS = settings.PLANET_SCENES


def advance(game: Game, frames: int) -> None:
    clock = pygame.time.Clock()
    for _ in range(frames):
        game.manager.handle_events([])
        dt = min(clock.tick(60) / 1000.0, 0.05)
        game.manager.update(dt)
        game.manager.draw()


def save(game: Game, name: str) -> None:
    game.manager.draw()
    pygame.image.save(game.screen, str(OUT / f"{name}.png"))
    print("saved", name)


def main() -> int:
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    window = pygame.display.get_surface()

    state = GameState()
    state.tutorial_done = True
    state.add_part("Solar Panel Array")
    game = Game(window, window, state)

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

    # mission brief card (no _test -> briefing shows)
    game.manager.switch("mars")
    save(game, "brief_mars")

    # each world mid-flight
    for planet_id in WORLD_PLANETS:
        game.manager.switch(planet_id, _test=True)
        advance(game, 45)
        scene = game.manager.current
        # walk the player forward a bit so the shot shows terrain ahead
        scene.player.pos.x += 420
        scene.player.rect.center = (round(scene.player.pos.x), round(scene.player.pos.y))
        advance(game, 20)
        save(game, f"world_{planet_id}")

    # mars with the storm active (visibility fix)
    game.manager.switch("mars", _test=True)
    advance(game, 30)
    scene = game.manager.current
    scene.storm_timer = scene.storm_interval - 0.1
    advance(game, 45)
    check = game.manager.current
    print("storm active:", check.storm_active)
    save(game, "mars_storm")

    # ending assembly with seven sockets
    for part in state.required_parts():
        state.add_part(part)
    game.manager.switch(settings.ENDING)
    save(game, "ending_assembly")

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
