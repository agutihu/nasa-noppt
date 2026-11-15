"""Tests for ``core.levels`` - JSON mission/level/planet data access."""

from __future__ import annotations

import json
import sys

sys.path.insert(0, r"E:\nasa")

import pytest

from core import levels, settings


class TestConstants:
    def test_level_keys(self):
        assert levels.LEVEL_KEYS == ("id", "name", "dialogue", "params", "objective")

    def test_planet_order(self):
        assert levels.PLANET_ORDER == (
            "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune",
        )
        assert len(levels.PLANET_ORDER) == 7

    def test_data_error_is_value_error(self):
        assert issubclass(levels.DataError, ValueError)


class TestLoadMission:
    def test_returns_dict(self):
        config = levels.load_mission()
        assert isinstance(config, dict)
        assert "levels" in config

    def test_levels_are_complete(self):
        for entry in levels.load_mission()["levels"]:
            for key in ("id", "name", "scene", "blurb", "briefing", "systems"):
                assert key in entry, f"{entry.get('id')} missing {key}"

    def test_title_and_subtitle_present(self):
        config = levels.load_mission()
        assert config.get("title")
        assert config.get("subtitle")

    def test_level_list(self):
        entries = levels.level_list()
        assert isinstance(entries, list)
        assert len(entries) == len(levels.level_ids())
        assert all(isinstance(entry, dict) for entry in entries)

    def test_level_ids_unique(self):
        ids = levels.level_ids()
        assert len(ids) == len(set(ids))

    def test_level_meta_found(self):
        first = levels.level_ids()[0]
        meta = levels.level_meta(first)
        assert meta["id"] == first

    def test_level_meta_unknown_raises(self):
        with pytest.raises(levels.DataError) as excinfo:
            levels.level_meta("does-not-exist")
        assert "does-not-exist" in str(excinfo.value)

    def test_level_names(self):
        names = levels.level_names()
        assert set(names) == set(levels.level_ids())
        assert all(isinstance(value, str) and value for value in names.values())

    def test_level_number(self):
        ids = levels.level_ids()
        assert levels.level_number(ids[0]) == 1
        assert levels.level_number(ids[-1]) == len(ids)

    def test_level_number_unknown_is_zero(self):
        assert levels.level_number("nope") == 0


class TestNextLevel:
    def test_next_of_first(self):
        ids = levels.level_ids()
        assert levels.next_level(ids[0]) == ids[1]

    def test_next_of_last_is_none(self):
        ids = levels.level_ids()
        assert levels.next_level(ids[-1]) is None

    def test_next_of_unknown_is_none(self):
        assert levels.next_level("nope") is None

    def test_next_of_planet_id_is_none(self):
        # The campaign is now planet based, but mission.json still holds the
        # legacy four-level list. See test_core_bugs.py.
        assert levels.next_level("mercury") is None


class TestPreviousMission:
    def test_first_planet_has_no_previous(self):
        assert levels.previous_mission("mercury") is None

    def test_chain(self):
        assert levels.previous_mission("venus") == "mercury"
        assert levels.previous_mission("mars") == "venus"
        assert levels.previous_mission("jupiter") == "mars"
        assert levels.previous_mission("saturn") == "jupiter"
        assert levels.previous_mission("uranus") == "saturn"
        assert levels.previous_mission("neptune") == "uranus"

    def test_unknown_id_returns_none(self):
        assert levels.previous_mission("pluto") is None

    def test_earth_not_in_planet_order(self):
        # "earth" is the ending world, it is deliberately absent from PLANET_ORDER
        assert "earth" not in levels.PLANET_ORDER
        assert levels.previous_mission("earth") is None

    def test_returns_none_for_non_string(self):
        assert levels.previous_mission(None) is None


class TestLoadLevel:
    def test_loads_planet_config(self):
        config = levels.load_level("mars")
        assert config["id"] == "mars"
        assert "params" in config

    def test_defaults_are_filled_in(self):
        config = levels.load_level("mars")
        assert "briefing" in config
        assert "facts" in config
        assert "source" in config
        assert "time_limit" in config
        assert "scene" in config

    def test_missing_file_raises_data_error(self):
        with pytest.raises(levels.DataError) as excinfo:
            levels.load_level("no-such-planet")
        assert "Missing data file" in str(excinfo.value)

    def test_malformed_json_raises_data_error(self, temp_data_dir):
        (temp_data_dir / "levels").mkdir()
        (temp_data_dir / "levels" / "broken.json").write_text("{oops", encoding="utf-8")
        with pytest.raises(levels.DataError) as excinfo:
            levels.load_level("broken")
        assert "Invalid JSON" in str(excinfo.value)

    def test_json_array_raises_data_error(self, temp_data_dir):
        (temp_data_dir / "levels").mkdir()
        (temp_data_dir / "levels" / "arr.json").write_text("[1,2]", encoding="utf-8")
        with pytest.raises(levels.DataError):
            levels.load_level("arr")

    def test_missing_keys_raise_data_error(self, temp_data_dir):
        (temp_data_dir / "levels").mkdir()
        (temp_data_dir / "levels" / "part.json").write_text(
            json.dumps({"id": "part", "name": "Part"}), encoding="utf-8"
        )
        with pytest.raises(levels.DataError) as excinfo:
            levels.load_level("part")
        assert "dialogue" in str(excinfo.value)

    def test_params_must_be_object(self, temp_data_dir):
        (temp_data_dir / "levels").mkdir()
        (temp_data_dir / "levels" / "bad.json").write_text(
            json.dumps(
                {
                    "id": "bad", "name": "Bad", "dialogue": "d",
                    "params": [], "objective": "o",
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(levels.DataError) as excinfo:
            levels.load_level("bad")
        assert "params" in str(excinfo.value)

    def test_briefing_must_be_list(self, temp_data_dir):
        (temp_data_dir / "levels").mkdir()
        (temp_data_dir / "levels" / "bad2.json").write_text(
            json.dumps(
                {
                    "id": "bad2", "name": "Bad", "dialogue": "d",
                    "params": {}, "objective": "o", "briefing": "nope",
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(levels.DataError) as excinfo:
            levels.load_level("bad2")
        assert "briefing" in str(excinfo.value)


class TestParamsFor:
    def test_merges_override(self):
        params = levels.params_for(
            {"params": {"speed": 1, "difficulty": {"hard": {"speed": 9}}}}, "hard"
        )
        assert params["speed"] == 9
        assert "difficulty" not in params

    def test_base_params_survive(self):
        params = levels.params_for(
            {"params": {"speed": 1, "difficulty": {"hard": {"jump": 9}}}}, "hard"
        )
        assert params["speed"] == 1
        assert params["jump"] == 9

    def test_unknown_difficulty_falls_back_to_normal(self):
        params = levels.params_for(
            {"params": {"speed": 1, "difficulty": {"normal": {"speed": 5}}}}, "insane"
        )
        assert params["speed"] == 5

    def test_missing_params_gives_empty_dict(self):
        assert levels.params_for({}, "easy") == {}

    def test_none_params_gives_empty_dict(self):
        assert levels.params_for({"params": None}, "easy") == {}

    def test_original_config_is_not_mutated(self):
        config = {"params": {"speed": 1, "difficulty": {"hard": {"speed": 9}}}}
        levels.params_for(config, "hard")
        assert "difficulty" in config["params"]

    def test_non_dict_difficulty_block_raises(self):
        # BUG: AttributeError escapes instead of a DataError.
        with pytest.raises(AttributeError):
            levels.params_for({"params": {"difficulty": 5}}, "easy")


class TestDialogue:
    def test_loads_mars(self):
        data = levels.load_dialogue("dialogue/mars.json")
        assert data["speaker"]
        assert "start" in data["lines"]

    def test_prefix_is_optional(self):
        a = levels.load_dialogue("dialogue/mars.json")
        b = levels.load_dialogue("mars.json")
        assert a["triggers"] == b["triggers"]

    def test_lines_are_list_of_dicts(self):
        data = levels.load_dialogue("dialogue/mars.json")
        for trigger, entries in data["lines"].items():
            assert isinstance(entries, list), trigger
            for entry in entries:
                assert set(entry) == {"speaker", "text"}
                assert entry["text"].strip()

    def test_triggers_matches_lines(self):
        data = levels.load_dialogue("dialogue/mars.json")
        assert set(data["triggers"]) == set(data["lines"])

    def test_missing_file_raises_data_error(self):
        with pytest.raises(levels.DataError):
            levels.load_dialogue("no-such-dialogue.json")

    def test_backslash_path_is_normalised(self):
        data = levels.load_dialogue("dialogue\\mars.json")
        assert "start" in data["lines"]

    def test_blank_lines_are_skipped(self, temp_data_dir):
        (temp_data_dir / "dialogue").mkdir()
        (temp_data_dir / "dialogue" / "d.json").write_text(
            json.dumps(
                {
                    "speaker": "Laika",
                    "lines": [
                        {"trigger": "start", "text": "   "},
                        {"trigger": "start", "text": "hello"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        data = levels.load_dialogue("d.json")
        assert len(data["lines"]["start"]) == 1


class TestPlanets:
    def test_load_planets(self):
        config = levels.load_planets()
        assert config["planets"]
        assert config["order"]

    def test_planet_entries_are_complete(self):
        for planet in levels.load_planets()["planets"]:
            for key in ("id", "name", "map_position"):
                assert key in planet, planet.get("id")

    def test_planet_index(self):
        index = levels.planet_index()
        assert "mercury" in index
        assert index["mercury"]["name"] == "Mercury"

    def test_planet_index_covers_every_planet(self):
        index = levels.planet_index()
        assert set(index) == {p["id"] for p in levels.load_planets()["planets"]}

    def test_empty_planets_raises(self, temp_data_dir):
        (temp_data_dir / "planets.json").write_text('{"planets": []}', encoding="utf-8")
        with pytest.raises(levels.DataError):
            levels.load_planets()

    def test_planet_missing_key_raises(self, temp_data_dir):
        (temp_data_dir / "planets.json").write_text(
            '{"planets": [{"id": "x"}]}', encoding="utf-8"
        )
        with pytest.raises(levels.DataError):
            levels.load_planets()


class TestRequiredParts:
    def test_seven_parts(self):
        parts = levels.required_parts()
        assert len(parts) == 7
        assert len(set(parts)) == 7

    def test_expected_names(self):
        assert levels.required_parts() == [
            "Solar Panel Array",
            "Hull Plating",
            "Navigation Module",
            "Shield Generator",
            "Fuel Cells",
            "Thermal Regulator",
            "Signal Antenna",
        ]

    def test_returns_a_fresh_list(self):
        first = levels.required_parts()
        first.append("junk")
        assert "junk" not in levels.required_parts()

    def test_falls_back_to_empty_when_data_missing(self, temp_data_dir):
        # A DataError inside the loader is swallowed and yields no parts.
        assert levels.required_parts() == []
