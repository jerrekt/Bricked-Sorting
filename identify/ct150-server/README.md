# CT 150 inference server (backup)

Read-only snapshot of the code running on CT 150 (Kratos) as of 2026-10-24. Not wired into any deploy; the live copies are in `/opt/bricked-sorting` on CT 150.

| File here | Lives on CT 150 | What it does |
|---|---|---|
| `brick_server.py` | `/opt/bricked-sorting/brick_server.py` | Flask server on port 5000. `POST /identify` sends the camera image to the Brickognize API, picks a bin, saves the scan. Also the 16-bin dashboard API and a relay of the Pi camera stream. |
| `classify.py` | `/opt/bricked-sorting/classify.py` | Maps the part name and color name to a shape and one of 8 color families, giving one of 16 bins. |
| `static/bins.html` | `/opt/bricked-sorting/static/bins.html` | The 16-bin dashboard page served at `/`. Its bin images (`static/assets/*.webp`) are not copied. |
| `bricked-server.service` | `/etc/systemd/system/bricked-server.service` | systemd unit that runs the server as root from `/opt/bricked-sorting`'s venv. |

Not copied: `sort_history.db`, `scanned_images/`, `venv/`, the `*.backup-*` files, `static/assets/`.

The Pi camera, LED and sensor code is not here yet. It lives on the Pi and has not been backed up.

Real addresses were replaced with placeholders: `<PI_TAILNET_IP>` (the Pi camera, port 8001), `<CT150_TAILNET_IP>` and `<CT150_LAN_IP>` (this server). Look the real values up in Tailscale. As committed, `brick_server.py` will not reach the camera until `CAMERA_STREAM_URL` and `CAMERA_SNAPSHOT_URL` are set.