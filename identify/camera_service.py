#!/usr/bin/env python3

import os
import time
import logging

import cv2
import numpy as np
import requests


IDENTIFY_URL = os.environ["IDENTIFY_URL"]
SNAPSHOT_URL = os.environ.get(
    "SNAPSHOT_URL",
    "http://127.0.0.1:8001/snapshot"
)

SCAN_INTERVAL = float(os.environ.get("SCAN_INTERVAL", "0.5"))
OCCUPIED_THRESHOLD = float(os.environ.get("OCCUPIED_THRESHOLD", "12"))
EMPTY_THRESHOLD = float(os.environ.get("EMPTY_THRESHOLD", "7"))
STABLE_THRESHOLD = float(os.environ.get("STABLE_THRESHOLD", "4"))
STABLE_FRAMES = int(os.environ.get("STABLE_FRAMES", "2"))
EMPTY_FRAMES = int(os.environ.get("EMPTY_FRAMES", "3"))

# Crop format: left,top,right,bottom as percentages from 0.0 to 1.0
TRAY_CROP = [
    float(x)
    for x in os.environ.get(
        "TRAY_CROP",
        "0.0,0.0,1.0,1.0"
    ).split(",")
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)


def crop_tray(frame):
    height, width = frame.shape[:2]
    left, top, right, bottom = TRAY_CROP

    x1 = int(width * left)
    y1 = int(height * top)
    x2 = int(width * right)
    y2 = int(height * bottom)

    return frame[y1:y2, x1:x2]


def gray_tray(frame):
    tray = crop_tray(frame)
    gray = cv2.cvtColor(tray, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (320, 240))


def get_frame():
    response = requests.get(SNAPSHOT_URL, timeout=5)
    response.raise_for_status()

    data = np.frombuffer(response.content, dtype=np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if frame is None:
        raise RuntimeError("Could not decode camera image")

    return frame


def identify(frame):
    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 85]
    )

    if not success:
        raise RuntimeError("Could not encode camera image")

    started = time.monotonic()

    response = requests.post(
        IDENTIFY_URL,
        files={
            "image": (
                "tray.jpg",
                encoded.tobytes(),
                "image/jpeg"
            )
        },
        timeout=30
    )

    response.raise_for_status()
    result = response.json()
    elapsed = time.monotonic() - started

    name = result.get("name", "Unknown LEGO")
    bin_name = result.get("bin", "Unknown")
    confidence = result.get("confidence", 0)

    if bin_name == "NO_LEGO":
        logging.info(
            "No LEGO detected; answer received in %.2f seconds",
            elapsed
        )
    else:
        logging.info(
            "Piece: %s | bin: %s | confidence: %s%% | answer: %.2f seconds",
            name,
            bin_name,
            confidence,
            elapsed
        )

    return result


def main():
    logging.info("Camera identification loop started")

    empty_reference = None
    previous_gray = None
    occupied = False
    stable_count = 0
    empty_count = 0
    last_frame = None

    while True:
        try:
            frame = get_frame()
            current_gray = gray_tray(frame)

            if empty_reference is None:
                empty_reference = current_gray.astype(np.float32)
                previous_gray = current_gray
                time.sleep(SCAN_INTERVAL)
                continue

            difference = np.mean(
                np.abs(
                    current_gray.astype(np.float32) -
                    empty_reference
                )
            )

            movement = np.mean(
                np.abs(
                    current_gray.astype(np.float32) -
                    previous_gray.astype(np.float32)
                )
            )

            if occupied:
                if difference < EMPTY_THRESHOLD:
                    empty_count += 1

                    if empty_count >= EMPTY_FRAMES:
                        occupied = False
                        stable_count = 0
                        empty_count = 0
                        last_frame = None
                        empty_reference = current_gray.astype(
                            np.float32
                        )

                        logging.info("Tray is empty again")
                else:
                    empty_count = 0

            else:
                if difference > OCCUPIED_THRESHOLD:
                    if movement < STABLE_THRESHOLD:
                        stable_count += 1
                        last_frame = frame.copy()
                    else:
                        stable_count = 0
                        last_frame = None

                    if stable_count >= STABLE_FRAMES:
                        logging.info("New piece settled; identifying once")

                        identify(last_frame)

                        occupied = True
                        stable_count = 0
                        empty_count = 0
                else:
                    stable_count = 0
                    last_frame = None

                    # Slowly adjust to lighting changes while empty.
                    empty_reference = (
                        empty_reference * 0.98 +
                        current_gray.astype(np.float32) * 0.02
                    )

            previous_gray = current_gray

        except requests.RequestException as error:
            logging.warning("Network error: %s", error)

        except Exception as error:
            logging.warning("Camera loop error: %s", error)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
