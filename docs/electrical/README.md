# Electrical

Wiring, power and switch notes for Bricked Sorting. V14 block diagram, power budget, pin maps and harness list follow in later PRs.

## Bin switches (proof of concept, on the Pi)
One switch per bin. When a bin is lifted, its count can't be trusted any more; the Live page says so, and the user re-pours only that bin to recount.

**Wiring, every switch the same:** C → GND, NO → GPIO, internal pull-up on.

| Bin state | Switch | Pin |
|---|---|---|
| Seated | pressed | LOW |
| Lifted (open) | released | HIGH |
| Wire broken | open | HIGH, reads as open (fails safe) |

Don't use NC: a broken wire would then read as "bin seated".

Current pins (Ethan's Pi): GPIO 23, 24, 25, 16, 20. Which bin each one is under goes in `SWITCHES` in `pi_bin_switches.py`.

## Pi → Live service
`pi_bin_switches.py` posts the full list of open bins on every change and every 20 s:

```
POST /live/bins
Authorization: Bearer <BRICKED_BINS_TOKEN>
{"open": ["1-3"], "drawers_open": []}
```

- Codes: `1-1` to `2-8` now; `F1`–`F8`, `B1`–`B8` accepted for V14.
- `drawers_open`: `front` / `back` (V14 drawer switches; empty for now).
- Own key, separate from the CT 150 camera key. No update for 90 s = the page shows "Bin switches: not reporting" and ignores open bins.
- A bin that opens and closes again is marked **Recount** until someone presses Reset counts.

Check the page without the Pi: `live.html?test=bins` cycles fake switch states in that browser only.

## V14 plan (agreed 2026-11-07)
- Bins: a reed switch in the drawer floor under each bin, a 6 × 2 mm magnet in each bin's bottom. Same wiring rule (seated = LOW).
- One MCP23017 on each drawer (8 bins each), so only 3V3, GND, SDA, SCL ride each drawer.
- Two drawer-closed switches stay as the interlock: the scoop doesn't move while a drawer is out.
- The Pi stays the brain.
