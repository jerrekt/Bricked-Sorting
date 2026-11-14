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
| P6_PLA_face_F1..F3 / B1..B3 | PLA red body (slot 1), black lettering (slot 2) (BJ 2026-11-09) | one drawer-face piece per plate, face + inlay as one object with 2 parts | outer face down |
| P7_PLA_bars_and_switch_mounts | PLA | 8 retaining-bar pieces (170) + 2 closed-switch mounts (171) | |
| P8_PLA_red_stud_left_hopper | PLA red | stud 130 (open ring, hopper ledge) | frame5, inserts 4.3 |
| P9_PLA_red_stud_right_cap | PLA red | stud 131 (capped) | frame5 |
| P10_PLA_red_corner_caps | PLA red | 12 corner caps 135 (4 corners x 3 rows), standing | frame5 |
| P11_PLA_red_hopper / P12_PLA_red_feed_chute | PLA red | hopper 201, feed chute 202 | deck5, inserts 4.3 |
| P2_PLA_coupons | PLA | reed coupon tray + floor, C1 clip, servo saddle | (replaces P2_PLA_coupons_and_deck_tests; drum cradle moved to P13) |
| P12_PLA_red_feed_chute | PLA red | chute 202, on its side | re-posed 2026-11-12 |
| P13_PLA_deck_parts_plate1/2 | PLA any | drum cradles A/B, motor wall, landing ramp, slider post, camera bridge, LED holders A/B, webcam mount, APDS mount, cable spool, 2 USB clips | no supports |
| P14_PETG_deck_V2_springs_rollers | PETG | V2 tray, 3 leaf springs (V1_2, V2_1, V2_2), 4 drum rollers (625 pocket 16.1) | no supports |
| P15_PLA_drum_barrel | PLA | 47b tumbler barrel (V13 reuse), outlet end down, ~7 h | v13_reuse/ STLs exported from cad/reference_v13 STEPs; ~2 cm2 tree support under the flight |
| P16_PLA_drum_and_scanner_small_plate1-3 | PLA | 49b outlet plate, 48 rear guard, 54 drive core, 56 NEMA17 bracket, 2x 62 saddle, 2x 63 cap, 2x 59 door link, 59b, 57d, 60 | V13 reuse, no supports |
| P17_TPU_drum_tire | TPU | 55 friction tire | |
| P18_PLA_deck_scanner_electronics_plate1-2 | PLA | 210 scanner plate, 214 trapdoors A/B, 220 funnel, 225 electronics trays 1a/1b/2_pi, 227 PSU cover, 217 XIAO camera mount, 226 clip 3 | scanner plate, funnel, electronics trays: Tree (auto) supports, build plate only |
