"""The single shared state object.

Scenes read and write this; nothing else in the game is global. Difficulty is applied here
so no level ever branches on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core import levels, save, settings

MULTIPLIERS = {
    "easy": {"speed": 0.75, "time": 1.25, "hearts": 5, "hint": 20.0},
    "normal": {"speed": 1.00, "time": 1.00, "hearts": 3, "hint": 45.0},
    # hint 0.0 means "only when the player asks"
    "hard": {"speed": 1.25, "time": 0.85, "hearts": 2, "hint": 0.0},
}


@dataclass
class GameState:
    parts: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    deaths: int = 0
    difficulty: str = "normal"
    current_level: str | None = None
    elapsed: float = 0.0
    tutorial_done: bool = False
    volume: float = 0.8
    muted: bool = False
    text_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.difficulty not in MULTIPLIERS:
            self.difficulty = "normal"
        self.volume = max(0.0, min(1.0, float(self.volume)))
        self.text_scale = max(0.8, min(1.6, float(self.text_scale)))

    # --- parts --------------------------------------------------------------
    def add_part(self, name: str | None) -> bool:
        if not name or name in self.parts:
            return False
        self.parts.append(name)
        self.save()
        return True

    def has_part(self, name: str | None) -> bool:
        return bool(name) and name in self.parts

    @property
    def part_count(self) -> int:
        return len(self.parts)

    def required_parts(self) -> list[str]:
        return levels.required_parts()

    def all_parts(self) -> bool:
        required = self.required_parts()
        return bool(required) and all(self.has_part(part) for part in required)

    # --- facts --------------------------------------------------------------
    def add_fact(self, key: str | None) -> bool:
        if not key or key in self.facts:
            return False
        self.facts.append(key)
        self.save()
        return True

    def has_fact(self, key: str) -> bool:
        return key in self.facts

    @property
    def fact_count(self) -> int:
        return len(self.facts)

    # --- difficulty ---------------------------------------------------------
    def _multipliers(self) -> dict:
        return MULTIPLIERS.get(self.difficulty, MULTIPLIERS["normal"])

    def scale_speed(self, value: float) -> float:
        return value * self._multipliers()["speed"]

    def scale_time(self, value: float) -> float:
        return value * self._multipliers()["time"]

    def hearts(self) -> int:
        return int(self._multipliers()["hearts"])

    def hint_idle(self) -> float:
        return float(self._multipliers()["hint"])

    def next_difficulty(self) -> None:
        order = list(settings.DIFFICULTIES)
        index = (order.index(self.difficulty) + 1) % len(order)
        self.difficulty = order[index]
        self.save()

    def toggle_text_scale(self) -> float:
        self.text_scale = 1.25 if self.text_scale < 1.2 else 1.0
        self.save()
        return self.text_scale

    # --- progress -----------------------------------------------------------
    def is_unlocked(self, planet: dict) -> bool:
        for rule in planet.get("unlock", []) or []:
            if rule == "tutorial_done" and not self.tutorial_done:
                return False
            if rule == "all_parts" and not self.all_parts():
                return False
        return True

    def reset(self) -> None:
        self.parts.clear()
        self.facts.clear()
        self.deaths = 0
        self.current_level = None
        self.elapsed = 0.0
        self.tutorial_done = False
        # text_scale/volume/muted survive a reset on purpose (player preferences)
        save.clear()

    # --- persistence --------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "version": save.VERSION,
            "parts": list(self.parts),
            "facts": list(self.facts),
            "deaths": self.deaths,
            "difficulty": self.difficulty,
            "current_level": self.current_level,
            "elapsed": round(self.elapsed, 2),
            "tutorial_done": self.tutorial_done,
            "volume": round(self.volume, 2),
            "muted": self.muted,
            "text_scale": round(self.text_scale, 2),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        def _list(value) -> list[str]:
            return [str(item) for item in value] if isinstance(value, list) else []

        return cls(
            parts=_list(data.get("parts")),
            facts=_list(data.get("facts")),
            deaths=int(data.get("deaths", 0) or 0),
            difficulty=str(data.get("difficulty", "normal")),
            current_level=data.get("current_level"),
            elapsed=float(data.get("elapsed", 0.0) or 0.0),
            tutorial_done=bool(data.get("tutorial_done", False)),
            volume=float(data.get("volume", 0.8) or 0.8),
            muted=bool(data.get("muted", False)),
        )

    def save(self) -> bool:
        return save.write(self.to_dict())

    def load(self) -> bool:
        data = save.read()
        if not data:
            return False
        restored = GameState.from_dict(data)
        self.parts = restored.parts
        self.facts = restored.facts
        self.deaths = restored.deaths
        self.difficulty = restored.difficulty
        self.current_level = restored.current_level
        self.elapsed = restored.elapsed
        self.tutorial_done = restored.tutorial_done
        self.volume = restored.volume
        self.muted = restored.muted
        self.text_scale = restored.text_scale
        return True

    # --- derived text -------------------------------------------------------
    def status_line(self) -> str:
        required = len(self.required_parts())
        return f"{self.part_count}/{required} parts  |  {len(self.facts)} facts  |  {self.deaths} losses"
