"""Previews for V10 rendered from the actual exported STL meshes."""
from pathlib import Path
import json, struct, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'bins_v10'
ns = {'__file__': str(ROOT / 'render_previews_v3.py')}
src = (ROOT / 'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
exec(compile(src, 'preview_renderer', 'exec'), ns); render = ns['render']
R = json.loads((OUT / 'dimensions_and_checks.json').read_text())

def load(name):
    raw = (OUT / (name + '.stl')).read_bytes(); n = struct.unpack_from('<I', raw, 80)[0]
    dt = np.dtype([('n', '<f4', (3,)), ('v', '<f4', (3, 3)), ('a', '<u2')])
    return np.frombuffer(raw, dtype=dt, count=n, offset=84)['v'].astype(float)

def rz(v, deg):
    t = math.radians(deg); M = np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]]); return v @ M.T
def rx(v, deg):
    t = math.radians(deg); M = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]]); return v @ M.T

# STLs were re-centered for printing; rebuild assembly offsets from bounding boxes
def to_asm(v, ref):  # move mesh so its bbox matches the reference bbox min corner
    mn = v.reshape(-1, 3).min(axis=0); return v - mn + ref
H = R['heights']; RI, RO = R['radii']['bin_inner_face'], R['radii']['bin_outer_face']
COL = {'lower': (.45, .5, .56), 'S': (.95, .78, .2), 'M': (.2, .52, .78), 'L': (.13, .16, .2), 'loc': (.62, .66, .7), 'scoop': (.08, .58, .62)}
CLASS = {1: 'M', 2: 'S', 3: 'S', 4: 'M', 5: 'S', 6: 'L', 7: 'L', 8: 'M'}
# Site colors: swatches from web/data/bins.json (slot 8 'unknown' has none on the site; neutral gray here)
SITE = {1: '#D6372B', 2: '#F2C21B', 3: '#3E9B45', 4: '#2F74C8', 5: '#B65FA8', 6: '#2A2B2E', 7: '#E9E7E1', 8: '#8A8F98'}
SITE_LABEL = {1: 'Red / Orange', 2: 'Yellow', 3: 'Green / Lime', 4: 'Blue / Azure', 5: 'Pink / Purple', 6: 'Black / Dark Gray', 7: 'White / Light Gray', 8: 'Unknown'}
def hexc(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
def yaw(k): return 90.0 - 22.5 * (k - 0.5)
pitch_half = math.radians(11.25)

lower = load('40_bin_lower_PRINT_8'); loc = load('42_bin_locator_PRINT_16')
up8 = load('41_bin_upper_PRINT_8'); ups = {c: up8 for c in 'SML'}
scoop = load('43_compact_scoop_PRINT_FLAT')

def wedge_ref(mesh_y_extent_min):
    return None
# bin solids in build frame: centerline +Y, x symmetric, inner face y min = RI*cos(...) approx; use known bbox
def place_bin(v, k, z0):
    v = v.reshape(-1, 3).copy(); v[:, 0] -= (v[:, 0].min() + v[:, 0].max()) / 2
    v[:, 1] += (R['radii']['bin_inner_face'] * 0 + bin_ymin) - v[:, 1].min(); v[:, 2] += z0 - v[:, 2].min()
    return rz(v, yaw(k)).reshape(-1, 3, 3)
# inner-face chord points sit at y = sqrt(RI^2-g^2)*cos(half)-g*sin(half) ... use exact side-point minimum
g = 3.0; t = math.sqrt(RI * RI - g * g); bin_ymin = min(t * math.cos(pitch_half) + g * math.sin(pitch_half), RI * math.cos(pitch_half))
# rounded corners pull the true minimum in slightly; good enough for a preview
lg = .2; rl = R['radii']['locator_inner_edge']; t2 = math.sqrt(rl * rl - lg * lg); loc_ymin = t2 * math.cos(pitch_half) + lg * math.sin(pitch_half)
def place_loc(k, z0):
    v = loc.reshape(-1, 3).copy(); v[:, 0] -= (v[:, 0].min() + v[:, 0].max()) / 2
    v[:, 1] += loc_ymin - v[:, 1].min(); v[:, 2] += z0 - v[:, 2].min(); return rz(v, yaw(k)).reshape(-1, 3, 3)

actors = []
zc_up = H['upper_carrier_underside'] + 3
for k in range(1, 9):
    actors.append((place_loc(k, 0), np.array(COL['loc'])))
    actors.append((place_bin(lower, k, H['lower_seat']), hexc(SITE[k])))
    actors.append((place_loc(k, zc_up), np.array(COL['loc'])))
    actors.append((place_bin(ups[CLASS[k]], k, H['upper_seat']), hexc(SITE[k])))
# scoop: print-flat mesh -> assembly pose (rotate -40 about X), at the slot 4 lower-tier pose
sv = scoop.reshape(-1, 3).copy()
# recover origin: hub screw pattern centered at x=0; floor min y in print frame is the rear (-55/cos40 - flare)
sv[:, 0] -= (sv[:, 0].min() + sv[:, 0].max()) / 2
sv[:, 1] -= sv[:, 1].min() + 55 / math.cos(math.radians(40)) + 6.0
sv[:, 2] -= sv[:, 2].min()
sa = rx(sv, -40)
pose = [p for p in R['delivery_poses'] if p['tier'] == 'lower' and p['slot'] == 4][0]
sa[:, 2] += pose['scoop_lowest_z'] - sa[:, 2].min()
actors.append((rz(sa, yaw(4)).reshape(-1, 3, 3), np.array(COL['scoop'])))
render(actors, OUT / 'tiers_cad.png', (520, 900, 650), (0, 120, 150), (1300, 900))
render(actors, OUT / 'tiers_top.png', (0, 1, 2000), (0, 120, 0), (1000, 620))

# single parts
single = [(lower.reshape(-1, 3, 3), tuple(hexc(SITE[1])), 'Floor 1 bin x8 (140, sill 70)'), (up8.reshape(-1, 3, 3), tuple(hexc(SITE[4])), 'Floor 2 bin x8 (140, open top)'),
          (loc.reshape(-1, 3, 3), COL['loc'], 'Locator x16'), (sv.reshape(-1, 3, 3), COL['scoop'], 'Compact scoop (print flat)')]
tiles = []
for i, (v, c, label) in enumerate(single):
    p = OUT / f'_part{i}.png'; render([(v, np.array(c))], p, (260, -420, 320), tuple(v.reshape(-1, 3).mean(axis=0)), (420, 380)); tiles.append((p, label))

f = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
fb = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
im = Image.new('RGB', (2000, 1500), '#f6f7f8'); d = ImageDraw.Draw(im)
d.text((40, 25), 'BRICKED SORTING | V10 BINS, LOCATORS AND COMPACT SCOOP (600 x 350 option)', font=fb(34), fill='#20313f')
d.text((40, 75), f"Two tiers x 8 bins on 22.5 deg pitch | footprint {R['footprint']['width']:.0f} x {R['footprint']['depth_from_yaw_axis']:.0f} mm from the yaw axis | stack {R['heights']['stack_top']:.0f} mm", font=f(24), fill='#52636e')
im.paste(Image.open(OUT / 'tiers_cad.png'), (20, 120))
top = Image.open(OUT / 'tiers_top.png').resize((660, 409)); im.paste(top, (1320, 150))
d.text((1330, 125), 'Top view, floor 2 (scoop at slot 4)', font=f(20), fill='#20313f')
y0 = 560; d.text((1330, y0), 'Bin colors = site slots (both floors)', font=fb(20), fill='#20313f')
for i in range(8):
    k = i + 1; xx = 1330 + (i % 2) * 320; yy = y0 + 35 + (i // 2) * 30
    d.rectangle((xx, yy, xx + 22, yy + 22), fill=SITE[k], outline='#20313f')
    d.text((xx + 32, yy), f'{k}  {SITE_LABEL[k]}', font=f(18), fill='#20313f')
y1 = 720
lines = [f"Lift travel needed {R['lift_travel_needed_mm']:.0f} mm (current CAD 105)",
         f"Mouth {R['mouth_clear_width_at_inner_wall']:.1f} mm vs 40 mm outlet",
         f"Scoop sweep r {R['radii']['scoop_sweep_radius_measured']:.0f}, locator r {R['radii']['locator_inner_edge']:.0f}",
         f"Clashes: bins {len(R['bin_and_locator_clashes'])}, scoop {len(R['scoop_clashes_at_16_delivery_poses'])} (16 poses)",
         f"Upper share {100*R['tier_totals_L']['upper_share']:.0f}% of geometric volume"]
for i, t_ in enumerate(lines): d.text((1330, y1 + i * 30), t_, font=f(19), fill='#20313f')
for i, (p, label) in enumerate(tiles):
    x = 20 + i * 490; tile = Image.open(p).resize((420, 290)); im.paste(tile, (x, 1050)); d.text((x + 10, 1345), label, font=f(20), fill='#20313f'); p.unlink()
d.text((40, 1440), 'Layout proposal from actual STL meshes. Not a print release: switch size, drawer carriers, lift extension and part flight are unverified.', font=f(20), fill='#7a5a1e')
im.save(OUT / 'V10_overview.png'); print('ok')
