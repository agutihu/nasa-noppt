"""Scene-level campaign + gameplay-rule tests (tutorial, endings, moments,
food management, the 4-level chain, the full campaign walk).

Run from the project root::

    python -m pytest E:\\nasa\\tests\\campaign -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pygame  # noqa: E402

from harness import make_game, run_frames, capture, key, click  # noqa: E402

from core import levels, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402

EXPECTED_PARTS = [
    "Solar Panel Array",
    "Hull Plating",
    "Navigation Module",
    "Shield Generator",
    "Fuel Cells",
    "Thermal Regulator",
    "Signal Antenna",
]


# ---------------------------------------------------------------------------
# 3. tutorial
# ---------------------------------------------------------------------------

def test_tutorial_win_sets_tutorial_done(game):
    """tutorial.py:_finish sets tutorial_done = True."""
    scene = game.manager.switch(settings.TUTORIAL)
    assert game.state.tutorial_done is False
    scene._finish()
    assert game.state.tutorial_done is True


def test_tutorial_win_done_switches_to_the_map(game):
    scene = game.manager.switch(settings.TUTORIAL)
    scene._finish()
    scene._win_done()
    assert game.manager.current_name == settings.MAP


def test_tutorial_unlocks_mercury(game):
    scene = game.manager.switch(settings.TUTORIAL)
    scene._finish()
    assert game.state.is_unlocked("mercury") is True
    assert game.state.is_unlocked(levels.planet_index()["mercury"]) is True


# ---------------------------------------------------------------------------
# 7. the three endings
# ---------------------------------------------------------------------------

def test_ending_reads_the_shared_state(game):
    """AGENTS.md: EndingScene must fall back to self.state (base Scene)."""
    scene = game.manager.switch(settings.ENDING)
    assert scene.state is game.state, "EndingScene did not pick up the shared GameState"


def test_ending_win_branch(game):
    game.state.outcome = "win"
    for part in EXPECTED_PARTS:
        game.state.add_part(part)
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "win"
    run_frames(game, frames=2)
    assert scene.dlg.lines[0]["text"] == "Laika completed the mission. She is returning home."


def test_ending_incomplete_branch(game):
    game.state.outcome = "incomplete"
    game.state.add_part(EXPECTED_PARTS[0])
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "incomplete"
    run_frames(game, frames=2)
    assert (
        "I won't give up, try again before going back to Earth."
        in [line["text"] for line in scene.dlg.lines]
    )


def test_ending_lost_branch(game):
    game.state.outcome = "lost"
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "lost"
    run_frames(game, frames=2)
    assert "Laika did not return." in [line["text"] for line in scene.dlg.lines]


def test_ending_auto_detects_win_from_parts(game):
    """No explicit outcome: all seven parts -> win."""
    for part in EXPECTED_PARTS:
        game.state.add_part(part)
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "win"


def test_ending_auto_detects_incomplete_from_some_parts(game):
    game.state.add_part(EXPECTED_PARTS[0])
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "incomplete"


def test_ending_auto_detects_lost_without_parts(game):
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "lost"


def test_ending_text_is_drawn_per_branch(game):
    """The three headline strings must be reachable in the draw path."""
    expected = {
        "win": "MISSION COMPLETE",
        "incomplete": "LAIKA RETURNING",
        "lost": "LAIKA DID NOT RETURN",
    }
    for outcome, headline in expected.items():
        game.state.outcome = outcome
        scene = game.manager.switch(settings.ENDING)
        drawn = []

        class _Probe:
            def __init__(self, sink):
                self.sink = sink

            def blit(self, *args, **kwargs):
                pass

        # capture text.draw calls
        from core import text as core_text

        original = core_text.draw

        def spy(surface, message, *args, **kwargs):
            drawn.append(message)

        core_text.draw = spy
        try:
            scene.draw(game.manager.screen)
        finally:
            core_text.draw = original
        assert headline in drawn, f"{outcome} did not draw {headline!r} (drew {drawn})"


def test_ending_can_be_reached_from_the_map_only_with_all_parts(game):
    """The map's finale button must stay hidden until all seven parts exist."""
    scene = game.manager.switch(settings.MAP)
    earth = levels.planet_index()["earth"]
    scene.select(earth)
    assert scene.panel_buttons == [], "finale button visible with no parts"
    for part in EXPECTED_PARTS:
        game.state.add_part(part)
    scene = game.manager.switch(settings.MAP)
    scene.select(earth)
    assert len(scene.panel_buttons) == 1, "finale button missing with all parts"


# ---------------------------------------------------------------------------
# 10. the scripted moment in every world
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("planet_id", list(levels.PLANET_ORDER))
def test_every_planet_has_a_moment_in_data(planet_id):
    cfg = levels.load_level(planet_id)
    moment = cfg["params"].get("moment")
    assert moment, f"{planet_id}.json has no params.moment"
    assert "at" in moment and "duration" in moment


@pytest.mark.parametrize("planet_id", list(levels.PLANET_ORDER))
def test_moment_fires_without_crashing(game, planet_id):
    scene = game.manager.switch(planet_id, _test=True)
    assert scene.moment_cfg is not None
    assert scene.moment_fired is False
    # teleport past the trigger point
    scene.player.respawn(scene.moment_x + 10, scene.player.pos.y)
    ok, exc, tb = capture(run_frames, game, frames=10)
    assert ok, f"{planet_id}: {exc}\n{tb}"
    assert scene.moment_fired is True, f"{planet_id}: the signature moment never fired"
    # the set piece spits out reinforcements
    assert len(scene.walkers) + len(scene.ufos) > 0


@pytest.mark.parametrize("planet_id", list(levels.PLANET_ORDER))
def test_moment_never_fires_before_the_trigger(game, planet_id):
    scene = game.manager.switch(planet_id, _test=True)
    scene.player.respawn(max(0, scene.moment_x - 400), scene.player.pos.y)
    ok, exc, tb = capture(run_frames, game, frames=10)
    assert ok, f"{planet_id}: {exc}\n{tb}"
    assert scene.moment_fired is False


# ---------------------------------------------------------------------------
# 9. food management: wrong food restarts, other tasks retry
# ---------------------------------------------------------------------------

def test_wrong_food_restarts_the_mission(game):
    """design.md: wrong food -> 'FOOD SAFETY PROTOCOL VIOLATED' + restart mission."""
    scene = game.manager.switch(settings.LEVEL1)
    scene._handle_vendor_confirm({"items": ["soda_can", "cookie"]})
    assert scene.phase == "food_wrong"
    assert scene.modal is not None
    assert "FOOD SAFETY PROTOCOL VIOLATED" in scene.modal.title
    # the restart button restarts the mission
    scene.modal.buttons[0].activate()
    assert game.state.outcome == "lost"
    assert game.manager.current_name == settings.LEVEL1


def test_correct_food_does_not_restart(game):
    scene = game.manager.switch(settings.LEVEL1)
    scene._handle_vendor_confirm({"items": ["sealed_drink", "irradiated_chicken"]})
    assert scene.phase == "food_eat"
    assert game.state.outcome is None


def test_other_task_failure_retries_the_task(game):
    """design.md: other task failures retry the challenge, not the whole game."""
    scene = game.manager.switch(settings.LEVEL2)
    scene._handle_vendor_confirm_landing({"items": ["toy", "balloon", "disco"]})
    assert scene.phase == "landing_briefing"
    assert game.state.outcome is None, "a wrong equipment pick must not end the mission"


def test_wrong_resting_spot_only_warns(game):
    """playguide: the wrong rest choice warns but does not restart."""
    scene = game.manager.switch(settings.LEVEL1)
    ok, exc, tb = capture(scene._choose_rest, "control")
    assert ok, f"choosing a rest bay crashed the level: {exc}\n{tb}"
    assert scene.phase == "complete"
    assert game.state.outcome is None


# ---------------------------------------------------------------------------
# 11. the 4-level campaign (Outpost -> Landing -> Surface -> Lava Tunnel)
# ---------------------------------------------------------------------------

def test_level1_completion_marks_outpost_done(game):
    scene = game.manager.switch(settings.LEVEL1)
    game.state.elapsed = scene.phase_start + 10.0
    scene.t = scene.phase_start + 10.0
    ok, exc, tb = capture(scene._handle_complete, 0.0)
    assert ok, f"{exc}\n{tb}"
    assert "outpost" in game.state.levels_done


def test_level2_completion_marks_landing_done(game):
    scene = game.manager.switch(settings.LEVEL2)
    game.state.elapsed = scene.phase_start + 10.0
    scene.level_time = 12.0
    ok, exc, tb = capture(scene._handle_complete, 0.0)
    assert ok, f"{exc}\n{tb}"
    assert "landing" in game.state.levels_done


def test_level3_completion_marks_surface_done(game):
    scene = game.manager.switch(settings.LEVEL3)
    game.state.elapsed = scene.phase_start + 10.0
    ok, exc, tb = capture(scene._handle_complete, 0.0)
    assert ok, f"{exc}\n{tb}"
    assert "surface" in game.state.levels_done


def test_level4_completion_marks_tunnel_done_and_wins(game):
    for level_id in ("outpost", "landing", "surface"):
        game.state.mark_level_done(level_id)
    scene = game.manager.switch(settings.LEVEL4)
    game.state.elapsed = scene.phase_start + 10.0
    ok, exc, tb = capture(scene._handle_complete, 0.0)
    assert ok, f"{exc}\n{tb}"
    assert "tunnel" in game.state.levels_done
    assert game.state.outcome == "win"
    assert game.manager.current_name == settings.ENDING


def test_level1_to_level2_chain_works(game):
    """Level 1 -> briefing -> level 2 must actually navigate."""
    scene = game.manager.switch(settings.LEVEL1)
    game.state.elapsed = scene.phase_start + 10.0
    scene.t = scene.phase_start + 10.0
    ok, exc, tb = capture(scene._handle_complete, 0.0)
    assert ok, f"level 1 completion crashed: {exc}\n{tb}"
    assert game.manager.current_name == settings.BRIEFING
    # press a key -> the briefing advances to the next level
    ok, exc, tb = capture(game.manager.handle_events, [key(pygame.K_SPACE)])
    assert ok, f"{exc}\n{tb}"
    ok, exc, tb = capture(game.manager.update, 1 / 60.0)
    assert ok, f"{exc}\n{tb}"
    assert game.manager.current_name == settings.LEVEL2, (
        f"the briefing did not advance to level2 (it went to "
        f"{game.manager.current_name!r})"
    )


def test_briefing_scene_boots(game):
    ok, exc, tb = capture(game.manager.switch, settings.BRIEFING, level_id="outpost")
    assert ok, f"BriefingScene crashed on enter: {exc}\n{tb}"


# ---------------------------------------------------------------------------
# 4. the whole campaign walk
# ---------------------------------------------------------------------------

def _advance_dialogue(scene, limit: int = 30) -> None:
    """Push the dialogue box to the end so queued callbacks (like _win) run."""
    for _ in range(limit):
        if not scene.dlg.is_active():
            break
        scene.dlg.advance()


def test_full_campaign_walk(game):
    """tutorial -> 7 planets -> finale -> win ending."""
    # 1. tutorial
    tutorial = game.manager.switch(settings.TUTORIAL)
    tutorial._finish()
    assert game.state.tutorial_done is True

    # 2. every planet in turn
    for planet_id in levels.PLANET_ORDER:
        assert game.state.is_unlocked(planet_id) is True, planet_id
        scene = game.manager.switch(planet_id, _test=True)
        # collect the part (walk into it)
        scene.player.respawn(*scene.part.pos)
        scene._check_pickups()
        assert scene.part.taken is True
        # walk back to the ship
        scene.player.respawn(*scene.exit_pos)
        scene._check_pickups()
        _advance_dialogue(scene)
        assert scene.won is True, f"{planet_id}: the level did not complete"
        assert game.state.is_level_done(planet_id) is True

    # 3. every part collected
    for part in EXPECTED_PARTS:
        assert game.state.has_part(part) is True, part
    assert game.state.all_parts() is True

    # 4. the finale is unlocked and the ending says WIN
    scene = game.manager.switch(settings.ENDING)
    assert scene.outcome == "win"


def test_map_launch_buttons_follow_the_chain(game):
    """The map only offers 'Launch mission' for the unlocked, un-collected planet."""
    game.state.tutorial_done = True
    scene = game.manager.switch(settings.MAP)
    planets = {p["id"]: p for p in scene.planets}
    scene.select(planets["mercury"])
    assert len(scene.panel_buttons) == 1
    scene.select(planets["venus"])
    assert scene.panel_buttons == [], "venus offered before mercury was cleared"
    game.state.mark_level_done("mercury")
    scene = game.manager.switch(settings.MAP)
    scene.select(planets["venus"])
    assert len(scene.panel_buttons) == 1


def test_map_locks_a_collected_planet(game):
    game.state.tutorial_done = True
    game.state.add_part("Solar Panel Array")
    scene = game.manager.switch(settings.MAP)
    planets = {p["id"]: p for p in scene.planets}
    scene.select(planets["mercury"])
    assert scene.panel_buttons == [], "a collected planet must not be replayable from the map"
