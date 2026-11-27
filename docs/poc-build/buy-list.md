# POC buy list and parts check (2026-11-26)

POC demo: Wed Dec 2. Built from the CAD parts lists (`cad-v14-all:cad/v14/integration/buy_list.md`, the deck and scoop `parts.json`) checked against what is on file as owned (Mnemosyne `inventory/parts-owned.md`).

## Buy

| Item | Qty | For | Notes |
|---|---|---|---|
| 370 vibration motor, **6 V**, ~6000 rpm, one eccentric weight | 3 (2 + spare) | V1, V2 trays | Body must be **~24 mm** across (saddle 62 is drawn for 24 mm). Runs from the 5 V buck. Amazon examples: [B0D5LL75WR](https://www.amazon.com/Fan-Shaped-Vibration-Vibrator-6V12V24V-Electric/dp/B0D5LL75WR), [B0D73WDXNK](https://www.amazon.com/Eccentric-Vibration-Vibrating-Fan-Shaped-Precision/dp/B0D73WDXNK). Check the listing's drawing for the body size before buying. |
| Servo extension lead, 3-wire | 1 m | scoop tilt servo | |
| DRV8833 board | 1 | drives V1/V2 | **Only if not owned.** On file: 2 MOSFET trigger-switch modules, which can drive the two motors instead (one each). |

## Check you have (not on file as owned)

| Item | Qty needed | For |
|---|---|---|
| 625ZZ bearings | 16 | drum rollers 8, scoop 8 |
| GT2 6 mm belt | ~1.3 m | scoop |
| GT2 20T pulley, 5 mm bore + idler | 1 + 1 | scoop |
| M5 nyloc nuts | 11 | drum axles 4, scoop 7 |
| M5 × 25 | 5 | scoop (kit on file stops at 20 mm; M5 × 30 may work, check each spot) |
| M3 × 30 | 1 | scoop |
| NEMA17 | **2** | drum + scoop (only one is on file) |
| TMC2209 | 2 | drum + scoop steppers (DRV8825s on file would also work) |
| KW11-3Z limit switch | 1 | scoop home |
| USB webcam (Logitech) | 1 | Identify |
| APDS-9960 (GY-9960) | 1 | colour sensor |
| LED bar 70 mm | 2 | scanner lights |
| Slim 12 V 10 A PSU (142 × 40 × 28) | 1 | electronics tray 1a |
| IEC C14 fused + switched inlet | 1 | back wall tile |
| PTFE film or wax | | drum thrust ring |

## On file as owned (no need to buy)

#6 × 3/4 in wood screws (400), #6 × 1 1/4, #9 × 2 1/2; M5 × 30 (50 sets), M5 × 50 (30 sets); M3 flat head kit 8–25 mm; M3 socket head assortment; M2–M5 kit 8–20 mm; M3 and M5 heat-set inserts; 3 × MG996R; 5 × DRV8825; 12 V 20 A PSU; DROK 12 V → 5 V bucks; XT30/60/90; limit switches; one NEMA17.

## After it arrives

Tell Claude what came in so the inventory note is updated. Vibration motors: test one tray first (V1 with its 2 springs) before mounting the second.
