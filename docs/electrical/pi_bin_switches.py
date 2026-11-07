#!/usr/bin/env python3
"""Bin switches on the Pi -> Live page.

Reads one switch per bin and tells the Live service which bins are open (lifted).
Sends the full list on every change and every 20 s, so the page knows the switches
are still reporting. Reference script: Ethan wires it into his Pi setup.

Wiring (every switch the same): C -> GND, NO -> GPIO, internal pull-up on.
  Bin seated = switch pressed = LOW.  Bin lifted (or wire broken) = HIGH = open.

Run:
  export BRICKED_BINS_TOKEN=...        # from Branden, never commit it
  python3 pi_bin_switches.py
Needs only gpiozero (already on Raspberry Pi OS).
"""
import json
import os
import signal
import threading
import time
import urllib.error
import urllib.request

from gpiozero import Button

API = os.environ.get("BRICKED_API", "https://bricked-api.adsuaracloud.com")
TOKEN = os.environ["BRICKED_BINS_TOKEN"]
HEARTBEAT = 20  # seconds

# GPIO -> bin code (floor-slot, like on the Live page). Fill in which bin each switch sits under.
SWITCHES = {
    23: "1-1",
    24: "1-2",
    25: "1-3",
    16: "1-4",
    20: "1-5",
}

buttons = {gpio: Button(gpio, pull_up=True, bounce_time=0.05) for gpio in SWITCHES}
lock = threading.Lock()
last_sent = None


def open_bins():
    # is_pressed = pin pulled LOW = bin seated
    return sorted(code for gpio, code in SWITCHES.items() if not buttons[gpio].is_pressed)


def send(force=False):
    global last_sent
    with lock:
        now = open_bins()
        if now == last_sent and not force:
            return
        body = json.dumps({"open": now, "drawers_open": []}).encode()
        req = urllib.request.Request(API + "/live/bins", data=body, method="POST", headers={
            "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json",
            "User-Agent": "bricked-pi-bins"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
            last_sent = now
            print(time.strftime("%H:%M:%S"), "open:", now or "none", flush=True)
        except (urllib.error.URLError, OSError) as e:
            print(time.strftime("%H:%M:%S"), "send failed:", e, flush=True)  # retried next change or heartbeat


for b in buttons.values():
    b.when_pressed = b.when_released = lambda: send()

stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *_: stop.set())
send(force=True)
try:
    while not stop.wait(HEARTBEAT):
        send(force=True)
except KeyboardInterrupt:
    pass
