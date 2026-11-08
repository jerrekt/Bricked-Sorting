# V14 module F: frame + skin (interface 5)

Built 2026-11-05 23:50 PT on branch `cad-v14-frame5`; updated 2026-11-06 19:50 PT to `../interface.json` **v14-interface-5.1** (720 x 360 x 614 body + 50 studs, wood structure, 2 mm red PLA skin; drawer openings x +-310, z 12..136; two 1x2 roof cross rails under the hopper stud).
- Script: `build_frame.py` (CadQuery 2.8, shapely, matplotlib) with helpers in `f_common.py`. Run `python3 build_frame.py`.
- Outputs: `world/` (STEP, machine coordinates, plus `frame_assembly.step`), `print/` (STLs laid on the bed, `_PRINT_<qty>`), `parts.json`, `checks.json`, `cut_list.md`, `drilling_map.md/.json/.png`, 4 stills.

Coordinates: origin floor centre, +Y front, +Z up, +X = the front viewer's left.

## What's in it
| Group | Parts | Grams (day profile) |
|---|---|---|
| Wood (100-109) | 4 posts 2x2 x 600, 2+2 top rails, 2+2 deck cleats, 2 bottom rails, 2 beam posts (1x2), **2 roof cross rails 1x2 x 310 laid flat at x -292 / -68 (z 593..612)**, floor ply 720 x 360, deck ply 708 x 348 notched + 56 mm funnel hole | bought, see `cut_list.md` |
| Skin walls (110-113) | 36 tiles, 2.0 mm face + 1.6 x 2.8 ribs on the back. Front/back columns at x 0, +-180 (front) / 0, +-200 (back, so the panel edges are seams), rows z 212 / 412. Sides: columns at y 0, rows 212 / 412. Drawer openings x +-310, z 12..136 in both walls (drawer faces overlay them) | 2470 |
| Access panel (115) | two halves x -200..0 / 0..200, z 330..560, 8 countersunk M3 into keeper bars | 236 |
| Keeper bars (116/117) | 8 bars screwed to the deck cleat / top rail, M3 inserts behind the panel's top and bottom edges | 40 |
| Roof (114) | 8 tiles 180 x 180 at z 612..614 on the top rails and the two cross rails (locator ribs hug the cross rails' sides, no ribs over them), hole r 90 at (-180, 0), csk M3 from below into the studs | 606 |
| Studs (130/131) | left: open ring OD 216 / ID 200 with an internal ledge ID 170 at z 640..646 (4 M3 inserts) for the hopper collar; right: capped. Both have inserts in the foot; screwed from below through the roof | 456 |
| Corner caps (135) | 12 L sections 24 x 24 x 200, ribs over the posts | 300 |
| Clips (120-123) | 128 C1 + 6 C2 screwed channel clips, 24 C3 roof clips, 90 loose H bridge clips | 198 |
| **Total printed** | 46 tiles + 22 other parts + 248 clips | **~4.31 kg, ~59 h** |

Grams use the vault runbook day profile (4 walls = 1.68 mm solid per face, 1.0 top / 0.6 bottom skins, 15 % sparse); every tile prints solid (2 mm < 2 skins). Hours: 49 g/h for chunky parts (BJ's 120 g in 2 h 26 min) and 75 g/h for solid sheets; the sheet rate is my estimate, slice one tile to calibrate.

## How the skin holds on (no visible screws)
- Every tile: face down on the bed, ribs up. Border ribs follow the outline; an extra rib sits on every wood line the tile crosses (deck cleat z 281, top rail z 593, side bottom rails z 31). Ribs end 1.2 mm short of the wood.
- **C1** clip (slot 1.74 = rib + 2 x 0.07, runbook sliding fit) screwed to the post / cleat / rail with one #6 x 3/4, grips a rib. **C2** = two-rib slot (3.34) for the side-wall seam over the beam posts. **H** = same slot, no screw: joins the two border ribs of neighbouring tiles where there is no wood (seams at x 0 / +-180, z 212 / 412, roof seams). **C3** screws to the inner face of a top rail and takes the rib hanging from a roof tile.
- Assembly: screw all clips and keeper bars to the wood (positions in `drilling_map.md`, 166 screws); lay each wall's tiles face-down and press H clips over the seams (positions in `parts.json: h_clip_positions`); press the wall panel onto the C clips; roof: H-clip the 8 tiles, screw both studs on from below, then drop it onto the rails (ribs into the C3 slots); corner caps press onto their own C1 clips last.
- Fit: C/H slots use 0.07 per side (sliding), untested on ribs: **print one C1 and one H clip plus a 40 mm strip of tile edge first** and file the result in the runbook. Lead-in chamfers 0.6 on every slot. Tile faces have no chamfer (BJ's elephant-foot compensation is in the profile); the studs and clips have 0.6 bed chamfers.

## Checks (`checks.json`)
- All 68 printed parts + clips fit 248 (largest: panel halves 200 x 230, stud 216).
- Everything inside the 720 x 360 x 664 envelope; no clashes between any F parts (wood, tiles, clips, bars, studs, caps); the wood pieces don't overlap each other.
- Openings: both drawer openings clear, the panel region holds only the two panel halves, roof hole r 90 clear.
- Zones: nothing from F inside the K, S or D zones except the 24 C3 roof clips, 5 mm proud of the top rails' inner faces at z 578..612 (K's own note already says stay clear of the rails). The cross rails sit at z 593..612, above the K zone (608) and 4 mm above the deck's drum top (589; deck README).

## Print notes
- Red PLA, day profile. Tiles face down (smooth outer face), ribs up; roof tiles top-face down; studs: ring foot down (ledge has a 45 deg underside), cap top down; corner caps standing on end with a brim; clips base down, 20-30 per plate.
- Print order: one C1 + H clip + a tile-edge coupon (fit), then a side tile and its clips on a scrap of 2x2, then the rest.
- Keeper bars lie on their countersunk face. M3 inserts: 8 roof/stud feet, 4 stud ledge, 8 keeper bars.

## Deck-module hand-offs built into F
- Left stud ledge: ID 170, top z 646, 4 M3 inserts at r 92.5 at 45/135/225/315 deg from (-180, 0). The hopper collar (K) sits on it.
- Roof hole r 90 at (-180, 0); roof underside z 612; stud screw heads flush on the roof underside at r 104 / 102.
- Deck ply has the 56 mm funnel hole at (240, 0). Deck parts screw into the ply with #6 wood screws (K README lists them).

## Roof support under the hopper (interface 5.1)
Two 1x2 cross rails, **laid flat** (38 wide, 19 tall, z 593..612) at x -292 and -68, y -155..155 between the long top rails, toe-screwed from the top before the roof goes on. Flat because upright (38 tall, bottom 574) would cut 15 mm into the drum (top 589 at the rear, 587.5 under the x -68 rail); flat leaves 4-5.5 mm. The stud foot (x -288..-72) bears over both rails through the 2 mm roof. Two C3 clips moved 36 mm to clear the rail ends. The 4 mm ribbed roof ring is not needed.

## INTERFACE REQUESTS
1. ~~D zone vs skin opening~~ resolved by 5.1 (opening +-310, body +-306, overlay faces).
2. **Floor ply edge:** the ply is 720 x 360 = the skin outer face, so its edge shows for z 0..12 under the tiles (the tiles stand on the ply's top edge). Fine as a plinth (paint it red) or cut the ply 716 x 356 and let the skin run to z 0; I built it to the interface.
3. ~~Roof stiffness under the hopper~~ resolved by 5.1 (cross rails above).
4. Wood: 1x2 "38 tall" means the 38 mm face is vertical for rails and cleats (the 19 mm face toward the wall). The clips assume 6 mm wood-to-skin; measure the actual lumber (often 1.5 x 1.5 in / 0.75 x 1.5 in) before cutting.

## Vault log lines (for the main chat, `inbox/changes.yaml`)
- 2026-11-05 23:50 PT, claim, Bricked Sorting: V14 module F (frame + skin) built on `cad-v14-frame5` to interface 5.
  - Wood cut list (4 x 2x2 posts, 8 x 1x2 rails/cleats/beam posts, 2 ply sheets) and a drilling map with 166 #6 clip pilots.
  - 46 x 2 mm red PLA tiles on printed channel clips (C1/C2/H/C3, 0.07 sliding fit), 2-part access panel on keeper bars, 8 roof tiles, two 216 studs (left ring with hopper ledge), 12 corner caps.
  - ~4.33 kg / ~59 h printed; all clash, zone, bed and opening checks clean. Print one clip + tile-edge coupon before the tiles.
- 2026-11-05 23:50 PT, question, Bricked Sorting: D zone (x +-314) overlaps the skin's +-300 opening by 14 mm each side; and whether a 1x2 cross rail under the hopper stud is wanted. (Answered by interface 5.1.)
- 2026-11-06 19:50 PT, claim, Bricked Sorting: module F updated to interface 5.1: openings x +-310 z 12..136; two 1x2 roof cross rails laid flat at x -292 / -68 (z 593..612, 4-5.5 mm over the drum) carry the hopper stud; ~4.31 kg; checks clean.

## Drawer check (re-run 2026-11-08 12:45 PT: drawers `cad-v14-all` @86274c8 vs frame `b4965a3` + deck `ce96b78`)
`check_drawers.py` -> `check_drawers_5.1.json`. **All clean:** 0 clashes with the frame (closed), 0 with the deck, 0 with any frame part at 50 / 100 / 150 mm of travel for both drawers. Bodies x +-306, z 23..131.5 inside the +-310 / 12..136 openings; overlay faces x +-330, z 8..140, back plane at |y| 180 on the skin (their 174 bbox is the lip inside the opening).
Correction: the 2026-11-06 run reported the faces 6 mm too deep. That was a frame bug, not a drawer one: the 5.1 rebuild read the skin plane from `envelope.y` (+-192 after 5.1), so the front/back skin had moved out 12 mm. Fixed in b4965a3 (skin back at +-180). No drawer change was needed.
