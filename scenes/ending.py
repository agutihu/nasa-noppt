"""Finale: assemble the ship from collected parts, then the stats screen."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, planets, sprites
from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from ui.button import Button
from ui.dialogue_box import DialogueBox

hex_to_rgb = core_color.hex_to_rgb


def _fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class EndingScene(Scene):
    name = settings.ENDING
    counts_time = True

    def on_enter(self, **data) -> None:
        if not self.state.all_parts():
            self.manager.switch(settings.MAP)
            return

        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)

        self.index = levels.planet_index()
        self.required = self.state.required_parts()
        self.ship_center = (430, 330)
        # sockets: one row under the ship, sized for however many parts the run has
        socket_count = len(self.required)
        self.socket_positions = [
            (self.ship_center[0] + (slot - (socket_count - 1) / 2) * 80, 480)
            for slot in range(socket_count)
        ]
        # cargo tray: two columns, kept above the dialogue box
        self.tray_positions = [
            (
                940 + (index // 4) * 140,
                168 + (index % 4) * 92,
            )
            for index in range(socket_count)
        ]
        self.placed: dict[str, int] = {}
        self.selected: str | None = None
        self.phase = "assemble"
        self.t = 0.0

        self.dlg = DialogueBox(self.game)
        self.launch_button = None
        self.stats_buttons: list[Button] = []
        self._build_stats_buttons()
        self._intro()

    def _intro(self) -> None:
        lines = [
            f"All {len(self.required)} parts recovered. Drag each one into its socket, then we go home."
        ]
        self.dlg.queue(lines, on_done=None)

    def _build_stats_buttons(self) -> None:
        y = 640
        self.stats_buttons = [
            Button((settings.WIDTH // 2 - 220, y, 200, 52), "Fly again", self._play_again),
            Button((settings.WIDTH // 2 + 20, y, 200, 52), "Back to menu", self._menu, style="ghost"),
        ]

    def _play_again(self) -> None:
        self.state.reset()
        self.manager.switch(settings.TUTORIAL)

    def _menu(self) -> None:
        self.manager.switch(settings.MENU)

    def _part_planet(self, part: str):
        for planet in self.index.values():
            if planet.get("part") == part:
                return planet
        return None

    # --- interaction --------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.switch(settings.MENU)
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.phase != "assemble":
                    continue
                # tray pick
                for part, pos in zip(self.required, self.tray_positions):
                    if part in self.placed:
                        continue
                    rect = pygame.Rect(0, 0, 64, 64)
                    rect.center = pos
                    if rect.collidepoint(event.pos):
                        self.selected = part
                        audio.play("hover", 0.8)
                        break
                # socket drop
                else:
                    if self.selected:
                        for slot, socket_pos in enumerate(self.socket_positions):
                            rect = pygame.Rect(0, 0, 70, 70)
                            rect.center = socket_pos
                            if rect.collidepoint(event.pos):
                                self._place(self.selected, slot)
                                break

        if self.phase == "stats":
            for button in self.stats_buttons:
                button.handle_events(events)
        elif self.launch_button:
            self.launch_button.handle_events(events)

    def _place(self, part: str, slot: int) -> None:
        if part in self.placed:
            return
        self.placed[part] = slot
        self.selected = None
        audio.play("part")
        planet = self._part_planet(part)
        if planet:
            self.dlg.hint(f"{planet['name']}: {planet['fact']}")
        if len(self.placed) >= len(self.required):
            self.launch_button = Button(
                (self.ship_center[0] - 110, self.ship_center[1] + 240, 220, 52),
                "Launch for home",
                self._launch,
            )

    def _launch(self) -> None:
        self.phase = "stats"
        audio.play("win")
        self.state.save()
        self.launch_button = None

    # --- update -------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        self.dlg.update(dt)

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        if self.phase == "stats":
            self._draw_stats(screen)
            screen.blit(self.vignette, (0, 0))
            return

        # earth limb
        planets.draw_planet(screen, (200, 760), 300, (58, 126, 184), band_color=(88, 168, 116), bands=2, seed=7)

        text.draw(screen, "ASSEMBLY BAY", (settings.WIDTH // 2, 70), 30, settings.ACCENT, display=True, center=True)
        text.draw(
            screen,
            "Click a part, then click a socket.",
            (settings.WIDTH // 2, 116),
            22,
            settings.DIM,
            center=True,
            shadow=False,
        )

        sprites.draw_ship(screen, self.ship_center, 1.5, self.t, thrust=False)

        # sockets
        for slot, socket_pos in enumerate(self.socket_positions):
            occupant = next((p for p, s in self.placed.items() if s == slot), None)
            if occupant:
                part_color = hex_to_rgb(self._part_planet(occupant).get("color", "#8fa3c8"))
                sprites.draw_part(screen, socket_pos, 24, part_color, self.t)
            else:
                pulse = 0.5 + 0.5 * abs(math.sin(self.t * 2.0))
                pygame.draw.circle(screen, settings.PANEL_EDGE, socket_pos, 30, 2)
                pygame.draw.circle(screen, (16, 26, 44), socket_pos, 26)
                if self.selected:
                    pygame.draw.circle(screen, settings.ACCENT, socket_pos, int(30 + 6 * pulse), 1)

        # tray
        text.draw(screen, "CARGO", (settings.WIDTH - 250, 112), 16, settings.ACCENT, display=True, center=True)
        for part, pos in zip(self.required, self.tray_positions):
            if part in self.placed:
                continue
            rect = pygame.Rect(0, 0, 64, 64)
            rect.center = pos
            is_selected = self.selected == part
            pygame.draw.rect(screen, settings.PANEL_LIGHT if is_selected else settings.PANEL, rect, border_radius=10)
            pygame.draw.rect(
                screen,
                settings.ACCENT if is_selected else settings.PANEL_EDGE,
                rect,
                2 if is_selected else 1,
                border_radius=10,
            )
            sprites.draw_part(screen, pos, 18, hex_to_rgb(self._part_planet(part).get("color", "#8fa3c8")), self.t)
            text.draw(screen, part, (pos[0], pos[1] + 44), 14, settings.DIM, center=True, shadow=False)

        if self.launch_button:
            self.launch_button.draw(screen)

        self.dlg.draw(screen)
        screen.blit(self.vignette, (0, 0))

    def _draw_stats(self, screen: pygame.Surface) -> None:
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 4, 10, 235))
        screen.blit(veil, (0, 0))

        text.draw(screen, "WELCOME HOME", (settings.WIDTH // 2, 150), 40, settings.ACCENT, display=True, center=True)
        text.draw(
            screen,
            "The ship is whole again. Laika says hello to the ground crew.",
            (settings.WIDTH // 2, 212),
            24,
            settings.INK,
            center=True,
            max_width=720,
            shadow=False,
        )

        rows = [
            ("Mission time", _fmt_time(self.state.elapsed)),
            ("Losses", str(self.state.deaths)),
            ("Parts recovered", f"{self.state.part_count}/{len(self.required)}"),
            ("Facts learned", str(self.state.fact_count)),
        ]
        y = 280
        for label, value in rows:
            text.draw(screen, label, (settings.WIDTH // 2 - 130, y), 22, settings.DIM)
            text.draw(screen, value, (settings.WIDTH // 2 + 130, y), 22, settings.INK, right=True)
            y += 44

        if self.state.facts:
            text.draw(
                screen,
                "Facts: " + ", ".join(self.state.facts),
                (settings.WIDTH // 2, 505),
                17,
                settings.FAINT,
                center=True,
                max_width=760,
                shadow=False,
            )

        if self.state.best_times:
            bests = "  ".join(
                f"{levels.planet_index().get(level_id, {}).get('name', level_id)} {_fmt_time(time)}"
                for level_id, time in sorted(
                    self.state.best_times.items(),
                    key=lambda item: self.state.levels_done.index(item[0]),
                )
            )
            text.draw(
                screen,
                "Best times: " + bests,
                (settings.WIDTH // 2, 470),
                18,
                settings.DIM,
                center=True,
                max_width=980,
                shadow=False,
            )

        text.draw(
            screen,
            "Every mechanic in this game comes from NASA data: planetary fact sheets, APOD, JPL solar system values.",
            (settings.WIDTH // 2, 556),
            18,
            settings.DIM,
            center=True,
            max_width=860,
            shadow=False,
        )

        for button in self.stats_buttons:
            button.draw(screen)
