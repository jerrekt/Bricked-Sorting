# V14 single-chat build: progress

**2026-11-06: interface 5.1** (720 x 360 wood frame + PLA skin). Frame and deck are done elsewhere (`cad-v14-frame5`, `cad-v14-deck5`). This branch: drawers (done 19:45), scoop (done 20:09), integration (done 20:35: `integration/`, 8.66 kg / 148 h, one open item for the frame chat: the 5.1 drawer opening).

Branch `cad-v14-all` (from `cad-v14`; interface **v14-interface-4.3** since 21:30: print rules, fits and gram estimates come from the vault `runbooks/3d-printing.md`; 2.4 mm skins; access panel 420..668). Order from the vault handoff `projects/bricked-sorting-v14-cad-handoff.md` ("one chat" section). A fresh chat: read this list, then the module README of the last done module, then continue at the first open item.

- [x] 1. Runner test kit, interface 4: `drawer/runner_test/` (2026-11-05 19:05 PT; stations re-sent 19:19 with a longer foot for 2 grid holes): rails 160/161 on the drawer underside, floor roller stations 162/163, guide 164. Sent to BJ. (The 18:31 interface-2 T-rail kit is withdrawn: do not print.)
- [x] 2. Drawers + bins (D): `drawer/` (2026-11-05 19:19 PT), interface 4.1. Keyed rails (front ±300, back ±200), 4+5 tray tiles, rib bars, retaining bar, 2 closed switches. All checks clean.
- [ ] 3. Scoop slide (S): `scoop/` — interface-2 draft kept in `scoop/i2_draft/` for its helpers; rebuild to interface 4.
- [ ] 4. Deck (K): `deck/`
- [ ] 5. Frame (F): `frame/`
- [ ] 6. Integration: checks, stills, one-brick animation, zip, buy list + board PR (merge only on "push")

## Message from BJ (2026-11-05 21:58 PT)
Interface is 4.3. Use the vault print runbook for fits and gram estimates, and re-estimate the drawers with it. Their 7.2 kg was solid volume.
- Re-estimate done 22:05 PT with the day-profile model (4 walls = 1.68 mm solid per face, 5/3 shells, 15 % infill): drawers ~7.3 kg either way, because the tray plates (5 mm), faces (3 mm skins) and bins (1.26 walls) are thin enough to print solid under 4 loops. Levers if D must shrink: tray plate 5 -> 2.4 with ribs (-1.2 kg), faces 3 -> 1.7 skins (-0.9), bins 1.26 -> 0.84 walls (-0.6).
- Scoop (S) is still to build: use the runbook fits (dovetails 0.065-0.07, 625 pocket coupon at 16.0/16.1/16.2 first, inserts per inventory/parts-owned.md) and the day-profile grams.

## Decisions taken in this chat (need BJ's OK at integration)
- Runner (interface 4): rail 16 wide x 24 tall (z 8.5..32.5) with a 16.5 side slot; a 16 mm bearing in a 16.5 slot cannot fit the 20 mm tunnel, so the spine tunnels become 24 wide x 26 tall (z 8..34), drawer floor on the rails at z 32.5, bins ~139 tall (top 176).
- Rollers: per rail a front load pair (y 207, 225) and a rear anti-lift pair (165, 183), rear-most slotted for preload; hard stop = closed slot end at 205; detent = 0.4 bump on the slot ceiling.
- Coordinate frame as written is left-handed (front viewer sees +X on the left in CAD). Bins numbered by the real viewer; decide at integration.

## Open questions for BJ
- Runner killer test result (droop at 205 with 6-8 kg).

## Vault lines to log (main chat logs these in inbox/changes.yaml)
- 2026-11-05 19:05 PT: V14 runner test kit rebuilt to interface 4 (rail 160/161 with 16.5 slot on the drawer underside, 625ZZ floor stations 162/163, guide 164); interface-2 T-rail kit withdrawn.
- 2026-11-05 19:19 PT: V14 module D done to interface 4.1 on cad-v14-all: keyed drawers (rails ±300 front, ±200 back), bins 138.5 tall (top 176), retaining bar, two drawer-closed KW11-3Z; ~7.2 kg filament estimate; all clash/zone/bed checks clean.
