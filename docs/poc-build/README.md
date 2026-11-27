# POC build pack

Build instructions for the proof of concept (demo **Wed Dec 2, 1 pm**; report **Tue Dec 1, 5 pm**). Start here.

| Order | Guide | What |
|---|---|---|
| 0 | [`build-order.md`](build-order.md) | **Start here:** the order across all the guides, motion tests, first run, demo-day list. |
| 1 | [`isolate-mounting.md`](isolate-mounting.md) | Drum, drive, V1/V2 trays, hopper and chute (chute as printed, with a support block and a card deflector). Also sets the two centre lines every other guide uses. |
| 2 | [`identify.md`](identify.md) | Funnel hole, funnel, scanner plate with trapdoors and linkage, servo, camera bridge, webcam, LEDs, colour sensor. |
| 3 | [`indicate.md`](indicate.md) | Scoop beam (measure the beam posts first), carriage, belt drive, home switch, cup and tilt servo, 16 POC containers. |
| 4 | [`electronics.md`](electronics.md) | Trays, PSU, mains inlet, bucks, drivers, power diagram, proposed pin map, cable routes, power-up checks. |
| 5 | [`skin.md`](skin.md) | New front mid rail, wall tiles, access panel and keeper bars, corner caps, roof halves with the studs. |
| | [`fit-checks.md`](fit-checks.md) | Every tight spot found in the CAD, what real wood can do to it, and the fix or check. |
| | [`buy-list.md`](buy-list.md) | What to buy and what to check you have. |
| | `img/` | Layouts and step views used by the guides. |

Common to all guides: **front** = logo side, **back** = access panel side, **hopper end** / **scanner end**. Positions are in inches from the two centre lines on the deck (Isolate step 0), or from a part that is already in.

## Slides

Deck: "Bricked Sorting: Proof of Concept" (Claude Slides artifact, private to BJ). Updated 2026-11-26:
- Cover and Next Semester: new CAD renders with the team logo.
- Current Status: print totals 5.6 kg / 51 jobs / ~150 h; vacuum attachment moved to Working; wall panels in Not Yet.
- Budget: filament spent ~$61. Performance: 182 print files checked.

Still to fill before Dec 2: photo of the built machine (Our Proof of Concept), test results (Specification Sheet, Performance), weight. The Current Status "Working" list still says every stage is mounted; correct it the day before.

## Found while writing these (2026-11-26)

1. **Chute (P12)** leaves about 38 % of the hopper outlet open and has no support. Not redesigned: Isolate section 5 fixes it with a scrap block and a card deflector.
2. **Front mid rail height** was given as 14 11/16 in above the floor top. That number measured from the floor's underside. Correct: centre **9 7/16 in below the top edge of the front top rail** (Skin step 0).
3. **Access panel keeper bars** were in the CAD but on no print plate. Now **P26 v1** in `walls/`.
4. **625ZZ count:** the scoop needs 12 (8 carriage rollers, 2 cup pivots, idler), not 8. About 20 for drum + scoop.
5. Funnel hole: cut **2 1/4 in**, not 2 3/16 (the funnel tube is 2 3/16 in OD).
6. **V1 → V2 hand-off does not work** (pieces miss V2 or jam under V1). Trays on hold until a fix is chosen. See `fit-checks.md`.
7. Electronics trays touch the access-panel keeper bars and a post: notch the trays, move tray 1a 1/8 in.
8. The scoop can't reach the drawers' hopper-end bin column (home switch in the way): POC containers spaced to the real travel.

## Open items

1. Vibration motors not bought; trays can be mounted but not tested.
2. Pin map in `electronics.md` is a proposal: confirm with Ethan, Vivek and Marshall before soldering.
3. Motion code (`poc_run.py`) not written yet.

## Asking Claude to pick this up

Say "read `docs/poc-build`" (branch `poc-build-guides`, or `main` once merged). Source CAD: `cad-v14-deck5` (deck), `cad-v14-frame5` (frame and skin), `cad-v14-all` (scoop, plates, print log, integration).
