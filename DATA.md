# HOMEBOUND — Data & Content Reference

HOMEBOUND is data-driven: all gameplay content lives in JSON and is loaded through
`core/levels.py`. Scenes never hardcode numbers — they read from these files.

## `data/planets.json`

Top-level keys:

- `order` — list of planet ids in display order.
- `sun` — sun name + color.
- `planets` — list of planet entries.

Each planet entry:

| Key | Meaning |
|---|---|
| `id` | Stable key, e.g. `mars`, `mercury`, `earth`, `jupiter`, … |
| `name` | Display name. |
| `part` | Ship part associated with this planet (or `null` for the Earth finale / pure archive). |
| `playable` | Scene name to launch, `null` for archive-only, `"ending"` for the finale. |
| `map_position` | `[x, y]` normalized map position. |
| `orbit_px` | Orbit radius on the map. |
| `radius` | Map icon radius. |
| `color` | Planet color (hex). |
| `band_color` | Band color (hex). |
| `bands` | Number of procedural bands. |
| `craters` | Number of procedural craters. |
| `ring` / `ring_color` | Ring flag + color. |
| `tagline` | One-line mission flavor text. |
| `fact` | The single fact shown on the map / archive card. |
| `facts` | Fact keys used by the level / archive. |
| `unlock` | Unlock rules, e.g. `["tutorial_done"]`, `["all_parts"]`. |

## `data/levels/<id>.json`

Required keys:

- `id`, `name`, `style`, `part` (`{name, color}`), `params` (object), `dialogue`.

Optional keys with defaults:

- `objective` (default `""`).
- `facts` (default `[]`).
- `unlock` (default `[]`).
- `hint_rules` (default `{idle_seconds: 45, deaths: 3}`).

`style` is one of: `platformer`, `top_down`, `timed_survival`.

### Implemented levels

| Level | Style | Key params |
|---|---|---|
| `tutorial` | `top_down` | `player_start`, `move_speed`, `accel`, `friction`, `marker`, `crate`, `hint_prompt_seconds` |
| `mars` | `platformer` | `gravity_px`, `jump_speed`, `hold_boost`, `move_speed`, `accel`, `friction`, `chaser_speed`, `patrol_speed`, `storm_interval`, `storm_duration`, `visibility_radius`, `part_pos`, `player_start`, `checkpoints` |
| `mercury` | `top_down` | `player_start`, `move_speed`, `accel`, `friction`, `sun_speed`, `heat_rise_rate`, `heat_fall_rate`, `meter_max`, `part_pos`, `shadows` |
| `venus` | `timed_survival` | `player_start`, `move_speed`, `accel`, `friction`, `time_limit`, `pressure_rate`, `canister_effect`, `fragments_needed`, `part_pos`, `exit_pos`, `fragments`, `canisters`, `acid_pools` |

## `data/dialogue/<id>.json`

Shape:

```json
{
  "speaker": "Laila",
  "lines": [
    { "trigger": "start", "text": "..." },
    { "trigger": "hint", "text": "..." }
  ]
}
```

Triggers used across levels:

- `start` — opening lines.
- `marker` / `crate` / `hint_prompt` / `win` / `idle` — tutorial task lines.
- `storm` — Mars dust storm warning.
- `death_3` — Laila hint after third death.
- `heat` — Mercury heat warning.
- `countdown` — Venus half-time countdown.
- `hint` — manual Laila hint (H).

## `data/cache/apod.json`

Boot-screen APOD entry: `title`, `explanation`, `url`, `media_type`, `date`, `fetched_at`,
`offline_fallback`.

## Adding content

Because the game is data-driven, retuning a level or adding dialogue usually requires only JSON
edits — no Python changes — provided required keys keep their shapes.
