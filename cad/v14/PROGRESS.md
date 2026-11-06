# V14 single-chat build: progress

Branch `cad-v14-all` (from `cad-v14`; interface **v14-interface-4** merged 18:55, interface 2 work was redone). Order from the vault handoff `projects/bricked-sorting-v14-cad-handoff.md` ("one chat" section). A fresh chat: read this list, then the module README of the last done module, then continue at the first open item.

- [x] 1. Runner test kit, interface 4: `drawer/runner_test/` (2026-11-05 19:05 PT): rails 160/161 on the drawer underside, floor roller stations 162/163, guide 164. Sent to BJ. (The 18:31 interface-2 T-rail kit is withdrawn: do not print.)
- [ ] 2. Drawers + bins (D): `drawer/` — interface-2 build (18:39) withdrawn; rebuilding to interface 4 (`build_drawer.py` still the old one until this is ticked).
- [ ] 3. Scoop slide (S): `scoop/` — interface-2 draft kept in `scoop/i2_draft/` for its helpers; rebuild to interface 4.
- [ ] 4. Deck (K): `deck/`
- [ ] 5. Frame (F): `frame/`
- [ ] 6. Integration: checks, stills, one-brick animation, zip, buy list + board PR (merge only on "push")

## Decisions taken in this chat (need BJ's OK at integration)
- Runner (interface 4): rail 16 wide x 24 tall (z 8.5..32.5) with a 16.5 side slot; a 16 mm bearing in a 16.5 slot cannot fit the 20 mm tunnel, so the spine tunnels become 24 wide x 26 tall (z 8..34), drawer floor on the rails at z 32.5, bins ~139 tall (top 176).
- Rollers: per rail a front load pair (y 207, 225) and a rear anti-lift pair (165, 183), rear-most slotted for preload; hard stop = closed slot end at 205; detent = 0.4 bump on the slot ceiling.
- Coordinate frame as written is left-handed (front viewer sees +X on the left in CAD). Bins numbered by the real viewer; decide at integration.

## Open questions for BJ
- Runner killer test result (droop at 205 with 6-8 kg).
