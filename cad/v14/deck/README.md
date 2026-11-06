# V14 module K: deck (drum, hopper, trays, scanner, electronics)

Built to **v14-interface-4.1** (frozen) on branch `cad-v14-deck`.
- Script: `build_deck.py` (CadQuery 2.8). It reads `../interface.json` and the V13 STEPs in `../../reference_v13/`. Helpers are in `k_common.py`, a copy of `cad-v14-all:cad/v14/common.py`, so this branch builds on its own.
- Outputs:
  - `world/`: STEP in machine coordinates, plus `deck_assembly.step`
  - `print/`: new parts laid flat
  - `parts.json`, `checks.json`, and 5 stills

Coordinates are right-handed: +X is the front viewer's left, +Y is the front, +Z is up.

**Rev 2 (2026-11-05 20:40 PT, BJ):**
- Small hopper (~150 across) with a 4-piece collar to the stud ring and M3 seam lugs.
- Drum tilt cut to 2°, and the drum raised.
- Trays now 4.5°. The scanner floor stays at 459 and the funnel exit at 335.

## Brick path and heights
The heights are solved from the fixed scanner floor upward (`TRAY_DEG` at the top of the script).

| Stage | Where | z |
|---|---|---|
| Hopper 201 | One piece, ~150 across (r 75 rim). An oblique cone from the stud centre (-260, 0) down to the outlet r 30 at (-245, -50). Worst wall 44.9°. | 778 → 681 |
| Collar 200 (4 quarters) | r 77.7..144.5 (stud ring ID 290). Top slopes from 780 at the ring to 778 at the rim, so stray bricks slide in. It sits on the hopper's rim flange with 4 × M3. | 775..780 |
| Feed chute 202 | U trough at **45°**. Ends 22 mm inside the drum rear, 18 below the axis. | 679 → 594 |
| Drum (V13, as-is) | Axis front-back at x -200, rear end at y 0, tilted **2°** down toward +Y. Barrel top at the rear is 692.6, under the roof at 700. | axis 612.6 → 606.3 |
| Outlet | 49b window at the bottom of the front plate | 538.5 |
| V1 203 (2 pieces + splice) | Along +X at y 216, x -245 → 75 | 528.1 → 502.9 (**4.5°**) |
| V2 204 | Diagonal (65, 205) → (262, 8), notched where V1 drops in | 494.9 → 473.0 (**4.5°**) |
| Landing ramp 211 | V13 ramp, lowered | 467 → 459 |
| Scanner floor | Over (330, 0) | **459** |
| Drop funnel 220 | Mouth r 54 at 415, 45° cone to r 28, tube through the deck hole | exit **335** |

**Max tray slope: about 5.0°.** The remaining height is ~6 mm between the drum top (692.6 rear, plate top 693.8) and the roof underside at 700. Using it would give ~5.0° and leave ~1 mm, and the chute would drop to ~43°. I kept 4.5° for the margin.

## Parts
**Drum, reused as-is.** The V13 drum group is moved rigidly into the new frame: 47b barrel, 49b static plate, 48 rear guard, 4 × 50 rollers, 54 core, 55 TPU tire, 56 NEMA17 bracket.

**New: drum supports.**
- **205 cradles A/B.** Each roller sits between 5 mm axle forks (M5). A cheek takes the 49b ear (2 × M3). The motor wall for bracket 56 (4 × M5) is merged into cradle B. Bases bolt to the deck grid.

**New: hopper and chute.**
- **201 hopper.** One piece with a rim flange r 75..92 at z 770..775 (4 M3 inserts at r 84).
- Three arms run out to the roof inserts at r 108 from (-260, 0), at **180° / 240° / 300°**. These angles changed from rev 1 so the arms stay clear of the raised drum.
- **200 collar.** 4 quarters, each with M3 seam lugs (6 × 16 × 10.5, one each side of the seam at r 112, M3 × 16 + nut across). Screwed down into the flange inserts.
- **202 chute.**

**New: trays.**
- **203 V1** (two pieces + splice) and **204 V2**, PETG.
- **207** PETG leaf springs, plus the reused V7 vibration-motor saddle 62 and cap 63 under each tray.

**New: scanner and below.**
- **210-218 scanner:** a rework of V13 57-62/73/74. Standoffs on the deck grid at x 240/440, y ±80.
- **220** drop funnel.
- **225** electronics trays at the back access panel (top z 424).

## Checks (`checks.json`)
- All parts are inside the K zone.
  - The hopper is within r 100 through the roof hole and r 144.5 in the stud ring, below z 780.
  - The funnel stays within r 30 below the deck.
- No clashes. The by-design contacts are only springs and saddles touching their trays, and core and tire.
- Drum at 12 angles: 0 clashes.
- Scanner doors at 0/30/60/90°: 0 clashes.
- Every new part fits 248³.
- Estimated new PLA/PETG: **~1.8 kg**.

## Print notes
- **Hopper:** rim down, one piece, 211 × 197 × 100.
- **Collar quarters:** top face down.
- **Cradles 205:** tree supports.
- **Trays:** PETG, walls up.
- **Leaf springs:** on their side.
- **Scanner plate and funnel:** upside down.
- **Drum:** print order as in the V13 note (49b first, then 47b).

## Open questions
1. **Tray slope:** 4.5° built, ~5.0° is the most that fits. Test V1 with its motor before printing V2.
2. **Drum feed rate:** at 2° tilt the flight alone walks the bricks (90 mm per turn). If they move too slowly, raise the drum rpm.
3. **Electronics:** board sizes are placeholders (`EL` in the script). Measure the real boards.

## INTERFACE REQUESTS
None (built to 4.1). For F at integration:
- **3 M3 inserts in the roof underside** at r 108 from (-260, 0), angles 180 / 240 / 300°.
- The deck-grid holes used by the cradles, springs, standoffs, funnel flange and electronics legs.

## Vault log lines (for the main chat to add to `inbox/changes.yaml`)
- 2026-11-05 20:03 PT, claim, Bricked Sorting: V14 module K (deck) built on `cad-v14-deck` to interface 4.1 (rev 1).
  - V13 drum reused as-is; hopper, chute, V1/V2 on leaf springs.
  - V13-rework scanner over (330, 0), funnel exit 335, electronics at the back panel.
  - All checks clean.
- 2026-11-05 20:40 PT, decision, Bricked Sorting: deck rev 2 per BJ.
  - Before: big hopper filling the stud, drum tilt 6°, trays ~1-2°.
  - After: hopper ~150 across centred in the stud with a 4-piece collar (M3 seam lugs), drum tilt 2° and raised (barrel top 692.6 under the 700 roof), trays 4.5° (max ~5.0°), chute 45°.
  - Roof inserts move to 180/240/300° at r 108. Scanner floor 459 and funnel exit 335 unchanged.
