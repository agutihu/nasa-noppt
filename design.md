# HOMEBOUND — Game Design Document

HOMEBOUND is a solar system repair mission built for the NASA Space Apps Hackathon 2026.

## Premise

A pilot is stranded in orbit with a damaged ship. Laila, the ship's navigation core, is the
only companion standing between the pilot and home. The pilot must cross the solar system,
recover the parts needed to repair the ship, and fly home.

Every level in the game is built on one real planetary fact, and that fact is the mechanic.
Instead of teaching through text or quizzes, the player *experiences* planetary science.

## Story

The pilot wakes in a damaged orbit. Laila delivers the opening briefing: three critical parts
are scattered across the solar system. Bring them back and the ship can be rebuilt.

The emotional beat of the game is small and personal. The mechanics are cosmic. The two are
woven together through Laila's dialogue, which carries the human weight while the levels carry
the science.

## Design Pillars

1. **The fact is the mechanic.** Mars gravity is not a number on a screen — it is how the player
   jumps, how long the jump takes, how the rescue beacon must be approached. Heat on Mercury is not
   a stat panel — it is survival. Pressure on Venus is not a warning — it is the timer.
2. **Learn through play.** The tutorial teaches movement through doing. Hints come from Laila,
   not from a manual. The player learns the mechanics the same way the pilot learns to fly.
3. **Safety in failure.** Every lethal state resolves through a fair checkpoint or an in-world
   readable warning. The player should never feel cheated, only challenged.
4. **Science stays honest.** Every number the player sees is traceable to a NASA fact sheet. The
   game never smooths a fact for fun.

## Levels

| # | Level | Style | Real mechanic | Part recovered | Est. time |
|---|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial | Movement, interact, hint button | — (meet Laila) | 1 min |
| 1 | Mars | Platformer | 3.71 m/s² gravity; dust storm visibility | Navigation Module | 4 min |
| 2 | Mercury | Top-down stealth | Sun line sweep; heat meter; crater shadow | Solar Panel Array | 4 min |
| 3 | Venus | Timed survival | 92× pressure; canister cooling; 90 s limit | Hull Plating | 3 min |
| 6 | Earth | Assembly + stats | Drag parts onto ship; recap facts; stats screen | — (ending) | 2 min |

Jupiter, Saturn, Uranus, and Neptune ship as read-only "Data Archive" fact cards on the solar map.

## Level Design Details

### Level 0 — Earth orbit (tutorial)

Top-down, no fail state. Three-task arc:

1. Intro dialogue → objective "Fly to the beacon."
2. Reach pulsing beacon → objective "Collect the bracket crate below the ship."
3. Reach crate → objective "Press H to ask Laila for a hint."
4. Press H → Laila hint → win dialogue → back to map.

### Level 1 — Mars (platformer)

Low gravity and dust storms. Three-section design: easy gaps teaching long jumps, cliffs with
chaser, storm crossing with turret, then the part. Checkpoints at fixed x positions; camera
follows horizontally.

### Level 2 — Mercury (top-down stealth)

Sun line sweeps left-to-right; heat meter rises in sunlight and falls in crater shadow. Patrols
walk fixed paths; overheat at full heat damages the player.

### Level 3 — Venus (timed survival)

Arena survival: collect three hull fragments, use cooling canisters, avoid acid pools, reach the
escape beacon before the timer and pressure meter fill.

### Level 6 — Earth (finale / assembly)

Requires all three parts. Parts sit in a cargo tray; player clicks a part, then clicks a socket on
the ship. Placing a part plays Laila's fact for that planet. With all three placed, "Launch for
home" unlocks the stats screen.

## Core Mechanics

- **Movement.** Delta-time based. Top-down controllers use eight-direction jetpack movement with
  drift and braking. Platformer controllers use gravity from JSON, variable jump height, and coyote
  time.
- **Collection.** Parts are per-part flags, not counts. The player collects one of each required
  part before the finale unlocks.
- **Hazard readouts.** Meters (heat, pressure) combine color shifts with value readout and position
  changes so a colorblind player can still read them. Rapid flashing is capped below 1 Hz.
- **Dialogue.** Laila uses typewriter text, queued lines, triggers, and a manual hint mode (H).
- **Difficulty.** Easy / Normal / Hard scale hazard speed, timer length, hearts, and hint frequency
  through a single GameState multiplier set — levels never branch on difficulty directly.

## Educational Outcome

By the end of the run the player should have internalized, through play:

- How low gravity changes jump physics.
- How planetary temperature swings and shadows create stealth windows.
- How atmosphere and pressure constrain survival.
- That every gameplay rule maps to a real measurement.

The finale recaps the facts learned and shows run statistics, closing the loop between play and
learning.

## Art and Audio Direction

Art is fully procedural — planet discs, bands, craters, rings, sun, starfields, nebulae, ships,
drones, parts, hearts, and the Laila hologram are all drawn in code. No image assets block
production.

Audio is synthesized at runtime. No audio files ship with the game. Missing mixer support falls
back to silence safely.

## Win and Lose Structure

- The full arc is roughly 14 minutes of play.
- The player must collect all three required parts, then assemble the ship on Earth for the ending.
- Loss is fair: checkpoint respawn, readable meters, capped flashing, generous hint timing.
