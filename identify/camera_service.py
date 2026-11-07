#!/usr/bin/env python3
"""Bricked Sorting: Pi camera loop.

Reads frames from the local camera server (camera_stream.py, /snapshot), notices when a
new piece lands on the tray, sends ONE cropped photo of it to CT 150 /identify, and waits
for the tray to clear before looking for the next piece.

Settings (environment variables, kept in ~/.bricked_camera.env by setup_camera.sh):
  IDENTIFY_URL   required, CT 150 /identify (no ?preview=1)
  SNAPSHOT_URL   default http://127.0.0.1:8001/snapshot
  TRAY_CROP      left,top,right,bottom as 0-1 fractions, default whole picture
  PIXEL_DELTA    how much a pixel must change (0-255) to count as changed, default 25
  OCCUPIED_PCT   % of tray pixels changed = a piece is there, default 0.5
  EMPTY_PCT      % below which the tray counts as empty again, default 0.2
  MOVING_PCT     % changed between two frames = still moving, default 0.3
  STABLE_FRAMES  still frames in a row before sending, default 2
  EMPTY_FRAMES   empty frames in a row before re-arming, default 3
  SCAN_INTERVAL  seconds between frames, default 0.5
"""
import logging
import os
import time

import cv2
import numpy as np
import requests

IDENTIFY_URL = os.environ["IDENTIFY_URL"]
SNAPSHOT_URL = os.environ.get("SNAPSHOT_URL", "http://127.0.0.1:8001/snapshot")

SCAN_INTERVAL = float(os.environ.get("SCAN_INTERVAL", "0.5"))
PIXEL_DELTA = float(os.environ.get("PIXEL_DELTA", "25"))
OCCUPIED_PCT = float(os.environ.get("OCCUPIED_PCT", "0.5"))
EMPTY_PCT = float(os.environ.get("EMPTY_PCT", "0.2"))
MOVING_PCT = float(os.environ.get("MOVING_PCT", "0.3"))
STABLE_FRAMES = int(os.environ.get("STABLE_FRAMES", "2"))
EMPTY_FRAMES = int(os.environ.get("EMPTY_FRAMES", "3"))
RETRY_MAX = 60.0  # seconds, longest wait between tries while /identify is down

TRAY_CROP = [float(x) for x in os.environ.get("TRAY_CROP", "0.0,0.0,1.0,1.0").split(",")]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def crop_tray(frame):
    height, width = frame.shape[:2]
    left, top, right, bottom = TRAY_CROP
    return frame[int(height * top):int(height * bottom), int(width * left):int(width * right)]


def gray_tray(frame):
    gray = cv2.cvtColor(crop_tray(frame), cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (320, 240))
    return cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)  # blur hides sensor noise


def changed_pct(a, b):
    """Share of pixels (in %) that changed by more than PIXEL_DELTA.
    Works for any piece size, unlike an average over the whole picture."""
    return float(np.mean(np.abs(a - b) > PIXEL_DELTA) * 100.0)


def get_frame():
    response = requests.get(SNAPSHOT_URL, timeout=5)
    response.raise_for_status()
    frame = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError("Could not decode camera image")
    return frame


def identify(photo, settled_at):
    """Send one photo (already cropped to the tray) to /identify and log the answer."""
    success, encoded = cv2.imencode(".jpg", photo, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise RuntimeError("Could not encode camera image")

    response = requests.post(
        IDENTIFY_URL,
        files={"image": ("tray.jpg", encoded.tobytes(), "image/jpeg")},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    elapsed = time.monotonic() - settled_at

    if result.get("bin") == "NO_LEGO":
        logging.info("No LEGO detected; answer %.2f s after the piece settled", elapsed)
    else:
        logging.info(
            "Piece: %s | bin: %s | confidence: %s%% | answer: %.2f s after settling",
            result.get("name", "Unknown LEGO"), result.get("bin", "Unknown"),
            result.get("confidence", 0), elapsed,
        )
    return result


def main():
    logging.info("Camera identification loop started (keep the tray empty for the first second)")

    empty_reference = None
    previous_gray = None
    occupied = False
    stable_count = 0
    empty_count = 0
    last_frame = None
    retry_wait = 0.0     # grows while /identify fails
    next_try = 0.0

    while True:
        try:
            frame = get_frame()
            current_gray = gray_tray(frame)

            if empty_reference is None:
                empty_reference = current_gray
                previous_gray = current_gray
                time.sleep(SCAN_INTERVAL)
                continue

            difference = changed_pct(current_gray, empty_reference)
            movement = changed_pct(current_gray, previous_gray)

            if occupied:
                if difference < EMPTY_PCT:
                    empty_count += 1
                    if empty_count >= EMPTY_FRAMES:
                        occupied = False
                        stable_count = 0
                        empty_count = 0
                        last_frame = None
                        empty_reference = current_gray
                        logging.info("Tray is empty again")
                else:
                    empty_count = 0

            elif difference > OCCUPIED_PCT:
                if movement < MOVING_PCT:
                    stable_count += 1
                    last_frame = frame
                else:
                    stable_count = 0
                    last_frame = None

                if stable_count >= STABLE_FRAMES and last_frame is not None and time.monotonic() >= next_try:
                    logging.info("New piece settled (%.1f%% of tray changed); identifying once", difference)
                    try:
                        identify(crop_tray(last_frame), time.monotonic())
                        retry_wait = 0.0
                        occupied = True
                        stable_count = 0
                        empty_count = 0
                    except (requests.RequestException, ValueError, RuntimeError) as error:
                        retry_wait = min(RETRY_MAX, max(2.0, retry_wait * 2))
                        next_try = time.monotonic() + retry_wait
                        logging.warning("Identify failed (%s); trying again in %.0f s", error, retry_wait)

            else:
                stable_count = 0
                last_frame = None
                # Slowly follow lighting changes while the tray is empty.
                empty_reference = empty_reference * 0.98 + current_gray * 0.02

            previous_gray = current_gray

        except requests.RequestException as error:
            logging.warning("Camera server not answering: %s", error)
        except Exception as error:
            logging.warning("Camera loop error: %s", error)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
