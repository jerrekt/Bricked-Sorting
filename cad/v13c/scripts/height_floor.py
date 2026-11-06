"""Height floor for any V13-style machine that keeps the V13 lift, yaw, hub and compact scoop under a scanner on the
yaw axis. Same stack rules as build_bins_v13c.py / build_machine_v13c.py:
  lower bin wall  H_L >= S + NC + 24.2 + m            (part on the nose must pass under the upper carrier)
  upper delivery  LOW_MAX = Z_C + 13.5 + H_L + 26.5 + H_U + NC
  scanner floor   Z_S = ceil(LOW_MAX + 198.5 + 25 + 38) (scoop height 198.5 at 40 deg, 25 margin, 38 door drop)
  deck underside  Z_S - 53
Capacity: 0.0101 L per mm of fill (V10 wedge, RI 152..RO 290); lower fills to S - 2.4, upper to H_U - 12.4."""
import math, json
from pathlib import Path
SCOOP = 86.93054763120438 + 111.60025104657825
def stack(fill_L, NC=35.0, m=10.8, deck_above_underside=None, kept_deck=572.0):
    d = fill_L / 0.0101; S = 2.4 + d; HU = 12.4 + d; HL = S + NC + 24.2 + m
    low_max = 60 + 13.5 + HL + 26.5 + HU + NC; zs = math.ceil(low_max + SCOOP + 63)
    r = {'fill_L': fill_L, 'NC': NC, 'margin': m, 'S': round(S, 1), 'H_U': round(HU, 1), 'H_L': round(HL, 1), 'Z_S': zs,
         'total_with_V13_deck_kept': zs + kept_deck, 'total_with_new_312_deck_and_60_studs': zs - 53 + 372}
    return r
rows = [stack(f, nc, m) for f in (0.0, 0.25, 0.40) for nc, m in ((35.0, 10.8), (20.0, 5.0))]
need = {'Z_S_max_for_762_with_new_312_deck': 762 - 372 + 53}
out = {'about': __doc__.strip(), 'rows': rows, **need}
(Path(__file__).resolve().parent.parent / 'height_floor.json').write_text(json.dumps(out, indent=1) + '\n')
for r in rows: print(r)
print(need)
