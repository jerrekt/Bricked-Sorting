# V14 module F: frame and shell

Built to **v14-interface-4.3** on branch `cad-v14-frame`. Rev 3, 2026-11-05 22:20 PT (rev 1: 4.1 with 6 mm skins, ~30 kg; rev 2: 2.4 skins, 19.6 kg).

**Rev 3 (BJ, 21:58): levers 1-3 + open-grid floor.** 1.7 mm outer skins (walls, roof), 1.3 mm hidden deck face, 60 mm spine, floor as an open 2.4 × 8 rib grid on the 40 insert grid with solid 8 mm pads under the roller stations, the closed-switch mounts and the columns. Perimeter ribs 6.4, columns 1.7 walls. These are deviations from interface 4.3 (walls.skin 2.4, spine zone 184) that BJ approved.

**Rev 2 changes:** 2.4 mm skins, 2.4 mm ribs 10 tall on an 80 grid (perimeter rib 8), the deck inside the walls (bolts sideways into a solid band in the walls at z 380), access panel z 420..668 in 3 pieces (200 × 248), spine as an inverted U with 2.4 plates (printed top-down, no bridges), columns with 2.4 walls, fits from the vault runbook (0.07 per side on tenons, tongues and laps; M3 insert holes 4.1), teardrop horizontal holes, every part with a flat face on the bed and no supports. Grams and hours from BJ's day profile, not solid volume.
- Script: `build_frame.py` (CadQuery 2.8, reads `../interface.json`). Helpers in `f_common.py` (copy of `cad-v14-all:cad/v14/common.py`).
- Outputs: `world/` (STEP in machine coordinates + `frame_assembly.step`), `print/` (STL laid flat), `parts.json`, `checks.json`, 5 stills.
- Coordinates are right-handed: +X is the front viewer's left, +Y front, +Z up.

## What it is (110 printed parts, all unique STLs)
| Group | Parts | What |
|---|---|---|
| 100 floor | 15 tiles (5 × 3, 208 × 173) | Open grid: 2.4 × 8 ribs on every line of the 40 insert grid, 9 mm bosses with M3 inserts at every grid point (x ±480, y ±220, skipped under the columns), solid 8 mm pads where things stand (roller stations at x ±200/±300, switch mounts at ±400, columns), ring of inserts under the side walls. 6 mm perimeter rib with half-laps (0.07 fit), M3 + nut. |
| 105 spine | 4 segments (233 long) | Inverted U, y ±66, z 8..68 (60 tall): 2.4 top plate and side walls, ribs every 80, 12 mm feet inward at the bottom with counterbored floor bolts at y ±60. **Rail tunnels 24 × 26 (z 8..34) at x ±200 / ±300**. Printed top-plate-down: nothing bridges. Tongue + socket seams at 0.07 per side, 2 × M3 + nut. |
| 110 columns | 4 × 3 segments | 50 × 50 (x 470..520, y 210..260), 1.7 walls with 8 × 8 insert strips on the two inner faces. Tenon up (0.07 fit). Inserts on the inner faces for the wall panels (side walls along Y, front/back walls along X). Foot bolts to the floor, roof bolts into the top. |
| 115 side walls | 2 × 6 (210 wide × 247/225/220 tall) | Ribbed panels: 1.7 skin + 2.4 ribs, 10 tall, on an 80 grid (perimeter rib 6.4). Row 1 carries the **beam mount**: solid rib zone y ±34, z 180..270 with two gusset ribs and the 4 inserts at (±12, 200) and (±12, 248), axis X, opening on the inner face. Row 2 has the deck band: solid rib zone z 368..392 with inserts facing inward at z 380 that the deck edge bolts into. Bottom row bolts into the floor ring. Top row has roof inserts. |
| 120 front wall | 4 × 3 (235 wide × 184/165/165) | Starts at z 186 above the drawer opening (x ±470, z 8..186). Row 1 has a 12 mm lintel fill and the deck ledge. Row 2 carries the deck band (inserts at z 380). **No screws on the outside**: all seam screws go through the perimeter ribs from inside, the columns' inserts face inward, the floor is screwed from above. |
| 125-128 back wall | 4 + 4 + 6 + 6 | Same as the front for row 1. Above the deck: two side pieces (|x| 300..470, two rows), strips below and above the opening, and the **removable access panel** x -300..300, z 420..668 in 3 pieces (200 × 248), screwed from the outside into inserts around the opening. |
| 130 deck | 15 tiles (x splits at -310/-110/90/270, y at ±80) | Spans x ±500, y ±240 (inside the walls). 1.3 skin at 388.7..390 (hidden face), ribs 10 tall; the outer edges carry a 6 mm rib the full 18.7 down to 370 that bolts sideways into the wall bands. M3 insert bosses on the 40 grid (x ±480, y ±200), skipping 10 mm around openings. Drop hole r 32 at (330, 0) with a rib-free ring r 50; cable slots x ±410..470, y -210..-190. Corners notched for the columns. |
| 135 roof | 15 tiles (x splits at -380/-140/100/310, y at ±110) | 1.7 skin at 718.3..720, ribs 10 tall. Hopper hole r 100 at (-260, 0) with a ring rib. **3 hopper inserts at r 108, 180/240/300°** (bosses in the rib zone, inserts open downward). Counterbored bolts down into the wall-top and column inserts. Insert bosses for the stud screws. |
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
Model: every face gets its solid shell (4 walls = 1.68 mm per side, 5 top / 3 bottom layers), 15 % infill inside, so 1.3-2.4 mm skins print solid. Hours at 45 g/h with the 0.4 nozzle; a 0.6 nozzle on the panels and spine (groups 105-135) taken as 1.6× faster.

**Rev 3: 15.1 kg of red PLA (~$190 at $12.5/kg). 335 h with the 0.4 nozzle; 245 h with a 0.6 nozzle on the panels and spine** (the floor grid, columns and studs stay at 0.4). Per group: side walls 2.7, front 1.4, back 1.7 (incl. access panel 0.6), roof 2.2, deck 2.0, floor grid 1.6, columns 1.6, spine 0.9, studs 1.0. Per part in `parts.json` (`est_grams`, `est_hours_0.4`, `est_hours_0.6_on_panels`).

Why not 12-13: the perimeter ribs. 75 tiles and panels each carry a 6.4 × 10 rib around their edge for the seam screws; that is ~2.4 kg on its own. Fewer, larger tiles are not possible on the 248 bed. The only way under ~13 kg from here is a lighter roof/deck (open grids like the floor, a 1.3 mm deck skin is already in) or 1.3 mm outer skins, which start to show the ribs through.

## Print notes
- Panels: skin on the bed, no supports (ribs are open on top). Horizontal holes are teardrops.
- Floor grid: flat (any face). Deck and roof tiles: skin down.
- Spine: top plate down (the U opens upward on the bed); the tunnels are 24 mm bridges at the top of the print.
- Columns: standing, foot plate down, tenon up.
- Studs: open-ring quarters flange-down; capped quarters cap-down (45° brace under the flange).
- Day profile from the runbook (0.4 nozzle, 0.2 layers, 4 walls, 15 % infill, 3/5 shells). Elephant-foot compensation 0.15 is in the profile.
- Inserts: ~900 M3 (hole 4.1, verify with calipers per the runbook). Screws: ~420 M3 × 14 and M3 × 30 (seams through the 22 mm deck bands), ~120 M3 × 10, ~90 M3 × 12 + nut.

## Open questions
1. 15.1 kg vs the 12-13 kg expected: the perimeter ribs (see above). Say if the roof should become an open grid under a thin cosmetic skin (-1 kg).
2. Floor grid stiffness: 8 mm ribs on a 40 grid with pads under every load; the spine (60 tall) and the walls' bottom ribs tie it. If it flexes under the drawers, go 10 mm ribs (+0.3 kg).
3. Seam screws drive from inside: walls first, then the deck (bolts sideways into the bands from below), then the roof.

## INTERFACE REQUESTS
Approved deviations to record in the interface: walls.skin 1.7 (outer), deck face 1.3, spine zone z 8..68, floor as an open grid with pads, access panel 420..668.

## Vault log lines (for the main chat to add to `inbox/changes.yaml`)
- 2026-11-05 22:20 PT, decision, Bricked Sorting: frame rev 3 on `cad-v14-frame`: levers 1-3 (1.7 outer skins, 1.3 deck face, 60 mm spine) + open-grid printed floor with pads (BJ's pick over MDF). Day-profile estimate 15.1 kg / 335 h at 0.4, 245 h with a 0.6 nozzle on panels and spine. Checks vs drawers and deck clean. Remaining weight is the 75 perimeter ribs (~2.4 kg).
- 2026-11-05 21:35 PT, claim, Bricked Sorting: V14 module F rev 2 on `cad-v14-frame` to interface 4.3 (2.4 skins/ribs, deck inside the walls bolted into wall bands, 3-piece access panel, spine inverted U, runbook fits, no supports, flat bed faces).
  - Day-profile estimate 19.6 kg / ~440 h; the 9 kg budget is not reachable with 2.4 solid skins (skins alone 10.1 kg). Requests: 1.7 mm skins, hidden floor/deck at 1.3, spine 60 tall, sheet floor; together ~11-14 kg.
  - Checks vs drawers (in/out) and deck: clean.
- 2026-11-05 21:05 PT, claim, Bricked Sorting: V14 module F (frame and shell) rev 1 built on `cad-v14-frame` to interface 4.1.
  - 113 printed parts: ribbed panels (6 + 14), 4 columns, floor and deck grids, spine with rail tunnels, roof with hopper hole/inserts, two studs.
  - Clash checks against the drawer module (in and out) and the deck module: clean. Envelope exact.
  - Estimate ~30 kg red PLA; requests a 3 mm skin (would be ~17 kg).
