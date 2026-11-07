"""Send each identified piece to the Live page.

Lives next to brick_server.py on CT 150 and is called right after /identify has
its result. It never slows down or breaks /identify: it runs in a background
thread, gives up after 4 seconds, and only logs a warning on failure.

Settings come from the service's environment (root-only env file, see README):
  BRICKED_LIVE_TOKEN  the ingest key (required; nothing is sent without it)
  BRICKED_LIVE_URL    default https://bricked-api.adsuaracloud.com/live/event
"""
import base64
import logging
import os
import threading

import requests

log = logging.getLogger("live_hook")
URL = os.environ.get("BRICKED_LIVE_URL", "https://bricked-api.adsuaracloud.com/live/event")
MAX_IMAGE = 280_000  # the Live service refuses JPEGs over 300 KB
FIELDS = ("name", "part_id", "category", "confidence", "shape", "bin", "bin_number",
          "floor", "slot", "color", "color_bucket", "color_confidence", "rgb", "lego_detected")


def _send(payload: dict, token: str):
    try:
        r = requests.post(URL, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=4)
        if r.status_code >= 300:
            log.warning("live page refused piece: %s %s", r.status_code, r.text[:200])
    except Exception as e:
        log.warning("live page unreachable: %s", e)


def post_live(result: dict, jpeg_bytes: bytes | None = None) -> None:
    """Call after /identify. result is the dict /identify returns; jpeg_bytes the camera photo."""
    token = os.environ.get("BRICKED_LIVE_TOKEN", "").strip()
    if not token or not isinstance(result, dict):
        return
    if str(result.get("bin", "")).upper() == "NO_LEGO" or result.get("lego_detected") is False:
        return
    payload = {k: result[k] for k in FIELDS if k in result}
    if jpeg_bytes and len(jpeg_bytes) <= MAX_IMAGE:
        payload["image_b64"] = base64.b64encode(jpeg_bytes).decode()
    threading.Thread(target=_send, args=(payload, token), daemon=True).start()
