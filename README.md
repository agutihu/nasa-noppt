HOMEBOUND
=========

A solar system repair mission — NASA Space Apps Challenge 2026

A stranded pilot must cross the solar system, recover three ship parts, and fly home.
Every level is built on one real planetary fact, and that fact is the mechanic:

*   **Mars** — 3.71 m/s² gravity (38% of Earth) makes you jump long and floaty; dust storms cut visibility.
*   **Mercury** — 430 °C day / −180 °C night; outrun the sweeping sun line and hide in crater shadows while a heat meter rises.
*   **Venus** — 92 × Earth pressure and 465 °C heat; collect three hull fragments in 90 seconds before the pressure meter fills.
*   **Earth** — drag the recovered parts onto the ship, recap the facts, land.

Laila, the ship's navigation core, guides the player with dialogue and hints. Cached NASA APOD data appears on the boot screen so the game runs fully offline.

Target play time: about 14 minutes, so a judge can see the full arc in one sitting.

---------------------------------------------------------------
FEATURES
---------------------------------------------------------------

Gameplay
*   Five levels: Earth orbit tutorial, Mars platformer, Mercury stealth, Venus timed survival, Earth assembly finale.
*   Each level teaches one verified NASA fact; facts are displayed on the solar map and recapped at the end.
*   Laila dialogue system with typewriter text, queued lines, idle hints, and death-based hints.
*   Part-collection loop with persistent save/load (progress survives a restart).
*   Difficulty settings (Easy / Normal / Hard) that scale hazard speed, timer length, hearts, and hint frequency.
*   Accessibility: text-size toggle (Normal / Large), mute, pause anywhere, difficulty scaling, hazards coded with colour AND shape.
*   Pause overlay (Resume / Restart / Mute / Quit to map) available in every scene.
*   Solar system map hub with playable missions and read-only "Data Archive" fact cards for Jupiter, Saturn, Uranus, and Neptune.
*   Stats screen at the end: time, deaths, parts recovered, facts learned.

Technical
*   Python 3.12 with pygame-ce (never plain `pygame`).
*   1280 × 720, 60 FPS, delta-time movement (identical behavior at 30 and 60 FPS).
*   Fully data-driven: all numbers, dialogue, and facts live in JSON under `data/`.
*   Procedural art drawn in code — the game runs with an empty `assets/` folder.
*   Synthesized sound effects generated at runtime — no audio files required, silent fallback if the mixer is unavailable.
*   Cached NASA APOD on the boot screen; the game never needs internet to run.
*   Async-friendly main loop so a pygbag web build remains possible (desktop is the demo target).
*   Graceful fallbacks everywhere: missing JSON, missing assets, missing audio, corrupt save — nothing crashes the game.

---------------------------------------------------------------
TECH STACK
---------------------------------------------------------------

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12+ (tested on 3.14) | `pygame-ce` ships wheels for current CPython |
| Game library | pygame-ce >= 2.5.7 | Faster, maintained, better pygbag support than plain `pygame` |
| Rendering | Procedural `pygame.draw` primitives | Zero asset blocking; consistent retro look |
| Audio | Runtime synthesis | No audio files; silent fallback on any device |
| Data | JSON (`data/levels`, `data/planets`, `data/dialogue`) | Non-coders can retune numbers and dialogue |
| Save | JSON file next to the game (`savegame.json`) | Atomic write; corrupt saves never block startup |
| Window | 1280 × 720, 60 FPS, resizable with letterbox scaling | One target for all art and layouts |

---------------------------------------------------------------
PROJECT STRUCTURE
---------------------------------------------------------------

```
HOMEBOUND/
├── main.py                     # Async main loop, window, scene bootstrap
├── requirements.txt            # pygame-ce
├── README.md                   # This file
│
├── core/                       # Engine
│   ├── settings.py             # Constants, paths, palette, scene names
│   ├── scene.py                # Scene base + SceneManager (switch/push/pop/reload)
│   ├── game_state.py           # Single GameState: parts, facts, difficulty, save/load
│   ├── save.py                 # Atomic JSON save/load
│   ├── levels.py               # JSON loader + validation + playable-level helpers
│   ├── assets.py               # Font/image loading with graceful fallback
│   ├── audio.py                # Synthesized SFX, mute, no-crash if mixer missing
│   ├── text.py                 # Cached text wrapping + shadowed drawing
│   └── color.py                # Hex parsing, color mixing/scaling
│
├── scenes/                     # Screens
│   ├── boot.py                 # APOD splash screen
│   ├── menu.py                 # Title menu + settings (difficulty, volume, mute)
│   ├── map.py                  # Solar system hub, unlocks, archive cards
│   ├── pause.py                # Pause overlay
│   ├── tutorial.py             # Earth orbit tutorial
│   ├── mars.py                 # Mars platformer
│   ├── mercury.py              # Mercury stealth
│   ├── venus.py                # Venus timed survival
│   └── ending.py               # Earth assembly finale
│
├── entities/                   # Gameplay objects
│   ├── player.py               # Shared health/damage + top-down + platformer controllers
│   └── pickups.py              # Parts, health, canisters, fragments
│
├── ui/                         # UI widgets
│   ├── hud.py                  # Hearts, parts inventory, timer, objective
│   ├── dialogue_box.py         # Laila's typewriter dialogue + hints
│   ├── meter.py                # Heat / pressure / fuel meters
│   └── button.py               # Mouse + keyboard buttons
│
├── art/                        # Procedural drawing helpers
│   ├── sprites.py              # Astronaut, Laila hologram, ship, drone, part icon, heart
│   ├── planets.py              # Planet discs, bands, craters, rings, sun, orbits
│   └── backgrounds.py          # Starfields, nebulae, vignette, scanlines
│
├── data/                       # All gameplay content
│   ├── planets.json            # Map data, facts, unlock rules, archive cards
│   ├── levels/
│   │   └── tutorial.json       # Earth orbit tutorial level
│   ├── dialogue/
│   │   └── tutorial.json       # Laila's tutorial lines
│   └── cache/
│       └── apod.json           # Cached NASA APOD (offline fallback)
│
├── assets/                     # Optional; game runs without any of these
│   └── fonts/
│       ├── PressStart2P-Regular.ttf
│       └── VT323-Regular.ttf
│
└── tools/                      # Build-time helpers
    ├── fetch_apod.py           # Caches NASA APOD once; committed result keeps game offline
    ├── smoke_test.py           # Headless boot test of every scene (CI-friendly)
    └── playtest.py             # Scripted end-to-end run of the full game loop```

---------------------------------------------------------------
LEVELS AND MECHANICS (REAL PLANETARY FACTS)
---------------------------------------------------------------

| # | Level | Style | Real mechanic | Part recovered | Est. time |
|---|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial | Movement, interact, hint button | — (meet Laila) | 1 min |
| 1 | Mars | Platformer | 3.71 m/s² gravity → floaty long jumps; dust storm dims screen to a 120 px visibility circle every 25 s | Navigation Module | 4 min |
| 2 | Mercury | Top-down stealth | 430 °C day / −180 °C night → sun line sweeps, heat meter, hide in crater shadow | Solar Panel Array | 4 min |
| 3 | Venus | Timed survival | 465 °C, 92 bar pressure → pressure meter rises; cooling canisters slow it; 90 s limit | Hull Plating | 3 min |
| 6 | Earth | Assembly + stats | Drag 3 parts onto the ship; each snaps with its planet fact; stats screen | — (ending) | 2 min |

Jupiter, Saturn, Uranus, and Neptune appear as read-only "Data Archive" fact cards on the solar map — their facts stay in the game without building separate levels.

Total play time ≈ 14 minutes.

Verified facts used:

| Key | Fact |
|---|---|
| mars_gravity | Mars has about 38% of Earth's gravity (3.71 m/s²) |
| mars_dust_storms | Dust storms can cover the whole planet for weeks |
| mercury_temps | Day ~430 °C, night ~−180 °C |
| mercury_atmosphere | Almost no atmosphere to hold heat |
| venus_pressure | Surface pressure ~92 × Earth |
| venus_temp | Surface ~465 °C, hotter than Mercury |
| earth_home | 1 g gravity, 1 bar pressure, breathable atmosphere |
| jupiter_grs | The Great Red Spot is a storm wider than Earth |
| jupiter_radiation | Radiation belts would fry an unshielded spacecraft |
| saturn_rings | Rings are mostly water ice, extremely thin compared to their width |
| uranus_tilt | Rotates on its side; ~42 years sunlight then ~42 years darkness per pole |
| neptune_winds | Fastest winds in the solar system, over 2,000 km/h |

---------------------------------------------------------------
PLAYER FLOW
---------------------------------------------------------------

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

---------------------------------------------------------------
CONTROLS
---------------------------------------------------------------

| Action | Key |
|---|---|
| Move | WASD / arrow keys |
| Jump (Mars platformer) | Space (hold for higher) |
| Interact / pick up | E |
| Laila hint | H |
| Advance dialogue | Space / Enter / click |
| Pause | Esc |
| Menu navigation | Up/Down + Enter, or mouse |

---------------------------------------------------------------
HOW TO RUN
---------------------------------------------------------------

Prerequisites: Python 3.12+ (3.11–3.14 all work). Do not install plain `pygame` — use `pygame-ce`.

```bash
# 1. Clone the repository
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify pygame-ce (not plain pygame)
python -c "import pygame; print(pygame.version.ver)"

# 5. Run the game
python main.py
```

The game opens a 1280 × 720 window. It runs fully offline — no NASA API key, no internet connection, and no asset files are required.

Optional: cache a fresh NASA APOD image for the boot screen:

```bash
python tools/fetch_apod.py
```

---------------------------------------------------------------
TEAM
---------------------------------------------------------------

*   **Sanghaar** — Lead, gameplay & content: levels, entities, data, art primitives, Laila's script.
*   **Sulaiman** — Engine & shell: scene manager, GameState, save, UI, audio, map, boot, menu, ending.
*   **Story and level design:** Victoria and team.

---------------------------------------------------------------
NASA DATA & ATTRIBUTION
---------------------------------------------------------------

*   Planetary facts are drawn from NASA fact sheets (Mars, Mercury, Venus, Earth, Jupiter, Saturn, Uranus, Neptune) and verified before submission.
*   Boot screen uses NASA's Astronomy Picture of the Day (APOD), cached to `data/cache/apod.json` via `tools/fetch_apod.py`. If the fetch fails or there is no internet, a committed offline fallback keeps the game running.
*   All art and audio are procedural — generated in code, no external asset files required.

---------------------------------------------------------------

HOMEBOUND — every mechanic is a real planetary fact. Cached so it runs offline.
