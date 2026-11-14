# HOMEBOUND

**NASA Space Apps Challenge 2026** — a solar system repair mission.

A stranded pilot must travel the solar system with **Laila**, the ship's guide, recovering the parts
needed to get home. Every level runs on a real planetary fact, and that fact is the mechanic:
Mars gravity changes how you jump, Mercury's 430 °C daylight chases you into crater shadows, and
Venus's 92 atmospheres squeeze the clock.

## Status

**Pre-code sprint kickoff.** Scope, architecture and the 24-hour schedule are locked.

- [`plan.md`](plan.md) — scope, level specs, architecture, data formats, 24-hour phased schedule, demo script.
- [`developer.md`](developer.md) — Sanghaar/Sulaiman feature split, frozen interfaces, merge gates, fallback plan.

## Scope (24 hours)

| Level | Style | Real mechanic |
|---|---|---|
| Earth orbit (tutorial) | Top-down | Meet Laila, learn controls and the hint button |
| Mars | Platformer | 3.71 m/s² gravity, dust storms cut visibility |
| Mercury | Top-down stealth | Sun line sweeps; heat meter; hide in shadow |
| Venus | Timed survival | 92× Earth pressure, 90-second escape |
| Earth (finale) | Assembly | Rebuild the ship, recap the facts, stats screen |

Jupiter and Saturn appear as read-only "Data Archive" fact cards on the solar map.

## Tech

- Python 3.12, **pygame-ce** (never plain `pygame`)
- 1280 × 720, 60 FPS, delta-time movement
- Data-driven levels: all numbers and dialogue live in JSON
- Procedural art (no asset blocking), cached NASA APOD on the boot screen, fully offline-capable
- Desktop demo first; async-friendly loop so a pygbag web build stays possible

## Run it (once code lands)

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python main.py
```

## Controls

| Action | Key |
|---|---|
| Move | WASD / arrow keys |
| Jump (Mars) | Space (hold for higher) |
| Interact / pick up | E |
| Laila hint | H |
| Pause | Esc |

## Team

- **Sanghaar** — lead, gameplay and content (levels, entities, data, art primitives)
- **Sulaiman** — engine and shell (scene manager, state, UI, map, ending)
- Story and level design: Victoria and team
