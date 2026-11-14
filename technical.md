# HOMEBOUND — Technical Documentation

This document describes the architecture and implementation of HOMEBOUND.

## Overview

- **Language:** Python 3.12
- **Engine:** pygame-ce >= 2.5.7 (never plain `pygame`)
- **Resolution:** 1280 x 720, 60 FPS, delta-time based
- **Style:** Data-driven, one-direction data flow, no globals

## Architecture

### Scene / SceneManager / Game

Every screen is a `Scene` with three hooks:

```python
class Scene:
    def handle_events(self, events): ...
    def update(self, dt): ...
    def draw(self, screen): ...
    def on_enter(self, **data): ...
    def on_exit(self): ...
```

`SceneManager` owns the stack (list) and registry of named scenes:

- `switch(name, **data)` — replace the current scene.
- `push(name, **data)` — open an overlay (pause, dialogue focus) while the scene below keeps drawing.
- `pop()` — close the top overlay.
- `reload()` — switch to the current scene again (restart).
- `update(dt)` — forward delta time to the top scene; overlays update too.
- `draw()` — forward to every scene in the stack, top first.

The `Game` container holds the virtual screen surface, the real window, the state, and the manager.
Scenes never touch the window directly; they use the virtual surface and the manager handles scaling.

### GameState

A single shared `GameState` object owns all mutable progress:

- `parts` — list of recovered part names.
- `facts` — list of fact keys learned/logged.
- `deaths` — lifetime death count.
- `difficulty` — `easy` / `normal` / `hard`.
- `current_level` — active level id.
- `elapsed` — total play seconds.
- `tutorial_done` — tutorial completion flag.
- `volume`, `muted` — audio state.

Difficulty is applied through multipliers (speed, time, hearts, hint idle) so no level scene ever
branches on difficulty itself.

## Data Flow

```
data/*.json ──► core.levels.load_level() ──► Scene
                    │
GameState ◄── read/write parts, facts, deaths, difficulty, elapsed
                    │
     ui.HUD / ui.DialogueBox / ui.Meter ──► screen
```

One direction, no module-level mutables.

## Module Guide

| Module | Responsibility |
|---|---|
| `core/settings.py` | Constants, paths, palette, scene names, difficulties. |
| `core/scene.py` | Scene base, SceneManager, Game container. |
| `core/game_state.py` | Single state object, multipliers, persistence hooks. |
| `core/save.py` | Atomic JSON save/load, corrupt-file safe. |
| `core/levels.py` | JSON loading, validation, planet helpers, playable-level queries. |
| `core/assets.py` | Font/image loading with graceful fallbacks. |
| `core/audio.py` | Synthesized SFX, mute, mixer fallback. |
| `core/text.py` | Cached wrapping and text drawing. |
| `core/color.py` | Hex parsing and color math. |
| `scenes/` | Boot, menu, map, pause, tutorial, mars, mercury, venus, ending. |
| `entities/` | Player, pickups, hazards, enemies (as built). |
| `ui/` | HUD, dialogue box, meter, button, pause overlay, stats. |
| `art/` | Procedural sprites, planets, backgrounds. |
| `data/` | Levels, planets, dialogue, APOC cache. |
| `tools/` | `fetch_apod.py` — one-time NASA APOC cache. |

## Engineering Rules

1. Delta time everywhere — no `time.sleep`, no frame-counted timers.
2. No blocking calls in the loop; async-friendly `main()` so pygbag stays possible.
3. All numbers in JSON; no hardcoded gameplay numbers in scenes.
4. One `GameState`; scenes read/write through its public API only.
5. Asset paths only through `core.assets.path()`; missing asset = fallback shape, never a crash.
6. `main` must always launch; merge only at gates; a broken `main` is the only emergency.
7. 60 FPS target; profile any scene under 45 FPS and note the heavy moment.

## Save System

- File: `savegame.json` next to the game, atomically written via temp file + rename.
- Wrapped in try/except; corrupt or missing saves never block startup.
- Saved: parts, facts, deaths, difficulty, current level, elapsed, tutorial flag, volume, mute.

## Adding a New Level

1. Add level JSON under `data/levels/<id>.json`.
2. Add planet entry under `data/planets.json` with `playable`, `part`, `map_position`, `fact`, `facts`, `unlock`.
3. Register the scene in `main.py`.
4. Wire dialogue under `data/dialogue/<id>.json`.
5. Update HUD objective and unlock rules through `GameState`.

Bad JSON produces a readable `DataError`, not a traceback mid-frame.

## Build and Run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`; install `pygame-ce`.
