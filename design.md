# HOMEBOUND — Game Design Document

HOMEBOUND is a solar system repair mission built for the NASA Space Apps Hackathon 2026.

## Premise

A pilot is stranded in orbit with a damaged ship. Laika, the ship's navigation core, is the
only companion standing between the pilot and home. The pilot must cross the solar system,
recover the parts needed to repair the ship, and fly home.

Every level in the game is built on one real planetary fact, and that fact is the mechanic.
Instead of teaching through text or quizzes, the player *experiences* planetary science.

## Story

The pilot wakes in a damaged orbit. Laika delivers the opening briefing: seven critical parts
are scattered across seven worlds. Bring them all back and the ship can be rebuilt.

The emotional beat of the game is small and personal. The mechanics are cosmic. The two are
woven together through Laika's dialogue, which carries the human weight while the levels carry
the science.

## Design Pillars

1. **The fact is the mechanic.** Mars gravity is not a number on a screen — it is how the player
   jumps, how long the jump takes, how the rescue beacon must be approached. Heat on Mercury is not
   a stat panel — it is survival. Pressure on Venus is not a warning — it is the haze and the rain.
   Neptune's wind is not trivia — it pushes the player sideways.
2. **Learn through play.** The tutorial teaches movement through doing. Hints come from Laika,
   not from a manual. The player learns the mechanics the same way the pilot learns to fly.
3. **Safety in failure.** Every lethal state resolves through a fair checkpoint or an in-world
   readable warning. The player should never feel cheated, only challenged.
4. **Science stays honest.** Every number the player sees is traceable to a NASA fact sheet. The
   game never smooths a fact for fun.

## Levels

| # | Level | Real mechanic | Part recovered | Est. time |
|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial: movement, jump, fire, hint button | — (meet Laika) | 1 min |
| 1 | Mercury | Sun line sweep; heat waves; shadow hiding | Solar Panel Array | 4 min |
| 2 | Venus | 92× pressure haze; acid rain; geysers | Hull Plating | 4 min |
| 3 | Mars | 3.71 m/s² gravity; dust storm visibility | Navigation Module | 4 min |
| 4 | Jupiter | 2.5 g storm gravity; floating cloud platforms; lightning towers | Shield Generator | 4 min |
| 5 | Saturn | Ring debris showers between floating moonlets | Fuel Cells | 4 min |
| 6 | Uranus | 97° axial tilt; low horizon sun; methane haze; sideways rain | Thermal Regulator | 4 min |
| 7 | Neptune | 2,100 km/h supersonic winds; constant sideways push; meteors | Signal Antenna | 4 min |
| 8 | Earth | Assembly + stats | Drag all 7 parts onto ship; recap facts; stats screen | — (finale) | 2 min |

Missions unlock strictly in planetary order: win a world and the next padlock opens on the map.
Jupiter, Saturn, Uranus, and Neptune are full playable worlds, not fact cards.

## Level Design Details

### Level 0 — Earth orbit (tutorial)

Top-down, no fail state. Three-task arc:

1. Intro dialogue → objective "Fly to the beacon."
2. Reach pulsing beacon → objective "Collect the bracket crate below the ship."
3. Reach crate → objective "Press H to ask Laika for a hint."
4. Press H → Laika hint → win dialogue → back to map.

### Levels 1–7 — the seven worlds

Every planet world is generated from one seeded `data/levels/*.json` config through a shared
engine, so each world differs only in data: terrain profile, platform layout, hazards
(spikes, acid pools, ice patches, geysers, lightning towers, falling debris, wind), walkers,
saucers, checkpoints, and the part pedestal. Each world opens with a mission brief card, plays a
Laika start line, and ends at the labeled part, then the exit pad. Mars alone adds the recurring
dust storm that collapses visibility to a circle around the player (and hides enemy blips on the
minimap while active).

### Level 8 — Earth (finale / assembly)

Requires all seven parts. Parts sit in a cargo tray; player clicks a part, then clicks a socket on
the ship. Placing a part plays Laika's fact for that planet. With all seven placed, "Launch for
home" unlocks the stats screen, which now also lists the best time per mission.

## Core Mechanics

- **Movement.** Delta-time based. Top-down controllers use eight-direction jetpack movement with
  drift and braking. Platformer controllers use gravity from JSON, variable jump height, and coyote
  time.
- **Collection.** Parts are per-part flags, not counts. The player collects one of each required
  part before the finale unlocks.
- **Hazard readouts.** Meters (heat, pressure) combine color shifts with value readout and position
  changes so a colorblind player can still read them. Rapid flashing is capped below 1 Hz.
- **Dialogue.** Laika uses typewriter text, queued lines, triggers, and a manual hint mode (H).
- **Difficulty.** Easy / Normal / Hard scale enemy and hazard speed, storm timing, hearts, and
  hint frequency through a single GameState multiplier set — levels never branch on difficulty
  directly.

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
astronauts, aliens, saucers, parts, hearts, and the Laika hologram are all drawn in code. No
image assets block production.

Audio is synthesized at runtime. No audio files ship with the game. Missing mixer support falls
back to silence safely.

## Win and Lose Structure

- The full arc is roughly 14 minutes of play.
- The player must collect all three required parts, then assemble the ship on Earth for the ending.
- Loss is fair: checkpoint respawn, readable meters, capped flashing, generous hint timing.
