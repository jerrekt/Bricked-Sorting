#!/usr/bin/env python3
"""Fake /identify for building the Indicate stage before the camera works.

Returns made-up bin codes using the real piece list of one LEGO 10696 box.
Uses only the Python standard library. Does not call Brickognize, save
images or need any key.

Run:   python3 identify/fake_identify.py            (port 5001)
Try:   curl -s -X POST localhost:5001/identify
       curl -s localhost:5001/bins
Options: --port 5001  --misread 3   (percent sent to the unknown bin)
"""
import argparse, json, os, random
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BINS = json.load(open(os.path.join(ROOT, "web/data/bins.json")))
SET = json.load(open(os.path.join(ROOT, "web/data/set-10696.json")))
LOOKUP = json.load(open(os.path.join(ROOT, "indicate/bin-lookup.json")))
SLOT_OF = {s["key"]: s["slot"] for s in BINS["slots"]}
POOL = [p for p in SET["parts"] for _ in range(p["qty"])]
MISREAD = 3


def pick():
    p = random.choice(POOL)
    group = BINS["colorMap"].get(p["color"], "unknown")
    if group != "unknown" and random.random() * 100 < MISREAD:
        group = "unknown"
    floor = 1 if p["brick"] else 2
    slot = SLOT_OF[group]
    return {
        "code": f"{floor}-{slot}", "floor": floor, "slot": slot,
        "category": "brick" if p["brick"] else "other", "group": group,
        "name": p["part"], "color": p["color"],
        "confidence": round(random.uniform(0.6, 0.98), 2),
        "fake": True,
    }


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?")[0] != "/identify":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(min(n, 10_000_000))  # image is ignored
        self._send(200, pick())

    def do_GET(self):
        if self.path == "/bins":
            return self._send(200, LOOKUP)
        self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--misread", type=float, default=3)
    a = ap.parse_args()
    MISREAD = a.misread
    print(f"fake identify on port {a.port} (not the real server)")
    HTTPServer(("0.0.0.0", a.port), H).serve_forever()
