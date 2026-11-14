"""Async main loop — pygbag-ready, desktop default.

Scenes swap through ``SceneManager``; nothing blocks the loop (no sleeps, no network).
"""

from __future__ import annotations

import asyncio
import ctypes
import sys

import pygame

from core import audio, settings, text
from core.game_state import GameState
from core.scene import Game
from scenes.boot import BootScene
from scenes.menu import MenuScene
from scenes.map import MapScene
from scenes.tutorial import TutorialScene
from scenes.mars import MarsScene
from scenes.mercury import MercuryScene
from scenes.venus import VenusScene
from scenes.ending import EndingScene
from ui.pause import PauseScene


def _enable_dpi_awareness() -> None:
    """Opt out of Windows display scaling so text renders 1:1 and stays crisp."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


async def main() -> int:
    _enable_dpi_awareness()
    pygame.init()
    audio.init()

    window = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(settings.CAPTION)
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    clock = pygame.time.Clock()

    state = GameState()
    state.load()  # picks up preferences + progress if a save exists
    text.set_scale(state.text_scale)
    game = Game(virtual, window, state)

    game.manager.register(settings.BOOT, BootScene)
    game.manager.register(settings.MENU, MenuScene)
    game.manager.register(settings.MAP, MapScene)
    game.manager.register(settings.TUTORIAL, TutorialScene)
    game.manager.register(settings.MARS, MarsScene)
    game.manager.register(settings.MERCURY, MercuryScene)
    game.manager.register(settings.VENUS, VenusScene)
    game.manager.register(settings.ENDING, EndingScene)
    game.manager.register(settings.PAUSE, PauseScene)

    game.manager.switch(settings.BOOT)

    while game.running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game.running = False

        game.manager.handle_events(events)

        dt = clock.tick(settings.FPS) / 1000.0
        dt = min(dt, 0.05)  # never spiral after a freeze/tab switch
        game.manager.update(dt)

        virtual.fill(settings.SPACE)
        game.manager.draw()

        win_w, win_h = window.get_size()
        scale = min(win_w / settings.WIDTH, win_h / settings.HEIGHT)
        if abs(scale - 1.0) < 0.002:
            # exact fit: blit 1:1, no resampling — keeps text pixel-crisp
            window.fill(settings.SPACE_DEEP)
            window.blit(virtual, (0, 0))
        else:
            scaled = pygame.transform.smoothscale(
                virtual,
                (int(settings.WIDTH * scale), int(settings.HEIGHT * scale)),
            )
            rect = scaled.get_rect(center=(win_w // 2, win_h // 2))
            window.fill(settings.SPACE_DEEP)
            window.blit(scaled, rect)
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()
    return 0


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
