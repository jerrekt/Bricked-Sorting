# V14 integration (interface 5.1)

2026-11-06 20:35 PT on `cad-v14-all`. Script `build_integration.py` loads every module's `world/` (F from the `cad-v14-frame5` worktree, K from `cad-v14-deck5`, D and S from this branch), checks the whole machine and writes `checks.json`, `buy_list.md`, 3 stills and `one_brick.gif`.

## Results
| Check | Result |
|---|---|
| Frame vs drawers **open** (both out 150) | 0 clashes |
| Frame vs drawers **closed** | 8 small hits (40-75 mm³ each): frame5 is still on interface 5 (skin opening x ±300); the 5.1 opening is ±310 and the drawer body is ±306. **Frame chat: rebuild the two drawer-wall tile rows with the ±310 opening**, nothing else changes. |
| Frame vs deck, frame vs scoop, deck vs scoop, deck vs drawers, drawers vs scoop | 0 |
| Scoop at 17 poses vs frame, deck, closed drawers | 0 |
| Envelope | x ±360, y ±192 (overlay faces), z 0..664: exact |
| Printed total (day profile) | **8.66 kg, ~148 h** vs the 9.5 kg / 200 h budget: frame + skin 4.33 kg / 59 h, drawers 2.35 / 52, deck 1.37 / 23, scoop 0.62 / 14 |

Filament by the interface's budget lines: skin ~4.3 (budget 4.6) ✓, studs 0.46 (0.5) ✓, mechanisms (scoop + deck + runners/trays/faces) 3.7 (3.5) ~, bins 0.62 (1.0) ✓.

## Assembly order (from the module READMEs)
1. Wood: cut list and drilling map in `frame/`. Screw the posts, rails, cleats and beam posts; floor plywood; deck plywood last (after step 4).
2. Floor: drawer roller stations and guides (#6 screws, positions in `drawer/README.md`), closed-switch mounts; slide the drawers in from the front/back with the rails on the stations; set the preload.
3. Scoop: end plates onto the beam posts, beam segments plugged together, motor bracket and idler, carriage with its 6 bearings, cup and servo bracket, belt, lead clip at x 0.
4. Deck: cradles and drum, hopper, chute, trays on their springs, scanner on its standoffs, funnel through the hole, electronics trays; lift the deck plywood onto the cleats.
5. Skin: clips to the wood, tiles with H clips, roof with the studs, corner caps, access panel.
6. Print first: 625 pocket coupon and the runner test kit (`drawer/runner_test/`), then one C1/H clip + tile strip (frame README), then a trapdoor set and one V tray.

## Open items
- 625 pocket size (coupon) → scoop towers, idler, guide rollers.
- Runner killer test result.
- Frame5 → 5.1 drawer opening (±310).
- Scoop: beam sag check in print (see `scoop/README.md`).
- KW11-3Z body dimensions (assumed).

## Vault log lines
- 2026-11-06 20:35 PT, claim, Bricked Sorting: V14 integration on `cad-v14-all` (interface 5.1). Whole machine: drawers open/closed, scoop 17 poses, deck, frame: 0 clashes except 8 small hits of the 5.0 frame skin opening (±300) on the ±306 drawer body, fixed by the 5.1 opening. Printed total 8.66 kg / ~148 h (budget 9.5 / 200). Envelope 720 × 384 × 664 exact. `one_brick.gif` shows receive → carry → dump → return.
