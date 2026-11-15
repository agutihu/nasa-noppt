"""Finale: show win/lost/incomplete outcome with Laika return animation and stats screen."""

from __future__ import annotations

import math
import pygame

from core import audio, settings, text
from core.scene import Scene
from ui.button import Button
from ui.dialogue_box import DialogueBox

def _fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


# Color helpers (from core.color)
def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b)."""
    return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class EndingScene(Scene):
    name = settings.ENDING
    counts_time = False

    def on_enter(self, **data) -> None:
        self.state = data.get("state")  # passed from main.py
        self.outcome: str | None = getattr(self.state, "outcome", None) or data.get("outcome")

        # Determine outcome if not already set
        if not self.outcome:
            # Check if all levels are done
            if self.state and self.state.level_count >= len(settings.LEVEL_IDS):
                # All levels completed → win
                self.outcome = "win"
            elif getattr(self.state, "deaths", 0) > 0 and self.state.level_count < len(settings.LEVEL_IDS):
                # Some losses but not all levels → incomplete (Laika returns unfinished)
                self.outcome = "incomplete"
            else:
                # Lost: Laika doesn't return
                self.outcome = "lost"

        # Setup stars/nebula background
        self.stars = None
        self.neb = None
        self.vignette = None
        try:
            from art import backgrounds
            self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
            self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
            self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)
        except Exception:
            pass

        # Intro dialogue
        self.dlg = DialogueBox(self.game)
        self._intro()

        # Stats buttons
        y = settings.HEIGHT - 120
        self.buttons = [
            Button(
                (settings.WIDTH // 2 - 220, y, 200, 52),
                "Fly again",
                self._fly_again,
            ),
            Button(
                (settings.WIDTH // 2 + 20, y, 200, 52),
                "Back to menu",
                self._menu,
                style="ghost",
            ),
        ]

    def _intro(self) -> None:
        lines: list[str] = []
        if self.outcome == "win":
            lines = [
                "Laika completed the mission. She is returning home.",
                "All seven parts are recovered. The ship is whole.",
                "Well done, astronaut.",
            ]
        elif self.outcome == "incomplete":
            lines = [
                "Laika is returning, but the survey is unfinished.",
                "I won't give up, try again before going back to Earth.",
            ]
        elif self.outcome == "lost":
            lines = [
                "Laika did not return.",
                "The mission was a failure.",
            ]
        else:
            lines = [
                "Mission results are in.",
            ]
        self.dlg.queue(lines, on_done=None)

    # --- interaction --------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.switch(settings.MENU)
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    button.handle_events(events)

        if self.dlg.is_active():
            self.dlg.handle_events(events)

    # --- update -------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.dlg.is_active():
            self.dlg.update(dt)

    # --- drawing ------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        # Background
        if self.stars:
            screen.blit(self.stars, (0, 0))
        if self.neb:
            screen.blit(self.neb, (0, 0))
        if self.vignette:
            screen.blit(self.vignette, (0, 0))

        # Outcome message
        center_x = settings.WIDTH // 2

        if self.outcome == "win":
            text.draw(
                screen,
                "MISSION COMPLETE",
                (center_x, 150),
                40,
                settings.ACCENT,
                display=True,
                center=True,
            )
            text.draw(
                screen,
                "Laika is home. The ship is whole. Mission success.",
                (center_x, 212),
                24,
                settings.INK,
                center=True,
                max_width=720,
                shadow=False,
            )
        elif self.outcome == "incomplete":
            text.draw(
                screen,
                "LAIKA RETURNING",
                (center_x, 150),
                40,
                settings.ACCENT,
                display=True,
                center=True,
            )
            text.draw(
                screen,
                "I won't give up, try again before going back to Earth.",
                (center_x, 212),
                24,
                settings.INK,
                center=True,
                max_width=720,
                shadow=False,
            )
        elif self.outcome == "lost":
            text.draw(
                screen,
                "LAIKA DID NOT RETURN",
                (center_x, 150),
                40,
                settings.RED,
                display=True,
                center=True,
            )
            text.draw(
                screen,
                "The whole mission was a failure.",
                (center_x, 212),
                24,
                settings.INK,
                center=True,
                max_width=720,
                shadow=False,
            )
        else:
            text.draw(
                screen,
                "MISSION RESULTS",
                (center_x, 150),
                40,
                settings.DIM,
                display=True,
                center=True,
            )

        # Stats row
        rows = [
            ("Mission time", _fmt_time(getattr(self.state, "elapsed", 0.0))),
            ("Losses", str(getattr(self.state, "deaths", 0))),
            ("Parts recovered", 
             f"{getattr(self.state, 'part_count', 0)}/{max(1, len(getattr(self.state, 'required_parts', [])))})"),
            ("Facts learned", str(getattr(self.state, "fact_count", 0))),
        ]
        y = 300
        for label, value in rows:
            text.draw(screen, label, (settings.WIDTH // 2 - 130, y), 22, settings.DIM)
            text.draw(screen, value, (settings.WIDTH // 2 + 130, y), 22, settings.INK, right=True)
            y += 44

        # Facts preview
        facts = getattr(self.state, "facts", [])
        if facts:
            text.draw(
                screen,
                "Facts: " + ", ".join(facts[:6]),
                (settings.WIDTH // 2, 460),
                17,
                settings.FAINT,
                center=True,
                max_width=760,
                shadow=False,
            )

        # Best times
        best_times = getattr(self.state, "best_times", {})
        if best_times:
            bests = "  ".join(
                f"{label} {_fmt_time(time)}"
                for level_id, time in sorted(best_times.items())
                for label in [settings.LEVEL_IDS[i] if i < len(settings.LEVEL_IDS) else level_id]
                for i in [settings.LEVEL_IDS.index(level_id) if level_id in settings.LEVEL_IDS else -1]
            )
            text.draw(
                screen,
                "Best times: " + bests,
                (settings.WIDTH // 2, 490),
                18,
                settings.DIM,
                center=True,
                max_width=980,
                shadow=False,
            )

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Dialogue box (already drawn by handle_events, but draw it here too if needed)
        if self.dlg.is_active():
            self.dlg.draw(screen)

    # --- actions ------------------------------------------------------------

    def _fly_again(self) -> None:
        # Reset the state for a new mission
        if self.state:
            self.state.reset_mission()
        self.manager.switch(settings.TUTORIAL)

    def _menu(self) -> None:
        self.manager.switch(settings.MENU)