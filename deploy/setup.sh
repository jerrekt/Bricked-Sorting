#!/bin/sh
# One-time setup inside CT 150 (run as root). Safe to re-run.
# Does NOT touch bricked-server.service (port 5000, Pi /identify) or brickbase-dashboard.
set -eu
REPO_URL=https://github.com/jerrekt/Bricked-Sorting.git
DIR=/opt/bricked-site
SRC=$(mktemp -d)

apt-get update -q
apt-get install -y -q nginx git ca-certificates curl

id bricksite >/dev/null 2>&1 || useradd --system --home-dir "$DIR" --shell /usr/sbin/nologin bricksite
if [ ! -d "$DIR/.git" ]; then
  install -d -o bricksite -g bricksite "$DIR"
  runuser -u bricksite -- git clone -q --branch main "$REPO_URL" "$DIR"
fi
chmod 755 "$DIR"

# Install deploy files from a root-owned copy, not from the live checkout.
git clone -q --depth 1 --branch main "$REPO_URL" "$SRC/r"
install -m 755 "$SRC/r/deploy/autodeploy.sh" /usr/local/sbin/bricked-site-autodeploy
install -m 644 "$SRC/r/deploy/bricked-site-autodeploy.service" /etc/systemd/system/
install -m 644 "$SRC/r/deploy/bricked-site-autodeploy.timer" /etc/systemd/system/
install -m 644 "$SRC/r/deploy/nginx-bricked-site.conf" /etc/nginx/sites-available/bricked-site
rm -rf "$SRC"

ln -sf /etc/nginx/sites-available/bricked-site /etc/nginx/sites-enabled/bricked-site
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx
systemctl reload nginx

systemctl daemon-reload
systemctl enable --now bricked-site-autodeploy.timer
systemctl start bricked-site-autodeploy.service

echo "--- check"
curl -fsS -o /dev/null -w "local site: HTTP %{http_code}\n" http://localhost:8090/
systemctl list-timers bricked-site-autodeploy.timer --no-pager | head -3
