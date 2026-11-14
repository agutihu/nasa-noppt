# HOMEBOUND — Player Guide

A guide for playing HOMEBOUND.

## Welcome

You are the pilot. The ship is damaged. Laila, the navigation core, is guiding you home. Three
critical parts are scattered across the solar system — recover them and the ship can be rebuilt.

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

The game opens at 1280 x 720. Fully offline — no internet or asset files required.

Optional boot-screen cache refresh:

```bash
python tools/fetch_apod.py
```

## Controls

| Action | Key |
|---|---|
| Move | WASD / arrow keys |
| Jump (Mars platformer) | Space (hold for higher) |
| Interact / pick up | E |
| Laila hint | H |
| Advance dialogue | Space / Enter / click |
| Pause | Esc |
| Menu navigation | Up/Down + Enter, or mouse |

## Gameplay

### Flow

```
Boot (APOD splash) → Menu → Solar map → Level → Stats → Menu
```

The solar map is the hub. Playable planets unlock after the tutorial. The Earth finale unlocks
when all required parts are collected.

### Level Objectives

| # | Level | Objective |
|---|---|---|
| 0 | Earth orbit | Learn movement, interaction, and Laila's hint. Meet Laila. |
| 1 | Mars | Reach the lander wreck and recover the Navigation Module. |
| 2 | Mercury | Cross the sunlit surface to the outpost, recover the Solar Panel Array. |
| 3 | Venus | Collect fragments and escape within the time limit. |
| 6 | Earth | Assemble the ship with recovered parts; land; view stats. |

Jupiter, Saturn, Uranus, and Neptune appear as read-only fact cards.

## Laila and Hints

- Dialogue advances with Space / Enter / click, or by clicking.
- Laila types out lines at a steady pace.
- Press `H` at any time for a hint from Laila.
- Idle hints trigger after a delay; death-based hints trigger after repeated failures.
- Hints are readable at 1280 x 720.

## Difficulty

- **Easy** — 5 hearts, slower hazards, +25% time, frequent hints.
- **Normal** — 3 hearts, standard hazards, standard time, standard hints.
- **Hard** — 2 hearts, faster hazards, -15% time, hints on request only.

Difficulty applies to the next mission launched and persists.

## Save and Continue

- Progress auto-saves on part pickup and scene change.
- "Continue" loads the latest save from the menu.

## Troubleshooting

- Game will not start: confirm Python 3.12, `pip install pygame-ce`, and use `python main.py`.
- Window resize: handled with letterbox scaling.
- Missing assets: the game runs with fallbacks; no crash expected.
- No sound: mixer may be unavailable; mute/volume settings still work.
