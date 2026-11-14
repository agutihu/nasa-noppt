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

| # | Level | Style | Real mechanic | Part recovered |
|---|---|---|---|---|
| 0 | Earth orbit | Top-down tutorial | Movement, interact, hint button | — (meet Laila) |
| 1 | Mars | Platformer | 3.71 m/s² gravity; dust storm visibility | Navigation Module |
| 2 | Mercury | Top-down stealth | Sun line sweep; heat meter; crater shadow | Solar Panel Array |
| 3 | Venus | Timed survival | 92× pressure; canister cooling; 90 s limit | Hull Plating |
| 6 | Earth | Assembly + stats | Drag parts onto ship; recap facts; stats screen | — (ending) |

Jupiter, Saturn, Uranus, and Neptune ship as read-only "Data Archive" fact cards on the solar map.
The educational coverage stays wide without building more levels.

## Core Mechanics

- **Movement.** Delta-time based. Top-down controllers use eight-direction jetpack movement with
  drift and braking. Platformer controllers use gravity from JSON, variable jump height, and coyote
  time.
- **Collection.** Parts are per-part flags, not counts. The player collects one of each required
  part before the finale unlocks.
- **Hazard readouts.** Meters (heat, pressure) are rendered with color and position changes so a
  colorblind player can still read them. Rapid flashing is capped below 1 Hz.
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
