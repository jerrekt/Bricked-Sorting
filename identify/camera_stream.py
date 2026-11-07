#!/usr/bin/env python3
"""Bricked Sorting: the Pi's camera server (replaces the lost camera_service.py stream).

It is the only program that opens the USB camera. Everything else reads from it:
  GET /stream    MJPEG video (the CT 150 dashboard relays this)
  GET /snapshot  one JPEG of the newest frame (identify/camera_service.py polls this)
  GET /health    {"ok": true, "age_s": seconds since the last frame}

Settings come from environment variables (all optional):
  CAMERA_DEVICE=0 (or /dev/video0)  CAMERA_WIDTH=1280  CAMERA_HEIGHT=720  CAMERA_FPS=15
  JPEG_QUALITY=85  STREAM_PORT=8001
"""
import json
import logging
import os
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

_latest = None          # newest JPEG bytes
_latest_time = 0.0      # time.time() of the newest frame
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
    global _latest, _latest_time
    cap = None
    while True:
        if cap is None or not cap.isOpened():
            cap = open_camera()
            if cap is None:
                logging.warning("Camera %s not available; retrying in 3 s", DEVICE)
                time.sleep(3)
                continue

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
                _cond.notify_all()


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
        path = self.path.split("?", 1)[0]

        if path == "/health":
            age = time.time() - _latest_time if _latest else None
            ok = age is not None and age < 5
            body = json.dumps({"ok": ok, "age_s": None if age is None else round(age, 2)}).encode()
            self._send(200 if ok else 503, body, "application/json")

        elif path == "/snapshot":
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
            try:
                while True:
                    with _cond:
                        _cond.wait_for(lambda: _latest_time > last, timeout=5)
                        jpg, last = _latest, _latest_time
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
