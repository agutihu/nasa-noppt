# HOMEBOUND

A Junior Astronaut Mission Trainer for NASA Space Apps Challenge 2026.

## Overview

Today you are going to help with a really important mission, gathering information about Mars. 
Your base will be the martian output where you and Laika, a robotic dog, will gather information about invisible solar radiation, solar storms, environmental hazards, and possible signs of life, and take important decisions to secure your safety and from the mission.

**Hint:** There is a vending machine with a lot of items the you can take out, to help you during the mission

The game consists of a journey to Mars without landing on its surface. Instead, we will send a robotic dog named Laika, whose mission is to collect information about invisible solar radiation, solar storms, environmental hazards, and possible signs of life. Laika will be responsible for gathering this data, while the player must take care of the robot and protect both Laika and the spacecraft from different risks, such as radiation exposure, communication failures, and other potential hazards during the mission.

## Game Levels

The game consists of 4 levels plus an ending:

### Level 1: Living on the Outpost
- **Survival challenges**: Food, Exercise, and Rest
- **Food challenge**: Select TWO items from the vending machine. Correct: sealed drink and chicken treated with ionizing radiation. Wrong: can of soda and cookie (restarts the game)
- **Cleaning challenge**: After eating, clean the spacecraft panels using a vacuum cleaner
- **Rest challenge**: Choose where to sleep (preferably near a ventilation grille to remove CO₂)
- **Exercise**: Use stationary bicycle with safety harness (must select correct item from vending machine)
- **Rest mode**: Decide where Laika sleeps (near ventilation grille = safe)

### Level 2: Preparing for the Mission
- **Equipment selection**: Use vending machine to select essential landing equipment (parachute, heat shield, sky crane). Must select exactly 3 essential items from 6 options (3 essential + 3 distractors)
- **Communication test**: Send an instruction to Laika but do NOT press the send button. Wait 30 seconds for response. Correct: wait without sending. Trap: sending another message repeatedly
- **Science systems covered**: RADLAB + DONKI, OSDR, MARS TREK

### Level 3: Martian Surface
- **Photography mission**: Take photographs of marked camera buttons. Time limit: 5 minutes. If not completed by 3:30-minute mark, temperature begins to drop.
- **Sandstorm**: When sandstorm begins, find shelter behind rocks, stop all scientific activities, and activate Low Power Mode. Dust is so dense that sunlight cannot reach solar panels.
- **Extreme cold**: After sandstorm, temperature drops to -125°C. Activate Hibernation Mode to protect rover batteries. If rover not close enough to lava tunnel, it will be destroyed.
- **Time mechanics**: Mission has 5-minute countdown. Temperature drops at 3:30 mark. Hibernation mode lasts 45 seconds.

### Level 4: Lava Tunnel Exploration
- **Platforming navigation**: Navigate lava tunnel with flashlight. Not all tunnels are safe.
- **Find objects**: Must find and interact with two buttons: rock sample and camera
- **Obstacles**: Jump between rocks following a straight path. If fall, restart from checkpoint at cave entrance
- **Time limit**: Approximately 4 minutes total. Final 2 minutes dedicated to victory sequence.
- **Victory**: Laika returns to Earth inside spacecraft, reuniting with player

### Ending
- **Win**: Laika survives and returns home with mission completed
- **Incomplete**: Laika returns but mission unfinished - "I won't give up, try again before going back to Earth"
- **Lost**: Laika doesn't return - whole mission was a failure

## Simultaneous Systems (from briefing)
- **RADLAB + DONKI**: Radiación y mediciones reales
- **OSDR**: Salud (human/biological effects of spaceflight)
- **MARS TREK**: Datos reales de Marte

## Gameplay Mechanics
- Delta time everywhere; no `time.sleep`; async-friendly `main()` keeps the pygbag path possible
- Art and audio are fully procedural/synthesized; game runs with empty `assets/` and no audio files
- Missing data/assets/audio/save → graceful fallback, never crash
- Required parts for the ending: the seven part names in `data/planets.json` (Solar Panel Array, Hull Plating, Navigation Module, Shield Generator, Fuel Cells, Thermal Regulator, Signal Antenna)
- Pickups are proximity-based (walk into); `E` fires the blaster in worlds, `E`/`Space` advances dialogue
- Delta time everywhere; no `time.sleep`; async-friendly `main()` keeps the pygbag path possible

## Controls
- `E`/`Space`: Advance dialogue / Interact / Eat / Use
- Arrow keys / WASD: Move
- `F`: Toggle flashlight (Level 4)
- `H`: Laika hint (when available)
- `Esc`: Pause menu / Close dialogue

## Target Play Time
About 25-30 minutes, with mid-level checkpoints so a judge can see the full arc in one sitting.

## Installation
**Prerequisites:** Python 3.12 (3.11 also works).

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`; use `pygame-ce`.

## Adding a Level
To add a new level:
1. Create `data/levels/level<N>.json` with keys: `id`, `name`, `style`, `params`, `dialogue`, `phases`, `objective`, `systems`, `part`, `part_color`, `facts`
2. Create `scenes/level<N>.py` scene following the pattern of existing levels
3. Register the scene in `main.py` via `register_mission_scenes()`
4. Add level data to `data/mission.json` under the `levels` array
5. Add planet part in `data/planets.json`
6. Update documentation
"