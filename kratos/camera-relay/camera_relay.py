#!/usr/bin/env python3
"""Bricked Sorting: camera relay on CT 150.

The Pi can reach CT 150 over Tailscale but CT 150 can't reach the Pi, so the Pi PUSHES
frames here (identify/camera_push.py) and the website's nginx reads them from here.

  POST /push      one JPEG in the body (from the Pi). Answers {"watchers": n} so the Pi
                  sends 5 frames/s while someone watches and one every 5 s otherwise.
  GET  /stream    MJPEG for nginx /camera-stream (ends after 15 s without a new frame)
  GET  /snapshot  newest JPEG                      (nginx /camera-snapshot)
  GET  /health    {"ok": true} if a frame came in the last 12 s   (nginx /camera-health)

Settings (environment, all optional): RELAY_PORT=8002  MAX_FPS=6
Who can push: anyone who can reach port 8002 (Tailscale only: the Proxmox firewall only
lets Kratos reach CT 150 on 8080/5000). Pushes must be real JPEGs under 2 MB.
"""
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("RELAY_PORT", "8002"))
MAX_FPS = float(os.environ.get("MAX_FPS", "6"))
MAX_BYTES = 2_000_000
STALE = 12.0      # seconds without a push = camera offline
STREAM_IDLE = 15  # close a viewer's stream after this long with no new frame

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

_cond = threading.Condition()
_jpg = None
_at = 0.0
_watchers = 0
_pushes = []  # recent push times, for a simple rate limit


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_POST(self):
        global _jpg, _at
        if self.path.split("?", 1)[0] != "/push":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BYTES:
            self.close_connection = True
            return self._json(413 if n > MAX_BYTES else 400, {"error": "send one JPEG under 2 MB"})
        body = self.rfile.read(n)
        if body[:2] != b"\xff\xd8":
            return self._json(400, {"error": "not a JPEG"})
        now = time.time()
        with _cond:
            _pushes[:] = [t for t in _pushes if now - t < 1.0]
            if len(_pushes) >= 15:
                return self._json(429, {"error": "slow down", "watchers": _watchers})
            _pushes.append(now)
            first = _jpg is None or now - _at > STALE
            _jpg, _at = body, now
            _cond.notify_all()
            watchers = _watchers
        if first:
            logging.info("Camera frames coming in from %s", self.client_address[0])
        self._json(200, {"ok": True, "watchers": watchers})

    def do_GET(self):
        global _watchers
        path = self.path.split("?", 1)[0]
        with _cond:
            jpg, at = _jpg, _at
        fresh = jpg is not None and time.time() - at < STALE

        if path == "/health":
            return self._json(200 if fresh else 503, {"ok": fresh, "age_s": round(time.time() - at, 1) if jpg else None, "watchers": _watchers})

        if path == "/snapshot":
            return self._send(200, jpg, "image/jpeg") if fresh else self._send(503, b"camera offline", "text/plain")

        if path == "/stream":
            if not fresh:
                return self._send(503, b"camera offline", "text/plain")
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            with _cond:
                _watchers += 1
            last, sent_at = 0.0, 0.0
            try:
                while True:
                    time.sleep(max(0.0, sent_at + 1.0 / MAX_FPS - time.time()))
                    with _cond:
                        if not _cond.wait_for(lambda: _at > last, timeout=STREAM_IDLE):
                            break  # camera stopped sending: end, the page reconnects
                        jpg, last = _jpg, _at
                    sent_at = time.time()
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            finally:
                with _cond:
                    _watchers -= 1
            return

        self._send(404, b"not found", "text/plain")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    logging.info("Camera relay on port %d: POST /push, GET /stream /snapshot /health", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
