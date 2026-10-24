#!/bin/sh
# Pull jerrekt/Bricked-Sorting main and serve web/. Runs every 60 s as user bricksite.
# Installed to /usr/local/sbin by setup.sh, so pushes to the repo cannot change this script
# or the nginx config. Only the static files in web/ update automatically.
set -eu
REPO=/opt/bricked-site
cd "$REPO"
git fetch -q origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
[ "$LOCAL" = "$REMOTE" ] && exit 0
git reset -q --hard origin/main
echo "deployed $(git rev-parse --short HEAD) (was $(echo "$LOCAL" | cut -c1-7))"
