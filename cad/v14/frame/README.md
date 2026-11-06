# V14 module F: frame and shell

Built to **v14-interface-4.3** on branch `cad-v14-frame` (rev 2, 2026-11-05 21:35 PT; rev 1 was 4.1 with 6 mm skins, ~30 kg).

**Rev 2 changes:** 2.4 mm skins, 2.4 mm ribs 10 tall on an 80 grid (perimeter rib 8), the deck inside the walls (bolts sideways into a solid band in the walls at z 380), access panel z 420..668 in 3 pieces (200 × 248), spine as an inverted U with 2.4 plates (printed top-down, no bridges), columns with 2.4 walls, fits from the vault runbook (0.07 per side on tenons, tongues and laps; M3 insert holes 4.1), teardrop horizontal holes, every part with a flat face on the bed and no supports. Grams and hours from BJ's day profile, not solid volume.
- Script: `build_frame.py` (CadQuery 2.8, reads `../interface.json`). Helpers in `f_common.py` (copy of `cad-v14-all:cad/v14/common.py`).
- Outputs: `world/` (STEP in machine coordinates + `frame_assembly.step`), `print/` (STL laid flat), `parts.json`, `checks.json`, 5 stills.
- Coordinates are right-handed: +X is the front viewer's left, +Y front, +Z up.

## What it is (110 printed parts, all unique STLs)
| Group | Parts | What |
|---|---|---|
| 100 floor | 15 tiles (5 × 3, 208 × 173) | 4 mm skin on 4 mm underside ribs. M3 insert grid on top (40 pitch, x ±480, y ±220, skipped under the columns), plus a ring of inserts under the side walls and the column feet. 20 mm half-laps between tiles, M3 + nut. |
| 105 spine | 4 segments (233 long) | Inverted U, y ±66, z 8..184: 2.4 top plate and side walls, ribs every 80, 12 mm feet inward at the bottom with counterbored floor bolts at y ±60. **Rail tunnels 24 × 26 (z 8..34) at x ±200 / ±300**. Printed top-plate-down: nothing bridges. Tongue + socket seams at 0.07 per side, 2 × M3 + nut. |
| 110 columns | 4 × 3 segments | 50 × 50 (x 470..520, y 210..260), 2.4 walls with 8 × 8 insert strips on the two inner faces. Tenon up (0.07 fit). Inserts on the inner faces for the wall panels (side walls along Y, front/back walls along X). Foot bolts to the floor, roof bolts into the top. |
| 115 side walls | 2 × 6 (210 wide × 247/225/220 tall) | Ribbed panels: 2.4 skin + 2.4 ribs, 10 tall, on an 80 grid (perimeter rib 8). Row 1 carries the **beam mount**: solid rib zone y ±34, z 180..270 with two gusset ribs and the 4 inserts at (±12, 200) and (±12, 248), axis X, opening on the inner face. Row 2 has the deck band: solid rib zone z 368..392 with inserts facing inward at z 380 that the deck edge bolts into. Bottom row bolts into the floor ring. Top row has roof inserts. |
| 120 front wall | 4 × 3 (235 wide × 184/165/165) | Starts at z 186 above the drawer opening (x ±470, z 8..186). Row 1 has a 12 mm lintel fill and the deck ledge. Row 2 carries the deck band (inserts at z 380). **No screws on the outside**: all seam screws go through the perimeter ribs from inside, the columns' inserts face inward, the floor is screwed from above. |
| 125-128 back wall | 4 + 4 + 6 + 6 | Same as the front for row 1. Above the deck: two side pieces (|x| 300..470, two rows), strips below and above the opening, and the **removable access panel** x -300..300, z 420..668 in 3 pieces (200 × 248), screwed from the outside into inserts around the opening. |
| 130 deck | 15 tiles (x splits at -310/-110/90/270, y at ±80) | Spans x ±500, y ±240 (inside the walls). 2.4 skin at 387.6..390, ribs 10 tall; the outer perimeter rib is the full 17.6 down to 370 and bolts sideways into the wall bands. M3 insert bosses on the 40 grid (x ±480, y ±200), skipping 10 mm around openings. Drop hole r 32 at (330, 0) with a rib-free ring r 50; cable slots x ±410..470, y -210..-190. Corners notched for the columns. |
| 135 roof | 15 tiles (x splits at -380/-140/100/310, y at ±110) | 2.4 skin at 717.6..720, ribs 10 tall. Hopper hole r 100 at (-260, 0) with a ring rib. **3 hopper inserts at r 108, 180/240/300°** (bosses in the rib zone, inserts open downward). Counterbored bolts down into the wall-top and column inserts. Insert bosses for the stud screws. |
| 140 studs | 2 × 4 quarters | OD 312, 60 tall, flange r 134..156 onto the roof. **Left: open ring** (ID 290; the deck's hopper collar sits inside). **Right: capped.** Quarters joined with M3 lugs on the inside (lugs grow from the flange, no overhang); the capped quarters have a 45° brace under the flange so they print cap-down. Screwed down from above into roof inserts. |

Every seam: perimeter ribs face each other, one side has M3 inserts, the other clearance holes, on a global 100 mm grid (odd multiples of 50 mm in x, y and z), so holes line up whatever the panel split. Horizontal holes are teardrops (apex away from the bed).

## Checks (`checks.json`)
- Envelope: x ±520, y ±260, z 0..780 exactly. 
- Zones: no F part is inside the D zones, the S zone, the K zone or the four rail tunnels (the corner-column keep-out is excluded from S and K as the interface allows).
- Self: no clashes between the 110 parts.
- **Drawers closed and both fully out (205)** against the `cad-v14-all` drawer world parts (130): 0 clashes.
- **Deck** against the `cad-v14-deck` world parts (54): 0 clashes. The roof ribs (700..714) clear the drum top (692.6) and the hopper arms (≤ 700).
- Every part ≤ 248³, every part has a flat face on the bed (`bed_face` in parts.json), no supports: overhangs ≤ 45°, bridges ≤ 24 mm (spine tunnels), teardrop horizontal holes.

## Filament and time (BJ's day profile)
Model: every face gets its solid shell (4 walls = 1.68 mm per side, 5 top / 3 bottom layers), 15 % infill inside; a 2.4 mm skin therefore prints solid. Hours at 45 g/h (from the runbook's backplate timing).

**Estimate: 19.6 kg, ~440 h.** By group: walls 6.6 kg (side 3.0, front 1.7, back 1.9), roof 2.7, deck 2.8, floor 2.5, columns 2.0, spine 1.9, studs 1.0. Largest single part: a spine segment at 480 g (~11 h).

**The 9 kg target is not reachable with 2.4 mm solid skins on this body.** The skins alone are 3.4 m² (walls 1.8 + roof, deck and floor 1.6) × 2.4 mm = 8.2 L = 10.1 kg before any rib, column or stud. What it would take (each needs an interface change):
| Lever | Saves | Frame total |
|---|---|---|
| 1.7 mm skins (2 loops × 0.84, still solid) on everything | -3.0 kg | ~16.6 |
| ...plus floor and deck at 1.3 mm skins (hidden) | -1.3 | ~15.3 |
| ...plus spine 60 tall instead of 184 | -1.2 | ~14.1 |
| ...plus no roof/floor skin, open rib grids (floor on a 6 mm MDF sheet, roof a lattice under a thin vinyl/paper skin) | -3.0 | ~11 |
| ...plus 0.3 mm roof/deck/floor "skins" printed as 1 loop (cosmetic only) | | ~10 |
A fully printed 1040 × 520 × 720 closed body cannot get to 9 kg with the P2S profile; 9 kg means roughly 1 mm of average wall. Honest options: accept ~15-17 kg (lever rows 1-3), or take the floor and roof out of the printed scope (a sheet floor is the big one: 2.5 kg and also the stiffest part of the machine).

## Print notes
- Panels: skin on the bed, no supports (ribs are open on top). Horizontal holes are teardrops.
- Floor, deck and roof tiles: skin down.
- Spine: top plate down (the U opens upward on the bed); the tunnels are 24 mm bridges at the top of the print.
- Columns: standing, foot plate down, tenon up.
- Studs: open-ring quarters flange-down; capped quarters cap-down (45° brace under the flange).
- Day profile from the runbook (0.4 nozzle, 0.2 layers, 4 walls, 15 % infill, 3/5 shells). Elephant-foot compensation 0.15 is in the profile.
- Inserts: ~900 M3 (hole 4.1, verify with calipers per the runbook). Screws: ~420 M3 × 14 and M3 × 30 (seams through the 22 mm deck bands), ~120 M3 × 10, ~90 M3 × 12 + nut.

## Open questions
1. **Weight:** 19.6 kg vs the 9 kg budget; see the table above and the requests below.
2. **Floor at 8 mm** (2.4 skin + 5.6 ribs) carries ~10 kg of drawers on the roller stations; if it flexes, the sheet-floor option fixes both weight and stiffness.
3. **Bearing / rail fits** are the drawer module's; nothing in F runs a bearing.
4. Seam screws drive from inside: walls first, then the deck (it bolts sideways into the band from below the deck), then the roof. Assembly order for the integration README.

## INTERFACE REQUESTS
1. **Skin 2.4 → 1.7 mm** (2 loops) for walls, roof, deck and floor: -3.0 kg, still prints solid, no infill tuning.
2. **Floor and deck hidden surfaces at 1.3 mm** (3 loops total): -1.3 kg.
3. **Spine zone height 184 → 60**: -1.2 kg (the beam is on the side walls; the spine only stiffens the floor and carries the tunnels).
4. **Sheet floor** (6 mm MDF or plywood with the insert grid as drilled holes) instead of 15 printed tiles: -2.5 kg and stiffer. Biggest single lever; it is the one non-printed structural part.

## Vault log lines (for the main chat to add to `inbox/changes.yaml`)
- 2026-11-05 21:35 PT, claim, Bricked Sorting: V14 module F rev 2 on `cad-v14-frame` to interface 4.3 (2.4 skins/ribs, deck inside the walls bolted into wall bands, 3-piece access panel, spine inverted U, runbook fits, no supports, flat bed faces).
  - Day-profile estimate 19.6 kg / ~440 h; the 9 kg budget is not reachable with 2.4 solid skins (skins alone 10.1 kg). Requests: 1.7 mm skins, hidden floor/deck at 1.3, spine 60 tall, sheet floor; together ~11-14 kg.
  - Checks vs drawers (in/out) and deck: clean.
- 2026-11-05 21:05 PT, claim, Bricked Sorting: V14 module F (frame and shell) rev 1 built on `cad-v14-frame` to interface 4.1.
  - 113 printed parts: ribbed panels (6 + 14), 4 columns, floor and deck grids, spine with rail tunnels, roof with hopper hole/inserts, two studs.
  - Clash checks against the drawer module (in and out) and the deck module: clean. Envelope exact.
  - Estimate ~30 kg red PLA; requests a 3 mm skin (would be ~17 kg).
