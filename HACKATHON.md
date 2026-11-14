# HOMEBOUND — Hackathon Submission Notes

**NASA Space Apps Challenge 2026**

## Title

**HOMEBOUND — A Solar System Repair Mission**

## Tagline

*Five planets. Three parts. One ride home.*

## Concept

A stranded pilot must cross the solar system, recover three ship parts, and fly home.

Every level is built on one real planetary fact, and that fact is the mechanic — Mars gravity
makes the jump; Mercury's sun line and heat meter drive the stealth; Venus's pressure and timer
define survival.

## The Hook

Instead of a quiz, the player *experiences* planetary science. Every gameplay rule maps to a real
NASA measurement, and the full playable arc runs about 14 minutes.

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
2. **0:15** — Menu → map: "Five parts, seven planets, one ride home."
3. **0:30** — Tutorial: Laila introduces the mission; collect the first task.
4. **1:00** — Mars: jump in 38% gravity, dust storm hits, recover the Navigation Module.
5. **1:40** — Mercury: outrun the sun line, hide in a crater, heat meter saves you.
6. **2:15** — Venus: 92 atmospheres, 90 seconds, three fragments, escape.
7. **2:45** — Earth: drag parts on, facts recap, stats screen.
8. **3:00** — Close: "Every mechanic is a real planetary fact — gravity, sunlight, pressure. Cached so it runs offline."

## Judging Alignment

- **Educational:** facts are real NASA data, verified against fact sheets.
- **Gameplay:** real mechanics (gravity, heat, pressure, timing) drive the challenge.
- **Demo-ability:** complete arc in one sitting; ~14 min play time.

## NASA Data

- APOD boot screen via `tools/fetch_apod.py`, cached offline.
- Planetary facts from NASA fact sheets.

## Team

- **Sanghaar** — gameplay & content
- **Sulaiman** — engine & shell
- **Story and level design:** Victoria and team
