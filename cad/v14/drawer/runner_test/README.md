# V14 drawer runner test (print first)

Same runner the drawers use (3 per drawer). Single stage: a fixed rail (150) and a moving bar (151). Both run back into the center-spine strip so 96 mm stay engaged at the full 220 mm pull.

## Print (PETG, BJ's profile, no supports)
| File | Qty | Bed | Notes |
|---|---|---|---|
| `150c_coupon_rail_60_PRINT_1.stl` + `151c_coupon_bar_20/30/40_PRINT_1.stl` | 1 each | small | **print first** (~1 h). Bars have 2 / 3 / 4 notches = 0.20 / 0.30 / 0.40 mm per side |
| `150_runner_rail_PRINT_2.stl` | 2 | 246 x 246 (sits 45 deg) | base down |
| `151_runner_bar_PRINT_2.stl` | 2 | 243 x 243 (sits 45 deg) | flange down |

Coupon: slide each bar in from the end. Pick the tightest one that slides with no wobble and no catch. The full parts are drawn at 0.30; if you pick 0.20 or 0.40 tell me and I re-export before you print the long ones.

## Assemble
1. 5 M3 heat-set inserts into each bar flange (from the flange face).
2. Slide the bar into the rail **from the rail's plain end** (the end where the groove is open). The bar's tooth rides in the groove; it stops hard at 220 mm and clicks over a detent when closed.
3. Optional: PTFE tape on the rail floor.

## Killer test
- Screw both rails parallel to a board, ~400 mm apart, through the 7 holes (M3 or #4 wood screws, heads sit in the counterbores).
- Screw a plank across the two bar flanges (M3 x 8 into the inserts).
- Load 6-8 kg centered about 120 mm past the rails' front ends (where a drawer's load sits at full pull).
- Pull to the stop. Measure droop at the bar front end with calipers or a ruler vs unloaded.
- Pass: < 2-3 mm droop, no binding, 50-100 full cycles, the stop and detent still work.
- Report: droop, pull force feel, any whitening or wear.
