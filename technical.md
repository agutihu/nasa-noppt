# HOMEBOUND — Technical Documentation

This document describes the architecture and implementation of HOMEBOUND.

## Overview

- **Language:** Python 3.12
- **Engine:** pygame-ce >= 2.5.7 (never plain `pygame`)
- **Resolution:** 1280 × 720, 60 FPS, delta-time based
- **Style:** Data-driven, one-direction data flow, no module-level mutables

## Architecture

### Scene / SceneManager / Game

Every screen is a `Scene` with hooks:

```python
class Scene:
    def handle_events(self, events): ...
    def update(self, dt): ...
    def draw(self, screen): ...
    def on_enter(self, **data): ...
    def on_exit(self): ...
```

`SceneManager` owns a stack and a name registry:

- `switch(name, **data)` — replace the current scene.
- `push(name, **data)` — open an overlay (pause) while the scene below keeps drawing.
- `pop()` — close the top overlay.
- `reload()` — switch to the current scene (restart).
- `update(dt)` — forward delta time to the top scene; overlays update too.
- `draw()` — forward to every scene in the stack, top first.

The `Game` container holds the virtual screen surface, the real window, the state, and the manager.
Scenes use the virtual surface; the manager handles window scaling.

### GameState

A single shared `GameState` owns all mutable progress:

- `parts`, `facts`, `deaths`, `difficulty`, `current_level`, `elapsed`, `tutorial_done`, `volume`, `muted`.

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
| `core/assets.py` | Font/image loading with graceful fallback. |
| `core/audio.py` | Synthesized SFX, mute, mixer fallback. |
| `core/text.py` | Cached text wrapping + drawing. |
| `core/color.py` | Hex parsing + color math. |
| `scenes/` | boot, menu, map, tutorial, mars, mercury, venus, ending. |
| `entities/` | player, pickups, enemies. |
| `ui/` | hud, dialogue_box, meter, button, pause. |
| `art/` | sprites, planets, backgrounds. |
| `data/` | planets, levels, dialogue, APOD cache. |
| `tools/` | fetch_apod, playtest, smoke_test. |

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

## HUD and Dialogue Contracts

- `HUD` owns hearts, parts inventory, timer, and objective text. Levels never draw hearts.
- `DialogueBox` owns all Laila text: typewriter, queue, hint mode, advance keys (Space/Enter/
  click). While active, gameplay updates are frozen except dialogue.
- `Meter` owns value for heat / pressure / fuel; levels set values through `set`.

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

## Tools

| Tool | Purpose |
|---|---|
| `tools/smoke_test.py` | Headless smoke test: registers every scene, runs frames, reports failures. |
| `tools/playtest.py` | Scripted end-to-end playtest: tutorial → Mars storm/part → Mercury heat/part → Venus fragments/exit → map unlock → ending assemble/stats. |
| `tools/fetch_apod.py` | One-time NASA APOD fetch + cache to `data/cache/apod.json` / `apod.jpg`. |

Run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` (the scripts set these themselves).

See [TOOLS.md](TOOLS.md) for usage details.
