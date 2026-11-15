"""Progress persistence.

One small JSON file next to the game. Everything is wrapped in try/except: a corrupt or
missing save must never stop the player from starting a new mission.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from core import settings

VERSION = 2


def _path() -> Path:
    return settings.SAVE_FILE


def exists() -> bool:
    return _path().is_file()


def read() -> dict | None:
    try:
        raw = _path().read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def write(payload: dict) -> bool:
    path = _path()
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def clear() -> None:
    try:
        _path().unlink(missing_ok=True)
    except OSError:
        pass
