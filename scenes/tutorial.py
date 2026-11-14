"""Level 0: Earth orbit tutorial. Top-down, no fail state."""

from __future__ import annotations

import math
import pygame

from art import backgrounds
from core import audio, levels, settings, text
from core.scene import Scene
from entities.player import TopDownPlayer
from entities.pickups import Pickup
from ui.dialogue_box import DialogueBox
from ui.hud import HUD

MARKER_COLOR = settings.ACCENT
CRATE_COLOR = settings.GOLD


class TutorialScene(Scene):
    name = settings.TUTORIAL
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("tutorial")
        self.params = self.cfg["params"]
        self.dialogue = levels.load_dialogue(self.cfg["dialogue"])
        self.hud = HUD(self.state, self.cfg)
        self.hud.set_objective(self.cfg.get("objective", ""))

        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)

        self.screen_rect = pygame.Rect(0, 0, settings.WIDTH, settings.HEIGHT)
        self.player = TopDownPlayer(
            *self.params["player_start"], self.params, self.state, self.hud
        )
        marker = self.params["marker"]
        crate = self.params["crate"]
        self.marker_pos = pygame.Vector2(marker)
        self.crate = Pickup(crate, kind="crate", color=CRATE_COLOR, label="bracket")

        self.dlg = DialogueBox(self.game)
        self.stage = "start"
        self.hint_index = 0
        self.hinted_once = False
        self.won = False

        self.hud.hint_prompt = True
        self._play_start_dialogue()

    # --- dialogue ----------------------------------------------------------
    def _play_start_dialogue(self) -> None:
        lines = self.dialogue["lines"].get("start", [])
        if lines:
            self.dlg.queue(lines, on_done=self._start_done)
        else:
            self._start_done()

    def _start_done(self) -> None:
        self.stage = "go_marker"
        self.hud.set_objective("Fly to the beacon.")

    def _queue_trigger(self, trigger: str, on_done=None) -> None:
        lines = self.dialogue["lines"].get(trigger, [])
        if lines:
            self.dlg.queue(lines, on_done=on_done)
        elif on_done:
            on_done()

    def _hint_lines(self) -> None:
        lines = self.dialogue["lines"].get("hint", [])
        if not lines:
            return
        # the H press is the final task: show one hint, then launch the map
        if self.stage == "got_crate" and not self.hinted_once:
            self.hinted_once = True
            self.dlg.queue([lines[0]], on_done=self._finish)
            return
        line = lines[self.hint_index % len(lines)]
        self.hint_index += 1
        self.dlg.hint(line)

    # --- tasks -------------------------------------------------------------
    def _at_marker(self) -> None:
        if self.stage != "go_marker":
            return
        self.stage = "at_marker"
        self._queue_trigger("marker", self._marker_done)

    def _marker_done(self) -> None:
        self.hud.set_objective("Collect the bracket crate below the ship.")
        self.stage = "go_crate"

    def _got_crate(self) -> None:
        if self.stage != "go_crate":
            return
        self.crate.taken = True
        self.stage = "got_crate"
        self.hud.set_objective("Press H to ask Laila for a hint.")
        self._queue_trigger("crate", self._crate_done)

    def _crate_done(self) -> None:
        pass

    def _finish(self) -> None:
        if self.won:
            return
        self.won = True
        audio.play("win")
        self.state.tutorial_done = True
        self.state.add_fact("tutorial_parts")
        self.state.save()
        self._queue_trigger("win", self._win_done)

    def _win_done(self) -> None:
        self.manager.switch(settings.MAP)

    # --- input -------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self._hint_lines()
                elif event.key == pygame.K_ESCAPE:
                    self.manager.push(settings.PAUSE, parent=self)

    # --- update ------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t = getattr(self, "t", 0.0) + dt
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.screen_rect)

        if not self.dlg.is_active() and not self.won:
            if self.stage == "go_marker":
                if self.player.rect.collidepoint(self.marker_pos):
                    self._at_marker()
            elif self.stage == "go_crate":
                if (
                    self.crate
                    and not self.crate.taken
                    and self.player.pos.distance_to(pygame.Vector2(self.crate.pos)) < 30
                ):
                    self._got_crate()

        self.player.tick(dt)
        self.crate.update(dt)
        self.dlg.update(dt)
        self.hud.update(dt)

    # --- drawing -----------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        # beacon marker
        pulse = 0.5 + 0.5 * abs(math.sin(self.t * 2.5))
        pygame.draw.circle(
            screen, MARKER_COLOR, (int(self.marker_pos.x), int(self.marker_pos.y)), 8, 2
        )
        pygame.draw.circle(
            screen,
            MARKER_COLOR,
            (int(self.marker_pos.x), int(self.marker_pos.y)),
            int(4 + 4 * pulse),
        )
        text.draw(
            screen,
            "BEACON",
            (int(self.marker_pos.x), int(self.marker_pos.y) - 18),
            14,
            settings.DIM,
            center=True,
            shadow=False,
        )

        self.crate.draw(screen)
        self.player.draw(screen)

        self.hud.draw(screen)
        self.dlg.draw(screen)
        screen.blit(self.vignette, (0, 0))
