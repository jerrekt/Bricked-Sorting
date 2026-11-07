#!/usr/bin/env python3
"""Bricked Sorting: the Pi's camera server (replaces the lost camera_service.py stream).

It is the only program that opens the USB camera. Everything else reads from it:
  GET /stream    MJPEG video (the CT 150 dashboard relays this)
  GET /snapshot  one JPEG of the newest frame (identify/camera_service.py polls this)
  add ?public=1  640 px wide, 5 frames/s at most: what the public website gets
  GET /health    {"ok": true, "age_s": seconds since the last frame}

Settings come from environment variables (all optional):
  CAMERA_DEVICE=0 (or /dev/video0)  CAMERA_WIDTH=1280  CAMERA_HEIGHT=720  CAMERA_FPS=15
  JPEG_QUALITY=85  STREAM_PORT=8001
  PUBLIC_WIDTH=640 PUBLIC_FPS=5   size and rate for ?public=1 (what the website's /camera-stream uses)
  CAMERA_LOCK=1    after 3 s of auto, freeze focus, exposure and white balance where they
                   landed (steady colors and no false "piece" from auto changes). 0 = leave auto.
  CAMERA_CONTROLS  optional fixed v4l2 settings applied after that, e.g.
                   "focus_absolute=30,exposure_time_absolute=250,white_balance_temperature=4000"
"""
import json
import logging
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

DEVICE = os.environ.get("CAMERA_DEVICE", "0")
WIDTH = int(os.environ.get("CAMERA_WIDTH", "1280"))
HEIGHT = int(os.environ.get("CAMERA_HEIGHT", "720"))
FPS = float(os.environ.get("CAMERA_FPS", "15"))
QUALITY = int(os.environ.get("JPEG_QUALITY", "85"))
PORT = int(os.environ.get("STREAM_PORT", "8001"))

LOCK = os.environ.get("CAMERA_LOCK", "1") == "1"
CONTROLS = os.environ.get("CAMERA_CONTROLS", "").strip()
DEV_PATH = "/dev/video" + DEVICE if DEVICE.isdigit() else DEVICE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# (auto control names, value for "manual", value control names). Names differ between kernels.
_LOCKS = [
    (("focus_automatic_continuous", "focus_auto"), 0, ("focus_absolute",)),
    (("white_balance_automatic", "white_balance_temperature_auto"), 0, ("white_balance_temperature",)),
    (("auto_exposure", "exposure_auto"), 1, ("exposure_time_absolute", "exposure_absolute")),
]


def _v4l2(*args):
    r = subprocess.run(["v4l2-ctl", "-d", DEV_PATH] + list(args), capture_output=True, text=True, timeout=5)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def lock_controls():
    """Freeze focus, white balance and exposure at what auto chose, then apply CAMERA_CONTROLS."""
    try:
        ok, listing = _v4l2("--list-ctrls")
    except (OSError, subprocess.SubprocessError) as e:
        logging.warning("Camera lock skipped: v4l2-ctl not usable (%s). Install v4l-utils.", e)
        return
    # lines look like "    focus_absolute 0x009a090a (int) : min=0 max=250 ..."
    have = {line.split()[0] for line in listing.splitlines() if " 0x" in line}
    done = []
    if LOCK:
        for autos, manual, values in _LOCKS:
            auto = next((a for a in autos if a in have), None)
            value = next((v for v in values if v in have), None)
            if not auto or not value:
                continue
            ok, out = _v4l2("-C", value)               # what auto picked, e.g. "focus_absolute: 30"
            current = out.rsplit(":", 1)[-1].strip() if ok else ""
            ok1, _ = _v4l2("-c", "%s=%d" % (auto, manual))
            ok2 = _v4l2("-c", "%s=%s" % (value, current))[0] if current.lstrip("-").isdigit() else False
            done.append("%s=%s" % (value, current) if ok1 and ok2 else "%s (failed)" % value)
    if CONTROLS:
        ok, out = _v4l2("-c", CONTROLS)
        done.append(("set " if ok else "FAILED ") + CONTROLS + ("" if ok else ": " + out))
    if done:
        logging.info("Camera controls: %s", ", ".join(done))

_latest = None          # newest JPEG bytes
_latest_time = 0.0      # time.time() of the newest frame
_latest_frame = None    # newest raw frame, for the small public copy
_small = (0.0, None)    # (frame time, small JPEG) for ?public=1, made only when someone asks

PUBLIC_WIDTH = int(os.environ.get("PUBLIC_WIDTH", "640"))
PUBLIC_FPS = float(os.environ.get("PUBLIC_FPS", "5"))
_cond = threading.Condition()


def _try_open(source, backend, fourcc, size):
    cap = cv2.VideoCapture(source, backend)
    if not cap.isOpened():
        cap.release()
        return None
    if fourcc:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    if size:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    for _ in range(5):  # a USB camera can return a few empty frames at start
        ok, frame = cap.read()
        if ok and frame is not None:
            return cap
        time.sleep(0.2)
    cap.release()
    return None


def open_camera():
    """Open the camera with plain V4L2 (not GStreamer), trying the usual USB-camera setups."""
    source = int(DEVICE) if DEVICE.isdigit() else DEVICE
    tries = [
        ("V4L2 MJPG %dx%d" % (WIDTH, HEIGHT), cv2.CAP_V4L2, "MJPG", True),
        ("V4L2 default format, %dx%d" % (WIDTH, HEIGHT), cv2.CAP_V4L2, None, True),
        ("V4L2 camera defaults", cv2.CAP_V4L2, None, False),
        ("any backend, camera defaults", cv2.CAP_ANY, None, False),
    ]
    for label, backend, fourcc, size in tries:
        cap = _try_open(source, backend, fourcc, size)
        if cap is not None:
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logging.info("Camera %s open: %s (got %dx%d)", DEVICE, label, w, h)
            return cap
        logging.warning("Camera %s: %s failed", DEVICE, label)
    return None


def capture_loop():
    """Keep the capture thread alive no matter what goes wrong."""
    while True:
        try:
            _capture()
        except Exception:
            logging.exception("Capture loop crashed; restarting in 3 s")
            time.sleep(3)


def _capture():
    """Keep reading frames; reopen the camera if it drops out."""
    global _latest, _latest_time, _latest_frame
    cap = None
    lock_at = None
    while True:
        if cap is None or not cap.isOpened():
            cap = open_camera()
            if cap is None:
                logging.warning("Camera %s not available; retrying in 3 s", DEVICE)
                time.sleep(3)
                continue
            lock_at = time.time() + 3 if (LOCK or CONTROLS) else None  # let auto settle first

        if lock_at and time.time() >= lock_at:
            lock_at = None
            lock_controls()

        ok, frame = cap.read()
        if not ok or frame is None:
            logging.warning("Camera read failed; reopening")
            cap.release()
            cap = None
            time.sleep(1)
            continue

        ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
        if ok:
            with _cond:
                _latest = jpg.tobytes()
                _latest_time = time.time()
                _latest_frame = frame
                _cond.notify_all()


def small_jpeg():
    """Smaller, lower-quality copy for the public website (about 30 KB instead of ~150 KB).
    Made at most once per new frame, and only while someone is watching."""
    global _small
    with _cond:
        t, frame, cached = _latest_time, _latest_frame, _small
    if frame is None:
        return None, 0.0
    if cached[0] == t:
        return cached[1], t
    h, w = frame.shape[:2]
    if w > PUBLIC_WIDTH:
        frame = cv2.resize(frame, (PUBLIC_WIDTH, int(h * PUBLIC_WIDTH / w)), interpolation=cv2.INTER_AREA)
    ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if not ok:
        return None, 0.0
    with _cond:
        _small = (t, jpg.tobytes())
    return _small[1], t


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the journal quiet; one line per request is too much at 2 polls/s

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        public = "public=1" in query.split("&")   # the website asks for this: smaller and slower

        if path == "/health":
            age = time.time() - _latest_time if _latest else None
            ok = age is not None and age < 5
            body = json.dumps({"ok": ok, "age_s": None if age is None else round(age, 2)}).encode()
            self._send(200 if ok else 503, body, "application/json")

        elif path == "/snapshot":
            if public:
                jpg = small_jpeg()[0]
            else:
                with _cond:
                    jpg = _latest
            if jpg is None:
                self._send(503, b"no frame yet", "text/plain")
            else:
                self._send(200, jpg, "image/jpeg")

        elif path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            last = 0.0
            sent_at = 0.0
            gap = 1.0 / PUBLIC_FPS if public else 0.0
            try:
                while True:
                    if gap:
                        time.sleep(max(0.0, sent_at + gap - time.time()))
                        sent_at = time.time()
                    with _cond:
                        _cond.wait_for(lambda: _latest_time > last, timeout=5)
                        jpg, last = _latest, _latest_time
                    if public:
                        jpg, last = small_jpeg()
                        last = last or time.time()
                    if jpg is None:
                        continue
                    self.wfile.write(
                        b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                        + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n"
                    )
            except (BrokenPipeError, ConnectionResetError):
                pass  # viewer closed the stream

        else:
            self._send(404, b"not found", "text/plain")


def main():
    threading.Thread(target=capture_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    logging.info("Camera server on port %d: /stream /snapshot /health", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
