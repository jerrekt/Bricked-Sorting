# V14 module F: frame and shell

Built to **v14-interface-4.1** (frozen) on branch `cad-v14-frame`.
- Script: `build_frame.py` (CadQuery 2.8, reads `../interface.json`). Helpers in `f_common.py` (copy of `cad-v14-all:cad/v14/common.py`).
- Outputs: `world/` (STEP in machine coordinates + `frame_assembly.step`), `print/` (STL laid flat), `parts.json`, `checks.json`, 5 stills.
- Coordinates are right-handed: +X is the front viewer's left, +Y front, +Z up.

## What it is (113 printed parts, all unique STLs)
| Group | Parts | What |
|---|---|---|
| 100 floor | 15 tiles (5 × 3, 208 × 173) | 4 mm skin on 4 mm underside ribs. M3 insert grid on top (40 pitch, x ±480, y ±220, skipped under the columns), plus a ring of inserts under the side walls and the column feet. 20 mm half-laps between tiles, M3 + nut. |
| 105 spine | 4 segments (233 long) | Box beam y ±66, z 8..184: 6 mm top/bottom plates and side walls, centre web, X ribs every 60. **Rail tunnels 24 × 26 (z 8..34) at x ±200 / ±300**, bridged above. Bolts down into the floor grid (counterbored from above). Tongue + socket seams. |
| 110 columns | 4 × 3 segments | 50 × 50 (x 470..520, y 210..260), 6 mm walls with a cross web. Tenon up. Inserts on the inner faces for the wall panels (side walls along Y, front/back walls along X). Foot bolts to the floor, roof bolts into the top. |
| 115 side walls | 2 × 6 (210 wide × 247/225/220 tall) | Ribbed panels: 6 skin + 14 ribs (perimeter rib 8, internal ribs 3 on a 60 grid). Row 1 carries the **beam mount**: solid rib zone y ±34, z 180..270 with two gusset ribs and the 4 inserts at (±12, 200) and (±12, 248), axis X, opening on the inner face. Row 2 has the deck ledge (356..370, inserts up) and a 20 mm rib slot at 370..390 the deck passes through. Bottom row bolts into the floor ring. Top row has roof inserts. |
| 120 front wall | 4 × 3 (235 wide × 184/165/165) | Starts at z 186 above the drawer opening (x ±470, z 8..186). Row 1 has a 12 mm lintel fill and the deck ledge. Rows above the deck have skin from 370 but ribs from 390, so the deck slides in and they bolt down into deck-edge inserts. **No screws on the outside**: all seam screws go through the perimeter ribs from inside, the columns' inserts face inward, the floor is screwed from above. |
| 125-128 back wall | 4 + 4 + 6 + 6 | Same as the front for row 1. Above the deck: two side pieces (|x| 300..470, two rows), strips below and above the opening, and the **removable access panel** x -300..300, z 420..680 in 3 × 2 pieces (200 × 130), screwed from the outside into inserts around the opening. |
| 130 deck | 15 tiles (x splits at -310/-110/90/270, y at ±85) | Skin 384..390 on ribs 370..384. M3 insert bosses on the 40 grid (x ±480, y ±200), skipping 10 mm around openings. Drop hole r 32 at (330, 0) with a rib-free ring r 50; cable slots x ±410..470, y -210..-190. Tiles extend into the wall rib zone (±514, ±254), bolt down into the ledge inserts, and carry inserts for the wall rows above. Corners notched for the columns. |
| 135 roof | 15 tiles (x splits at -380/-140/100/310, y at ±110) | Skin 714..720 on ribs 700..714. Hopper hole r 100 at (-260, 0) with a ring rib. **3 hopper inserts at r 108, 180/240/300°** (bosses in the rib zone, inserts open downward). Counterbored bolts down into the wall-top and column inserts. Insert bosses for the stud screws. |
| 140 studs | 2 × 4 quarters | OD 312, 60 tall, flange r 134..156 onto the roof. **Left: open ring** (ID 290; the deck's hopper collar sits inside). **Right: capped.** Quarters joined with M3 lugs on the inside; screwed down from above into roof inserts. |

Every seam: perimeter ribs face each other, one side has M3 inserts, the other clearance holes, on a global 100 mm grid (odd multiples of 50 mm in x, y and z), so holes line up whatever the panel split.

## Checks (`checks.json`)
- Envelope: x ±520, y ±260, z 0..780 exactly. 
- Zones: no F part is inside the D zones, the S zone, the K zone or the four rail tunnels (the corner-column keep-out is excluded from S and K as the interface allows).
- Self: no clashes between the 113 parts.
- **Drawers closed and both fully out (205)** against the `cad-v14-all` drawer world parts (130): 0 clashes.
- **Deck** against the `cad-v14-deck` world parts (54): 0 clashes. The roof ribs (700..714) clear the drum top (692.6) and the hopper arms (≤ 700).
- Every part ≤ 248³. Largest: the spine segments 245 × 132 × 176 and side-wall row 1 at 247 tall.

## Filament
**Estimated ~30 kg of red PLA** (slicer-like estimate: 4 walls solid + 15 % infill), split roughly: walls 10.1 kg, floor 3.1, deck 3.8, roof 3.7, spine 4.0, columns 3.0, studs 1.1. The 6 mm skins over ~2.5 m² of surface are most of it. See open question 1.

## Print notes
- Panels: skin on the bed, no supports (ribs are open on top).
- Floor and deck tiles, roof: skin down.
- Spine: as is (tunnel bridges are 24 mm, PLA bridges fine).
- Columns: standing.
- Studs: ring quarters on their flange; the capped quarters upside down.
- Inserts: ~900 M3. Screws: ~420 M3 × 14 (seams), ~120 M3 × 10, ~90 M3 × 12 + nut.

## Open questions
1. **Weight and print time.** 30 kg and roughly 700-900 print hours is a lot for a frame. A 3 mm skin with the same 14 mm ribs would cut it to ~17 kg; 2 mm skin + 15% infill walls ~12 kg. That needs an interface change (walls.skin), so it is a request, not done.
2. **Floor at 8 mm** carries the drawers (~10 kg) on the roller stations: the stations are on the insert grid, so the loads go into 4 mm skin + ribs. If it flexes, add a 12 mm floor (interface change) or more spine-like stiffeners under the floor.
3. The access panel in 6 pieces is clumsy. A single 600 × 260 piece does not fit the bed; 3 pieces of 200 × 260 would, if the spec's 260 height were 248 (interface change).
4. Seam screws are driven from inside: the walls assemble before the deck goes in; the deck then closes most of the lower brick. Assembly order in the integration README.

## INTERFACE REQUESTS
1. `walls.skin` 6 → 3 (ribs stay 14): halves the filament (open question 1).
2. `back_wall.removable_access_panel.z` 420..680 → 420..668 so the panel is 3 pieces, not 6 (open question 3).
3. The side-wall rib slot for the deck (z 370..390 inside the rib zone) and the deck tiles extending to ±514 / ±254: both inside F-owned space, listed so the integration knows the deck is F's size, not ±500 / ±240.

## Vault log lines (for the main chat to add to `inbox/changes.yaml`)
- 2026-11-05 21:05 PT, claim, Bricked Sorting: V14 module F (frame and shell) built on `cad-v14-frame` to interface 4.1.
  - 113 printed parts: ribbed panels (6 + 14), 4 columns, floor and deck grids, spine with rail tunnels, roof with hopper hole/inserts, two studs.
  - Clash checks against the drawer module (in and out) and the deck module: clean. Envelope exact.
  - Estimate ~30 kg red PLA; requests a 3 mm skin (would be ~17 kg).
