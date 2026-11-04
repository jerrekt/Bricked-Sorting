"""Tests with a fake Discord signer and a fake webhook. No network."""
import hashlib
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from nacl.signing import SigningKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as appmod  # noqa: E402

KEY = SigningKey.generate()
IDS = {"Branden": "111", "Ethan": "222", "Marshall": "333"}
PW = "test-only-pass"
HOOK = "https://discord.com/api/webhooks/0/test"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    seed = {"note": "n", "milestone_labels": {"identify": "Identify"}, "tasks": [
        {"id": "identify-02", "milestone": "identify", "title": "Pi camera", "status": "in_progress", "owner": "Ethan"},
        {"id": "open-01", "milestone": "identify", "title": "Nobody owns this", "status": "todo", "owner": ""},
        {"id": "team-01", "milestone": "identify", "title": "Everyone", "status": "todo", "owner": "All", "due": "2026-12-06"},
        {"id": "done-01", "milestone": "identify", "title": "Finished", "status": "done", "owner": "Branden"},
    ]}
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps(seed))
    monkeypatch.setenv("BRICKED_SEED_PATH", str(p))
    monkeypatch.setenv("BRICKED_DB", str(tmp_path / "c.db"))
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", KEY.verify_key.encode().hex())
    monkeypatch.setenv("DISCORD_USERS", ",".join(f"{v}:{k}" for k, v in IDS.items()))
    monkeypatch.setenv("BRICKED_SITE_NAMES", "Branden,Ethan,Marshall,Vivek")
    monkeypatch.setenv("BRICKED_TEAM_PASSWORD_SHA256", hashlib.sha256(PW.encode()).hexdigest())
    monkeypatch.setenv("BRICKED_SITE_WRITES", "1")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", HOOK)
    appmod._seed.update(data=None, at=0)
    appmod.LIMITS.reset()
    posts = []
    monkeypatch.setattr(appmod.httpx, "post", lambda url, json=None, timeout=None: posts.append((url, json)))
    c = TestClient(appmod.app)
    c.posts = posts
    c.seed_path = p
    return c


def discord(c, name, cmd, ts=None, sig_key=KEY, **opts):
    body = json.dumps({"type": 2, "member": {"user": {"id": IDS.get(name, "999")}},
                       "data": {"name": cmd, "options": [{"name": k, "value": v} for k, v in opts.items()]}}).encode()
    ts = str(int(time.time()) if ts is None else ts)
    sig = sig_key.sign(ts.encode() + body).signature.hex()
    return c.post("/discord/interactions", content=body,
                  headers={"x-signature-ed25519": sig, "x-signature-timestamp": ts, "content-type": "application/json"})


def site(c, task, action, name="Marshall", pw=PW, ip="1.1.1.1", **extra):
    return c.post(f"/api/tasks/{task}/{action}", json={"name": name, "password": pw, **extra},
                  headers={"cf-connecting-ip": ip})


def task(c, tid):
    return next(t for t in c.get("/api/tasks").json()["tasks"] if t["id"] == tid)


# ---- Discord security ----

def test_ping_needs_valid_signature(client):
    body = b'{"type":1}'
    ts = str(int(time.time()))
    good = KEY.sign(ts.encode() + body).signature.hex()
    r = client.post("/discord/interactions", content=body, headers={"x-signature-ed25519": good, "x-signature-timestamp": ts})
    assert r.json() == {"type": 1}
    bad = SigningKey.generate().sign(ts.encode() + body).signature.hex()
    r = client.post("/discord/interactions", content=body, headers={"x-signature-ed25519": bad, "x-signature-timestamp": ts})
    assert r.status_code == 401


def test_stale_timestamp_rejected(client):
    assert discord(client, "Ethan", "mytasks", ts=int(time.time()) - 1000).status_code == 401


def test_unknown_discord_user_refused(client):
    r = discord(client, "Stranger", "claim", task="open-01")
    assert "not on the Bricked Sorting team" in r.json()["data"]["content"]
    assert task(client, "open-01")["owner"] == ""


def test_team_and_admin_names_from_env(client, monkeypatch):
    # A second instance (another team) sets its own names; defaults stay Bricked Sorting / Branden.
    monkeypatch.setenv("BOT_TEAM_NAME", "Ain't No Waymo")
    monkeypatch.setenv("BRICKED_ADMIN", "Ethan")
    r = discord(client, "Stranger", "mytasks")
    assert "not on the Ain't No Waymo team list. Ask Ethan" in r.json()["data"]["content"]
    assert "Only Ethan" in discord(client, "Marshall", "export").json()["data"]["content"]
    discord(client, "Marshall", "claim", task="open-01")
    assert "or Ethan can" in discord(client, "Branden", "claim", task="open-01").json()["data"]["content"]


# ---- ownership rules ----

def test_claim_unowned_then_feed(client):
    r = discord(client, "Marshall", "claim", task="open-01")
    assert r.json()["data"]["flags"] == 64
    t = task(client, "open-01")
    assert (t["owner"], t["status"]) == ("Marshall", "in_progress")
    url, payload = client.posts[-1]
    assert url == HOOK and payload["allowed_mentions"] == {"parse": []}
    assert "Marshall" in payload["content"] and "via Discord" in payload["content"]


def test_team_task_owned_by_all_is_claimable(client):
    discord(client, "Ethan", "claim", task="team-01")
    assert task(client, "team-01")["owner"] == "Ethan"


def test_cannot_claim_someone_elses(client):
    r = discord(client, "Marshall", "claim", task="identify-02")
    assert "owned by Ethan" in r.json()["data"]["content"]
    assert task(client, "identify-02")["owner"] == "Ethan"


def test_cannot_claim_done(client):
    r = discord(client, "Marshall", "claim", task="done-01")
    assert "already done" in r.json()["data"]["content"]


def test_only_owner_changes_status(client):
    r = discord(client, "Marshall", "done", task="identify-02")
    assert "Only Ethan" in r.json()["data"]["content"]
    discord(client, "Ethan", "done", task="identify-02")
    assert task(client, "identify-02")["status"] == "done"


def test_admin_override_on_discord(client):
    discord(client, "Branden", "release", task="identify-02")
    t = task(client, "identify-02")
    assert (t["owner"], t["status"]) == ("", "todo")


def test_blocked_reason_kept_and_cleaned(client):
    discord(client, "Ethan", "blocked", task="identify-02", reason="waiting @everyone\n" + "x" * 500)
    t = task(client, "identify-02")
    assert t["status"] == "blocked" and len(t["note"]) <= 200 and "\n" not in t["note"]
    assert client.posts[-1][1]["allowed_mentions"] == {"parse": []}


def test_release_then_other_claims(client):
    discord(client, "Ethan", "release", task="identify-02")
    discord(client, "Marshall", "claim", task="identify-02")
    assert task(client, "identify-02")["owner"] == "Marshall"


def test_mytasks_and_tasks(client):
    r = discord(client, "Ethan", "mytasks")
    assert "identify-02" in r.json()["data"]["content"]
    r = discord(client, "Ethan", "tasks")
    content = r.json()["data"]["content"]
    assert "done-01" not in content and "open-01" in content


def test_export_admin_only(client):
    discord(client, "Marshall", "claim", task="open-01")
    assert "Only Branden" in discord(client, "Ethan", "export").json()["data"]["content"]
    assert '"open-01"' in discord(client, "Branden", "export").json()["data"]["content"]


def test_unknown_task(client):
    assert "No task called" in discord(client, "Ethan", "claim", task="nope-99").json()["data"]["content"]


# ---- seed stays the source of truth ----

def test_seed_edits_show_up_and_overlay_survives(client):
    discord(client, "Marshall", "claim", task="open-01")
    seed = json.loads(client.seed_path.read_text())
    seed["tasks"][1]["title"] = "Renamed in git"
    seed["tasks"].append({"id": "new-01", "milestone": "identify", "title": "Added later", "status": "todo", "owner": ""})
    client.seed_path.write_text(json.dumps(seed))
    appmod._seed.update(at=0)  # let the cache expire
    t = task(client, "open-01")
    assert t["title"] == "Renamed in git" and t["owner"] == "Marshall"
    assert task(client, "new-01")["title"] == "Added later"


# ---- website writes ----

def test_site_claim_and_feed_says_site(client):
    r = site(client, "open-01", "claim")
    assert r.status_code == 200
    assert "via site" in client.posts[-1][1]["content"]


def test_site_wrong_password_and_lockout(client):
    for _ in range(8):
        assert site(client, "open-01", "claim", pw="wrong").status_code == 401
    assert site(client, "open-01", "claim").status_code == 429          # locked even with the right one
    assert site(client, "open-01", "claim", ip="2.2.2.2").status_code == 200  # other visitors unaffected


def test_site_name_must_be_on_list(client):
    assert site(client, "open-01", "claim", name="Mallory").status_code == 400


def test_site_has_no_admin_override(client):
    r = site(client, "identify-02", "release", name="Branden")
    assert r.status_code == 403


def test_site_status_rules(client):
    assert site(client, "identify-02", "status", name="Marshall", status="done").status_code == 403
    assert site(client, "identify-02", "status", name="Ethan", status="nonsense").status_code == 400
    assert site(client, "identify-02", "status", name="Ethan", status="done").status_code == 200


def test_site_writes_off_by_flag(client, monkeypatch):
    monkeypatch.setenv("BRICKED_SITE_WRITES", "0")
    assert site(client, "open-01", "claim").status_code == 503
    data = client.get("/api/tasks").json()
    assert data["writes"] is False and data["names"] == []


def test_site_writes_off_without_password(client, monkeypatch):
    monkeypatch.delenv("BRICKED_TEAM_PASSWORD_SHA256")
    assert site(client, "open-01", "claim").status_code == 503


def test_api_tasks_no_store_and_no_secrets(client):
    r = client.get("/api/tasks")
    assert r.headers["cache-control"] == "no-store"
    text = r.text
    assert PW not in text and HOOK not in text and "111" not in text


def test_bad_webhook_url_never_called(client, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://evil.example/hook")
    site(client, "open-01", "claim")
    assert client.posts == []


def test_cors_only_site_origin(client):
    r = client.options("/api/tasks", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"
    r = client.options("/api/tasks", headers={"Origin": "https://bricked-01.adsuaracloud.com", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "https://bricked-01.adsuaracloud.com"


def test_old_discordapp_webhook_host_accepted(client, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discordapp.com/api/webhooks/0/test")
    site(client, "open-01", "claim")
    assert client.posts and client.posts[-1][0].startswith("https://discordapp.com/api/webhooks/")


def test_lookalike_webhook_host_rejected(client, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com.evil.example/api/webhooks/0/x")
    site(client, "open-01", "claim")
    assert client.posts == []


# ---- parts (Build page bought flags) ----

def parts_on(client, monkeypatch, tmp_path):
    seed = {"versions": {"v1": {"name": "V1"}}, "parts": [
        {"id": "esp32-s3-sense", "part": "XIAO ESP32-S3 Sense", "versions": "both", "bought": False},
        {"id": "waymo-shell", "part": "Waymo shell", "versions": "both", "bought": True},
    ]}
    p = tmp_path / "parts.json"
    p.write_text(json.dumps(seed))
    monkeypatch.setenv("BOT_PARTS_PATH", str(p))
    appmod._parts.update(data=None, at=0)


def mark(c, part, bought=True, name="Marshall", pw=PW, ip="1.1.1.1"):
    return c.post(f"/api/parts/{part}", json={"name": name, "password": pw, "bought": bought},
                  headers={"cf-connecting-ip": ip})


def test_parts_off_by_default(client, monkeypatch):
    monkeypatch.delenv("BOT_PARTS_PATH", raising=False)
    monkeypatch.delenv("BOT_PARTS_URL", raising=False)
    appmod._parts.update(data=None, at=0)
    assert client.get("/api/parts").status_code == 404
    assert mark(client, "waymo-shell").status_code == 404
    assert "Parts bought" not in discord(client, "Branden", "export").json()["data"]["content"]


def test_parts_mark_bought_live_and_feed(client, monkeypatch, tmp_path):
    parts_on(client, monkeypatch, tmp_path)
    data = client.get("/api/parts").json()
    assert data["writes"] is True and "Marshall" in data["names"] and data["versions"]["v1"]["name"] == "V1"
    r = mark(client, "esp32-s3-sense", True)
    assert r.status_code == 200, r.text
    p = next(x for x in client.get("/api/parts").json()["parts"] if x["id"] == "esp32-s3-sense")
    assert p["bought"] is True and p["bought_by"] == "Marshall"
    assert "marked bought `esp32-s3-sense`" in client.posts[-1][1]["content"]
    assert client.posts[-1][1]["allowed_mentions"] == {"parse": []}
    assert mark(client, "waymo-shell", False).status_code == 200
    assert "marked not bought" in client.posts[-1][1]["content"]
    out = discord(client, "Branden", "export").json()["data"]["content"]
    assert '"esp32-s3-sense": true' in out and '"waymo-shell": false' in out


def test_parts_same_gate_as_site_claims(client, monkeypatch, tmp_path):
    parts_on(client, monkeypatch, tmp_path)
    assert mark(client, "nope-99").status_code == 404
    assert mark(client, "waymo-shell", name="Mallory").status_code == 400
    for _ in range(8):
        assert mark(client, "waymo-shell", pw="wrong").status_code == 401
    assert mark(client, "waymo-shell").status_code == 429
    assert client.post("/api/parts/waymo-shell", json={"name": "Ethan", "password": PW, "bought": "maybe"},
                       headers={"cf-connecting-ip": "3.3.3.3"}).status_code == 422
    monkeypatch.setenv("BRICKED_SITE_WRITES", "0")
    assert mark(client, "waymo-shell", ip="4.4.4.4").status_code == 503
    assert client.get("/api/parts").json()["writes"] is False


# ---- parts from Discord ----

def test_discord_parts_list_and_mark(client, monkeypatch, tmp_path):
    parts_on(client, monkeypatch, tmp_path)
    out = discord(client, "Ethan", "parts").json()["data"]
    assert out["flags"] == 64 and "esp32-s3-sense" in out["content"] and "waymo-shell" not in out["content"]
    assert "waymo-shell" in discord(client, "Ethan", "parts", show="have").json()["data"]["content"]
    r = discord(client, "Ethan", "bought", part="ESP32-S3-Sense").json()["data"]["content"]
    assert r.startswith("Done:") and "have it (Ethan)" in r
    assert "marked bought `esp32-s3-sense`" in client.posts[-1][1]["content"] and "via Discord" in client.posts[-1][1]["content"]
    assert discord(client, "Ethan", "parts").json()["data"]["content"] == "Nothing left to buy."
    discord(client, "Marshall", "notbought", part="waymo-shell")
    p = next(x for x in client.get("/api/parts").json()["parts"] if x["id"] == "waymo-shell")
    assert p["bought"] is False and p["bought_by"] == "Marshall"
    assert "No part called nope-99" in discord(client, "Ethan", "bought", part="nope-99").json()["data"]["content"]


def test_discord_parts_gated(client, monkeypatch, tmp_path):
    monkeypatch.delenv("BOT_PARTS_PATH", raising=False)
    monkeypatch.delenv("BOT_PARTS_URL", raising=False)
    appmod._parts.update(data=None, at=0)
    assert "not set up" in discord(client, "Ethan", "parts").json()["data"]["content"]
    assert "not set up" in discord(client, "Ethan", "bought", part="x").json()["data"]["content"]
    parts_on(client, monkeypatch, tmp_path)
    assert "not on the" in discord(client, "Mallory", "bought", part="waymo-shell").json()["data"]["content"]
    assert client.posts == []


def test_parts_extra_keys_pass_through(client, monkeypatch, tmp_path):
    seed = {"_note": "secret-ish", "stage_labels": {"identify": "Identify"}, "parts": [
        {"id": "apds9960", "part": "Color sensor", "stage": "identify", "versions": "all", "bought": False, "qty": "1", "price": "~$2"}]}
    p = tmp_path / "parts.json"
    p.write_text(json.dumps(seed))
    monkeypatch.setenv("BOT_PARTS_PATH", str(p))
    appmod._parts.update(data=None, at=0)
    data = client.get("/api/parts").json()
    assert data["stage_labels"] == {"identify": "Identify"} and data["versions"] == {} and "_note" not in data
    assert "· 1 · ~$2" in discord(client, "Ethan", "parts").json()["data"]["content"]


def test_real_bricked_parts_file_is_valid():
    data = json.loads((Path(__file__).resolve().parents[3] / "web" / "data" / "build_parts.json").read_text())
    ids = [p["id"] for p in data["parts"]]
    assert len(ids) == len(set(ids)) and all(len(i) <= 40 and i == i.lower() for i in ids)
    assert all(isinstance(p["bought"], bool) and p["stage"] in data["stage_labels"] for p in data["parts"])
    assert all(p["versions"] in ("all", "v1", "v2", "v3", "v1+v2") for p in data["parts"])
    assert all(not p["link"] or p["link"].startswith("https://") for p in data["parts"])
