# V14 module D: drawers, bins and runners

Built by the single V14 chat on `cad-v14-all` to interface v14-interface-2. Script: `build_drawer.py` (CadQuery 2.8, reads `../interface.json`; runner geometry in `runner.py`). Outputs: `world/` (STEP in machine coordinates, both drawers closed, plus `drawer_assembly.step`), `print/` (STL laid flat), `parts.json`, `checks.json`, four stills. The runner test kit is in `runner_test/`.

## What it is
- **Two identical drawers.** The back drawer is the front drawer turned 180° about Z. Only the face colour and the letter change (F or B).
- **4 undermount runners per drawer** (150 rail + 151 bar, PETG). Front runners sit at x = -400, -160, 80, 440. Turned 180°, the back runners land at 400, 160, -80, -440, so the two sets interleave in the spine strip.
  - Travel is 220 with a hard stop and a closed detent. 96 mm stays engaged at full pull.
  - Rails bolt into the floor grid (6 holes each). The tray bolts onto the bar flange inserts.
- **Tray:** 4 tiles per drawer (152.1-152.4), split in bin gaps at x = -232, 0, 232. The seams are 12 mm half-laps with 3 × M3 + nut.
  - The tray carries bin ribs (0.6 clearance), a rear stop wall and front stops.
  - It also carries a KW11-3Z boss and lever window under each bin. Four of them are offset 35 mm to clear a runner.
  - The MCP23017 bosses go on tile 3, and the closed-switch tab on tile 1.
- **Face:** 4 pieces per drawer (153 front, 154 back), z 10..184 in the wall opening.
  - Notched over the rails, with a grip slot in the two middle pieces.
  - Marks are an inlay: the face has a 0.6 mm pocket, and the matching `_ink` STL fills it. Put both on one plate and give `_ink` white on the AMS.
  - F1..F8 run left to right for someone standing at the front. The same piece turned 180° reads B1..B8 from the back, so B1 sits behind F8.
- **Bins (155, ×16):** 106.8 × 146.4 body plus a 2.4 label holder = inside the 108 × 150 cell. 120 tall, top at z 160.
  - Walls 1.26 (3 loops), floor 2.9, with a stiff top rim.
  - A handle slot in the front wall, and a slide-in label card (70 × 32 × ~0.5) open at the top.
- **Wiring:**
  - Each drawer carries its own MCP23017, which reads 8 bin switches. The drawer-closed switch is on the floor (156) and wires straight to the deck.
  - Only 4 wires (I2C + 3V3/GND) move. They run as a flat ribbon rolling loop in the lane at x 262 (back drawer: -262), from the floor clip (157) at y -20 to the tray anchor at y 74.
  - Loop length ~200 + bend. Its bend travels half the stroke (~110), so it survives 220.

## Checks (`checks.json`)
- Every part fits 248³. Rails and bars sit at 45° on the bed (246 / 243).
- No clashes in any of three states: both drawers closed, front open with back closed, back open with front closed.
- Open drawer: the bin rear is at y 295.6, outside the 260 face, so bins lift out freely.
- Bin top is at 160 (limit 176).
- Zones: all parts are inside the D zone, except the runner tails, which use the center-spine strip (request 1).

## Print notes
- Runners: PETG, base down / flange down, no supports. Do the coupon in `runner_test/` first.
- Bins: PLA, open top up, no supports, vase-like but 3 loops.
- Tray tiles: PLA, top up. Small tree supports (build plate only) under the switch and MCP bosses.
- Faces: outer face on the bed, so the inlay prints in the first layers.
- Mass: the slicer-like estimate is about 7.6 kg PLA+PETG for the whole module. Bins are ~2 kg, faces ~2 kg, tray ~2 kg, runners ~1.5 kg. Weigh after slicing; see the open questions for options.

## Open questions
1. Measure a KW11-3Z with calipers. Body 20 × 6.4 × 10.3 and M2 holes 9.5 apart are assumed; edit `SW_*`.
2. Bins could be 90 tall instead of 120, which saves ~0.5 kg. Taller bins catch bounces better. Kept at 120.
3. Face colours: proposed SME blue front and SME green back, white marks (all on hand).
4. Should the tray be lightened? It can be pocketed under each bin if the weight matters.

## INTERFACE REQUESTS
1. **Runner tails in the spine strip.**
   - Why: single stage cannot reach 220 mm inside a 190 mm deep zone. Rail and bar must run back to y -62 (front) or +62 (back).
   - Ask: give D the strip y ±66, z 8..30 at x = ±80, ±160, ±400, ±440 (±17 each side). The frame's spine sits between and above those lanes (above z 36 under each tray is drawer space, so the spine keeps to y ±66).
   - Also ask: let D use the floor at x 254..290 / -290..-254, y -30..-10 for the ribbon clips.
2. **Handedness.**
   - The interface says "+X right when you face the drawer" and "+Y toward the front". In a right-handed CAD frame those conflict: a person at the front (+Y) has +X on their left.
   - Effect: in CAD the scanner (x 330) is on the front viewer's left and the hopper on their right, mirrored from the layout sketch.
   - Bin numbering follows the real viewer (F1 at x +406), so the marks are right either way.
   - Decide at integration: accept the mirror, or swap which side is called the front.
3. **Bin switches.** Bin presence uses one KW11-3Z per bin, under the tray. That needs 16 windows, which are in the CAD now.
