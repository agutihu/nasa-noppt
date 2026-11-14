"""One-off: render map panel screenshots for layout verification (headless)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from core import settings
from core.game_state import GameState
from core.scene import Game
from scenes.map import MapScene

OUT = Path(__file__).resolve().parent / "shots"
OUT.mkdir(exist_ok=True)

pygame.init()
pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
screen = pygame.display.get_surface()

state = GameState()
state.parts = ["Solar Panel Array"]  # 1/3: mix of RECOVERED / READY / LOCKED chips
state.tutorial_done = True

game = Game(screen, screen, state)
scene = MapScene(game)
scene.name = settings.MAP
scene.on_enter()


def shot(name: str) -> None:
    pygame.event.pump()
    scene.update(1 / 60)
    scene.draw(screen)
    pygame.image.save(screen, str(OUT / f"{name}.png"))


shot("00_none")
for planet in scene.planets:
    scene.select(planet)
    shot(planet["id"])

pygame.quit()
print("saved:", sorted(p.name for p in OUT.glob("*.png")))
