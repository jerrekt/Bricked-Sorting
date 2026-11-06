# V14 module K: deck (drum, hopper, trays, scanner, electronics)

Built to **v14-interface-4.1** (frozen) on branch `cad-v14-deck`.
- Script: `build_deck.py` (CadQuery 2.8). It reads `../interface.json` and the V13 STEPs in `../../reference_v13/`. Helpers are in `k_common.py`, a copy of `cad-v14-all:cad/v14/common.py`, so this branch builds on its own.
- Outputs:
  - `world/`: STEP in machine coordinates, plus `deck_assembly.step`
  - `print/`: new parts laid flat
  - `parts.json`, `checks.json`, and 4 stills

Coordinates are right-handed: +X is the front viewer's left, +Y is the front, +Z is up.

## Brick path and heights
| Stage | Where | z |
|---|---|---|
| Hopper | Bowl in stud L (r 142 at 779 → r 97), throat r 97 through the roof hole, then an oblique cone to the outlet at (-200, -75) | 779 → 660 |
| Feed chute 202 | U trough, 43° slope, ends 22 mm inside the drum's rear end, 18 below the axis | 658 → 569 |
| Drum (V13, as-is) | Axis front-back at x -200, rear end at y 0, tilted **6°** down toward +Y | axis 589 → 570 |
| Outlet | 49b window at the bottom of the front plate (y ≈ 184) | 503 |
| V1 203 (long, 2 pieces + splice) | Along +X at y 212, from x -245 to 75. Low lip under the outlet. | 491 → 486 |
| V2 204 (short) | Diagonal from (65, 205) to (262, 8). Notched where V1 drops in. | 478 → 473 |
| Landing ramp 211 | V13 ramp, lowered to 8 mm | 467 → 459 |
| Scanner floor (doors) | Over (330, 0) | 459 |
| Drop funnel 220 | Mouth r 54 at z 415 (under the open door tips at 416). 45° cone to r 28, then a tube through the deck hole. | exit **335** |

## Parts
**Drum, reused as-is.** The whole V13 drum group is moved rigidly into the new frame: 47b barrel, 49b static plate, 48 rear guard, 4 × 50 rollers, 54 core, 55 TPU tire, 56 NEMA17 bracket.

**New: drum supports.**
- **205 cradles A/B.** Each roller sits between two 5 mm axle forks (M5). A cheek carries the 49b ear (two M3 at axial 166/178, as in V13). Bases bolt to the deck grid.
- The motor wall that holds bracket 56 (4 × M5 in its slots) is merged into cradle B.

**New: hopper and chute.**
- **200** bowl in 4 quarters.
- **201** throat. Three tabs screw up into the roof underside.
- **202** feed chute.

**New: trays.**
- **203** V1 (two pieces plus a splice).
- **204** V2.
- **207** PETG leaf springs: 2 mm blades leaning 20°, with feet on the deck grid. 3 under V1, 2 under V2.
- V7 vibration-motor saddle 62 and cap 63 are reused under each tray (24 mm motor).

**New: scanner (210-218).** A rework of V13 57-62/73/74: same plate, trapdoors, slider, MG996R saddle, camera bridge, LED holders, XIAO Sense and APDS mounts.
- Scanner floor at z 459.
- Standoffs moved onto the deck grid at x 240/440, y ±80.
- Ramp lowered.
- The V13 small parts 57d slider, 59/59b links and 60 horn arm are reused unchanged.

**New: funnel and electronics.**
- **220** drop funnel, with a flange on the deck grid.
- **225** two electronics trays at y -238..-150, top at z 424, level with the bottom of the back access panel. Pads with inserts at the board corners.
  - Tray 1: PSU, buck, XT30 inlet.
  - Tray 2: XIAO C3, 3 × TMC2209, MCP23017, DRV8833.

## Checks (`checks.json`)
- All parts are inside the K zone.
  - The funnel stays within r 30 below the deck (z 335..390).
  - The hopper stays within r 97 through the roof hole and r 142 inside the stud ring.
- No clashes. The listed by-design contacts are springs and saddles touching their trays, and core and tire.
- Drum turning at 12 angles (barrel + guard): 0 clashes against everything fixed, including the chute inside the rear opening.
- Scanner doors at 0/30/60/90°: 0 clashes with the funnel, ramp, saddle, APDS mount and post.
- Every new part fits 248³.
- Estimated new PLA/PETG: **~1.7 kg**. The drum parts already exist (V13).

## Print notes
- **Cradles 205:** tall forks, print with tree supports.
- **Hopper:** bowl quarters printed rim-down. Join them with glue or M3 tabs (the tabs aren't modeled yet, see open questions).
- **Trays:** PETG, walls up.
- **Leaf springs:** PETG, on their side, so the blade layers run along the bend.
- **Scanner plate and funnel:** upside down.
- **Drum:** print order is as in the V13 note (49b first, then 47b).

## Open questions
1. **Drum tilt is 6°, not V13's 8°.** At 8° the rear end rises 7 mm more, and either the hopper cone hits the drum top or the feed chute drops under 40°. If bricks walk too slowly, the barrel can go back to 8° by lowering the scanner (not possible without shrinking the door swing) or by shortening the hopper. Easier first try: speed up the drum motor.
2. **Tray slopes are only ~1-2°.** The trays rely on vibration, as V13 did at ~4.6°. Test V1 with a motor before printing V2.
3. **Hopper bowl seams:** add printed tabs or glue them? Undecided.
4. **The roof (F) needs 3 M3 inserts** under the hopper throat tabs, at r 108 from (-260, 0), angles 30/150/270°.
5. **Electronics dimensions are placeholders.** PSU 165 × 60 × 38, TMC carrier 70 × 50, and so on. Measure the real boards; the pads are placed from `EL` in the script.

## INTERFACE REQUESTS
None. The module builds to 4.1 as frozen. Notes for F at integration:
- The deck grid holes this module uses are listed per part in the script (cradles, springs, standoffs, funnel flange, electronics legs).
- The roof needs inserts for the hopper throat tabs (open question 4).

## Vault log lines (for the main chat to add to `inbox/changes.yaml`)
- 2026-11-05 20:03 PT, claim, Bricked Sorting: V14 module K (deck) built on `cad-v14-deck` to interface 4.1.
  - V13 drum reused as-is, axis front-back at x -200, tilted 6°.
  - Hopper in stud L feeds a 43° chute into the drum rear.
  - V1 (long, 2 pieces) and V2 on PETG leaf springs carry bricks to the V13-rework scanner over (330, 0).
  - Funnel exit at z 335. Electronics trays at the back access panel.
  - All zone, clash, drum-turning and door-swing checks clean. About 1.7 kg of new filament.
- 2026-11-05 20:03 PT, decision needed: drum tilt 6° instead of 8° to fit the hopper and chute under the 700 roof (README open question 1).
