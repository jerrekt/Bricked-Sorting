# Pi code (backup)

Read-only snapshot taken 2026-10-24 from the Raspberry Pi 5 (Raspberry Pi OS, Python 3.13), user `ethan`, home `/home/ethan`. Not deployed from here.

| File here | Lives on the Pi | What it does |
|---|---|---|
| `brick_server.py` | `/home/ethan/brick_server.py` | Older (Oct 1) Pi-side Flask server on port 5000 with `POST /identify` that calls Brickognize directly. Run by `brick-server.service`. |
| `systemd/brick-server.service` | `/etc/systemd/system/` | Runs `brick_server.py` as `ethan`, restarts on exit. Enabled. |
| `systemd/bricked-dashboard.service` | `/etc/systemd/system/` | Points at `/home/ethan/dashboard_server.py`, which does not exist. Not enabled. Stale. |
| `systemd/camera-stream.service` | `/home/ethan/.config/systemd/user/` | User service that runs `camera_service.py` (USB camera MJPEG stream on port 8001). Enabled, but the user has no linger, so it starts only with a login session. |

## Missing: `camera_service.py`
The source of the camera service is not in this folder because it **no longer exists on the Pi**; the service is running from memory. Only compiled bytecode survives, kept privately. If you have a copy of `camera_service.py`, add it here.

What the bytecode shows: a Flask app on port 8001 (`/stream` MJPEG, `/health`) that sets camera auto exposure and white balance, drives an RGB LED, posts images to `/identify` on the inference server, and sends updates and heartbeats to port 8080 there. This is read from strings, not confirmed line by line.

## Not found
No code for the APDS-9960 color sensor or the NeoPixel strip was found on the Pi, although the libraries are installed in its virtualenv.