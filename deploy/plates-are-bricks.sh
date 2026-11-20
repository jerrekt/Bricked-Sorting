#!/bin/sh
# One-time, on CT 150 as root: plain plates (Plate N x M) count as bricks -> bottom floor (BJ 2026-11-18).
# Edits the live classifier /opt/bricked-sorting/classify.py (makes a .bak first), runs its self-test, restarts the server.
set -eu
F=/opt/bricked-sorting/classify.py
cp "$F" "$F.bak-$(date +%Y%m%d%H%M%S)"
python3 - "$F" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
old = 'r"^brick \\d+ x \\d+( x \\d+)?$"'
new = 'r"^(brick|plate) \\d+ x \\d+( x \\d+)?$"'
if new in s:
    print("already done"); sys.exit(0)
if old not in s:
    sys.exit("could not find the brick pattern in classify.py; nothing changed")
s = s.replace(old, new, 1)
s = s.replace('("Plate 2 x 4", 90, "Orange", "OTHER_RED")', '("Plate 2 x 4", 90, "Orange", "BRICK_RED"), ("Plate, Round 2 x 2", 90, "Red", "OTHER_RED")', 1)
s = s.replace('SHAPE  BRICK only for a plain "Brick N x N" (or N x N x N).', 'SHAPE  BRICK for a plain "Brick N x N" (or N x N x N) or a plain "Plate N x N".', 1)
open(p, "w").write(s); print("classify.py updated")
PY
cd /opt/bricked-sorting && python3 classify.py | tail -2
systemctl restart bricked-server && echo "bricked-server restarted"
