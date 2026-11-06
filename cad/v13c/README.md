# V13C packaging study (2026-11-05, Claude)

Question (ChatGPT round 1, vault c290): keep the V13 Z lift + yaw + hub + compact scoop, shrink bins, tier pitch,
Z travel and the deck to about 762 mm with 16 bins. Build V13C if it keeps 70-80 % of the V13 CAD, else go to V14.

**Answer: 762 is not reachable with the V13 lift + scoop under a scanner on the yaw axis.** The best V13C that keeps
the V13 deck is **1133 mm** (V13 was 1362.5). It keeps 92 % of the V13 part designs, but it misses the height by 371 mm.

## What was built (VARIANT=v13c)
| | V13 | V13C |
|---|---|---|
| Lower bins (wall / sill) | 140 / 70 | 112 / 42 |
| Upper bins | 140 | 52 |
| Usable volume per bin, lower / upper | 0.68 / 1.29 L | 0.40 / 0.40 L |
| Tier pitch | 166.5 | 138.5 |
| Z travel (H_MIN..H_MAX) | 236.5 | 148.5 |
| Scanner floor Z_S | 677 | 561 |
| Deck top Z_DECK | 629 | 513 |
| Body top / stud height | 1248 / 110.5 | 1069 / 60 |
| Upper chute leg | 62 deg | 45 deg |
| **Total (hopper rim = stud top)** | **1362.5** | **1133** |
| Lift rods / T8 screw | 400 / 360 | 310 / 270 |
| 2020 extrusion | 20.5 m | 19.1 m |

Same lift, yaw motor, hub, scoop, locators, carrier tiles, rails, latch, drum, trays, scanner, camera and electronics.
The deck moves down rigidly with the scanner. Scoop nose clearances (35) and the lower-window margin (10.8) are the V10 values.

## Why 762 can't be reached (height_floor.json, scripts/height_floor.py)
The scanner floor has to sit above the scoop at the upper dump pose:
`Z_S = Z_C 60 + 13.5 + H_L + 26.5 + H_U + 35 + 198.5 (scoop height at 40 deg) + 63 (25 margin + 38 door drop)`.
The lower bin wall is at least `sill + 70`, so the part on the scoop nose can pass under the upper carrier.
- With the V13 deck kept, the deck adds 572 above Z_S. Even with empty bins the total is >= 1018 mm.
- A new V14-style deck (312 tall + 60 studs above the deck underside at Z_S - 53) needs Z_S <= 443.
  Even with 0 L bins and tightened clearances (nose 20, margin 5), Z_S is 446, so the total is 765.
  With 0.25 L bins it is 815 to 850 mm.
- The stack-up in c290 (deck underside near 390) skipped the scoop's own 198.5 mm height and the lower-bin window.

## Parts that survive unchanged (part_survival.json)
- **69 of 75 printed designs (92.0 %)** and **252 of 282 printed pieces (89.4 %)**.
  Rule: same volume (+-1 mm3) and the same bounding box (+-0.1) as a V13 rebuild. That rebuild matches all 36
  V13 STEPs in `reference_v13/` exactly.
- Changed: bins 40 and 41 (shorter), chute 51 upper and lower (45 deg), lift pedestal leg 63 (79.1 instead of 107.1),
  and stud ring quarter 78 (60 tall).
- Bought parts that get re-cut: the 2020 extrusions, the 12 mm rods and the T8 screw.

## Clash checks (checks_v13c.json; V13 rebuild with the same checks: checks_v13_same_sweep.json)
- **Lift and yaw sweep:** 16 lift heights (every 10 mm, H_MIN to H_MAX, plus every delivery height) x 25 yaws
  (every 7.5 deg, -90 to +90). 3280 exact booleans: carriage, yaw motor, hub and scoop against every fixed part,
  including both drawers.
  - **12 hits: the scoop grazes the lift top rod brace 03 (0.8-8.2 mm3).** This happens at lift 175-185, about
    60-70 below H_MAX, at |yaw| 37.5-52.5.
  - All 16 delivery poses are clean.
  - **Inherited from V13:** the same sweep on the V13 rebuild hits at lift 265-275, the same spot relative to H_MAX.
    V13's 24-pose check missed it.
  - Fix: move Z only with |yaw| <= 30, or notch the brace.
- **Drawers closed: 4 hits. The lower slot 1 and 8 bins hit the upper carrier side bars 65 (0.5 and 4.8 cm3).**
  The side bars hang 23 below the upper carrier, but the tier gap is 10. **Inherited:** the same 4 hits are in V13.
  Fix: side bars 65 at most 9 tall, or move them outboard of r 298.
- Deck (isolation) parts: only the by-design drive core / tire overlap. Drum turned in 30 deg steps: 0.
  Doors open vs scoop: 0. Drawers 350 mm out: 0. Latch blocks closed, free when lifted.
- New parts: all are valid single solids, watertight, and fit the 248 bed.

## Gate
92 % reuse, but 1133 mm against a 762 target: **V13C fails the height gate. Go back to V14** (or accept ~1.1 m).

## Run
```
cd cad/v13c/scripts
python3 prep_ref.py                                      # V13 STEPs loaded by file -> ref/
VARIANT=v13 SKIP_CHECKS=1 python3 build_machine_v13c.py  # V13 baseline parts
VARIANT=v13c python3 build_machine_v13c.py               # V13C + all checks (~10 min)
python3 compare_parts.py; python3 height_floor.py; python3 render_v13c.py v13c
```
Stills: `stills/v13c_1_closed.png`, `v13c_2_no_shell_upper_dump.png`, `v13c_3_side_762_line.png`.
Changed part STEPs (print pose): `parts/`.
