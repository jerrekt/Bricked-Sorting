#!/bin/bash
# Bricked Sorting: install the Pi camera loop (identify/camera_service.py) as a service.
# Also installs identify/camera_stream.py (the camera server on port 8001: /stream, /snapshot, /health).
# Safe to run again: it updates the code and keeps or replaces your settings.
set -e
U=$(id -un); H=$HOME
DIR=$H/bricked/identify
ENVF=$H/.bricked_camera.env
RAW=https://raw.githubusercontent.com/jerrekt/Bricked-Sorting/main/identify

echo "== 1/7 Getting camera_stream.py and camera_service.py from GitHub main"
mkdir -p "$DIR"
for f in camera_stream.py camera_service.py camera_push.py; do
  curl -fsSL "$RAW/$f" -o "$DIR/$f.new" && mv "$DIR/$f.new" "$DIR/$f"
done

echo "== 2/7 Checking Python packages"
if ! python3 -c "import cv2, numpy, requests" 2>/dev/null || ! command -v v4l2-ctl >/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq python3-opencv python3-numpy python3-requests v4l-utils
fi

echo "== 3/7 Camera server (port 8001) replaces the old camera-stream user service"
systemctl --user disable --now camera-stream 2>/dev/null || true
# The Pi no longer identifies pieces itself (CT 150 does, decided 2026-10-24): retire the old
# local brick-server on port 5000. Disabled, not deleted: "sudo systemctl enable --now brick-server" undoes it.
if systemctl list-unit-files brick-server.service 2>/dev/null | grep -q brick-server; then
  sudo systemctl disable --now brick-server 2>/dev/null && echo "Old Pi brick-server (port 5000) stopped and disabled."
fi
sudo usermod -aG video "$U"
sudo tee /etc/systemd/system/bricked-camera-stream.service >/dev/null <<UNIT
[Unit]
Description=Bricked Sorting camera server (/stream, /snapshot, /health on port 8001)
After=network-online.target

[Service]
User=$U
SupplementaryGroups=video
ExecStart=/usr/bin/python3 -u $DIR/camera_stream.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now bricked-camera-stream
sudo systemctl restart bricked-camera-stream
echo -n "Waiting for the first frame"
for i in $(seq 1 20); do curl -fs -m 2 -o /dev/null http://127.0.0.1:8001/snapshot && break; echo -n .; sleep 1; done; echo
curl -fs -m 2 -o /dev/null http://127.0.0.1:8001/snapshot || { echo "Camera server has no picture. Last log lines:"; journalctl -u bricked-camera-stream -n 15 --no-pager; exit 1; }
echo "Camera server OK."

echo "== 4/7 Settings (saved only in $ENVF, never in GitHub)"
OLD_ID=$(grep -E '^IDENTIFY_URL=' "$ENVF" 2>/dev/null | cut -d= -f2- || true)
OLD_SNAP=$(grep -E '^SNAPSHOT_URL=' "$ENVF" 2>/dev/null | cut -d= -f2- || true)
OLD_CROP=$(grep -E '^TRAY_CROP=' "$ENVF" 2>/dev/null | cut -d= -f2- || true)
ID=${IDENTIFY_URL:-}
if [ -z "$ID" ]; then
  [ -n "$OLD_ID" ] && echo "Saved IDENTIFY_URL: $OLD_ID  (press Enter to keep it)"
  read -rp "Type IDENTIFY_URL, like http://100.x.x.x:5000/identify, then Enter: " ID </dev/tty
fi
# forgive copy-paste extras: spaces, quotes, backticks, "IDENTIFY_URL=", trailing slash, ?preview=1
ID=$(printf '%s' "$ID" | tr -d '[:space:]`"'"'"'' | sed -e 's/^IDENTIFY_URL=//' -e 's/?preview=1$//' -e 's:/*$::')
ID=${ID:-$OLD_ID}
case "$ID" in http://*/identify|https://*/identify) echo "Using IDENTIFY_URL: $ID" ;;
  *) echo "Got '$ID'. It must look like http://100.x.x.x:5000/identify. Nothing changed."; exit 1;; esac
DEF_SNAP=${OLD_SNAP:-http://127.0.0.1:8001/snapshot}
read -rp "SNAPSHOT_URL [Enter = $DEF_SNAP]: " SNAP </dev/tty; SNAP=${SNAP:-$DEF_SNAP}
DEF_CROP=${OLD_CROP:-0.0,0.0,1.0,1.0}
read -rp "TRAY_CROP left,top,right,bottom 0-1 [Enter = $DEF_CROP]: " CROP </dev/tty; CROP=${CROP:-$DEF_CROP}

echo "== 5/7 Testing both URLs"
T=$(mktemp --suffix=.jpg)
curl -fsS -m 5 "$SNAP" -o "$T" || { echo "Can't get a photo from $SNAP. Is the camera service running, and is the port right? Nothing changed."; rm -f "$T"; exit 1; }
[ "$(head -c 2 "$T" | od -An -tx1 | tr -d ' ')" = "ffd8" ] || { echo "$SNAP didn't return a JPEG. Nothing changed."; rm -f "$T"; exit 1; }
echo "Snapshot OK."
# preview=1 so this test photo never shows on the Live page
R=$(curl -sS -m 30 -o /dev/null -w '%{http_code}' -F "image=@$T;type=image/jpeg" "$ID?preview=1" || true); rm -f "$T"
[ "$R" = "200" ] || { echo "/identify answered '$R' instead of 200. Is Tailscale up and the address right? Nothing changed."; exit 1; }
echo "/identify OK."
install -m 600 /dev/null "$ENVF"
# Website camera: the Pi pushes frames to the relay on the same CT 150, port 8002.
PUSH=${PUSH_URL:-$(printf '%s' "$ID" | sed -E 's#^(https?://[^/:]+).*#\1:8002/push#')}
printf 'IDENTIFY_URL=%s\nSNAPSHOT_URL=%s\nTRAY_CROP=%s\nPUSH_URL=%s\n' "$ID" "$SNAP" "$CROP" "$PUSH" > "$ENVF"

echo "== 6/7 Installing the bricked-camera service"
sudo tee /etc/systemd/system/bricked-camera.service >/dev/null <<UNIT
[Unit]
Description=Bricked Sorting camera loop (one photo per piece to /identify)
After=network-online.target tailscaled.service bricked-camera-stream.service
Wants=network-online.target bricked-camera-stream.service

[Service]
User=$U
EnvironmentFile=$ENVF
ExecStart=/usr/bin/python3 -u $DIR/camera_service.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now bricked-camera
sudo systemctl restart bricked-camera
sleep 3
systemctl --no-pager --lines=0 status bricked-camera | head -3
echo
echo "== 7/7 Installing bricked-camera-push (sends the picture to the website's Camera tab)"
sudo tee /etc/systemd/system/bricked-camera-push.service >/dev/null <<UNIT
[Unit]
Description=Bricked Sorting camera push to CT 150 (website Camera tab)
After=network-online.target tailscaled.service bricked-camera-stream.service
Wants=network-online.target bricked-camera-stream.service

[Service]
User=$U
EnvironmentFile=$ENVF
ExecStart=/usr/bin/python3 -u $DIR/camera_push.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now bricked-camera-push
sudo systemctl restart bricked-camera-push
P=$(curl -sS -m 5 -o /dev/null -w '%{http_code}' --data-binary @<(curl -fs -m 3 "$SNAP?public=1") -H 'Content-Type: image/jpeg' "$PUSH" || true)
if [ "$P" = "200" ]; then echo "Website camera relay OK."; else echo "Website camera relay answered '$P'. Fine if CT 150's relay isn't set up yet; the service keeps retrying."; fi
echo
echo "Done. Start with the tray EMPTY. Watch it with:  journalctl -u bricked-camera -f"
echo "Then drop a piece: it should log 'Piece: ...' and show on the Live page tagged camera."
