"""Tests for ``core.game_state`` - the shared mission state object.

Convention used throughout this file:
  * tests assert the behaviour the module actually implements;
  * every place where the implementation is *wrong* is marked with a
    ``BUG:`` comment that points at the matching xfail-test in
    ``test_core_bugs.py`` (run ``pytest --runxfail`` to see them fail).
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, r"E:\nasa")

import pytest

from core import levels, save, settings
from core.game_state import GameState


# --------------------------------------------------------------------------- #
# construction
# --------------------------------------------------------------------------- #
class TestConstruction:
    def test_defaults(self):
        state = GameState()
        assert state.mission_started is False
        assert state.levels_done == []
        assert state.current_level is None
        assert state.facts == []
        assert state.inventory == []
        assert state.photos == 0
        assert state.samples == 0
        assert state.deaths == 0
        assert state.difficulty == "normal"
        assert state.player_name == "Astronaut"
        assert state.elapsed == 0.0
        assert state.outcome is None
        assert state.volume == 0.8
        assert state.muted is False
        assert state.text_scale == 1.0
        assert state.show_hints is True
        assert state.best_times == {}
        assert state.tutorial_done is False

    def test_mutable_defaults_are_not_shared(self):
        a = GameState()
        b = GameState()
        a.levels_done.append("x")
        a.facts.append("f")
        a.inventory.append("i")
        a.best_times["x"] = 1.0
        assert b.levels_done == []
        assert b.facts == []
        assert b.inventory == []
        assert b.best_times == {}

    @pytest.mark.parametrize("bad", ["insane", "", None, 42, "EASY"])
    def test_invalid_difficulty_falls_back_to_normal(self, bad):
        assert GameState(difficulty=bad).difficulty == "normal"

    @pytest.mark.parametrize("level", [0.0, -1.0, 2.0, 99.0])
    def test_volume_is_clamped(self, level):
        assert GameState(volume=level).volume == max(0.0, min(1.0, level))

    @pytest.mark.parametrize("scale", [0.0, 0.1, 0.79, 1.61, 5.0])
    def test_text_scale_is_clamped(self, scale):
        state = GameState(text_scale=scale)
        assert 0.8 <= state.text_scale <= 1.6

    def test_text_scale_min_max_are_reachable(self):
        assert GameState(text_scale=0.8).text_scale == 0.8
        assert GameState(text_scale=1.6).text_scale == 1.6


# --------------------------------------------------------------------------- #
# inventory
# --------------------------------------------------------------------------- #
class TestInventory:
    def test_add_item_new(self):
        state = GameState()
        assert state.add_item("apple") is True
        assert state.inventory == ["apple"]

    def test_add_item_duplicate(self):
        state = GameState()
        state.add_item("apple")
        assert state.add_item("apple") is False
        assert state.inventory == ["apple"]

    @pytest.mark.parametrize("empty", [None, ""])
    def test_add_item_rejects_empty(self, empty):
        state = GameState()
        assert state.add_item(empty) is False
        assert state.inventory == []

    def test_has_item(self):
        state = GameState()
        state.add_item("apple")
        assert state.has_item("apple") is True
        assert state.has_item("pear") is False

    @pytest.mark.parametrize("empty", [None, ""])
    def test_has_item_rejects_empty(self, empty):
        assert GameState().has_item(empty) is False

    def test_add_part_and_has_part(self):
        state = GameState()
        assert state.add_part("Solar Panel Array") is True
        assert state.has_part("Solar Panel Array") is True
        assert state.add_part("Solar Panel Array") is False

    def test_take_item(self):
        state = GameState()
        state.add_item("apple")
        assert state.take_item("apple") is True
        assert state.inventory == []
        assert state.take_item("apple") is False

    def test_take_missing_item(self):
        assert GameState().take_item("nope") is False

    def test_part_count(self):
        state = GameState()
        assert state.part_count == 0
        state.add_part("a")
        state.add_part("b")
        assert state.part_count == 2


class TestParts:
    def test_required_parts_comes_from_data(self):
        state = GameState()
        assert state.required_parts() == levels.required_parts()
        assert len(state.required_parts()) == 7

    def test_required_parts_falls_back_to_inventory(self, temp_data_dir):
        state = GameState()
        state.add_part("a")
        assert state.required_parts() == ["a"]

    def test_all_parts_false_when_empty(self):
        assert GameState().all_parts() is False

    def test_all_parts_true_with_all_seven(self):
        state = GameState()
        for part in levels.required_parts():
            state.add_part(part)
        assert state.all_parts() is True

    def test_all_parts_counts_non_part_items(self):
        # BUG: part_count counts every inventory entry, so junk satisfies the check.
        # See test_core_bugs.py::test_all_parts_ignores_non_part_items
        state = GameState()
        for index in range(7):
            state.add_item(f"junk{index}")
        assert state.all_parts() is True


# --------------------------------------------------------------------------- #
# facts
# --------------------------------------------------------------------------- #
class TestFacts:
    def test_add_fact(self):
        state = GameState()
        assert state.add_fact("mars_gravity") is True
        assert state.has_fact("mars_gravity") is True

    def test_add_duplicate_fact(self):
        state = GameState()
        state.add_fact("mars_gravity")
        assert state.add_fact("mars_gravity") is False
        assert state.fact_count == 1

    @pytest.mark.parametrize("empty", [None, ""])
    def test_add_empty_fact(self, empty):
        state = GameState()
        assert state.add_fact(empty) is False
        assert state.fact_count == 0

    def test_fact_count(self):
        state = GameState()
        assert state.fact_count == 0
        state.add_fact("a")
        state.add_fact("b")
        assert state.fact_count == 2

    def test_has_fact_missing(self):
        assert GameState().has_fact("nope") is False


# --------------------------------------------------------------------------- #
# difficulty
# --------------------------------------------------------------------------- #
class TestDifficulty:
    def test_hearts_for_every_difficulty(self):
        state = GameState()
        results = {}
        for difficulty in settings.DIFFICULTIES:
            state.difficulty = difficulty
            results[difficulty] = state.hearts()
        assert results["easy"] == 5
        assert results["normal"] == 4
        # BUG: the design docs promise 2 hearts on hard, the code returns 3.
        # See test_core_bugs.py::test_hard_difficulty_has_two_hearts
        assert results["hard"] == 3

    def test_hearts_never_below_one(self):
        state = GameState()
        state.difficulty = "unknown"
        assert state.hearts() >= 1

    def test_scale_speed_per_difficulty(self):
        state = GameState()
        state.difficulty = "easy"
        assert state.scale_speed(100) == 75.0
        state.difficulty = "normal"
        assert state.scale_speed(100) == 100.0
        state.difficulty = "hard"
        assert state.scale_speed(100) == 125.0

    def test_scale_speed_unknown_difficulty_uses_normal(self):
        state = GameState()
        state.difficulty = "nonsense"
        assert state.scale_speed(100) == 100.0

    def test_cycle_difficulty_wraps(self):
        state = GameState()
        assert state.cycle_difficulty() == "normal"
        assert state.cycle_difficulty() == "hard"
        assert state.cycle_difficulty() == "easy"

    def test_cycle_difficulty_starts_from_normal(self):
        state = GameState()
        assert state.difficulty == "normal"
        assert state.cycle_difficulty() == "hard"

    def test_cycle_difficulty_from_unknown(self):
        state = GameState()
        state.difficulty = "nonsense"
        assert state.cycle_difficulty() == "easy"

    def test_toggle_text_scale(self):
        state = GameState()
        assert state.toggle_text_scale() == 1.25
        assert state.toggle_text_scale() == 1.0

    def test_toggle_hints(self):
        state = GameState()
        assert state.toggle_hints() is False
        assert state.toggle_hints() is True


# --------------------------------------------------------------------------- #
# progress
# --------------------------------------------------------------------------- #
class TestProgress:
    def test_mark_level_done(self):
        state = GameState()
        assert state.mark_level_done("mercury") is True
        assert state.is_level_done("mercury") is True
        assert state.level_count == 1

    def test_mark_level_done_is_idempotent(self):
        state = GameState()
        state.mark_level_done("mercury")
        state.mark_level_done("mercury")
        assert state.levels_done == ["mercury"]

    def test_best_time_recorded(self):
        state = GameState()
        state.mark_level_done("mercury", 12.345)
        assert state.best_time("mercury") == 12.35

    def test_best_time_keeps_the_fastest(self):
        state = GameState()
        state.mark_level_done("mercury", 12.0)
        state.mark_level_done("mercury", 20.0)
        assert state.best_time("mercury") == 12.0

    def test_best_time_improves(self):
        state = GameState()
        state.mark_level_done("mercury", 20.0)
        state.mark_level_done("mercury", 5.0)
        assert state.best_time("mercury") == 5.0

    def test_best_time_missing_is_none(self):
        assert GameState().best_time("nope") is None

    def test_is_level_done(self):
        assert GameState().is_level_done("mars") is False

    def test_level_count(self):
        state = GameState()
        state.levels_done.extend(["a", "b"])
        assert state.level_count == 2

    def test_complete_level_returns_next(self):
        state = GameState()
        assert state.complete_level("outpost") == "landing"
        assert state.is_level_done("outpost")

    def test_complete_level_final_returns_none(self):
        ids = levels.level_ids()
        state = GameState()
        assert state.complete_level(ids[-1]) is None

    def test_complete_level_for_planet_returns_none(self):
        # BUG: complete_level() walks mission.json (the legacy 4-level list) while
        # the campaign is now the seven planets, so it never advances.
        # See test_core_bugs.py::test_complete_level_advances_the_planet_campaign
        state = GameState()
        assert state.complete_level("mercury") is None

    def test_next_level_id(self):
        state = GameState()
        assert state.next_level_id() == "outpost"

    def test_next_level_id_skips_completed(self):
        state = GameState()
        state.levels_done.append("outpost")
        assert state.next_level_id() == "landing"

    def test_next_level_id_none_when_all_done(self):
        state = GameState()
        state.levels_done.extend(settings.LEVEL_IDS)
        assert state.next_level_id() is None


class TestUnlocks:
    def test_first_planet_needs_tutorial(self):
        state = GameState()
        assert state.is_unlocked("mercury") is False
        state.tutorial_done = True
        assert state.is_unlocked("mercury") is True

    def test_second_planet_needs_first(self):
        state = GameState()
        state.tutorial_done = True
        assert state.is_unlocked("venus") is False
        state.levels_done.append("mercury")
        assert state.is_unlocked("venus") is True

    def test_planet_chain(self):
        state = GameState()
        state.tutorial_done = True
        for index, planet in enumerate(levels.PLANET_ORDER):
            assert state.is_unlocked(planet) is (index == 0)
            state.levels_done.append(planet)

    def test_is_unlocked_accepts_a_planet_dict(self):
        state = GameState()
        state.tutorial_done = True
        planet = levels.planet_index()["mercury"]
        assert state.is_unlocked(planet) is True

    def test_planet_dict_honours_unlock_rules(self):
        state = GameState()
        planet = levels.planet_index()["mercury"]
        assert state.is_unlocked(planet) is False  # tutorial_done missing

    def test_planet_dict_all_parts_rule(self):
        state = GameState()
        state.tutorial_done = True
        earth = levels.planet_index()["earth"]
        assert state.is_unlocked(earth) is False
        for part in levels.required_parts():
            state.add_part(part)
        assert state.is_unlocked(earth) is True

    def test_unknown_plain_id(self):
        state = GameState()
        state.tutorial_done = True
        # BUG: an unknown id is reported as unlocked.
        # See test_core_bugs.py::test_unknown_level_id_is_locked
        assert state.is_unlocked("not-a-level") is True

    def test_unknown_plain_id_without_tutorial(self):
        assert GameState().is_unlocked("not-a-level") is False

    def test_legacy_level_chain(self):
        state = GameState()
        state.tutorial_done = True
        assert state.is_unlocked("outpost") is True
        assert state.is_unlocked("landing") is False
        state.levels_done.append("outpost")
        assert state.is_unlocked("landing") is True


class TestMissionLifecycle:
    def test_finish_mission_win(self):
        state = GameState()
        state.finish_mission("win")
        assert state.outcome == "win"
        assert state.current_level is None
        assert "home" in state.mission_line().lower()

    def test_finish_mission_lost(self):
        state = GameState()
        state.finish_mission("lost")
        assert "did not return" in state.mission_line()

    def test_finish_mission_incomplete(self):
        state = GameState()
        state.finish_mission("incomplete")
        assert "unfinished" in state.mission_line()

    def test_mission_line_default(self):
        assert "progress" in GameState().mission_line()

    def test_reset_mission_clears_progress(self):
        state = GameState()
        state.mission_started = True
        state.levels_done.append("mercury")
        state.current_level = "mars"
        state.facts.append("f")
        state.inventory.append("i")
        state.photos = 4
        state.samples = 2
        state.deaths = 3
        state.elapsed = 99.0
        state.outcome = "win"
        state.best_times["mercury"] = 1.0
        state.reset_mission()
        assert state.mission_started is False
        assert state.levels_done == []
        assert state.current_level is None
        assert state.facts == []
        assert state.inventory == []
        assert state.photos == 0
        assert state.samples == 0
        assert state.deaths == 0
        assert state.elapsed == 0.0
        assert state.outcome is None
        assert state.best_times == {}

    def test_reset_mission_keeps_preferences(self):
        state = GameState()
        state.volume = 0.25
        state.muted = True
        state.text_scale = 1.25
        state.show_hints = False
        state.reset_mission()
        assert state.volume == 0.25
        assert state.muted is True
        assert state.text_scale == 1.25
        assert state.show_hints is False

    def test_reset_mission_deletes_the_save_file(self, save_file):
        state = GameState()
        state.save()
        assert save_file.exists()
        state.reset_mission()
        assert not save_file.exists()

    def test_reset_mission_keeps_tutorial_flag(self):
        # BUG: tutorial_done survives reset_mission(), so "new game" skips the tutorial.
        # See test_core_bugs.py::test_reset_mission_clears_tutorial_done
        state = GameState()
        state.tutorial_done = True
        state.reset_mission()
        assert state.tutorial_done is True


# --------------------------------------------------------------------------- #
# persistence
# --------------------------------------------------------------------------- #
class TestPersistence:
    def test_to_dict_contains_all_keys(self):
        data = GameState().to_dict()
        for key in (
            "version", "mission_started", "levels_done", "current_level", "facts",
            "inventory", "photos", "samples", "deaths", "difficulty", "player_name",
            "elapsed", "outcome", "volume", "muted", "text_scale", "show_hints",
            "best_times",
        ):
            assert key in data, key

    def test_to_dict_uses_save_version(self):
        assert GameState().to_dict()["version"] == save.VERSION

    def test_to_dict_copies_lists(self):
        state = GameState()
        data = state.to_dict()
        data["levels_done"].append("x")
        assert state.levels_done == []

    def test_save_writes_the_file(self, save_file):
        assert GameState().save() is True
        assert save_file.exists()

    def test_save_is_valid_json(self, save_file):
        GameState().save()
        json.loads(save_file.read_text(encoding="utf-8"))

    def test_load_round_trip(self):
        state = GameState()
        state.mission_started = True
        state.levels_done.append("mercury")
        state.facts.append("f")
        state.inventory.append("i")
        state.photos = 3
        state.samples = 2
        state.deaths = 1
        state.difficulty = "hard"
        state.player_name = "Alex"
        state.elapsed = 42.5
        state.outcome = "win"
        state.volume = 0.3
        state.muted = True
        state.text_scale = 1.25
        state.show_hints = False
        state.best_times["mercury"] = 5.0
        state.save()

        restored = GameState()
        assert restored.load() is True
        assert restored.mission_started is True
        assert restored.levels_done == ["mercury"]
        assert restored.facts == ["f"]
        assert restored.inventory == ["i"]
        assert restored.photos == 3
        assert restored.samples == 2
        assert restored.deaths == 1
        assert restored.difficulty == "hard"
        assert restored.player_name == "Alex"
        assert restored.elapsed == 42.5
        assert restored.outcome == "win"
        assert restored.volume == 0.3
        assert restored.muted is True
        assert restored.text_scale == 1.25
        assert restored.show_hints is False
        assert restored.best_times == {"mercury": 5.0}

    def test_load_without_file_returns_false(self, save_file):
        assert GameState().load() is False

    def test_load_corrupt_file_returns_false(self, save_file):
        save_file.write_text("{not json", encoding="utf-8")
        assert GameState().load() is False

    def test_load_version_mismatch_returns_false(self, save_file):
        save_file.write_text(json.dumps({"version": 999, "volume": 0.2}), encoding="utf-8")
        state = GameState()
        assert state.load() is False

    def test_load_version_mismatch_keeps_preferences(self, save_file):
        save_file.write_text(
            json.dumps({"version": 999, "volume": 0.2, "muted": True, "text_scale": 1.25}),
            encoding="utf-8",
        )
        state = GameState()
        state.load()
        assert state.volume == 0.2
        assert state.muted is True
        assert state.text_scale == 1.25

    def test_load_version_mismatch_invalid_difficulty(self, save_file):
        save_file.write_text(json.dumps({"version": 999, "difficulty": "insane"}), encoding="utf-8")
        state = GameState()
        state.load()
        assert state.difficulty == "normal"

    def test_save_load_drops_tutorial_done(self):
        # BUG: tutorial_done is not part of to_dict()/_copy_from() so it is lost.
        # See test_core_bugs.py::test_save_load_preserves_tutorial_done
        state = GameState()
        state.tutorial_done = True
        state.save()
        restored = GameState()
        restored.load()
        assert restored.tutorial_done is False

    def test_save_load_turns_zero_volume_into_eight_tenths(self):
        # BUG: `float(data.get("volume", 0.8) or 0.8)` turns 0.0 into 0.8.
        # See test_core_bugs.py::test_save_load_preserves_zero_volume
        state = GameState()
        state.volume = 0.0
        state.save()
        restored = GameState()
        restored.load()
        assert restored.volume == 0.8

    def test_from_dict_defaults(self):
        state = GameState.from_dict({})
        assert state.difficulty == "normal"
        assert state.player_name == "Astronaut"
        assert state.volume == 0.8
        assert state.text_scale == 1.0
        assert state.show_hints is True

    def test_from_dict_truncates_player_name(self):
        state = GameState.from_dict({"player_name": "A" * 50})
        assert len(state.player_name) == 16

    def test_from_dict_none_player_name(self):
        # BUG: str(None) -> "None" instead of the "Astronaut" default.
        # See test_core_bugs.py::test_from_dict_none_player_name_uses_default
        state = GameState.from_dict({"player_name": None})
        assert state.player_name == "None"

    def test_from_dict_non_numeric_photos_raises(self):
        # BUG: int("abc") raises ValueError and escapes from_dict().
        # See test_core_bugs.py::test_from_dict_survives_bad_photos
        with pytest.raises(ValueError):
            GameState.from_dict({"photos": "abc"})

    def test_from_dict_best_times_not_a_mapping_raises(self):
        # BUG: AttributeError escapes from_dict().
        # See test_core_bugs.py::test_from_dict_survives_bad_best_times
        with pytest.raises(AttributeError):
            GameState.from_dict({"best_times": [1, 2]})

    def test_from_dict_non_numeric_best_time_raises(self):
        # BUG: float("zz") raises ValueError and escapes from_dict().
        # See test_core_bugs.py::test_from_dict_survives_bad_best_times
        with pytest.raises(ValueError):
            GameState.from_dict({"best_times": {"a": "zz"}})

    def test_from_dict_ignores_non_lists(self):
        state = GameState.from_dict({"facts": "abc", "inventory": 5, "levels_done": None})
        assert state.facts == []
        assert state.inventory == []
        assert state.levels_done == []

    def test_load_corrupt_fields_raises(self, save_file):
        # BUG: a corrupt-but-version-valid save crashes the game on start-up.
        # See test_core_bugs.py::test_load_survives_corrupt_save
        save_file.write_text(
            json.dumps({"version": save.VERSION, "photos": "abc"}), encoding="utf-8"
        )
        state = GameState()
        with pytest.raises(ValueError):
            state.load()

    def test_load_corrupt_version_raises(self, save_file):
        # BUG: int("abc") raises ValueError inside load().
        # See test_core_bugs.py::test_load_survives_corrupt_save
        save_file.write_text(json.dumps({"version": "abc"}), encoding="utf-8")
        state = GameState()
        with pytest.raises(ValueError):
            state.load()


# --------------------------------------------------------------------------- #
# derived text
# --------------------------------------------------------------------------- #
class TestDerivedText:
    def test_progress_line(self):
        state = GameState()
        state.levels_done.append("a")
        state.add_fact("f")
        state.deaths = 2
        line = state.progress_line()
        assert "1" in line and "facts" in line and "losses" in line

    def test_status_line_uses_inventory_length_as_denominator(self):
        # BUG: the denominator is len(inventory) so it always reads "N/N".
        # See test_core_bugs.py::test_status_line_shows_required_parts
        state = GameState()
        for part in levels.required_parts():
            state.add_part(part)
        assert state.status_line().startswith("7/7")

    def test_status_line_with_no_items(self):
        assert GameState().status_line().startswith("0/")

    def test_science_line(self):
        state = GameState()
        state.photos = 2
        state.samples = 3
        state.add_fact("f")
        line = state.science_line()
        assert "2 photos" in line and "3 samples" in line and "1 facts" in line
