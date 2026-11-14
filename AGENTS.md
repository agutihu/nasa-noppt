# AGENTS.md — Homebound

Compact agent instructions for the HOMEBOUND repository (NASA Space Apps 2026 game).

## Commands

- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run: `python main.py` — Python 3.12, **pygame-ce** (never plain `pygame`).
- Smoke test (headless): `python tools/smoke_test.py`
- Full-loop playtest (headless): `python tools/playtest.py`
- APOD cache: `python tools/fetch_apod.py`

Headless tools set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` internally.

## Architecture essentials

- One `GameState` owns progress (parts, facts, deaths, difficulty, save/load). Scenes use its public API only; no module-level mutables.
- Scene contract: `handle_events`, `update(dt)`, `draw(screen)`, optional `on_enter`/`on_exit`. Manager: `switch`, `push`, `pop`, `reload`.
- Gameplay numbers live in JSON under `data/` — no hardcoded gameplay numbers in scenes.

## Conventions / gotchas

- Delta time everywhere; no `time.sleep`; async-friendly `main()` keeps the pygbag path possible.
- Art and audio are fully procedural/synthesized; game runs with empty `assets/` and no audio files.
- Missing data/assets/audio/save → graceful fallback, never crash.
- Required parts for the ending: `Navigation Module`, `Solar Panel Array`, `Hull Plating`.
- Pickups are proximity-based (walk into); `E` advances dialogue, not pickup.

## Docs

- `README.md` is the main doc; see `DOCS.md` for the full documentation map.

Keep this file short. Detail lives in the sibling docs (`design.md`, `technical.md`, `playguide.md`, `TOOLS.md`, `SCIENCE.md`, `DATA.md`, `HACKATHON.md`, `CONTRIBUTING.md`).
