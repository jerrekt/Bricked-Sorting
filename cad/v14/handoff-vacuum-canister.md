# Handoff: vacuum canister that docks on the hopper stud

This is for a new chat. Attach `jerrekt/Bricked-Sorting` with push access, and `jerrekt/mnemosyne` (read-only is fine).

Read these first, in order:
1. The vault's `runbooks/3d-printing.md` (print profile, fits, grams).
2. The vault's `inventory/parts-owned.md` (inserts and screws BJ owns).
3. This file.
4. `cad/v14/INTERFACE.md` and `interface.json` (v14-interface-5.1).
5. `cad/v14/handoff-top-attachment.md`. It has the same stud measurements, but some of its fit numbers are older than the PETG values below.

Where the geometry lives:
- Frame and studs: branch `cad-v14-frame5`, `cad/v14/frame/build_frame.py`, function `stud_parts()`.
- Hopper: branch `cad-v14-deck5`, `cad/v14/deck/build_deck.py`, function `hopper()`, constants in `k_common.py`.
- Plates, print log, integration check and BOM: branch `cad-v14-all`.

## The job
BJ wants a separate vacuum attachment. It works in two stages:
1. **Collect.** The canister sits inline between his shop vac hose and a nozzle. It sucks loose LEGO off the table or floor. A screen keeps every piece in the canister and out of the vac.
2. **Feed.** The canister detaches from the vac with the pieces still inside. It sits on top of the machine's left stud, and a gate in its bottom opens to drop the pieces into the hopper.

It is a separate accessory. Nothing on the machine changes, unless BJ agrees that a small feature on the hopper or stud is worth a reprint (both are already printed).

## Ask BJ before designing (don't assume any of these)
His rule is: don't assume component sizes; use the parts he actually owns.
- **Vacuum:** which shop vac (model), and the hose end it uses: OD/ID and cuff type. Common sizes are 1-1/4, 1-7/8 and 2-1/2 in, but measure his. Ask which nozzle or wand goes on the intake side.
- **Load size:** how much one load should hold. One 10696 set is 484 pieces.
  - The hopper holds only about **0.93 L** (an oblique cone from r 75 at z 658 to r 30 at z 557).
  - So either one canister load is ≤ ~0.9 L of loose pieces, or the gate meters the pieces (opens part way, or you dump in stages).
  - Ask BJ to measure the bulk volume of one set in a measuring jug.
- **Scope:** is this needed for the semester-1 POC demo (early December) or for semester 2? This decides whether it goes in the `1_now` folder or `3_semester2`.
- **Material:** PETG for anything that takes impacts, or red PLA for looks. Optionally a TPU liner where pieces hit the wall.

## Interface on top of the machine (as built and printed)
Machine coordinates: origin at the floor centre, +X is the front viewer's left, +Y is front, +Z is up.

| Item | Value |
|---|---|
| Left stud (130, printed, red PLA) | Centre (-180, 0). OD **216**. Open ring with an 8 mm wall (ID 200). Foot on the roof at z 614, **top rim r 100..108 at z 664**. The top outer edge is sharp; the 0.6 chamfer is on the bottom edge only. |
| Hopper (201, printed) | Sits inside the stud. **Flat top ring r 75..100 at z 663** (1 mm below the stud rim). **Mouth r 75** (150 across). Outlet r 30 at (-210, 40, 557), then a chute to the drum. |
| Hopper screw bores | Four **6.4 mm bores at r 92.5** (45/135/225/315 deg). They run from the top (z 663) down to M3 countersunk heads at z 651, so they are 12 deep. They are open, and could key a gate (see the idea below). |
| Right stud (131, printed) | Centre (+180, 0). OD 216, capped with a flat top at z 664 and a 2.4 mm wall. Could be a parking spot for the canister. |
| Roof | 2 mm red PLA. Never load it directly. The left stud is screwed through it into two 1x2 cross rails at x -292 / -68. A full canister resting on the stud is fine. |
| Machine height | 664. A canister on top makes it taller: keep the total sane and stable, and say the final height. |

## Requirements
- **Docking:** locate on the stud **OD 216** with a socket (ring or C shape) that seats on the rim at z 664. Use the runbook's sliding fit for the material; the scoop used **0.20 per side** in PETG. Print a short coupon ring of the socket before the full part.
  - Socket wall ≥ 2.4.
  - Depth 15–30, so it sits square and can't tip off when full.
  - Don't touch the roof tiles around the stud.
- **The drop has to land in the hopper mouth (r 75).** Pieces must not land on the hopper's top ring or the stud rim, and must not bounce out.
- **The gate opens only when the canister is docked,** so nothing spills while carrying it. Idea to check (BJ hasn't decided):
  - The gate disc has 4 pins (~5.6 dia, ≤ 10 long) at r 92.5, 90 deg apart, that drop into the hopper's 6.4 bores.
  - Twisting the canister body then turns it against the held disc and lines up the openings.
  - Check the pins clear the screw heads at z 651.
  - Alternatives: a slide gate, or an iris. Pick whichever prints with no supports and can't jam on a piece.
- **Screen between the pieces and the vac outlet:** holes ≤ 5 mm round (or slots ≤ 2.5 mm). The smallest pieces in 10696 are 1x1 round plates and 1x1 round tiles (8 dia × 3.2). Put the screen where pieces can't pack against it and choke the airflow (side-entry inlet, screen high up near the lid).
- **Inlet:** tangential or angled downward, so pieces slow down and spin against the wall instead of hammering the gate. Seal the joints well enough that the vac still lifts a 2x4 brick at the nozzle.
- **Hose fittings:** both hose fittings must come off without tools (friction cuff or bayonet), sized to BJ's measured hose.
- **Material:** PETG by default (impacts). The visible shell can be red PLA if BJ wants it to look like part of the brick.

## Print and CAD rules (same as every module)
- **Deliverables:** a new branch `cad-v14-vac` from `cad-v14-all`, with folder `cad/v14/vac/` containing:
  - `build_vac.py` (CadQuery)
  - `world/` STEP files in machine coordinates (docked pose)
  - `print/` STL files posed on the bed
  - `parts.json` (grams and hours on BJ's day profile)
  - `checks.json`
  - `README.md` with open questions
  - stills
- **Part numbers:** **250–269** (F 100–149, D 150–179, S 180–199 and K 200–249 are taken).
- **Printability:**
  - No supports: overhangs ≤ 45 deg, bridges ≤ 30.
  - Horizontal holes get the 0.5 mm truncated teardrop (`k_common.teardrop()`).
  - Every part has a flat face on the bed and fits ≤ 248 × 248.
  - Run `plates/support_check.py`.
- **Inserts and fits:**
  - M3 heat-set holes **4.4 in PETG**, 4.3 in PLA.
  - M5 Ruthex holes 6.4.
  - PETG sliding fits 0.20 per side.
- **Before anything goes to BJ:**
  - `plates/check_bodies.py`: every print STL must be ONE solid.
  - `integration/build_integration.py`: add the docked canister and show **0 clashes** with the stud, hopper and roof tiles.
- **Print file:** the next plate is **P24**. Add it to `plates/versions.json` and name it `P24_v1_<PETG|PLAred|TPU>_vac_<what>.3mf`; the material in the name is what to load. Any later change bumps the version and adds a change-log line that says whether to reprint.
- **Then:**
  - rebuild the pack (`build_print_pack.py`)
  - run `print_status.py` and `make_previews.py`, so the website Prints page shows it
  - add the hardware value to `integration/build_bom.py` (a rough "value used", not whole packs)
  - publish to the `prints` branch, which BJ's NAS folder pulls every 15 min
- **Filament:** BJ logs real grams and time from Bambu after each print, into `plates/print_log.json`.
  - Prices: red PLA $9.99/kg, PETG $39.99 per 4 kg, both plus 9.375 % tax.

## Git
- Commit and push all work, but never push to main; the website goes through a PR that BJ merges.
- Never use a bare `git stash`.
- Every commit ends with the Co-Authored-By and Claude-Session trailers.
- Vault: push nothing to Mnemosyne. List the log lines in the README for the main chat.
