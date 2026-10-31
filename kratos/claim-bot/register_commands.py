#!/usr/bin/env python3
"""Register the slash commands with Discord, once (and again if commands change).

Run on your own machine, not the server. The bot token is used for this one call
and is never stored:

  DISCORD_APP_ID=... DISCORD_GUILD_ID=... DISCORD_BOT_TOKEN=... python3 register_commands.py

Guild commands appear in your server right away. Nothing else uses the token,
so you can reset it in the Discord developer portal afterwards.
"""
import os
import sys

import httpx

TASK = {"name": "task", "description": "Task id, like identify-02", "type": 3, "required": True, "max_length": 40}
STATUS_CHOICES = [{"name": n, "value": v} for n, v in
                  [("to do", "todo"), ("in progress", "in_progress"), ("blocked", "blocked"), ("done", "done")]]

COMMANDS = [
    {"name": "tasks", "description": "List open tasks (or one status)",
     "options": [{"name": "status", "description": "Only this status", "type": 3, "required": False, "choices": STATUS_CHOICES}]},
    {"name": "mytasks", "description": "Your open tasks"},
    {"name": "claim", "description": "Take a task", "options": [TASK]},
    {"name": "start", "description": "Mark your task in progress", "options": [TASK]},
    {"name": "blocked", "description": "Mark your task blocked", "options": [
        TASK, {"name": "reason", "description": "What is blocking it", "type": 3, "required": True, "max_length": 200}]},
    {"name": "done", "description": "Mark your task done", "options": [TASK]},
    {"name": "todo", "description": "Move your task back to to do", "options": [TASK]},
    {"name": "release", "description": "Give up a task so someone else can claim it", "options": [TASK]},
    {"name": "export", "description": "Branden only: live owners and statuses for tasks.json"},
]


def main():
    app_id, guild, token = (os.environ.get(k, "").strip() for k in ("DISCORD_APP_ID", "DISCORD_GUILD_ID", "DISCORD_BOT_TOKEN"))
    if not (app_id and guild and token):
        sys.exit("Set DISCORD_APP_ID, DISCORD_GUILD_ID and DISCORD_BOT_TOKEN for this one run.")
    r = httpx.put(f"https://discord.com/api/v10/applications/{app_id}/guilds/{guild}/commands",
                  headers={"Authorization": f"Bot {token}"}, json=COMMANDS, timeout=15)
    if r.status_code >= 300:
        sys.exit(f"Discord said {r.status_code}: {r.text[:300]}")
    print("Registered:", ", ".join("/" + c["name"] for c in r.json()))


if __name__ == "__main__":
    main()
