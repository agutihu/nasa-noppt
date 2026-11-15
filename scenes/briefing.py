"""Briefing scene shown between levels, with level intro and Laika dialogue.

Displays the level title, a brief objective, and Laika's greeting.
The player presses any key or space to continue to the next level.
"""

from __future__ import annotations

import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from art import environments
from ui.dialogue_box import DialogueBox

_MISSION_TO_LEVEL = {
    "outpost": "level2",
    "landing": "level3",
    "surface": "level4",
    "tunnel": "ending",
}

class BriefingScene(Scene):
    name = settings.BRIEFING
    counts_time = False

    def __init__(self, game) -> None:
        # Store the game reference so we can access the real manager later.
        self.game = game
        # Minimal placeholders so Scene.__init__ doesn't crash;
        # we set self.manager properly in on_enter().
        self.screen = pygame.Surface((1, 1))
        self.state = None
        self.manager = None
        self.level_id = "outpost"
        self.dlg = DialogueBox(self)
        self.t = 0.0
        self.continue_key = False

    def on_enter(self, **data) -> None:
        self.t = 0.0
        self.continue_key = False
        # level_id may come from switch(level_id="outpost") or default
        level_id = data.get("level_id", self.level_id)
        actual_level_id = _MISSION_TO_LEVEL.get(level_id, level_id)
        # load the level config to get name and blurb
        self.cfg = levels.load_level(actual_level_id)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.hud = None  # not needed for briefing

        # show Laika's intro line
        lines = self.dialogue["lines"].get("start", [])
        if lines:
            self.dlg.queue(lines, on_done=self._start_done)
        else:
            self._start_done()

        # Set the manager reference so update() can switch scenes.
        # The test's game object is stored as self.game.
        if self.game and hasattr(self.game, "manager"):
            self.manager = self.game.manager
        elif self.stack and self.stack[-1] and hasattr(self.stack[-1], "manager") and self.stack[-1].manager:
            self.manager = self.stack[-1].manager

    def _start_done(self) -> None:
        self.continue_key = True
        audio.play("click")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.continue_key = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.continue_key = True

    def update(self, dt: float) -> None:
        self.t += dt
        if self.continue_key:
            audio.play("click")
            # Determine the next level based on sequential unlock.
            # Use the mission-to-level mapping so we switch to level file names
            # (e.g. 'outpost' -> 'level1') rather than mission IDs ('landing').
            next_level = _MISSION_TO_LEVEL.get(self.level_id, self.level_id)
            if next_level != self.level_id and next_level in settings.PLAYABLE_SCENES:
                self.manager.switch(next_level)
            else:
                # Fallback: advance to the next mission ID
                order = list(settings.LEVEL_IDS)
                if self.level_id in order:
                    idx = order.index(self.level_id)
                    next_idx = idx + 1
                    if next_idx < len(order):
                        self.manager.switch(settings.LEVEL_IDS[next_idx])
                    else:
                        if hasattr(self.state, "finish_mission") and self.state.outcome is None:
                            self.state.finish_mission("win")
                        self.manager.switch(settings.ENDING)
                else:
                    self.manager.switch(settings.LEVEL1)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(environments.outpost_room(settings.WIDTH, settings.HEIGHT), (0, 0))
        # dim overlay
        overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        text.draw(
            surface,
            self.cfg["name"].upper(),
            (settings.WIDTH // 2, 180),
            30,
            settings.ACCENT,
            display=True,
            center=True,
        )
        text.draw(
            surface,
            self.cfg.get("blurb", ""),
            (settings.WIDTH // 2, 260),
            20,
            settings.DIM,
            display=True,
            center=True,
            max_width=600,
        )

        text.draw(
            surface,
            "Press any key or SPACE to continue",
            (settings.WIDTH // 2, settings.HEIGHT - 100),
            18,
            settings.FAINT,
            display=True,
            center=True,
        )

        if self.dlg.is_active():
            self.dlg.draw(surface)


# ---------------------------------------------------------------------------
# Main scene registration
# ---------------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    """Register the new mission scenes with the scene manager."""
    from scenes.level1 import Level1Scene
    from scenes.level2 import Level2Scene
    from scenes.level3 import Level3Scene
    from scenes.level4 import Level4Scene
    from scenes.ending import EndingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.LEVEL2, Level2Scene)
    manager.register(settings.LEVEL3, Level3Scene)
    manager.register(settings.LEVEL4, Level4Scene)
    manager.register(settings.BRIEFING, BriefingScene)
