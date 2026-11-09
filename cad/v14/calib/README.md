# PETG fit calibration (P2S)

BJ's fits in the vault runbook were measured in Inland PLA only. The runner rails, stations, guides (and the deck's V trays and springs) are PETG, so check PETG first. One plate, ~55 g, ~1.2 h. PETG day profile, textured PEI, no supports, everything flat as exported. Dots on each part = which value (1 dot = first).

| Row | Part | Values (1..5 dots) | Test | Used for |
|---|---|---|---|---|
| A | 180 625ZZ pockets, 5.2 deep | 15.9 / 16.0 / 16.1 / 16.2 / 16.3 | press a 625 in by hand/vise: tightest that seats fully without cracking | guide block, scoop rollers in PETG |
| B | 181 M3 insert holes, 5.7 deep, rev 2 | 4.3 / 4.4 / 4.5 / 4.6 / 4.7 (rev 1 3.9-4.3: all too small) | set an insert with the iron: clean collar, doesn't spin or wobble | rail-top inserts |
| C | 182 M5 axle holes, through 8 | 5.0 / 5.1 / 5.2 / 5.3 / 5.4 | push an M5 screw: snug, no slop | station roller axles |
| D | 183 dovetail pairs rev 2 (elephant-foot + corner reliefs) | 0.10 / 0.15 / 0.20 / 0.25 / 0.30 per side (rev 1 0.05-0.15: none fit) | slide the male down into the female: tightest that goes by hand | any PETG slide/lap joint |

Report: "PETG: A <dots>, B <dots>, C <dots>, D <dots>" and which plate. The runbook gets a PETG line; the rails/stations get re-cut to those numbers before the runner kit is printed.

Script: `build_petg_calib.py` -> `print/`.
