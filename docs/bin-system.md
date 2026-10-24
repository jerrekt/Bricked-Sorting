# Bin system and data contract

Shared by the website, Kratos (classification) and the Indicate controller. The table lives in
`web/data/bins.json`; change it there and every part reads the same thing.

## Bin codes
`floor-slot`, for example `1-3`.
- Floor 1 = bottom row = regular rectangular bricks (Brick N x M).
- Floor 2 = top row = everything else (plates, tiles, slopes, round and modified bricks, wheels...).
- Slots 1-7 = color groups, left to right. Slot 8 = unknown color for that floor.

| Slot | Group | Merged shades (10696) |
|---|---|---|
| 1 | Red / Orange | Red, Dark Red, Orange, Dark Orange, Bright Light Orange |
| 2 | Yellow | Yellow, Bright Light Yellow |
| 3 | Green / Lime | Green, Bright Green, Dark Green, Lime, Yellowish Green |
| 4 | Blue / Azure | Blue, Dark Blue, Dark Azure, Medium Azure, Light Aqua |
| 5 | Pink / Purple | Bright Pink, Dark Pink, Magenta, Dark Purple, Lavender, Medium Lavender |
| 6 | Black / Dark Gray | Black, Dark Bluish Gray |
| 7 | White / Light Gray | White, Light Bluish Gray |
| 8 | Unknown | Tan, browns, all transparent colors, anything the camera can't place |

Why these groups: they are the biggest color groups in one 10696 box (BrickLink inventory, 484 pieces).
Per box: floor 2 gets 335 pieces, floor 1 gets 149.

## Messages (planned, not built)
Identify -> Indicate, one per piece:
```json
{"code": "1-3", "floor": 1, "slot": 3, "category": "brick", "group": "green", "confidence": 0.82, "ts": "2026-10-24T18:00:00Z"}
```
Indicate -> Kratos, bin limit switch:
```json
{"code": "1-3", "event": "opened", "ts": "2026-10-24T18:05:00Z"}
```
Indicate maps `floor` to Z height and `slot` to yaw angle using `physical` in bins.json (filled in once the hardware is measured).

## Inventory rules
- Count Everything sets the collection total. Add New LEGO adds a box to it. Normal sorting never changes it.
- Find What's Missing re-sorts only bins flagged as opened, plus pieces found, then compares every bin to the total.
- A shortfall in a color bin next to a surplus in that floor's unknown bin is shown as a likely misread, not a loss.
