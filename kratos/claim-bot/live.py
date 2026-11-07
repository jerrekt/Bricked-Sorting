"""Live page service: pieces from the real camera (via CT 150) or from the simulator,
shown on the website and sent to Marshall's bin bridge.

Off unless BRICKED_LIVE_ENABLED=1, so other bots that run this same code don't get it.
Security design: Mnemosyne runbooks/security-review.md, "Bricked Sorting Live page and bin bridge".
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import io
import json
import random
import re
import threading
import time
from collections import deque
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

import app as core

router = APIRouter()
Image.MAX_IMAGE_PIXELS = 20_000_000  # refuse decompression bombs

MAX_BODY = 450_000        # bytes of JSON, image included (base64)
MAX_IMAGE_IN = 300_000    # bytes of JPEG before re-encoding
THUMB = 320               # px, longest side
KEEP_EVENTS = 200
KEEP_IMAGES = 30
WAIT_MAX = 25             # seconds a long-poll may hold
MAX_WAITERS = 40
SIM_MAX_RATE = 2.0        # pieces per second
SIM_MAX_SECONDS = 600
INGEST_LIMIT, INGEST_WINDOW = 600, 60
BINS_LIMIT, BINS_WINDOW = 120, 60
SENSOR_STALE = 90         # seconds without a Pi update before the switches count as offline
BIN_CODE = re.compile(r"^(?:[12]-[1-8]|[FB][1-8])$")   # floor-slot now, V14 drawer codes later
DRAWERS = {"front", "back"}
NO_STORE = {"Cache-Control": "no-store"}
DATA_BASE = "https://raw.githubusercontent.com/jerrekt/Bricked-Sorting/main/web/data/"


def enabled() -> bool:
    return core.env("BRICKED_LIVE_ENABLED") == "1"


def need_enabled():
    if not enabled():
        raise HTTPException(404, "Not found")


# ---------- shared state ----------

class Hub:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset_all()

    def reset_all(self):
        with self.lock:
            self.events: deque = deque(maxlen=KEEP_EVENTS)
            self.images: dict[int, bytes] = {}
            self.next_id = 1
            self.counts = {"live": {}, "sim": {}}
            self.last_live_at = 0.0
            self.sim = {"running": False, "until": 0.0, "rate": 0.0, "by": "", "token": 0}
            self.waiters = 0
            # bin switches (Pi): open bins with the time they opened, bins that need a recount
            self.open: dict[str, float] = {}
            self.recount: set[str] = set()
            self.drawers_open: list[str] = []
            self.sensors_at = 0.0
            self.bins_rev = 0

    def set_bins(self, open_codes: list[str], drawers: list[str]) -> None:
        """The Pi sends the full list of open bins each time; work out what changed."""
        with self.lock:
            now = round(time.time(), 3)
            before = set(self.open)
            after = set(open_codes)
            for code in before - after:          # closed again: count is no longer trusted
                del self.open[code]
                self.recount.add(code)
            for code in after - before:
                self.open[code] = now
            drawers = sorted(set(drawers))
            changed = before != after or drawers != self.drawers_open or not self.sensors_on()
            self.drawers_open = drawers
            self.sensors_at = now
            if changed:
                self.bins_rev += 1

    def sensors_on(self) -> bool:
        return time.time() - self.sensors_at < SENSOR_STALE

    def bins_state(self) -> dict:
        with self.lock:
            return self._bins()

    def _bins(self) -> dict:  # caller holds the lock
        on = self.sensors_on()
        return {"sensors": on, "sensors_at": self.sensors_at, "rev": self.bins_rev,
                "open": dict(self.open) if on else {}, "drawers_open": list(self.drawers_open) if on else [],
                "recount": sorted(self.recount)}

    def add(self, evt: dict, image: bytes | None = None) -> dict:
        with self.lock:
            evt = dict(evt, id=self.next_id, ts=round(time.time(), 3), has_image=bool(image))
            self.next_id += 1
            self.events.append(evt)
            c = self.counts[evt["source"]]
            c[evt["code"]] = c.get(evt["code"], 0) + 1
            if evt["source"] == "live":
                self.last_live_at = evt["ts"]
            if image:
                self.images[evt["id"]] = image
                for old in sorted(self.images)[:-KEEP_IMAGES]:
                    del self.images[old]
            return evt

    def after(self, last: int, limit: int = 50) -> list[dict]:
        with self.lock:
            return [e for e in self.events if e["id"] > last][:limit]

    def mode(self) -> str:
        if self.sim["running"]:
            return "sim"
        if time.time() - self.last_live_at < 60:
            return "live"
        return "idle"

    def state(self) -> dict:
        with self.lock:
            sim = {k: v for k, v in self.sim.items() if k != "token"}
            return {
                "mode": self.mode(), "sim": sim, "last_live_at": self.last_live_at,
                "counts": {k: dict(v) for k, v in self.counts.items()},
                "events": list(self.events)[-30:], "last_id": self.next_id - 1,
                "bins": self._bins(),
            }


HUB = Hub()


# ---------- reference data (bins and the 10696 piece list) ----------

_ref = {"data": None, "at": 0.0}


def ref() -> dict:
    if _ref["data"] and time.time() - _ref["at"] < 600:
        return _ref["data"]
    def get(name):
        local = core.env("BRICKED_DATA_DIR")
        if local:
            return json.loads((Path(local) / name).read_text())
        r = httpx.get(DATA_BASE + name, timeout=4)
        r.raise_for_status()
        return r.json()
    bins, pieces = get("bins.json"), get("set-10696.json")
    slot_of = {s["key"]: s["slot"] for s in bins["slots"]}
    swatch = {s["slot"]: s.get("swatch") for s in bins["slots"]}
    pool = [p for p in pieces["parts"] for _ in range(int(p.get("qty", 1)))]
    _ref.update(data={"bins": bins, "slot_of": slot_of, "swatch": swatch, "pool": pool}, at=time.time())
    return _ref["data"]


# ---------- ingest from CT 150 ----------

def token_ok(header: str, name: str = "BRICKED_LIVE_TOKEN") -> bool:
    want = core.env(name)
    if len(want) < 24 or not header.startswith("Bearer "):
        return False
    a = hashlib.sha256(header[7:].strip().encode()).digest()
    b = hashlib.sha256(want.encode()).digest()
    return hmac.compare_digest(a, b)


def thumbnail(b64: str) -> bytes:
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(400, "image is not base64")
    if len(raw) > MAX_IMAGE_IN:
        raise HTTPException(413, "image too large")
    try:
        im = Image.open(io.BytesIO(raw))
        if im.format != "JPEG":
            raise ValueError("not jpeg")
        im.load()
        im = im.convert("RGB")
        im.thumbnail((THUMB, THUMB))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=75)  # fresh file: no metadata, nothing but pixels
        return out.getvalue()
    except Exception:
        raise HTTPException(400, "image must be a JPEG photo")


def as_int(v, lo, hi):
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def to_hex(v) -> str | None:
    """CT 150 sends rgb as [r, g, b], "r,g,b" or "#rrggbb"; the page wants "#rrggbb"."""
    if isinstance(v, str):
        t = v.strip()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", t):
            return t.lower()
        v = [x for x in re.split(r"[\s,]+", t.strip("()[]")) if x]
    if isinstance(v, (list, tuple)) and len(v) == 3:
        try:
            r, g, b = (int(float(x)) for x in v)
        except (TypeError, ValueError):
            return None
        if all(0 <= x <= 255 for x in (r, g, b)):
            return f"#{r:02x}{g:02x}{b:02x}"
    return None


def confidence(v) -> float | None:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v > 1:
        v /= 100  # CT 150 reports percent
    return round(min(max(v, 0.0), 1.0), 3)


@router.post("/live/event")
async def live_event(request: Request):
    need_enabled()
    if not token_ok(request.headers.get("authorization", "")):
        raise HTTPException(401, "bad token")
    if core.LIMITS.over("live:ingest", INGEST_LIMIT, INGEST_WINDOW):
        raise HTTPException(429, "slow down")
    size = int(request.headers.get("content-length") or 0)
    if size > MAX_BODY:
        raise HTTPException(413, "too large")
    body = await request.body()
    if len(body) > MAX_BODY:
        raise HTTPException(413, "too large")
    try:
        data = json.loads(body)
        assert isinstance(data, dict)
    except Exception:
        raise HTTPException(400, "send JSON")
    core.LIMITS.add("live:ingest")

    if str(data.get("bin", "")).upper() == "NO_LEGO" or not data.get("lego_detected", True):
        return {"ok": True, "ignored": "no piece"}
    floor, slot = as_int(data.get("floor"), 1, 2), as_int(data.get("slot"), 1, 8)
    if floor is None or slot is None:
        raise HTTPException(400, "floor must be 1-2 and slot 1-8")
    image = await asyncio.to_thread(thumbnail, data["image_b64"]) if data.get("image_b64") else None
    evt = HUB.add({
        "source": "live", "code": f"{floor}-{slot}", "floor": floor, "slot": slot,
        "name": core.clean(data.get("name", ""), 80), "color": core.clean(data.get("color", ""), 40),
        "part_id": core.clean(data.get("part_id", ""), 20), "confidence": confidence(data.get("confidence")),
        "category": core.clean(data.get("category", ""), 40), "shape": core.clean(data.get("shape", ""), 40),
        "color_confidence": confidence(data.get("color_confidence")), "hex": to_hex(data.get("rgb")),
    }, image)
    return {"ok": True, "id": evt["id"], "code": evt["code"]}


# ---------- bin switches from the Pi ----------

class Bins(BaseModel):
    open: list[str] = []
    drawers_open: list[str] = []


@router.post("/live/bins")
def live_bins(body: Bins, request: Request):
    """Full list of bins that are open right now (switch released). Send on every change
    and at least every 30 s, so the page can tell the switches are still reporting."""
    need_enabled()
    if not token_ok(request.headers.get("authorization", ""), "BRICKED_BINS_TOKEN"):
        raise HTTPException(401, "bad token")
    if core.LIMITS.over("live:bins", BINS_LIMIT, BINS_WINDOW):
        raise HTTPException(429, "slow down")
    if len(body.open) > 32 or len(body.drawers_open) > 2:
        raise HTTPException(400, "too many")
    codes = [str(c).strip().upper() for c in body.open]
    bad = [c for c in codes if not BIN_CODE.match(c)]
    if bad:
        raise HTTPException(400, "bin codes look like 1-3 (or F3 / B3)")
    drawers = [str(d).strip().lower() for d in body.drawers_open]
    if any(d not in DRAWERS for d in drawers):
        raise HTTPException(400, "drawers are front or back")
    core.LIMITS.add("live:bins")
    HUB.set_bins(codes, drawers)
    return {"ok": True, **HUB.bins_state()}


# ---------- readers (website and Marshall's bridge) ----------

@router.get("/live/state")
def live_state():
    need_enabled()
    return JSONResponse(HUB.state(), headers=NO_STORE)


@router.get("/live/events")
async def live_events(after: int = 0, wait: int = 0):
    need_enabled()
    wait = max(0, min(int(wait), WAIT_MAX))

    def reply(found, **extra):
        return JSONResponse({"events": found, "last_id": HUB.next_id - 1, "mode": HUB.mode(),
                             "bins": HUB.bins_state(), **extra}, headers=NO_STORE)

    found = HUB.after(after)
    if found or not wait:
        return reply(found)
    if HUB.waiters >= MAX_WAITERS:
        return reply([], busy=True)
    HUB.waiters += 1
    rev, on = HUB.bins_rev, HUB.sensors_on()
    try:
        end = time.time() + wait
        while time.time() < end:
            await asyncio.sleep(0.25)
            found = HUB.after(after)
            if found or HUB.bins_rev != rev or HUB.sensors_on() != on:   # a bin opened or closed
                break
    finally:
        HUB.waiters -= 1
    return reply(found)


@router.get("/live/img/{event_id}.jpg")
def live_img(event_id: int):
    need_enabled()
    img = HUB.images.get(event_id)
    if img is None:
        raise HTTPException(404, "no image")
    return Response(img, media_type="image/jpeg",
                    headers={**NO_STORE, "X-Content-Type-Options": "nosniff"})


# ---------- simulator ----------

def sim_piece() -> dict:
    r = ref()
    p = random.choice(r["pool"])
    group = r["bins"]["colorMap"].get(p["color"], "unknown")
    if group != "unknown" and random.random() < 0.03:  # camera misreads go to slot 8
        group = "unknown"
    floor = 1 if p.get("brick") else 2
    slot = r["slot_of"][group]
    return {"source": "sim", "code": f"{floor}-{slot}", "floor": floor, "slot": slot,
            "name": core.clean(p.get("part", ""), 80), "color": core.clean(p.get("color", ""), 40),
            "part_id": "", "confidence": round(random.uniform(0.6, 0.98), 2), "hex": p.get("hex"),
            "category": "Brick" if p.get("brick") else "Other", "shape": "",
            "color_confidence": round(random.uniform(0.7, 0.99), 2)}


def sim_loop(run_token: int):
    while True:
        with HUB.lock:
            s = HUB.sim
            if not s["running"] or s["token"] != run_token:
                return
            if time.time() >= s["until"]:
                s.update(running=False)
                return
            delay = 1.0 / s["rate"]
        try:
            HUB.add(sim_piece())
        except Exception as e:  # bad reference data: stop rather than spin
            core.log.warning("sim stopped: %s", e)
            with HUB.lock:
                HUB.sim.update(running=False)
            return
        time.sleep(delay)


class Control(BaseModel):
    name: str
    password: str
    action: str
    rate: float = 0.5
    minutes: float = 5
    code: str = ""      # bin code, only for "recounted"


def control_gate(request: Request, body: Control) -> str:
    """Same team password and lockout as the task buttons, with its own on/off flag."""
    if core.env("BRICKED_SIM_CONTROL") != "1" or not core.CFG.password_hash:
        raise HTTPException(503, "Simulation control is turned off.")
    who = "site:" + core.visitor(request)
    if core.LIMITS.over(who + ":fail", core.FAIL_LIMIT, core.FAIL_WINDOW):
        raise HTTPException(429, "Too many wrong tries. Wait 10 minutes.")
    given = hashlib.sha256(body.password.encode()).hexdigest()
    if not hmac.compare_digest(given, core.CFG.password_hash):
        core.LIMITS.add(who + ":fail")
        raise HTTPException(401, "Wrong team password.")
    name = core.clean(body.name, 70)
    if name not in core.CFG.names:
        raise HTTPException(400, "Pick your name from the list.")
    if core.LIMITS.over(who + ":control", 20, 600):
        raise HTTPException(429, "Too many changes. Wait a few minutes.")
    core.LIMITS.add(who + ":control")
    return name


@router.post("/live/control")
def live_control(body: Control, request: Request, bg: BackgroundTasks):
    need_enabled()
    name = control_gate(request, body)
    act = body.action
    if act == "start":
        ref()  # fail now, not inside the thread, if the piece list can't load
        rate = min(max(float(body.rate), 0.1), SIM_MAX_RATE)
        secs = min(max(float(body.minutes), 0.5) * 60, SIM_MAX_SECONDS)
        with HUB.lock:
            tok = HUB.sim["token"] + 1
            HUB.sim.update(running=True, until=time.time() + secs, rate=rate, by=name, token=tok)
            HUB.counts["sim"] = {}
        threading.Thread(target=sim_loop, args=(tok,), daemon=True).start()
        text = f"**{name}** started the simulator ({rate:g} pieces/s, {secs / 60:g} min) on the Live page"
    elif act == "stop":
        with HUB.lock:
            HUB.sim.update(running=False)
        text = f"**{name}** stopped the simulator"
    elif act == "recounted":
        # One bin was poured back into the hopper: clear its Recount flag and zero its count,
        # so the pieces are counted again as they come back through. Other bins keep their counts.
        code = body.code.strip().upper()
        if not BIN_CODE.match(code):
            raise HTTPException(400, "bin codes look like 1-3 (or F3 / B3)")
        with HUB.lock:
            if code in HUB.open:
                raise HTTPException(409, f"Bin {code} is still open. Put it back first.")
            if code not in HUB.recount:
                raise HTTPException(409, f"Bin {code} doesn't need a recount.")
            HUB.recount.discard(code)
            HUB.counts["live"].pop(code, None)
            HUB.bins_rev += 1
        text = f"**{name}** recounted bin {code} on the Live page"
    elif act == "reset":
        with HUB.lock:
            HUB.counts = {"live": {}, "sim": {}}
            if HUB.recount:
                HUB.recount = set()
                HUB.bins_rev += 1
        text = f"**{name}** reset the Live bin counts"
    else:
        raise HTTPException(400, "action must be start, stop, reset or recounted")
    bg.add_task(core.post_feed, text)
    return {"ok": True, **HUB.state()["sim"]}
