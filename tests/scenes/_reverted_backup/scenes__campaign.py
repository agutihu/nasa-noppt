"""Shared machinery for the four campaign levels.

Every campaign level is a sequence of phases declared in ``data/levels/<id>.json``.
The plumbing that all four levels need - phase switching, the ``update`` dispatcher,
timers, dialogue handling and the "advance once the dialogue clears" rule - lives here
so a level file only has to contain its own game-specific logic.

Why this module exists: the four levels used to each carry their own copy of that
plumbing, and the copies drifted. Three of them never transitioned out of their
``intro`` phase, so the campaign could not be finished. One implementation plus a
strict dispatcher - a phase without a handler is a hard error, not a silent stall -
removes that whole class of bug.
"""

from __future__ import annotations

import math

import pygame

from core import audio, levels, settings
from core.scene import Scene
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.modal import Modal
from ui.vending import Vending


class CampaignScene(Scene):
    """Base class for Level 1 - Level 4.

    Subclasses must:

    * define ``phase_handlers`` - a mapping of phase id to handler method name;
    * implement ``draw(self, surface)``;
    * call ``self._init_campaign(level_id)`` from ``on_enter``.
    """

    #: phase id -> handler method name. A phase without an entry is an error.
    phase_handlers: dict[str, str] = {}

    #: How close the player has to be to interact with a world object.
    INTERACT_RADIUS = 78.0

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _init_campaign(self, level_id: str) -> None:
        """Load the level config and set up the shared campaign state."""
        self.cfg = levels.load_level(level_id)
        self.params = levels.params_for(self.cfg, self.state.difficulty)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.hud = HUD(self.state, level_name=self.cfg["name"], accent=settings.ACCENT)
        self.dlg = DialogueBox(self.game)
        self.modal: Modal | None = None
        self.vending: Vending | None = None

        self.t = 0.0
        self.phase = "intro"
        self.objective = ""
        self.level_time = 0.0
        self.level_start = self.state.elapsed
        self.phase_start = self.state.elapsed

        self._next_phase: str | None = None
        self._next_phase_time = 0.0
        self.vending_event: dict | None = None
        self._phase_ids = [str(entry.get("id")) for entry in self.cfg.get("phases", [])]

    # ------------------------------------------------------------------
    # Phase configuration
    # ------------------------------------------------------------------

    def _phase_config(self, phase: str | None = None) -> dict:
        """The JSON block describing ``phase`` (empty dict when unknown)."""
        phase_id = phase or self.phase
        for entry in self.cfg.get("phases", []):
            if entry.get("id") == phase_id:
                return entry
        return {}

    def _phase_elapsed(self) -> float:
        """Seconds spent in the current phase."""
        return max(0.0, self.state.elapsed - self.phase_start)

    def _phase_limit(self, phase: str | None = None) -> float | None:
        """Time limit for a phase in seconds, scaled by difficulty.

        Returns ``None`` when the phase has no limit. Every gameplay number comes
        from ``data/levels/*.json`` - never from a literal in a scene.
        """
        limit = self._phase_config(phase).get("time_limit")
        if limit is None:
            return None
        return float(limit) * self._time_scale()

    def _time_scale(self) -> float:
        """Difficulty multiplier for every phase timer (easy is generous)."""
        order = list(settings.DIFFICULTIES)
        index = order.index(self.state.difficulty) if self.state.difficulty in order else 1
        return {"easy": 1.25, "normal": 1.0, "hard": 0.85}[order[index]]

    def _phase_trigger(self, phase: str | None = None) -> str | None:
        """The dialogue trigger configured for a phase."""
        trigger = self._phase_config(phase).get("dialogue_trigger")
        return str(trigger) if trigger else None

    # ------------------------------------------------------------------
    # Phase switching
    # ------------------------------------------------------------------

    def _goto_phase(self, phase: str, **data) -> None:
        """Switch to ``phase``.

        The phase id is validated against the JSON config, per-phase state is
        cleared, the objective is applied and the phase dialogue is fired.
        """
        if self._phase_ids and phase not in self._phase_ids:
            raise KeyError(
                f"{type(self).__name__}: unknown phase {phase!r} "
                f"(known phases: {self._phase_ids})"
            )

        self.phase = phase
        self.phase_start = self.state.elapsed
        self.objective = ""
        self.modal = None
        self.vending = None
        self._next_phase = None
        self._next_phase_time = 0.0

        self._reset_phase_state()

        config = self._phase_config(phase)
        self.objective = config.get("objective", "")
        self._on_phase_enter(phase, config)

        trigger = config.get("dialogue_trigger")
        if trigger:
            self._say(str(trigger))

    def _reset_phase_state(self) -> None:
        """Per-level hook: drop anything that must not survive a phase change."""

    def _on_phase_enter(self, phase: str, config: dict) -> None:
        """Per-level hook: react to a phase starting (timers, baselines, banners)."""

    def _schedule_next(self, phase: str, delay: float) -> None:
        """Advance to ``phase`` after ``delay`` seconds. Consumed by ``update``."""
        self._next_phase = phase
        self._next_phase_time = self.state.elapsed + delay

    def _cancel_scheduled(self) -> None:
        self._next_phase = None
        self._next_phase_time = 0.0

    def _advance_when_dialogue_clears(self, phase: str) -> bool:
        """Switch to ``phase`` once the current dialogue has finished.

        Returns ``True`` when the switch happened. A phase whose dialogue trigger
        has no lines in the JSON file advances immediately, which keeps a missing
        dialogue from stalling the level.
        """
        if self.dlg.is_active() or self.dlg.lines:
            return False
        self._goto_phase(phase)
        return True

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
    # Failure
    # ------------------------------------------------------------------

    def _lose_mission(self, scene_name: str | None = None) -> None:
        """The mission failed - record the loss and restart this level."""
        audio.play("boom")
        self.state.finish_mission("lost")
        self.manager.switch(scene_name or self.name)

    # ------------------------------------------------------------------
    # Movement helpers
    # ------------------------------------------------------------------

    def _move_speed(self) -> float:
        """Horizontal move speed in px/s, scaled by difficulty."""
        return self.state.scale_speed(float(self.params.get("move_speed") or 250))

    def _read_direction(self) -> pygame.Vector2:
        """Normalised movement direction from WASD / arrow keys."""
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0.0, 0.0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1.0
        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    def _apply_movement(self, dt: float, *, speed_scale: float = 1.0) -> float:
        """Move the player from the keyboard. Returns the distance travelled."""
        direction = self._read_direction()
        if direction.length_squared() == 0:
            return 0.0
        step = direction * (self._move_speed() * speed_scale * dt)
        self.player_pos += step
        self._clamp_player()
        return step.length()

    def _clamp_player(self) -> None:
        """Keep the player inside the play area."""
        margin = 28.0
        self.player_pos.x = max(margin, min(settings.WIDTH - margin, self.player_pos.x))
        self.player_pos.y = max(margin, min(settings.HEIGHT - margin, self.player_pos.y))

    def _near(self, target: pygame.Rect | tuple[float, float], radius: float | None = None) -> bool:
        """True when the player is within ``radius`` of a rect centre or a point."""
        if isinstance(target, pygame.Rect):
            point = target.center
        else:
            point = target
        limit = self.INTERACT_RADIUS if radius is None else radius
        return self.player_pos.distance_to(pygame.Vector2(point)) <= limit

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.t += dt
        self.level_time = max(0.0, self.state.elapsed - self.level_start)

        if self._next_phase is not None and self.state.elapsed >= self._next_phase_time:
            upcoming = self._next_phase
            self._cancel_scheduled()
            self._goto_phase(upcoming)

        handler_name = self.phase_handlers.get(self.phase)
        if handler_name is None:
            raise KeyError(
                f"{type(self).__name__}: phase {self.phase!r} has no handler "
                f"(known phases: {sorted(self.phase_handlers)})"
            )
        getattr(self, handler_name)(dt)

        self.hud.update(dt)
        if self.dlg.is_active():
            self.dlg.update(dt)
        if self.modal:
            self.modal.update(dt)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Route events to whatever is on top: dialogue, modal, vending, keys.

        Events must be handled here and never pulled from ``pygame.event.get()``
        inside a handler - the main loop already drained the queue, so a handler
        that polls the queue never sees a single event.
        """
        for event in events:
            if event.type == pygame.QUIT:
                self.game.quit()
                return

        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return

        if self.modal is not None:
            if self.modal.is_active():
                self._handle_modal_events(events)
                self.modal.handle_events(events)
                return
            self.modal = None

        if self.vending is not None:
            self.vending_event = self.vending.handle_events(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.push(settings.PAUSE, parent=self)
                return

        self._handle_extra_events(events)

    def _handle_modal_events(self, events: list[pygame.event.Event]) -> None:
        """Per-level hook for events while a modal is open."""

    def _handle_extra_events(self, events: list[pygame.event.Event]) -> None:
        """Per-level hook for events the shared handler does not consume."""

    # ------------------------------------------------------------------
    # Vending machine
    # ------------------------------------------------------------------

    def _open_vending(self, phase_id: str) -> Vending:
        """Open the vending machine configured for ``phase_id``.

        The widget only reports what the player did - the rules live in the
        scene, in ``_on_vending_confirm``.
        """
        spec = self._phase_config(phase_id).get("vending") or {}
        items = list(spec.get("items") or [])
        mode = str(spec.get("mode", "cart"))
        self.vending = Vending(
            self.game,
            items,
            title=str(spec.get("title", "VENDING MACHINE")),
            subtitle=str(spec.get("subtitle", "")),
            footer=str(spec.get("footer", "SELECT")),
            max_select=int(spec.get("max_select", 1)),
            code_mode=bool(spec.get("code_mode", False)) or mode == "code",
        )
        self.vending.on_footer = self._on_vending_confirm
        self.vending.show()
        return self.vending

    def _on_vending_confirm(self, payload: dict) -> None:
        """Called when the player confirms a vending selection."""


def circle_overlaps_rect(circle: tuple[float, float, float], rect: pygame.Rect) -> bool:
    """True when a circle overlaps a rectangle (used to keep markers reachable)."""
    cx, cy, radius = circle
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    return math.hypot(cx - closest_x, cy - closest_y) <= radius
