# Bricked Sorting V14: shared interface, version 5

**Interface 5.1 (2026-11-06 19:35):** the frame chat found the drawer body (x ±314) wider than the skin opening (±300). Fixed: bins 70 wide at **76 pitch** (centers -266 + 76 i), drawer body **x ±306**, skin opening **x ±310, z 12..136**, and drawer faces **overlay** the opening like cabinet drawers (x ±330, 10 mm proud of the skin, so the envelope is y ±192). Roof: the 2 mm roof must not carry the hopper alone; two 1x2 cross rails at x -180 ±112 if they clear the drum (top 589), otherwise a 4 mm ribbed roof ring under the stud.

**Read `interface.json` for every number; this page explains them.** Version 5 (2026-11-05 23:10) replaces versions 1-4.3 (kept in `INTERFACE_v4_superseded.md` / `interface_v4_superseded.json` for history). Why: the fully printed 1040 x 520 machine came out at ~25 kg and ~550 print hours. BJ chose to **resize the body, build the structure from wood (simple straight cuts) and keep a thin red PLA skin** for the LEGO look. Bins were ~2 L each for a 1 L box; now ~0.58 L.

## The machine
Body **720 x 360 x 614 + 50 mm studs = 664 mm (26.1 in)**, a 2x1 LEGO brick. Same path as before: small hopper in the left roof stud -> V13 drum (static outlet plate, helical flight) -> V1 -> V2 vibration trays -> V13-style scanner -> drops through the deck at **(240, 0)** into the scoop -> the scoop slides on a belt-driven beam to one of 8 x positions and tilts to the front or back row -> 16 bins in **two opposing drawers** (F1-F8 front, B1-B8 back).

## Coordinates
mm, right-handed, origin at the floor center, +Y to the front, +Z up, so **+X is the front viewer's left**. Bin numbers follow the real viewer.

## Wood structure (straight crosscuts only; the store cuts the plywood)
| Piece | Qty | Cut | Where |
|---|---|---|---|
| 2x2 corner post | 4 | 600 | \|x\| 316..354, \|y\| 136..174, z 12..612 |
| 1x2 top rail, long / short | 2 / 2 | 632 / 272 | under the roof at z 574..612 |
| 1x2 deck cleat, long / short | 2 / 2 | 632 / 272 | z 262..300, the deck plywood sits on them |
| 1x2 bottom rail, short walls | 2 | 272 | z 12..50 |
| 1x2 beam post (vertical) | 2 | 212 | x ±(335..354), y ±19, z 50..262; the scoop beam screws in |
| 1/2 in plywood floor | 1 | 720 x 360 | z 0..12 |
| 1/2 in plywood deck | 1 | 708 x 348, 38 x 38 notch at each corner | z 300..312 |
Printed parts screw to wood with #6 wood screws (3.6 mm clearance). Printed-to-printed joints use M3 inserts.

## Skin and studs
2.0 mm red PLA, printed solid, 4 mm off the wood on printed clips. Outer faces at x ±360, y ±180; roof skin z 612..614 on the top rails. Tiles ≤ 248, seams on the brick's natural lines. Drawer openings in the front and back walls: x -300..300, z 12..134. Removable back access panel x -200..200, z 330..560 for the electronics. Studs at x ±180: OD 216, 50 tall; the left one is an open ring (ID 200) holding the hopper over a roof opening r 90; the right one is capped.

## Zones
| Module | Space |
|---|---|
| **F** frame + skin | the wood, skin, clips, roof, studs, corner caps |
| **D** drawers | front x ±314, y 52..180; back x ±314, y -180..-52; z 12..132. Front rails x ±200 run back on the floor to y -40, back rails x ±120 to y +40, rail zone z 12..38 |
| **S** scoop slide | x ±354, y ±150, z 134..296, minus posts and beam posts; nothing below z 134 at any pose |
| **K** deck | x ±354, y ±172, z 312..608 (clear of top rails and post corners), plus the hopper in the left stud and the drop funnel r 25 at (240, 0), z 270..312 through a deck hole r 28 |

## Bins and drawers
16 open bins, 70 x 95 footprint, 85 tall (z 41..126), 0.57 L. Centers x = -266 + 76 i, rows at y ±102.5 (front 55..150, back -150..-55). Two drawers, travel 150 (inner edge ends 25 past the skin), PETG rails on the drawer underside riding 625ZZ floor stations screwed into the plywood, hard stops, closed detent, keyed by rail spacing (front ±200, back ±120), retaining bar, one KW11-3Z closed switch per side. Faces in two colors with F/B and 1-8, label card slot per bin.

## Scoop slide
PLA box beam ~50 x 30 spanning x ±335 at y ±15, z 138..188, 3-4 keyed segments, end plates screwed to the beam posts. Salvaged NEMA17 + GT2 belt near the beam mid-height, printed idler/tensioner, endstop. Scoop: shallow two-ended cup above a pivot at z ~200 (lip ~85 out, ~20 up), dump at 40°: the brick leaves at |y| ≥ 75, z ≥ 136, off a surface ≥ 40°; taper the ends (opposite end rises to ~270); TPU pad. Receive and park at carriage x 240 under the funnel exit (240, 0, 270); nothing from S inside r 32 of (240, 0) above z 265.

## Deck
V13 drum as-is (47b, 49b, rollers, drive), new cradles screwed to the deck plywood. Hopper ~150 across in the left stud. Trays at ~4.5°. Scanner over (240, 0) with the funnel through the deck. Electronics at the back behind the access panel.

## Printing
Follow Mnemosyne `runbooks/3d-printing.md` (BJ's P2S day profile and measured fits): grams estimated with the day profile, dovetails 0.065-0.07 per side, press pockets -0.02, 625 pocket coupon first. No supports, a flat face on the bed, parts ≤ 248. **Budget: ≤ ~9.5 kg and ≤ ~200 h printed in total** (skin ~4.6, studs ~0.5, mechanisms ~3.5, bins ~1).

## Deliverables per module (unchanged)
`build_<module>.py` reading `interface.json`; `world/` STEPs in machine coordinates; `print/` STLs laid flat; `parts.json` with grams and print hours (day profile) and bought parts; `checks.json`; README with INTERFACE REQUESTS and vault lines; 3-4 stills. Frame module also delivers the **wood cut list** and a drilling map for the screw positions.
