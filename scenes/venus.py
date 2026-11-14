"""Level 3: Venus timed survival. Pressure meter, fragments, acid pools."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, sprites
from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from entities.player import TopDownPlayer
from entities.pickups import Pickup
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.meter import Meter

hex_to_rgb = core_color.hex_to_rgb


class VenusScene(Scene):
    name = settings.VENUS
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("venus")
        self.params = self.cfg["params"]
        self.dialogue = levels.load_dialogue(self.cfg["dialogue"])
        self.part_color = hex_to_rgb(self.cfg["part"]["color"])
        self.hud = HUD(self.state, self.cfg)
        self.hud.set_objective(self.cfg.get("objective", ""))
        self.hud.set_hearts(self.state.hearts(), self.state.hearts())

        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=17)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=9)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)

        # single-screen arena centered
        arena_w, arena_h = 720, 600
        self.arena = pygame.Rect(
            (settings.WIDTH - arena_w) // 2,
            (settings.HEIGHT - arena_h) // 2 + 30,
            arena_w,
            arena_h,
        )
        offset = pygame.Vector2(self.arena.x, self.arena.y)

        start = self.params["player_start"]
        self.player = TopDownPlayer(start[0], start[1], self.params, self.state, self.hud)

        self.acid = [pygame.Rect(p).move(offset) for p in self.params["acid_pools"]]
        self.fragments = [
            Pickup(pygame.Vector2(f) + offset, kind="part", color=self.part_color, label="fragment")
            for f in self.params["fragments"]
        ]
        self.canisters = [
            Pickup(pygame.Vector2(c) + offset, kind="crate", color=settings.ACCENT, label="canister")
            for c in self.params["canisters"]
        ]
        self.exit_pos = pygame.Vector2(self.params["exit_pos"]) + offset

        self.pressure = Meter(
            (40, 34, 300, 20),
            "PRESSURE",
            settings.DANGER,
            max_value=100.0,
            show_value=True,
            unit=" bar",
            real_min=0.0,
            real_max=92.0,
        )
        self.pressure.set(0)

        self.time_limit = self.params["time_limit"]
        self.time_left = self.time_limit
        self.frag_needed = self.params["fragments_needed"]
        self.collected = 0

        self.dlg = DialogueBox(self.game)
        self.t = 0.0
        self.won = False
        self.lost = False
        self.restart_timer = 0.0
        self.countdown_hinted = False
        self.acid_cooldown = 0.0
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

    def _win(self) -> None:
        if self.won:
            return
        self.won = True
        audio.play("win")
        self.state.add_part(self.cfg["part"]["name"])
        self.state.add_fact("venus_pressure")
        self.state.add_fact("venus_temp")
        self.state.save()

    def _fail(self) -> None:
        if self.lost or self.won:
            return
        self.lost = True
        audio.play("lose")
        self.state.deaths += 1
        self.state.save()
        self.restart_timer = 0.0

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
        self.player.update(dt, keys, self.arena.inflate(-4, -4))

        if not self.won and not self.lost:
            # timer
            self.time_left -= dt
            if self.time_left <= 0:
                self._fail()
            elif self.time_left <= self.time_limit / 2 and not self.countdown_hinted:
                self.countdown_hinted = True
                lines = self.dialogue["lines"].get("countdown", [])
                if lines:
                    self.dlg.hint(lines[0])

            # pressure
            self.pressure.add(self.params["pressure_rate"] * dt)
            self.pressure.update(dt)
            if self.pressure.ratio >= 1.0:
                self._fail()

            # canisters
            for canister in self.canisters:
                canister.update(dt)
                if not canister.taken and canister.collides(self.player.rect):
                    canister.taken = True
                    audio.play("pickup")
                    self.pressure.add(-self.params["canister_effect"])

            # fragments
            for fragment in self.fragments:
                fragment.update(dt)
                if not fragment.taken and fragment.collides(self.player.rect):
                    fragment.taken = True
                    audio.play("part")
                    self.collected += 1
                    if self.collected >= self.frag_needed:
                        self.hud.set_objective("All fragments secured - reach the escape beacon!")

            # acid
            self.acid_cooldown = max(0.0, self.acid_cooldown - dt)
            if self.acid_cooldown <= 0 and any(p.collidepoint(self.player.pos) for p in self.acid):
                self.acid_cooldown = 0.8
                self.player.take_damage()

            # exit
            if self.collected >= self.frag_needed:
                if self.player.pos.distance_to(self.exit_pos) < 34:
                    self._win()

        self.hud.set_hearts(self.player.health, self.player.max_health)

        if self.player.dead and not self.lost:
            self.restart_timer += dt
            if self.restart_timer > 1.0:
                self.lost = True
                self.manager.switch(settings.VENUS)

        if self.lost:
            self.restart_timer += dt
            if self.restart_timer > 1.4:
                self.manager.switch(settings.VENUS)

        self.dlg.update(dt)
        self.hud.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        # arena
        pygame.draw.rect(screen, (24, 34, 52), self.arena, border_radius=10)
        pygame.draw.rect(screen, settings.PANEL_EDGE, self.arena, 2, border_radius=10)

        # acid pools
        for pool in self.acid:
            pygame.draw.rect(screen, (120, 190, 90, 90), pool, border_radius=8)
            pygame.draw.rect(screen, (180, 230, 120), pool, 1, border_radius=8)

        # exit beacon
        ready = self.collected >= self.frag_needed
        pulse = 0.5 + 0.5 * abs(math.sin(self.t * 3.0))
        exit_color = settings.GREEN if ready else settings.FAINT
        pygame.draw.circle(screen, exit_color, self.exit_pos, int(10 + 6 * pulse) if ready else 10, 2)
        text.draw(
            screen,
            "ESCAPE" if ready else "LOCKED",
            (self.exit_pos.x, self.exit_pos.y - 20),
            14,
            exit_color,
            center=True,
            shadow=False,
        )

        # pickups
        for fragment in self.fragments:
            fragment.draw(screen)
        for canister in self.canisters:
            canister.draw(screen)
        self.player.draw(screen)

        # timer text
        remaining = max(0.0, self.time_left)
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        text.draw(
            screen,
            f"{minutes:01d}:{seconds:02d}",
            (settings.WIDTH // 2, 66),
            30,
            settings.DANGER if remaining < 20 else settings.INK,
            display=True,
            center=True,
        )

        # collected counter
        text.draw(
            screen,
            f"FRAGMENTS {self.collected}/{self.frag_needed}",
            (settings.WIDTH // 2, 100),
            20,
            settings.DIM,
            center=True,
            shadow=False,
        )

        self.pressure.draw(screen)
        self.hud.draw(screen)
        self.dlg.draw(screen)
        screen.blit(self.vignette, (0, 0))
