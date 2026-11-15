"""Pause overlay: resume, restart, sound, quit to map."""

from __future__ import annotations

import pygame

from core import audio, settings, text
from core.scene import Scene
from ui.button import Button

PANEL = pygame.Rect(settings.WIDTH // 2 - 210, 178, 420, 372)


class PauseScene(Scene):
    name = settings.PAUSE

    def __init__(self, game) -> None:
        super().__init__(game)
        self.parent = None
        self.buttons: list[Button] = []
        self.focus = 0

    def on_enter(self, **data) -> None:
        self.parent = data.get("parent")
        audio.set_muted(self.state.muted)
        self._build()

    def _build(self) -> None:
        y = PANEL.y + 108
        width = PANEL.width - 72
        left = PANEL.x + 36

        self.buttons = [
            Button((left, y, width, 52), "Resume", self.resume),
            Button((left, y + 64, width, 52), "Restart mission", self.restart, style="ghost"),
            Button(
                (left, y + 128, width, 52),
                f"Sound: {'Off' if self.state.muted else 'On'}",
                self.toggle_sound,
                style="ghost",
            ),
            Button((left, y + 192, width, 52), "Quit to map", self.quit_to_map, style="danger"),
        ]
        if 0 <= self.focus < len(self.buttons):
            self.buttons[self.focus].focused = True

    # --- actions ------------------------------------------------------------
    def resume(self) -> None:
        self.manager.pop()

    def restart(self) -> None:
        name = getattr(self.parent, "name", settings.MAP) if self.parent else settings.MAP
        self.manager.switch(name)

    def toggle_sound(self) -> None:
        self.state.muted = not self.state.muted
        self.state.save()
        audio.set_muted(self.state.muted)
        self._build()

    def quit_to_map(self) -> None:
        self.state.save()
        self.manager.switch(settings.MAP)

    # --- loop ---------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.resume()
                    return
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.focus = (self.focus + 1) % len(self.buttons)
                    self._sync_focus()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.focus = (self.focus - 1) % len(self.buttons)
                    self._sync_focus()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.buttons[self.focus].activate()
                    return
        for button in self.buttons:
            if button.handle_events(events):
                return

    def _sync_focus(self) -> None:
        for index, button in enumerate(self.buttons):
            button.focused = index == self.focus

    def draw(self, screen: pygame.Surface) -> None:
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 4, 10, 190))
        screen.blit(veil, (0, 0))

        pygame.draw.rect(screen, settings.PANEL, PANEL, border_radius=14)
        pygame.draw.rect(screen, settings.PANEL_EDGE, PANEL, 1, border_radius=14)
        text.draw(screen, "PAUSED", (PANEL.centerx, PANEL.y + 48), 26, settings.ACCENT, display=True, center=True)
        text.draw(
            screen,
            "Laika is holding the map steady.",
            (PANEL.centerx, PANEL.y + 78),
            19,
            settings.DIM,
            center=True,
            shadow=False,
        )
        for button in self.buttons:
            button.draw(screen)
