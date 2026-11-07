#!/usr/bin/env python3
"""Bricked Sorting: send the Pi camera to CT 150 so the website can show it.

CT 150 can't open connections to the Pi, so the Pi pushes instead. Takes the small public
frame from the local camera server (camera_stream.py, /snapshot?public=1) and POSTs it to
the camera relay on CT 150 (kratos/camera-relay). 5 frames/s while someone is watching the
Camera tab, one every 5 s otherwise (keeps the page's Live/Offline badge right).

Settings (environment, from ~/.bricked_camera.env):
  PUSH_URL      http://<CT150_TAILNET_IP>:8002/push   (setup_camera.sh fills it in)
  SNAPSHOT_URL  default http://127.0.0.1:8001/snapshot
  PUSH_FPS=5    IDLE_EVERY=5 (seconds between frames when nobody watches)
"""
import logging
import os
import time

import requests

PUSH_URL = os.environ["PUSH_URL"]
SNAP = os.environ.get("SNAPSHOT_URL", "http://127.0.0.1:8001/snapshot")
SNAP += ("&" if "?" in SNAP else "?") + "public=1"
FPS = float(os.environ.get("PUSH_FPS", "5"))
IDLE_EVERY = float(os.environ.get("IDLE_EVERY", "5"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def main():
    session = requests.Session()
    watchers, failing_since, last_log = 0, None, 0.0
    logging.info("Pushing camera frames to %s", PUSH_URL.split("/push")[0] + "/push")
    while True:
        started = time.time()
        try:
            jpg = session.get(SNAP, timeout=3)
            jpg.raise_for_status()
            r = session.post(PUSH_URL, data=jpg.content, headers={"Content-Type": "image/jpeg"}, timeout=5)
            r.raise_for_status()
            now_watching = int(r.json().get("watchers", 0))
            if now_watching != watchers:
                logging.info("%d watching the Camera tab", now_watching)
            watchers = now_watching
            if failing_since:
                logging.info("Relay reachable again")
            failing_since = None
        except (requests.RequestException, ValueError) as e:
            watchers = 0
            failing_since = failing_since or started
            if started - last_log > 60:  # one line a minute while it's down, not 5 a second
                logging.warning("Push failed: %s", e)
                last_log = started
        wait = (1.0 / FPS) if watchers else IDLE_EVERY
        time.sleep(max(0.05, wait - (time.time() - started)))


if __name__ == "__main__":
    main()
