"""Level 3: Martian Surface.

Rover exploration: take photographs, survive sandstorm, activate hibernation.
"""

from __future__ import annotations

import math
import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from core.game_state import GameState
from art import environments, sprites
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

        self.hud.set_counters([
            {"label": "PHOTOS", "value": f"0/{self.total_photos}", "color": settings.ACCENT},
            {"label": "SAMPLES", "value": "0/1", "color": settings.GOLD},
        ])

        # backdrop
        self.backdrop, self.rocks = environments.mars_surface(settings.WIDTH, settings.HEIGHT, seed=11)

        # player
        self.player_pos = pygame.Vector2(self.params["player_start"])
        self.vending_rect = pygame.Rect(96, 196, 112, 168)

        # PPTX: rock/soil sample collection + low power mode during the sandstorm
        self.sample_rect = pygame.Rect(880, 300, 60, 60)
        self.low_power = False
        self.sandstorm_pos = pygame.Vector2(self.player_pos)
        self.cold_period = 45.0

        # marked camera buttons on the surface
        self.photo_button_rects = [
            pygame.Rect(300, 260, 60, 60),
            pygame.Rect(480, 200, 60, 60),
            pygame.Rect(660, 260, 60, 60),
            pygame.Rect(840, 200, 60, 60),
            pygame.Rect(420, 340, 60, 60),
            pygame.Rect(600, 340, 60, 60),
        ]

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
        self.low_power = False

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

    def _lose_mission(self) -> None:
        """The rover was destroyed / the survival run failed."""
        audio.play("boom")
        self.state.finish_mission("lost")
        self.manager.switch(settings.LEVEL3)

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
        elapsed = self.state.elapsed - self.phase_start

        # PPTX: five minutes to reach and interact with all marked cameras; when
        # the countdown reaches the 3:30 mark the temperature begins to drop.
        if elapsed >= 180.0:
            self.hud.banner("TEMPERATURE DROPPING TO -125°C - ACTIVATE HIBERNATION MODE", 4.0, settings.DANGER)
            self._goto_phase("cold_alert")
            return
        if elapsed >= 300.0:
            # Five minutes ran out before the survey objectives were met.
            self._lose_mission()
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_e] and not self.dlg.is_active():
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            # rock / soil sample collection alongside the photography
            if self.sample_rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])):
                if self.state.add_item("mars_sample"):
                    self.state.samples = int(getattr(self.state, "samples", 0) or 0) + 1
                    self.hud.toast("Mars rock sample collected!")
                    audio.play("confirm", 0.4)
            # press E near a photo button to take picture
            for i, rect in enumerate(self.photo_button_rects):
                if rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])):
                    self.photos_taken += 1
                    self.hud.toast(f"Photo {self.photos_taken}/{self.total_photos} taken!")
                    audio.play("camera", 0.4)
                    if self.photos_taken >= self.total_photos:
                        if self.state.has_item("mars_sample"):
                            self._goto_phase("sandstorm")
                        else:
                            self.hud.toast("Collect the rock sample before the storm arrives.")
                    return

    # -- sandstorm --
    def _handle_sandstorm(self, dt: float) -> None:
        self.t += dt
        self.sandstorm_active = True
        # PPTX: player must find shelter behind the rocks, stop scientific
        # activities and activate Low Power Mode. Moving through the dust means
        # the dense dust blocks the solar panels -> the rover fails.
        moved = pygame.Vector2(self.player_pos) - self.sandstorm_pos
        if moved.length() > 40.0:
            self.hud.banner("DUST STORM - SOLAR PANELS UNREACHABLE - ROVER LOST", 4.0, settings.DANGER)
            self._lose_mission()
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_l] and not self.dlg.is_active():
            # PPTX: stop scientific activities / protect the rover systems.
            self.low_power = True
            audio.play("power_down", 0.5)
            self.hud.toast("LOW POWER MODE ACTIVATED - scientific activities halted")

        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start))
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.hud.toast(f"Sandstorm! Visibility dropping. Find shelter behind rocks. Low Power Mode: {'ON' if self.low_power else 'OFF'}. Time left: {minutes:01d}:{seconds:02d}")
        if remaining <= 0:
            self._goto_phase("cold_alert")

    # -- cold_alert --
    def _handle_cold_alert(self, dt: float) -> None:
        self.t += dt
        # PPTX: after the storm the temperature drops to -125C; the player must
        # decide to continue or activate Hibernation Mode.
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start))
        self.hud.toast(f"Temperature dropping to -125 °C! Activate Hibernation Mode.")
        keys = pygame.key.get_pressed()
        if keys[pygame.K_h] and not self.dlg.is_active():
            # PPTX: activate Hibernation Mode to protect the rover from the cold.
            self.hibernation_active = True
            self._goto_phase("hibernation")
            return
        if remaining <= 0:
            # never hibernated in time - the rover was destroyed by the cold
            self._lose_mission()

    # -- hibernation --
    def _handle_hibernation(self, dt: float) -> None:
        self.t += dt
        remaining = max(0.0, 45.0 - (self.state.elapsed - self.phase_start))
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