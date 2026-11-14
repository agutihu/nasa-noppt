"""JSON level and planet data.

All gameplay numbers live in ``data/levels/*.json`` and ``data/planets.json``. Scenes read
through this module so a bad edit produces a readable error instead of a traceback in the
middle of a frame.
"""

from __future__ import annotations

import json
from pathlib import Path

from core import settings

LEVEL_KEYS = ("id", "name", "style", "params", "dialogue")


class DataError(ValueError):
    """Raised when a data file is missing, malformed or incomplete."""


def _read_json(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise DataError(f"Missing data file: {path.relative_to(settings.ROOT)}") from None
    except OSError as exc:
        raise DataError(f"Cannot read {path.name}: {exc}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DataError(f"Invalid JSON in {path.name} (line {exc.lineno}): {exc.msg}") from None
    if not isinstance(data, dict):
        raise DataError(f"{path.name} must contain a JSON object")
    return data


def load_level(level_id: str) -> dict:
    path = settings.DATA / "levels" / f"{level_id}.json"
    config = _read_json(path)
    missing = [key for key in LEVEL_KEYS if key not in config]
    if missing:
        raise DataError(f"{path.name} is missing: {', '.join(missing)}")

    config.setdefault("part", None)
    config.setdefault("facts", [])
    config.setdefault("unlock", [])
    config.setdefault("hint_rules", {"idle_seconds": 45, "deaths": 3})
    config.setdefault("objective", "")
    if not isinstance(config["params"], dict):
        raise DataError(f"{path.name}: 'params' must be an object")
    return config


def load_planets() -> dict:
    config = _read_json(settings.DATA / "planets.json")
    planets = config.get("planets")
    if not isinstance(planets, list) or not planets:
        raise DataError("planets.json: 'planets' must be a non-empty list")
    for planet in planets:
        for key in ("id", "name", "map_position"):
            if key not in planet:
                raise DataError(f"planets.json: entry {planet!r} is missing '{key}'")
    config.setdefault("order", [planet["id"] for planet in planets])
    return config


def planet_index() -> dict[str, dict]:
    return {planet["id"]: planet for planet in load_planets()["planets"]}


def load_dialogue(relative: str) -> dict:
    """Load a dialogue file and index its lines by trigger.

    File shape::

        {"speaker": "Laika", "lines": [{"trigger": "start", "text": "..."}]}
    """
    name = relative.replace("\\", "/")
    if name.startswith("dialogue/"):
        name = name[len("dialogue/") :]
    path = settings.DATA / "dialogue" / name
    config = _read_json(path)

    by_trigger: dict[str, list[str]] = {}
    for entry in config.get("lines", []):
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("text", "")).strip()
        if not text:
            continue
        trigger = str(entry.get("trigger", "start"))
        by_trigger.setdefault(trigger, []).append(text)

    return {
        "speaker": config.get("speaker", "Laika"),
        "lines": by_trigger,
        "triggers": list(by_trigger.keys()),
    }


def level_ids() -> list[str]:
    folder = settings.DATA / "levels"
    if not folder.is_dir():
        return []
    return sorted(path.stem for path in folder.glob("*.json"))


def playable_levels() -> list[dict]:
    """Planets with a real mission in this build (excludes archive cards and the finale)."""
    return [
        planet
        for planet in load_planets()["planets"]
        if planet.get("playable")
        and planet["playable"] not in (None, "ending")
        and planet.get("part")
    ]


def mission_chain() -> list[str]:
    """Mission planets in the order they must be completed (finale excluded)."""
    return [
        planet["id"]
        for planet in load_planets()["planets"]
        if planet.get("playable") and planet["playable"] != "ending"
    ]


def previous_mission(planet_id: str) -> str | None:
    """The mission that must be won before this one, or None for the first."""
    chain = mission_chain()
    if planet_id in chain:
        index = chain.index(planet_id)
        if index > 0:
            return chain[index - 1]
    return None


def required_parts() -> list[str]:
    return [planet["part"] for planet in playable_levels()]


def finale_level() -> str:
    for planet in load_planets()["planets"]:
        if planet.get("playable") == "ending":
            return "ending"
    return "ending"
