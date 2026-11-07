"""Runner test kit, interface 5.1 (print this first): one drawer's worth of runners at the new size.
Right rail (guided) + left rail (floating, mirror), 4 floor stations, 1 guide block. Stations and the guide
screw into plywood with #6 wood screws. Also a 625 pocket coupon (16.0 / 16.1 / 16.2) per the runbook."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import print_pose, bed_fit, export, grams, hours, render, bbox
import runner as R
import cadquery as cq

OUT = HERE / 'runner_test'
INS = [60, 100, 140, 175]           # rail-top M3 inserts, rail local y
DET = R.ROLLERS_Y[-1] - R.RAIL_Y0_WORLD - 6.0
rail_R = R.rail(insert_ys=INS, detent_y=DET)
rail_L = R.mirror_x(rail_R)
stF, rF, _ = R.station(R.ROLLERS_Y, slotted_index=0)
stB, rB = stF, []
gd, rG, _ = R.guide_block((134.0, 162.0))


def coupon():
    """625 pocket coupon: three pockets 16.0 / 16.1 / 16.2 dia, 5.2 deep, 1/2/3 dots."""
    c = cq.Workplane().box(70, 26, 7, centered=False)
    for k, d in enumerate((16.0, 16.1, 16.2)):
        x = 12 + k * 23
        c = c.cut(cq.Workplane().circle(d / 2).extrude(6).translate((x, 13, 1.8)))
        for j in range(k + 1):
            c = c.cut(cq.Workplane().circle(0.8).extrude(2).translate((x - 4 + j * 4, 2.5, 6)))
    return c


def check():
    fixed = [('station', stF), ('guide', gd)] + [(f'roller_{i}', r) for i, r in enumerate(rF + rB + rG)]
    out = {}
    for d in (0, 3, 6, 10, 50, 100, 149, 150, 151, 153):
        rr = rail_R.translate((0, R.RAIL_Y0_WORLD + d, 0))
        hits = {}
        for n, f in fixed:
            v = rr.intersect(f); vol = v.val().Volume() if v.vals() else 0
            if vol > 0.01: hits[n] = round(vol, 2)
        out[d] = hits
    return out


parts = [('160_rail_R_guided', rail_R, 2, 'PETG'), ('161_rail_L_floating', rail_L, 2, 'PETG'),
         ('162_station_R', stF, 0, 'PETG'), ('162_station_L', R.mirror_x(stF), 0, 'PETG'),
         ('164_guide_block_R', gd, 0, 'PETG'), ('165_625_pocket_coupon', coupon(), 0, 'PETG')]
report = []
for name, shp, how, mat in parts:
    if how == 2:
        w = shp.rotate((0, 0, 0), (0, 1, 0), -90 if '_R_' in name else 90)
        bedp, diag = print_pose(w, diag=False)
    else:
        bedp, diag = print_pose(shp)
    export(bedp, OUT / f'{name}_PRINT_1.stl')
    g = grams(shp, 1.27)
    report.append({'part': name, 'qty': 1, **bed_fit(bedp), 'bed_face': 'closed web down (slot up)' if how == 2 else 'foot down', 'grams_PETG': g, 'hours': hours(g)})
chk = check()
(OUT / 'runner_test_parts.json').write_text(json.dumps({'interface': 'v14-interface-5.1', 'parts': report, 'sweep_check_right_rail_mm': chk,
    'bought': [{'item': '625ZZ', 'qty': 8}, {'item': 'M5 x 25 screw + nut', 'qty': 6}, {'item': 'M5 x 16 screw', 'qty': 2},
               {'item': 'M3 insert', 'qty': 8}, {'item': 'M3 x 12 screw', 'qty': 2}, {'item': '#6 x 3/4 wood screw', 'qty': 10}]}, indent=1))
for r in report: print(r)
print(chk)
items = [(rail_R.translate((200, R.RAIL_Y0_WORLD + 150, 0)), (0.95, 0.55, 0.15), 1), (rail_L.translate((-200, R.RAIL_Y0_WORLD + 150, 0)), (0.95, 0.55, 0.15), 1)]
for s_ in (stF, gd): items.append((s_.translate((200, 0, 0)), (0.25, 0.45, 0.75), 1))
items.append((R.mirror_x(stF).translate((-200, 0, 0)), (0.25, 0.45, 0.75), 1))
for r in rF + rG: items.append((r.translate((200, 0, 0)), (0.75, 0.75, 0.78), 1))
for r in rF: items.append((R.mirror_x(r).translate((-200, 0, 0)), (0.75, 0.75, 0.78), 1))
ply = cq.Workplane().box(720, 360, 12, centered=(True, True, False))
items.append((ply, (0.85, 0.75, 0.55), 0.5))
render(items, OUT / 'runner_test_extended.png', cam=(700, -500, 420), focal=(0, 120, 20), title='Runner test 5.1: rails 160/161 at the 150 mm stop on 625ZZ stations screwed to the plywood floor')
