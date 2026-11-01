#!/usr/bin/env bash
# Make the user, folders and an empty secrets file for one bot. Run as root.
#   bash add-bot.sh bricked-claim
set -euo pipefail
name="${1:?usage: add-bot.sh <name>}"
[[ "$name" =~ ^[a-z][a-z0-9-]{1,30}$ ]] || { echo "name: lowercase letters, digits, dashes"; exit 1; }
user="bot-$name"
id -u "$user" >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin "$user"
install -d -o root -g root -m 0755 "/opt/$name"
install -d -o "$user" -g "$user" -m 0700 "/var/lib/$name"
install -d -o root -g root -m 0700 "/etc/$name"
[ -f "/etc/$name/bot.env" ] || install -o root -g root -m 0600 /dev/null "/etc/$name/bot.env"
echo "Ready: user $user, code /opt/$name, data /var/lib/$name, secrets /etc/$name/bot.env (root only)"
