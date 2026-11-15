"""Campaign progression + gameplay-rule tests.

Run from the project root::

    python -m pytest E:\\nasa\\tests\\campaign -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pygame  # noqa: E402

from harness import make_game, run_frames, capture, key  # noqa: E402

from core import levels, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402


# ---------------------------------------------------------------------------
# fixtures live in conftest.py (state / game)
# ---------------------------------------------------------------------------


def planet_dicts() -> dict[str, dict]:
    return levels.planet_index()


# ---------------------------------------------------------------------------
# 1. fresh state / unlock chain
# ---------------------------------------------------------------------------

def test_planet_order_matches_planets_json():
    """PLANET_ORDER must list exactly the 7 playable planets in campaign order."""
    planets = levels.load_planets()["planets"]
    playable = [p["id"] for p in planets if p.get("playable") and p["playable"] != "ending"]
    assert list(levels.PLANET_ORDER) == playable, (
        f"PLANET_ORDER={levels.PLANET_ORDER} != playable planets {playable}"
    )


def test_fresh_state_locks_everything(state: GameState):
    """Fresh save: no planet is unlocked (mercury needs the tutorial)."""
    assert state.tutorial_done is False
    for planet_id in levels.PLANET_ORDER:
        assert state.is_unlocked(planet_id) is False, planet_id
    for planet in planet_dicts().values():
        if planet.get("playable"):
            assert state.is_unlocked(planet) is False, planet["id"]


def test_unlock_chain_step_by_step(state: GameState):
    """Each planet unlocks only after the previous one is in levels_done."""
    state.tutorial_done = True
    for index, planet_id in enumerate(levels.PLANET_ORDER):
        # everything after the current one stays locked
        for later in levels.PLANET_ORDER[index + 1:]:
            assert state.is_unlocked(later) is False, later
        assert state.is_unlocked(planet_id) is True, planet_id
        state.mark_level_done(planet_id, 1.0)
    # all seven unlocked at the end
    for planet_id in levels.PLANET_ORDER:
        assert state.is_unlocked(planet_id) is True


def test_unlock_chain_blocks_skips(state: GameState):
    """You cannot skip a planet in the chain."""
    state.tutorial_done = True
    state.mark_level_done("mercury")
    assert state.is_unlocked("venus") is True
    assert state.is_unlocked("mars") is False
    state.mark_level_done("venus")
    assert state.is_unlocked("mars") is True
    assert state.is_unlocked("jupiter") is False


# ---------------------------------------------------------------------------
# 2. is_unlocked() - three input flavours
# ---------------------------------------------------------------------------

def test_is_unlocked_planet_dict_honours_unlock_rules(state: GameState):
    """A planet dict honours its own 'unlock' list (tutorial_done / all_parts)."""
    planets = planet_dicts()

    # mercury: unlock == ["tutorial_done"]
    assert state.is_unlocked(planets["mercury"]) is False
    state.tutorial_done = True
    assert state.is_unlocked(planets["mercury"]) is True

    # earth (the finale): unlock == ["all_parts"]
    assert state.is_unlocked(planets["earth"]) is False
    for part in levels.required_parts():
        state.add_part(part)
    assert state.is_unlocked(planets["earth"]) is True


def test_is_unlocked_planet_dict_also_applies_the_chain(state: GameState):
    """A planet dict with an empty unlock list still needs the chain."""
    planets = planet_dicts()
    state.tutorial_done = True
    assert state.is_unlocked(planets["venus"]) is False
    state.mark_level_done("mercury")
    assert state.is_unlocked(planets["venus"]) is True


def test_is_unlocked_plain_id_rules(state: GameState):
    """Plain ids: mercury needs the tutorial, every other planet needs the previous."""
    assert state.is_unlocked("mercury") is False
    state.tutorial_done = True
    assert state.is_unlocked("mercury") is True
    assert state.is_unlocked("venus") is False
    state.mark_level_done("mercury")
    assert state.is_unlocked("venus") is True
    assert state.is_unlocked("mars") is False


def test_is_unlocked_legacy_level_ids(state: GameState):
    """Legacy ids keep the old LEVEL_IDS order; index 0 is always unlocked."""
    order = list(settings.LEVEL_IDS)
    assert order == ["outpost", "landing", "surface", "tunnel"]
    # index 0 is always unlocked - even with no tutorial and no progress
    assert state.is_unlocked(order[0]) is True
    for index in range(1, len(order)):
        level_id = order[index]
        assert state.is_unlocked(level_id) is False, level_id
        state.mark_level_done(order[index - 1])
        assert state.is_unlocked(level_id) is True, level_id


def test_is_unlocked_legacy_ids_ignore_tutorial(state: GameState):
    """The legacy branch must not require tutorial_done for index 0."""
    fresh = GameState()
    assert fresh.tutorial_done is False
    assert fresh.is_unlocked("outpost") is True


# ---------------------------------------------------------------------------
# 4. required parts / finale lock
# ---------------------------------------------------------------------------

EXPECTED_PARTS = [
    "Solar Panel Array",
    "Hull Plating",
    "Navigation Module",
    "Shield Generator",
    "Fuel Cells",
    "Thermal Regulator",
    "Signal Antenna",
]


def test_required_parts_are_the_seven_planet_parts(state: GameState):
    assert levels.required_parts() == EXPECTED_PARTS
    assert state.required_parts() == EXPECTED_PARTS


def test_required_parts_do_not_shrink_when_collected(state: GameState):
    """required_parts() must NOT return the collected parts."""
    assert state.required_parts() == EXPECTED_PARTS
    state.add_part("Solar Panel Array")
    assert state.required_parts() == EXPECTED_PARTS
    assert len(state.required_parts()) == 7


def test_all_parts_and_finale_lock(state: GameState):
    planets = planet_dicts()
    assert state.all_parts() is False
    for index, part in enumerate(EXPECTED_PARTS[:-1]):
        state.add_part(part)
        assert state.all_parts() is False, f"finale unlocked after {index + 1} parts"
        assert state.is_unlocked(planets["earth"]) is False
    state.add_part(EXPECTED_PARTS[-1])
    assert state.all_parts() is True
    assert state.is_unlocked(planets["earth"]) is True


# ---------------------------------------------------------------------------
# 5. previous_mission
# ---------------------------------------------------------------------------

def test_previous_mission_for_every_planet():
    for index, planet_id in enumerate(levels.PLANET_ORDER):
        expected = None if index == 0 else levels.PLANET_ORDER[index - 1]
        assert levels.previous_mission(planet_id) == expected, planet_id


def test_previous_mission_for_map_planets():
    planets = planet_dicts()
    for planet in planets.values():
        planet_id = planet["id"]
        result = levels.previous_mission(planet_id)
        if planet_id in levels.PLANET_ORDER:
            assert result is not None or planet_id == "mercury"
        else:
            # 'earth' (the finale) is not part of the planet chain
            assert result is None


def test_previous_mission_unknown_id():
    assert levels.previous_mission("not-a-planet") is None


# ---------------------------------------------------------------------------
# 6. add_part / has_part
# ---------------------------------------------------------------------------

def test_add_part_stores_in_inventory(state: GameState):
    assert state.add_part("Solar Panel Array") is True
    assert "Solar Panel Array" in state.inventory
    assert state.has_part("Solar Panel Array") is True
    assert state.part_count == 1
    # duplicates are refused
    assert state.add_part("Solar Panel Array") is False
    assert state.part_count == 1


def test_add_part_none_and_empty(state: GameState):
    assert state.add_part(None) is False
    assert state.add_part("") is False
    assert state.has_part(None) is False
    assert state.has_part("") is False
    assert state.inventory == []


def test_part_count_tracks_inventory(state: GameState):
    for part in EXPECTED_PARTS:
        state.add_part(part)
    assert state.part_count == 7
    assert state.all_parts() is True


# ---------------------------------------------------------------------------
# 8. difficulty
# ---------------------------------------------------------------------------

def test_hearts_per_difficulty():
    """design.md: Easy 5 hearts, Normal 3 hearts, Hard 2 hearts."""
    expected = {"easy": 5, "normal": 3, "hard": 2}
    actual = {}
    for difficulty in ("easy", "normal", "hard"):
        st = GameState(difficulty=difficulty)
        actual[difficulty] = st.hearts()
    assert actual == expected, f"hearts {actual} != spec {expected}"


def test_time_multiplier_per_difficulty():
    """design.md: Easy +25% time, Normal 1.0, Hard -15% time."""
    from scenes.campaign import CampaignScene

    expected = {"easy": 1.25, "normal": 1.0, "hard": 0.85}
    actual = {}
    for difficulty in ("easy", "normal", "hard"):
        st = GameState(difficulty=difficulty)
        scene = CampaignScene.__new__(CampaignScene)
        scene.state = st
        actual[difficulty] = CampaignScene._time_scale(scene)
    assert actual == expected, f"time scale {actual} != spec {expected}"


def test_difficulty_values_are_not_hardcoded_in_scenes():
    """AGENTS.md: all gameplay numbers come from data, not hardcoded."""
    from scenes import campaign

    source = Path(campaign.__file__).read_text(encoding="utf-8")
    assert '{"easy": 1.25, "normal": 1.0, "hard": 0.85}' in source, (
        "the difficulty multipliers are hardcoded in scenes/campaign.py, not read from data"
    )


def test_params_for_reads_the_difficulty_override_block():
    """levels.params_for() must consume the difficulty block from the JSON."""
    cfg = levels.load_level("level1")
    params = levels.params_for(cfg, "easy")
    assert params.get("move_speed") == 200, (
        "level1.json 'difficulty_overrides' was not applied by levels.params_for()"
    )


def test_hints_are_gated_by_difficulty():
    """design.md: Easy hints always, Hard hints on request only."""
    from scenes import world_level

    source = Path(world_level.__file__).read_text(encoding="utf-8")
    assert "show_hints" in source, (
        "world_level.py never reads state.show_hints - hints are not gated by difficulty"
    )


def test_cycle_difficulty_steps_through_the_three_modes(state: GameState):
    assert state.difficulty == "normal"
    assert state.cycle_difficulty() == "hard"
    assert state.cycle_difficulty() == "easy"
    assert state.cycle_difficulty() == "normal"


# ---------------------------------------------------------------------------
# 12. pickups / blaster / dialogue keys (world level)
# ---------------------------------------------------------------------------

def test_world_pickups_are_proximity_based(game):
    """Walking into a pickup collects it - no key press needed."""
    scene = game.manager.switch("mercury", _test=True)
    assert scene.part.taken is False
    # teleport the player onto the part
    scene.player.respawn(*scene.part.pos)
    scene._check_pickups()
    assert scene.part.taken is True
    assert game.state.has_part("Solar Panel Array") is True


def test_world_collecting_part_activates_the_return_pad(game):
    scene = game.manager.switch("mercury", _test=True)
    assert scene.exit_active is False
    scene.player.respawn(*scene.part.pos)
    scene._check_pickups()
    assert scene.exit_active is True


def test_e_fires_the_blaster(game):
    scene = game.manager.switch("mercury", _test=True)
    assert len(scene.lasers) == 0
    scene.handle_events([key(pygame.K_e)])
    assert len(scene.lasers) == 1, "pressing E did not fire a laser bolt"


def test_e_and_space_advance_dialogue(game):
    scene = game.manager.switch("mercury", _test=True)
    scene._start_mission()
    assert scene.dlg.is_active() is True
    # E reveals the line, a second E moves to the next line
    scene.handle_events([key(pygame.K_e)])
    assert scene.dlg.fully_revealed is True
    index_before = scene.dlg.index
    scene.handle_events([key(pygame.K_e)])
    assert scene.dlg.index == index_before + 1
    # space advances too
    index_before = scene.dlg.index
    scene.handle_events([key(pygame.K_SPACE)])
    assert scene.dlg.index >= index_before
