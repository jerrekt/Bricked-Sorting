# V14 single-chat build: progress

Branch `cad-v14-all` (from `cad-v14`, interface v14-interface-2). Order from the vault handoff `projects/bricked-sorting-v14-cad-handoff.md` ("one chat" section). A fresh chat: read this list, then the module README of the last done module, then continue at the first open item.

- [x] 1. Runner test pair: `drawer/runner_test/` (2026-11-05 18:31 PT). Sent to BJ to print. Fit coupon first (0.20/0.30/0.40), full parts at 0.30.
- [x] 2. Drawers + bins (D): `drawer/` (2026-11-05 18:39 PT). 4 runners per drawer (not 3), checks clean, see `drawer/README.md` INTERFACE REQUESTS 1-3.
- [ ] 3. Scoop slide (S): `scoop/`
- [ ] 4. Deck (K): `deck/`
- [ ] 5. Frame (F): `frame/`
- [ ] 6. Integration: checks, stills, one-brick animation, zip, buy list + board PR (merge only on "push")

## Decisions taken in this chat (need BJ's OK at integration)
- Runner is undermount (bins are 108 wide on a 116 pitch, so there is no room for side rails). 4 runners per drawer at x = -400, -160, 80, 440 (front); the back drawer is the same parts turned 180 deg, so its runners land at 400, 160, -80, -440 and the sets interleave in the spine strip.
- Coordinate frame as written is left-handed (front viewer sees +X on the left in CAD). Bins are numbered by the real viewer; decide at integration (drawer README request 2).
- Single stage cannot give 220 mm travel inside a 190 mm drawer zone, so both rail members run back into the center-spine strip (front rails y -62..256). 96 mm stays engaged at full pull. The spine strip (F) must leave these rails room (INTERFACE REQUEST, see `drawer/README.md`).
- Rails are 318 / 314 long and print at 45 deg on the bed (bed extent 246 / 243, under 248).

## Open questions for BJ
- Coupon result (which clearance slides best).
- Runner killer test result (droop at 220 with 6-8 kg).
