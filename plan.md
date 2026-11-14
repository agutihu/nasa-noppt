# HOMEBOUND — 24-Hour Build Plan

**NASA Space Apps Hackathon 2026**
Working title: **HOMEBOUND** — *a solar system repair mission*
Guide character: **Laila**

A stranded pilot must cross the solar system, recover three critical ship parts, and fly home.
Every level is built on one real planetary fact, and that fact is the mechanic.

---

## 1. Decisions locked at kickoff

| Item | Decision | Why |
|---|---|---|
| Guide name | **Laila** (not Laika) | Matches Victoria's brief; the PDFs say it is a find/replace |
| Shipped levels | **0 Tutorial, 1 Mars, 2 Mercury, 3 Venus, 6 Earth finale** | 5 levels is a complete, demoable arc in 24h |
| Cut levels | Jupiter (4) and Saturn (5) | Highest effort / lowest time-to-playable |
| Python | 3.12 pinned (3.11 also fine) | Matches `pygame-ce` wheels; 3.14 may not have wheels yet |
| Game library | **pygame-ce** (`pip install pygame-ce`) | Faster, maintained, better pygbag support. Never install plain `pygame` |
| Resolution | **1280 × 720**, 60 FPS, 32 px tiles for Mars | One target for all art and layouts |
| Target | **Desktop first**, async-friendly loop for a late pygbag build | Never risk the demo on a web port |
| Art | **Procedural shapes** drawn in code + optional PNG fallback | Zero asset blocking; consistent retro look |
| Audio | Tiny synthesized / royalty-free SFX, mute toggle, missing file = silence | Audio must never crash the game |
| Real NASA data | **APOD on the title/boot screen, cached to JSON** with bundled fallback | Visible API use, works offline |
| Extras | Pause menu, mute, **save/load progress** | Cheap, expected, judged well |
| Dropped extras | Quiz, gamepad, leaderboards, live AI dialogue | Not worth the hours |
| Language | English only | One language pass, no i18n work |
| Repo | Public: `github.com/imamsanghaarc/nasa` | Submission + judging |

---

## 2. What ships and what does not

### Ships

| # | Level | Style | Mechanic from real data | Part recovered | Minutes |
|---|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial | Movement, interact, hint button | — (meet Laila) | 1 |
| 1 | Mars | Platformer | 3.71 m/s² gravity (~38% Earth) → floaty long jumps; dust storm cuts visibility | Navigation Module | 4 |
| 2 | Mercury | Top-down stealth | 430 °C day / −180 °C night → sun line sweeps, heat meter, hide in crater shadow | Solar Panel Array | 4 |
| 3 | Venus | Timed survival | 465 °C, 92 bar pressure → pressure meter only slows with cooling canisters | Hull Plating | 3 |
| 6 | Earth | Assembly + stats | Drag 3 parts onto the ship; recap facts; stats screen | — (ending) | 2 |

**Total play time ≈ 14 minutes.** A judge can see everything in one sitting.

### Does not ship (but still appears in the game)

Jupiter and Saturn levels are cut, but their **facts stay in the game** as read-only
"Data Archive" cards on the solar system map (Phase 7 bonus, ~30 min). The map then shows
all planets and the educational coverage stays wide without building two more levels.

### Never cut, no matter what

Tutorial, Laila's dialogue + hints, the part-collection loop, the fact display, win and lose states.
Those are the story and the judging criteria.

---

## 3. Player flow

```
boot (APOD splash, cached) → menu (Play / Continue / Settings / Quit)
   → solar map (hub; shows parts collected, unlocks)
       → Tutorial (auto on first run)
       → Mars | Mercury | Venus (any order, unlocked after tutorial)
       → Earth finale (unlocked when all 3 parts collected)
   → stats screen → menu (or New Game)
```

- Any planet can be replayed; parts are per-part flags, not counts.
- Pause overlay works in every scene (Esc), with Resume / Restart / Mute / Quit to map.
- Progress auto-saves on part pickup and on scene change; "Continue" loads it.

---

## 4. Architecture

One engine, many planets. Every screen is a `Scene`; the manager never knows what a scene does.

```python
class Scene:
    def handle_events(self, events): ...
    def update(self, dt): ...          # seconds, not frames
    def draw(self, screen): ...
```

Data flow (one direction, no globals):

```
data/*.json  ──►  core.levels.load_level()  ──►  Scene
                                              │
GameState  ◄── read/write parts, facts, deaths, difficulty, elapsed
                                              │
                    ui.HUD / ui.DialogueBox / ui.Meter  ──►  screen
```

### Folder structure (tagged with owner — see `developer.md`)

```
space-game/
  main.py                 # [Sulaiman] async main loop, window, bootstrap
  requirements.txt        # [Sulaiman]
  core/                   # [Sulaiman] engine
    scene.py              # Scene base + SceneManager (switch/push/pop)
    game_state.py         # GameState + difficulty multipliers
    save.py               # save/load JSON in user dir
    levels.py             # [Sanghaar] JSON loader + validation + path helper
    assets.py             # font/image/sound loading with graceful fallback
    audio.py              # sfx play, mute, no-crash if missing
    settings.py           # WIDTH, HEIGHT, FPS, colors, paths
  scenes/                 # screens
    boot.py  menu.py  map.py  ending.py     # [Sulaiman]
    tutorial.py  mars.py  mercury.py  venus.py   # [Sanghaar]
  entities/               # [Sanghaar] gameplay objects
    player.py             # shared movement + platformer + top-down variants
    enemies.py            # chaser, patrol, turret (turret optional)
    hazards.py            # dust storm, sun sweep, acid, debris, radiation
    pickups.py            # part, health, canister, fragment
  ui/                     # [Sulaiman]
    hud.py  dialogue_box.py  meter.py  button.py  pause.py  stats.py
  art/                    # [Sanghaar] procedural drawing helpers
    planets.py  sprites.py  backgrounds.py
  data/
    planets.json          # [Sanghaar] map data, facts, unlock rules
    levels/*.json         # [Sanghaar] per-level params
    dialogue/*.json       # [Sanghaar] Laila lines
    cache/apod.json       # [Sulaiman] fetched once by tools/fetch_apod.py
  assets/
    fonts/  images/  sounds/   # optional; game runs with none of them
  tools/
    fetch_apod.py         # [Sulaiman] run once before the sprint, commits result
```

### Engineering rules

1. **Delta time everywhere.** No `time.sleep`, no frame-counted timers.
2. **No blocking calls in the loop.** Async-friendly `main()`, so pygbag stays possible.
3. **All numbers in JSON.** Leslie/Fatima can retune without touching Python.
4. **One `GameState`.** No module-level mutables; scenes receive the state object.
5. **Asset paths only through `core.assets.path()`.** Missing asset = fallback shape, never a crash.
6. **`main` branch must always launch.** Merge only at gates; a broken main is the only emergency.
7. **60 FPS target.** Profile any scene below 45 and note the heavy moment.

---

## 5. Data formats

### `data/planets.json` (map + archive cards)

```json
{
  "order": ["mercury", "venus", "mars", "jupiter", "saturn"],
  "planets": [
    {
      "id": "mars",
      "name": "Mars",
      "part": "Navigation Module",
      "playable": "mars",
      "map_position": [0.68, 0.55],
      "color": "#c1440e",
      "fact": "Mars has about 38% of Earth's gravity (3.71 m/s²).",
      "facts": ["mars_gravity", "mars_dust_storms", "mars_atmosphere"],
      "unlock": ["tutorial_done"]
    },
    {
      "id": "jupiter",
      "name": "Jupiter",
      "part": "Shield Generator",
      "playable": null,
      "map_position": [0.42, 0.38],
      "color": "#d9a066",
      "fact": "The Great Red Spot is a storm wider than Earth.",
      "facts": ["jupiter_radiation", "jupiter_grs"],
      "unlock": []
    }
  ]
}
```

`playable: null` renders the planet as a **Data Archive** card (fact only, no mission).

### `data/levels/<id>.json`

```json
{
  "id": "mars",
  "name": "Mars",
  "style": "platformer",
  "part": { "name": "Navigation Module", "color": "#8fd3ff" },
  "params": {
    "gravity": 3.71,
    "jump_speed": 520,
    "move_speed": 260,
    "storm_interval": 25,
    "storm_duration": 8,
    "visibility_radius": 120,
    "checkpoint_x": [0, 1800, 3600]
  },
  "hint_rules": { "idle_seconds": 45, "deaths": 3 },
  "dialogue": "dialogue/mars.json",
  "facts": ["mars_gravity", "mars_dust_storms"],
  "unlock": ["tutorial_done"]
}
```

Difficulty multiplies only JSON values: hazard speed ×0.75/1.0/1.25, timer ×1.25/1.0/0.85,
hearts 5/3/2, hint idle 20/45/∞ seconds.

### `data/dialogue/<id>.json`

```json
{
  "speaker": "Laila",
  "lines": [
    { "trigger": "start",   "text": "Three point seven one metres per second squared. That is Mars gravity — thirty-eight percent of home. Jump like you mean it." },
    { "trigger": "storm",   "text": "Dust storm rolling in. Visibility is dropping. Keep moving toward the light." },
    { "trigger": "death_3", "text": "Hold jump longer for height. Release early for short hops." },
    { "trigger": "win",     "text": "Navigation Module recovered. Now we can find our way home." }
  ]
}
```

### `data/cache/apod.json`

```json
{ "title": "...", "explanation": "...", "url": "...", "media_type": "image",
  "date": "2026-11-14", "fetched_at": 1763... , "offline_fallback": true }
```

`tools/fetch_apod.py` runs once; if it fails, the committed file keeps the game working forever.

### Facts used (verify against NASA before freeze)

| Key | Fact | Source to verify |
|---|---|---|
| mars_gravity | 3.71 m/s², 38% of Earth | NASA Mars Fact Sheet |
| mars_dust_storms | Storms can cover the whole planet for weeks | NASA Mars |
| mercury_temps | Day ~430 °C, night ~−180 °C | NASA Mercury Fact Sheet |
| mercury_atmosphere | Almost no atmosphere to hold heat | NASA Mercury |
| venus_pressure | Surface pressure ~92× Earth | NASA Venus Fact Sheet |
| venus_temp | Surface ~465 °C, hotter than Mercury | NASA Venus |
| (archive) jupiter_grs, jupiter_radiation, saturn_rings_ice | see PDFs | NASA |

---

## 6. Level specs (build-ready)

### Level 0 — Earth orbit (tutorial)

- **Goal:** learn move, interact, hint button; meet Laila; open the map.
- **Layout:** single screen, wrecked ship, three floating markers: move to marker → pick up a
  small item → press `H` when Laila prompts.
- **Win:** all three tasks. **Lose:** none. **Fail-safes:** no hazards.
- **Done when:** a first-time player finishes in under 90 s without instructions.
- **JSON:** `move_speed`, `markers` (positions), `hint_rules`.
- **Effort:** S.

### Level 1 — Mars (platformer)

- **Goal:** reach the lander wreck and take the Navigation Module.
- **Mechanic:** low gravity (3.71) → high, floaty jumps; every 25 s a dust storm dims the screen
  to a 120 px visibility circle for 8 s.
- **Layout:** 3 sections — (a) easy gaps teaching long jumps, (b) cliffs + 1 chaser drone,
  (c) storm crossing + 1 turret, then the part.
- **Hazards:** gaps (fall → last checkpoint), 2 chasers, 1 turret, storm.
- **Hearts:** 3 (difficulty-scaled). **Win:** pick up part. **Lose:** hearts 0 → checkpoint respawn,
  deaths++.
- **Laila beats:** start (gravity fact), first storm (move toward light), 3 deaths (jump timing), win.
- **Done when:** winnable and losable; storm never flashes faster than 1 Hz.
- **Effort:** M (biggest single file).

### Level 2 — Mercury (top-down stealth)

- **Goal:** cross the sunlit surface to the outpost, take the Solar Panel Array.
- **Mechanic:** a sun line sweeps right→left at `sun_speed`; heat meter rises in sunlight, falls in
  crater shadow; full meter = damage. Patrol drones roam shadows.
- **Layout:** crater shadows as safe pockets; the player must stay ahead of or behind the line.
- **Hazards:** heat meter, 2–3 patrol drones. (Cold slow-zones are optional; drop first.)
- **Win:** reach part. **Lose:** heat full 3× or hearts 0. **Hearts:** 3.
- **Laila beats:** start (430/−180 swing), meter orange (hide in a crater), win (why extremes).
- **Done when:** a first-timer survives the first sweep; meter legible at a glance.
- **Effort:** M.

### Level 3 — Venus (timed survival)

- **Goal:** collect 3 Hull Plating fragments inside the arena, then reach the exit.
- **Mechanic:** pressure meter rises constantly, only slowed by cooling canisters; 90 s limit.
- **Layout:** arena with fragments at 3 corners, acid pools between them, heavy movement
  (slower acceleration than Mars).
- **Hazards:** acid pools (damage over time), 1 chaser. Falling debris is optional.
- **Win:** 3 fragments + exit before timer/meter. **Lose:** pressure full or timer 0.
- **Laila beats:** start (465 °C, 92 bar), mid (countdown), win (hotter than Mercury).
- **Done when:** winnable in 90 s with ~20 s to spare; timer never invisible.
- **Effort:** S (reuses meter, pickups, chaser).

### Level 6 — Earth (finale)

- **Goal:** assemble the ship and land.
- **Part A (required):** drag each collected part onto the ship; each snaps with its planet fact.
- **Part B (optional, cut first):** gentle 15 s re-entry dodge reusing simple controls.
- **Win:** land → stats screen: time, deaths, parts, facts learned.
- **Done when:** only reachable with all 3 parts; stats survive a restart.
- **Effort:** S.

---

## 7. 24-hour phased schedule

`H0` = the moment you both open the repo. Merge gates are fixed; anything unfinished at a gate
is cut, not carried.

| Phase | Hours | Owner(s) | Deliverable | Gate |
|---|---|---|---|---|
| **P0 Kickoff** | H0–H1 | both | repo cloned, venv, `pygame-ce` installs, branches made, these docs read, ownership confirmed | `python main.py` opens a window |
| **P1 Skeleton & contracts** | H1–H4 | Sulaiman: scene manager, GameState, save, assets/audio, settings. Sanghaar: JSON schema, loader, tutorial data, Laila script, entity base, procedural art helpers | menu → dummy scene → back | **G1 merge** |
| **P2 Vertical slice** | H4–H7 | Sulaiman: HUD, DialogueBox, Button. Sanghaar: tutorial scene + hints | A stranger finishes the tutorial and can read a fact | **G2 merge** |
| **P3 Mars** | H7–H11 | Sanghaar: platformer, storm, chaser, turret. Sulaiman: hearts, Meter base, pause overlay | Mars winnable **and** losable, restart is fair | **G3 merge** |
| **P4 Mercury** | H11–H15 | Sanghaar: sun sweep, heat meter wiring, patrols. Sulaiman: map screen with unlocks + part icons | Mercury winnable from the map after tutorial | **G4 merge** |
| **P5 Venus** | H15–H17.5 | Sanghaar: timer, pressure, canisters, fragments. Sulaiman: difficulty multipliers applied in GameState | Venus winnable in 90 s | **G5 merge** |
| **P6 Close the loop** | H17.5–H20 | Sulaiman: ending assembly, stats, save/load, APOD boot screen. Sanghaar: ending dialogue, balance pass | New game → 3 parts → Earth → stats → relaunch continues | **G6 merge** |
| **P7 Polish** | H20–H22 | both | SFX, screen shake, particles, archive cards, fact verification, FPS check | stable 60 FPS, all facts verified | **G7 merge** |
| **P8 Freeze & demo** | H22–H23.5 | both | README, screenshots, `v1.0` tag, 3-min demo recorded, submission text | code frozen | **freeze** |
| **P9 Buffer** | H23.5–H24 | both | submission fields, zip/links, optional pygbag attempt | submitted |

### Phase detail

**P0 (H0–H1) — Kickoff**
1. `git clone`, `python -m venv .venv`, activate, `pip install pygame-ce`, freeze requirements.
2. Confirm `import pygame` is pygame-ce (`pygame.version.ver`).
3. Both create branches: `feat/engine`, `feat/levels`.
4. Send the team a 5-line message: name is Laila, scope is 5 levels, desktop demo, we need facts
   confirmed (table in §5), art is procedural.
5. `tools/fetch_apod.py` run by Sulaiman **once**, commit `data/cache/apod.json`.

**P1 (H1–H4) — Skeleton and frozen contracts**
Sulaiman: `Scene`/`SceneManager`, async `main()`, `GameState`, save/load, `settings`, asset/font
helpers, dummy scene. Sanghaar: `core/levels.py`, `data/planets.json`, `data/levels/tutorial.json`,
`data/dialogue/tutorial.json`, `entities/player.py` base, `art/*` primitives (planet disc, starfield,
ground tiles, glow).
*Gate:* window opens, menu → dummy scene → Esc → menu. Contracts in `developer.md` unchanged unless
both agree in the chat.

**P2 (H4–H7) — Vertical slice**
Sulaiman delivers HUD (hearts + parts + timer slot), DialogueBox (typewriter, `H` hint, page by
click/space), buttons. Sanghaar delivers the tutorial scene wired to dialogue and the map unlock.
*Gate:* someone outside the pair completes the tutorial and later says one fact they learned.

**P3 (H7–H11) — Mars**
Sanghaar: platformer controller (coyote time 100 ms, variable jump), 3-section layout, checkpoints,
storm overlay with smooth fade, chaser/turret. Sulaiman: hearts component, generic `Meter`, pause
overlay reusable by all scenes.
*Gate:* Mars is winnable and losable; death always returns to a checkpoint, never mid-air over a gap.

**P4 (H11–H15) — Mercury**
Sanghaar: horizontal sun band with shadow pockets, heat rise/fall, vision tint, patrols. Sulaiman:
solar map with planet positions from `planets.json`, part/check icons, archive cards stub.
*Gate:* Tutorial → map → Mercury is reachable with no console errors.

**P5 (H15–H17.5) — Venus**
Sanghaar: 90 s timer, pressure meter, canisters, 3 fragments, acid pools, heavy movement.
Sulaiman: difficulty setting screen values applied through `GameState` multipliers, mute toggle.
*Gate:* Venus winnable under 90 s on Normal; Easy is noticeably easier.

**P6 (H17.5–H20) — Close the loop**
Sulaiman: Earth assembly (drag parts, snap, show fact), stats, save/load auto-hooks, boot screen
with APOD image/fallback. Sanghaar: ending lines, full-run balance, retune JSON.
*Gate:* cold start → tutorial → 3 planets → Earth → stats → relaunch → Continue works.

**P7 (H20–H22) — Polish**
SFX for pickup/hit/jump/win, screen shake on hit, dust/star particles, archive cards for
Jupiter/Saturn, fact verification pass, FPS check on the heaviest moment (Mars storm + Venus timer).
*Gate:* no fact text without a NASA source check; 60 FPS sustained.

**P8 (H22–H23.5) — Freeze and demo**
README with screenshots and run steps, tag `v1.0`, record a 3-minute demo following §10,
write submission text. **No new features after H22.**
*Gate:* repo cloned fresh on a second machine runs the demo path.

**P9 (H23.5–H24) — Buffer**
Submit early, keep 30 minutes for upload/link problems. Optional pygbag test only if the build is
already safe.

---

## 8. Git workflow

- Branches: `feat/engine` (Sulaiman), `feat/levels` (Sanghaar). Short-lived sub-branches only if
  a feature risks breaking your own branch.
- Push at least every 2 hours, even if incomplete — the other person needs your stubs.
- Commit style: `type(scope): what` → `feat(mars): dust storm visibility overlay`,
  `fix(hud): meter not resetting on restart`, `data(venus): pressure rate tune`.
- **Merge windows at G1–G7 only.** Whoever is free merges, then both pull `main` immediately.
- If `main` is broken, fixing it beats any feature. Nothing else merges until it runs.
- Tag `v1.0` at freeze; tag `demo` if a later fix ships.

---

## 9. Testing checklist (run at every gate)

- [ ] Fresh clone + venv + `pip install -r requirements.txt` + `python main.py` works.
- [ ] Menu → map → each unlocked planet → back to map works with no traceback.
- [ ] Every level loads from JSON; no magic numbers in scene files.
- [ ] Every level can be **won** and **lost**; both result screens work.
- [ ] Deaths respawn at a fair checkpoint; no infinite fall loops.
- [ ] Laila hints fire on idle (45 s), 3 deaths, and `H`; text is readable at 1280×720.
- [ ] Part pickup shows on the HUD and persists after restart (save/load).
- [ ] Pause (Esc) works in all scenes; mute works; volume never stuck at 0.
- [ ] Timer and meters are visible, never covered by the dialogue box.
- [ ] Facts match the verified table; no hallucinated numbers.
- [ ] No rapid flashing > 1 Hz (storms, hits); colourblind-safe hazard colours (shape + colour).
- [ ] 60 FPS on the heaviest moment; note any dip.
- [ ] Runs on a second machine, different OS/resolution.
- [ ] Alt-tab, window resize, and missing `assets/` files do not crash.

---

## 10. Cut order if the clock runs out

Cut in this order, top first:

1. Venus falling debris (keep acid + timer).
2. Mercury cold slow-zones (keep sun + heat).
3. Earth re-entry dodge (keep assembly + stats).
4. Secondary enemies (turret on Mars, third patrol).
5. Particles / screen shake.
6. Archive cards for Jupiter and Saturn.
7. APOD live image (keep the cached text card).
8. Save/load (worst case: single-session game).
9. **Venus level entirely** (Arc becomes Tutorial + Mars + Mercury + Earth).

Do **not** cut: tutorial, dialogue/hints, part loop, fact display, win/lose, pause.

---

## 11. Three-minute demo script (for judges)

1. **0:00** — Boot screen: APOD image with title and "data: NASA APOD".
2. **0:15** — Menu → map. Say: "Three parts, seven planets, one ride home."
3. **0:30** — Tutorial: Laila introduces the mission and the parts; collect the first marker.
4. **1:00** — Mars: jump in 38% gravity, a dust storm hits, recover the Navigation Module.
5. **1:40** — Mercury: outrun the sun line, hide in a crater, heat meter saved you.
6. **2:15** — Venus: 92 atmospheres, 90 seconds, three fragments, escape.
7. **2:45** — Earth: drag the parts on, facts recap, stats screen.
8. **3:00** — Close: "Every mechanic is a real planetary fact — gravity, sunlight, pressure.
   Cached so it runs offline."

---

## 12. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Mars platformer eats the schedule | High | Time-box to H11; cut section (c) first, keep storm |
| pygbag/web export fails at the end | Medium | Desktop is the demo; async loop + no blocking calls from day one |
| Two devs editing the same file | Medium | Folder ownership + frozen contracts (`developer.md` §2) |
| Sulaiman unavailable | Medium | Sanghaar absorbs in the order listed in `developer.md` §8 |
| APA/APOD fetch fails during judging | Low | Cached JSON committed; game never needs internet |
| Fact errors embarrass the team | Medium | Verification table §5, checked at P7 |
| Python 3.14 has no pygame-ce wheel | Medium | Install 3.12 side-by-side for the project |
| Merge conflict costs an hour | High | Merge only at gates; push every 2 h; no shared files |

---

## 13. Open items for Victoria / the team

1. **Name confirmed: Laila** — reply "yes" so art and dialogue files can be finalised.
2. **Scope confirmed:** tutorial + Mars + Mercury + Venus + Earth assembly. Jupiter/Saturn become
   fact cards. Object now or after H4 it is expensive.
3. **Resolution 1280×720**, procedural art. If Bryan has sprites, send them by H8 with fixed frame
   sizes, otherwise the game ships procedural.
4. **Desktop demo** for judging; a web link is a bonus only.
5. **Facts:** who signs off the NASA numbers (Leslie?) — we need the check at H20.
6. Does the team want the "Data Archive" cards for Jupiter and Saturn? (30 min, adds coverage.)

---

## 14. Judging alignment (Space Apps 1–5 rubric)

Every feature below exists to defend a specific criterion. Point judges at them by name.

| Criterion | What the game does | Where judges see it |
|---|---|---|
| **Impact** | Teaches real planetary science through mechanics rather than text; difficulty settings and accessibility make it playable by anyone; fact logging rewards curiosity | Fact cards on the map, stats screen, Easy/Normal/Hard + Large text options in Settings |
| **Creativity** | One idea carries the whole design: *the fact is the mechanic*. Laila (a holographic navigator) delivers every fact diegetically, never as a pop-up | Laila's dialogue, hologram art, fact-driven meters |
| **Validity** | Numbers are real and sourced: Mars 3.71 m/s², Mercury −180/430 °C, Venus 92 bar/465 °C. Runs offline, 60 FPS, tested by automated smoke + playtest suites | In-game meters show real units (°C, bar); `tools/smoke_test.py` and `tools/playtest.py` in the repo |
| **Relevance** | NASA data is the core loop, not decoration: planetary fact sheets drive every rule, cached APOD opens the game, sources are cited on every fact card | Boot screen (APOD credit), map fact cards ("NASA Planetary Fact Sheet"), ending stats footer |
| **Presentation** | 3-minute demo script (§11) with a fixed story beat per minute | Demo video + README |

### Hard rules for the remaining hours

1. No fact appears on screen without a NASA source behind it. If Leslie cannot source a number, the line gets cut.
2. Every meter carries real units (°C, bar, m/s²) so a judge can verify values at a glance.
3. The game must run from a fresh clone with no internet — cached APOD, no live calls.
4. Accessibility ship-list: difficulty settings, text size, mute, pause, colour+shape hazard coding (storm = dark vignette, sun = orange line, acid = jagged green pools). Never colour alone.
5. The presenter's story: *"We turned planetary data into game rules. You don't read that Mars has 38% gravity — you feel it in the jump."*
