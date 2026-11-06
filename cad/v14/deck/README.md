# V14 module K: deck (drum, hopper, trays, scanner, electronics), interface 5

Built 2026-11-06 00:20 PT on branch `cad-v14-deck5` to `../interface.json` **v14-interface-5**: the rev 2 deck (branch `cad-v14-deck`, interface 4.1) re-fitted into the 708 x 348 deck ply with ~296 mm of height (ply top z 312, roof underside z 612).
- Script: `build_deck.py` (CadQuery 2.8); helpers in `k_common.py` (same as the frame module's `f_common.py`). Reads `../interface.json` and the V13 STEPs in `../../reference_v13/`. Run `python3 build_deck.py`.
- Outputs: `world/` (STEP in machine coordinates + `deck_assembly.step`), `print/` (new parts laid on the bed), `parts.json` (grams, hours, bought parts, the 42 deck-ply screw positions), `checks.json`, 5 stills.

Coordinates: origin floor centre, +Y front, +Z up, +X = the front viewer's left.

## What changed from rev 2 (rev 3)
The body lost 90 mm each side and the hopper stud moved to (-180, 0), so the rev 2 layout (drum along Y under the stud) no longer closes: a 180 drum + plate + tray no longer fits in 344 mm of depth with the hopper chute behind it. Rev 3 turns the **drum along X** (axis at y 40, rear end at x -150, outlet plate face at x ~36), feeds it from the hopper through a short chute behind the rear end, runs **V1 along +Y** in front of the outlet plate and **V2 diagonally back** to the scanner at (240, 0). Heights are solved from the funnel upward (`Z_S`, `V2_B`, `V1_B`, `DRUM_REAR` at the top of the script).

| Stage | Where | z |
|---|---|---|
| Hopper 201 | one piece, r 75 rim at (-180, 0) z 658, oblique cone (far wall 46.8°) to the outlet r 30 at (-210, 40, 557); flange r 85..100 sits on the stud-ring ledge (frame 130, z 646) with 4 csk M3; sloped top ring to r 100 at z 663 catches strays | 557 → 663 |
| Chute 202 | U trough at **46.9°** into the drum's rear opening, 30 below the axis, 12 inside | 555 → 479 |
| Drum (V13, as-is) | axis along +X at y 40, rear at x -150, tilted **1°** down toward the outlet | rear axis 508.9, top 588.9; plate top 592 (roof at 612) |
| Outlet window (49b) | bottom of the plate at x ~36, 20 mm above V1's floor | 438 |
| V1 203 | along +Y at x 60 (38..82), y 5..145, **4.5°**, low catch lip under the window | 420.6 → 409.6 |
| V2 204 | (75, 148) → (172, 8), 170 long, **4.5°**, notched where V1 drops in | 401.6 → 388.2 |
| Landing ramp 211 | V13 ramp over x 155..204 | 382 → 374 |
| Scanner floor | over (240, 0) | **374.2** |
| Drop funnel 220 | mouth r 50 at 330, **55° cone** to r 25.5 at 313, tube OD 27.5 through the r 28 deck hole, step to OD 25 at z 300, exit | **270** |

Height budget: drum top 589 / plate top 592 under the 612 roof (20 mm spare; K zone 608). Levers if more is needed: the funnel cone (55° now), tilt 0°, or shorter trays.

## Parts
- **Drum, reused as-is:** 47b barrel, 49b static plate, 48 rear guard, 4 x 50 rollers, 54 core, 55 TPU tire, 56 NEMA17 bracket (plus the V13 door links, slider and horn arm for the scanner, and the V7 vibration saddles 62/63).
- **205 cradles A (y+) / B (y-):** two 4 mm fork plates per roller (M5 axle), a cheek for the 49b ear (2 x M3), a 3 mm base with 4 #6 wood screws, a 25 mm web along the base. Print base-down, no supports.
- **206 motor wall:** separate part now (it was merged into cradle B); bracket 56 bolts to it with 4 x M5; foot with 4 #6.
- **201 hopper, 202 chute, 203/204 trays (PETG), 207 leaf springs (PETG, 2 per tray, foot with 2 #6), 210-218 scanner (V13 rework; plate 220 x 180 x 3 with a notch under V2's saddle; standoffs on the ply at x 150/180/330, y +-80), 220 funnel (flange with 4 #6), 225 electronics trays (2.4 mm, legs with #6, M3 insert pads).** Electronics sit at y -170..-62 behind the access panel (x -200..200, z 330..560); the PSU is the big one at x -290..-125.
- Estimated new PLA/PETG: **~1.37 kg, ~23 h** (day profile, see the frame README for the model). Biggest: hopper 200 g, scanner plate 150 g, cradles 2 x 120 g, electronics tray 1 ~115 g.

## Checks (`checks.json`), all clean
- Every part inside the K zone (x +-354, y +-172, z 312..608), the funnel inside r 27.5 below the deck, the hopper inside the r 90 roof hole with >= 1 mm and inside the stud ring above.
- No clashes between parts (by-design contacts: springs/saddles on their trays, core/tire, V1 in V2's notch, 49b ears on the cheeks, rollers in the forks, bracket on the motor wall).
- Drum turned in 30° steps: 0 clashes at all 12 (the chute tip clears the flight).
- Scanner doors at 0/30/60/90°: 0 clashes; the funnel mouth is 1 mm below the open door tips.
- **Against the frame module** (`cad-v14-frame5` world STEPs: posts, top rails, roof tiles, stud ring, C3 roof clips): 0 clashes.
- All 26 new parts fit 248; electronics tray 1 goes on the bed diagonally.

## Print notes
- Hopper: flange (rim) down, outlet up, cone walls >= 45°. Chute: on a side wall. Trays and springs: PETG, trays walls-up, springs on their side. Cradles and motor wall: base down. Scanner plate, trapdoors, funnel: upside down. Drum: as the V13 note (49b first, then 47b, axis vertical).
- Test order: 49b + one cradle (check the ear/cheek and the roller forks), V1 with one spring and the saddle, then the hopper.
- Deck ply screws: 42 x #6 x 3/4 in, positions in `parts.json: deck_ply_screws` (drill 2.5 mm pilots in the ply before it goes on the cleats).

## Open questions
1. Drum feed: 1° tilt + the helical flight. If pieces are slow, raise the rpm or go to 2° (costs 3 mm of height; there is 20 spare).
2. Electronics board sizes are placeholders (`EL` in the script); measure the real boards.
3. Hopper load: the stud ring carries the hopper on the 2 mm roof (frame README request 3). Keep the hopper under ~1 kg of bricks until a cross rail is in.

## INTERFACE REQUESTS
None. Built to interface 5; the hopper flange matches the ledge in frame part 130 (my own frame module).

## Vault log lines (for the main chat, `inbox/changes.yaml`)
- 2026-11-06 00:20 PT, claim, Bricked Sorting: V14 module K (deck) rev 3 on `cad-v14-deck5` to interface 5.
  - Drum turned along X (axis y 40, rear x -150, tilt 1°), hopper r 75 in the left stud on the stud-ring ledge, 47° chute, V1 along +Y, V2 diagonal to the scanner at (240, 0), scanner floor 374, funnel exit 270, electronics behind the panel.
  - ~1.37 kg / ~23 h new parts; all zone, clash, drum-rotation, door-swing, bed and frame cross-checks clean.
  - Frame + deck together: ~5.7 kg / ~82 h (budget was ~5.5 kg).
