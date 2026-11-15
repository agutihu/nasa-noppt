"""Level 2: Preparing for the Mission.

Equipment selection + delayed communication test.
"""

from __future__ import annotations

import math
import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from core.game_state import GameState
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.vending import Vending


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_rect(index: int, grid_rect: pygame.Rect) -> pygame.Rect:
    cols = 3
    gap = 12
    card_w = (grid_rect.width - gap * (cols - 1)) // cols
    card_h = min(126, (grid_rect.height - gap * (rows - 1)) // max(1, rows))
    col = index % cols
    row = index // cols
    return pygame.Rect(
        grid_rect.x + col * (card_w + gap),
        grid_rect.y + row * (card_h + gap),
        card_w,
        card_h,
    )


def _draw_astronaut_at(surface: pygame.Surface, pos: tuple[int, int], t: float) -> None:
    cx, cy = pos
    s = 1.0
    f = 1
    bob = math.sin(t * 6.0) * 1.5 * s
    # simple astronaut drawing
    pygame.draw.rect(surface, (232, 238, 248), pygame.Rect(cx - 9 * s, cy - 7 * s + bob, 18 * s, 17 * s), border_radius=max(2, int(5 * s)))
    pygame.draw.rect(surface, (94, 210, 208), pygame.Rect(cx - 6 * s, cy - 4 * s, 12 * s, 8 * s), border_radius=max(1, int(1 * s)))
    pygame.draw.circle(surface, (94, 210, 208), (cx, cy - 2 * s + bob), max(1, int(2 * s)))


# ---------------------------------------------------------------------------
# Level 2 Scene
# ---------------------------------------------------------------------------

class Level2Scene(Scene):
    name = settings.LEVEL2
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("level2")
        self.params = levels.params_for(self.cfg, self.state.difficulty)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.hud = HUD(self.state, level_name=self.cfg["name"], accent=settings.ACCENT)
        self.dlg = DialogueBox(self.game)
        self.modal: Modal | None = None
        self.vending: Vending | None = None
        self.t = 0.0
        self.phase = "intro"
        self.phase_start = 0.0
        self.level_time = 0.0

        # briefing background
        self.backdrop = environments.outpost_room(settings.WIDTH, settings.HEIGHT)

        # player
        self.player_pos = pygame.Vector2(self.params["player_start"])
        self.vending_rect = pygame.Rect(96, 196, 112, 168)

        # three rest bays (not used in landing, but keep for consistency)
        self.rest_bays = []

        # objective
        self.objective = ""

        self.phase_start = self.state.elapsed
        self._goto_phase("intro")

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def _goto_phase(self, phase: str, **data) -> None:
        self.phase = phase
        self.phase_start = self.state.elapsed
        self.objective = ""
        self.modal = None
        self.vending = None

        if phase == "landing_correct":
            self._say("landing_correct")
            self._schedule_next("comm_test", 3.0)
            return
        if phase == "landing_wrong":
            self._say("landing_wrong")
            self._schedule_next("intro", 2.0)
            return
        if phase == "complete":
            self._schedule_next("briefing", 3.0)
            return

        phase_cfg = next((p for p in self.cfg["phases"] if p["id"] == phase), None)
        if phase_cfg:
            self.objective = phase_cfg.get("objective", "")
            trig = phase_cfg.get("dialogue_trigger")
            if trig:
                self._say(trig)

    def _schedule_next(self, phase: str, delay: float) -> None:
        self._next_phase = phase
        self._next_phase_time = self.state.elapsed + delay

    # ------------------------------------------------------------------
    # Dialogue
    # ------------------------------------------------------------------

    def _say(self, trigger: str, speaker: str | None = None) -> None:
        lines = self.dialogue["lines"].get(trigger, [])
        if not lines:
            if self.dlg.is_active():
                self.dlg.advance()
            return
        self.dlg.queue(lines, speaker=speaker, on_done=self._on_dialogue_done)

    def _on_dialogue_done(self) -> None:
        if self.dlg.index + 1 < len(self.dlg.lines):
            self.dlg.index += 1
            self.dlg.revealed = 0.0
        else:
            self.dlg.clear()

    # ------------------------------------------------------------------
    # Phase logic
    # ------------------------------------------------------------------

    def _handle_intro(self, dt: float) -> None:
        self.t += dt
        if self.player_pos.distance_to(pygame.Vector2(640, 380)) > 30:
            direction = (pygame.Vector2(640, 380) - self.player_pos).normalize() * 120 * dt
            self.player_pos += direction
        if self.player_pos.distance_to(pygame.Vector2(640, 380)) < 50 and not self.dlg.is_active():
            self._say("intro")

    # -- landing_briefing --
    def _handle_landing_briefing(self, dt: float) -> None:
        self.t += dt
        if self.modal:
            # modal handles its own events; just draw it
            if self.modal.buttons and self.modal.focus >= 0:
                pass
            self.modal.draw(self.screen)
            return
        if self.dlg.is_active():
            self.dlg.update(dt)
            return
        if not self.vending:
            items = self.cfg["phases"][1]["vending"]["items"]
            self.vending = Vending(
                self.game,
                items,
                title="LANDING EQUIPMENT",
                subtitle="Select THREE items needed for safe landing. Parachute, heat shield, sky crane.",
                footer="SELECT",
                max_select=3,
                code_mode=False,
            )
            self.vending.set_labels({it["id"]: str(index + 1) for index, it in enumerate(items)})

        ev = self.vending.handle_events(pygame.event.get())
        if ev == {"action": "select", "item": str}:
            self.hud.toast(f"Selected: {self.vending.items[self.vending.focus]['name']}")
        elif ev == {"action": "footer"}:
            self._handle_vendor_confirm_landing(self.vending._confirm_payload if hasattr(self.vending, '_confirm_payload') else {})
            self.vending = None
            self._goto_phase("landing_correct")
        elif ev == {"action": "close"}:
            self.vending = None

        if self.vending:
            self.vending.draw(self.screen)

    def _handle_vendor_confirm_landing(self, payload: dict) -> None:
        selected = payload.get("items", [])
        if len(selected) != 3:
            self.hud.toast("Select exactly three items.")
            audio.play("deny")
            return
        essential = {"parachute", "heat_shield", "sky_crane"}
        chosen = set(selected)
        if chosen == essential:
            audio.play("confirm")
            self._goto_phase("landing_correct")
        else:
            audio.play("deny")
            # show which were wrong
            wrong = chosen - essential
            self.hud.toast(f"Essential items missing: {', '.join(wrong)}")
            self._goto_phase("landing_wrong")

    # -- comm_test --
    def _handle_comm_test(self, dt: float) -> None:
        self.t += dt
        # display timer and instruction
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start))
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.hud.toast(f"Communications delay: {minutes:01d}:{seconds:02d}. Do NOT press the button.")
        # if player presses space, penalize
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not self.dlg.is_active():
            self.hud.toast("Mission control warns: Do not send another message!")
            audio.play("deny")
        if remaining <= 0:
            self._say("comm_success")
            self._schedule_next("complete", 3.0)

    # -- complete --
    def _handle_complete(self, dt: float) -> None:
        self.t += dt
        if self.state.elapsed - self.phase_start >= 5.0:
            self.state.mark_level_done("landing", self.level_time)
            self.manager.switch(settings.BRIEFING, level_id="landing")

    # ------------------------------------------------------------------
    # General loop
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.game.quit()
            if self.dlg.is_active():
                self.dlg.handle_events(events)
                return
            if self.modal and self.modal.is_active():
                self.modal.handle_events(events)
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.modal:
                    self.modal = None
                elif self.dlg.is_active():
                    self.dlg.clear()
                else:
                    self.manager.push(settings.PAUSE, parent=self)
                return

    def update(self, dt: float) -> None:
        self.t += dt
        self.level_time = self.state.elapsed - self.phase_start

        if self.phase == "intro":
            self._handle_intro(dt)
        elif self.phase == "landing_briefing":
            self._handle_landing_briefing(dt)
        elif self.phase == "comm_test":
            self._handle_comm_test(dt)
        elif self.phase == "complete":
            self._handle_complete(dt)

        self.hud.update(dt)
        if self.dlg.is_active():
            self.dlg.update(dt)
        if self.modal:
            self.modal.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.backdrop, (0, 0))

        _draw_astronaut_at(surface, (640, 380), self.t)

        self.hud.draw(surface)

        if self.dlg.is_active():
            self.dlg.draw(surface)

        if self.modal:
            self.modal.draw(surface)

        # draw vending if active
        if self.vending:
            self.vending.draw(self.screen)

        # draw objective banner
        if self.objective:
            text.draw(surface, f"OBJECTIVE: {self.objective}",
                     (settings.WIDTH // 2, 60), 20, settings.INK, display=True, center=True)


# ---------------------------------------------------------------------------
# Scene registration
# ---------------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    from scenes.level1 import Level1Scene
    from scenes.level2 import Level2Scene
    from scenes.briefing import BriefingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.LEVEL2, Level2Scene)
    manager.register(settings.BRIEFING, BriefingScene)