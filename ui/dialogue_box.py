"""Laika's dialogue box: typewriter text, queued lines, hint mode."""

from __future__ import annotations

import pygame

from art import sprites
from core import audio, settings, text

ADVANCE_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e)


class DialogueBox:
    def __init__(self, game, rect: tuple[int, int, int, int] | None = None) -> None:
        self.game = game
        self.screen = game.screen
        self.rect = pygame.Rect(rect or (104, settings.HEIGHT - 198, settings.WIDTH - 208, 170))
        self.lines: list[str] = []
        self.index = 0
        self.speaker = "Laika"
        self.revealed = 0.0
        self.chars_per_second = 62.0
        self.active = False
        self.on_done = None
        self.accent = settings.ACCENT
        self.t = 0.0
        self.is_hint = False
        self._blip_budget = 0.0

    # --- content ------------------------------------------------------------
    def queue(
        self,
        lines: list[str],
        speaker: str | None = None,
        on_done=None,
        *,
        accent: tuple[int, int, int] | None = None,
        hint: bool = False,
    ) -> None:
        cleaned = [str(line).strip() for line in lines if str(line).strip()]
        if not cleaned:
            return
        self.lines = cleaned
        self.index = 0
        self.revealed = 0.0
        self.active = True
        self.is_hint = hint
        self.speaker = speaker or "Laika"
        self.on_done = on_done
        self.accent = accent or (settings.GOLD if hint else settings.ACCENT)

    def show(self, line: str, speaker: str | None = None, on_done=None, **kwargs) -> None:
        self.queue([line], speaker, on_done, **kwargs)

    def hint(self, line: str) -> None:
        self.queue([line], accent=settings.GOLD, hint=True)

    def clear(self) -> None:
        self.lines = []
        self.index = 0
        self.revealed = 0.0
        self.active = False
        self.on_done = None

    @property
    def current_text(self) -> str:
        return self.lines[self.index] if 0 <= self.index < len(self.lines) else ""

    @property
    def fully_revealed(self) -> bool:
        return self.revealed >= len(self.current_text)

    def is_active(self) -> bool:
        return self.active

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> bool:
        if not self.active:
            return False
        for event in events:
            advance = False
            if event.type == pygame.KEYDOWN and event.key in ADVANCE_KEYS:
                advance = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                advance = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                advance = True
            if advance:
                self.advance()
                break
        return True

    def advance(self) -> None:
        if not self.active:
            return
        if not self.fully_revealed:
            self.revealed = len(self.current_text)
            return
        if self.index + 1 < len(self.lines):
            self.index += 1
            self.revealed = 0.0
            return
        self._finish()

    def _finish(self) -> None:
        callback = self.on_done
        self.clear()
        if callback:
            callback()

    # --- update -------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        if not self.active:
            return
        before = int(self.revealed)
        self.revealed = min(len(self.current_text), self.revealed + self.chars_per_second * dt)
        if int(self.revealed) > before and not self.is_hint:
            self._blip_budget += (self.revealed - before)
            if self._blip_budget >= 5:
                self._blip_budget = 0.0
                audio.play("dialogue", 0.45)

    # --- drawing ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return

        rect = self.rect
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((6, 11, 24, 238))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 1, border_radius=10)
        pygame.draw.rect(surface, self.accent, rect, 2, border_radius=10)

        # portrait
        portrait_center = (rect.x + 62, rect.y + 58)
        pygame.draw.circle(surface, (8, 18, 30), portrait_center, 40)
        pygame.draw.circle(surface, self.accent, portrait_center, 40, 1)
        sprites.draw_laika(
            surface,
            portrait_center,
            self.t,
            scale=0.62,
            talking=not self.fully_revealed,
        )

        # speaker + page counter
        name = self.speaker.upper()
        text.draw(surface, name, (rect.x + 118, rect.y + 18), 18, self.accent, display=True)
        if len(self.lines) > 1:
            text.draw(
                surface,
                f"{self.index + 1}/{len(self.lines)}",
                (rect.right - 22, rect.y + 18),
                18,
                settings.DIM,
                right=True,
                shadow=False,
            )
        if self.is_hint:
            text.draw(surface, "HINT", (rect.x + 118 + text.measure(name, 18, True)[0] + 14, rect.y + 18), 18, settings.GOLD)

        visible = self.current_text[: int(self.revealed)]
        text.draw(
            surface,
            visible,
            (rect.x + 118, rect.y + 48),
            24,
            settings.INK,
            max_width=rect.width - 150,
            shadow=False,
            line_gap=4,
        )

        if self.fully_revealed:
            blink = (pygame.time.get_ticks() // 420) % 2 == 0
            if blink:
                arrow_x = rect.right - 30
                arrow_y = rect.bottom - 26
                pygame.draw.polygon(
                    surface,
                    self.accent,
                    [(arrow_x - 7, arrow_y - 5), (arrow_x + 7, arrow_y - 5), (arrow_x, arrow_y + 5)],
                )
                text.draw(
                    surface,
                    "space",
                    (arrow_x - 16, arrow_y - 4),
                    16,
                    settings.FAINT,
                    right=True,
                    shadow=False,
                )
