# Interface: camera → server → Live page → bins

```
Pi camera ──photo──▶ CT 150 /identify ──result──▶ Pi (unchanged, over Tailscale)
                           │
                           └─result + small photo──▶ Live service (bricked-api) ──▶ Live page
                                                                │
Live page "Start simulator" ──fake pieces──────────────────────┘
                                                                │
                                         Marshall's laptop bridge ◀─ bin codes ─┘
                                                │ USB serial "1-3"
                                             Arduino ──▶ chute ──▶ answers "OK 1-3"
```

## Bin code
`floor-slot`, like `1-3`. Floor 1 bottom (bricks), floor 2 top (everything else). Slots 1-7 color groups, slot 8 unknown color. Table: `web/data/bins.json` (source), `indicate/bin-lookup.csv` (copy for Indicate).

## What `/identify` returns (CT 150, read 2026-10-24)
`name`, `part_id`, `category`, `confidence` (percent), `shape`, `bin`, `bin_number` (1-16), `floor`, `slot`, `color`, `color_bucket`, `rgb`, `color_confidence`, `box`, `image_url`. No piece: `bin` = `NO_LEGO`, `bin_number` 0. The Live page and the bins use only `floor` and `slot`.

## Live service (https://bricked-api.adsuaracloud.com)
| Route | Who | What |
|---|---|---|
| `POST /live/event` | CT 150 only (bearer key) | One identified piece: the `/identify` result, optional `image_b64` JPEG |
| `GET /live/state` | anyone | Mode (`live`, `sim`, `idle`), last 30 pieces, counts per bin |
| `GET /live/events?after=ID&wait=25` | Live page, bridge | New pieces after ID; waits up to 25 s for one |
| `GET /live/img/ID.jpg` | Live page | The small photo of a camera piece |
| `POST /live/control` | Live page buttons (team password) | `start` / `stop` the simulator, `reset` counts |

Each piece: `{id, ts, source: "live"|"sim", code, floor, slot, name, color, confidence (0-1), has_image, hex}`.

## Bridge ↔ Arduino (USB serial, 115200)
Bridge sends `1-3\n`. Arduino answers `OK 1-3` when the chute is there, or `ERR reason`. One command at a time; the bridge waits up to 10 s. `PING` → `PONG`, `HOME` → `OK HOME`. Code: `indicate/bridge/bin_bridge.py`, `indicate/arduino/bin_receiver/`.

## Not built yet
Bin limit switch "opened" events back to the server.
