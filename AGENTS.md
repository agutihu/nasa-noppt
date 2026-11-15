# AGENTS.md — LAIKA: MARS MISSION

Compact instructions for the HOMEBOUND repository (NASA Space Apps 2026 game).

## ⚠️ Critical Fixes (learned the hard way)

| Issue | Fix | Why it matters |
|-------|-----|----------------|
| `register_mission_scenes` not importable from `core.levels` | Import from `scenes.briefing` in `main.py` | Game crashes on launch with `NameError` |
| `tutorial_done` attribute missing from `GameState` | Add `tutorial_done: bool = False` | Planets stay locked after tutorial win |
| `is_unlocked()` only checks `LEVEL_IDS` sequence | Also check `self.tutorial_done` for non-LEVEL_IDS planets | Map planets remain locked after completing tutorial |
| `has_part()` method missing from `GameState` | Add `has_part(self, part_id)` method | Inventory/part checking fails |
| Modal dialogue box not closable | Add X button + outside-click close in `ui/modal.py` | Player cannot dismiss failure/warning panels |
| `previous_mission()` function missing | Add to `core/levels.py` | Level navigation breaks |

## 🎯 Core Commands

- `python tools/smoke_test.py` — All 14 scenes + ending must output `ok` and `all scenes ok`
- `python main.py` — Launch the game (Python 3.12, **pygame-ce**, never plain `pygame`)
- `python tools/playtest.py` — Full-loop headless playtest
- `python tools/fetch_apod.py` — **Only needs to be run once** to cache APOD; game uses cached `data/cache/apod.json` thereafter

Headless tools set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` internally.

## 📁 Key Directories

| Directory | What's inside |
|-----------|--------------|
| `core/` | `GameState` (save/load, outcome tracking, difficulty, facts, inventory/parts), `is_unlocked()`, `has_part()`, `complete_level()`, `mark_level_done()` |
| `scenes/` | 14 scene files + ending: `boot.py`, `menu.py`, `tutorial.py`, `briefing.py`, `map.py`, `level1-4.py`, `ending.py`, `world_level.py` |
| `data/levels/` | Per-level JSON configs (difficulty, time limits, required parts) |
| `data/dialogue/` | Laika dialogue lines (`mars.json`) |
| `ui/` | Modal system (`modal.py`) with X button and outside-click close |
| `entities/` | Player, pickups, enemies, world objects |
| `art/` | Procedural generation: backgrounds, sprites, planets, worlds, environments |
| `tools/` | Smoke test, playtest, APOD fetch, world/map screenshots |

## 🎮 Gameplay Mechanics

- **4-level campaign**: Outpost → Landing → Surface → Lava Tunnel (sequential unlock)
- **3 endings**: Win (Laika survives + mission complete) / Incomplete (Laika returns unfinished) / Lost (Laika does not return)
- **Difficulty**: Easy (5 hearts, +25% time, hints always) / Normal / Hard (2 hearts, −15% time, hints on request only)
- **Food management**: Wrong food = restart mission; other tasks = retry task
- **Pickups**: Proximity-based (walk into); `E` fires blaster in worlds; `E`/`Space` advances dialogue
- **All gameplay numbers from `data/levels/*.json`** — no hardcoded values
- **100% procedural art/audio** — game runs with empty `assets/` folder

## ⚠️ Conventions / Gotchas

- Delta time everywhere; no `time.sleep`; async-friendly `main()`
- Missing data/assets/audio/save → graceful fallback, never crash
- Required parts for ending: the seven names in `data/planets.json`
  (Solar Panel Array, Hull Plating, Navigation Module, Shield Generator, Fuel Cells, Thermal Regulator, Signal Antenna)
- `is_unlocked(level_id)`: index 0 always unlocked; others require previous level in `self.levels_done`
  **Exception**: tutorial-level planet unlocks also require `self.tutorial_done`
- Modal close: X button in top-right + outside-click closes; do not rely on clicking "empty space"
- `tutorial_done` must be set to `True` when tutorial completes (in `tutorial.py:_win_done`)
- `previous_mission(planet_id)`: supports navigation back through the campaign

## 📚 Documentation (10 files, all in sync per DOCS.md)

- `README.md` — Main project overview
- `DOCS.md` — Full documentation map
- `design.md` — Game design document
- `technical.md` — Technical implementation
- `playguide.md` — Player guide
- `SCIENCE.md` — Science systems (RADLAB, DONKI, OSDR, MARS TREK)
- `DATA.md` — Game data structures
- `TOOLS.md` — Development tools and workflow
- `HACKATHON.md` — NASA Space Apps Challenge guidelines
- `CONTRIBUTING.md` — How to contribute

Plus: `LAIKA_MARS_MISSION_Project_Journey.docx` (word journey document)

## ✅ Verification

- `python tools/smoke_test.py` → `all scenes ok` (14 scenes + ending)
- All 10 documentation files verified
- GitHub `origin/main` pushed with 43 files changed
- APOD cached offline in `data/cache/apod.json`