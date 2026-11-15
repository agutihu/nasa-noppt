"""Reusable vending machine.

Three modes share one widget:

* ``cart``  - pick N items, then dispense (food challenge)
* ``code``  - each item has a number, enter the code (safety harness)
* ``load``  - load equipment into a bay, items stay loaded (landing kit)

The scene owns the rules; the widget only reports what the player did.
"""

from __future__ import annotations

import math

import pygame

from core import audio, settings, text
from ui.button import Button

COLS = 3


class Vending:
    def __init__(
        self,
        game,
        items: list[dict],
        *,
        title: str = "VENDING MACHINE",
        subtitle: str = "",
        footer: str = "DISPENSE",
        max_select: int = 1,
        code_mode: bool = False,
        preselected: list[str] | None = None,
    ) -> None:
        self.game = game
        self.screen = game.screen
        self.items = list(items)
        self.title = title
        self.subtitle = subtitle
        self.footer_label = footer
        self.max_select = max(1, int(max_select))
        self.code_mode = code_mode
        self.selected: list[str] = [item for item in (preselected or []) if self._exists(item)]
        self.locked: set[str] = set()
        self.labels: dict[str, str] = {}
        self.open = False
        self.hovered: str | None = None
        self.focus = 0
        self.t = 0.0
        self.message = ""

        self.rect = pygame.Rect(92, 32, 1096, 656)
        self.grid_rect = pygame.Rect(self.rect.x + 36, self.rect.y + 120, 690, 436)
        self.detail_rect = pygame.Rect(self.grid_rect.right + 28, self.rect.y + 120, 306, 436)
        self.confirm_button = Button(
            (self.detail_rect.x + 12, self.rect.bottom - 68, self.detail_rect.width - 24, 48),
            footer,
            self._confirm,
            size=20,
        )
        self.close_button = Button(
            (self.rect.right - 62, self.rect.y + 22, 42, 34),
            "X",
            self._close,
            style="ghost",
            size=18,
        )

    # --- state --------------------------------------------------------------
    def _exists(self, item_id: str) -> bool:
        return any(item["id"] == item_id for item in self.items)

    def item(self, item_id: str) -> dict | None:
        for entry in self.items:
            if entry["id"] == item_id:
                return entry
        return None

    def set_locked(self, ids) -> None:
        self.locked = set(ids)

    def set_labels(self, labels: dict[str, str]) -> None:
        self.labels = dict(labels)

    def reset(self, *, keep: list[str] | None = None) -> None:
        self.selected = [item for item in (keep or []) if self._exists(item)]
        self.message = ""

    def show(self) -> None:
        self.open = True
        audio.play("beep")

    def hide(self) -> None:
        self.open = False
        audio.play("back")

    @property
    def selected_items(self) -> list[dict]:
        return [entry for entry in self.items if entry["id"] in self.selected]

    # --- actions ------------------------------------------------------------
    def _close(self) -> None:
        if self.open:
            self.open = False
            audio.play("back")

    def _toggle(self, item: dict) -> None:
        if item["id"] in self.locked:
            audio.play("deny")
            return
        if item["id"] in self.selected:
            self.selected.remove(item["id"])
            audio.play("back", 0.7)
            return
        if len(self.selected) >= self.max_select:
            self.selected.pop(0)
        self.selected.append(item["id"])
        audio.play("click", 0.8)

    def _confirm(self) -> None:
        if not self.selected:
            audio.play("deny")
            self.message = "Select at least one item first."
            return
        payload = {
            "action": "footer",
            "items": list(self.selected),
            "numbers": [index + 1 for index, entry in enumerate(self.items) if entry["id"] in self.selected],
        }
        self.on_footer(payload)

    def on_footer(self, payload: dict) -> None:
        """Overridden by the scene (or assigned as a callback)."""

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> dict | None:
        if not self.open:
            return None
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._close()
                    return {"action": "close"}
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.selected:
                        self._confirm()
                    return {"action": "footer"}
                if event.key in (pygame.K_RIGHT, pygame.K_TAB):
                    self.focus = (self.focus + 1) % len(self.items)
                elif event.key == pygame.K_LEFT:
                    self.focus = (self.focus - 1) % len(self.items)
                elif event.key == pygame.K_DOWN:
                    self.focus = (self.focus + COLS) % len(self.items)
                elif event.key == pygame.K_UP:
                    self.focus = (self.focus - COLS) % len(self.items)
                elif event.key == pygame.K_SPACE:
                    self._toggle(self.items[self.focus])
                elif self.code_mode and pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(self.items):
                        self.focus = index
                        self._toggle(self.items[index])
                        return {"action": "select", "item": self.items[index]["id"]}
            elif event.type == pygame.MOUSEMOTION:
                self.hovered = self._item_at(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                item = self._item_at(event.pos)
                if item:
                    self.focus = self.items.index(item)
                    self._toggle(item)
                    return {"action": "select", "item": item["id"]}
        if self.close_button.handle_events(events):
            return {"action": "close"}
        if self.confirm_button.handle_events(events):
            return {"action": "footer"}
        return None

    def _item_at(self, pos: tuple[int, int]) -> dict | None:
        for index, item in enumerate(self.items):
            if self._card_rect(index).collidepoint(pos):
                return item
        return None

    # --- layout -------------------------------------------------------------
    def _card_rect(self, index: int) -> pygame.Rect:
        rows = max(1, math.ceil(len(self.items) / COLS))
        gap = 12
        card_w = (self.grid_rect.width - gap * (COLS - 1)) // COLS
        card_h = min(126, (self.grid_rect.height - gap * (rows - 1)) // max(1, rows))
        col = index % COLS
        row = index // COLS
        return pygame.Rect(
            self.grid_rect.x + col * (card_w + gap),
            self.grid_rect.y + row * (card_h + gap),
            card_w,
            card_h,
        )

    # --- drawing ------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        if not self.open:
            return

        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 3, 8, 216))
        surface.blit(veil, (0, 0))

        rect = self.rect
        pygame.draw.rect(surface, (28, 24, 32), rect, border_radius=18)
        pygame.draw.rect(surface, settings.PANEL_EDGE, rect, 2, border_radius=18)
        pygame.draw.rect(surface, (40, 50, 62), rect.inflate(-18, -18), 1, border_radius=14)

        # machine header
        pygame.draw.rect(surface, (18, 22, 30), (rect.x + 20, rect.y + 16, rect.width - 40, 74), border_radius=10)
        pygame.draw.rect(surface, settings.ACCENT, (rect.x + 20, rect.y + 16, 8, 74), border_radius=3)
        text.draw(surface, self.title, (rect.x + 44, rect.y + 28), 22, settings.ACCENT, display=True)
        if self.subtitle:
            text.draw(surface, self.subtitle, (rect.x + 44, rect.y + 58), 20, settings.DIM, shadow=False)
        pygame.draw.circle(surface, settings.GREEN if self.open else settings.FAINT, (rect.x + 44, rect.y + 76), 4)

        # glass grid
        pygame.draw.rect(surface, (14, 26, 34), self.grid_rect.inflate(16, 16), border_radius=10)
        pygame.draw.rect(surface, (64, 116, 120), self.grid_rect.inflate(16, 16), 1, border_radius=10)

        for index, item in enumerate(self.items):
            self._draw_card(surface, index, item)

        # detail + confirm
        pygame.draw.rect(surface, (18, 18, 26), self.detail_rect, border_radius=10)
        pygame.draw.rect(surface, settings.PANEL_EDGE, self.detail_rect, 1, border_radius=10)
        self._draw_detail(surface)

        selected_count = len(self.selected)
        counter = f"{selected_count}/{self.max_select} selected"
        if self.code_mode:
            counter = "Enter the item code"
        text.draw(
            surface,
            counter,
            (self.confirm_button.rect.centerx, self.confirm_button.rect.y - 24),
            15,
            settings.FAINT,
            center=True,
            shadow=False,
        )
        self.confirm_button.enabled = bool(self.selected)
        self.confirm_button.draw(surface)
        self.close_button.draw(surface)

        if self.message:
            text.draw(
                surface,
                self.message,
                (self.confirm_button.rect.centerx, self.confirm_button.rect.y - 46),
                16,
                settings.WARN,
                center=True,
                shadow=False,
            )

        text.draw(
            surface,
            "Click or arrows + space  |  Enter to confirm  |  Esc to step back",
            (rect.centerx, rect.bottom - 16),
            15,
            settings.FAINT,
            center=True,
            shadow=False,
        )

    def _draw_card(self, surface: pygame.Surface, index: int, item: dict) -> None:
        card = self._card_rect(index)
        chosen = item["id"] in self.selected
        locked = item["id"] in self.locked
        focused = index == self.focus
        hovered = item["id"] == self.hovered

        fill = (40, 48, 60) if chosen else (24, 28, 38)
        if hovered and not chosen:
            fill = (32, 38, 50)
        if locked:
            fill = (20, 22, 28)
        pygame.draw.rect(surface, fill, card, border_radius=9)
        border = settings.ACCENT if chosen else (settings.PANEL_EDGE if not focused else settings.MUTED if hasattr(settings, "MUTED") else settings.DIM)
        pygame.draw.rect(surface, border, card, 2 if chosen or focused else 1, border_radius=9)

        icon = pygame.Rect(card.x + 10, card.y + 12, 52, 52)
        pygame.draw.rect(surface, (16, 18, 24), icon, border_radius=7)
        pygame.draw.rect(surface, item.get("color", settings.DIM), icon, 1, border_radius=7)
        self._draw_icon(surface, icon, item)

        text.draw(
            surface,
            item["name"],
            (card.x + 72, card.y + 14),
            18,
            settings.INK if not locked else settings.FAINT,
            max_width=card.width - 84,
            shadow=False,
        )
        tag = item.get("tag", "")
        if tag:
            text.draw(
                surface,
                tag,
                (card.x + 72, card.y + 42),
                15,
                settings.FAINT,
                max_width=card.width - 84,
                shadow=False,
            )

        label = self.labels.get(item["id"], "")
        if locked:
            label = label or "LOADED"
        if chosen:
            label = "SELECTED"
        if label:
            chip_w = text.measure(label, 12, True)[0] + 14
            chip = pygame.Rect(card.right - chip_w - 8, card.bottom - 24, chip_w, 17)
            pygame.draw.rect(surface, (10, 12, 16), chip, border_radius=8)
            pygame.draw.rect(surface, settings.GREEN if locked else settings.ACCENT, chip, 1, border_radius=8)
            text.draw(
                surface,
                label,
                (chip.centerx, chip.centery - 1),
                12,
                settings.GREEN if locked else settings.ACCENT,
                display=True,
                center=True,
                shadow=False,
            )

        if self.code_mode:
            badge = pygame.Rect(card.x + 8, card.y + 8, 22, 22)
            pygame.draw.rect(surface, settings.ACCENT, badge, border_radius=6)
            text.draw(
                surface,
                str(index + 1),
                (badge.centerx, badge.centery - 1),
                13,
                (10, 20, 22),
                display=True,
                center=True,
                shadow=False,
            )

    def _draw_detail(self, surface: pygame.Surface) -> None:
        detail = self.detail_rect
        item = self.item(self.hovered) if self.hovered else None
        if item is None and self.selected:
            item = self.item(self.selected[-1])
        if item is None and self.items:
            item = self.items[self.focus]

        text.draw(surface, "ITEM FILE", (detail.x + 18, detail.y + 16), 12, settings.ACCENT, display=True)
        if item is None:
            text.draw(surface, "Hover an item.", (detail.x + 18, detail.y + 48), 19, settings.DIM, shadow=False)
            return

        text.draw(
            surface,
            item["name"],
            (detail.x + 18, detail.y + 44),
            22,
            settings.INK,
            max_width=detail.width - 36,
            shadow=False,
        )
        selected = item["id"] in self.selected
        state_label = "SELECTED" if selected else self.labels.get(item["id"], "AVAILABLE")
        text.draw(
            surface,
            state_label,
            (detail.x + 18, detail.y + 76),
            14,
            settings.GREEN if selected else settings.FAINT,
            display=True,
            shadow=False,
        )

        text.draw(
            surface,
            item.get("desc", ""),
            (detail.x + 18, detail.y + 104),
            20,
            settings.DIM,
            max_width=detail.width - 36,
            shadow=False,
            line_gap=5,
        )

        if item.get("note"):
            box = pygame.Rect(detail.x + 16, detail.bottom - 92, detail.width - 32, 66)
            pygame.draw.rect(surface, (12, 16, 22), box, border_radius=8)
            pygame.draw.rect(surface, settings.PANEL_EDGE, box, 1, border_radius=8)
            text.draw(
                surface,
                item["note"],
                (box.x + 10, box.y + 8),
                16,
                settings.GOLD,
                max_width=box.width - 20,
                shadow=False,
            )

    # --- tiny procedural icons ---------------------------------------------
    def _draw_icon(self, surface: pygame.Surface, rect: pygame.Rect, item: dict) -> None:
        kind = item.get("icon", "box")
        color = item.get("color", settings.ACCENT)
        cx, cy = rect.center
        if kind == "drink":
            pygame.draw.rect(surface, color, (cx - 10, cy - 14, 20, 28), border_radius=3)
            pygame.draw.rect(surface, (240, 240, 240), (cx - 10, cy - 4, 20, 6))
            pygame.draw.line(surface, (240, 240, 240), (cx + 4, cy - 18), (cx + 8, cy - 6), 2)
        elif kind == "chicken":
            pygame.draw.circle(surface, color, (cx - 3, cy), 11)
            pygame.draw.line(surface, (240, 230, 210), (cx + 5, cy + 6), (cx + 14, cy + 12), 4)
            pygame.draw.circle(surface, (240, 230, 210), (cx + 15, cy + 13), 3)
        elif kind == "can":
            pygame.draw.rect(surface, color, (cx - 8, cy - 15, 16, 30), border_radius=5)
            pygame.draw.ellipse(surface, (220, 220, 220), (cx - 8, cy - 17, 16, 7))
            pygame.draw.line(surface, (30, 30, 30), (cx - 8, cy), (cx + 8, cy), 1)
        elif kind == "cookie":
            pygame.draw.circle(surface, color, (cx, cy), 13)
            for dx, dy in ((-4, -4), (5, -2), (0, 5), (-6, 4)):
                pygame.draw.circle(surface, (60, 34, 24), (cx + dx, cy + dy), 2)
        elif kind == "harness":
            pygame.draw.arc(surface, color, (cx - 14, cy - 14, 28, 28), 0.3, 2.9, 3)
            pygame.draw.line(surface, color, (cx - 8, cy - 2), (cx - 2, cy + 12), 3)
            pygame.draw.line(surface, color, (cx + 8, cy - 2), (cx + 2, cy + 12), 3)
        elif kind == "duck":
            pygame.draw.ellipse(surface, color, (cx - 14, cy - 2, 24, 16))
            pygame.draw.circle(surface, color, (cx + 7, cy - 8), 8)
            pygame.draw.polygon(surface, (255, 170, 40), [(cx + 14, cy - 9), (cx + 22, cy - 5), (cx + 14, cy - 2)])
            pygame.draw.circle(surface, (20, 20, 20), (cx + 9, cy - 10), 1)
        elif kind == "ball":
            pygame.draw.circle(surface, color, (cx, cy), 13)
            pygame.draw.arc(surface, (255, 255, 255), (cx - 13, cy - 13, 26, 26), 0.4, 2.6, 2)
        elif kind == "rocket":
            pygame.draw.polygon(surface, color, [(cx, cy - 16), (cx + 9, cy + 6), (cx, cy + 2), (cx - 9, cy + 6)])
            pygame.draw.polygon(surface, (255, 180, 90), [(cx - 5, cy + 6), (cx + 5, cy + 6), (cx, cy + 18)])
        elif kind == "parachute":
            pygame.draw.arc(surface, color, (cx - 15, cy - 16, 30, 26), 0.1, 3.0, 4)
            pygame.draw.line(surface, (230, 230, 230), (cx - 12, cy - 4), (cx, cy + 12), 1)
            pygame.draw.line(surface, (230, 230, 230), (cx + 12, cy - 4), (cx, cy + 12), 1)
            pygame.draw.circle(surface, (230, 230, 230), (cx, cy + 13), 3)
        elif kind == "shield":
            pygame.draw.polygon(surface, color, [(cx, cy - 15), (cx + 13, cy - 8), (cx + 9, cy + 10), (cx, cy + 16), (cx - 9, cy + 10), (cx - 13, cy - 8)])
            pygame.draw.polygon(surface, (30, 30, 30), [(cx, cy - 8), (cx + 7, cy - 4), (cx + 5, cy + 6), (cx, cy + 10), (cx - 5, cy + 6), (cx - 7, cy - 4)], 1)
        elif kind == "crane":
            pygame.draw.polygon(surface, color, [(cx - 14, cy + 12), (cx + 2, cy - 14), (cx + 14, cy + 12)])
            pygame.draw.line(surface, (240, 240, 240), (cx - 8, cy + 4), (cx + 8, cy + 4), 2)
            pygame.draw.line(surface, (240, 240, 240), (cx, cy - 10), (cx, cy + 14), 2)
        elif kind == "pizza":
            pygame.draw.polygon(surface, color, [(cx - 14, cy - 8), (cx + 14, cy - 8), (cx, cy + 16)])
            for dx, dy in ((-6, -2), (3, 0), (0, 7)):
                pygame.draw.circle(surface, (180, 40, 40), (cx + dx, cy + dy), 2)
        elif kind == "balloon":
            pygame.draw.ellipse(surface, color, (cx - 9, cy - 16, 18, 22))
            pygame.draw.line(surface, (220, 220, 220), (cx, cy + 6), (cx + 3, cy + 16), 1)
        elif kind == "disco":
            pygame.draw.circle(surface, color, (cx, cy), 13)
            pygame.draw.line(surface, (30, 30, 30), (cx - 13, cy), (cx + 13, cy), 1)
            pygame.draw.line(surface, (30, 30, 30), (cx, cy - 13), (cx, cy + 13), 1)
            pygame.draw.circle(surface, (255, 255, 255), (cx - 5, cy - 5), 2)
        elif kind == "vent":
            pygame.draw.rect(surface, color, (cx - 14, cy - 9, 28, 18), border_radius=3)
            for i in range(3):
                pygame.draw.line(surface, (20, 20, 20), (cx - 10, cy - 4 + i * 5), (cx + 10, cy - 4 + i * 5), 1)
        elif kind == "wrench":
            pygame.draw.line(surface, color, (cx - 9, cy + 9), (cx + 9, cy - 9), 4)
            pygame.draw.circle(surface, color, (cx - 11, cy + 11), 5, 2)
            pygame.draw.circle(surface, color, (cx + 11, cy - 11), 5, 2)
        elif kind == "tape":
            pygame.draw.circle(surface, color, (cx, cy), 13, 5)
            pygame.draw.circle(surface, (30, 30, 30), (cx, cy), 5)
        else:
            pygame.draw.rect(surface, color, (cx - 12, cy - 12, 24, 24), border_radius=4)
