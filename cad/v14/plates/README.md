# Print plates (one .3mf per plate, parts already arranged; open in Bambu Studio, "load geometry only")

`make_plate.py OUT file.stl[:qty] ...` packs STLs onto a 240 x 240 area and spills to _plate2 if needed.

| Plate | Material | Parts | Purpose |
|---|---|---|---|
| P1_PETG_calibration | PETG | 13 (calib/ 180-183) | PETG fits: 625 pockets, M3 insert holes, M5 holes, dovetails |
| P2_PLA_coupons_and_deck_tests | PLA | reed coupon tray + floor (172), one C1 skin clip (120), drum cradle A (205), servo saddle (213) | reed/magnet test, clip test, deck fit checks |
| P3_PETG_deck_tray_test | PETG | V1 tray (203) + one leaf spring (207) | tray + spring test |

Runner kit plate comes after the PETG numbers are in.
| P4_PETG_runner_kit | PETG (SUNLU Matte profile, fan max 40%) | rails 160/161, stations 162 L/R, guide 164 | runner killer test; PETG fits 2026-11-08: insert 4.4, axle 5.1, guide M5 screwed into 5.0 |
| P5_PLA_insert_holes | PLA (Inland) | 184 insert bar 4.0/4.1/4.2/4.3/4.4 | PLA insert hole was never tested (4.1 assumed); PETG needed 4.4 |
| P6_PLA_face_F1..F3 / B1..B3 | PLA red (all six, BJ 2026-11-09); inlay part white (AMS) | one drawer-face piece per plate, face + inlay as one object with 2 parts | outer face down |
| P7_PLA_bars_and_switch_mounts | PLA | 8 retaining-bar pieces (170) + 2 closed-switch mounts (171) | |
