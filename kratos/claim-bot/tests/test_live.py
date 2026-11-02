"""Live page tests: token-gated ingest, image re-encoding, readers, simulator. No network."""
import base64
import hashlib
import io
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as appmod  # noqa: E402
import live  # noqa: E402

TOKEN = "t" * 32
PW = "test-only-pass"
ROOT = Path(__file__).resolve().parents[3]  # repo root (web/data has the real bins and piece list)


def jpeg(w=640, h=480, exif=True) -> bytes:
    im = Image.new("RGB", (w, h), (200, 30, 30))
    out = io.BytesIO()
    kw = {"exif": b"Exif\x00\x00" + b"\x00" * 20} if exif else {}
    im.save(out, "JPEG", **kw)
    return out.getvalue()


@pytest.fixture()
def c(tmp_path, monkeypatch):
    monkeypatch.setenv("BRICKED_LIVE_ENABLED", "1")
    monkeypatch.setenv("BRICKED_LIVE_TOKEN", TOKEN)
    monkeypatch.setenv("BRICKED_SIM_CONTROL", "1")
    monkeypatch.setenv("BRICKED_TEAM_PASSWORD_SHA256", hashlib.sha256(PW.encode()).hexdigest())
    monkeypatch.setenv("BRICKED_SITE_NAMES", "Branden,Ethan,Marshall,Vivek")
    monkeypatch.setenv("BRICKED_DATA_DIR", str(ROOT / "web" / "data"))
    monkeypatch.setenv("BRICKED_DB", str(tmp_path / "c.db"))
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/0/test")
    live.HUB.reset_all()
    live._ref.update(data=None, at=0)
    appmod.LIMITS.reset()
    posts = []
    monkeypatch.setattr(appmod.httpx, "post", lambda url, json=None, timeout=None: posts.append(json))
    client = TestClient(appmod.app)
    client.posts = posts
    yield client
    with live.HUB.lock:
        live.HUB.sim.update(running=False)


def send(c, body, token=TOKEN):
    return c.post("/live/event", content=json.dumps(body),
                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


RESULT = {"name": "Brick 2 x 4", "part_id": "3001", "color": "Blue", "confidence": 87.5,
          "bin": "BRICK_BLUE", "bin_number": 4, "floor": 1, "slot": 4}


def test_off_unless_enabled(c, monkeypatch):
    monkeypatch.setenv("BRICKED_LIVE_ENABLED", "0")
    assert c.get("/live/state").status_code == 404
    assert send(c, RESULT).status_code == 404


def test_ingest_needs_token(c):
    assert send(c, RESULT, token="wrong" * 8).status_code == 401
    assert c.post("/live/event", json=RESULT).status_code == 401


def test_short_server_token_disables_ingest(c, monkeypatch):
    monkeypatch.setenv("BRICKED_LIVE_TOKEN", "short")
    assert send(c, RESULT, token="short").status_code == 401


def test_ingest_result_shows_in_state(c):
    r = send(c, RESULT)
    assert r.status_code == 200 and r.json()["code"] == "1-4"
    s = c.get("/live/state").json()
    e = s["events"][-1]
    assert e["source"] == "live" and e["confidence"] == 0.875 and e["name"] == "Brick 2 x 4"
    assert s["counts"]["live"] == {"1-4": 1} and s["mode"] == "live"


def test_no_lego_ignored(c):
    r = send(c, {"bin": "NO_LEGO", "bin_number": 0, "lego_detected": False})
    assert r.json()["ignored"] and c.get("/live/state").json()["events"] == []


def test_bad_floor_slot_rejected(c):
    assert send(c, dict(RESULT, floor=3)).status_code == 400
    assert send(c, dict(RESULT, slot=9)).status_code == 400
    assert send(c, dict(RESULT, slot="x")).status_code == 400


def test_text_cleaned(c):
    send(c, dict(RESULT, name="A\nB" + "x" * 300))
    e = c.get("/live/state").json()["events"][-1]
    assert "\n" not in e["name"] and len(e["name"]) <= 80


def test_image_reencoded_small_and_clean(c):
    r = send(c, dict(RESULT, image_b64=base64.b64encode(jpeg()).decode()))
    eid = r.json()["id"]
    img = c.get(f"/live/img/{eid}.jpg")
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"
    assert img.headers["x-content-type-options"] == "nosniff"
    im = Image.open(io.BytesIO(img.content))
    assert max(im.size) <= 320 and "exif" not in im.info


def test_non_jpeg_and_garbage_rejected(c):
    png = io.BytesIO()
    Image.new("RGB", (10, 10)).save(png, "PNG")
    assert send(c, dict(RESULT, image_b64=base64.b64encode(png.getvalue()).decode())).status_code == 400
    assert send(c, dict(RESULT, image_b64=base64.b64encode(b"<script>").decode())).status_code == 400
    assert send(c, dict(RESULT, image_b64="not base64!!")).status_code == 400


def test_too_big_rejected(c):
    big = base64.b64encode(b"\xff" * 400_000).decode()
    assert send(c, dict(RESULT, image_b64=big)).status_code == 413


def test_only_last_images_kept(c):
    b64 = base64.b64encode(jpeg(80, 60)).decode()
    ids = [send(c, dict(RESULT, image_b64=b64)).json()["id"] for _ in range(live.KEEP_IMAGES + 3)]
    assert c.get(f"/live/img/{ids[0]}.jpg").status_code == 404
    assert c.get(f"/live/img/{ids[-1]}.jpg").status_code == 200


def test_events_after_and_long_poll(c):
    first = send(c, RESULT).json()["id"]
    send(c, dict(RESULT, floor=2, slot=8))
    r = c.get(f"/live/events?after={first}").json()
    assert [e["code"] for e in r["events"]] == ["2-8"]
    t = time.time()
    r = c.get(f"/live/events?after={r['last_id']}&wait=1").json()
    assert r["events"] == [] and 0.9 < time.time() - t < 3


def control(c, action, pw=PW, **kw):
    return c.post("/live/control", json={"name": "Marshall", "password": pw, "action": action, **kw},
                  headers={"cf-connecting-ip": "9.9.9.9"})


def test_sim_needs_password_and_flag(c, monkeypatch):
    assert control(c, "start", pw="nope").status_code == 401
    monkeypatch.setenv("BRICKED_SIM_CONTROL", "0")
    assert control(c, "start").status_code == 503


def test_sim_runs_labels_and_stops(c):
    r = control(c, "start", rate=2, minutes=1)
    assert r.status_code == 200 and r.json()["running"]
    time.sleep(1.3)
    evs = c.get("/live/state").json()["events"]
    assert evs and all(e["source"] == "sim" for e in evs)
    for e in evs:
        f, s = map(int, e["code"].split("-"))
        assert f in (1, 2) and 1 <= s <= 8 and (f, s) == (e["floor"], e["slot"])
    assert control(c, "stop").json()["running"] is False
    n = len(c.get("/live/state").json()["events"])
    time.sleep(0.8)
    assert len(c.get("/live/state").json()["events"]) == n
    assert any("started the simulator" in p["content"] for p in c.posts)


def test_sim_rate_and_time_capped(c):
    r = control(c, "start", rate=50, minutes=999).json()
    assert r["rate"] == live.SIM_MAX_RATE and r["until"] - time.time() <= live.SIM_MAX_SECONDS + 1


def test_sim_maps_bricks_to_floor_1(c):
    data = live.ref()
    floor_of = {}
    for p in data["pool"]:
        floor_of.setdefault(appmod.clean(p["part"], 80), set()).add(1 if p.get("brick") else 2)
    for _ in range(300):
        e = live.sim_piece()
        assert e["floor"] in floor_of[e["name"]]


def test_reset_counts(c):
    send(c, RESULT)
    control(c, "reset")
    assert c.get("/live/state").json()["counts"] == {"live": {}, "sim": {}}


def test_wrong_passwords_share_lockout_with_task_buttons(c):
    for _ in range(appmod.FAIL_LIMIT):
        control(c, "start", pw="nope")
    assert control(c, "start").status_code == 429
