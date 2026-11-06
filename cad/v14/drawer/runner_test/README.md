# V14 drawer runner test, interface 4 (print first)

This is one drawer's worth of runners. The rails ride on the drawer underside, and the 625ZZ rollers stay fixed to the floor.

## Parts
| File | Qty | Notes |
|---|---|---|
| `160_rail_R_guided` | 1 | PETG. Lay it on its side, slot facing up; it sits 45° on the bed (240 × 240). No supports. |
| `161_rail_L_floating` | 1 | Mirror of 160. Same print settings. |
| `162_station_front_R` / `_L` | 1 each | PETG. The front roller pair carries the load. |
| `163_station_rear_preload_R` / `_L` | 1 each | PETG. The rear pair stops the rail lifting. The rear-most roller sits in a 2 mm vertical slot so you can preload it. |
| `164_guide_block_R` | 1 | PETG. Two rollers on vertical axles against the R rail's inner face. The L rail floats. |

Bought parts: 10 × 625ZZ, 8 × M5 × 25 + nut (station axles, nut in the hex trap), 2 × M5 × 16 (guide axles, self-tapping into the 4.2 holes), 8 × M3 inserts (rail tops).

## Assemble
1. Put a 625ZZ on each station axle: the head goes on the slot side, the nut in the hex trap. Leave the slotted rear roller finger-loose.
2. Screw both stations to a board in line along the rail: front block rollers at y 207 / 225, rear at 165 / 183 (machine numbers). That's 18 mm between rollers in a pair and 24 mm between the pairs.
   - Put the R and L stations 600 apart, parallel.
   - Put the guide block on the inside of the R rail, between the two stations.
3. Slide each rail on **from its open front end** (the end with the lead-in). The rollers run inside the 16.5 slot.
4. Bolt a plank across both rail tops (4 inserts each).
5. Pull the drawer fully out and lift the rail tail gently. Raise the slotted rear roller until it just touches the lower slot wall, then tighten it.

## What it should do (CAD sweep in `runner_test_parts.json`)
- Free from 0 to 205 mm.
- A light click about 6 mm out: the detent bump lifts the rail 0.15.
- A hard stop at 205: the rear roller hits the closed slot end.

## Killer test
- Put 6-8 kg on the plank, centered about 130 mm past the front rollers (where a loaded drawer sits at full pull).
- Measure the droop at the plank's front edge.
- Pass:
  - droop under 2-3 mm
  - no binding
  - stop and detent still work after 50-100 cycles
- Report the droop, how the pull feels, and any wear or whitening.
