# Fit checks (2026-11-26)

What was checked in the CAD before building, and what to watch for with the real wood. All numbers are CAD gaps; real wood and hand placement move them, so anything under 1/8 in has a check or a fix in a guide.

Method: every pair of separately placed parts was meshed and the smallest gap measured (the whole-machine clash check only finds overlaps, and the deck check had allowed any spring-to-tray contact). Plus: every skin screw against the smallest boards measured, screw tips under the deck against the scoop, and ray tests for where pieces fall.

## Does not fit (decision needed)

| Where | CAD | What happens | Guide |
|---|---|---|---|
| **V1 → V2 hand-off** | V2 is under only ~1/4 of V1's outlet | Pieces leaving V1 at x 40–72 mm fall 97 mm to the deck. Pieces that land on V2 run under V1 with 2.8–6 mm of headroom: bricks (9.6 mm) jam. | Isolate step 4, trays on hold |
| V2 ↔ V1 front spring (S2) | 0.0 mm | Both vibrate: they rub | same |
| V2 ↔ V1 side wall | 0.02 mm | same | same |
| Scoop carriage ↔ home switch mount | flag hits the mount 2 mm past home | the hopper-end bin column (26 mm past home) can't be reached | POC: containers spaced to the real travel (Indicate 5). Drawers: switch must move (CAD) |

## Fixed in the guides

| Where | CAD | Fix | Guide |
|---|---|---|---|
| Hopper outlet ↔ chute | 38 % of the outlet open, no support | 1x2 support block + card deflector; ring 1/8 in under the outlet | Isolate 5 |
| Hopper ↔ chute ring | 0.5 mm | block trimmed to give 1/8 in | Isolate 5 |
| Electronics trays ↔ access panel keeper bars | 0.0 mm (4 places) | notch each tray's back edge 7/8 × 3/16 in at the bars → 3.3–4.4 mm | Electronics 0 |
| Tray 1a ↔ hopper-end back post | 0.0 mm | tray 1a 1/8 in toward the scanner end → 3.0 mm (5.4 for the AC cover) | Electronics 0 |
| Front mid rail height | given 1/2 in too high (from the floor underside) | 9 7/16 in below the top edge of the front top rail | Skin 0 |
| Access panel keeper bars | on no print plate | P26 v1 | Skin 2 |
| Funnel tube ↔ deck hole | 0.5 mm radial with a 2 3/16 in hole | 2 1/4 in hole saw → 1.1 mm | Identify 0 |

## Tight but OK: check during the build

| Where | CAD | Real-life risk | Check |
|---|---|---|---|
| Hopper outside ↔ drum rear guard (turns) | 1.95 mm | roof vs deck height | spin the drum with the roof on (Isolate 6) |
| Drum ↔ roof cross rail | 5.4 mm | cross rail height | same |
| Tray front legs ↔ drum cradle B | 2.3 mm | both hand placed | ≥ 1/16 in (Electronics 0) |
| Trays ↔ access panel | 3.2 mm | panel flex | panel goes on without touching |
| Scanner doors open ↔ funnel mouth | ~1 mm | plate feet height | open by hand; shim feet 1/16 in if they touch (Identify 3) |
| V2 end ↔ landing ramp | 3.1 mm | ramp placement | ramp glued last (Identify 4) |
| V2 low spring (S4) ↔ landing ramp | 2.5 mm | same | same |
| V1 ↔ drum outlet plate 49b | 3.3 mm | V1 vibrates | ~1/8 in (Isolate 4) |
| V1 springs ↔ drum cradles | 3.7 mm | hand placed | ≥ 1/8 in |
| V1 front spring ↔ V2 high spring | 2.5 mm | both vibrate | ≥ 1/16 in |
| Scoop motor ↔ hopper-end wall tiles | 3.3 mm | beam post position | look after the walls go on (Indicate 6) |
| Scanner foot 1 ↔ tray 2 leg | 5.0 mm | hand placed | |
| Cable clip 226-1 ↔ scanner-end back post | 5.0 mm | | |

## Checked and fine

- **Skin screws:** all 220 (walls 132, corner caps 48, roof 32, keeper bars 8) land at least 5/32 in inside the wood with the smallest boards measured (2x2 34.9 mm, 1x2 36.4 mm).
- **Screw tips under the deck:** #6 × 3/4 through 3–6 mm feet into 7/16–1/2 in deck pokes 1/16–3/16 in out underneath. The scoop cup's highest point at a dump is 7 mm under the deck, and under the deck screws it stays at least 1/4 in below their tips, so nothing hits.
- **Tray legs:** #6 × 1 1/4 through tray + leg (22 mm) goes about 3/8 in into the deck and does not come through.
- **Hopper in the roof:** at least 10.7 mm from every roof tile; it sits on the stud ledge as drawn.
- **Front mid rail:** V2's high end passes 9 mm above it.
- Whole-machine clash check (frame, deck, scoop, drawers, vacuum): 0 overlaps.
