# V14 accessory V: vacuum canister (parts 250-266)

Built on `cad-v14-vac` (from `cad-v14-all`), 2026-11-18. Script `build_vac.py` reads `../interface.json` and writes
`world/` (STEP, docked on the left stud, gate closed), `collect/` (STEP of the wand elbows on the mouth, same frame),
`print/` (STL on the bed), `parts.json`, `checks.json` and 5 stills. `build_preview.py` -> `how_it_works.gif` (9 frames,
cut in half: collect, dock, half turn, drop). Plates: `make_plates.sh` -> `../plates/P24_*`.
Nothing on the machine changes.

**Status: P24 v6, all parts printed (2026-11-25). Dock is a little tight to twist: sand the skirt and wax. Dyson adapter waits on the Adapter Base STEP from BJ.**
Print files are in the `vac` folder of the print pack (BJ 2026-11-18), not `1_now`.

The print pack on the `prints` branch (2026-11-18) was built from this branch. Until `cad-v14-vac` is merged into
`cad-v14-all`, rebuild the pack from here, or P24 drops out of it.

## What it is
A yellow canister, 224 across and 283 tall, with two black eyes and a black mouth at the front, a black handle at the
back and a round hose port on top. BJ's brief (2026-11-18): carried while vacuuming, 2.5 in shop-vac hose, rigid wand down to the floor
from the mouth, an original look (not a copy of the LEGO minifigure head), keep the stud on top, needed for the
December demo. The eyes are the important part. Yellow parts in PLA, and the vac's own wands fit a cuff, so no wand tubes are printed.

- **Collect.** The vac hose pushes into the top port (256). Three printed elbows (258) push onto the mouthpiece (257)
  and turn the mouth 105 deg (3 x 35, a 7 shape, BJ 2026-11-24); the vac's own wands push onto the second elbow. Pieces come in through the
  mouth, glance off the tilted screen (254, 25 deg, slots running down the slope) and drop into the funnel. Air goes
  up through the screen to the port. When the vac stops, anything held on the screen falls off.
- **Feed.** Pull the hose and wand off, carry it by the handle (260), set it on the left stud and turn it until the 4
  pins drop into the hopper's screw bores. Then turn the body half a turn clockwise (seen from above): the gate disc
  (252) stays put on the pins, and the body's drop hole comes round over the disc's hole. Turn back to close.
- **Gate lock.** Body hole and disc hole are 180 deg apart, each 60 across. Nothing opens until the body has turned
  87 deg relative to the disc, and a spring detent holds each end position. The stop is an M3 x 12 through the collar
  whose tip rides in a recess on the disc rim.

## Parts
| No. | Part | Load | Bed face | g | h |
|---|---|---|---|---|---|
| 250 | lower shell: socket collar, funnel stop, mouth pad, screen ledge, tilted top edge | PLA yellow | collar down | 551 | 12.2 |
| 251 | funnel insert, 34.5 deg far wall, 60 mm drop hole 42 off the axis | PETG black | foot down | 388 | 8.6 |
| 252 | gate disc with 4 pins, rim recess and 2 detents | PETG black | top face down, pins up | 143 | 3.2 |
| 253 | pivot cap (hidden) | PLA, on the port plate | flange down | 2 | 0.1 |
| 254 | screen, 199 slots 2.4 x 26, ribs on the clean side | PETG black | flat, ribs up | 128 | 2.8 |
| 255 | lid with spigot, 5 wall ribs and 8 roof ribs | PLA yellow | roof down | 386 | 8.6 |
| 256 | hose port (the stud on top), tapered socket | PLA yellow | base down | 86 | 1.9 |
| 257 | mouthpiece: flange + a copy of the hose cuff | PETG black | flange down | 51 | 1.1 |
| 258 | wand elbow 42 deg, x2 | PETG black | socket down | 88 each | 2.0 each |
| 260 | handle | PETG black | on its side | 73 | 1.6 |
| 261 | eye, x2: capsule 15.8 x 33.8 x 2.2, glued into a pocket above the mouth, 0.8 proud | PETG black | flat | 1 each | 0.1 |
| 265 | coupon: stepped socket ring for the stud (0.15 / 0.10) | PLA any | chamfered end down | 39 | 0.9 |
| 266 | coupon: hose socket | PLA any | small end down | 20 | 0.5 |

Part 259 (wand tube 240) stays in the script but is not printed (`PRINT_WAND_TUBES = False`).

Day-profile estimate: canister **1.81 kg, about 40 h**; elbows 0.18 kg, 4 h; coupons 59 g. By material: yellow PLA
**1.02 kg**, black PETG 0.96 kg. About $22 of filament with tax.

Bought: none except the yellow PLA. From the kit: 21 M3 heat-set inserts, 15 M3 x 8 and 6 M3 x 12 socket screws.

## Numbers that matter
- **Dock:** socket 216.3 on the 216 stud: 0.15 per side, PLA on PLA. That is the runbook's "loose" PLA value, picked
  because the body has to turn on the stud; the coupon ring also carries 0.10. 20 deep, collar wall 7.8. Skirt bottom
  at z 644, 30 above the roof tiles. The disc sits on the stud rim; the pins are 5.6 in the 6.4 bores, 8 in, 4 above
  the screw heads.
- **Inserts:** 4.3 holes in the PLA parts (shell, lid, port), 4.4 in the PETG funnel.
- **Lid joint:** PLA spigot in the PLA shell, 0.15 per side.
- **Drop:** everything falls inside r 73.6; the hopper mouth is r 75. The gate hole is 60, the same as the hopper outlet.
- **Height:** machine + canister = **927 mm** (canister top 263 above the stud).
- **Load:** funnel 1.25 L, 1.48 L up to the mouth lip. The hopper holds 0.93 L, so a full load backs up in the
  canister and feeds down as the hopper drains. Empty it before closing the gate, or a piece can get pinched.
- **Screen:** slots 2.4 (limit 2.5), 12,170 mm2 open, 5.7 times the hose bore.
- **Hose (not measured):** drawn for a cuff 57.0 at the tip and 58.5 at the base. Socket 58.7 at the entry, 56.85 at
  36 deep. The mouthpiece and elbow ends copy the cuff, which is why the vac's own wands go straight on.

## Checks (`checks.json`, `../integration/checks.json`)
- Docked, gate closed: **0 clashes** with the frame (studs, roof tiles, clips) and the deck (hopper). Run by
  `integration/build_integration.py` (key `V_vac_docked`); the other machine checks are unchanged and still 0.
- **The deck's `201_hopper.step` is not a valid solid** (`isValid()` is False): OCC cut / intersect on it return garbage
  without an error, so any boolean clash result against the hopper, from any module, proves nothing. The canister was
  re-checked on the meshes instead (`checks.json` -> `dock.mesh_check`): pins 0.40 from the bore walls (drawn 0.40),
  disc underside 1.00 above the hopper ring and resting on the stud rim, shell 0.14 from the stud (drawn 0.15) and
  8.1 from the hopper.
- 0 clashes between canister parts, closed and open. Stop screw: free from 0 to 180 deg, bumps at 6 and 174, hard
  stops beyond.
- `plates/check_bodies.py`: all 13 print STLs are one solid. `plates/support_check.py`: 0 mm2 needing support; the only
  steep area is 25 mm2 at the tops of the two eye pockets (a 1.4 mm ledge).
- Every part fits 248 x 248 x 248 with a flat bed face. Tallest: lower shell 236.

## Print order
1. **P24 file 1: both coupons, in PLA** (1.4 h, 59 g, any colour).
   - Ring: chamfered end first onto the left stud. It should go all the way down by hand and turn freely. If it stops
     after 6 mm, the 0.10 end is too tight and 0.15 stays. Flip it to feel 0.10 on its own. Report which end turns
     freely without rattling.
   - Hose cuff into the small socket, pushed in by hand. Report how deep it goes (mm from the socket's top edge), or
     caliper the cuff at the tip and 40 mm back. Depth 33 = the drawn size; 20 = cuff tip 57.7; 10 = 58.2; goes right
     through = 56.85 or smaller. 19.5 mm of depth is 1 mm of diameter.
2. Files 3, 5, 6, 7 do not depend on the coupons: lid, funnel, gate disc + eyes, screen. File 2 (lower shell) waits for the
   ring result.
3. Files 4 and 8 (hose port, mouthpiece + handle + elbows) after the hose number is in.

Supports off. PLA files on the PLA profile, PETG files on the runbook PETG profile (fan max 40 %).

## Assembly
Inserts first. 4.3 holes: 4 in the mouth pad, 1 in the collar (stop) and 2 in the collar flat at the back, 4 in the
lid spigot and 2 in the lid flat at the back, 4 under the hose port. 4.4 holes: 3 round the funnel insert and 1 under
its centre.
1. Port onto the lid roof from inside: 4 x M3 x 8.
2. Funnel insert up into the lower shell until it stops, drop hole at the back: 3 x M3 x 8 through the shell.
3. Gate disc under it, its hole at the front; pivot cap and M3 x 12 into the centre.
4. Stop screw M3 x 12 into the collar insert (on the left when you face the mouth), into the disc's rim recess.
5. Screen on its ledge, ribs up. Lid on: 4 x M3 x 8 through the seam.
6. Mouthpiece: 4 x M3 x 8. Handle: 4 x M3 x 12 through the access bores from the grip side.
7. Eyes: a drop of super glue in each pocket, tops leaning toward the middle. Left and right are the same piece
   turned over. The 0.10 gap is drawn for glue, not a press fit.

## Open questions for BJ
1. **Hose cuff size** and the vac model (coupon 266 or calipers). Until then the hose parts are a guess.
2. **Yellow PLA spool.** Yellow is not on file. The estimate is 1.02 kg of yellow, so one 1 kg spool is borderline:
   slice files 2-4 in Bambu before buying. Recent jobs ran 25-35 % under the CAD estimate, so one spool may do.
3. **PLA shell.** PLA is stiffer than PETG but cracks more easily if the canister is dropped. The parts that take the
   hits (screen, funnel, gate) are still PETG.
4. **Weight and time.** 1.8 kg empty and about 44 h with the elbows is a lot for the demo. A shorter funnel at
   30 deg would save roughly 100 g and 13 mm of height (rough estimate). Most of the weight is the size.
5. **Gate lock** is a detent plus the 87 deg dead band, not a positive lock. Good enough, or should the stud release
   a latch?
6. **Face.** The eyes are an original design (two capsules leaning in), not the LEGO minifigure face. A different
   expression is two numbers in the script (`EYE_TILT`, `EYE_H`); BJ's own artwork can replace the outline.
7. **Bulk volume of one 10696 set** in a measuring jug, against the 1.25 L funnel.
8. **Funnel slope** is 34.5 deg on printed layer steps: flat plates may sit on it until the body is twisted or
   tapped. Steeper costs height (45 deg adds about 37 mm).
9. **Seam leak.** The lid spigot has a 0.15 gap over 12 mm. If the 2x4 lift test is weak, a turn of tape on the
   spigot fixes it.
10. Parking on the right stud works, but the canister sits 9 mm high on its pins there.

## INTERFACE REQUESTS
None. It uses the stud OD, the stud rim and the hopper's 4 open screw bores as printed.

Note for the deck chat (K): re-export `201_hopper.step` as a valid solid so the integration clash check can see it.

## Vault log lines (for the main chat; nothing was pushed to Mnemosyne)
- 2026-11-18, claim, Bricked Sorting: vacuum canister accessory V drafted on `cad-v14-vac` (`cad/v14/vac/`, parts
  250-266, plate P24 v2, 8 files): yellow canister 224 x 283 that docks on the left stud; half-turn gate disc held by
  4 pins in the hopper screw bores; tilted 2.4 mm slot screen; hose port on top; 2 elbows on the mouth for the vac's
  own wands; 2 glued-in black eyes. Docked check 0 clashes; machine + canister 927 mm.
- 2026-11-18, decision, BJ: canister is carried while vacuuming, 2.5 in shop-vac hose, rigid wand, original look with
  the stud kept on top, wanted for the December demo. Print files go in their own `vac` folder of the print pack. Yellow parts in PLA. The vac's own wands
  fit a cuff, so no wand tubes are printed.
- 2026-11-18, open, 3d-printing runbook: PLA large round fit drawn 0.15 per side for the 216 stud socket and the lid
  joint; coupon 265 tests 0.15 and 0.10, file the result under PLA fits. Hose cuff not measured (drawn 57.0 tip /
  58.5 base); file the coupon 266 result. Yellow PLA is not on file.
- 2026-11-18, finding: `cad-v14-deck5` `201_hopper.step` is not a valid solid, so the integration's boolean clash
  checks against the hopper are blind; the canister was verified on meshes instead. Deck chat should re-export it.
- 2026-11-18, estimate: canister 1.81 kg / ~40 h plus elbows 0.18 kg / 4 h, day profile; yellow PLA 1.02 kg, black
  PETG 0.96 kg; 21 M3 inserts, 15 M3 x 8, 6 M3 x 12 from the kit.
