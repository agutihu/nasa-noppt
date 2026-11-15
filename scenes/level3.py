"""Level 3: Martian Surface.

Rover exploration: take photographs, survive sandstorm, activate hibernation.
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
    pygame.draw.rect(surface, (232, 238, 248), pygame.Rect(cx - 9 * s, cy - 7 * s + bob, 18 * s, 17 * s), border_radius=max(2, int(5 * s)))
    pygame.draw.circle(surface, (94, 210, 208), (cx, cy - 2 * s + bob), max(1, int(2 * s)))


# ---------------------------------------------------------------------------
# Level 3 Scene
# ---------------------------------------------------------------------------

class Level3Scene(Scene):
    name = settings.LEVEL3
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("level3")
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
        self.sandstorm_active = False
        self.hibernation_active = False
        self.photos_taken = 0
        self.total_photos = 6
        self.cold_timer = 0.0

        # backdrop
        self.backdrop = environments.mars_surface(settings.WIDTH, settings.HEIGHT, seed=11)

        # player
        self.player_pos = pygame.Vector2(self.params["player_start"])
        self.vending_rect = pygame.Rect(96, 196, 112, 168)

        # photo button rects (simulated)
        self.photo_button_rects = []

        # rest bays
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
        self.sandstorm_active = False
        self.hibernation_active = False
        self.photos_taken = 0

        if phase == "photo_intro":
            self._say("photo_intro")
            self._schedule_next("take_photos", 3.0)
            return
        if phase == "sandstorm":
            self.sandstorm_active = True
            self._say("sandstorm")
            self._schedule_next("cold_alert", 45.0)
            return
        if phase == "hibernation":
            self.hibernation_active = True
            self._say("hibernation")
            self._schedule_next("complete", 5.0)
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

    # -- take_photos --
    def _handle_take_photos(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        # press E near a photo button to take picture
        if keys[pygame.K_e] and not self.dlg.is_active():
            # check if near any button
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            for i, rect in enumerate(self.photo_button_rects):
                if rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])):
                    self.photos_taken += 1
                    self.hud.toast(f"Photo {self.photos_taken}/{self.total_photos} taken!")
                    audio.play("camera", 0.4)
                    if self.photos_taken >= self.total_photos:
                        self._say("take_photos_done")
                        self._schedule_next("sandstorm", 5.0)
                    return

    # -- sandstorm --
    def _handle_sandstorm(self, dt: float) -> None:
        self.t += dt
        self.sandstorm_active = True
        # visual: darken screen, show storm text
        # timer: 45 seconds
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start))
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.hud.toast(f"Sandstorm! Visibility dropping. Find shelter behind rocks. Time left: {minutes:01d}:{seconds:02d}")
        # after 45s, transition to cold alert
        if remaining <= 0:
            self._goto_phase("cold_alert")

    # -- cold_alert --
    def _handle_cold_alert(self, dt: float) -> None:
        self.t += dt
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start - 45.0))
        # actually cold alert starts after sandstorm, 45s timer
        # display cold warning
        self.hud.toast(f"Temperature dropping to -125 °C! Activate Hibernation Mode.")
        # if player presses H, activate hibernation
        keys = pygame.key.get_pressed()
        if keys[pygame.K_h] and not self.dlg.is_active():
            self.hibernation_active = True
            self._say("hibernation")
            self._schedule_next("hibernation", 45.0)
            return
        # if timer expires without hibernation
        if (self.state.elapsed - self.phase_start) > 45.0 + 45.0:
            # rover destroyed - should we game over?
            self._goto_phase("complete")

    # -- hibernation --
    def _handle_hibernation(self, dt: float) -> None:
        self.t += dt
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start - 90.0))
        self.hud.toast(f"Hibernation Mode active. Cold protecting rover. Time left: {int(remaining)}s")
        if remaining <= 0:
            self._goto_phase("complete")

    # -- complete --
    def _handle_complete(self, dt: float) -> None:
        self.t += dt
        if self.state.elapsed - self.phase_start >= 5.0:
            self.state.mark_level_done("surface", self.level_time)
            self.manager.switch(settings.BRIEFING, level_id="surface")

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
        elif self.phase == "take_photos":
            self._handle_take_photos(dt)
        elif self.phase == "sandstorm":
            self._handle_sandstorm(dt)
        elif self.phase == "cold_alert":
            self._handle_cold_alert(dt)
        elif self.phase == "hibernation":
            self._handle_hibernation(dt)
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

        # draw photo buttons
        for i, rect in enumerate(self.photo_button_rects):
            pygame.draw.rect(surface, (94, 210, 208), rect, 2, border_radius=5)
            text.draw(surface, f"CAM {i+1}", (rect.centerx, rect.centery - 10), 12, settings.DIM, display=True, center=True)

        # draw objective banner
        if self.objective:
            text.draw(surface, f"OBJECTIVE: {self.objective}",
                     (settings.WIDTH // 2, 60), 20, settings.INK, display=True, center=True)


# ----------------------------------------------------------------------
# Scene registration
# ----------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    from scenes.level1 import Level1Scene
    from scenes.level2 import Level2Scene
    from scenes.level3 import Level3Scene
    from scenes.briefing import BriefingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.LEVEL2, Level2Scene)
    manager.register(settings.LEVEL3, Level3Scene)
    manager.register(settings.BRIEFING, BriefingScene)