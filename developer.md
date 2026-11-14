# Developer Plan — Sanghaar & Sulaiman

Companion to `plan.md`. This file is the working agreement: who writes which file, what the
interfaces are, and what happens if one of us disappears mid-sprint.

**Rule zero:** one file, one owner. You may *read* anything, you may only *write* your own files.
Need a change in the other person's file? Post the ask in the chat, do not edit it.

---

## 1. The split at a glance

| | **Sanghaar** | **Sulaiman** |
|---|---|---|
| Role | Lead, gameplay & content | Engine & shell |
| Owns | `scenes/` planet levels, `entities/`, `art/`, `data/`, `core/levels.py` | `main.py`, `core/` (except `levels.py`), `ui/`, `scenes/boot.py`, `menu.py`, `map.py`, `ending.py`, `tools/` |
| Builds | Tutorial, Mars, Mercury, Venus, enemies, hazards, pickups, Laila's script, level tuning | Scene manager, GameState, save/load, HUD, dialogue box, meters, pause, map, APOD, ending UI |
| Cannot touch | `ui/`, `core/scene.py`, `core/game_state.py`, `core/save.py` | `entities/`, `art/`, `data/levels`, `data/dialogue`, planet scenes |
| Branch | `feat/levels` | `feat/engine` |
| Gate reviews | Merges G1, G3, G5, G7 | Merges G2, G4, G6 |

Effort balance: ~13 h each, with the merge gates staggered so nobody waits on the other for more
than one phase. Sulaiman's work is front-loaded (everything else imports it); Sanghaar's levels are
back-loaded but already unblocked after G1.

---

## 2. Frozen contracts

These are agreed at **G1 (hour 4)** and then changed only by a message to both + a 2-line note in
this file. Code to these, and nothing breaks.

### `core/scene.py` — Sulaiman

```python
class Scene:
    def handle_events(self, events): ...   # list[pygame.event.Event]
    def update(self, dt): ...              # dt in seconds
    def draw(self, screen): ...
    def on_enter(self, **data): ...        # called after switch/push
    def on_exit(self): ...

class SceneManager:
    def __init__(self, screen, state): ...
    def switch(self, name: str, **data): ...   # replace current scene
    def push(self, name: str, **data): ...     # overlay (pause, dialogue focus)
    def pop(self): ...
    def run(self, dt): ...                     # events, update, draw for current+overlays
    current: Scene
```

Scene names are strings: `"boot"`, `"menu"`, `"map"`, `"tutorial"`, `"mars"`, `"mercury"`,
`"venus"`, `"ending"`.

### `core/game_state.py` — Sulaiman

```python
@dataclass
class GameState:
    parts: list[str]          # ["Navigation Module", ...]
    facts: list[str]          # fact keys unlocked
    deaths: int
    difficulty: str           # "easy" | "normal" | "hard"
    current_level: str | None
    elapsed: float            # total play seconds
    new_game: bool            # tutorial not yet done

    def add_part(self, name): ...
    def has_part(self, name) -> bool: ...
    def add_fact(self, key): ...
    def scale_speed(self, v) -> float   # hazard speed multiplier
    def scale_time(self, v) -> float    # timer multiplier
    def hearts(self) -> int             # 5 / 3 / 2
    def hint_idle(self) -> float        # 20 / 45 / inf
    def save(self): ...
    def load(self) -> bool: ...
    def reset(self): ...
```

**Contract:** if `GameState.scale_*`, `hearts()` or `hint_idle()` change, every level changes with
them — that is intentional. Never branch on difficulty inside a level scene.

### `core/levels.py` + data — Sanghaar

```python
def load_level(level_id: str) -> dict      # parsed JSON, validated
def load_planets() -> dict                 # data/planets.json
def load_dialogue(dialogue_path: str) -> dict
def level_ids() -> list[str]
```

Guarantees to Sulaiman: keys `id`, `name`, `style`, `part{name,color}`, `params{}`,
`hint_rules{idle_seconds,deaths}`, `dialogue`, `facts[]`, `unlock[]` always exist. Levels with
`style: "platformer" | "top_down" | "timed_survival"` are the only three in scope.

### `ui/` — Sulaiman, consumed by Sanghaar

```python
class HUD:
    def __init__(self, state, level_cfg): ...
    def set_hearts(self, current, maximum): ...
    def set_timer(self, seconds | None): ...
    def set_objective(self, text): ...
    def update(self, dt); def draw(self, screen)

class Meter:                      # heat, pressure, fuel
    def __init__(self, x, y, w, h, label, color, max_value=100): ...
    def set(self, value); def update(self, dt); def draw(self, screen)

class DialogueBox:
    def show(self, text, speaker="Laila", on_done=None): ...
    def queue(self, lines: list[str], speaker="Laila", on_done=None): ...
    def handle_events(self, events) -> bool   # True if it consumed input
    def update(self, dt); def draw(self, screen)
    def is_active(self) -> bool
    def hint(self, text): ...                 # the H button path

class Button:
    def __init__(self, rect, label, on_click, style="primary"): ...
    def handle_events(self, events); def draw(self, screen)
```

Sanghaar's rule: while `dialogue.is_active()`, the level freezes gameplay updates (except the
dialogue), so the player never takes damage mid-sentence.

### `entities/` — Sanghaar

```python
class Player:
    def __init__(self, x, y, cfg, state, hud): ...
    rect: pygame.Rect
    def update(self, dt, events, level): ...
    def draw(self, screen): ...
    def take_damage(self, n=1) -> bool        # True if it died
    health: int

class Chaser:  __init__(self, pos, cfg); update(dt, player, level); draw(screen)
class Patrol:  __init__(self, a, b, cfg); update(dt, player, level); draw(screen)
class Pickup:  __init__(self, pos, kind, payload=None); update(dt); draw(screen); collides(player)
```

Sulaiman never imports from `entities/`; the level scene composes everything.

### Asset access

```python
# core/assets.py — Sulaiman
def path(relative: str) -> str        # resolves assets/... , returns "" if missing
def image(relative, fallback_size=None) -> Surface | None
def font(size: int, bold=False) -> pygame.font.Font
def play(name: str, volume=1.0) -> None    # silent if missing
```

All drawing of missing assets falls back to primitives. The game must run with an empty `assets/`.

---

## 3. Sulaiman — work packages

| ID | Package | Files | Est. | Done when |
|---|---|---|---|---|
| S1 | Repo skeleton, `requirements.txt`, `settings.py`, async `main.py` | `main.py`, `core/settings.py` | 0.5 h | window opens at 1280×720/60, Esc quits async-safe |
| S2 | `Scene` + `SceneManager` (switch/push/pop), scene registry | `core/scene.py` | 1.5 h | menu → dummy → back; overlay pause works |
| S3 | `GameState` + difficulty multipliers + auto-hooks | `core/game_state.py` | 1 h | unit check script prints hearts/scale per difficulty |
| S4 | Save/load to user JSON, Continue flow | `core/save.py` | 0.75 h | relaunch restores parts, facts, difficulty |
| S5 | Assets/audio/font helpers with fallbacks | `core/assets.py`, `core/audio.py` | 0.75 h | delete `assets/` → game still runs |
| S6 | HUD, hearts, timer slot, objective line | `ui/hud.py` | 1 h | part pickup appears instantly, timer readable |
| S7 | DialogueBox (typewriter 40 cps, advance on Space/click, `H` hint, portrait box) | `ui/dialogue_box.py` | 1.5 h | 3 lines of long text fit, no overflow |
| S8 | `Meter`, `Button`, pause overlay (Resume/Restart/Mute/Map) | `ui/meter.py`, `ui/button.py`, `ui/pause.py` | 1 h | reuse in Mars/ Mercury / Venus unchanged |
| S9 | Solar map: orbits, planet dots from `planets.json`, locks, part ticks, archive cards | `scenes/map.py` | 1.5 h | Tutorial done → Mars/Mercury/Venus unlocked |
| S10 | Boot screen with cached APOD + `tools/fetch_apod.py` | `scenes/boot.py`, `tools/fetch_apod.py` | 0.5 h | works offline with committed JSON |
| S11 | Ending: drag parts onto ship, snap + fact, stats screen | `scenes/ending.py`, `ui/stats.py` | 1.5 h | 3 parts required, stats correct |
| S12 | Settings: difficulty + volume, persisted | `scenes/menu.py` (settings tab) | 0.5 h | changes apply to next level load |

Total ≈ 13 h. Order is S1→S2→S3→S5→S4→S6→S7→S8→S9→S10→S11→S12, with S10 done early
(run the fetch once during P0 so the cache is committed before anyone needs it).

**Sulaiman's stubs are due at G1 (hour 4).** A stub is better than nothing: an empty `HUD.draw()`
lets Sanghaar finish a level that Sulaiman dresses later.

---

## 4. Sanghaar — work packages

| ID | Package | Files | Est. | Done when |
|---|---|---|---|---|
| G1 | JSON schema + `core/levels.py` loader/validator + path helper | `core/levels.py`, `data/levels/*.json` | 1 h | bad JSON gives a readable error, not a crash |
| G2 | `data/planets.json` (5 playable/archive entries) + Laila scripts | `data/planets.json`, `data/dialogue/*.json` | 1 h | every level has start/hint/win lines |
| G3 | Art primitives: starfield, planet disc with bands, ground tiles, glow, part icons | `art/*.py` | 1.5 h | identical look on all levels, no PNGs needed |
| G4 | `entities/player.py` shared movement + top-down variant | `entities/player.py` | 1.5 h | 8-dir move, dt-based, no drift |
| G5 | Platformer controller: gravity from JSON, variable jump, coyote time, checkpoints | `entities/player.py` | 1.5 h | Mars jumps feel floaty but controlled |
| G6 | `entities/enemies.py` chaser + patrol | `entities/enemies.py` | 1 h | chaser dies in 2 hits, patrol damages on touch |
| G7 | `entities/hazards.py`: dust storm, sun sweep, acid, debris | `entities/hazards.py` | 1 h | storm fades, no >1 Hz flashing |
| G8 | `entities/pickups.py`: part, health, canister, fragment | `entities/pickups.py` | 0.5 h | pickup adds part/fact through GameState |
| G9 | Tutorial scene + hint trigger wiring | `scenes/tutorial.py` | 1 h | 90 s completion, all 3 tasks |
| G10 | Mars scene + 3 sections + tuning | `scenes/mars.py` | 2 h | winnable and losable from checkpoints |
| G11 | Mercury scene + sun sweep + heat meter | `scenes/mercury.py` | 1.5 h | heat meter readable, shadows safe |
| G12 | Venus scene + timer + pressure + fragments | `scenes/venus.py` | 1.5 h | 90 s win, 20 s spare |
| G13 | Balance pass across all JSON + fact check | `data/**` | 1 h | Easy/Normal/Hard all playable |

Total ≈ 15.5 h, so G3 (art) and G13 (balance) are the flex items. If behind at H11, Mars keeps
storm and drops the turret; at H15, Mercury drops cold zones.

**Sanghaar's blockers:** HUD/DialogueBox at G1 (stub), Meter at G3 (stub). Until then, use a local
`_debug_draw` inside the level scene and delete it at merge.

---

## 5. Who is doing what, per gate

| Gate | Hour | Sanghaar | Sulaiman |
|---|---|---|---|
| P0 | H0–H1 | venv, clone, plan read, `data/` schema draft, team message | venv, clone, `main.py` + settings, APOD fetch committed |
| G1 | H1–H4 | `levels.py`, planets + tutorial JSON, dialogue draft, player base, art primitives | SceneManager, GameState, save, assets/audio, dummy scene |
| G2 | H4–H7 | Tutorial scene wired to dialogue/hints | HUD, DialogueBox, Button, menu |
| G3 | H7–H11 | Mars scene, platformer, storm, chaser/turret | Hearts, Meter, pause overlay |
| G4 | H11–H15 | Mercury scene, sun sweep, heat, patrols | Solar map, unlocks, part ticks |
| G5 | H15–H17.5 | Venus scene, timer, pressure, canisters | Difficulty + volume settings, multipliers |
| G6 | H17.5–H20 | Ending dialogue, balance, retune JSON | Ending assembly, stats, save hooks, APOD boot |
| G7 | H20–H22 | SFX hooks, particles, fact verification | Screen shake, archive cards, FPS pass |
| Freeze | H22–H23.5 | demo script, README facts section | README run steps, screenshots, tag, submission text |

---

## 6. Coordination rules

1. **Push every 2 hours** to your branch, even if it is half-finished. No long local-only work.
2. **Merge only at gates**, at the hour in the table, even if it is imperfect. Imperfect + merged
   beats perfect + unmerged at hour 20.
3. **After a merge, both pull `main` before writing another line.** Stale branches cause 80% of
   conflicts here.
4. **Interface changes:** message both + append a line here under §2. Never silently change a
   signature that the other person already calls.
5. **Never rename a JSON key** the other person reads; add a new one and keep the old.
6. **`main` must launch.** If it does not, the person who broke it fixes it immediately and nothing
   merges until it does.
7. **Ask for help after 20 minutes stuck**, not 60. Ping with: what you expected, what happened, the
   last commit hash.
8. **No new features after H22.** Only fixes that keep the demo path alive.
9. **Run `black .`** before commits once `black` is in requirements (cosmetic, avoids diff noise).
10. **Commit messages:** `type(scope): what`. A commit that fixes the demo path gets priority over
    any feature.

---

## 7. Integration points (the only places we touch)

| Point | Provider → Consumer | Contract |
|---|---|---|
| Scene switching | Sanghaar's levels call `manager.switch("map")` on win | name + kwargs only |
| State mutation | every level writes parts/facts/deaths via `GameState` | no level reads `state` internals beyond the API |
| HUD | level constructs `HUD(state, cfg)` and calls `set_*` | level never draws hearts itself |
| Dialogue | level calls `dialogue.queue([...])` from `data/dialogue/*.json` | level never draws text boxes |
| Meters | level owns the value, `Meter` only renders | `meter.set(value)` each frame |
| Ending | `ending` reads `state.parts` | requires all 3 required parts, else bounces to map |
| Save | `state.save()` on pickup + scene change | levels do not serialize anything themselves |

---

## 8. If Sulaiman is unavailable

Sanghaar absorbs in this order. Stop at the first item that does not fit the remaining hours, and
cut from `plan.md` §10 to pay for it.

1. **HUD + Meter + DialogueBox** (blocking — no game without them, ~3 h).
2. **SceneManager + GameState** (~2.5 h; simple dict-based scenes are acceptable).
3. **Map screen** (~1.5 h; a list of three buttons is an acceptable map).
4. **Menu + boot + pause** (~1 h combined).
5. **Ending assembly** (~1 h; a single "Assemble" button that shows the three facts is acceptable).
6. **Save/load** (drop entirely before spending an hour on it).
7. **APOD** (drop; keep the static title card).

At that point the committed scope becomes Tutorial + Mars + Mercury + Earth, and **Venus is cut
first** because it is the least mechanically distinct (timer + meter already exist).

Corollary: Sanghaar should not start Venus until the map/ending owner confirms they exist, because
Venus is the cheapest level to sacrifice.

---

## 9. Definition of done (per work package)

- [ ] Runs from a fresh clone with `python main.py`; no traceback, no console spam.
- [ ] Uses `dt`; identical behaviour at 30 and 60 FPS.
- [ ] No hardcoded gameplay numbers — JSON only.
- [ ] No `time.sleep`, no network call inside the loop.
- [ ] Missing asset → fallback shape, not a crash.
- [ ] Win and lose paths both tested (levels) / both button paths tested (UI).
- [ ] Reads and writes `GameState` through the public API only.
- [ ] Works with `assets/` emptied.
- [ ] Committed with a `type(scope):` message and pushed.
- [ ] For levels: hint at idle, at 3 deaths, and on `H`.
- [ ] For UI: readable at 1280×720 and at 1024×576 (scaled), no text overflow.

---

## 10. First 30 minutes (copy-paste order)

```bash
# 1. Get the code
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install (pygame-ce, never plain pygame)
pip install pygame-ce
python -c "import pygame; print(pygame.version.ver)"

# 3. Branch
git checkout -b feat/engine     # Sulaiman
git checkout -b feat/levels     # Sanghaar

# 4. Sulaiman only, once:
python tools/fetch_apod.py      # writes data/cache/apod.json, then commit it
```

If `pip install pygame-ce` fails on Python 3.14, install Python 3.12 for the project venv — do not
downgrade to plain `pygame`.

**Then, before writing code:**

1. Confirm the four frozen interfaces in §2 with a thumbs-up in the chat.
2. Sulaiman pushes `main.py` + empty `core/` files at H0.5 so Sanghaar can import.
3. Sanghaar pushes `data/planets.json` + one `data/levels/tutorial.json` at H1 so the map can be
   built against real data.
4. Both run the §10 checklist again at every gate.

---

## 11. Never touch / never cut

**Never touch (other owner's files):**
`ui/*`, `core/scene.py`, `core/game_state.py`, `core/save.py`, `core/assets.py`, `scenes/map.py`,
`scenes/menu.py`, `scenes/boot.py`, `scenes/ending.py` → Sulaiman.
`entities/*`, `art/*`, `data/levels/*`, `data/dialogue/*`, `data/planets.json` → Sanghaar.

**Never cut:** tutorial, Laila's dialogue and hints, the part-collection loop, the fact display,
win/lose states, pause. Everything else is negotiable.

---

## 12. Judging alignment (who owns which criterion)

The presenter carries Presentation, but the build has to make their job easy. Feature-to-criterion
ownership:

| Criterion | Owner | Standing deliverable |
|---|---|---|
| Impact | Sanghaar | Fact logging, stats screen, difficulty + text-size + mute settings, accessible hazards |
| Creativity | Sanghaar | Laila's dialogue and hologram, fact-as-mechanic level rules |
| Validity | Sulaiman | Tested game loop (`tools/smoke_test.py`, `tools/playtest.py`), offline APOD, 60 FPS |
| Relevance | Sanghaar | Real units on meters, sourced fact cards, NASA data in JSON (checked by Sulaiman) |
| Presentation | Sanghaar (docs) → presenter | Demo script in `plan.md` §11, README quickstart, screenshots |

**Rule:** any new feature must name the criterion it defends before it is built. A feature that
defends none of the five gets cut.
