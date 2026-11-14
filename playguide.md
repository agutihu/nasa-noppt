# HOMEBOUND — Player Guide

A guide for playing HOMEBOUND.

## Welcome

You are the pilot. The ship is damaged. Laika, the navigation core, is guiding you home. Seven
critical parts are scattered across seven worlds — recover them all and the ship can be rebuilt.

Every level is built on a real NASA planetary fact. The fact is the mechanic.

## Installation

Requirements: Python 3.12 (3.11 also works).

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`. Use `pygame-ce`.

## Running

```bash
python main.py
```

The game opens at 1280 × 720 and runs fully offline — no internet or asset files required.

Optional boot-screen cache refresh:

```bash
python tools/fetch_apod.py
```

## Controls

| Action | Key |
|---|---|
| Move | WASD / arrow keys |
| Jump | Space (hold for higher) |
| Fire blaster | E |
| Pick up / interact | Walk into the item (proximity) |
| Laika hint | H |
| Advance dialogue | Space / Enter / click |
| Pause | Esc |
| Menu navigation | Up/Down + Enter, or mouse |

## Gameplay

### Flow

```
Boot (APOD splash) → Menu → Solar map → Level → Stats → Menu
```

The solar map is the hub. Missions unlock one after another — win a world and the next
padlock opens. The Earth finale unlocks when all seven parts are collected.

### Level Objectives

| # | Level | Objective |
|---|---|---|
| 0 | Earth orbit | Learn movement, interaction, and Laika's hint. Meet Laika. Tasks: fly to beacon → collect bracket crate → press H. |
| 1 | Mercury | Cross the regolith and recover the Solar Panel Array. The sun line sweeps the surface — stay in shadow. |
| 2 | Venus | Fight through acid rain and geysers to recover the Hull Plating. |
| 3 | Mars | Reach the lander wreck and recover the Navigation Module. Low gravity + dust storms that drop visibility. |
| 4 | Jupiter | Ride the storm platforms above the cloud decks and recover the Shield Generator. |
| 5 | Saturn | Cross the floating moonlets under ring-debris showers and recover the Fuel Cells. |
| 6 | Uranus | Navigate the tilted haze and sideways rain to recover the Thermal Regulator. |
| 7 | Neptune | Push against supersonic winds and recover the Signal Antenna. |
| 8 | Earth | Assemble the ship with all seven parts; launch; view stats. |

Every world has a mission briefing card before launch, a circular minimap in the top-right
corner, a stopwatch (no time limit — it only records how long you took), mid-level
checkpoints, and a labeled part on a pedestal. Ground aliens charge you, patrol saucers fire
plasma; press E to fire your blaster, or jump on a walker to crush it.

## Laika and Hints

- Dialogue advances with Space / Enter / click, or by clicking.
- Laika types out lines at a steady pace.
- Press `H` at any time for a hint from Laika.
- Idle hints trigger after a delay; death-based hints trigger after repeated failures.
- Hints are readable at 1280 × 720.

## Difficulty

- **Easy** — 5 hearts, slower enemies and hazards, gentler storm timing, frequent hints.
- **Normal** — 3 hearts, standard enemies, hazards, and storm timing.
- **Hard** — 2 hearts, faster enemies and hazards, tighter storm timing, hints on request only.

Difficulty applies to the next mission launched and persists.

## Save and Continue

- Progress auto-saves on part pickup and scene change.
- "Continue" loads the latest save from the menu.

## Troubleshooting

- Game will not start: confirm Python 3.12, `pip install pygame-ce`, and use `python main.py`.
- Window resize: handled with letterbox scaling.
- Missing assets: the game runs with fallbacks; no crash expected.
- No sound: mixer may be unavailable; mute/volume settings still work.
