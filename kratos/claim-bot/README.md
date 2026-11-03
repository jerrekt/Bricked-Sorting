# Claim bot

Lets the team claim and update tasks on the Tasks page from Discord or from the site.

- `tasks.json` in GitHub stays the source for titles, details, due dates and new tasks.
- This server only stores **who owns a task and its status**, and merges that over `tasks.json` on every read.
- Every change posts to one Discord channel, marked "via Discord" or "via site".

## Discord commands
`/tasks` `/mytasks` `/claim task` `/start task` `/blocked task reason` `/done task` `/todo task` `/release task` `/export` (Branden only)

Replies are private to the person who typed the command. The channel feed is how everyone sees the changes.

## Rules (enforced by the server)
- Claim only if nobody owns it (or it's "All") and it isn't done.
- Only the owner can change or release a task. Branden can override from Discord, not from the site.
- Only the Discord IDs in `DISCORD_USERS` can use commands. Every request's Discord signature is checked, and requests older than 5 minutes are rejected.
- Site buttons need a name from the list plus the team password. 8 wrong tries locks that visitor out for 10 minutes. The buttons are off unless `BRICKED_SITE_WRITES=1`.

## Build page parts (optional)
Set `BOT_PARTS_URL` (the Waymo bot uses `https://raw.githubusercontent.com/jerrekt/Aint-No-WAYmo/main/build_parts.json`) to turn on `GET /api/parts` and `POST /api/parts/{id}` (`{name, password, bought}`). Same gate as site claims. The file stays the list; this server only keeps who marked each part bought, posts it to the feed, and `/export` lists it for a PR. Empty = off.

## Run the tests
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
    .venv/bin/python -m pytest -q tests

The tests use a fake Discord signer and a fake webhook. No network, no real keys.

## Deploy
See `deploy/bots/README.md`.

## Registering commands without Python (Windows)
`register_commands.ps1` sends the same commands as `register_commands.py` from PowerShell:

    powershell -ExecutionPolicy Bypass -File .\register_commands.ps1

It asks for the Application ID, the server ID and the bot token (typed hidden, used once, never saved). It sends a `DiscordBot` user agent; with PowerShell's default one Discord answers 403 code 40333. Reset the bot token afterwards. If you change the commands, change both files.

## Keeping git in sync
`/export` prints the live owners and statuses. Copy them into `web/data/tasks.json` by pull request now and then, so the static fallback matches.
