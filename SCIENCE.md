# HOMEBOUND — NASA Science Appendix

This document lists the real NASA data behind HOMEBOUND's mechanics, facts, and imagery.

## Planetary Facts in Play

| Key | Fact | Source to verify |
|---|---|---|
| `mars_gravity` | Mars has about 38% of Earth's gravity (3.71 m/s²) | NASA Mars Fact Sheet |
| `mars_dust_storms` | Dust storms can cover the whole planet for weeks | NASA Mars |
| `mercury_temps` | Day ~430 °C, night ~−180 °C | NASA Mercury Fact Sheet |
| `mercury_atmosphere` | Almost no atmosphere to hold heat | NASA Mercury |
| `venus_pressure` | Surface pressure ~92 × Earth | NASA Venus Fact Sheet |
| `venus_temp` | Surface ~465 °C, hotter than Mercury | NASA Venus |
| `earth_home` | 1 g gravity, 1 bar pressure, breathable atmosphere | NASA Earth |
| `jupiter_grs` | Great Red Spot is a storm wider than Earth | NASA Jupiter |
| `jupiter_radiation` | Radiation belts would fry an unshielded spacecraft | NASA Jupiter |
| `saturn_rings` | Rings are mostly water ice, extremely thin vs. width | NASA Saturn |
| `uranus_tilt` | Rotates on its side; ~42 years sunlight then ~42 years darkness per pole | NASA Uranus |
| `neptune_winds` | Winds over 2,000 km/h — fastest in the solar system | NASA Neptune |
| `tutorial_parts` | Tutorial introduces the three-part recovery mission | In-house briefing |

## Boot Screen Imagery

- Uses NASA's Astronomy Picture of the Day (APOD) via `tools/fetch_apod.py`, cached to
  `data/cache/apod.json` + `data/cache/apod.jpg`.
- Falls back to a bundled offline entry when the cache is missing or the fetch fails.

## Verification

All gameplay numbers and fact text must be checked against the NASA sources above before
submission. No fact in the game should ship without a source check.
