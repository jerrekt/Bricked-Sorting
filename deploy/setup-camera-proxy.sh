#!/bin/sh
# One-time, inside CT 150 as root: let the public site show the Pi camera at /camera-stream.
# Asks for the Pi's Tailscale address and keeps it out of GitHub
# (/etc/nginx/conf.d/bricked-pi-camera.conf). Re-run any time the Pi's address changes.
set -eu
CONF=/etc/nginx/conf.d/bricked-pi-camera.conf
REPO_URL=https://github.com/jerrekt/Bricked-Sorting.git
SRC=$(mktemp -d)
trap 'rm -rf "$SRC"' EXIT

printf "Pi Tailscale IP (tailscale status, the Pi row, starts with 100.): "
read -r PI </dev/tty
PI=$(printf '%s' "$PI" | tr -d '[:space:]')
case "$PI" in 100.*.*.*) ;; *) echo "That isn't a 100.x.x.x Tailscale address. Nothing changed."; exit 1;; esac

echo "--- checking the Pi camera from CT 150"
curl -fsS -m 5 -o /dev/null "http://$PI:8001/snapshot" \
  || { echo "CT 150 can't get http://$PI:8001/snapshot. Is bricked-camera-stream running on the Pi? Nothing changed."; exit 1; }
echo "Pi camera answers."

git clone -q --depth 1 --branch main "$REPO_URL" "$SRC/r"
cp /etc/nginx/sites-available/bricked-site "$SRC/site.bak"
[ -f "$CONF" ] && cp "$CONF" "$SRC/conf.bak"

printf 'upstream bricked_pi_camera { server %s:8001; keepalive 4; }\n' "$PI" > "$CONF"
chmod 644 "$CONF"
install -m 644 "$SRC/r/deploy/nginx-bricked-site.conf" /etc/nginx/sites-available/bricked-site

if nginx -t 2>/dev/null; then
  systemctl reload nginx
else
  echo "nginx config test failed; putting the old config back."
  cp "$SRC/site.bak" /etc/nginx/sites-available/bricked-site
  if [ -f "$SRC/conf.bak" ]; then cp "$SRC/conf.bak" "$CONF"; else rm -f "$CONF"; fi
  nginx -t && systemctl reload nginx
  exit 1
fi

echo "--- check"
curl -fsS -o /dev/null -w "site: HTTP %{http_code}\n" http://localhost:8090/
curl -fsS -m 5 -o /dev/null -w "camera snapshot through nginx: HTTP %{http_code}\n" http://localhost:8090/camera-snapshot
curl -sS -m 3 -o /dev/null -w "camera stream through nginx: HTTP %{http_code} (%{size_download} bytes in 3 s)\n" http://localhost:8090/camera-stream || true
