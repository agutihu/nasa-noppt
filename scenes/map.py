"""Solar system map: hub screen to inspect and launch missions."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, planets, sprites
from core import audio, color as core_color, levels, settings, text

hex_to_rgb = core_color.hex_to_rgb


def draw_ring(
    screen: pygame.Surface,
    cx: int,
    cy: int,
    radius: float,
    color: tuple[int, int, int],
    t: float,
) -> None:
    pulse = 0.35 + 0.35 * abs(math.sin(t * 2.0))
    ring_r = radius * pulse
    pygame.draw.circle(screen, color, (cx, cy), int(ring_r), 2)

from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from ui.button import Button

hex_to_rgb = core_color.hex_to_rgb


class MapScene(Scene):
    name = settings.MAP

    def on_enter(self, **data) -> None:
        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)
        self.planets = levels.load_planets()["planets"]
        self.selected = None
        self.t = 0.0
        self.toast = ""
        self.toast_timer = 0.0
        self.mouse = (settings.WIDTH // 2, settings.HEIGHT // 2)
        self._resolve_positions()
        self.panel_buttons: list[Button] = []
        self.detail = None
        self._build_panel()

    def _resolve_positions(self) -> None:
        for planet in self.planets:
            p = planet["map_position"]
            planet["_pos"] = (int(p[0] * settings.WIDTH), int(p[1] * settings.HEIGHT))

    def _seed_for(self, planet) -> int:
        return sum(ord(ch) for ch in planet["id"]) * 7 + 1

    # --- selection ----------------------------------------------------------
    def _find_at(self, pos: tuple[int, int]):
        for planet in self.planets:
            px, py = planet["_pos"]
            radius = int(planet["radius"] * 1.9)
            if (pos[0] - px) ** 2 + (pos[1] - py) ** 2 <= radius * radius:
                return planet
        return None

    def select(self, planet) -> None:
        self.selected = planet
        self._build_panel()
        audio.play("click")

    def deselect(self) -> None:
        if self.selected:
            self.selected = None
            self._build_panel()
            audio.play("back")

    def _panel_rect(self) -> pygame.Rect:
        return pygame.Rect(884, 120, 372, 552)

    def _build_panel(self) -> None:
        self.detail = self.selected
        self.panel_buttons = []
        panel = self._panel_rect()
        x = panel.x + 34
        width = panel.width - 68
        base_y = panel.bottom - 76

        if self.selected is None:
            return

        name = self.selected["name"]
        part = self.selected.get("part")
        playable = self.selected.get("playable")
        unlock = self.selected.get("unlock") or []

        if playable == "ending":
            title = f"{name} - Finale"
        elif playable:
            title = f"{name} Mission"
        else:
            title = f"{name} - Archive"

        y = panel.y + 300
        text.draw(
            self.screen,
            title,
            (panel.centerx, y),
            24,
            settings.INK,
            display=True,
            center=True,
            max_width=panel.width - 60,
            shadow=False,
        )
        text.draw(
            self.screen,
            self.selected.get("tagline", ""),
            (panel.centerx, y + 34),
            17,
            settings.DIM,
            center=True,
            max_width=panel.width - 60,
            shadow=False,
        )

        # fact block
        fact_y = panel.y + 404
        text.draw(self.screen, "FACT", (x, fact_y - 2), 15, settings.ACCENT, shadow=False)
        text.draw(
            self.screen,
            self.selected.get("source", "NASA"),
            (panel.right - 30, fact_y - 2),
            14,
            settings.FAINT,
            right=True,
            shadow=False,
        )
        text.draw(
            self.screen,
            self.selected["fact"],
            (x, fact_y + 20),
            17,
            settings.INK,
            max_width=panel.width - 48,
            shadow=False,
            line_gap=3,
        )

        # part row
        if part:
            row_y = panel.y + 526
            sprites.draw_part(
                self.screen,
                (x + 12, row_y),
                11,
                settings.ACCENT,
                self.t,
                glow=False,
            )
            text.draw(
                self.screen,
                part,
                (x + 34, row_y),
                16,
                settings.INK,
                max_width=panel.width - 50,
                shadow=False,
            )

        y = panel.bottom - 66
        if playable == "ending":
            if self.state.all_parts():
                self.panel_buttons.append(
                    Button((x, y, width, 46), "Assemble the ship", self._launch_ending)
                )
            else:
                text.draw(
                    self.screen,
                    f"requires {self.state.part_count}/{len(self.state.required_parts())} parts",
                    (panel.centerx, y + 20),
                    15,
                    settings.DIM,
                    center=True,
                    shadow=False,
                )
        elif playable:
            unlocked = self.state.is_unlocked(self.selected)
            owned = self.state.has_part(part) if part else False
            if owned:
                text.draw(
                    self.screen,
                    "part recovered",
                    (panel.centerx, y + 10),
                    14,
                    settings.GREEN,
                    center=True,
                    shadow=False,
                )
            elif unlocked:
                self.panel_buttons.append(
                    Button((x, y, width, 46), f"Launch mission", self._launch_planet)
                )
            else:
                text.draw(
                    self.screen,
                    "mission locked",
                    (panel.centerx, y + 10),
                    14,
                    settings.DIM,
                    center=True,
                    shadow=False,
                )
        else:
            logged = self.state.has_fact(f"{self.selected['id']}_fact")
            self.panel_buttons.append(
                Button(
                    (x, y, width, 46),
                    "View fact again" if logged else "Add fact to log",
                    self._log_archive,
                )
            )

    def _launch_planet(self) -> None:
        self.manager.switch(self.selected["playable"])

    def _launch_ending(self) -> None:
        self.manager.switch(settings.ENDING)

    def _log_archive(self) -> None:
        for key in self.selected.get("facts", []):
            self.state.add_fact(key)
        self.toast = f"{self.selected['name']} fact logged"
        self.toast_timer = 3.0
        self.state.save()
        self._build_panel()

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.switch(settings.MENU)
                    return
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if self.selected and any(not b.enabled for b in []) and False:
                        pass
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                planet = self._find_at(event.pos)
                if planet is not None:
                    self.select(planet)
                    return
                panel = self._panel_rect()
                if panel.collidepoint(event.pos):
                    pass
                else:
                    self.deselect()

        # panel buttons
        for index, button in enumerate(self.panel_buttons):
            if button.handle_events(events):
                return

        # map-level keys
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
            ):
                if self.selected:
                    self._launch_selected()
                return

    def _launch_selected(self) -> None:
        planet = self.selected
        playable = planet.get("playable") if planet else None
        part = planet.get("part") if planet else None
        if not playable:
            return
        if playable == "ending":
            if self.state.all_parts():
                self.manager.switch(settings.ENDING)
            return
        if self.state.has_part(part) if part else False:
            return
        if self.state.is_unlocked(planet):
            self.manager.switch(playable)

    def update(self, dt: float) -> None:
        self.t += dt
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast = ""

    def draw(self, screen: pygame.Surface) -> None:
        self.screen = screen
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        # orbits (skip duplicates)
        seen_orbits = set()
        sun_pos = (settings.WIDTH // 2, settings.HEIGHT // 2 + 16)
        for planet in self.planets:
            orbit = planet["orbit_px"]
            if orbit in seen_orbits:
                continue
            seen_orbits.add(orbit)
            planets.draw_orbit(
                screen,
                sun_pos,
                orbit,
                color=(38, 58, 96),
                dashed=2,
            )

        planets.draw_sun(screen, sun_pos, 44, self.t)

        # hints: pulse arcs toward the nearest playable planet
        for planet in self.planets:
            px, py = planet["_pos"]
            is_playable = bool(planet.get("playable"))
            if is_playable:
                dist = math.hypot(px - settings.WIDTH // 2, py - settings.HEIGHT // 2)
                if dist > 60:
                    angle = math.atan2(py - settings.HEIGHT // 2, px - settings.WIDTH // 2)
                    radius = min(dist - planet["radius"] - 8, 34)
                    anchor_x = settings.WIDTH // 2 + math.cos(angle) * radius
                    anchor_y = settings.HEIGHT // 2 + math.sin(angle) * radius
                    pulse = 0.35 + 0.35 * abs(math.sin(self.t * 2.0 + planet["_seed"] if "_seed" in planet else self.t * 2.0))
                    pygame.draw.line(
                        screen,
                        settings.ACCENT,
                        (settings.WIDTH // 2, settings.HEIGHT // 2),
                        (anchor_x, anchor_y),
                        1,
                    )
                    pygame.draw.circle(
                        screen,
                        settings.ACCENT,
                        (int(anchor_x), int(anchor_y)),
                        int(2 + 2 * pulse),
                    )

        # planets
        hover = self._find_at(self.mouse)
        for planet in self.planets:
            px, py = planet["_pos"]
            color = hex_to_rgb(planet.get("color", "#8fa3c8"))
            if planet == hover:
                draw_ring(screen, px, py, int(planet["radius"]) * 1.9 + 10, settings.ACCENT, self.t)
            planets.draw_planet(
                screen,
                (px, py),
                planet["radius"],
                color,
                band_color=hex_to_rgb(planet.get("band_color", "#5a6b82")),
                bands=planet.get("bands", 0),
                craters=planet.get("craters", 0),
                seed=self._seed_for(planet),
                ring=planet.get("ring", False),
                ring_color=hex_to_rgb(planet.get("ring_color", "#d2c4b4")),
            )
            if self.selected == planet:
                pygame.draw.circle(screen, settings.ACCENT, (px, py), int(planet["radius"]) * 1.55, 2)
                self._draw_hover_tooltip(screen, planet)
            elif planet == hover:
                self._draw_hover_tooltip(screen, planet)

        # status bar top-left
        text.draw(
            screen,
            "SOLAR SYSTEM",
            (20, 18),
            20,
            settings.ACCENT,
            display=True,
            shadow=False,
        )
        text.draw(
            screen,
            f"PARTS {self.state.part_count}/{len(self.state.required_parts())}",
            (20, 44),
            19,
            settings.INK,
            shadow=False,
        )

        # part dots across the top
        x = 210
        for part in self.state.required_parts():
            owned = self.state.has_part(part)
            color = settings.GREEN if owned else settings.FAINT
            sprites.draw_part(screen, (x, 46), 9, color, self.t, glow=False)
            text.draw(screen, part, (x + 20, 38), 14, settings.DIM, max_width=250, shadow=False)
            x += 180

        # menu button
        menu_btn = Button((settings.WIDTH - 300, 16, 284, 44), "Back to menu", self.manager.switch)
        menu_btn.on_click = lambda: self.manager.switch(settings.MENU)
        menu_btn.draw(screen)

        # detail panel
        panel = self._panel_rect()
        pygame.draw.rect(screen, settings.PANEL, panel, border_radius=14)
        pygame.draw.rect(screen, settings.PANEL_EDGE, panel, 1, border_radius=14)
        text.draw(screen, "DETAILS", (panel.x + 18, panel.y + 22), 17, settings.ACCENT, display=True)
        pygame.draw.line(screen, settings.PANEL_EDGE, (panel.x + 18, panel.y + 44), (panel.right - 18, panel.y + 44), 1)

        if self.selected:
            self._draw_selected_detail(screen)
        else:
            text.draw(
                screen,
                "Select a planet to inspect its mission or archive fact.",
                (panel.centerx, panel.centery),
                18,
                settings.DIM,
                center=True,
                shadow=False,
            )

        for button in self.panel_buttons:
            button.draw(screen)

        # toast
        if self.toast:
            label = self.toast
            width = text.measure(label, 18)[0] + 40
            rect = pygame.Rect((settings.WIDTH - width) // 2, settings.HEIGHT - 66, width, 30)
            pygame.draw.rect(screen, (6, 11, 24, 220), rect, border_radius=15)
            pygame.draw.rect(screen, settings.GOLD, rect, 1, border_radius=15)
            text.draw(
                screen,
                label,
                (rect.centerx, rect.centery),
                18,
                settings.INK,
                center=True,
                middle=True,
                shadow=False,
            )

        screen.blit(self.vignette, (0, 0))

    def _draw_selected_detail(self, screen: pygame.Surface) -> None:
        panel = self._panel_rect()
        planet = self.selected
        px, py = planet["_pos"]
        preview_y = panel.y + 96
        preview_radius = min(52, int(planet["radius"]) * 5)
        planets.draw_planet(
            screen,
            (panel.centerx, preview_y),
            preview_radius,
            hex_to_rgb(planet.get("color", "#8fa3c8")),
            band_color=hex_to_rgb(planet.get("band_color", "#5a6b82")),
            bands=planet.get("bands", 0),
            craters=planet.get("craters", 0),
            seed=self._seed_for(planet),
            ring=planet.get("ring", False),
            ring_color=hex_to_rgb(planet.get("ring_color", "#d2c4b4")),
        )

    def _draw_hover_tooltip(self, screen: pygame.Surface, planet) -> None:
        name = planet["name"]
        width = text.measure(name, 16)[0] + 20
        rect = pygame.Rect(
            planet["_pos"][0] - width // 2,
            planet["_pos"][1] - 34,
            width,
            20,
        )
        pygame.draw.rect(screen, settings.PANEL, rect, border_radius=6)
        pygame.draw.rect(screen, settings.PANEL_EDGE, rect, 1, border_radius=6)
        text.draw(screen, name, (rect.centerx, rect.centery), 16, settings.INK, center=True, middle=True, shadow=False)
