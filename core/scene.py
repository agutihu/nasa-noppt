"""Scene stack and manager.

Every screen is a ``Scene`` with the same four hooks. The manager never inspects what a
scene does, which is why a new planet only needs a register call in ``main.py``.
"""

from __future__ import annotations

from typing import Callable

import pygame

from core import settings


class Scene:
    name = "scene"
    counts_time = False

    def __init__(self, game) -> None:
        self.game = game
        self.screen: pygame.Surface = game.screen
        self.state = game.state
        self.manager = game.manager

    def on_enter(self, **data) -> None:
        """Called once when the scene becomes active."""

    def on_exit(self) -> None:
        """Called when the scene is removed or replaced."""

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pass


class SceneManager:
    def __init__(self, game) -> None:
        self.game = game
        self.state = game.state
        self.screen: pygame.Surface = game.screen
        self.registry: dict[str, Callable[[object], Scene]] = {}
        self.stack: list[Scene] = []

    # --- registration -------------------------------------------------------
    def register(self, name: str, factory: Callable[[object], Scene]) -> None:
        self.registry[name] = factory

    # --- transitions --------------------------------------------------------
    def switch(self, name: str, **data) -> Scene:
        factory = self._factory(name)
        if self.stack:
            self.stack[-1].on_exit()
        self.stack = []
        scene = factory(self.game)
        self._assert_name(scene, name)
        self.stack.append(scene)
        scene.on_enter(**data)
        return scene

    def push(self, name: str, **data) -> Scene:
        """Open an overlay; the scene below keeps drawing but stops updating."""
        factory = self._factory(name)
        scene = factory(self.game)
        self._assert_name(scene, name)
        self.stack.append(scene)
        scene.on_enter(**data)
        return scene

    def pop(self) -> None:
        if not self.stack:
            return
        scene = self.stack.pop()
        scene.on_exit()

    def reload(self) -> Scene:
        if not self.stack:
            raise RuntimeError("Nothing to reload")
        return self.switch(self.stack[-1].name)

    @property
    def current(self) -> Scene | None:
        return self.stack[-1] if self.stack else None

    @property
    def current_name(self) -> str:
        return self.stack[-1].name if self.stack else ""

    # --- loop ---------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.stack:
            self.stack[-1].handle_events(events)

    def update(self, dt: float) -> None:
        if not self.stack:
            return
        scene = self.stack[-1]
        if scene.counts_time:
            self.state.elapsed += dt
        scene.update(dt)

    def draw(self) -> None:
        for scene in self.stack:
            scene.draw(self.screen)

    # --- helpers ------------------------------------------------------------
    def _factory(self, name: str) -> Callable[[object], Scene]:
        factory = self.registry.get(name)
        if factory is None:
            raise KeyError(f"No scene registered under '{name}'")
        return factory

    @staticmethod
    def _assert_name(scene: Scene, expected: str) -> None:
        if not scene.name:
            scene.name = expected


class Game:
    """Small container handed to every scene: virtual screen, window, state, manager."""

    def __init__(self, screen: pygame.Surface, window: pygame.Surface, state) -> None:
        self.screen = screen
        self.window = window
        self.state = state
        self.manager: SceneManager = SceneManager(self)
        self.running = True

    def quit(self) -> None:
        self.running = False

    def scale_mouse(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Translate a window coordinate into the 1280x720 virtual canvas."""
        win_w, win_h = self.window.get_size()
        if win_w <= 0 or win_h <= 0:
            return (0, 0)
        scale = min(win_w / settings.WIDTH, win_h / settings.HEIGHT)
        offset_x = (win_w - settings.WIDTH * scale) / 2
        offset_y = (win_h - settings.HEIGHT * scale) / 2
        return (
            int((pos[0] - offset_x) / scale),
            int((pos[1] - offset_y) / scale),
        )
