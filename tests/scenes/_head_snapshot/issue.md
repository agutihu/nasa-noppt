# ISSUE: Level 3 (and Levels 2 & 4) are unplayable — the game never leaves the `intro` phase

**Status:** Open — Blocker
**Severity:** Critical (game-breaking)
**Reported by:** Leslie — *"there was something that won't let her move"*
**Date raised:** 2026-11-15
**Affected files:** `scenes/level3.py`, `scenes/level2.py`, `scenes/level4.py`, `data/dialogue/mars.json`
**Reproduced by:** Headless simulation of all four campaign levels (see [Reproduction](#reproduction))

---

## 1. Summary

The player's report ("something that won't let her move") is really a **hard blocker**: Level 3
**never advances past its very first phase**. The player is dropped into the `intro` phase, the
intro dialogue plays, and then the level sits there forever — no camera buttons, no rock sample,
no sandstorm, no hibernation, no way to finish.

This is **not** a physics/collision/"stuck on geometry" problem. The level is simply never told
to move on. The same missing transition exists in **Level 2** and **Level 4**, so after
Level 1 the entire rest of the campaign is unreachable.

| Level | Result of 20s headless run | Status |
|-------|------------------------------|--------|
| Level 1 | `intro` → `food_briefing` | OK |
| Level 2 | `intro` (stuck) | **Broken** |
| Level 3 | `intro` (stuck) | **Broken** |
| Level 4 | `intro` (stuck) | **Broken** |

---

## 2. Root cause

### 2.1 No transition out of `intro`

`scenes/level3.py:184-190`

```python
def _handle_intro(self, dt: float) -> None:
    self.t += dt
    if self.player_pos.distance_to(pygame.Vector2(640, 380)) > 30:
        direction = (pygame.Vector2(640, 380) - self.player_pos).normalize() * 120 * dt
        self.player_pos += direction
    if self.player_pos.distance_to(pygame.Vector2(640, 380)) < 50 and not self.dlg.is_active():
        self._say("intro")
    # <-- NO TRANSITION. There is no _goto_phase("photo_intro") anywhere.
```

Every `_goto_phase(...)` call in `level3.py` is at lines 109, 201, 225, 255, 268, 280 — **none of
them leaves `intro`**. The phase chain `intro → photo_intro → take_photos → sandstorm →
cold_alert → hibernation → complete` (declared in `data/levels/level3.json`) is therefore
unreachable from the start.

Level 1 does it correctly (`scenes/level1.py:343-344`):

```python
# transition to food_briefing after dialogue
if not self.dlg.is_active() and self.dlg.lines == []:
    self._goto_phase("food_briefing")
```

Levels 2, 3 and 4 are missing that line.

### 2.2 `_schedule_next()` is dead code across the whole project

`scenes/level3.py:151-153` (identical in `level1.py:266`, `level2.py:127`, `level4.py:157`):

```python
def _schedule_next(self, phase: str, delay: float) -> None:
    self._next_phase = phase
    self._next_phase_time = self.state.elapsed + delay
```

`self._next_phase` and `self._next_phase_time` are **written but never read** — a repo-wide
`grep` returns only the four assignment sites, no reads. So even after fixing §2.1, Level 3
would still hang, because two of its transitions rely on this dead mechanism:

- `photo_intro → take_photos`  (`_goto_phase`, line 126-129)
- `hibernation → complete`      (`_goto_phase`, line 135-139)

### 2.3 `update()` dispatcher is missing a branch

`scenes/level3.py:312-327` handles `intro`, `take_photos`, `sandstorm`, `cold_alert`,
`hibernation`, `complete` — but **not `photo_intro`**, which is a phase declared in
`data/levels/level3.json:30-34`.

### 2.4 Origin

Introduced by commit `315996f` *"feat(mission): align gameplay exactly with the PPTX mission
plan"*, which rewrote the Level 2/3/4 phase handlers but never wired the intro transitions.
The bug was already present in `1dea22d`; the smoke test never caught it because
`tools/smoke_test.py` only boots scenes for 30 frames — it never asserts that a level *progresses*.

---

## 3. Reproduction

1. Launch the game: `python main.py`
2. Complete Level 1 (or select Level 3 from the map once unlocked)
3. Level 3 opens on **"OBJECTIVE: Follow Laika to the research area."**
4. Press `SPACE`/`E` to dismiss the intro dialogue
5. Wait. **Nothing else ever happens.** No camera buttons appear, no sample rock, no sandstorm.

### Headless proof

```python
# tools/_repro.py (temporary)
for _ in range(60 * 20):                      # 20 simulated seconds
    game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
    game.manager.update(1 / 60.0)
    game.manager.draw()
print(seen_phases)
```

```
level1: phases -> ['intro', 'food_briefing']
level2: phases -> ['intro']          <- stuck
level3: phases -> ['intro']          <- stuck
level4: phases -> ['intro']          <- stuck
```

---

## 4. Full issue list

### 4.1 Blocker

| # | Location | Issue | Fix | Est. |
|---|----------|-------|-----|------|
| 1 | `level3.py:184-190` | `_handle_intro` never leaves `intro` | Add `if not self.dlg.is_active() and self.dlg.lines == []: self._goto_phase("photo_intro")` | 5 min |
| 2 | `level3.py:151-153` | `_schedule_next()` writes `_next_phase`/`_next_phase_time`, never read | Either consume them in `update()`, or replace with direct `_goto_phase()` calls (preferred — matches Level 1 style) | 15 min |
| 3 | `level3.py:312-327` | `update()` has no `photo_intro` branch | Add `elif self.phase == "photo_intro": self._handle_photo_intro(dt)` + handler that advances to `take_photos` once its dialogue clears | 10 min |
| 4 | `level2.py:154-160` | Same missing `intro → landing_briefing` transition | Add the same guard → `_goto_phase("landing_briefing")` | 5 min |
| 5 | `level4.py:195-201` | Same missing `intro → flashlight_on` transition | Add the same guard → `_goto_phase("flashlight_on")` | 5 min |

### 4.2 Secondary (Level 3)

| # | Location | Issue | Fix | Est. |
|---|----------|-------|-----|------|
| 6 | `level3.py:199-206` | The `elapsed >= 300.0` fail check is **unreachable** — the `elapsed >= 180.0` check above it returns first, so the photo phase can never fail | Reorder: check `>= 300` (loss) first, then `>= 180` (temperature drop) | 5 min |
| 7 | `level3.py:262` | Cold-alert timer hardcodes `45.0`s but `data/levels/level3.json:51` says `time_limit: 10` | Read the phase `time_limit` from the JSON instead of hardcoding | 10 min |
| 8 | `level3.py:89, 237-241` | `sandstorm_pos` is captured at level start and never re-baselined when the storm begins, so the "you moved during the storm" check compares against the **level-start** position. Any 40px displacement = instant rover loss (latent instant-death trap) | Reset `self.sandstorm_pos = pygame.Vector2(self.player_pos)` when entering the `sandstorm` phase | 5 min |
| 9 | `level3.py:193-228, 338` | **No player movement code.** `player_pos` is never changed by input, and the astronaut is drawn at a hard-coded `(640, 380)` instead of `player_pos`. Photo/sample interaction uses the **mouse cursor** position, so the avatar is purely decorative | Add WASD/arrow movement in `_handle_take_photos`; draw the astronaut at `self.player_pos`; base interaction on player proximity (or keep mouse but show the avatar) | 30 min |
| 10 | `level3.py:74-77, 123` | HUD counters are set once in `on_enter` and never updated → always shows `PHOTOS 0/6`. Also `_goto_phase()` resets `photos_taken = 0` | Update counters via `hud.set_counters(...)` on each photo; don't reset the counter on phase change | 15 min |
| 11 | `level3.py:28` | `_item_rect()` references an undefined `rows` → `NameError` if ever called. `level2.py:28` and `level4.py:28` share the same copy-paste bug (`level1.py:27-36` is correct) | Copy the correct `rows = max(1, math.ceil(grid_rect.width / 200))` line from `level1.py` | 5 min |
| 12 | `level3.py:62` | `Modal` is never imported. Harmless at runtime only because of `from __future__ import annotations`, but `self.modal: Modal \| None` breaks under `typing.get_type_hints()` | Add `from ui.modal import Modal` | 2 min |
| 13 | `data/dialogue/mars.json` | Triggers `photo_intro`, `take_photos`, `sandstorm`, `cold_alert`, `hibernation` **do not exist** → `_say()` silently no-ops. None of the Level 3 briefings ever reach the player | Add the five triggers to `mars.json` | 20 min |
| 14 | `data/dialogue/mars.json:12` | The `intro` line shown in Level 3 is Level 1's: *"Welcome to the Mars outpost…"* — wrong scene text | Give Level 3 its own intro line (or a per-level trigger) | 10 min |

---

## 5. Proposed fix

### 5.1 Make `_schedule_next()` work (or remove it)

Preferred: **drop `_schedule_next()` from Level 3** and call `_goto_phase()` directly once the
dialogue clears — this is the pattern Level 1 already uses and it removes a whole class of
silent-stall bugs.

```python
# level3.py — _goto_phase
if phase == "photo_intro":
    self._say("photo_intro")
    return                       # handler below advances to take_photos
if phase == "take_photos":
    self.photos_taken = 0
    self._say("take_photos")
    return
```

```python
# level3.py — new handler
def _handle_photo_intro(self, dt: float) -> None:
    self.t += dt
    if not self.dlg.is_active() and self.dlg.lines == []:
        self._goto_phase("take_photos")
```

### 5.2 Wire the intro transition (the actual blocker)

```python
# level3.py — _handle_intro
def _handle_intro(self, dt: float) -> None:
    self.t += dt
    if self.player_pos.distance_to(pygame.Vector2(640, 380)) > 30:
        direction = (pygame.Vector2(640, 380) - self.player_pos).normalize() * 120 * dt
        self.player_pos += direction
    if self.player_pos.distance_to(pygame.Vector2(640, 380)) < 50 and not self.dlg.is_active():
        self._say("intro")
    # NEW: move on once the intro dialogue has finished
    if not self.dlg.is_active() and self.dlg.lines == []:
        self._goto_phase("photo_intro")
```

The identical guard goes into `level2.py` (→ `"landing_briefing"`) and `level4.py`
(→ `"flashlight_on"`).

### 5.3 Correct the timers and the storm baseline

```python
# level3.py — _handle_take_photos
if elapsed >= 300.0:            # loss check FIRST (was unreachable)
    self._lose_mission()
    return
if elapsed >= 180.0:            # temperature drop
    self.hud.banner("TEMPERATURE DROPPING TO -125°C - ACTIVATE HIBERNATION MODE", 4.0, settings.DANGER)
    self._goto_phase("cold_alert")
    return
```

```python
# level3.py — _goto_phase("sandstorm")
self.sandstorm_pos = pygame.Vector2(self.player_pos)   # baseline at storm start
```

Cold-alert length should come from `data/levels/level3.json` (`time_limit: 10`), not a literal.

### 5.4 Guard against a repeat

Add a regression check to `tools/smoke_test.py`: after booting each campaign level, assert the
phase actually **changed** within N simulated frames (with dialogue auto-advanced). This is what
would have caught this the day it was written.

---

## 6. Time estimate

| Work item | Scope | Estimate |
|-----------|-------|----------|
| **P0 — unblock the game** | Items 1-5: wire `intro` transitions in Levels 2/3/4, add `photo_intro` branch, replace dead `_schedule_next()` | **~40 min** |
| **P1 — Level 3 correctness** | Items 6-8: timer ordering, JSON-driven `time_limit`, storm baseline | **~20 min** |
| **P1 — Level 3 feel** | Items 9-10: real movement, live HUD counters | **~45 min** |
| **P2 — polish & hygiene** | Items 11-14: `rows` NameError, `Modal` import, missing dialogue triggers, wrong intro line | **~40 min** |
| **P2 — regression guard** | Phase-advance assertion in `tools/smoke_test.py` | **~20 min** |
| | **Total (P0+P1)** | **~1 h 45 min** |
| | **Total (everything)** | **~2 h 45 min** |

**Add ~30 min** if a full manual playtest of all four levels is required before the fix is
signed off (recommended — the campaign has never actually been played past Level 1).

**Critical path:** P0 only = **40 minutes** to make Levels 2-4 reachable again.

---

## 7. Verification plan

- [ ] `python tools/smoke_test.py` → `all scenes ok`
- [ ] Headless phase trace for Levels 1-4 shows a full phase chain, no stall
- [ ] Manual playtest: Level 3 completes intro → photos → sample → sandstorm → cold alert →
      hibernation → briefing
- [ ] Level 3 photo phase can actually be failed at the 5-minute mark
- [ ] Level 3 cold-alert timer matches `data/levels/level3.json` (`time_limit: 10`)
- [ ] Player can move with WASD/arrows; the avatar follows the cursor/player position
- [ ] All Level 3 dialogue triggers exist in `data/dialogue/mars.json`
- [ ] Level 3 `intro` line is Mars-surface text, not "Welcome to the Mars outpost"

---

## 8. Notes for the team

- `tools/smoke_test.py` never ran the campaign levels — it only boots `tutorial`, the seven
  world planets, `menu`, `map`, `pause` and `ending`. The four campaign levels
  (`scenes/level1-4.py`) were **never smoke-tested at all**. This is how the blocker survived.
  - **Verified 2026-11-15**: `grep` for `LEVEL1|LEVEL2|LEVEL3|LEVEL4` in `tools/smoke_test.py`
    returns **zero matches**, and the smoke test still reports `all scenes ok` while Levels 2-4
    are completely unreachable. A passing smoke test currently proves nothing about this game.

### Scope — what this issue does *not* cover

- The world-level (seven-planet) fixes are **unrelated**: `is_unlocked()` accepting a planet dict
  or id, `required_parts()` returning the seven part names, `add_part()` / `has_part()`,
  `params.moment` + `_update_moment()`, and the `EndingScene` state fallback all live in
  `core/game_state.py`, `core/levels.py`, `scenes/ending.py` and `scenes/world_level.py`
  (committed as `2da57f9`).
- This issue is confined to the **4-level campaign** (`scenes/level1-4.py` +
  `data/levels/level{1..4}.json`), which is a separate track from the planet world levels.
  `scenes/level2.py`, `scenes/level3.py` and `scenes/level4.py` are **not** modified in the
  working tree, so every finding above is still current.
- `data/dialogue/mars.json` was also extended in the working tree, but only with a `moment`
  trigger for the Mars **world** level. The five missing Level 3 campaign triggers
  (`photo_intro`, `take_photos`, `sandstorm`, `cold_alert`, `hibernation`) are still absent.
- All gameplay numbers are supposed to come from `data/levels/*.json` (per `AGENTS.md`), but
  Level 3 hardcodes `180.0`, `300.0`, `45.0`, `10` and `40.0` in Python. Items 6-8 move these
  back into JSON.
- `_schedule_next()` appears in all four campaign scenes and is dead in all four. If it is
  removed rather than revived, `level1.py` and `level4.py` need a check that nothing depended
  on it.

---

*Related: see `AGENTS.md` ("Critical Fixes" table) — add an entry for "campaign levels never
leave the `intro` phase" once fixed.*
