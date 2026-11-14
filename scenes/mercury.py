"""Level 2: Mercury top-down stealth. Outrun the sun line; hide in shadows."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, planets, sprites
from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from entities.enemies import Patrol
from entities.player import TopDownPlayer
from entities.pickups import Pickup
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.meter import Meter

hex_to_rgb = core_color.hex_to_rgb

WORLD_W = 1760
WORLD_H = 560


class MercuryScene(Scene):
    name = settings.MERCURY
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("mercury")
        self.params = self.cfg["params"]
        self.dialogue = levels.load_dialogue(self.cfg["dialogue"])
        self.part_color = hex_to_rgb(self.cfg["part"]["color"])
        self.hud = HUD(self.state, self.cfg)
        self.hud.set_objective(self.cfg.get("objective", ""))
        self.hud.set_hearts(self.state.hearts(), self.state.hearts())

        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=13)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)

        self.world_rect = pygame.Rect(0, 0, WORLD_W, WORLD_H)
        start = self.params["player_start"]
        self.player = TopDownPlayer(start[0], start[1], self.params, self.state, self.hud)

        self.shadows = [pygame.Rect(s) for s in self.params["shadows"]]
        cx, cy = self.params["part_pos"]
        self.part = Pickup((cx, cy), kind="part", color=self.part_color, label=self.cfg["part"]["name"])

        self.patrols = [
            Patrol((520, 420), (520, 280), self.cfg, self.state),
            Patrol((940, 120), (1100, 120), self.cfg, self.state),
            Patrol((1240, 420), (1400, 420), self.cfg, self.state),
        ]

        self.sun_x = float(WORLD_W + 120)
        self.heat = Meter(
            (40, 34, 300, 20),
            "SUIT TEMP",
            settings.DANGER,
            max_value=self.params["meter_max"],
            show_value=True,
            unit="\u00b0C",
            real_min=-180.0,
            real_max=430.0,
        )
        self.heat.set(self.params["meter_max"] * 0.3)

        self.dlg = DialogueBox(self.game)
        self.t = 0.0
        self.won = False
        self.lost = False
        self.restart_timer = 0.0
        self.heat_hinted = False
        self.overheated = False
        self._intro_dialogue()

    def _intro_dialogue(self) -> None:
        lines = self.dialogue["lines"].get("start", [])
        if lines:
            self.dlg.queue(lines, on_done=self._intro_done)

    def _intro_done(self) -> None:
        pass

    def _hint(self) -> None:
        lines = self.dialogue["lines"].get("hint", [])
        if lines:
            self.dlg.hint(lines[0])

    def _heat_warning(self) -> None:
        if self.heat_hinted:
            return
        lines = self.dialogue["lines"].get("heat", [])
        if lines:
            self.dlg.hint(lines[0])
            self.heat_hinted = True

    def _win_dialogue(self) -> None:
        lines = self.dialogue["lines"].get("win", [])
        if lines:
            self.dlg.queue(lines, on_done=self._win)
        else:
            self._win()

    def _win(self) -> None:
        if self.won:
            return
        self.won = True
        audio.play("win")
        self.state.add_part(self.cfg["part"]["name"])
        self.state.add_fact("mercury_temps")
        self.state.add_fact("mercury_atmosphere")
        self.state.save()

    def _camera(self) -> tuple[int, int]:
        target_x = self.player.pos.x - settings.WIDTH / 2
        target_y = self.player.pos.y - settings.HEIGHT / 2
        return (int(max(0, min(target_x, WORLD_W - settings.WIDTH))),
                int(max(0, min(target_y, WORLD_H - settings.HEIGHT))))

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.push(settings.PAUSE, parent=self)
                elif event.key == pygame.K_h:
                    self._hint()

    def update(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.world_rect)

        if not self.won and not self.lost:
            self.sun_x -= self.params["sun_speed"] * dt
            if self.sun_x < -200:
                self.sun_x = WORLD_W + 200

            in_shadow = any(s.collidepoint(self.player.pos) for s in self.shadows)
            in_sunlight = self.player.pos.x > self.sun_x
            if in_sunlight and not in_shadow:
                self.heat.add(self.params["heat_rise_rate"] * dt)
                if self.heat.ratio >= 0.72 and not self.heat_hinted:
                    self._heat_warning()
            else:
                self.heat.add(-self.params["heat_fall_rate"] * dt)
            self.heat.update(dt)

            if self.heat.ratio >= 1.0 and not self.overheated:
                self.overheated = True
                self.player.take_damage()
                self.state.deaths += 1
                self.state.save()
            if self.heat.ratio < 0.5:
                self.overheated = False

            for patrol in self.patrols:
                patrol.update(dt, self.player)
                if patrol.collides_player(self.player):
                    self.player.take_damage()

            if not self.part.taken and self.player.rect.colliderect(self.part.rect):
                self.part.taken = True
                self._win_dialogue()

        self.hud.set_hearts(self.player.health, self.player.max_health)

        if self.player.dead and not self.lost:
            self.restart_timer += dt
            if self.restart_timer > 1.0:
                self.lost = True
                self.manager.switch(settings.MERCURY)

        self.dlg.update(dt)
        self.hud.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        camera = self._camera()
        screen.blit(self.stars, (-camera[0] % settings.WIDTH, -camera[1]))
        screen.blit(self.neb, (0, 0))

        def ws(pos):
            return (int(pos[0] - camera[0]), int(pos[1] - camera[1]))

        # sun line
        line_x = self.sun_x - camera[0]
        pygame.draw.line(screen, settings.WARN, (line_x, -40), (line_x, settings.HEIGHT + 40), 3)
        pygame.draw.line(screen, settings.WARN, (line_x - 4, -40), (line_x - 4, settings.HEIGHT + 40), 1)
        # night/day tint
        if line_x > 0:
            veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(veil, (30, 10, 10, 90), pygame.Rect(line_x, 0, settings.WIDTH - line_x, settings.HEIGHT))
            screen.blit(veil, (0, 0))

        # shadows
        for shadow in self.shadows:
            r = shadow.move(-camera[0], -camera[1])
            pygame.draw.rect(screen, (10, 16, 30), r)
            pygame.draw.rect(screen, (44, 60, 90), r, 1)

        for patrol in self.patrols:
            patrol.draw(screen, camera)
        if not self.part.taken:
            sprites.draw_part(screen, ws(self.part.pos), 14, self.part_color, self.t)
        self.player.draw(screen)

        self.heat.draw(screen)
        self.hud.draw(screen)
        self.dlg.draw(screen)
        screen.blit(self.vignette, (0, 0))
