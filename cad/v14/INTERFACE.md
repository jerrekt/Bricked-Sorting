# Bricked Sorting V14: shared interface for the parallel CAD chats

Four chats build four modules at the same time. They only fit together if everyone uses the same numbers, so the numbers live in `interface.json` (read it in your script; do not retype them). If a number does not work for your module, keep building to it and write the change you want under **INTERFACE REQUESTS** in your module README. The integration step decides.

**Interface 4 (2026-11-05 18:55):** (1) drawer rails move UNDER the drawers and run back through tunnels in the center spine (front rails at x ±300 reach y -60, back rails at x ±200 reach y +60), rollers fixed to the floor, travel 205: a single-stage drawer can't extend past its own depth unless its rails reach back beyond it. (2) Drop funnel exit lowered to z 335; the scoop keeps out of r 40 around (330, 0) above z 330. (3) Scoop starting geometry: shallow two-ended cup above a pivot at z ~268, lip 114 out / 25 up, dump at 40° (lip y 103, z 214); the opposite end rises to ~360, so taper the ends; TPU pad against bounce. (4) Beam in 5 segments of ~200 with 60-80 mm sleeves. (5) Carriage cable in a drag chain on the beam's back face. interface.json has the numbers.

**Interface 3 (2026-11-05 18:35):** beam is a ~65 x 40 PLA box in 4-5 keyed segments (mounts moved to z 200/248), belt near the beam's mid-height, scoop lip must reach |y| >= 100, drawers ride on 625ZZ rollers, two drawer switches only, drawers keyed.

**Interface 2 (2026-11-05 18:20):** after a design review with ChatGPT, the single 490 mm drawer became **two opposing 8-bin drawers** (front row out the front, back row out the back, ~220 mm single-stage printed runners), and the drum stays the V13 160 x 180. Everything below reflects that.

Decided by BJ on 2026-11-05: max height 30 in (a couple of inches over is OK), same 1040 x 520 footprint, one bin tier with 16 bins (two rows of 8), scoop rides a rail between the rows and tilts to either row (no Z lift, no yaw), drum raised on the deck with a small hopper, **fully printed frame** (no 2020 extrusion). The scoop slide may use a GT2 belt. Layout sketch: `../v14_layout_sketch.png` (sketch, not CAD).

## The machine in one paragraph
Bricks go into a small hopper in the left roof stud, fall into the rear of the V13 drum (static outlet plate, helical flight), come out the drum's front end onto V1 and V2 vibration trays that run sideways (+X) to the scanner at the right. The scanner (V13 design: landing ramp, trapdoors, XIAO S3 Sense camera, APDS-9960, LED bar) drops each brick through a hole in the deck at **(330, 0)** into the scoop. The scoop carriage runs on a printed beam that spans the lower brick at y = 0, moves to one of 8 x positions and tilts toward the back row or the front row, dropping the brick into one of 16 open bins; the front row is one drawer pulled out the front, the back row another pulled out the back. Body 1040 x 520 x 720 plus two 60 mm roof studs = 780 (30.7 in).

## Coordinates
mm. Origin at the floor center. +X right when you face the drawer, +Y toward the front (the drawer pulls out +Y), +Z up.

| | |
|---|---|
| Envelope | X -520..520, Y -260..260, Z 0..780 |
| Lower brick / deck brick / studs | z 0..390 / 390..720 / 720..780 |
| Wall zone | 20 thick inward from every outer face (6 skin + 14 ribs). Interior clear X ±500, Y ±240 |
| Corner columns (frame) | keep-out at all four inside corners: \|x\| 470..500, \|y\| 210..240, z 8..700 |
| Floor | z 0..8, top has M3 insert holes on a 40 grid: x = -480..480, y = -220..220 (frame skips holes under the columns) |
| Deck panel | z 370..390 (skin 384..390, ribs 370..384). Top has M3 inserts on a 40 grid: x = -480..480, y = -200..200, skipping holes within 10 of an opening |
| Deck openings | drop hole r 32 at (330, 0), no ribs within r 50 of it; cable slots x -470..-410 and 410..470, y -210..-190 |
| Front and back walls | drawer opening x -470..470, z 8..186 in each |
| Center spine | y -66..66, z 8..184 under the beam, between the drawers: frame may put a spine here; drawer runners may bolt to its sides |
| Service clearance | 300 mm behind the machine for the back drawer |
| Side walls | beam mount: four M3 inserts on each inner face (x = ±500, axis along X) at (y, z) = (±12, 200) and (±12, 248) |
| Roof | z 700..720 (skin 714..720, ribs 700..714). Hopper opening r 100 at (-260, 0). Left stud: open ring OD 312 / ID 290 (hopper inside). Right stud: closed cap |
| Back wall | removable access panel x -300..300, z 420..680 |
| Print bed | every printed part ≤ 248 x 248 x 248 |
| Fasteners | M3 heat-set inserts (4.0 hole, 5.7 deep), M3 screws (3.4 clearance), M5 where a load needs it |

## Zones (who owns what space)
| Module | Space it may fill |
|---|---|
| **F frame** | the wall zones, floor, deck panel, roof, studs, corner columns, bracing. Bracing stays out of the D, S and K zones |
| **D drawers** | front: x ±466, y 70..260; back: x ±466, y -260..-70; z 8..184 (drawers, faces, runners, bins, switches) |
| **S scoop** | x ±500, y ±240, z 186..366, minus the corner columns. Nothing in S may go below z 186 at any pose |
| **K deck** | x ±500, y ±240, z 390..700, plus the hopper inside the left stud (to z 780, through the roof opening) and the drop funnel (cylinder r 30 at (330, 0), z 366..390, through the deck hole) |

Bins: 16, footprint 108 x 150, open top, top at z ≤ 176. Centers x = -406 + 116 i (i = 0..7), rows at y = -150 and +150.
Drawers: two, 8 bins each, travel 220 each. Runners: printed PETG rail with 625ZZ bearings as rollers (about 3 per side: two carry the load, one captures against lift), hard end stops, closed detent. The two drawers are keyed so neither fits the other side, and a retaining bar holds all 8 bins, so a seated drawer means all its bins are present. Switches: one KW11-3Z drawer-closed switch per side, no per-bin switches.
Bin IDs: **F1..F8** front row and **B1..B8** back row, each numbered left to right for the person standing at that drawer (so B1 is behind F8). Marking: the two drawer faces print in different filament colors, with F or B and 1-8 embossed over each bin, and every bin has a slide-in label card slot for its category.
Drum: keep the V13 drum as-is (47b 160 x 180 barrel with the helical flight, 49b static plate).
Scoop poses: **receive** = carriage at x 330, level, catching a brick that falls from the funnel exit at (330, 0, 366), r 25. **Dump** = carriage at a bin x, tilted toward -Y or +Y; the brick leaves the lip at |y| ≥ 95, z ≥ 186, and lands inside the bin opening. **Park** = receive pose; the drawer may open only when parked.

Part numbers: F 100-149, D 150-179, S 180-199, K 200-249.
Bought parts allowed: electronics, motors, servos, switches, LEDs, 625ZZ bearings, GT2 6 mm belt + 20T pulleys + idler (scoop slide only), M3/M5 screws and nuts, M3 heat-set inserts, TPU or PTFE film. Everything else printed.

## Modules

### F: frame and shell (`cad/v14/frame/`)
Ribbed panels that are the structure: floor, four walls per brick, deck panel, roof, two studs, corner columns. Joints bolted with M3 inserts (tongue + 2 bolts per 100 mm of seam is a fair start). Add hidden bracing so a drawer pulled out 220 with 5 kg in it does not rack the frame. Front and back walls each have a drawer opening; the area above (z 186..390) carries the deck. A center spine under the beam (y ±66) is the natural place to stiffen the floor and to carry the inner runners. Side walls carry the beam mount inserts. Back wall also has the removable access panel in the deck brick. Studs like V13's 78/79 quarter rings (reference in `../reference_v13/frame_v13/`). Look: LEGO red brick, studs on top; no visible screws on the front if you can avoid it.

### D: drawers, bins and runners (`cad/v14/drawer/`)
Two 8-bin drawers, the same except for their keying (front pulls +Y, back pulls -Y), faces and handles, runners made of a printed PETG rail with 625ZZ bearings as rollers and hard end stops, bolted to the floor grid and/or the center spine, a closed detent, a drawer-closed switch mount (KW11-3Z) per side, a retaining bar over the bins, and keying so the front drawer cannot go in the back and vice versa. No per-bin switches. Bins: open top, 108 x 150 footprint, easy to lift out one-handed and to pour from, each with a label card slot on the face toward its drawer front. Faces carry the F/B and 1-8 marks (see Bin IDs). V10 bins and the V12 drawer latch are in `../reference_v13/bins_v10/` and `frame_v13/`.

### S: scoop slide (`cad/v14/scoop/`)
The printed beam (closed box ~65 tall x 40 deep in PLA, 4-5 keyed segments with internal splices, joints staggered and none at midspan; target < 2 mm sag at center) that bolts to the side-wall inserts, a carriage on 625ZZ bearings, a NEMA17 (BJ's salvaged 48 mm, 5 mm shaft; no lead-screw motor) + GT2 belt drive with a printed idler and tensioner, a homing endstop (KW11-3Z) at -X, the scoop and its tilt servo (MG996R or a smaller servo if it fits; say which), and a cable path from the carriage to a deck cable slot. Must hit all 17 poses (receive + 8 x 2 dumps). At each dump the brick leaves the lip at |y| >= 100 and z >= 190 on a surface tilted at least 40 deg, and nothing dips below z 186. Pivot the scoop on its own shaft or bushings, not on the servo horn. Run the belt near the beam's mid-height. The V3 carriage, hub and open scoop are in `../reference_v13/carriage_v3/` for reference.

### K: deck (`cad/v14/deck/`)
Everything on the deck: the V13 drum (reuse `47b` and `49b` as-is from `../reference_v13/drum_v13/`, plus rollers 50, drive core 54, TPU tire 55, motor bracket 56 from `drum_v7/`), new low cradles that bolt to the deck grid, a small hopper inside the left stud with a chute into the drum's rear end, V1 and V2 vibration trays running +X from the drum outlet to the scanner, the scanner (rework of V13's 57-62, 73, 74 in `deck_v13/`) with its trapdoors over (330, 0) and a funnel through the deck hole, and the electronics tray (PSU 60 x 165, XIAO ESP32-S3 Sense, XIAO ESP32-C3, MCP23017, 3x TMC2209, DRV8833, buck) toward the back where the access panel can reach it. Drum axis runs front-back with the outlet toward +Y unless you have a better reason.

## What every module chat delivers
In `cad/v14/<module>/`:
- `build_<module>.py` (CadQuery 2.8), reading `../interface.json`.
- `world/`: each part as STEP in machine coordinates (so integration can drop them in as-is), plus `<module>_assembly.step`.
- `print/`: each part as STL laid flat for printing, named `NNN_name_PRINT_qty.stl`.
- `parts.json`: label, part number, qty, bed extent, est. grams, print hours if you have them, and bought parts with qty.
- `checks.json`: every part inside its zone at every pose, no self-clashes, every part fits 248³, and module-specific checks (S: all 17 poses; D: both drawers closed and fully open; K: drum turning 12 angles).
- `README.md`: what you built, print notes, open questions, and **INTERFACE REQUESTS**.
- Three or four PNG stills.
Commit only your folder, on your own branch `cad-v14-<module>` made from `cad-v14`. Do not touch `web/`, do not open a PR, do not merge. The repo is public: no addresses, passwords or tokens.

## Integration (after all four are done)
One chat pulls the four branches, assembles, checks the envelope, pairwise clashes, the scoop at all 17 poses against the drawer and frame, each drawer at 220 with the scoop parked, the drum turning, bed fit, total filament, then renders the stills and the one-brick animation, updates the buy list (remove 2020 extrusion, T-nuts, metal slides and the NEMA17 lead-screw motor; add belt and pulleys. The two salvaged NEMA17s drive the drum and the slide) and the task board on a PR.
