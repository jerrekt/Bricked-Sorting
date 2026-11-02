#!/usr/bin/env python3
"""Bin bridge: listens to the Live page and sends each bin code to the Arduino over USB.

  pip install pyserial
  python bin_bridge.py --dry-run                 # just print the codes, no Arduino
  python bin_bridge.py --port COM5               # Windows
  python bin_bridge.py --port /dev/ttyACM0       # Mac/Linux (ls /dev/tty.* or /dev/ttyACM*)

What the Arduino gets, one line per piece:   1-3\n
What it must answer when the chute is there: OK 1-3
It can also answer:                          ERR <anything>
Only one command is sent at a time; the next waits for OK, ERR or the timeout.

By default it only follows SIMULATOR pieces (press Start simulator on the Live page).
Use --source live for the real camera, or --source any for both.
Stop with Ctrl+C.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

API = "https://bricked-api.adsuaracloud.com"


def get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "bricked-bin-bridge/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def valid(code):
    parts = str(code).split("-")
    return len(parts) == 2 and parts[0] in ("1", "2") and parts[1] in tuple("12345678")


class Arduino:
    def __init__(self, port, baud, timeout):
        import serial  # pyserial
        self.s = serial.Serial(port, baud, timeout=0.2)
        self.timeout = timeout
        time.sleep(2)  # most boards reset when the port opens
        self.s.reset_input_buffer()
        print(f"Connected to {port} at {baud} baud")

    def send(self, code):
        self.s.write((code + "\n").encode())
        end = time.time() + self.timeout
        while time.time() < end:
            line = self.s.readline().decode(errors="replace").strip()
            if not line:
                continue
            if line == f"OK {code}":
                return "OK"
            if line.startswith("ERR"):
                return line
            print(f"   arduino: {line}")  # its own debug prints
        return "TIMEOUT"


def main():
    ap = argparse.ArgumentParser(description="Send Live page bin codes to the Arduino.")
    ap.add_argument("--port", help="serial port, like COM5 or /dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--dry-run", action="store_true", help="print codes only, no Arduino")
    ap.add_argument("--source", choices=["sim", "live", "any"], default="sim")
    ap.add_argument("--timeout", type=float, default=10, help="seconds to wait for OK")
    ap.add_argument("--api", default=API)
    a = ap.parse_args()
    if not a.dry_run and not a.port:
        sys.exit("Give --port (like COM5) or use --dry-run.")

    arduino = None if a.dry_run else Arduino(a.port, a.baud, a.timeout)
    last = get(a.api + "/live/state", 10)["last_id"]  # start from now, skip old pieces
    print(f"Listening for {a.source} pieces. Ctrl+C to stop.")
    while True:
        try:
            r = get(f"{a.api}/live/events?after={last}&wait=25", 35)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"   can't reach the server ({e}); retrying in 5 s")
            time.sleep(5)
            continue
        events = r.get("events", [])
        if len(events) > 10:
            print(f"   {len(events) - 10} pieces arrived too fast; skipping to the newest 10")
            events = events[-10:]
        for e in events:
            last = max(last, e["id"])
            if a.source != "any" and e.get("source") != a.source:
                continue
            code = e.get("code", "")
            if not valid(code):
                print(f"   skipped bad code {code!r}")
                continue
            label = f"{code}  {e.get('name', '')[:40]}  ({e.get('source')})"
            if arduino is None:
                print(f"-> {label}  [dry run]")
            else:
                t = time.time()
                result = arduino.send(code)
                print(f"-> {label}  {result} in {time.time() - t:.1f} s")
        last = max(last, r.get("last_id", last))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
