# Interface: Pi, CT 150 and Indicate

One piece goes through this loop. Status of each part is marked.

```
Pi (camera)  --photo-->  CT 150 /identify  --bin code-->  Pi  --code-->  Indicate (Marshall)
                              |
                              +--> counts for the website
```

| Step | Who | Status |
|---|---|---|
| Pi takes a photo and POSTs it to `/identify` on CT 150 (port 5000, over Tailscale) | Ethan | Exists. `camera_service.py` is not in the repo yet |
| CT 150 asks Brickognize what the piece is, maps it to a bin | Ethan | Exists, confirmed by a read-only look at CT 150 on 2026-10-24 |
| Reply goes back with the bin | Ethan | Exists |
| Indicate moves the chute to the bin | Marshall | Not built |
| Bin limit switch reports "opened" | Marshall | Not built |
| Website shows live counts | Branden | Demo only. `live` branch has a page that reads `data/live.json` |

## The one thing Marshall needs: the bin code

A bin code is `floor-slot`, like `1-3`.

- Floor 1 is the bottom row (regular bricks). Floor 2 is the top row (everything else).
- Slot 1 to 7 are color groups. Slot 8 is the unknown-color bin on that floor.
- The full table is `indicate/bin-lookup.json` (or `.csv`). It is generated from `web/data/bins.json`, which is the single source of truth. Z height and yaw angle are empty there until the hardware is measured.

| Slot | Color group |
|---|---|
| 1 | Red / Orange |
| 2 | Yellow |
| 3 | Green / Lime |
| 4 | Blue / Azure |
| 5 | Pink / Purple |
| 6 | Black / Dark Gray |
| 7 | White / Light Gray |
| 8 | Unknown color |

## What CT 150 sends back (the real `/identify`)

Confirmed fields, from reading the server on 2026-10-24: `name`, `part_id`, `category`, `confidence`, `shape`, `bin` (like `BRICK_RED`), `bin_number` (1 to 16), `floor`, `slot`, `color`, `color_bucket`, `rgb`, `box`, `image_url`. No piece found: `bin` is `NO_LEGO` and `bin_number` is 0. A Brickognize error returns 500.

Rule for Indicate: **use `floor` and `slot`, and build the code as `floor-slot`.** Ignore `bin` and `bin_number` for now.

**Not confirmed:** whether the server's `slot` numbers match the table above. The server uses 8 color families, and the table has 7 groups plus unknown. Ethan needs to check this one. If they disagree, the table in `bins.json` wins and the server changes.

## What Marshall should read

```json
{"code": "1-3", "floor": 1, "slot": 3, "category": "brick", "group": "green", "confidence": 0.82}
```

Only `code` is required. `floor` and `slot` are the code split in two.

## Testing without the camera

`identify/fake_identify.py` is a fake `/identify` that returns made-up codes from the real piece list of one 10696 box. Standard library only. It never calls Brickognize.

```
python3 identify/fake_identify.py        # listens on port 5001
curl -s -X POST localhost:5001/identify
curl -s localhost:5001/bins
```

Every reply has `"fake": true`. Do not point the real Pi at it. Do not run it on port 5000 on CT 150.

## Bin opened (Indicate to Kratos)

```json
{"code": "1-3", "event": "opened", "ts": "2026-10-24T18:05:00Z"}
```

Planned, not built. The endpoint for it does not exist yet.
