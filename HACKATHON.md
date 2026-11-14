# HOMEBOUND — Hackathon Submission Notes

**NASA Space Apps Challenge 2026**

## Title

**HOMEBOUND — A Solar System Repair Mission**

## Tagline

*Nine levels. Seven worlds. One ride home.*

## Concept

A stranded pilot must cross the solar system, recover seven ship parts from seven worlds, and fly
home.

Every level is built on one real planetary fact, and that fact is the mechanic — Mercury's sweeping
sun line drives the heat, Venus's acid rain pours from a 92-bar sky, Mars's low gravity makes every
jump floaty, Jupiter has no ground at all, Saturn rains ring debris, Uranus tilts the horizon, and
Neptune's supersonic winds push you sideways.

## The Hook

Instead of a quiz, the player *experiences* planetary science. Every gameplay rule maps to a real
NASA measurement, each world has its own weather, hazards, and enemies, and the full playable arc
runs about 25–30 minutes with checkpoints so it stays demo-able.

## Quick Start

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Fully offline — no internet or asset files required.

## Three-Minute Demo Script

1. **0:00** — Boot: APOD splash, title, "data: NASA APOD".
2. **0:15** — Menu → map: "Seven parts, seven worlds, one ride home."
3. **0:30** — Tutorial: Laika introduces the mission; collect the first task.
4. **0:50** — Mercury: the sun line sweeps, heat waves rise, recover the Solar Panel Array.
5. **1:15** — Venus: acid rain and geysers under a 92-bar sky, recover the Hull Plating.
6. **1:40** — Mars: 38% gravity jumps, a dust storm swallows the screen, recover the Navigation Module.
7. **2:05** — Jupiter → Neptune montage: storm platforms, ring debris, tilted haze, supersonic winds.
8. **2:35** — Earth: drag all seven parts onto the ship, facts recap, stats screen with per-level best times.
9. **3:00** — Close: "Every mechanic is a real planetary fact — sunlight, pressure, gravity, wind. Cached so it runs offline."

## Judging Alignment

- **Educational:** facts are real NASA data, verified against fact sheets.
- **Gameplay:** real mechanics (gravity, heat, pressure, wind) drive the challenge.
- **Demo-ability:** complete arc in one sitting; ~25–30 min play time with checkpoints.

## NASA Data

- APOD boot screen via `tools/fetch_apod.py`, cached offline.
- Planetary facts from NASA fact sheets.

## Team

- **Sanghaar** — gameplay & content
- **Sulaiman** — engine & shell
- **Story and level design:** Victoria and team
