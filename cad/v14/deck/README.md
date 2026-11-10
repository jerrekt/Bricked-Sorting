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
- **Against the frame module** (`cad-v14-frame5` world STEPs: posts, top rails, the two flat roof cross rails at x -292 / -68 (z 593..612, interface 5.1), roof tiles, stud ring, C3 roof clips): 0 clashes; the drum top passes 5 mm under the x -68 cross rail.
- All 26 new parts fit 248; electronics tray 1 goes on the bed diagonally.

## Print notes
- Hopper: flange (rim) down, outlet up, cone walls >= 45°. Chute: on a side wall. Trays and springs: PETG, trays walls-up, springs on their side. Cradles and motor wall: base down. Scanner plate, trapdoors, funnel: upside down. Drum: as the V13 note (49b first, then 47b, axis vertical).
- Test order: 49b + one cradle (check the ear/cheek and the roller forks), V1 with one spring and the saddle, then the hopper.
- Deck ply screws: 42 x #6 x 3/4 in, positions in `parts.json: deck_ply_screws` (drill 2.5 mm pilots in the ply before it goes on the cleats).

## Open questions
1. Drum feed: 1° tilt + the helical flight. If pieces are slow, raise the rpm or go to 2° (costs 3 mm of height; there is 20 spare).
2. Electronics board sizes are placeholders (`EL` in the script); measure the real boards.
3. ~~Hopper load~~: interface 5.1 put two flat 1x2 cross rails under the stud (frame README).

## INTERFACE REQUESTS
None. Built to interface 5 (re-checked clean against 5.1 on 2026-11-06 19:55 PT; nothing in K changed); the hopper flange matches the ledge in frame part 130 (my own frame module).

## Vault log lines (for the main chat, `inbox/changes.yaml`)
- 2026-11-06 00:20 PT, claim, Bricked Sorting: V14 module K (deck) rev 3 on `cad-v14-deck5` to interface 5.
  - Drum turned along X (axis y 40, rear x -150, tilt 1°), hopper r 75 in the left stud on the stud-ring ledge, 47° chute, V1 along +Y, V2 diagonal to the scanner at (240, 0), scanner floor 374, funnel exit 270, electronics behind the panel.
  - ~1.37 kg / ~23 h new parts; all zone, clash, drum-rotation, door-swing, bed and frame cross-checks clean.
  - Frame + deck together: ~5.7 kg / ~82 h (budget was ~5.5 kg).

## Nov 8 electrical update (rev 3.1, 2026-11-08 16:40 PT)
From the electrical chat: Pi 4B brain, USB webcam instead of the XIAO S3 Sense, 12 V 10 A PSU (~199 x 98 x 42), IEC C14 fused + switched inlet, two bucks (>= 5 A servos/vibration, >= 3 A Pi/logic), XT30 + fuse on the 12 V side, deck MCP23017 dropped.
| Part | What | Where |
|---|---|---|
| 225 tray 1a | PSU in a 6 mm fence, 2 strap slots (hook-and-loop or zip ties until its holes are measured), 2 M3 inserts for the cover | x -316..-86, y -172..-60; PSU x -290..-91, AC end at x -290 |
| 227 PSU terminal cover | wraps the terminal end, AC slot on top (lead up to the inlet), DC slot on +y, 2 tabs with M3 | x -308..-280 |
| IEC inlet (frame) | fixed back tile B c1 r3, centre x -268, z 445 (frame README) | 50 mm above the cover |
| 225 tray 1b | 5 A buck, XT30 + fuse, 3 A buck, DRV8833, XIAO C3 (M3 insert pads) | x -82..12 |
| 225 tray 2 | Pi 4B (M2 x 16 + nut traps, 58 x 49 holes) with its USB/Ethernet end facing the camera (+x, 70 mm free for plugs), 2-slot TMC2209 carrier | L-shape x 16..180, clears the scanner standoff |
| 217 webcam mount | generic: 34 mm lens window over the bridge hole, 2 zip-tie slot pairs to strap the webcam face-down; lens stays 128 mm above the trapdoor (`CAM`) | replaces the XIAO mount |
| Cable route | 215 post zip-tie slots (2 pairs) → over the plate corner (x 338, y -92) → clip 226-1 (332, -112) → spool 228 at (255, -133) for ~1 m of slack → clip 226-2 (198, -140) → Pi USB | |
Power the Pi through its GPIO 5 V pins from the 3 A buck; a USB-C plug on the Pi's -y side has only ~20 mm to the back wall.
Checks: 0 clashes (parts, drum at 12 angles, doors, frame incl. the inlet and back tiles), all in K, all fit 248. New parts ~1.51 kg / ~25 h for the deck now.
Placeholders to measure: PSU holes, both bucks, XT30/fuse holder, XIAO carrier, TMC carrier, webcam, IEC module.

## 625 pocket result (2026-11-09 19:20 PT)
BJ's PETG coupon (plate P1, row A): **dot 3 = 16.1 mm seats with a light push.** The scoop and drawer pockets are already drawn at 16.1. The reused V7 drum roller 50 had 16.2 pockets (would slip), so it is redrawn as **`50b_drum_625_roller`** (same OD 32 x 14, 10 through, 5.2-deep pockets at **16.1**), printed in **PETG**, qty 4: `print/50b_drum_625_roller_PETG_pocket16.1_PRINT_4.stl` (~7 g each). Checks still clean (parts, drum at 12 angles, frame).
Vault line: `2026-11-09 7:12pm PT, claim, 3D printing: PETG 625ZZ pocket (5.2 deep) = 16.1 mm (coupon P1 row A dot 3, seats with a light push); drum rollers redrawn to 16.1 in PETG on cad-v14-deck5.`
