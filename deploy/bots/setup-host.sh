#!/usr/bin/env bash
# Base packages for the bots container. Run once as root inside the container.
set -euo pipefail
apt-get update
apt-get install -y python3-venv git curl ca-certificates
# cloudflared from Cloudflare's apt repo (check the current instructions on
# developers.cloudflare.com before running; not re-verified here).
mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(. /etc/os-release; echo "$VERSION_CODENAME") main" \
  > /etc/apt/sources.list.d/cloudflared.list
apt-get update && apt-get install -y cloudflared
echo "Base setup done. Next: add-bot.sh <name>"
