# Handoff: top attachment ("Bricked tool") on the sorter's studs

For a new chat. Attach `jerrekt/Bricked-Sorting` (push) and `jerrekt/mnemosyne` (read is fine). Read `runbooks/3d-printing.md` in the vault first (print profile, fits, grams), then this file. Interface: `cad/v14/INTERFACE.md` + `interface.json` **v14-interface-5.1** on `cad-v14`. Frame (studs, roof) is on `cad-v14-frame5` (`cad/v14/frame/`, script `build_frame.py`, function `stud_parts()`); hopper on `cad-v14-deck5`.

## The job
Design a printed accessory that mounts on top of the sorter like a LEGO part stacking on a 2x1 brick: it grips the two studs. BJ decides what the "tool" is (holder, tray, sign, brick-separator-shaped caddy...); this handoff fixes the mounting geometry. Build it on a new branch `cad-v14-top` in `cad/v14/top/` with the same deliverables as every module: `build_top.py` (CadQuery), `world/` STEP in machine coordinates, `print/` STL on the bed, `parts.json` (day-profile grams/hours), `checks.json`, `README.md` with open questions and vault log lines, stills, a zip for BJ.

## Stud measurements (interface 5.1, as built on `cad-v14-frame5`)
Machine coordinates: origin at the floor centre, +X = the front viewer's **left**, +Y front, +Z up.
| Item | Value |
|---|---|
| Stud centres | (-180, 0) left/hopper, (+180, 0) right; 360 apart, 144 mm gap between the two rims |
| Stud OD | 216 (r 108), both |
| Stud height | 50: foot on the roof skin at **z 614**, top at **z 664** |
| Roof skin | 2 mm red PLA, z 612..614, 720 x 360 (x +-360, y +-180); the studs are screwed to it from below (4 M3 each at r 102-104); the roof sits on 2x2 top rails round the edge and two flat 1x2 cross rails under the left stud at x -292 and -68 |
| Left stud (130) | open ring, wall 8 (ID 200), internal ledge ID 170 at z 640..646 that carries the hopper collar (4 M3 inserts at r 92.5, 45/135/225/315 deg). The hopper mouth is inside: **the opening must stay clear** (r 100 at the top) unless the attachment *is* a feed aid. The roof has an r 90 hole under it |
| Right stud (131) | capped: 2.4 wall, 2 mm flat top at z 664, hollow (ID 211.2) down to the 8 mm foot ring (r 96..108). Nothing to screw into from above |
| Edges | 0.6 mm 45 deg chamfer on the outer rim: bottom edge of the ring stud, top edge of the capped stud |
| Scale | the body is a 2x1 brick at **45:1** (LEGO 8 mm unit = 360); LEGO stud OD 4.8 -> 216 exact, LEGO stud height 1.8 -> 81, built at 50 |

## Mounting rules
- Grip the stud **OD** with a socket (ring or C-shape): ID = 216 + 2 x 0.07 = **216.14** for a sliding fit per the runbook (dovetails/slides 0.065-0.07 per side); -0.02 per side only for a true press, and then print a short coupon ring first. Socket wall >= 2.4, depth 20-40 so it registers square; a 216 socket plus walls (~222) still fits the 248 bed, but the second socket does not: **one socket per printed part**, bridged by a separate bar with keyed joints (0.07 fit) or screws + M3 inserts (4.1 hole, 5.7 deep).
- Load path into the stud walls, not the 2 mm roof: nothing may rest on the roof skin between the studs except through a foot over a top rail (edge 2x2 at x +-360 / y +-180, or the cross rails at x -292 / -68, y +-155) and even then keep it light (< 1 kg total on the roof).
- Keep the left stud open from above (hopper feed) and don't block the right stud's cap unless BJ says so. Envelope above the machine is free, but keep the overall height sane (the machine is 664 tall).
- Inserts per `inventory/parts-owned.md` (M3 generic 4.0-4.2). No supports, a flat bed face per part, parts <= 248, day-profile grams (every face solid 1.68 mm, 15 % infill), red PLA unless it should look like a LEGO accessory in another colour (AMS colours on hand: SME green, SME blue, white, red, black).

## Checks to run
Socket fit on the stud STEPs (`cad-v14-frame5:cad/v14/frame/world/130_stud_ring_left_hopper.step`, `131_stud_cap_right.step`): 0.07 gap, no overlap with the roof tiles (`114_roof_tile_*`) or the hopper (`cad-v14-deck5:cad/v14/deck/world/201_hopper.step`). Envelope: x +-360, y +-192 unless it deliberately overhangs. Bed fit. Weight on the roof.

## Vault
Push nothing to the vault; list log lines in the README for the main chat. Claim line for the vault when you start: "2026-11-07, claim, Bricked Sorting: top attachment (`cad-v14-top`) — <what it is>, mounts on the 216 studs with a 0.07 sliding socket".
