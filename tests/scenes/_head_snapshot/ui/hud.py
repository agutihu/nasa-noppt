"""Mission HUD: level identity, objective, timer, counters, gauges, banners.

Every level uses the same strip so the four missions feel like one interface.
"""

from __future__ import annotations

import pygame

from core import settings, text
from ui.meter import Meter


class HUD:
    def __init__(self, state, cfg: dict | None = None, level_name: str = "", accent: tuple[int, int, int] | None = None) -> None:
        self.state = state
        self.cfg = cfg or {}
        self.level_name = level_name
        self.t = 0.0
        self.banner_time = 0.0
        self.banner_text = ""
        self.banner_tone = settings.ACCENT
        self.toast_time = 0.0
        self.toast_text = ""
        self.objective = ""
        self.timer: float | None = None
        self.counters: list[dict] = []
        self.meters: list[Meter] = []
        self.accent = accent or settings.ACCENT
        self.challenge = ""
        self.hint_prompt = False
        self.checklist: list[dict] = []
        self.target: tuple[str, tuple[int, int, int]] = ("Mission", settings.ACCENT)
        self.hearts_current = 1
        self.hearts_max = 1

    def set_hearts(self, current: int | None, maximum: int | None) -> None:
        self.hearts_current = current
        self.hearts_max = maximum

    def set_checklist(self, items: list[dict]) -> None:
        self.checklist = list(items)

    def set_target(self, name: str, color: tuple[int, int, int]) -> None:
        """Set the labeled part target in the top bar."""
        self.target = (name, color)
        self.objective = ""
        self.timer: float | None = None
        self.counters: list[dict] = []
        self.meters: list[Meter] = []
        self._meter_index: dict[str, Meter] = {}
        self.banner_text = ""
        self.banner_time = 0.0
        self.banner_tone = settings.ACCENT
        self.toast_text = ""
        self.toast_time = 0.0
        self.hint_prompt = False
        self.t = 0.0

    # --- data ---------------------------------------------------------------
    def set_level(self, name: str, challenge: str = "") -> None:
        self.level_name = name
        self.challenge = challenge

    def set_objective(self, value: str) -> None:
        self.objective = value

    def set_timer(self, seconds: float | None) -> None:
        self.timer = None if seconds is None else max(0.0, float(seconds))

    def set_counters(self, counters: list[dict]) -> None:
        """``[{"label": "PHOTOS", "value": "2/6", "color": ...}]``"""
        self.counters = list(counters)

    def update_counter(self, label: str, value: str, color: tuple[int, int, int] | None = None) -> None:
        for counter in self.counters:
            if counter["label"] == label:
                counter["value"] = value
                if color:
                    counter["color"] = color
                return

    def add_meter(self, label: str, value: float, maximum: float, color, **kwargs) -> Meter:
        index = len(self.meters)
        rect = (settings.WIDTH - 286, 70 + index * 46, 258, 40)
        meter = Meter(rect, label, color, maximum, show_value=True, **kwargs)
        meter.set(value)
        self.meters.append(meter)
        self._meter_index[label] = meter
        return meter

    def meter(self, label: str) -> Meter | None:
        return self._meter_index.get(label)

    def set_meter(self, label: str, value: float) -> None:
        meter = self._meter_index.get(label)
        if meter is not None:
            meter.set(value)

    def banner(self, message: str, seconds: float = 3.0, tone=None) -> None:
        self.banner_text = message
        self.banner_time = max(0.5, seconds)
        self.banner_tone = tone or settings.ACCENT

    def toast(self, message: str, seconds: float = 2.4) -> None:
        self.toast_text = message
        self.toast_time = max(0.5, seconds)

    def update(self, dt: float) -> None:
        self.t += dt
        self.banner_time = max(0.0, self.banner_time - dt)
        self.toast_time = max(0.0, self.toast_time - dt)
        for meter in self.meters:
            meter.update(dt)

    # --- drawing ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_top_bar(surface)
        self._draw_counters(surface)
        self._draw_meters(surface)
        self._draw_banner(surface)
        self._draw_toast(surface)
        if self.hint_prompt:
            self._draw_hint_prompt(surface)

    def _draw_top_bar(self, surface: pygame.Surface) -> None:
        bar = pygame.Surface((settings.WIDTH, 60), pygame.SRCALPHA)
        bar.fill((8, 6, 10, 214))
        surface.blit(bar, (0, 0))
        pygame.draw.line(surface, settings.PANEL_EDGE, (0, 60), (settings.WIDTH, 60), 1)
        pygame.draw.line(surface, self.accent, (0, 59), (170, 59), 2)

        text.draw(
            surface,
            self.level_name.upper(),
            (22, 13),
            14,
            self.accent,
            display=True,
        )
        if self.challenge:
            chip_w = text.measure(self.challenge.upper(), 12, True)[0] + 20
            chip = pygame.Rect(22, 34, chip_w, 18)
            pygame.draw.rect(surface, (8, 14, 18), chip, border_radius=9)
            pygame.draw.rect(surface, self.accent, chip, 1, border_radius=9)
            text.draw(
                surface,
                self.challenge.upper(),
                (chip.centerx, chip.centery - 1),
                12,
                self.accent,
                display=True,
                center=True,
                middle=True,
            )

        if self.objective:
            text.draw(
                surface,
                self.objective,
                (settings.WIDTH // 2, 22),
                21,
                settings.INK,
                center=True,
                max_width=560,
                shadow=False,
            )

        if self.timer is not None:
            remaining = max(0.0, self.timer)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            danger = remaining <= 20.0
            color = settings.DANGER if danger else settings.INK
            alpha = 255
            if danger:
                alpha = 165 + int(90 * abs(pygame.math.Vector2(1, 0).rotate(self.t * 320).x))
            text.draw(
                surface,
                f"{minutes:01d}:{seconds:02d}",
                (settings.WIDTH - 24, 10),
                24,
                color,
                display=True,
                right=True,
                alpha=alpha,
            )
            text.draw(
                surface,
                "TIME LEFT",
                (settings.WIDTH - 24, 38),
                12,
                settings.FAINT,
                right=True,
                shadow=False,
            )

    def _draw_counters(self, surface: pygame.Surface) -> None:
        if not self.counters:
            return
        x = 24
        for counter in self.counters:
            label = str(counter.get("label", ""))
            value = str(counter.get("value", ""))
            color = counter.get("color", self.accent)
            label_w = text.measure(label, 13, True)[0]
            value_w = text.measure(value, 20)[0]
            width = label_w + value_w + 34
            rect = pygame.Rect(x, 72, width, 30)
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((8, 6, 10, 190))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 1, border_radius=15)
            pygame.draw.circle(surface, color, (rect.x + 13, rect.centery), 4)
            text.draw(surface, label, (rect.x + 24, rect.centery - 6), 13, settings.DIM, display=True, shadow=False)
            text.draw(surface, value, (rect.right - 12, rect.centery - 10), 20, color, right=True, shadow=False)
            x += width + 8

    def _draw_meters(self, surface: pygame.Surface) -> None:
        if not self.meters:
            return
        top = self.meters[0].rect.y - 10
        bottom = self.meters[-1].rect.y + self.meters[-1].rect.height + 6
        panel = pygame.Surface((276, bottom - top + 4), pygame.SRCALPHA)
        panel.fill((8, 6, 10, 170))
        surface.blit(panel, (settings.WIDTH - 294, top))
        pygame.draw.rect(surface, settings.PANEL_EDGE, (settings.WIDTH - 294, top, 276, bottom - top + 4), 1, border_radius=8)
        for meter in self.meters:
            meter.draw(surface)

    def _draw_banner(self, surface: pygame.Surface) -> None:
        if self.banner_time <= 0.0 or not self.banner_text:
            return
        fade = min(1.0, self.banner_time / 0.4)
        alpha = int(255 * fade)
        band = pygame.Surface((settings.WIDTH, 52), pygame.SRCALPHA)
        band.fill((8, 6, 10, int(210 * fade)))
        surface.blit(band, (0, 128))
        pygame.draw.line(surface, self.banner_tone, (0, 128), (settings.WIDTH, 128), 1)
        pygame.draw.line(surface, self.banner_tone, (0, 180), (settings.WIDTH, 180), 1)
        text.draw(
            surface,
            self.banner_text,
            (settings.WIDTH // 2, 142),
            22,
            self.banner_tone,
            display=True,
            center=True,
            alpha=alpha,
        )

    def _draw_toast(self, surface: pygame.Surface) -> None:
        if self.toast_time <= 0.0 or not self.toast_text:
            return
        fade = min(1.0, self.toast_time / 0.35)
        width = min(760, text.measure(self.toast_text, 21)[0] + 48)
        rect = pygame.Rect(0, 0, width, 42)
        rect.midbottom = (settings.WIDTH // 2, settings.HEIGHT - 214)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((10, 8, 14, int(228 * fade)))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, self.accent, rect, 1, border_radius=10)
        text.draw(
            surface,
            self.toast_text,
            (rect.centerx, rect.centery - 9),
            21,
            settings.INK,
            center=True,
            shadow=False,
            alpha=int(255 * fade),
        )

    def _draw_hint_prompt(self, surface: pygame.Surface) -> None:
        label = "H  Laika hint"
        width = text.measure(label, 18)[0] + 24
        rect = pygame.Rect(settings.WIDTH - width - 22, settings.HEIGHT - 46, width, 26)
        pygame.draw.rect(surface, (10, 8, 14), rect, border_radius=13)
        pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 1, border_radius=13)
        text.draw(
            surface,
            label,
            (rect.centerx, rect.centery - 2),
            18,
            settings.ACCENT,
            center=True,
            shadow=False,
        )
