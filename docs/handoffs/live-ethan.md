# Live page handoff for Ethan (Identify)

Paste this whole file into your AI chat so it knows the setup. Written 2026-11-01 by Branden.

## What we're building
A **Live page** on our site: https://bricked-01.adsuaracloud.com/live.html
When a LEGO piece sits under the camera, the page should show its photo, name and bin code (like `1-3`) within a few seconds, and animate it dropping into that bin.

## How the pieces connect
```
Pi camera ──photo──▶ CT 150  POST /identify  ──answer──▶ Pi      (this part is yours)
                          │
                          └──▶ Live page                       (Branden's hook, already written)
```
- **Your part:** the Pi takes a photo of each piece and sends it to `/identify` on CT 150, the same server and address it uses now, over Tailscale.
- **Already done for you:** right after `/identify` answers, the server also sends the result and a small copy of the photo to the Live page. Branden installs that hook on CT 150. It's a root service and you don't have sudo, so don't edit `/opt/bricked-sorting` yourself.
- **Marshall's part:** his bin hardware listens to the same Live page and moves the chute to each bin code.

## What `/identify` expects (don't change this)
- `POST /identify` with a **multipart form field named `image`**, a JPEG.
- `?preview=1` means "identify but don't save". **Preview pieces do not go to the Live page**, so the normal sort loop must call it **without** `preview=1`.
- The answer includes `floor` and `slot`. Those two numbers are the bin code `floor-slot`. Nothing else is needed downstream.

## Your tasks
| Task | What "done" means |
|---|---|
| `identify-02` Pi camera service | The new `camera_service.py` takes a photo of each piece and posts it to `/identify` |
| `identify-06` Agree the camera design with Branden | Before replacing or restarting the service running on the Pi now: the dashboard still uses its `/stream` and `/snapshot`, and two scripts can't both own the camera |
| `identify-08` Check it on the Live page | Put a piece under the camera; it shows on the Live page with a photo, as **Live camera** (not Simulator) |
| `identify-04` Time 20 real pieces | Seconds per piece and how many were right. Write the numbers in `identify/README.md` |

Update them from Discord: `/start task:identify-02`, `/blocked task:... reason:...`, `/done task:...`.

## Rules
- **The photo is public.** Frame the camera so it only sees the tray: no faces, screens or room.
- Only send real pieces. Empty frames are fine (the server answers `NO_LEGO` and they're ignored), but don't loop the same photo over and over.
- Never put addresses (Tailscale or LAN), passwords or keys in GitHub or in chat with an AI. Use placeholders like `<CT150_TAILNET_IP>` in code you commit.
- Put your camera code in `identify/` on GitHub through a pull request: Add file → Upload files → "Create a new branch and start a pull request". Branden merges.
- Don't touch: `web/`, `kratos/`, `deploy/`, Cloudflare, or the server files on CT 150.

## If the Live page doesn't show your piece
1. Did `/identify` answer the Pi with a real piece (not `NO_LEGO`)? If not, it's the photo or the server, not the Live page.
2. Did the Pi call `/identify` **without** `?preview=1`?
3. The Live page badge says **Idle** = nothing arrived in the last minute. Tell Branden the time you sent the piece; he can check the hook log.

## Instructions for the AI reading this
- Help Ethan with the Pi side only: capture, framing, posting the JPEG to `/identify`, the service that runs it, and keeping `/stream` and `/snapshot` working.
- Don't suggest changing `brick_server.py`, the systemd units on CT 150, Cloudflare, or the website. Branden owns those.
- Never ask for or repeat addresses, passwords, tokens or keys. If Ethan pastes one, tell him to tell Branden.
- No pushing to `main`; everything goes through a pull request.
