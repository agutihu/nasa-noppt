"""The single shared state object.

Scenes read and write this; nothing else in the game is global. It holds mission
progress, science facts unlocked, the small inventory the outpost vending machines
dispense, and the player's preferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core import levels, save, settings


@dataclass
class GameState:
    mission_started: bool = False
    levels_done: list[str] = field(default_factory=list)
    current_level: str | None = None
    facts: list[str] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)
    photos: int = 0
    samples: int = 0
    deaths: int = 0
    difficulty: str = "normal"
    player_name: str = "Astronaut"
    elapsed: float = 0.0
    outcome: str | None = None
    volume: float = 0.8
    muted: bool = False
    text_scale: float = 1.0
    show_hints: bool = True
    best_times: dict[str, float] = field(default_factory=dict)
    tutorial_done: bool = False

    def __post_init__(self) -> None:
        if self.difficulty not in settings.DIFFICULTIES:
            self.difficulty = "normal"
        self.volume = max(0.0, min(1.0, float(self.volume)))
        self.text_scale = max(0.8, min(1.6, float(self.text_scale)))

    # --- inventory ----------------------------------------------------------
    def add_item(self, item_id: str | None) -> bool:
        if not item_id or item_id in self.inventory:
            return False
        self.inventory.append(item_id)
        return True

    def has_item(self, item_id: str | None) -> bool:
        return bool(item_id) and item_id in self.inventory

    def has_part(self, part_id: str | None) -> bool:
        return bool(part_id) and part_id in self.inventory

    def add_part(self, part_id: str | None) -> bool:
        """Record a recovered part; returns True when it was new."""
        return self.add_item(part_id)

    def take_item(self, item_id: str) -> bool:
        if item_id not in self.inventory:
            return False
        self.inventory.remove(item_id)
        return True

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

    def hearts(self) -> int:
        """Return the number of hearts based on difficulty."""
        order = list(settings.DIFFICULTIES)
        idx = order.index(self.difficulty) if self.difficulty in order else 1
        return max(1, 5 - idx)

    def scale_speed(self, value: float) -> float:
        """Scale speed based on difficulty multiplier."""
        order = list(settings.DIFFICULTIES)
        idx = order.index(self.difficulty) if self.difficulty in order else 1
        multipliers = {"easy": 0.75, "normal": 1.0, "hard": 1.25}
        return value * multipliers.get(order[idx], 1.0)

    @property
    def part_count(self) -> int:
        return len(self.inventory)

    def required_parts(self) -> list[str]:
        """The parts the mission needs - one per playable planet."""
        names = levels.required_parts()
        if names:
            return names
        return list(self.inventory)

    def all_parts(self) -> bool:
        """True when every required part has been recovered."""
        required = self.required_parts()
        if not required:
            return False
        return self.part_count >= len(required)

    # --- difficulty ---------------------------------------------------------
    def cycle_difficulty(self) -> str:
        """Step through easy -> normal -> hard and return the new difficulty."""
        order = list(settings.DIFFICULTIES)
        index = (order.index(self.difficulty) + 1) % len(order) if self.difficulty in order else 0
        self.difficulty = order[index]
        self.save()
        return self.difficulty

    def toggle_text_scale(self) -> float:
        self.text_scale = 1.25 if self.text_scale < 1.2 else 1.0
        self.save()
        return self.text_scale

    def toggle_hints(self) -> bool:
        self.show_hints = not self.show_hints
        self.save()
        return self.show_hints

    # --- progress -----------------------------------------------------------
    def mark_level_done(self, level_id: str, time_seconds: float | None = None) -> bool:
        """Record a cleared level; keeps the best time per level."""
        if level_id not in self.levels_done:
            self.levels_done.append(level_id)
        if time_seconds is not None:
            best = self.best_times.get(level_id)
            if best is None or float(time_seconds) < best:
                self.best_times[level_id] = round(float(time_seconds), 2)
        self.save()
        return True

    def is_level_done(self, level_id: str) -> bool:
        return level_id in self.levels_done

    def best_time(self, level_id: str) -> float | None:
        return self.best_times.get(level_id)

    def is_unlocked(self, level_id) -> bool:
        """Sequential campaign: each mission opens after the previous one is cleared.

        Accepts either a planet definition (``data/planets.json``) or a plain id.
        The first planet needs the tutorial; every other planet needs the one
        before it. The finale needs every part.
        """
        if isinstance(level_id, dict):
            planet = level_id
            rules = planet.get("unlock", []) or []
            if "tutorial_done" in rules and not self.tutorial_done:
                return False
            if "all_parts" in rules and not self.all_parts():
                return False
            previous = levels.previous_mission(str(planet.get("id", "")))
            if previous is not None and not self.is_level_done(previous):
                return False
            return True

        level_id = str(level_id)
        if level_id in levels.PLANET_ORDER:
            previous = levels.previous_mission(level_id)
            return self.tutorial_done if previous is None else self.is_level_done(previous)

        order = list(settings.LEVEL_IDS)
        if level_id not in order:
            return self.tutorial_done
        index = order.index(level_id)
        return index == 0 or order[index - 1] in self.levels_done

    def next_level_id(self) -> str | None:
        for level_id in settings.LEVEL_IDS:
            if not self.is_level_done(level_id):
                return level_id
        return None

    def complete_level(self, level_id: str, time_seconds: float | None = None) -> str | None:
        """Mark a level cleared and return the next one (None on the finale)."""
        self.mark_level_done(level_id, time_seconds)
        return levels.next_level(level_id)

    @property
    def level_count(self) -> int:
        return len(self.levels_done)

    def reset_mission(self) -> None:
        self.mission_started = False
        self.levels_done.clear()
        self.current_level = None
        self.facts.clear()
        self.inventory.clear()
        self.photos = 0
        self.samples = 0
        self.deaths = 0
        self.elapsed = 0.0
        self.outcome = None
        self.best_times.clear()
        # text_scale/volume/muted/show_hints survive a reset on purpose
        save.clear()

    def finish_mission(self, outcome: str) -> None:
        self.outcome = outcome
        self.current_level = None
        self.save()

    # --- persistence --------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "version": save.VERSION,
            "mission_started": self.mission_started,
            "levels_done": list(self.levels_done),
            "current_level": self.current_level,
            "facts": list(self.facts),
            "inventory": list(self.inventory),
            "photos": self.photos,
            "samples": self.samples,
            "deaths": self.deaths,
            "difficulty": self.difficulty,
            "player_name": self.player_name,
            "elapsed": round(self.elapsed, 2),
            "outcome": self.outcome,
            "volume": round(self.volume, 2),
            "muted": self.muted,
            "text_scale": round(self.text_scale, 2),
            "show_hints": self.show_hints,
            "best_times": {key: round(value, 2) for key, value in self.best_times.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        def _list(value) -> list[str]:
            return [str(item) for item in value] if isinstance(value, list) else []

        return cls(
            mission_started=bool(data.get("mission_started", True)),
            levels_done=_list(data.get("levels_done")),
            current_level=data.get("current_level"),
            facts=_list(data.get("facts")),
            inventory=_list(data.get("inventory")),
            photos=int(data.get("photos", 0) or 0),
            samples=int(data.get("samples", 0) or 0),
            deaths=int(data.get("deaths", 0) or 0),
            difficulty=str(data.get("difficulty", "normal")),
            player_name=str(data.get("player_name", "Astronaut"))[:16],
            elapsed=float(data.get("elapsed", 0.0) or 0.0),
            outcome=data.get("outcome"),
            volume=float(data.get("volume", 0.8) or 0.8),
            muted=bool(data.get("muted", False)),
            text_scale=float(data.get("text_scale", 1.0) or 1.0),
            show_hints=bool(data.get("show_hints", True)),
            best_times={
                str(key): float(value)
                for key, value in (data.get("best_times") or {}).items()
            },
        )

    def _copy_from(self, other: "GameState") -> None:
        self.mission_started = other.mission_started
        self.levels_done = other.levels_done
        self.current_level = other.current_level
        self.facts = other.facts
        self.inventory = other.inventory
        self.photos = other.photos
        self.samples = other.samples
        self.deaths = other.deaths
        self.difficulty = other.difficulty
        self.player_name = other.player_name
        self.elapsed = other.elapsed
        self.outcome = other.outcome
        self.volume = other.volume
        self.muted = other.muted
        self.text_scale = other.text_scale
        self.show_hints = other.show_hints
        self.best_times = other.best_times

    def save(self) -> bool:
        return save.write(self.to_dict())

    def load(self) -> bool:
        data = save.read()
        if not data:
            return False

        # preferences survive a version bump; old campaign progress does not
        if int(data.get("version", 0) or 0) != save.VERSION:
            self.volume = max(0.0, min(1.0, float(data.get("volume", self.volume) or 0.8)))
            self.muted = bool(data.get("muted", self.muted))
            self.text_scale = max(0.8, min(1.6, float(data.get("text_scale", self.text_scale) or 1.0)))
            self.difficulty = str(data.get("difficulty", self.difficulty))
            if self.difficulty not in settings.DIFFICULTIES:
                self.difficulty = "normal"
            return False

        self._copy_from(GameState.from_dict(data))
        return True

    # --- derived text -------------------------------------------------------
    def progress_line(self) -> str:
        return (
            f"{self.level_count}/{len(settings.LEVEL_IDS)} levels  |  "
            f"{self.fact_count} facts  |  {self.deaths} losses"
        )

    def status_line(self) -> str:
        return f"{len(self.inventory)}/{max(1, len(self.inventory))} parts  |  {len(self.facts)} facts  |  {self.deaths} losses"

    def mission_line(self) -> str:
        if self.outcome == "win":
            return "Mission complete - Laika is home."
        if self.outcome == "lost":
            return "Laika did not return."
        if self.outcome == "incomplete":
            return "Home, but the survey is unfinished."
        return "Mars survey in progress"

    def science_line(self) -> str:
        return f"{self.photos} photos  |  {self.samples} samples  |  {self.fact_count} facts"
