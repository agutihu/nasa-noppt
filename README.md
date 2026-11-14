# HOMEBOUND

A solar system repair mission — NASA Space Apps Challenge 2026

A stranded pilot must cross the solar system, recover three ship parts, and fly home.
Every level is built on one real planetary fact, and that fact is the mechanic:

*   **Mars** — 3.71 m/s² gravity (38% of Earth) makes you jump long and floaty; dust storms cut visibility.
*   **Mercury** — 430 °C day / −180 °C night; outrun the sweeping sun line and hide in crater shadows while a heat meter rises.
*   **Venus** — 92 × Earth pressure and 465 °C heat; collect three hull fragments in 90 seconds before the pressure meter fills.
*   **Earth** — drag the recovered parts onto the ship, recap the facts, land.

Laila, the ship's navigation core, guides the player with dialogue and hints. Cached NASA APOD data appears on the boot screen so the game runs fully offline.

The full playable arc — tutorial, Mars, Mercury, Venus, Earth finale — is implemented, and the whole loop was verified end-to-end with a scripted headless playtest.

Target play time: about 14 minutes, so a judge can see the full arc in one sitting.

## What this project is

HOMEBOUND is an educational space game made for the NASA Space Apps Challenge 2026 hackathon.

The idea: space is hostile, and each planet's hostility becomes a playable rule. Instead of a quiz, the player *experiences* planetary science — low gravity on Mars, extreme temperature swings on Mercury, crushing pressure on Venus — while recovering the parts needed to repair their ship and return to Earth.

## Features

### Gameplay

*   Five levels implemented: Earth orbit tutorial, Mars platformer, Mercury stealth, Venus timed survival, Earth assembly finale.
*   Each level teaches one verified NASA fact; facts are displayed on the solar map and recapped at the end.
*   Laila dialogue system with typewriter text, queued lines, idle hints, and death-based hints.
*   Part-collection loop with persistent save/load (progress survives a restart).
*   Difficulty settings (Easy / Normal / Hard) that scale hazard speed, timer length, hearts, and hint frequency.
*   Pause overlay (Resume / Restart / Mute / Quit to map) available in every scene.
*   Solar system map hub with playable missions and read-only "Data Archive" fact cards for Jupiter, Saturn, Uranus, and Neptune.
*   Stats screen at the end: mission time, losses, parts recovered, facts learned.

### Technical

*   Python 3.12 with pygame-ce (never plain `pygame`).
*   1280 × 720, 60 FPS, delta-time movement (identical behavior at 30 and 60 FPS).
*   Fully data-driven: all numbers, dialogue, and facts live in JSON under `data/`.
*   Procedural art drawn in code — the game runs with an empty `assets/` folder.
*   Synthesized sound effects generated at runtime — no audio files required, silent fallback if the mixer is unavailable.
*   Cached NASA APOD on the boot screen; the game never needs internet to run.
*   Async-friendly main loop so a pygbag web build remains possible (desktop is the demo target).
*   Graceful fallbacks everywhere: missing JSON, missing assets, missing audio, corrupt save — nothing crashes the game.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12 | Pinned for `pygame-ce` wheel compatibility |
| Game library | pygame-ce >= 2.5.7 | Faster, maintained, better pygbag support than plain `pygame` |
| Rendering | Procedural `pygame.draw` primitives | Zero asset blocking; consistent retro look |
| Audio | Runtime synthesis | No audio files; silent fallback on any device |
| Data | JSON (`data/levels`, `data/planets`, `data/dialogue`) | Non-coders can retune numbers and dialogue |
| Save | JSON file next to the game (`savegame.json`) | Atomic write; corrupt saves never block startup |
| Window | 1280 × 720, 60 FPS, resizable with letterbox scaling | One target for all art and layouts |

## Project structure

```
HOMEBOUND/
├── main.py                     # Async main loop, window, scene bootstrap
├── requirements.txt            # pygame-ce
├── README.md
├── design.md
├── technical.md
├── playguide.md
├── .gitignore
│
├── core/                       # Engine
│   ├── settings.py             # Constants, paths, palette, scene names
│   ├── scene.py                # Scene base + SceneManager + Game
│   ├── game_state.py           # Single GameState: parts, facts, difficulty, save/load
│   ├── save.py                 # Atomic JSON save/load
│   ├── levels.py               # JSON loader + validation + playable-level helpers
│   ├── assets.py               # Font/image loading with graceful fallback
│   ├── audio.py                # Synthesized SFX, mute, no-crash if mixer missing
│   ├── text.py                 # Cached text wrapping + drawing
│   └── color.py                # Hex parsing + color math
│
├── scenes/                     # Screens
│   ├── boot.py                 # APOD splash screen
│   ├── menu.py                 # Title menu + settings
│   ├── map.py                  # Solar system hub, unlocks, archive cards
│   ├── tutorial.py             # Earth orbit tutorial
│   ├── mars.py                 # Mars platformer
│   ├── mercury.py              # Mercury stealth
│   ├── venus.py                # Venus timed survival
│   └── ending.py               # Earth assembly finale
│
├── entities/                   # Gameplay objects
│   ├── player.py               # Shared health/damage + top-down + platformer controllers
│   ├── pickups.py              # Parts, health, canisters, fragments, crates
│   └── enemies.py              # Chaser, Patrol, Turret, Projectile
│
├── ui/                         # UI widgets
│   ├── hud.py                  # Hearts, parts inventory, timer, objective
│   ├── dialogue_box.py         # Laila's typewriter dialogue + hints
│   ├── meter.py                # Heat / pressure / fuel meters
│   ├── button.py               # Mouse + keyboard buttons
│   └── pause.py                # Pause overlay
│
├── art/                        # Procedural drawing helpers
│   ├── sprites.py              # Astronaut, Laila hologram, ship, drone, part icon, heart
│   ├── planets.py              # Planet discs, bands, craters, rings, sun, orbits
│   └── backgrounds.py          # Starfields, nebulae, vignette, scanlines
│
├── data/                       # All gameplay content
│   ├── planets.json            # Map data, facts, unlock rules, archive cards
│   ├── levels/
│   │   ├── tutorial.json
│   │   ├── mars.json
│   │   ├── mercury.json
│   │   └── venus.json
│   ├── dialogue/
│   │   ├── tutorial.json
│   │   ├── mars.json
│   │   ├── mercury.json
│   │   └── venus.json
│   └── cache/
│       └── apod.json           # Cached NASA APOD (offline fallback)
│
├── assets/                     # Optional; game runs without any of these
│   └── fonts/
│       ├── PressStart2P-Regular.ttf
│       └── VT323-Regular.ttf
│
└── tools/                      # Dev / QA tools
    ├── fetch_apod.py           # Caches NASA APOD once; committed result keeps game offline
    ├── playtest.py             # Scripted end-to-end playtest of the full loop
    └── smoke_test.py           # Headless smoke test: boot every scene, run frames
```

## Levels and mechanics (real planetary facts)

| # | Level | Style | Real mechanic | Part recovered | Est. time |
|---|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial | Movement, interact, hint button | — (meet Laila) | 1 min |
| 1 | Mars | Platformer | 3.71 m/s² gravity → floaty long jumps; dust storm dims screen to a 120 px visibility circle every 25 s | Navigation Module | 4 min |
| 2 | Mercury | Top-down stealth | 430 °C day / −180 °C night → sun line sweeps, heat meter, hide in crater shadow | Solar Panel Array | 4 min |
| 3 | Venus | Timed survival | 465 °C, 92 bar pressure → pressure meter rises; cooling canisters slow it; 90 s limit | Hull Plating | 3 min |
| 6 | Earth | Assembly + stats | Drag 3 parts onto the ship; each snaps with its planet fact; stats screen | — (ending) | 2 min |

Jupiter, Saturn, Uranus, and Neptune appear as read-only "Data Archive" fact cards on the solar map — their facts stay in the game without building separate levels.

Total play time ≈ 14 minutes.

## Player flow

```
Boot (APOD splash, cached)
  → Menu (New mission / Continue / Settings / Quit)
    → Solar map (hub; shows parts collected, unlocks)
        → Tutorial (auto on first run)
        → Mars | Mercury | Venus (any order, unlocked after tutorial)
        → Earth finale (unlocked when all 3 parts collected)
    → Stats screen → Menu (or New Game)
```

*   Any planet can be replayed; parts are per-part flags, not counts.
*   Pause overlay works in every scene (Esc): Resume / Restart / Mute / Quit to map.
*   Progress auto-saves on part pickup and on scene change; "Continue" loads it.

## Controls

| Action | Key |
|---|---|
| Move | WASD / arrow keys |
| Jump (Mars platformer) | Space (hold for higher) |
| Pick up / interact | Walk into the item (proximity) |
| Laila hint | H |
| Advance dialogue | Space / Enter / click / E |
| Pause | Esc |
| Menu navigation | Up/Down + Enter, or mouse |

## How to run

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`; use `pygame-ce`.

The game opens at 1280 × 720 and runs fully offline — no internet or asset files required.

Optional boot-screen cache refresh:

```bash
python tools/fetch_apod.py
```

## Testing and tools

```bash
python tools/smoke_test.py   # headless smoke test: boot every scene, run frames, report
python tools/playtest.py     # scripted end-to-end playtest of the full game loop
python tools/fetch_apod.py  # one-time NASA APOD cache
```

See [TOOLS.md](TOOLS.md) for details.

## Team

*   **Sanghaar** — Lead, gameplay & content: levels, entities, data, art primitives, Laila's script.
*   **Sulaiman** — Engine & shell: scene manager, GameState, save, UI, audio, map, boot, menu, ending.
*   **Story and level design:** Victoria and team.

## NASA data & attribution

*   Planetary facts are drawn from NASA fact sheets (Mars, Mercury, Venus, Earth, Jupiter, Saturn, Uranus, Neptune) and verified before submission.
*   Boot screen uses NASA's Astronomy Picture of the Day (APOD), cached to `data/cache/apod.json` via `tools/fetch_apod.py`. If the fetch fails or there is no internet, a committed offline fallback keeps the game running.
*   All art and audio are procedural — generated in code, no external asset files required.

---

HOMEBOUND — every mechanic is a real planetary fact. Cached so it runs offline.
