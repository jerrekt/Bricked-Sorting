# V14 module D: drawers, bins and runners (interface 5.1)

Built on `cad-v14-all`, 2026-11-06 19:45 PT. Script `build_drawer.py` (reads `../interface.json`; runner geometry in `runner.py`; test kit `build_runner_test.py` → `runner_test/`). Outputs: `world/` STEP (both drawers closed) + `drawer_assembly.step`, `print/` STL laid flat, `parts.json` (day-profile grams and hours, bought parts), `checks.json`, 4 stills.

## What it is
- **Two keyed drawers**, front rails at x ±200, back at ±120; the back drawer is the front one turned 180°.
- **Runners (160/161 rail, 162 station, 164 guide):** PETG rail 16 × 24.5 on the drawer underside (z 12.5..37), 220 long, tail at y -40. One 3-roller 625ZZ station per rail screwed to the plywood (#6): anti-lift roller at y 124 (slotted, M3 jack preload), load pair at 148 / 171. Travel 150, hard stop = closed slot end, detent bump 0.4. Guide block (two vertical 625ZZ) on the +X rail only. 56 mm engaged at full pull.
- **Tray (166):** 2.4 plate on the rail tops (z 37..39.4) with 6 mm ribs under it between the rails, 4 tiles split in bin gaps (x -152 / 0 / 152), 10 mm half-laps with M3 + nut. Bin shims to z 41, 4 mm locators in the 6.6 gaps, rear wall, front stops, retaining-bar posts, closed-switch tab.
- **Face (167 F / 168 B):** overlay x ±330, z 8..140, 2 mm skin with 6 mm ribs inside the opening, 3 pieces (splits ±95), grip slot in the middle piece, red PLA (BJ 2026-11-09), F/B + 1-8 as a 0.6 inlay (`_ink` on the AMS, black). A tongue under the tray front edge; bolts into the rail front inserts.
- **Bins (169, ×16):** 69.4 × 92 + 2.4 label holder in a 70 × 95 cell (0.6 drop-in), 85 tall (z 41..126), 0.84 walls, 1.2 floor, rim, finger slot, 46 × 24 label card slot. ~39 g each.
- **Retaining bar (170):** 4 pieces in post seats over the inner rims (y 55..60, z 126.3..130.3).
- **Closed switch (171):** KW11-3Z on the floor at x -250 (back +250), #6 screw, tab under the tray. Stays as the interlock (scoop doesn't move while a drawer is out).
- **Bin switches (2026-11-08, V14 plan in `docs/electrical/README.md`):** a 2 x 14 mm glass reed (N/O) lies in a groove in the tray plate top under every bin (glass z 38..40, 1 mm under the bin floor), at bin-local x +25 so it clears the rails (front +-200, back +-120) on every bin with one bin design. 2 mm boss under the plate, 1.5 lead slots, 2.5 wire holes at both ends; leads go down and along the underside. Each bin has a 6 x 2 magnet pressed into a floor boss (pocket 5.96 from the bottom, open on the bed face) over the reed's +y end (a disc over the middle can sit in the field null). Seated = closed = LOW (C to GND, NO to the MCP pin, pull-up on).
- **MCP23017 (1 per drawer):** module (assumed 40 x 25, no headers, wires soldered) slides into two hooks under tray tile 2 at x -75..-35, y 117..143 (pcb z 25..26.6, end stop at +x). 4 wires (3V3, GND, SDA, SCL) to the deck with a service loop for the 150 travel. Addresses 0x20 front / 0x21 back (0x22 for the deck one).
- **Reed coupon (172):** a 44 x 60 tray piece + a bin-floor square with the magnet boss. Print and test before the trays: reed must close with the floor square sitting on the pads and open when it is lifted ~10 mm.

## Checks (`checks.json`)
- No clashes: both closed, either open, both open. Zones: all in D (rails in the allowed strip, faces in the face zone). Bin top 126.0 (limit 126). Open bins rear edge at y 205.6, past the skin (180). Runner sweep clean 0..150, detent at ~6, stop at 150. Every part on the bed with a flat face, no supports.

## Filament (day profile): **2.38 kg, ~53 h** (incl. switch bosses and the 172 coupon)
Rails 0.19, stations + guides 0.11, trays 0.74, faces 0.65, bins 0.62, bars/switch 0.04. Budget line was "mechanisms ~3.5 incl. scoop/deck, bins ~1": bins are under; trays and faces are the fat (2.4 and 2 mm plates print solid). If D must shed: faces 2 → 1.3 mm (-0.2), tray plate 2.4 → 1.7 with the same ribs (-0.2).

## Print notes
Rails PETG on their side (closed web down). Stations and guide foot down. Trays plate-down (ribs up). Faces outer face down (inlay in the first layers, AMS second colour). Bins floor down. Fits: inserts 4.1, rail tenons/laps 0.07, bins 0.6.

## Open questions
1. 625 pocket coupon result (16.0/16.1/16.2) → fixes the guide-roller and scoop pockets.
2. Runner killer test: droop at 150 with 6-8 kg.
3. KW11-3Z body not measured (assumed 20 × 6.4 × 10.3, M2 holes 9.5 apart).
4. Reed glass assumed 2.0 x 14; MCP23017 module assumed 40 x 25 x 1.6. Measure before printing the trays.
5. The frame chat's face-vs-tile clash (2026-11-06) was a frame bug (skin placed at the 5.1 envelope y +-192); fixed on `cad-v14-frame5` b4965a3, faces unchanged.

## INTERFACE REQUESTS
None. Note for F: the stations' feet sit at y 115..180 (front) / -180..-115 (back), x 206..259 / 128..181 (and mirrored); the drawer-closed mounts at x ±250, y 56..92. Keep floor clips and bottom rails clear of those.

## Vault log lines
- 2026-11-08 PT, claim, Bricked Sorting: module D bin switches: glass reed under every bin in the tray plate, 6 x 2 magnet pressed into each bin floor, one MCP23017 per drawer under tray tile 2, drawer-closed KW11s kept; reed coupon 172 to test first.
- 2026-11-06 19:35 PT, claim, Bricked Sorting: runner test kit rebuilt to interface 5.1 (`v14_runner_test_51.zip`): rail 220 flat on the bed, one 3-roller 625ZZ station per rail on #6 wood screws, 625 pocket coupon 16.0/16.1/16.2. Earlier kits withdrawn.
- 2026-11-06 19:45 PT, claim, Bricked Sorting: module D rebuilt to 5.1 on `cad-v14-all`: bins 70 × 95 × 85 at 76 pitch, body ±306 through the ±310 opening, overlay faces ±330, travel 150, rails ±200 / ±120. Day-profile estimate 2.35 kg / 52 h. All checks clean.
