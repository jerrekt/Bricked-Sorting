# V14 module D: drawers, bins and runners (interface 4.1)

Built by the single V14 chat on `cad-v14-all`. Script: `build_drawer.py` (CadQuery 2.8, reads `../interface.json`); runner geometry is in `runner.py`, and the test kit is in `runner_test/`.

Outputs:
- `world/`: STEP files in machine coordinates (both drawers closed), plus `drawer_assembly.step`
- `print/`: STLs laid flat
- `parts.json`, `checks.json`
- 4 stills

## What it is
- **Two keyed drawers.** The front drawer's rails are at x ±300 and the back drawer's at ±200, so each drawer only fits its own floor stations. The back drawer is the same design turned 180°.
- **Runners (160/161 rails, 162/163 stations, 164 guide):**
  - The rail is 16 × 24 PETG on the drawer underside, z 8.5..32.5. It has a 16.5 side slot and its tail runs through the spine tunnels.
  - Each rail runs on a front load pair of 625ZZ (y 207/225) and a rear anti-lift pair (165/183). The rear-most roller has a preload slot with an M3 jack screw.
  - Travel is 205. The hard stop is the closed slot end, and the closed detent is a 0.4 mm bump.
  - The +X rail of each drawer gets a guide block (two vertical-axle 625ZZ). The other rail floats.
- **Tray (165):** 5 mm PLA plate on the rail tops, z 32.5..37.5.
  - Front drawer: 4 tiles, split at x -232/0/232. Back drawer: 5 tiles, split at ±116/±348, so its seams stay clear of its stations.
  - The tray carries bin locators, a rear stop wall, front stops, and plate half-laps with 2 bolts.
  - Under it are 3 rows of rib bars (172), bolted up into the plate. They sit only where nothing fixed is on the floor along the travel, and they bridge the seams.
- **Faces (166 front, 167 back):** one piece per tile, z 10..184.
  - Notched over the rails, with grip slots.
  - The F/B + number marks are a 0.6 mm inlay: an `_ink` STL fills the pocket, white on the AMS.
  - Numbering: F1 is the left bin for a person at the front, and B1 the left bin for a person at the back (behind F8).
- **Bins (168, ×16):** 106.8 × 146.4 plus a 2.4 label holder. 138.5 tall, top at 176.
  - Walls 1.26 (3 loops), stiff rim, handle slot, slide-in label card.
- **Retaining bar (169 + posts 171):** one bar per tile sits in post seats just above the bins' inner rims (y 72..82, z 176.5..182.5). Bins can't lift out until the bar comes off.
- **Drawer-closed switch:** one KW11-3Z per drawer on the floor (170) at x -400 (back: +400), pressed by a tab (173) under the tray when closed. No per-bin switches.

## Checks (`checks.json`)
- Every part fits 248³. Rails print on their side at 45° (240).
- No clashes in any state: both closed, front open, back open, both open.
- Zones: everything is inside the D zone; the rail tails are in the spine tunnels as allowed.
- Bin top is 176.0. Open bins sit at y 280.6, past the 260 face.
- The runner sweep is clean 0..205, with the detent at about 6 mm and the stop past 205.
- Mass estimate: ~7.2 kg (PLA + PETG). Weigh it after slicing.

## Print notes
- Tray tiles: plate down, no supports (the switch tab and ribs are separate parts).
- Rib bars: on their side, inserts from the top face.
- Faces: outer face on the bed.
- Bins: open top up.
- Runners: PETG; see `runner_test/README.md`.

## Open questions
1. Measure a KW11-3Z with calipers. The body is assumed to be 20 × 6.4 × 10.3 with M2 holes 9.5 apart.
2. Face colours: proposed SME blue for the front and SME green for the back, both with white marks.
3. Handedness: as written, the interface has a front viewer seeing +X on their left. Bin marks follow the real viewer. Decide at integration.

## INTERFACE REQUESTS
None. Interface 4.1 already has the 26 mm tunnels.
- F: the spine needs tunnels 24 × 26 at x ±200 / ±300 that the rails pass through.
- F: the floor-grid holes listed in each station or guide need inserts.
