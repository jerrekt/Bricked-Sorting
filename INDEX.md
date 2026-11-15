# Bricked Sorting prints

One folder for every print. File names: `P<n>_v<version>_<material>_<what>.3mf`.
If a plate number has a higher version than what you printed, check the change log below to see if you need to reprint.

done = printed (kept for reprints); 1_now = barebones to print next (makes it sort); 2_later = after it sorts (back drawer, faces, skin)

Material in the file name is what to load: PETG (functional, any colour), PLAred (visible red shell parts: studs, hopper, corner caps, drawer faces with black lettering in slot 2), TPU, PLA (PLA calibration only). Renamed 2026-11-15, no geometry change.

| Plate | Version | Folder | Material | What | Files |
|---|---|---|---|---|---|
| P1 | v1 | done | PETG | PETG calibration rev 1 (done) | 1 |
| P1b | v1 | done | PETG | PETG dovetails rev 1 (done) | 1 |
| P1c | v1 | done | PETG | PETG dovetails rev 2 + insert holes rev 2 (done: dovetail 0.20, insert 4.4) - not printed, not needed | 1 |
| P1d | v1 | done | PETG | PETG insert holes only (done) | 1 |
| P2 | v1 | done | PETG | Coupons: reed tray + floor with magnet pocket, C1 skin clip, servo saddle | 1 |
| P3 | v1 | done | PETG | V1 vibration tray + 1 leaf spring | 1 |
| P4 | v1 | 2_later | PETG | Runner kit: 2 rails, 2 stations, guide. Front kit printed 2026-11-13 (drill the 4.4 face insert in its rails); print 1 more for the back drawer | 1 |
| P5 | v1 | done | PLA | PLA insert-hole bar (done: PLA 4.3) | 1 |
| P6 | v1 | 2_later | PLAred | Drawer faces, red + black lettering, one per plate. B1 printed 2026-11-09 (in done/); F1-F3, B2, B3 left | 6 |
| P7 | v1 | 1_now | PETG | Drawer retaining bars + closed-switch mounts | 1 |
| P8 | v1 | done | PLAred | Left stud (open ring, holds the hopper), red | 1 |
| P9 | v1 | done | PLAred | Right stud (capped), red | 1 |
| P10 | v1 | 2_later | PLAred | 12 corner caps, red (5 mm brim) | 1 |
| P11 | v1 | done | PLAred | Hopper (rev 2, no supports), red | 1 |
| P12 | v1 | done | PETG | Feed chute, red | 1 |
| P13 | v2 | 1_now | PETG | Deck parts left: drum cradle A, webcam mount, webcam cable spool, APDS9960 mount, USB clips 1-2 | 1 |
| P14 | v1 | done | PETG | V2 tray, 3 leaf springs, 4 drum rollers (625 pocket 16.1) | 1 |
| P15 | v1 | done | PETG | Drum barrel (3 walls), printing 2026-11-15, ~10.6 h | 1 |
| P16 | v2 | 1_now | PETG | Drum + gate small parts left: rear guard, drive hub (drill 5 mm if tight), 2 door links, servo arm, 2 vib motor saddles | 1 |
| P17 | v1 | done | TPU | Drum friction tire (TPU) | 1 |
| P18 | v3 | 1_now | PETG | Drop funnel, PSU terminal cover, 3 electronics trays, XIAO camera mount, USB clip 3 (2 plates) | 2 |
| P19 | v1 | 1_now | PETG | Deck parts missing from your project: drum cradle B, motor wall, slider post, LED holders A/B | 1 |
| P20 | v1 | 1_now | PETG | Scoop (PETG fits): 3 beam segments, carriage (tree support ~28 cm2), cup (small tree support), motor bracket, idler channel/slider/wheel, endstop mount, pushrod, servo bracket. ~600 g, one long plate | 1 |
| P21 | v1 | 1_now | TPU | Scoop cup pad (TPU) | 1 |

## Change log

- **P13** v2 2026-11-15: only the parts not printed yet (camera bridge and landing ramp are done); cradle B, motor wall, slider post, LED holders moved to P19
- **P16** v2 2026-11-15: only the parts not printed yet (outlet plate, NEMA bracket, vib caps, gate slider, servo link are done)
- **P18** v2 2026-11-14: PETG insert holes 4.4 on the electronics trays; scanner plate rev 2 (hinge tabs were floating 0.9 mm off the plate, feet now flare so no supports, screwdriver holes over the foot screws). Reprint the scanner plate if you printed v1; v1 trays OK if inserts go in with a push
- **P18** v3 2026-11-15: only the parts not printed yet (scanner plate v2 and both trapdoors are done)

## Filament used

**Total: 1707 g** (PETG 1131 g, PLA 572 g, TPU 4 g) over 59 h of printing (P15 barrel still printing)

Filament used, one line per Bambu job (from BJ's print history). grams source=estimate: part geometry at 2 walls / 15% infill, no supports, brim or purge (the slicer usually reads 5-15% higher); replace with source=slicer when BJ sends the grams Bambu shows for a job. Other projects (JE, SJSU SAEC, SME sign) are not counted.

| When | Bambu job | h | Plate | Ver | Material | g | Status | Parts / note |
|---|---|---|---|---|---|---|---|---|
| 2026-11-08 10:48 | 165_625_pocket_coupon | 0.37 | (coupon) | v1 | PLA | 7 (estimate) | done | 165 625 pocket coupon |
| 2026-11-08 11:26 | pa_line + flow coarse/fine (Bambu) | 1.48 | (Bambu calib) | v0 | PETG | 25 (estimate) | done | PA line, flow rate coarse, flow rate fine (Bambu built-in calibration, rough guess) |
| 2026-11-08 16:12 | 180_petg_625_pockets + 183... | 1.3 | P1 | v1 | PETG | 35 (estimate) | done | 625 pockets, insert holes rev1, M5 holes, dovetails rev1 |
| 2026-11-08 17:49 | 183_petg_dovetail... | 0.72 | P1b | v1 | PETG | 16 (estimate) | done | dovetails rev 2 |
| 2026-11-08 18:58 | 181_petg_insert_holes | 0.33 | P1d | v1 | PETG | 4 (estimate) | done | insert hole bar |
| 2026-11-08 19:18 | 181_petg_insert_holes | 0.38 | P1d | v1 | PETG | 4 (estimate) | done | insert hole bar rev 2 (picked 4.4) |
| 2026-11-08 20:20 | 160_rail + 161 + 162... | 0.17 | P4 (old 4.x kit) | v0 | PETG | 3 (estimate) | canceled | runner kit (stopped at ~10 min) |
| 2026-11-08 20:32 | 160_rail + 161 + 162... | 2.9 | P4 (old 4.x kit) | v0 | PETG | 99 (estimate) | done | rails, stations, guide (old 4.x kit, superseded) (rough: same parts as the 5.1 kit) |
| 2026-11-09 13:22 | 184_pla_insert_holes | 0.3 | P5 | v1 | PLA | 4 (estimate) | done | PLA insert bar |
| 2026-11-09 13:55 | P6_PLA_face_B1 | 3.4 | P6 | v1 | PLA | 89 (estimate) | done | drawer face B1 (red + black lettering) |
| 2026-11-09 21:13 | P8_PLA_red_stud_left_hopper | 3.5 | P8 | v1 | PLA | 148 (estimate) | done | 130 stud ring left (red) |
| 2026-11-10 14:31 | p8-p12_plate_2 | 3.7 | P9 | v1 | PLA | 172 (estimate) | done | 131 stud cap right (red) |
| 2026-11-12 16:47 | p8-p12_plate_5 | 3.1 | P11 | v1 | PLA | 152 (estimate) | done | 201 hopper rev 1 (red) (with supports, not counted) |
| 2026-11-12 20:28 | p8-p12_plate_6 | 0.3 | P3 | v1 | PETG | 4 (estimate) | canceled | V1 tray + spring (stopped at ~18 min) |
| 2026-11-12 20:47 | p8-p12_plate_6 | 1.3 | P3 | v1 | PETG | 37 (estimate) | done | 203 V1 tray, 207 spring V1_1 |
| 2026-11-12 22:20 | p8-p12_plate_9 | 2.2 | P12 | v1 | PETG | 30 (estimate) | done | 202 feed chute (black in the history thumbnail) |
| 2026-11-13 09:26 | p8-p12_plate_8 | 7.0 | P14+P4 | v1 | PETG | 120 (estimate) | done | 204 V2 tray, 207 springs x3, 50b rollers x4, 162 stations L/R, 164 guide R |
| 2026-11-13 17:25 | p8-p12_plate_10 | 1.5 | P2 | v1 | PETG | 32 (estimate) | done | 172 reed coupon tray + floor, 120 clip C1, 213 servo saddle |
| 2026-11-13 19:23 | p8-p12_plate_3 | 2.0 | P4 | v1 | PETG | 63 (estimate) | done | 160 rail R, 161 rail L (missing the front face insert: drill 4.4) |
| 2026-11-14 10:00 | p8-p12_plate_4 | 5.8 | P13/P16/P18 | v1 | PETG | 142 (estimate) | done | 215 camera bridge, 214 trapdoors A/B, 56 NEMA17 bracket, 211 landing ramp, 63 caps x2, 57d slider, 59b servo link |
| 2026-11-14 16:12 | p8-p12_plate_12 | 2.2 | P16 | v1 | PETG | 72 (estimate) | done | 49b drum outlet plate |
| 2026-11-14 19:28 | p8-p12_plate_15 | 0.5 | P17 | v1 | TPU | 4 (estimate) | done | 55 drum tire |
| 2026-11-14 21:33 | p8-p12_plate_16 | 3.6 | P18 | v2 | PETG | 103 (estimate) | done | 210 scanner plate (scanner plate rev 2, confirmed v2 by BJ (access holes there)) |
| 2026-11-15 01:20 | p8-p12_plate_11 | 10.6 | P15 | v1 | PETG | 342 (estimate) | printing | 47b drum barrel (3 walls) |

---

# P14–P18 — what each part is

Zip naming: `P<first>-P<last>.zip` (plate range). Plate files keep their `P<n>_<material>_<what>` names.
All print without supports unless noted. Everything is PETG except P17 (TPU tire). 54 drive core is a V13 part with a PLA-sized 5 mm bore: if it is tight on the motor shaft in PETG, run a 5 mm drill through it.

## P14 — PETG — deck V2 tray, springs, drum rollers
| Part | What it is |
|---|---|
| 204_V2_tray | Second vibration tray: takes bricks from V1 and lines them up single-file into the drum |
| 207_leaf_spring_V1_2 | Second leaf spring for the V1 tray (V1_1 came with P3) |
| 207_leaf_spring_V2_1, V2_2 | The two leaf springs the V2 tray sits on; they let it shake |
| 50b_drum_625_roller ×4 | Drum support rollers; each takes one 625 bearing (16.1 pocket, PETG fit) on an M5 axle in the cradles |

## P15 — PETG — drum barrel
| Part | What it is |
|---|---|
| 47b_tumbler_barrel_helical_flight | The rotating drum; the spiral flight inside walks bricks forward one at a time. Small tree support (~2 cm²) |

## P16 — PETG — drum and scanner small parts (3 plates)
| Part | What it is |
|---|---|
| 49b_drum_static_outlet_plate | Fixed plate at the drum exit; bricks leave the drum through it onto the landing ramp |
| 48_drum_rear_feed_guard | Cover at the drum's back (feed) end so bricks don't fall out |
| 56_drum_NEMA17_adjustable_bracket | Drum motor mount; slots let you push the tire against the drum (bolts to motor wall 206, M5 × 16) |
| 54_drum_drive_core_5mm | Hub on the motor's 5 mm shaft; carries the TPU tire (P17) |
| 62_vib_motor_saddle ×2 | Holders for the vibration motors under the V1/V2 trays |
| 63_vib_motor_cap ×2 | Caps that clamp each vibration motor into its saddle |
| 57d_door_slider | Sliding gate that rides on slider post 212 (test the slide; sand the post if tight) |
| 60_servo_horn_arm | Arm on the servo horn that drives the gate |
| 59_door_link ×2, 59b_servo_link | Linkage from the servo arm to the gate/trapdoors |

## P17 — TPU — drum tire
| Part | What it is |
|---|---|
| 55_drum_friction_tire_TPU | Rubber tire on hub 54; friction-drives the drum |

## P18 — PETG — scanner and electronics (3 plates; M3 insert holes 4.4 for PETG)
| Part | What it is |
|---|---|
| 210_scanner_plate | Platform where each brick stops to be scanned; sits on 4 standoffs on the deck. Rev 2: no supports (flared feet, hinge tabs joined, screw access holes) |
| 214_trapdoor_A, B | Trapdoors in the scanner plate; open to drop the brick after the scan |
| 220_drop_funnel | Under the trapdoors; guides the brick down into the scoop cup. Small tree support |
| 217_xiao_sense_camera_mount | Holds the XIAO ESP32-S3 Sense camera over the scanner |
| 225_electronics_tray_1a_psu | Tray for the power supply (M3 inserts) |
| 225_electronics_tray_1b_power_io | Tray for the power input / switch / fuse side (M3 inserts) |
| 225_electronics_tray_2_pi | Tray for the Raspberry Pi (M3 inserts) |
| 227_psu_terminal_cover | Finger guard over the PSU's AC screw terminals (2 M3 inserts) |
| 226_usb_cable_clip_3 | Clip that routes the USB cable along the deck |

