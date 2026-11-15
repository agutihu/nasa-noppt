"""Level 1: Living on the Outpost.

Four-phase outpost: Food Challenge → Exercise → Rest → Complete.
Each phase has its own objective, vending machine interaction, and dialogue.
Wrong food choice restarts the game per the deck brief.
"""

from __future__ import annotations

import math
import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from core.game_state import GameState
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.vending import Vending
from ui.modal import Modal
from art import environments, sprites


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_rect(index: int, grid_rect: pygame.Rect) -> pygame.Rect:
    """Return the card rect for an item in a 3-column grid."""
    rows = max(1, math.ceil(grid_rect.width / 200))  # rough
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
    """Draw the astronaut at a fixed position for the outpost scene."""
    cx, cy = pos
    s = 1.0
    f = 1
    bob = math.sin(t * 6.0) * 1.5 * s
    step = math.sin(t * 11.0) * 3.5 * s if True else 0.0
    suit = (232, 238, 248)
    shade = (198, 208, 226)
    stripe = (240, 130, 60)
    dark = (46, 58, 84)

    # jetpack flame (none while grounded)
    # backpack
    pygame.draw.rect(surface, (110, 128, 158),
                     pygame.Rect(int(cx - f * 15 * s - 5 * s), int(cy - 8 * s + bob), int(11 * s), int(16 * s)),
                     border_radius=max(1, int(3 * s)))
    # legs
    ground = cy + 17 * s
    for index in (-1, 1):
        swing = step * index if True else index * 1.2 * s
        leg_h = 9 * s + abs(swing) * 0.2
        hip_x = cx + index * 4 * s
        leg = pygame.Rect(int(hip_x - 3 * s + swing * 0.4), int(ground - leg_h), int(6 * s), int(leg_h))
        pygame.draw.rect(surface, shade, leg, border_radius=max(1, int(2 * s)))
        boot = pygame.Rect(leg.x - int(1 * s), ground - int(3 * s), leg.width + int(3 * s), int(3 * s))
        pygame.draw.rect(surface, dark, boot, border_radius=max(1, int(1 * s)))

    # torso
    torso = pygame.Rect(int(cx - 9 * s), int(cy - 7 * s + bob), int(18 * s), int(17 * s))
    pygame.draw.rect(surface, suit, torso, border_radius=max(2, int(5 * s)))
    pygame.draw.rect(surface, stripe,
                     pygame.Rect(torso.x, torso.y + int(7 * s), torso.width, int(3 * s)),
                     border_radius=max(1, int(1 * s)))
    pygame.draw.circle(surface, settings.ACCENT, (int(cx - f * 4 * s), int(cy - 2 * s + bob)), max(1, int(2 * s)))

    # helmet + visor
    helmet_y = cy - 13 * s + bob
    pygame.draw.circle(surface, suit, (int(cx), int(helmet_y)), int(10 * s))
    pygame.draw.circle(surface, (150, 162, 186), (int(cx), int(helmet_y)), int(10 * s), max(1, int(1.4 * s)))
    visor = pygame.Rect(int(cx - 6 * s + f * 2 * s), int(helmet_y - 5 * s), int(11 * s), int(8 * s))
    pygame.draw.rect(surface, (24, 34, 56), visor, border_radius=max(1, int(3 * s)))
    pygame.draw.rect(surface, (64, 140, 190), visor, max(1, int(1 * s)), border_radius=max(1, int(3 * s)))
    glint_x = visor.x + int(3 * s) + (2 * s if f > 0 else 0)
    pygame.draw.circle(surface, (140, 220, 255), (int(glint_x), int(helmet_y - 3 * s + bob)), max(1, int(1.5 * s)))


# ---------------------------------------------------------------------------
# Level 1 Scene
# ---------------------------------------------------------------------------

class Level1Scene(Scene):
    name = settings.LEVEL1
    counts_time = True

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("level1")
        self.params = levels.params_for(self.cfg, self.state.difficulty)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.meta = levels.level_meta("outpost")  # just for name
        self.hud = HUD(self.state, level_name=self.cfg["name"], accent=settings.ACCENT)
        self.dlg = DialogueBox(self.game)
        self.modal: Modal | None = None
        self.vending: Vending | None = None
        self.t = 0.0
        self.phase = "intro"
        self.phase_start = 0.0
        self.level_time = 0.0
        self.food_wrong_confirmed = False
        self.crumbs_cleaned = 0
        self.crumbs_total = 14

        # outpost background
        self.backdrop = environments.outpost_room(settings.WIDTH, settings.HEIGHT)

        # player / laika
        self.player_pos = pygame.Vector2(self.params["player_start"])
        self.laika_offset = pygame.Vector2(-60, -40)

        # vending machine rect for hit area
        self.vending_rect = pygame.Rect(96, 196, 112, 168)  # left wall machine

        # three rest bays at bottom
        bay_w = 150
        bay_h = 140
        gap = 20
        self.rest_bays = []
        for i, label in enumerate(["Control area", "Exercise area", "Resting stations"]):
            x = 300 + i * (bay_w + gap)
            self.rest_bays.append({
                "rect": pygame.Rect(x, settings.HEIGHT - bay_h - 32, bay_w, bay_h),
                "label": label,
                "bad": label in ("Control area", "Exercise area"),
                "reason": "CO₂ accumulation risk.",
            })

        # bike interact point
        self.bike_rect = pygame.Rect(980, 280, 100, 60)

        # table for eating
        self.table_rect = pygame.Rect(360, 280, 80, 80)

        # objectives
        self.objective = ""

        # start timer
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
        self.food_wrong_confirmed = False
        self.crumbs_cleaned = 0
        # ensure Laika portrait sync
        self.dlg.clear()

        # special: food wrong → modal + restart
        if phase == "food_wrong":
            self._show_food_wrong()
            return

        # special: food correct → proceed to eat
        if phase == "food_correct":
            self._phase_food_correct()
            return

        # special: last phase
        if phase == "complete":
            self._phase_complete()
            return

        # reset per-phase state
        if hasattr(self, "_phase_") and hasattr(self, "_phase_" + phase):
            getattr(self, "_phase_" + phase + "_init")()

        # set objective from phase config
        phase_cfg = next((p for p in self.cfg["phases"] if p["id"] == phase), None)
        if phase_cfg:
            self.objective = phase_cfg.get("objective", "")
            # trigger dialogue
            trig = phase_cfg.get("dialogue_trigger")
            if trig:
                self._say(trig)

    def _phase_intro_init(self) -> None:
        pass

    def _phase_food_briefing_init(self) -> None:
        # show safety briefing modal; proceed button opens vending
        from ui.modal import Modal as M
        self.modal = Modal(
            "SAFETY BRIEFING",
            "No open liquids: in microgravity, a spilled drink floats and can reach the panels, vents, and the outpost's most sensitive circuits.\n\n"
            "No crumbly food: crumbs float into the ventilation grilles and circuit boards.\n\n"
            "Select two items from the vending machine. Correct: sealed drink + irradiated chicken.\n\n"
            "Press Confirm when you have chosen.",
            buttons=[("Proceed", None, "primary")],
            width=660,
        )
        self.modal._height = 320
        self.modal.rect.height = 320
        self.modal.buttons[0].focused = True

    def _phase_food_correct(self) -> None:
        # add items to inventory, proceed to eat phase
        # the vending was already confirmed with correct pair; just advance
        self._say("food_correct")
        # advance to the eating phase once the choice is confirmed
        self._goto_phase("food_eat")

    def _phase_food_eat_init(self) -> None:
        pass

    def _phase_clean_crumbs_init(self) -> None:
        self.crumbs_cleaned = 0

    def _phase_exercise_intro_init(self) -> None:
        pass

    def _phase_vending_code_init(self) -> None:
        pass

    def _phase_bike_ready_init(self) -> None:
        pass

    def _phase_rest_intro_init(self) -> None:
        pass

    def _phase_complete_init(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Dialogue
    # ------------------------------------------------------------------

    def _say(self, trigger: str, speaker: str | None = None) -> None:
        lines = self.dialogue["lines"].get(trigger, [])
        if not lines:
            # trigger not found; advance anyway
            if self.dlg.is_active():
                self.dlg.advance()
            return
        self.dlg.queue(lines, speaker=speaker, on_done=self._on_dialogue_done)

    def _on_dialogue_done(self) -> None:
        # simple advance logic: if last line, go to next phase or stay
        if self.dlg.index + 1 < len(self.dlg.lines):
            self.dlg.index += 1
            self.dlg.revealed = 0.0
        else:
            self.dlg.clear()
            # check if we have a scheduled next phase
            pass

    def _schedule_next(self, phase: str, delay: float) -> None:
        # we'll switch in the update loop after delay seconds
        self._next_phase = phase
        self._next_phase_time = self.state.elapsed + delay

    # ------------------------------------------------------------------
    # Food challenge handling
    # ------------------------------------------------------------------

    def _lose_mission(self) -> None:
        """Laika is lost - the mission failed (e.g. running freely in microgravity)."""
        audio.play("boom")
        self.state.finish_mission("lost")
        self.manager.switch(settings.LEVEL1)  # fresh start

    def _show_food_wrong(self) -> None:
        """Show the protocol violated modal and restart the mission."""

        self.modal = Modal(
            "FOOD SAFETY PROTOCOL VIOLATED",
            "Open liquids and crumbly food damage the outpost's sensitive circuits and ventilation grilles.\n\n"
            "The mission will restart. Choose sealed drinks and irradiated chicken.",
            buttons=[
                ("Restart mission", self._lose_mission, "danger"),
                ("Back to menu", lambda: self.manager.switch(settings.MENU), "ghost"),
            ],
            width=660,
        )

    def _handle_vendor_confirm(self, payload: dict) -> None:
        """Called by Vending.on_footer. payload.items are the selected item ids."""
        selected = payload.get("items", [])
        # We require exactly 2 items for food challenge
        if len(selected) != 2:
            self.hud.toast("Select exactly two items.")
            audio.play("deny")
            return

        # Identify correct vs wrong
        correct_ids = {"sealed_drink", "irradiated_chicken"}
        wrong_ids = {"soda_can", "cookie"}
        chosen = set(selected)

        if chosen == {"sealed_drink", "irradiated_chicken"}:
            # Correct!
            audio.play("confirm")
            self._goto_phase("food_correct")
        elif chosen.isdisjoint(correct_ids):
            # Both wrong (soda + cookie)
            audio.play("deny")
            self._goto_phase("food_wrong")
        elif chosen.intersection(wrong_ids) and chosen.intersection(correct_ids):
            # One wrong, one correct — still wrong per challenge rules
            audio.play("deny")
            self._goto_phase("food_wrong")
        else:
            # Shouldn't happen, but safe fallback
            audio.play("deny")
            self.hud.toast("That combination is not allowed.")

    # ------------------------------------------------------------------
    # Phase logic
    # ------------------------------------------------------------------

    # -- intro --
    def _handle_intro(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        # move toward Laika / table
        if self.player_pos.distance_to(pygame.Vector2(400, 300)) > 30:
            direction = (pygame.Vector2(400, 300) - self.player_pos).normalize() * 120 * dt
            self.player_pos += direction
        # talk to Laika when close
        if self.player_pos.distance_to(pygame.Vector2(400, 300)) < 50 and not self.dlg.is_active():
            self._say("intro")

        # transition to food_briefing after dialogue
        if not self.dlg.is_active() and self.dlg.lines == []:
            self._goto_phase("food_briefing")

    # -- food_briefing --
    def _handle_food_briefing(self, dt: float) -> None:
        self.t += dt
        # handle modal input
        if self.modal:
            handled = self.modal.handle_events(pygame.event.get())
            if self.modal.buttons and self.modal.focus >= 0:
                self.modal.buttons[self.modal.focus].draw(self.screen)  # drawn elsewhere
            if self.modal.handle_events(pygame.event.get()) == "activate":
                # proceed
                self.modal = None
                self._goto_phase("vending_code")
            return

        # if dialogue active, let it play
        if self.dlg.is_active():
            self.dlg.update(dt)
            return

        # otherwise, show briefing text and wait for space/enter
        # (handled by modal above; if modal not yet created, create it)
        if not self.modal:
            self.modal = Modal(
                "SAFETY BRIEFING",
                "No open liquids: in microgravity, a spilled drink floats and can reach the panels, vents, and the outpost's most sensitive circuits.\n\n"
                "No crumbly food: crumbs float into the ventilation grilles and circuit boards.\n\n"
                "Select two items from the vending machine. Correct: sealed drink + irradiated chicken.\n\n"
                "Press Confirm when you have chosen.",
                buttons=[("Proceed", None, "primary")],
                width=660,
            )

    # -- vending_code --
    def _handle_vending_code(self, dt: float) -> None:
        self.t += dt
        # build vending machine
        items = self.cfg["phases"][3]["vending"]["items"]  # code mode items
        if not self.vending:
            self.vending = Vending(
                self.game,
                items,
                title="SAFETY HARNESS",
                subtitle="Enter the code for the safety harness.",
                footer="CONFIRM",
                max_select=1,
                code_mode=True,
            )
            self.vending.set_labels({it["id"]: str(index + 1) for index, it in enumerate(items)})

        ev = self.vending.handle_events(pygame.event.get())
        if ev == {"action": "select", "item": str}:
            # show which was selected via toast
            self.hud.toast(f"Selected: {self.vending.items[self.vending.focus]['name']}")
        elif ev == {"action": "footer"}:
            self._handle_vendor_confirm(self.vending._confirm_payload if hasattr(self.vending, '_confirm_payload') else {})
            self.vending = None
            self._goto_phase("bike_ready")
        elif ev == {"action": "close"}:
            self.vending = None

        # draw vending over everything
        if self.vending:
            self.vending.draw(self.screen)

    # -- bike_ready --
    def _handle_bike_ready(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        # show modal with two choices
        if not self.dlg.is_active():
            if not self.modal:
                self.modal = Modal(
                    "BIKE READY",
                    "The bicycle is ready. Would you like to strap in and ride, or run freely?",
                    buttons=[
                        ("Strap in and ride", lambda: self._goto_phase("bike"), "primary"),
                        ("Run freely", self._lose_mission, "ghost"),
                    ],
                    width=500,
                )
            self.modal.draw(self.screen)
            # handle button activation via keyboard
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1 or event.key == pygame.K_2:
                        # map 1/2 to buttons
                        idx = 0 if event.key == pygame.K_1 else 1
                        self.modal.buttons[idx].activate()
            return

    # -- bike QTE --
    def _handle_bike(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        # QTE: alternating left/right adds progress; same key twice reduces gain
        # We'll use simple timer: 22s total, need to press alternating keys
        # For simplicity: if player presses alternate keys, timer advances; else no progress
        # Actually, let's just track time and if 22s elapses, success
        if self.t - self.phase_start >= 22.0:
            # Strapped-in ride completed; Laika must now rest.
            self._goto_phase("rest_intro")
            return

        # simple visual: show a pulse that fills; player presses any key to keep going
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and not self.dlg.is_active():
                # just advance time a bit
                pass

    # -- rest_intro --
    def _handle_rest_intro(self, dt: float) -> None:
        self.t += dt
        if not self.dlg.is_active():
            # show Laika's question
            self._say("rest_intro")
            # after dialogue, show choice modal
            if not self.modal:
                self.modal = Modal(
                    "WHERE SHOULD LAIKA SLEEP?",
                    "Laika will ask the player where he want to sleep, offering three options:\n\n"
                    "Control area.\n"
                    "Exercise area.\n"
                    "Resting stations.\n\n"
                    "If the player chooses the wrong location, Laika will receive a CO₂ accumulation warning.",
                    buttons=[
                        ("Control area", lambda: self._choose_rest("control"), "ghost"),
                        ("Exercise area", lambda: self._choose_rest("exercise"), "ghost"),
                        ("Resting stations", lambda: self._choose_rest("resting"), "primary"),
                    ],
                    width=560,
                )
            self.modal.draw(self.screen)
            # handle button clicks
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # modal handles its own clicks; just in case
                    pass
        else:
            self.dlg.update(dt)

    def _choose_rest(self, choice: str) -> None:
        # find the bay matching choice
        for bay in self.rest_bays:
            if choice in bay["label"] or choice == bay["label"].split()[0].lower():
                self.modal = None
                if bay["bad"]:
                    # Wrong location: CO2 accumulation risk. Warn, then the level completes.
                    self._say(bay["reason"])
                # Either way the rest sequence resolves and the level advances.
                self._goto_phase("complete")
                return
        # fallback
        self.modal = None

    # -- clean_crumbs --
    def _handle_clean_crumbs(self, dt: float) -> None:
        self.t += dt
        # vacuum cleaner proximity interaction
        # If player presses E near the vacuum rect, increment counter
        keys = pygame.key.get_pressed()
        if keys[pygame.K_e] and not self.dlg.is_active():
            # check if near vacuum
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            # virtual coordinate (assuming 1280x720, no scaling in this scene)
            if self.vacuum_rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])):
                self.crumbs_cleaned += 1
                self.hud.toast(f"Crumb cleaned ({self.crumbs_cleaned}/{self.crumbs_total})")
                audio.play("vacuum", 0.4)
        if self.crumbs_cleaned >= self.crumbs_total:
            self._say("clean_crumbs_done")
            self._schedule_next("exercise_intro", 2.0)

    # -- complete --
    def _handle_complete(self, dt: float) -> None:
        self.t += dt
        if self.t - self.phase_start >= 5.0:
            self.state.mark_level_done("outpost", self.level_time)
            self.manager.switch(settings.BRIEFING, level_id="outpost")  # go to next level briefing

    # ------------------------------------------------------------------
    # General loop
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.game.quit()
            # let dialogue and modal eat events first
            if self.dlg.is_active():
                self.dlg.handle_events(events)
                return
            if self.modal and self.modal.is_active():
                self.modal.handle_events(events)
                return
            # key escapes
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

        # handle phase-specific logic
        if self.phase == "intro":
            self._handle_intro(dt)
        elif self.phase == "food_briefing":
            self._handle_food_briefing(dt)
        elif self.phase == "vending_code":
            self._handle_vending_code(dt)
        elif self.phase == "bike_ready":
            self._handle_bike_ready(dt)
        elif self.phase == "bike":
            self._handle_bike(dt)
        elif self.phase == "rest_intro":
            self._handle_rest_intro(dt)
        elif self.phase == "clean_crumbs":
            self._handle_clean_crumbs(dt)
        elif self.phase == "complete":
            self._handle_complete(dt)

        # update HUD
        self.hud.update(dt)

        # update dialogue
        if self.dlg.is_active():
            self.dlg.update(dt)

        # update modal if open
        if self.modal:
            self.modal.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.backdrop, (0, 0))

        # draw astronaut
        _draw_astronaut_at(surface, (640, 380), self.t)

        # draw laika portrait small
        # (the dialogue box handles its own portrait)

        # draw HUD
        self.hud.draw(surface)

        # draw dialogue
        if self.dlg.is_active():
            self.dlg.draw(surface)

        # draw modal if open
        if self.modal:
            self.modal.draw(surface)

        # draw vending if active (drawn on top in _handle_vending_code already,
        # but we also need it here if not fully taken over)
        # Actually vending draws itself in its handler; skip here to avoid double-draw

        # draw rest bay highlights
        for bay in self.rest_bays:
            color = settings.WARN if bay["bad"] else settings.GREEN
            pygame.draw.rect(surface, color, bay["rect"], 4, border_radius=10)
            text.draw(surface, bay["label"], (bay["rect"].centerx, bay["rect"].top - 10),
                     14, color, display=True, center=True)

        # draw bike interact
        pygame.draw.rect(surface, settings.ACCENT, self.bike_rect, 3, border_radius=8)
        text.draw(surface, "E: Exercise", (self.bike_rect.centerx, self.bike_rect.top - 10),
                 14, settings.ACCENT, display=True, center=True)

        # draw table for eating
        pygame.draw.rect(surface, (60, 96, 120), self.table_rect, border_radius=8)
        text.draw(surface, "TABLE", (self.table_rect.centerx, self.table_rect.centery),
                 16, settings.DIM, display=True, center=True)

        # draw objective banner
        if self.objective:
            text.draw(surface, f"OBJECTIVE: {self.objective}",
                     (settings.WIDTH // 2, 60), 20, settings.INK, display=True, center=True)


# ---------------------------------------------------------------------------
# Boot/menu changes to register the new scene
# ---------------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    """Register the new mission scenes with the scene manager."""
    from scenes.level1 import Level1Scene
    from scenes.briefing import BriefingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.BRIEFING, BriefingScene)