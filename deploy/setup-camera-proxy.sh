#!/bin/sh
# One-time, inside CT 150 as root: show the Pi camera on the website's Camera tab.
# Installs the camera relay (kratos/camera-relay, port 8002) that the Pi pushes frames to,
# and the nginx paths /camera-stream, /camera-snapshot, /camera-health. Safe to re-run.
# Doesn't touch bricked-server (5000), the dashboard (8080) or anything else.
# Asks for the team password (hidden) so only the team can watch; stores only its hash.
set -eu
REPO_URL=https://github.com/jerrekt/Bricked-Sorting.git
DIR=/opt/bricked-camera-relay
CONF=/etc/nginx/conf.d/bricked-pi-camera.conf
SRC=$(mktemp -d)
trap 'rm -rf "$SRC"' EXIT

git clone -q --depth 1 --branch main "$REPO_URL" "$SRC/r"

ENVF=/etc/bricked-camera-relay.env
echo "--- 1/4 team password for the Camera tab"
OLD=$(grep -E '^RELAY_PASSWORD_SHA256=' "$ENVF" 2>/dev/null | cut -d= -f2- || true)
[ -n "$OLD" ] && echo "A password is already set. Press Enter to keep it."
printf "Team password (same as the Live page buttons; hidden, Enter = %s): " "$( [ -n "$OLD" ] && echo keep || echo 'no password, open stream' )"
stty -echo </dev/tty 2>/dev/null || true; read -r PW </dev/tty; stty echo </dev/tty 2>/dev/null || true; echo
if [ -n "$PW" ]; then HASH=$(printf '%s' "$PW" | sha256sum | cut -d' ' -f1); else HASH=$OLD; fi
PW=
KEY=$(grep -E '^RELAY_SESSION_KEY=' "$ENVF" 2>/dev/null | cut -d= -f2- || true)
[ -n "$KEY" ] || KEY=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
install -m 600 /dev/null "$ENVF"
printf 'RELAY_PASSWORD_SHA256=%s\nRELAY_SESSION_KEY=%s\n' "$HASH" "$KEY" > "$ENVF"
[ -n "$HASH" ] && echo "Password set (only its hash is stored, in $ENVF)." || echo "No password: the Camera tab stays open to everyone."

echo "--- 2/4 camera relay service (port 8002)"
id bricked-relay >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin bricked-relay
install -d -m 755 "$DIR"
install -m 644 "$SRC/r/kratos/camera-relay/camera_relay.py" "$DIR/camera_relay.py"
cat > /etc/systemd/system/bricked-camera-relay.service <<UNIT
[Unit]
Description=Bricked Sorting camera relay (Pi pushes frames, website reads them)
After=network-online.target

[Service]
User=bricked-relay
EnvironmentFile=$ENVF
ExecStart=/usr/bin/python3 -u $DIR/camera_relay.py
Restart=always
RestartSec=3
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now bricked-camera-relay
systemctl restart bricked-camera-relay
sleep 1
curl -s -m 3 -o /dev/null -w "relay: HTTP %{http_code} (503 = running, no frames from the Pi yet)\n" http://127.0.0.1:8002/health || true

echo "--- 3/4 nginx paths"
cp /etc/nginx/sites-available/bricked-site "$SRC/site.bak"
[ -f "$CONF" ] && cp "$CONF" "$SRC/conf.bak"
echo 'upstream bricked_pi_camera { server 127.0.0.1:8002; keepalive 4; }' > "$CONF"
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

echo "--- 4/4 check"
curl -fsS -o /dev/null -w "site: HTTP %{http_code}\n" http://localhost:8090/
curl -s -m 5 -o /dev/null -w "camera through nginx: HTTP %{http_code} (200 once the Pi is pushing)\n" http://localhost:8090/camera-health || true
curl -s -m 5 -o /dev/null -w "camera stream without the password: HTTP %{http_code} (401 = locked, good)\n" http://localhost:8090/camera-snapshot || true
echo "Next: on the Pi, re-run identify/setup_camera.sh so it starts bricked-camera-push."
