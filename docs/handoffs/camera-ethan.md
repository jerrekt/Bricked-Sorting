# Camera handoff for Ethan (Identify): get real pieces onto the Live page

Paste this whole file into your AI chat. Written 2026-11-07 by Branden.

## Where things stand (Nov 7)
| Piece | Status |
|---|---|
| CT 150 `/identify` (Brickognize) | Working |
| Hook from `/identify` to the Live page | **Installed today.** Every non-preview piece `/identify` saves now shows on https://bricked-01.adsuaracloud.com/live.html with its photo |
| Live page | Shows the photo, name, part, match %, color and the bin; refresh once if an old tab is open |
| Your bin switches (`pi_bin_switches.py`) | Working: the Live page shows "Bin switches: reporting" |
| **Pi camera loop** | **Your job (this file)** |

## Goal
The Pi notices when a new piece lands on the tray, takes **one** photo of it, sends it to `/identify`, and moves on. The piece then appears on the Live page within a few seconds, tagged **camera**.

## How to build it (`identify/camera_service.py`)
1. **Don't open the camera a second time.** The service already on the Pi owns the camera and serves `/stream` and `/snapshot` (the CT 150 dashboard uses them). Read frames from that service locally, e.g. `GET http://127.0.0.1:<PORT>/snapshot`, instead of opening the camera in a new script. Two programs can't both own the camera.
2. **Detect a new piece, then send once:**
   - Grab a frame about every 0.5 s.
   - Compare the tray area with an **empty-tray reference** (mean absolute difference over a crop of just the tray).
   - Difference above a threshold = a piece is there. Wait until two frames in a row look the same (the piece stopped moving), then send that frame **once**.
   - Don't send again until the tray goes back to empty. This stops the same photo being sent over and over.
   - Re-take the empty reference when the tray has been empty for a while (lighting drifts).
3. **Send it:** `POST <IDENTIFY_URL>` (the CT 150 `/identify`, **without** `?preview=1`) with a multipart field named **`image`** holding the JPEG. Timeout 30 s.
4. **Read the answer:** `name`, `part_id`, `confidence` (percent), `color`, `bin`, `floor`, `slot`.
   - `bin == "NO_LEGO"` → nothing found; ignore it and wait for the tray to clear.
   - **`floor` and `slot` from `/identify` count from 0** (floor 0 = bricks, slot 0 = first bin). The Live page shows them from 1 (bin `1-1` = floor 0, slot 0). The hook converts for the Live page; if your code uses them (LEDs, a display), add 1 the same way.
5. **Log one line per piece:** time, name, bin, confidence, and seconds from "piece settled" to "answer received". That's what task `identify-04` needs.
6. **Settings from environment variables, not the code:** `IDENTIFY_URL`, `SNAPSHOT_URL`, the tray crop, thresholds. The URL contains a private address, so it never goes in GitHub. Keep it in a file only you can read on the Pi (`~/.bricked_camera.env`, mode 600) and load it with `EnvironmentFile=` in the service. Ask Branden for a paste-and-run setup script if you need one; nobody should have to edit files to paste addresses or keys.
7. **Run it as a service** (systemd, `Restart=always`) so it starts with the Pi.

## Check it (tasks)
- `identify-02` **Pi camera service:** `camera_service.py` runs as a service and sends one photo per piece.
- `identify-08` **Live page:** put a piece on the tray; within a few seconds it shows on the Live page with your photo, tagged **camera**. Screenshot it for Branden.
- `identify-04` **Time 20 real pieces:** seconds per piece and how many were right. Write the numbers in `identify/README.md`.
Update them from Discord: `/start task:identify-02`, `/done task:...`.

## If the Live page doesn't show your piece
1. Did `/identify` answer with a real piece (not `NO_LEGO`)? If not, it's the photo (framing, light, focus), not the Live page.
2. Did you call it **without** `?preview=1`? Preview pieces never go to the Live page.
3. Badge says **Idle** = nothing arrived in the last minute. Tell Branden the time you sent the piece; he can read the hook log on CT 150.

## Rules
- **The photo is public.** Frame the camera so it only sees the tray: no faces, screens or room.
- Never put addresses (Tailscale or LAN), passwords or keys in GitHub or in chat with an AI. Use placeholders like `<CT150_TAILNET_IP>` in code you commit.
- Code goes in `identify/` through a pull request (GitHub web: Add file → Upload files → "Create a new branch and start a pull request"). Branden merges after a review.
- Don't touch: `web/`, `kratos/`, `deploy/`, Cloudflare, or the server files on CT 150.

## Instructions for the AI reading this
- Help Ethan with the Pi side only: reading frames from the existing camera service, piece detection, posting the JPEG to `/identify`, logging, and the systemd service.
- Write `identify/camera_service.py` plus a short `identify/README.md` (how to install, the env variables, how to run the timing test). Python 3, standard library plus `requests`, `numpy` and `Pillow` (or OpenCV if it's already installed).
- Don't suggest changing `brick_server.py`, the CT 150 systemd units, Cloudflare or the website. Branden owns those.
- Never ask for or repeat addresses, passwords, tokens or keys. If Ethan pastes one, tell him to tell Branden so it can be changed.
- No pushing to `main`; everything goes through a pull request.
