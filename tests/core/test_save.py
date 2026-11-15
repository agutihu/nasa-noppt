"""Tests for ``core.save`` - the tiny JSON persistence layer."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, r"E:\nasa")

import pytest

from core import save, settings


class TestPath:
    def test_path_follows_settings(self, save_file):
        assert save._path() == save_file

    def test_exists_false_when_missing(self, save_file):
        assert save.exists() is False

    def test_exists_true_after_write(self, save_file):
        save.write({"a": 1})
        assert save.exists() is True


class TestWrite:
    def test_write_returns_true(self, save_file):
        assert save.write({"hello": "world"}) is True

    def test_write_creates_file(self, save_file):
        save.write({"hello": "world"})
        assert save_file.exists()

    def test_write_round_trips(self, save_file):
        payload = {"a": 1, "b": [1, 2, 3], "c": {"d": True}}
        save.write(payload)
        assert save.read() == payload

    def test_write_is_indented_json(self, save_file):
        save.write({"a": 1})
        raw = save_file.read_text(encoding="utf-8")
        assert "\n" in raw
        assert json.loads(raw) == {"a": 1}

    def test_write_leaves_no_tmp_file(self, save_file):
        save.write({"a": 1})
        leftovers = list(save_file.parent.glob("*.tmp"))
        assert leftovers == []

    def test_write_overwrites(self, save_file):
        save.write({"a": 1})
        save.write({"b": 2})
        assert save.read() == {"b": 2}

    def test_write_into_missing_directory_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "SAVE_FILE", tmp_path / "nope" / "deeper" / "s.json")
        assert save.write({"a": 1}) is False

    def test_write_to_directory_path_returns_false(self, tmp_path, monkeypatch):
        as_dir = tmp_path / "adir"
        as_dir.mkdir()
        monkeypatch.setattr(settings, "SAVE_FILE", as_dir)
        assert save.write({"a": 1}) is False

    def test_write_non_serializable_raises(self, save_file):
        # BUG: only OSError is caught, a TypeError from json.dumps escapes.
        with pytest.raises(TypeError):
            save.write({"bad": object()})
        # documented in test_core_bugs.py::test_save_write_non_serializable


class TestRead:
    def test_read_missing_returns_none(self, save_file):
        assert save.read() is None

    def test_read_corrupt_json_returns_none(self, save_file):
        save_file.write_text("{not json at all", encoding="utf-8")
        assert save.read() is None

    def test_read_empty_file_returns_none(self, save_file):
        save_file.write_text("", encoding="utf-8")
        assert save.read() is None

    def test_read_json_array_returns_none(self, save_file):
        save_file.write_text("[1, 2, 3]", encoding="utf-8")
        assert save.read() is None

    def test_read_json_scalar_returns_none(self, save_file):
        save_file.write_text("42", encoding="utf-8")
        assert save.read() is None

    def test_read_json_null_returns_none(self, save_file):
        save_file.write_text("null", encoding="utf-8")
        assert save.read() is None

    def test_read_object_returns_dict(self, save_file):
        save_file.write_text('{"a": 1}', encoding="utf-8")
        data = save.read()
        assert isinstance(data, dict)
        assert data == {"a": 1}

    def test_read_directory_returns_none(self, tmp_path, monkeypatch):
        as_dir = tmp_path / "adir"
        as_dir.mkdir()
        monkeypatch.setattr(settings, "SAVE_FILE", as_dir)
        assert save.read() is None


class TestClear:
    def test_clear_removes_file(self, save_file):
        save.write({"a": 1})
        assert save_file.exists()
        save.clear()
        assert not save_file.exists()

    def test_clear_on_missing_file_is_safe(self, save_file):
        save.clear()  # must not raise
        assert not save_file.exists()

    def test_clear_on_directory_is_safe(self, tmp_path, monkeypatch):
        as_dir = tmp_path / "adir"
        as_dir.mkdir()
        monkeypatch.setattr(settings, "SAVE_FILE", as_dir)
        save.clear()  # must not raise
        assert as_dir.exists()


class TestVersion:
    def test_version_is_int(self):
        assert isinstance(save.VERSION, int)
        assert save.VERSION >= 1
