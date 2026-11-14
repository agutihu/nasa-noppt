"""Level 1: Mars platformer. Low gravity + dust storm."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, planets, sprites
from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from entities.enemies import Chaser, Patrol, Projectile, Turret
from entities.player import PlatformerPlayer
from entities.pickups import Pickup
from ui.dialogue_box import DialogueBox
from ui.hud import HUD

hex_to_rgb = core_color.hex_to_rgb

WORLD_W = 4400
WORLD_H = 720
GROUND_Y = 560


class MarsScene(Scene):
    name = settings.MARS
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("mars")
        self.params = self.cfg["params"]
        self.dialogue = levels.load_dialogue(self.cfg["dialogue"])
        self.part_color = hex_to_rgb(self.cfg["part"]["color"])
        self.hud = HUD(self.state, self.cfg)
        self.hud.set_objective(self.cfg.get("objective", ""))
        self.hud.set_hearts(self.state.hearts(), self.state.hearts())

        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)

        self.screen_rect = pygame.Rect(0, 0, settings.WORLD_W if False else settings.WIDTH, settings.HEIGHT)

        start = self.params["player_start"]
        self.player = PlatformerPlayer(start[0], start[1], self.params, self.state, self.hud)
        self.player.max_health = self.state.hearts()
        self.player.health = self.player.max_health

        self.platforms = [
            pygame.Rect(0, GROUND_Y, 700, 160),
            pygame.Rect(760, 430, 260, 170),
            pygame.Rect(1120, 300, 260, 200),
            pygame.Rect(1480, 430, 280, 150),
            pygame.Rect(1780, 510, 320, 140),   # checkpoint zone
            pygame.Rect(2180, 450, 220, 160),
            pygame.Rect(2500, 300, 220, 170),
            pygame.Rect(2820, 430, 220, 160),
            pygame.Rect(3140, 510, 240, 140),   # checkpoint zone
            pygame.Rect(3400, 450, 860, 150),   # storm runway
            pygame.Rect(3920, 130, 260, 120),   # part platform
            pygame.Rect(4160, GROUND_Y, 240, 160),
        ]
        self.checkpoints = self.params["checkpoints"]
        self.last_checkpoint = self.checkpoints[0]

        cx, cy = self.params["part_pos"]
        self.part = Pickup((cx, cy), kind="part", color=self.part_color, label=self.cfg["part"]["name"])

        self.chasers = [Chaser((2280, 500), self.cfg, self.state)]
        self.patrols = []
        self.turrets = [Turret((3720, 505), (1, 0.15), 2.4)]
        self.projectiles: list[Projectile] = []

        self.storm_timer = 0.0
        self.storm_active = False
        self.storm_time_left = 0.0
        self.storm_count = 0
        self.storm_hinted = False

        self.dlg = DialogueBox(self.game)
        self.deaths_at_start = self.state.deaths
        self.death_hinted = False
        self.t = 0.0
        self.won = False
        self.lost = False
        self.restart_timer = 0.0

        self._intro_dialogue()

    # --- systems ----------------------------------------------------------
    def _intro_dialogue(self) -> None:
        lines = self.dialogue["lines"].get("start", [])
        if lines:
            self.dlg.queue(lines, on_done=self._intro_done)
        else:
            self._intro_done()

    def _intro_done(self) -> None:
        pass

    def _hint(self) -> None:
        lines = self.dialogue["lines"].get("hint", [])
        if lines:
            self.dlg.hint(lines[(self.state.deaths) % len(lines)])

    def _death_hint(self) -> None:
        lines = self.dialogue["lines"].get("death_3", [])
        if lines:
            self.dlg.queue(lines)

    def _storm_line(self) -> None:
        lines = self.dialogue["lines"].get("storm", [])
        if lines:
            self.dlg.hint(lines[0])

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
        self.state.add_fact("mars_gravity")
        self.state.add_fact("mars_dust_storms")
        self.state.save()

    # --- camera -----------------------------------------------------------
    def _camera_x(self) -> float:
        target = self.player.pos.x - settings.WIDTH / 2
        return max(0.0, min(target, WORLD_W - settings.WIDTH))

    # --- storm ------------------------------------------------------------
    def _update_storm(self, dt: float) -> None:
        if self.won or self.lost:
            return
        if self.storm_active:
            self.storm_time_left -= dt
            if self.storm_time_left <= 0:
                self.storm_active = False
            elif not self.storm_hinted and self.storm_time_left <= 6.0:
                self._storm_line()
                self.storm_hinted = True
        else:
            self.storm_timer += dt
            if self.storm_timer >= self.params["storm_interval"]:
                self.storm_active = True
                self.storm_time_left = self.params["storm_duration"]
                self.storm_timer = 0.0
                self.storm_count += 1
                self.storm_hinted = False
                self._storm_line()

    # --- input / update ---------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.push(settings.PAUSE, parent=self)
                elif event.key == pygame.K_SPACE:
                    self.player.jump()
                elif event.key == pygame.K_h:
                    self._hint()

    def update(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        solids = [p for p in self.platforms]
        self.player.update(dt, keys, None, solids)

        if not self.lost and not self.won:
            self._update_storm(dt)

            # damage
            for chaser in self.chasers:
                chaser.update(dt, self.player, self.screen_rect)
                if chaser.collides_player(self.player):
                    self.player.take_damage()
            for patrol in self.patrols:
                patrol.update(dt, self.player)
                if patrol.collides_player(self.player):
                    self.player.take_damage()

            new_projectiles = []
            for turret in self.turrets:
                shot = turret.update(dt, self.player.pos)
                if shot:
                    new_projectiles.append(shot)
            for proj in self.projectiles:
                proj.update(dt, self.screen_rect)
                if not proj.dead and proj.collides_player(self.player):
                    self.player.take_damage()
                    proj.dead = True
            self.projectiles = [p for p in self.projectiles if not p.dead]
            self.projectiles.extend(new_projectiles)
            self.hud.set_hearts(self.player.health, self.player.max_health)

            # part
            if not self.part.taken and self.part.collides(self.player.rect):
                self.part.taken = True
                self._win_dialogue()

            # checkpoints passed
            for cp in self.checkpoints:
                if self.player.pos.x >= cp:
                    self.last_checkpoint = cp

        # death / respawn
        if self.player.dead and not self.lost:
            self.restart_timer += dt
            if self.restart_timer > 1.0:
                self.restart_timer = 0.0
                self.state.deaths += 1
                self.state.save()
                cx = self.last_checkpoint
                cy = next((p.top for p in self.platforms if p.left <= cx <= p.right), GROUND_Y)
                self.player.respawn(cx, cy - 40)
                self.hud.set_hearts(self.player.health, self.player.max_health)
                if self.state.deaths >= 3 and not self.death_hinted:
                    self.death_hinted = True
                    self._death_hint()

        # bottomless fall
        if self.player.pos.y > WORLD_H + 200 and not self.lost:
            self._die()

        self.dlg.update(dt)
        self.hud.update(dt)

    def _die(self) -> None:
        if self.lost:
            return
        self.lost = True
        self.player.dead = True
        audio.play("lose")

    # --- drawing ----------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        camera_x = self._camera_x()
        camera = (int(camera_x), 0)
        screen.blit(self.stars, (-int(camera_x % settings.WIDTH), 0))
        screen.blit(self.neb, (0, 0))

        def world_to_screen(wx: float, wy: float) -> tuple[int, int]:
            return (int(wx - camera[0]), int(wy - camera[1]))

        # platforms
        for plat in self.platforms:
            r = plat.move(-camera[0], -camera[1])
            pygame.draw.rect(screen, (42, 56, 82), r, border_radius=4)
            pygame.draw.rect(screen, (74, 98, 134), r, 1, border_radius=4)
            top = r.copy(); top.height = 6
            pygame.draw.rect(screen, (110, 140, 178), top)

        # part
        if not self.part.taken:
            self.part.pos = pygame.Vector2(self.params["part_pos"])
            draw_x = self.params["part_pos"][0] - camera[0]
            draw_y = self.params["part_pos"][1] - camera[1]
            sprites.draw_part(screen, (int(draw_x), int(draw_y)), 14, self.part_color, self.t)

        # enemies + projectiles
        for chaser in self.chasers:
            chaser.draw(screen, camera)
        for patrol in self.patrols:
            patrol.draw(screen, camera)
        for turret in self.turrets:
            turret.draw(screen, camera)
        for proj in self.projectiles:
            proj.draw(screen, camera)

        # player
        self.player.draw(screen)

        # storm overlay
        if self.storm_active:
            radius = self.params["visibility_radius"]
            px = int(self.player.pos.x - camera[0])
            py = int(self.player.pos.y - camera[1])
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            cut = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(cut, (0, 0, 0, 255), (radius, radius), radius)
            overlay.blit(cut, (px - radius, py - radius), special_flags=pygame.BLEND_RGBA_SUB)
            screen.blit(overlay, (0, 0))

        self.hud.draw(screen)
        self.dlg.draw(screen)
        screen.blit(self.vignette, (0, 0))
