"""Curated NASA science layer.

The game ships with cached values from the three systems named on the slides:

* RADLAB + DONKI - radiation measurements and space-weather events
* OSDR           - human/biological effects of spaceflight
* MARS TREK      - real Martian terrain, temperature and lava-tube sites

``tools/fetch_science.py`` can refresh the DONKI cache when the machine is online; the
game itself never touches the network, so it runs offline and on the judge's laptop.
"""

from __future__ import annotations

import json

from core import settings

_FALLBACK = {
    "updated": "bundled",
    "systems": [
        {
            "id": "radlab",
            "name": "RADLAB + DONKI",
            "role": "Radiation and real measurements",
            "url": "https://ccmc.gsfc.nasa.gov/tools/DONKI/",
            "status": "cache",
            "metrics": [
                {"label": "Mars surface dose", "value": "~0.64 mSv/day"},
                {"label": "Solar particle event", "value": "watch the feed"},
            ],
        },
        {
            "id": "osdr",
            "name": "OSDR",
            "role": "Health and biology",
            "url": "https://osdr.nasa.gov/",
            "status": "cache",
            "metrics": [
                {"label": "Bone density", "value": "~1-1.5% / month"},
                {"label": "Muscle loss", "value": "without loading"},
            ],
        },
        {
            "id": "marstrek",
            "name": "MARS TREK",
            "role": "Real Mars terrain",
            "url": "https://trek.nasa.gov/mars/",
            "status": "cache",
            "metrics": [
                {"label": "Survey site", "value": "Gale Crater"},
                {"label": "Night low", "value": "-125 C"},
            ],
        },
    ],
    "facts": [],
}

_cache: dict | None = None


def _read() -> dict:
    path = settings.DATA / "science.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(_FALLBACK)
        data.setdefault("systems", [])
        data.setdefault("facts", [])
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return dict(_FALLBACK)


def load(refresh: bool = False) -> dict:
    global _cache
    if refresh or _cache is None:
        _cache = _read()
    return _cache


def systems() -> list[dict]:
    return list(load().get("systems", []))


def system(system_id: str) -> dict | None:
    for entry in systems():
        if entry.get("id") == system_id:
            return entry
    return None


def facts() -> list[dict]:
    return list(load().get("facts", []))


def fact(fact_id: str) -> dict | None:
    for entry in facts():
        if entry.get("id") == fact_id:
            return entry
    return None


def updated() -> str:
    return str(load().get("updated", "bundled"))


def latest_event() -> dict | None:
    """Optional cached DONKI event written by tools/fetch_science.py."""
    path = settings.DATA / "cache" / "donki.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError, ValueError):
        return None
