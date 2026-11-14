"""Buttons that work with both mouse and keyboard focus."""

from __future__ import annotations

import pygame

from core import audio, settings, text


class Button:
    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        on_click=None,
        *,
        size: int = 22,
        display: bool = False,
        style: str = "primary",
        enabled: bool = True,
        subtitle: str | None = None,
        align: str = "center",
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.size = size
        self.display = display
        self.style = style
        self.enabled = enabled
        self.subtitle = subtitle
        self.align = align
        self.hovered = False
        self.focused = False
        self.was_hovered = False

    # --- interaction --------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> bool:
        clicked = False
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                inside = self.rect.collidepoint(event.pos)
                if inside and not self.was_hovered and self.enabled:
                    audio.play("hover", 0.6)
                self.was_hovered = inside
                self.hovered = inside
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.enabled and self.rect.collidepoint(event.pos):
                    clicked = True
        if clicked:
            self.activate()
        return clicked

    def activate(self) -> None:
        if not self.enabled:
            return
        audio.play("click")
        if self.on_click:
            self.on_click()

    # --- drawing ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        active = self.enabled and (self.hovered or self.focused)
        rect = self.rect.copy()
        if active:
            rect.y -= 2

        if self.style == "primary":
            fill = settings.ACCENT if self.enabled else (54, 66, 84)
            fill = tuple(min(255, channel + 24) for channel in fill) if active else fill
            text_color = (8, 20, 26)
            border = settings.ACCENT
        elif self.style == "danger":
            fill = (66, 22, 34) if self.enabled else (40, 34, 40)
            fill = (96, 30, 46) if active else fill
            text_color = settings.DANGER if self.enabled else settings.FAINT
            border = settings.DANGER
        else:  # ghost
            fill = settings.PANEL_LIGHT if active else settings.PANEL
            text_color = settings.INK if self.enabled else settings.FAINT
            border = settings.ACCENT if active else settings.PANEL_EDGE

        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, 2 if active else 1, border_radius=8)
        if active:
            pygame.draw.rect(
                surface, border, rect.inflate(8, 8), 1, border_radius=12
            )

        if self.align == "left":
            label_pos = (rect.x + 20, rect.centery)
            anchor_right = False
        else:
            label_pos = (rect.centerx, rect.centery)
            anchor_right = False

        label_y = rect.centery
        if self.subtitle:
            label_y = rect.centery - 10
        text.draw(
            surface,
            self.label,
            (label_pos[0], label_y),
            self.size,
            text_color,
            display=self.display,
            center=not anchor_right,
            middle=True,
        )
        if self.subtitle:
            text.draw(
                surface,
                self.subtitle,
                (rect.centerx, rect.centery + 14),
                16,
                settings.DIM if self.enabled else settings.FAINT,
                center=True,
                middle=True,
                shadow=False,
            )
