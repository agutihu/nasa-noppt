"""Laika's dialogue box: portrait, typewriter text, per-line speakers, hints."""

from __future__ import annotations

import pygame

from art import sprites
from core import audio, settings, text

ADVANCE_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e)

SPEAKER_COLORS = {
    "Laika": settings.ACCENT,
    "Mission Control": settings.WARN,
    "System": settings.DIM,
    "Astronaut": settings.GOLD,
}


def _is_laika(speaker: str) -> bool:
    return speaker.strip().lower().startswith("laika")


class DialogueBox:
    def __init__(self, game, rect: tuple[int, int, int, int] | None = None) -> None:
        self.game = game
        self.screen = game.screen
        self.rect = pygame.Rect(rect or (104, settings.HEIGHT - 198, settings.WIDTH - 208, 170))
        self.lines: list[dict] = []
        self.index = 0
        self.speaker = "Laika"
        self.default_speaker = "Laika"
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
        lines,
        speaker: str | None = None,
        on_done=None,
        *,
        accent: tuple[int, int, int] | None = None,
        hint: bool = False,
    ) -> None:
        normalised: list[dict] = []
        for line in lines or []:
            if isinstance(line, dict):
                body = str(line.get("text", "")).strip()
                voice = str(line.get("speaker", speaker or self.default_speaker))
            else:
                body = str(line).strip()
                voice = speaker or self.default_speaker
            if body:
                normalised.append({"text": body, "speaker": voice})
        if not normalised:
            if on_done:
                on_done()
            return

        self.lines = normalised
        self.index = 0
        self.revealed = 0.0
        self.active = True
        self.is_hint = hint
        self.speaker = normalised[0]["speaker"]
        self.default_speaker = speaker or self.speaker
        self.on_done = on_done
        self.accent = accent or (settings.GOLD if hint else SPEAKER_COLORS.get(self.speaker, settings.ACCENT))

    def show(self, line: str, speaker: str | None = None, on_done=None, **kwargs) -> None:
        self.queue([line], speaker, on_done, **kwargs)

    def hint(self, line: str) -> None:
        self.queue([line], self.default_speaker, accent=settings.GOLD, hint=True)

    def clear(self) -> None:
        self.lines = []
        self.index = 0
        self.revealed = 0.0
        self.active = False
        self.on_done = None

    @property
    def current_line(self) -> dict:
        if 0 <= self.index < len(self.lines):
            return self.lines[self.index]
        return {"text": "", "speaker": self.speaker}

    @property
    def current_text(self) -> str:
        return self.current_line["text"]

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
            if event.type == pygame.KEYDOWN and event.key in ADVANCE_KEYS + (pygame.K_ESCAPE,):
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
            self.speaker = self.current_line["speaker"]
            self.accent = SPEAKER_COLORS.get(self.speaker, settings.ACCENT)
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
            self._blip_budget += self.revealed - before
            if self._blip_budget >= 5:
                self._blip_budget = 0.0
                audio.play("dialogue", 0.45)

    # --- drawing ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return

        rect = self.rect
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((10, 8, 14, 238))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 1, border_radius=10)
        pygame.draw.rect(surface, self.accent, rect, 2, border_radius=10)

        portrait_center = (rect.x + 58, rect.y + rect.height // 2)
        speaker = self.current_line["speaker"]
        if _is_laika(speaker):
            sprites.draw_laika_portrait(
                surface, portrait_center, 88, self.t,
                dim=False,
            )
        else:
            self._draw_badge(surface, portrait_center, speaker)

        name = speaker.upper()
        text.draw(surface, name, (rect.x + 118, rect.y + 18), 16, self.accent, display=True)
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
            text.draw(
                surface,
                "HINT",
                (rect.x + 122 + text.measure(name, 16, True)[0], rect.y + 18),
                17,
                settings.GOLD,
                shadow=False,
            )

        visible = self.current_text[: int(self.revealed)]
        text.draw(
            surface,
            visible,
            (rect.x + 118, rect.y + 48),
            23,
            settings.INK,
            max_width=rect.width - 150,
            shadow=False,
            line_gap=3,
        )

        if self.fully_revealed and (pygame.time.get_ticks() // 420) % 2 == 0:
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

    def _draw_badge(self, surface: pygame.Surface, center: tuple[int, int], speaker: str) -> None:
        color = SPEAKER_COLORS.get(speaker, settings.DIM)
        pygame.draw.circle(surface, (18, 16, 22), center, 42)
        pygame.draw.circle(surface, color, center, 42, 2)
        cx, cy = center
        if "control" in speaker.lower():
            pygame.draw.arc(surface, color, (cx - 18, cy - 16, 36, 30), 0.2, 3.0, 3)
            pygame.draw.circle(surface, color, (cx - 15, cy + 2), 4)
            pygame.draw.circle(surface, color, (cx + 15, cy + 2), 4)
            pygame.draw.line(surface, color, (cx, cy + 2), (cx, cy + 14), 3)
        else:
            pygame.draw.rect(surface, color, (cx - 12, cy - 12, 24, 24), 2, border_radius=4)
            pygame.draw.line(surface, color, (cx - 6, cy), (cx + 6, cy), 2)
            pygame.draw.line(surface, color, (cx, cy - 6), (cx, cy + 6), 2)
