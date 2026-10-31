# Bots container

One small container on Kratos that runs Branden's bots. The first one is the
Bricked Sorting claim server (`kratos/claim-bot`). Each bot is kept apart:

| Per bot | Example for the claim bot |
|---|---|
| Linux user (no login) | `bot-bricked-claim` |
| Code (root-owned, read-only to the bot) | `/opt/bricked-claim/src` |
| Data (only the bot can write) | `/var/lib/bricked-claim` |
| Secrets (root-only, 0600) | `/etc/bricked-claim/bot.env` |
| Service | `bricked-claim.service` |
| Port, localhost only | `127.0.0.1:8701` |

A bot can't read another bot's secrets or data. Someone who gets full root in
the container could, so anything handling money or personal data gets its own
container instead.

Only Branden logs in here. No teammate accounts.

## 1. Create the container (Proxmox, by hand)
Unprivileged Debian 12 LXC, 1 CPU, 512 MB RAM, 4 GB disk, DHCP, `firewall=1`
on net0. Pick the ID. Then write `/etc/pve/firewall/<ID>.fw` from
`firewall.example.fw` (put the real gateway address in; it is not in this repo).
Test as in Mnemosyne `private/mini-waymo-ct312-firewall.md`.

## 2. Base setup (inside the container, as root)
    bash setup-host.sh
Installs python3-venv, git, curl and cloudflared's package. Nothing bot-specific.

## 3. Add the claim bot (as root)
    bash add-bot.sh bricked-claim
    git clone --depth 1 https://github.com/jerrekt/Bricked-Sorting /opt/bricked-claim/src
    python3 -m venv /opt/bricked-claim/venv
    /opt/bricked-claim/venv/bin/pip install -r /opt/bricked-claim/src/kratos/claim-bot/requirements.txt
    cp bricked-claim.service /etc/systemd/system/
    # fill /etc/bricked-claim/bot.env from bot.env.example (nano, never paste secrets into chat)
    systemctl daemon-reload && systemctl enable --now bricked-claim
    curl -s 127.0.0.1:8701/health

## 4. Tunnel
One cloudflared tunnel for the container, one hostname per bot. See
`cloudflared-config.example.yml`. Then put the hostname in
`web/tasks.html` (`<meta name="bricked-api">`) by pull request.

## 5. Discord
1. Discord developer portal: New Application. Copy the Application ID and Public Key into `bot.env`.
2. Set "Interactions Endpoint URL" to `https://<api hostname>/discord/interactions`. Discord checks it right away; the service must be running.
3. In the team server: a channel for task updates, then Integrations, Webhooks, New Webhook. Copy its URL into `bot.env`.
4. Install the app in the server (OAuth2 URL with the `applications.commands` scope).
5. Register commands once, from your own PC: see `kratos/claim-bot/register_commands.py`. The bot token is only used for that run; reset it afterwards.

## Updating the code (by hand, no timer)
    cd /opt/bricked-claim/src && git pull --ff-only
    /opt/bricked-claim/venv/bin/python -m py_compile kratos/claim-bot/app.py && systemctl restart bricked-claim

## Turning site buttons off fast
Set `BRICKED_SITE_WRITES=0` in `bot.env` and restart. Discord keeps working.
