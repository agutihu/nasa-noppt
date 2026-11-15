"""Centered modal panel used for failures, warnings and mission cards."""

from __future__ import annotations

import pygame

from core import audio, settings, text
from ui.button import Button


class Modal:
    def __init__(
        self,
        title: str,
        body: str = "",
        *,
        tone: str = "danger",
        kicker: str = "",
        buttons: list[tuple[str, object, str]] | None = None,
        footer: str = "",
        width: int = 660,
    ) -> None:
        self.title = title
        self.body = body
        self.tone = {
            "danger": settings.DANGER,
            "warn": settings.WARN,
            "good": settings.GREEN,
            "info": settings.ACCENT,
        }.get(tone, settings.ACCENT)
        self.kicker = kicker
        self.footer = footer
        self.width = width
        self.t = 0.0

        self.rect = pygame.Rect(0, 0, width, 300)
        self.buttons: list[Button] = []
        specs = buttons or [("Continue", None, "primary")]
        self._height = self._measure_height(specs)
        self.rect.height = self._height
        self.rect.center = (settings.WIDTH // 2, settings.HEIGHT // 2 - 20)

        y = self.rect.bottom - 74
        total = len(specs)
        each = (self.width - 80 - (total - 1) * 16) // total
        for index, (label, callback, style) in enumerate(specs):
            self.buttons.append(
                Button(
                    (self.rect.x + 40 + index * (each + 16), y, each, 46),
                    label,
                    callback,
                    style=style,
                    size=20,
                )
            )
        if self.buttons:
            self.buttons[0].focused = True
        self.focus = 0

    # --- layout -------------------------------------------------------------
    def _measure_height(self, specs) -> int:
        body_lines = text.wrap(self.body, 21, self.width - 96) if self.body else []
        height = 132 + len(body_lines) * 24
        if self.kicker:
            height += 24
        if self.footer:
            height += 26
        height += 78
        return max(height, 250)

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_RIGHT):
                    self.focus = (self.focus + 1) % max(1, len(self.buttons))
                    self._sync_focus()
                elif event.key in (pygame.K_LEFT,):
                    self.focus = (self.focus - 1) % max(1, len(self.buttons))
                    self._sync_focus()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if self.buttons:
                        self.buttons[self.focus].activate()
                    return True
        for index, button in enumerate(self.buttons):
            if button.handle_events(events):
                self.focus = index
                return True
        return False

    def _sync_focus(self) -> None:
        for index, button in enumerate(self.buttons):
            button.focused = index == self.focus

    # --- drawing ------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 3, 8, 208))
        surface.blit(veil, (0, 0))

        panel = self.rect
        pygame.draw.rect(surface, settings.PANEL, panel, border_radius=14)
        pygame.draw.rect(surface, settings.PANEL_EDGE, panel, 1, border_radius=14)
        pygame.draw.rect(surface, self.tone, panel, 3, border_radius=14)

        y = panel.y + 26
        if self.kicker:
            text.draw(
                surface,
                self.kicker.upper(),
                (panel.centerx, y),
                13,
                self.tone,
                display=True,
                center=True,
            )
            y += 26
        text.draw(
            surface,
            self.title,
            (panel.centerx, y),
            23,
            settings.INK,
            display=True,
            center=True,
            max_width=panel.width - 70,
        )
        y += 34 + (text.measure(self.title, 23, True)[1] if "\n" in self.title else 0)

        if self.body:
            text.draw(
                surface,
                self.body,
                (panel.x + 48, y),
                21,
                settings.DIM,
                max_width=panel.width - 96,
                shadow=False,
                line_gap=4,
            )

        if self.footer:
            text.draw(
                surface,
                self.footer,
                (panel.centerx, panel.bottom - 96),
                17,
                settings.FAINT,
                center=True,
                shadow=False,
            )

        for button in self.buttons:
            button.draw(surface)


class Confirm:
    """Tiny yes/no helper that builds two buttons."""

    @staticmethod
    def build(title: str, body: str, yes_label: str, on_yes, no_label: str = "Not yet", on_no=None, **kwargs) -> Modal:
        def _yes() -> None:
            audio.play("click")
            if on_yes:
                on_yes()

        return Modal(
            title,
            body,
            buttons=[(yes_label, _yes, "primary"), (no_label, on_no, "ghost")],
            **kwargs,
        )
