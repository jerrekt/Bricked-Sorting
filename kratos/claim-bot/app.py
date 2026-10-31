"""Bricked Sorting claim server.

Teammates claim and update tasks from Discord (slash commands) or from the
Tasks page on the website. tasks.json on GitHub stays the source for titles,
details, due dates and new tasks. This server only stores who owns each task
and its status, and merges that over tasks.json when anyone reads the board.

Every setting comes from environment variables (see deploy/bots/bot.env.example).
No secret is ever written in this repo.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel

log = logging.getLogger("claim-bot")

STATUSES = ("todo", "in_progress", "blocked", "done")
STATUS_WORD = {"todo": "to do", "in_progress": "in progress", "blocked": "blocked", "done": "done"}
SEED_TTL = 60          # seconds between fetches of tasks.json
MAX_NOTE = 200         # characters kept from a "blocked" reason
DISCORD_MAX_AGE = 300  # seconds; older signed requests are rejected
WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class Config:
    """Read once per call so tests can change the environment."""

    @property
    def seed_url(self): return env("BRICKED_SEED_URL", "https://raw.githubusercontent.com/jerrekt/Bricked-Sorting/main/web/data/tasks.json")
    @property
    def seed_path(self): return env("BRICKED_SEED_PATH")
    @property
    def db_path(self): return env("BRICKED_DB", "claims.db")
    @property
    def discord_key(self): return env("DISCORD_PUBLIC_KEY")
    @property
    def admin(self): return env("BRICKED_ADMIN", "Branden")
    @property
    def webhook(self): return env("DISCORD_WEBHOOK_URL")
    @property
    def password_hash(self): return env("BRICKED_TEAM_PASSWORD_SHA256").lower()
    @property
    def site_writes(self): return env("BRICKED_SITE_WRITES") == "1"
    @property
    def origin(self): return env("BRICKED_ALLOWED_ORIGIN", "https://bricked-01.adsuaracloud.com")

    @property
    def discord_users(self) -> dict[str, str]:
        """DISCORD_USERS="1234:Branden,5678:Ethan" -> {"1234": "Branden", ...}"""
        out = {}
        for pair in env("DISCORD_USERS").split(","):
            if ":" in pair:
                uid, name = pair.split(":", 1)
                if uid.strip().isdigit() and name.strip():
                    out[uid.strip()] = name.strip()
        return out

    @property
    def names(self) -> list[str]:
        raw = env("BRICKED_SITE_NAMES")
        if raw:
            return [n.strip() for n in raw.split(",") if n.strip()]
        return sorted(set(self.discord_users.values()))


CFG = Config()


# ---------- text and limits ----------

def clean(text: str, limit: int) -> str:
    """Drop control characters, squash whitespace, cap length."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


class Limiter:
    """In-memory sliding-window counter. Fine for one process."""

    def __init__(self):
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def count(self, key: str, window: float) -> int:
        now = time.time()
        with self.lock:
            q = self.hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            return len(q)

    def add(self, key: str):
        with self.lock:
            self.hits[key].append(time.time())

    def over(self, key: str, limit: int, window: float) -> bool:
        return self.count(key, window) >= limit

    def reset(self):
        with self.lock:
            self.hits.clear()


LIMITS = Limiter()
FAIL_LIMIT, FAIL_WINDOW = 8, 600        # wrong team passwords per visitor
WRITE_LIMIT, WRITE_WINDOW = 30, 600     # changes per visitor or Discord user
FEED_LIMIT, FEED_WINDOW = 120, 3600     # posts to the Discord channel, all sources


# ---------- seed (tasks.json) ----------

_seed = {"data": None, "at": 0.0}
_seed_lock = threading.Lock()


def load_seed(force: bool = False) -> dict:
    with _seed_lock:
        fresh = _seed["data"] is not None and time.time() - _seed["at"] < SEED_TTL
        if fresh and not force:
            return _seed["data"]
        try:
            if CFG.seed_path:
                data = json.loads(Path(CFG.seed_path).read_text())
            else:
                r = httpx.get(CFG.seed_url, timeout=2.5)
                r.raise_for_status()
                data = r.json()
            if not isinstance(data.get("tasks"), list):
                raise ValueError("tasks.json has no task list")
            _seed.update(data=data, at=time.time())
        except Exception as e:  # keep serving the last good copy
            log.warning("seed load failed: %s", e)
            if _seed["data"] is None:
                raise HTTPException(503, "Task list is unavailable right now.")
        return _seed["data"]


# ---------- database (owner and status overlay) ----------

_db_lock = threading.RLock()  # change() calls find() -> overlay() while holding it


def db() -> sqlite3.Connection:
    con = sqlite3.connect(CFG.db_path, timeout=5)
    con.execute("""CREATE TABLE IF NOT EXISTS task_state(
        task_id TEXT PRIMARY KEY, owner TEXT NOT NULL, status TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '', updated_at REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, actor TEXT, via TEXT,
        action TEXT, old_status TEXT, new_status TEXT, old_owner TEXT, new_owner TEXT,
        note TEXT, at REAL)""")
    return con


def overlay() -> dict[str, dict]:
    with _db_lock, db() as con:
        rows = con.execute("SELECT task_id, owner, status, note, updated_at FROM task_state").fetchall()
    return {r[0]: {"owner": r[1], "status": r[2], "note": r[3], "updated_at": r[4]} for r in rows}


def merged() -> dict:
    seed = load_seed()
    over = overlay()
    tasks = []
    for t in seed["tasks"]:
        t = dict(t)
        o = over.get(t.get("id"))
        if o:
            t["owner"], t["status"] = o["owner"], o["status"]
            if o["note"]:
                t["note"] = o["note"]
            t["updated_at"] = o["updated_at"]
        tasks.append(t)
    return {**{k: v for k, v in seed.items() if k != "tasks"}, "tasks": tasks}


def find(task_id: str) -> dict:
    task_id = clean(task_id, 40).lower()
    for t in merged()["tasks"]:
        if t.get("id") == task_id:
            return t
    raise HTTPException(404, f"No task called {task_id}.")


def unowned(owner: str) -> bool:
    return owner in ("", "All", None)


def change(task_id: str, actor: str, via: str, action: str, *, is_admin: bool = False,
           status: str | None = None, note: str = "") -> dict:
    """Apply one change with the ownership rules. Returns the updated task."""
    if status is not None and status not in STATUSES:
        raise HTTPException(400, "Status must be todo, in_progress, blocked or done.")
    with _db_lock:
        t = find(task_id)
        owner, old = t.get("owner") or "", t.get("status", "todo")
        if action == "claim":
            if old == "done":
                raise HTTPException(409, f"{t['id']} is already done.")
            if not unowned(owner) and owner != actor:
                raise HTTPException(409, f"{t['id']} is owned by {owner}. They can release it, or Branden can.")
            new_owner, new_status = actor, ("in_progress" if old in ("todo", "blocked") else old)
        elif action == "status":
            if owner != actor and not is_admin:
                raise HTTPException(403, f"Only {owner or 'the owner'} can change {t['id']}. Claim it first.")
            new_owner, new_status = owner, status
        elif action == "release":
            if owner != actor and not is_admin:
                raise HTTPException(403, f"Only {owner or 'the owner'} can release {t['id']}.")
            new_owner, new_status = "", ("todo" if old != "done" else "done")
        else:
            raise HTTPException(400, "Unknown action.")
        note = clean(note, MAX_NOTE) if new_status == "blocked" else ""
        now = time.time()
        with db() as con:
            con.execute("""INSERT INTO task_state(task_id, owner, status, note, updated_at) VALUES(?,?,?,?,?)
                ON CONFLICT(task_id) DO UPDATE SET owner=excluded.owner, status=excluded.status,
                note=excluded.note, updated_at=excluded.updated_at""",
                        (t["id"], new_owner, new_status, note, now))
            con.execute("""INSERT INTO audit(task_id, actor, via, action, old_status, new_status,
                old_owner, new_owner, note, at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (t["id"], actor, via, action, old, new_status, owner, new_owner, note, now))
    t.update(owner=new_owner, status=new_status, note=note)
    return t


# ---------- Discord channel feed ----------

def feed_text(t: dict, actor: str, via: str, action: str) -> str:
    title = clean(t.get("title", ""), 120)
    if action == "claim":
        what = "claimed"
    elif action == "release":
        what = "released"
    else:
        what = "marked " + STATUS_WORD.get(t["status"], t["status"])
    line = f"**{actor}** {what} `{t['id']}` {title} (via {via})"
    if t.get("note"):
        line += f"\nReason: {t['note']}"
    return line


def post_feed(text: str):
    url = CFG.webhook
    if not url.startswith(WEBHOOK_PREFIX):
        return
    if LIMITS.over("feed", FEED_LIMIT, FEED_WINDOW):
        log.warning("feed cap reached, not posting")
        return
    LIMITS.add("feed")
    try:
        httpx.post(url, json={"content": text[:1900], "allowed_mentions": {"parse": []}}, timeout=8)
    except Exception as e:
        log.warning("feed post failed: %s", e)


# ---------- app ----------

app = FastAPI(title="Bricked Sorting claims", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[CFG.origin], allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], max_age=600)


def visitor(request: Request) -> str:
    # The app listens on 127.0.0.1 behind cloudflared, so Cloudflare's header is the real visitor.
    return request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/tasks")
def api_tasks():
    data = merged()
    writes = CFG.site_writes and bool(CFG.password_hash)
    data.update(live=True, writes=writes, names=CFG.names if writes else [])
    return JSONResponse(data, headers={"Cache-Control": "no-store"})


class SiteBody(BaseModel):
    name: str
    password: str
    status: str | None = None
    note: str = ""


def site_gate(request: Request, body: SiteBody) -> str:
    if not (CFG.site_writes and CFG.password_hash):
        raise HTTPException(503, "Changes from the website are turned off.")
    who = "site:" + visitor(request)
    if LIMITS.over(who + ":fail", FAIL_LIMIT, FAIL_WINDOW):
        raise HTTPException(429, "Too many wrong tries. Wait 10 minutes.")
    given = hashlib.sha256(body.password.encode()).hexdigest()
    if not hmac.compare_digest(given, CFG.password_hash):
        LIMITS.add(who + ":fail")
        raise HTTPException(401, "Wrong team password.")
    name = clean(body.name, 70)
    if name not in CFG.names:
        raise HTTPException(400, "Pick your name from the list.")
    if LIMITS.over(who + ":write", WRITE_LIMIT, WRITE_WINDOW):
        raise HTTPException(429, "Too many changes. Wait a few minutes.")
    LIMITS.add(who + ":write")
    return name


def site_action(task_id: str, action: str, request: Request, body: SiteBody, bg: BackgroundTasks):
    name = site_gate(request, body)
    # No admin override from the website: the shared password can't prove who is clicking.
    t = change(task_id, name, "site", action, status=body.status, note=body.note)
    bg.add_task(post_feed, feed_text(t, name, "site", action))
    return {"ok": True, "task": t}


@app.post("/api/tasks/{task_id}/claim")
def site_claim(task_id: str, body: SiteBody, request: Request, bg: BackgroundTasks):
    return site_action(task_id, "claim", request, body, bg)


@app.post("/api/tasks/{task_id}/status")
def site_status(task_id: str, body: SiteBody, request: Request, bg: BackgroundTasks):
    return site_action(task_id, "status", request, body, bg)


@app.post("/api/tasks/{task_id}/release")
def site_release(task_id: str, body: SiteBody, request: Request, bg: BackgroundTasks):
    return site_action(task_id, "release", request, body, bg)


# ---------- Discord interactions ----------

def verify_discord(request_body: bytes, sig: str, ts: str) -> None:
    key = CFG.discord_key
    if not key:
        raise HTTPException(503, "Discord is not set up.")
    try:
        if abs(time.time() - int(ts)) > DISCORD_MAX_AGE:
            raise ValueError("stale")
        VerifyKey(bytes.fromhex(key)).verify(ts.encode() + request_body, bytes.fromhex(sig))
    except (BadSignatureError, ValueError, TypeError):
        raise HTTPException(401, "invalid request signature")


def reply(text: str) -> dict:
    # Ephemeral (flag 64): only the person who typed the command sees the answer.
    # Everyone else sees the change in the feed channel.
    return {"type": 4, "data": {"content": text[:1900], "flags": 64, "allowed_mentions": {"parse": []}}}


def task_line(t: dict) -> str:
    owner = t.get("owner") or "nobody"
    due = f" · due {t['due']}" if t.get("due") else ""
    return f"`{t['id']}` {clean(t.get('title', ''), 80)} · {STATUS_WORD.get(t.get('status'), t.get('status'))} · {owner}{due}"


def list_reply(tasks: list[dict], empty: str) -> dict:
    if not tasks:
        return reply(empty)
    lines, size = [], 0
    for t in tasks:
        line = task_line(t)
        if size + len(line) > 1800:
            lines.append(f"…and {len(tasks) - len(lines)} more. See the Tasks page.")
            break
        lines.append(line)
        size += len(line) + 1
    return reply("\n".join(lines))


@app.post("/discord/interactions")
async def discord(request: Request, bg: BackgroundTasks):
    body = await request.body()
    verify_discord(body, request.headers.get("x-signature-ed25519", ""),
                   request.headers.get("x-signature-timestamp", ""))
    data = json.loads(body)
    if data.get("type") == 1:  # Discord's ping when the endpoint is saved
        return {"type": 1}
    if data.get("type") != 2:
        return reply("Unsupported interaction.")
    # The rest reads the task list and the database, so run it off the event loop.
    return await run_in_threadpool(handle_command, data, bg)


def handle_command(data: dict, bg: BackgroundTasks) -> dict:

    user = (data.get("member") or {}).get("user") or data.get("user") or {}
    name = CFG.discord_users.get(str(user.get("id", "")))
    if not name:
        return reply("You're not on the Bricked Sorting team list. Ask Branden to add you.")
    if LIMITS.over("discord:" + name, WRITE_LIMIT, WRITE_WINDOW):
        return reply("Too many commands. Wait a few minutes.")

    cmd = (data.get("data") or {}).get("name", "")
    opts = {o.get("name"): o.get("value") for o in (data.get("data") or {}).get("options", [])}
    is_admin = name == CFG.admin

    try:
        if cmd == "tasks":
            want = opts.get("status")
            tasks = [t for t in merged()["tasks"] if t.get("status") != "done"] if not want else \
                    [t for t in merged()["tasks"] if t.get("status") == want]
            return list_reply(tasks, "No tasks match.")
        if cmd == "mytasks":
            mine = [t for t in merged()["tasks"] if t.get("owner") == name and t.get("status") != "done"]
            return list_reply(mine, "You have no open tasks. Try /tasks and /claim one.")
        if cmd == "export":
            if not is_admin:
                return reply("Only Branden can export.")
            rows = overlay()
            text = json.dumps({k: {"owner": v["owner"], "status": v["status"]} for k, v in sorted(rows.items())})
            return reply("Live owners and statuses (copy into tasks.json by pull request):\n```json\n" + text[:1700] + "\n```")

        LIMITS.add("discord:" + name)
        task_id = str(opts.get("task", ""))
        if cmd == "claim":
            t, action = change(task_id, name, "Discord", "claim", is_admin=is_admin), "claim"
        elif cmd == "release":
            t, action = change(task_id, name, "Discord", "release", is_admin=is_admin), "release"
        elif cmd in ("start", "done", "todo"):
            st = {"start": "in_progress", "done": "done", "todo": "todo"}[cmd]
            t, action = change(task_id, name, "Discord", "status", is_admin=is_admin, status=st), "status"
        elif cmd == "blocked":
            t, action = change(task_id, name, "Discord", "status", is_admin=is_admin, status="blocked",
                               note=str(opts.get("reason", ""))), "status"
        else:
            return reply("Unknown command.")
    except HTTPException as e:
        return reply(str(e.detail))

    bg.add_task(post_feed, feed_text(t, name, "Discord", action))
    return reply("Done: " + task_line(t))
