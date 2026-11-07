# V14 module S: scoop slide (interface 5.1)

Built on `cad-v14-all`, 2026-11-06 20:30 PT. Script `build_scoop.py` (reads `../interface.json` and the drawer `world/` for the bin check). Outputs: `world/` STEP (fixed parts + moving parts at receive) + `scoop_assembly.step`, `print/` STL laid flat, `parts.json` (day-profile grams/hours, bought parts), `checks.json` (17 poses), 4 stills.

## What it is
- **Beam (180):** closed PLA box 30 × 50 at y ±15, z 138..188, x ±335, 3 segments (joints at x ±112) with 20 mm plugs at 0.07 fit and 2 × M3 through the sides. End plates 6 thick screw into the 1x2 beam posts' inner faces with 3 × #6 each. Internal diaphragms every 60.
- **Carriage (181, PETG):** 2 top rollers on the beam top (y ±8) and 4 side rollers (vertical axles) on both faces, 625ZZ, 0.05 gaps; PTFE anti-lift hooks under the beam's bottom edges at z 136 (nothing below 134). Top plate at z 205..208 carries the pivot towers (|x| 46..54, 625 pockets at z 222). Belt clamp arm on +y, endstop flag on −x.
- **Drive:** salvaged NEMA17 above a plate at the −x end (x −354..−308, y 15..68, z 172..176, saddle over the beam top with 2 × M3), shaft down to a 20T pulley; GT2 6 mm belt in a horizontal loop at z 160..166 on the +y side (runs at y 40 / 52.7); idler wheel on two 625ZZ in a slider (185/186/187) in a channel at x 301..334 with an M3 tension screw; KW11-3Z endstop (188) on the beam top at x −326..−312, −y side. Home at carriage x −240.
- **Scoop cup (182):** 80 wide, flat floor ±65 at z 227 with lip ramps to y ±88 / +12, walls 14 → 4 tapered, 2 mm, keel, 5 mm stub axles into the tower bearings. TPU pad (183) on the floor. **Dump 40°:** lip at |y| 75.1, z 179.6 off a 40° floor (lip ramp 12° at dump); opposite end rises to 292.8 (zone 296).
- **Tilt drive:** MG996R on a separate bracket (190) **outside the cup's sweep** at y −117..−93 (the cup sweeps |y| ≤ 88 down to z 180), shaft along x; parallel 4-bar: 28 mm horn and a 28 mm crank on the cup's −x wall, 105 mm pushrod (189), arms pointing up at rest, 1:1 motion.
- **Receive:** carriage x 240, cup floor 43 mm under the funnel exit (270), cup top 241 < 265 keep-out; catch area 80 × 130 for the r 22 funnel.
- Servo lead as a 400 mm rolling loop on the −y face (fixed clip at x 0, z 140..167).

## Checks (`checks.json`, 17 poses: receive, home, 8 front dumps, 8 back dumps)
- 0 clashes against the beam, posts, motor, idler, endstop, belt, and the closed drawers' bins/faces/trays; 0 self clashes (cup vs carriage/bracket/servo at every tilt).
- All poses inside the S zone; min z 136.0 at every pose; max z 292.8.
- Funnel keep-out at receive: 0.
- Brick landing (slide from the cup centre, μ 0.3 / 0.45): lands at |y| 120 / 110, inside the bin row (55..150, bin opening 56..147) with 26 mm of drop from the lip to the bin top. μ 0 lands at 146 (edge); real bricks on TPU are ≥ 0.3.
- Every part ≤ 248, flat bed face, no supports except possibly the carriage's belt-clamp arm (tree, build plate only).

## Filament (day profile): **0.62 kg, ~14 h**
Beam 0.39 (3 × 118-140 g), carriage 0.10, bracket 0.03, cup 0.05 + TPU pad 0.02, drive bits 0.03.

## Open questions
1. **625 pocket size** (coupon 16.0/16.1/16.2) sets the tower pockets and the idler bore; drawn at 16.1 / 16.1.
2. The belt runs 25 mm off the beam face (motor body must clear the posts): the clamp arm is a 10 mm cantilever; fine at this speed.
3. Beam sag: 670 span, 30 × 50 × 2.4 PLA box carries ~0.4 kg of carriage + cup + servo at midspan: estimated < 1 mm. If it bounces, add a 1x2 wood stiffener under it (zone allows z 134..138 is only 4 mm: no) → or thicken the walls to 3.2 (+0.1 kg).
4. The pushrod linkage adds two M3 pins; servo horn is the stock 25T arm cut to 28 mm radius.

## INTERFACE REQUESTS
None. Note for K: the funnel's r 25 tube ends at z 270 directly over the cup (floor 227, walls to 241); for F: the lead clip at (0, −19..−25, 140).

## Vault log lines
- 2026-11-06 20:30 PT, claim, Bricked Sorting: module S built to 5.1 on `cad-v14-all`: 30 × 50 box beam in 3 keyed segments on the 1x2 beam posts, 6-roller carriage (nothing below z 136), belt drive with the NEMA17 at the −x end, 80 × 176 cup pivoting at z 222 with a 40° dump (lip |y| 75 / z 180), MG996R outboard at y −105 through a 4-bar pushrod. 17 poses clash-free vs the drawers; 0.62 kg / 14 h.
