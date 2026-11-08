#!/usr/bin/env python3
"""Bricked Sorting: camera relay on CT 150.

The Pi can reach CT 150 over Tailscale but CT 150 can't reach the Pi, so the Pi PUSHES
frames here (identify/camera_push.py) and the website's nginx reads them from here.

  POST /push      one JPEG in the body (from the Pi). Answers {"watchers": n} so the Pi
                  sends 5 frames/s while someone watches and one every 5 s otherwise.
  GET  /stream    MJPEG for nginx /camera-stream (ends after 15 s without a new frame)
  GET  /snapshot  newest JPEG                      (nginx /camera-snapshot)
  GET  /health    {"ok": true} if a frame came in the last 12 s   (nginx /camera-health)
  POST /login     {"password": "..."} -> sets a 12-hour cookie      (nginx /camera-login)
  GET  /session   200 if the cookie is good, 401 if not             (nginx /camera-session)

Team password: when RELAY_PASSWORD_SHA256 is set, /stream and /snapshot need the cookie
from /login (same team password as the Live page buttons). /health stays public so the
page can show Live/Offline. 5 wrong tries from one visitor = 10 minutes locked out.

Settings (environment, /etc/bricked-camera-relay.env, written by deploy/setup-camera-proxy.sh):
  RELAY_PASSWORD_SHA256  sha256 hex of the team password (unset = no password, open stream)
  RELAY_SESSION_KEY      random secret that signs the cookies (unset = new one each restart)
  RELAY_PORT=8002  MAX_FPS=6
Who can push: anyone who can reach port 8002 (Tailscale only: the Proxmox firewall only
lets Kratos reach CT 150 on 8080/5000). Pushes must be real JPEGs under 2 MB.
"""
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("RELAY_PORT", "8002"))
MAX_FPS = float(os.environ.get("MAX_FPS", "6"))
MAX_BYTES = 2_000_000
STALE = 12.0      # seconds without a push = camera offline
STREAM_IDLE = 15  # close a viewer's stream after this long with no new frame

PASSWORD_SHA256 = os.environ.get("RELAY_PASSWORD_SHA256", "").strip().lower()
SESSION_KEY = (os.environ.get("RELAY_SESSION_KEY", "").strip() or secrets.token_hex(32)).encode()
COOKIE = "bs_cam"
SESSION_SECONDS = 12 * 3600
FAIL_LIMIT, FAIL_WINDOW = 5, 600       # per visitor
GLOBAL_FAIL_LIMIT = 30                 # all visitors together, same window

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

_cond = threading.Condition()
_jpg = None
_at = 0.0
_watchers = 0
_pushes = []  # recent push times, for a simple rate limit


_fails = {}       # visitor -> [times of wrong tries]
_fails_lock = threading.Lock()


def _sign(expires):
    return hmac.new(SESSION_KEY, str(expires).encode(), hashlib.sha256).hexdigest()


def make_cookie():
    exp = int(time.time()) + SESSION_SECONDS
    return "%s=%d.%s; Max-Age=%d; Path=/; HttpOnly; Secure; SameSite=Strict" % (COOKIE, exp, _sign(exp), SESSION_SECONDS)


def cookie_ok(header):
    if not PASSWORD_SHA256:
        return True                      # no password set up: open, like before
    for part in (header or "").split(";"):
        name, _, value = part.strip().partition("=")
        if name == COOKIE and "." in value:
            exp, _, sig = value.partition(".")
            if exp.isdigit() and int(exp) > time.time() and hmac.compare_digest(sig, _sign(int(exp))):
                return True
    return False


def too_many_fails(who, now):
    with _fails_lock:
        for k in list(_fails):
            _fails[k] = [t for t in _fails[k] if now - t < FAIL_WINDOW]
            if not _fails[k]:
                del _fails[k]
        total = sum(len(v) for v in _fails.values())
        return len(_fails.get(who, [])) >= FAIL_LIMIT or total >= GLOBAL_FAIL_LIMIT


def add_fail(who, now):
    with _fails_lock:
        _fails.setdefault(who, []).append(now)


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

    def _visitor(self):
        # nginx is only reached through the Cloudflare tunnel, which sets CF-Connecting-IP
        return (self.headers.get("CF-Connecting-IP") or self.client_address[0]).strip()

    def _login(self):
        now = time.time()
        who = self._visitor()
        if not PASSWORD_SHA256:
            return self._json(200, {"ok": True, "password": False})
        if too_many_fails(who, now):
            return self._json(429, {"error": "Too many wrong tries. Wait 10 minutes."})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > 2000:
            self.close_connection = True
            return self._json(400, {"error": "Send the password."})
        try:
            password = str(json.loads(self.rfile.read(n)).get("password", ""))
        except (ValueError, AttributeError):
            return self._json(400, {"error": "Send the password."})
        given = hashlib.sha256(password.encode()).hexdigest()
        if not hmac.compare_digest(given, PASSWORD_SHA256):
            add_fail(who, now)
            return self._json(401, {"error": "Wrong team password."})
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie", make_cookie())
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global _jpg, _at
        if self.path.split("?", 1)[0] == "/login":
            return self._login()
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

        if path == "/session":
            ok = cookie_ok(self.headers.get("Cookie"))
            return self._json(200 if ok else 401, {"ok": ok, "password": bool(PASSWORD_SHA256)})

        if path in ("/snapshot", "/stream") and not cookie_ok(self.headers.get("Cookie")):
            return self._send(401, b"team password needed", "text/plain")

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
    logging.info("Camera relay on port %d: POST /push /login, GET /stream /snapshot /health /session", PORT)
    logging.info("Team password %s", "required for /stream and /snapshot" if PASSWORD_SHA256 else "NOT set: stream is open")
    server.serve_forever()


if __name__ == "__main__":
    main()
