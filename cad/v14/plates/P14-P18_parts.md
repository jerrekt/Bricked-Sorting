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
| 210_scanner_plate | Platform where each brick stops to be scanned; sits on 4 standoffs on the deck. Small tree support (~15 cm²) |
| 214_trapdoor_A, B | Trapdoors in the scanner plate; open to drop the brick after the scan |
| 220_drop_funnel | Under the trapdoors; guides the brick down into the scoop cup. Small tree support |
| 217_xiao_sense_camera_mount | Holds the XIAO ESP32-S3 Sense camera over the scanner |
| 225_electronics_tray_1a_psu | Tray for the power supply (M3 inserts) |
| 225_electronics_tray_1b_power_io | Tray for the power input / switch / fuse side (M3 inserts) |
| 225_electronics_tray_2_pi | Tray for the Raspberry Pi (M3 inserts) |
| 227_psu_terminal_cover | Finger guard over the PSU's AC screw terminals (2 M3 inserts) |
| 226_usb_cable_clip_3 | Clip that routes the USB cable along the deck |
