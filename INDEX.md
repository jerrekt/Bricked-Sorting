# Bricked Sorting prints

One folder for every print. File names: `P<n>_v<version>_<material>_<what>.3mf`.
If a plate number has a higher version than what you printed, check the change log below to see if you need to reprint.

done = printed (kept for reprints); 1_now = what the semester-1 POC still needs; 3_semester2 = the finished machine only (back drawer, drawer bars, faces, corner caps, walls, drawers); vac = the vacuum canister accessory (wanted for the December demo, not part of the machine)

Material in the file name is what to load: PETG (functional, any colour), PLAred (visible red shell parts: studs, hopper, corner caps, drawer faces with black lettering in slot 2), TPU, PLA (PLA calibration only). Renamed 2026-11-15, no geometry change.

| Plate | Version | Folder | Material | What | Files |
|---|---|---|---|---|---|
| P1 | v1 | done | PETG | PETG calibration rev 1 (done) | 1 |
| P1b | v1 | done | PETG | PETG dovetails rev 1 (done) | 1 |
| P1c | v1 | done | PETG | PETG dovetails rev 2 + insert holes rev 2 (done: dovetail 0.20, insert 4.4) - not printed, not needed | 1 |
| P1d | v1 | done | PETG | PETG insert holes only (done) | 1 |
| P2 | v1 | done | PETG | Coupons: reed tray + floor with magnet pocket, C1 skin clip, servo saddle | 1 |
| P3 | v1 | done | PETG | V1 vibration tray + 1 leaf spring | 1 |
| P4 | v1 | 3_semester2 | PETG | Runner kit: 2 rails, 2 stations, guide. Front kit printed 2026-11-13 (drill the 4.4 face insert in its rails); print 1 more for the back drawer | 1 |
| P5 | v1 | done | PLA | PLA insert-hole bar (done: PLA 4.3) | 1 |
| P6 | v1 | 3_semester2 | PLAred | Drawer faces, red + black lettering, one per plate. B1 printed 2026-11-09 (in done/); F1-F3, B2, B3 left | 6 |
| P7 | v1 | 3_semester2 | PETG | Drawer retaining bars + closed-switch mounts | 1 |
| P8 | v1 | done | PLAred | Left stud (open ring, holds the hopper), red | 1 |
| P9 | v1 | done | PLAred | Right stud (capped), red | 1 |
| P10 | v1 | 3_semester2 | PLAred | 12 corner caps, red (5 mm brim) | 1 |
| P11 | v1 | done | PLAred | Hopper (rev 2, no supports), red | 1 |
| P12 | v1 | done | PETG | Feed chute, red | 1 |
| P13 | v3 | done | PETG | Deck parts left: drum cradle A, webcam mount, webcam cable spool, APDS9960 mount, USB clips 1-2 - printed 2026-11-16 | 1 |
| P14 | v1 | done | PETG | V2 tray, 3 leaf springs, 4 drum rollers (625 pocket 16.1) | 1 |
| P15 | v1 | done | PETG | Drum barrel (3 walls), printing 2026-11-15, ~10.6 h | 1 |
| P16 | v2 | done | PETG | Drum + gate small parts left: rear guard, drive hub (drill 5 mm if tight), 2 door links, servo arm, 2 vib motor saddles - printed 2026-11-15 | 1 |
| P17 | v1 | done | TPU | Drum friction tire (TPU) | 1 |
| P18 | v5 | done | PETG | Plate 1: PSU tray 1a (slim PSU 142x40x28, M3 grid) + Pi tray 2 (M3 grid). Plate 2: tray 1b (M3 grid), drop funnel, PSU AC-end cover, 16 tray legs. No supports | 2 |
| P19 | v2 | done | PETG | Deck parts missing from your project: drum cradle B, motor wall, slider post, LED holders A/B - printed 2026-11-16 | 1 |
| P20 | v3 | done | PETG | Plate 1: 3 beam segments standing plug-end up, SUPPORTS OFF (only 25 mm bridges inside the closed box), 5 mm brim. Plate 2: carriage, cup, motor bracket, idler channel/slider/wheel, endstop mount, pushrod, servo bracket; tree support | 2 |
| P21 | v1 | 1_now | TPU | Scoop cup pad (TPU) | 1 |
| P22 | v1 | done | PLAred | Roof tiles: 8 DIFFERENT files, print each once (one 180 x 180 tile per plate, ~1 h each), red PLA, face down, no supports. c1/c2 have the quarter cutout around the funnel stud (screw hole r 104), c3/c4 go under the capped stud (hole r 102). Layout: c1..c4, r1 back / r2 front. All 8 printed by 2026-11-21; roof + studs assembled. | 8 |
| P23 | v1 | done | PLA | Roof clips: 24 C3 (screw to the top rails, hold the tile ribs) + 12 H (join the roof seams). Print in your calibrated Inland PLA: the slot fit is PLA-sized - printed 2026-11-22 | 1 |
| P24 | v3 | vac | PETG/PLA/PLAyellow | Vacuum canister (accessory, docks on the left stud): 8 files, no supports. PRINT FILE 1 (2 PLA coupons) FIRST and report: does the ring slide onto the stud and turn (chamfered end = 0.15 fit, other end = 0.10), and how many mm does your hose cuff go into the small socket. Yellow PLA: 2 lower shell, 3 lid, 4 hose port (+ pivot cap). Black PETG: 5 funnel, 6 gate disc + 2 eyes (glue the eyes into their pockets above the mouth), 7 screen, 8 mouthpiece + handle + 2 wand elbows. The hose parts (4, 8) are sized for a 57.0-58.5 mm cuff until the coupon result is in | 8 |

## Change log

- **P13** v2 2026-11-15: only the parts not printed yet (camera bridge and landing ramp are done); cradle B, motor wall, slider post, LED holders moved to P19
- **P13** v3 2026-11-15: 0.5 mm teardrop tops on cradle A sideways holes
- **P16** v2 2026-11-15: only the parts not printed yet (outlet plate, NEMA bracket, vib caps, gate slider, servo link are done)
- **P18** v2 2026-11-14: PETG insert holes 4.4 on the electronics trays; scanner plate rev 2 (hinge tabs were floating 0.9 mm off the plate, feet now flare so no supports, screwdriver holes over the foot screws). Reprint the scanner plate if you printed v1; v1 trays OK if inserts go in with a push
- **P18** v3 2026-11-15: only the parts not printed yet (scanner plate v2 and both trapdoors are done)
- **P18** v4 2026-11-16: no supports: funnel has a 45 deg gusset under its flange (prints mouth-down; also removes a 4 mm lip that was inside the bore), electronics tray legs are separate parts (16 x 225_tray_leg, the #6 goes through tray + leg), XIAO camera mount dropped (Pi + Logitech webcam); USB clip 3 dropped (stale part from an old layout, it hit a frame post). Throw away v3 files
- **P18** v5 2026-11-16: trays fitted to the real parts: slim PSU S-120-12 (142 x 40 x 28) on rails, screwed by its 2 end tabs into M3 inserts, AC-end cover resized; trays 1b and 2 (and the free part of 1a) are a universal 10 mm M3 hole grid for boards on nylon standoffs, no guessed board pads. Throw away v4
- **P19** v2 2026-11-15: 0.5 mm teardrop tops on the sideways holes (cradle B, motor wall). If you already printed v1, it is fine: just clean the hole tops
- **P20** v2 2026-11-16: split in 2 plates and spaced out: v1 in one plate sliced to 23 h / 576 g with 134 g of support (some trapped inside the beam) and a path conflict between the tall segments. Throw away v1
- **P20** v3 2026-11-16: fixed parts that were not one piece: beam plugs (the 20 mm joint plug floated 1 mm off segments 1-2, Bambu "empty layer"), carriage endstop flag, cup +x stub axle, idler slider arms, idler tension: block moved outboard of the beam post (it hit post L) and the screw now goes into a lug on the slider; cup stubs now run through the tower 625s (pockets from the inner face). Segments stand plug-up. 18 scoop poses clash-free. Throw away v1/v2
- **P24** v2 2026-11-18: yellow parts (lower shell, lid, hose port) are PLA now (BJ): insert holes 4.3, stud socket and lid joint at 0.15 per side, coupons in PLA with a 0.15 / 0.10 stepped ring; wand tubes dropped (the vac's own wands fit, old file 9); 2 black eyes added (file 6) with pockets in the lower shell; other black parts unchanged except 0.05 mm on the funnel rim and disc recess. Nothing was printed from v1: throw v1 away
- **P24** 2026-11-22: file 3 (lid) printed, 242.9 g, 6 h 9 m (in done/)
- **P24** 2026-11-23: file 5 (funnel) printed, 309 g slicer, 7 h 39 m (in done/)
- **P24** v3 2026-11-23: only file 2 (lower shell) changed. Coupon: the 0.15 ring was tight on the stud but fit (BJ), so the skirt bore over the stud is 0.25 per side now (216.5). The bore above the stud rim, funnel seat, gate disc and lid joint are unchanged, so the v2 lid and funnel you printed still fit. Files 1, 4, 6, 7, 8 are the same parts as v2
- **P24** 2026-11-23: file 1 (coupons) printed; ring result above, hose result still to come (in done/)
- **P24** 2026-11-24: file 2 (lower shell, v3) printed (in done/)

## Filament used

**Total: 4789.19 g** (PETG 2521.29 g, PLA 1257 g, PLAred 764 g, PLAyellow 242.9 g, TPU 4 g) over 123 h of printing

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
| 2026-11-15 01:20 | p8-p12_plate_11 | 11.1 | P15 | v1 | PETG | 342 (estimate) | done | 47b drum barrel (3 walls; finished 2026-11-15 ~12:26) |
| 2026-11-15 ~12:40 | p8-p12 plate 3 (P16 v2 parts) | 1.75 | P16 | v2 | PETG | 50.29 (slicer) | done | 48 rear guard, 54 drive hub, 59 door link x2, 60 servo arm, 62 vib saddle x2 (marked done by BJ 2026-11-15; 1 h 45 min) |
| 2026-11-15 14:39 | P19_v2+P13_v3_PETG_combined | 9.87 | P19+P13 | v2 | PETG | 290 (slicer) | done | 205 cradle A, 205 cradle B, 206 motor wall, 212 slider post, 216 LED holders A/B, 217 webcam mount, 218 APDS mount, 228 cable spool, 226 USB clips 1-2 (finished ~00:30 Nov 16) |
| 2026-11-16 00:45 | P20_v3_PETG_scoop_plate1_beam | 12.0 | P20 | v3 | PETG | 350 (slicer) | done | 180 beam segments 1-3 (3 walls, 15% gyroid, 0.2 mm, supports off, slow/quiet speed; finished 2026-11-16 ~12:45 pm) |
| 2026-11-17 by 05:57 | P20_v3_PETG_scoop_plate2_carriage_cup_brackets | 0 | P20 | v3 | PETG | 163 (estimate (CAD x 0.75, Bambu ran ~25-35 % under CAD)) | done | 181 carriage, 182 cup, 184 motor bracket, 185 idler channel, 186 idler slider, 187 idler wheel, 188 endstop mount, 189 pushrod, 190 servo bracket (grams/time not sent yet) |
| 2026-11-17 by 15:05 | P18_v5_PETG_funnel_and_electronics_plate2 | 0 | P18 | v5 | PETG | 131 (estimate (CAD x 0.75, Bambu ran ~25-35 % under CAD)) | done | 220 drop funnel, 225 tray 1b, 227 PSU cover, 225 tray legs x16 (grams/time not sent yet) |
| 2026-11-17 by 22:19 | P18_v5_PETG_funnel_and_electronics_plate1 | 0 | P18 | v5 | PETG | 97 (estimate (CAD x 0.75, Bambu ran ~25-35 % under CAD)) | done | 225 tray 1a PSU, 225 tray 2 Pi (grams/time not sent yet) |
| 2026-11-19 by 20:36 | P22_v1_PLAred_roof_tile_c1_r1 x8 | 5.8 | P22 | v1 | PLAred | 407 (estimate (8 x 67.8 g CAD x 0.75)) | done | 114 roof tile c1_r1 x8 (1 used, 7 spares) (printed the same tile file 8 times; each P22 file is a different roof spot, so 7 tiles still to print. grams/time not sent yet) |
| 2026-11-20 by 22:09 | P22_v1_PLAred_roof_tile_c2_r1 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c2_r1 (matched from BJ's print-history thumbnails; Bambu grams not sent) |
| 2026-11-20 by 22:09 | P22_v1_PLAred_roof_tile_c2_r2 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c2_r2 (matched from BJ's print-history thumbnails; Bambu grams not sent) |
| 2026-11-20 by 22:09 | P22_v1_PLAred_roof_tile_c3_r1 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c3_r1 (matched from BJ's print-history thumbnails; Bambu grams not sent) |
| 2026-11-20 by 22:09 | P22_v1_PLAred_roof_tile_c3_r2 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c3_r2 (matched from BJ's print-history thumbnails; Bambu grams not sent) |
| 2026-11-21 by 17:46 | P22_v1_PLAred_roof_tile_c1_r2 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c1_r2 (BJ: studs and roof tiles assembled; Bambu grams not sent) |
| 2026-11-21 by 17:46 | P22_v1_PLAred_roof_tile_c4_r1 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c4_r1 (BJ: studs and roof tiles assembled; Bambu grams not sent) |
| 2026-11-21 by 17:46 | P22_v1_PLAred_roof_tile_c4_r2 | 0.73 | P22 | v1 | PLAred | 51 (estimate (67.8 g CAD x 0.75)) | done | 114 roof tile c4_r2 (BJ: studs and roof tiles assembled; Bambu grams not sent) |
| 2026-11-22 by 14:53 | P23_v1_PLA_roof_clips | 1.5 | P23 | v1 | PLA | 75 (estimate) | done | 24 x 123 clip C3 roof, 12 x 122 clip H (roof) (Bambu grams/time not sent) |
| 2026-11-22 15:00 | P24_v2_PLAyellow_vac_3_lid | 6.15 | P24 | v2 | PLAyellow | 242.9 (slicer) | done | 255 vac lid (Inland PLA yellow (AMS slot 6), 6h9m, 636 layers; finished by 2026-11-22 22:31) |
| 2026-11-22 22:35 | P24_v2_PETG_vac_5_black_funnel | 7.65 | P24 | v2 | PETG | 309 (slicer) | done | 251 vac funnel (black PETG, 7h39m; done by 2026-11-23 18:40) |
| 2026-11-23 19:00 | P24_v2_PLA_vac_1_coupons_PRINT_FIRST | 1.4 | P24 | v2 | PLA | 59 (CAD estimate) | done | 265 vac coupon socket ring, 266 vac coupon hose socket (ring at 0.15 tight on the stud but fits; hose depth not reported yet) |
| 2026-11-24 06:46 | P24_v3_PLAyellow_vac_2_shell_lower | 12.2 | P24 | v3 | PLA | 551 (CAD estimate) | done | 250 vac shell lower (yellow PLA; done by 2026-11-24 14:34; slicer time and grams not reported (CAD estimate)) |

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

