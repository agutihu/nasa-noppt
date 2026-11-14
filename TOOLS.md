# HOMEBOUND — Tools & Testing Reference

Developer and QA utilities shipped with the project.

## Overview

| Tool | File | Purpose |
|---|---|---|
| NASA APOD cache | `tools/fetch_apod.py` | Fetch and cache NASA's Astronomy Picture of the Day. |
| Smoke test | `tools/smoke_test.py` | Headless smoke test: boot every scene, run frames, report failures. |
| Playtest | `tools/playtest.py` | Scripted end-to-end playtest of the full game loop. |
| Map panel shots | `tools/shot_map.py` | Render the map detail panel headless for every planet; layout/QA checks. |

## `tools/fetch_apod.py`

Fetches today's NASA Astronomy Picture of the Day from `api.nasa.gov/planetary/apod` and writes:

- `data/cache/apod.json` — title, explanation, media type, date, etc.
- `data/cache/apod.jpg` — thumbnail image (when the media type is an image).

Run once with internet:

```bash
python tools/fetch_apod.py
```

Optionally pass a NASA API key:

```bash
python tools/fetch_apod.py YOUR_API_KEY
```

If the fetch fails, the game keeps running with the bundled offline entry in `data/cache/apod.json`
(`offline_fallback: true`).

## `tools/smoke_test.py`

Headless smoke test. Boots pygame with dummy video/audio drivers, registers all scenes in the
`SceneManager`, runs a fixed number of frames per scene, and reports which scenes boot cleanly.

Run from the project root:

```bash
python tools/smoke_test.py
```

Expected output: one `ok` line per scene, then `all scenes ok`.

## `tools/playtest.py`

Scripted end-to-end playtest. Drives the real game loop headlessly and verifies the full arc:

1. Tutorial: intro dialogue finishes, player reaches beacon, collects crate, presses H, level completes.
2. Mars: dust storm activates, Navigation Module collected.
3. Mercury: heat rises in sunlight, Solar Panel Array collected.
4. Venus: fragments collected, escape triggers win, Hull Plating collected.
5. Map: Earth finale unlocks with all parts.
6. Ending: assembly accepts parts, launch, stats screen shown.

Run from the project root:

```bash
python tools/playtest.py
```

Exits `0` and prints `full loop ok` when all checks pass; exits `1` listing any failures.

## `tools/shot_map.py`

Renders the map screen headless — once with nothing selected, then once per planet with the
detail panel open — and saves PNGs to `tools/shots/` (git-ignored). Use it to verify panel
layout, text fitting, and status chips after changing the map or planet data.

```bash
python tools/shot_map.py
```

## Running Headless

The tools set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` automatically. No display is
required.
