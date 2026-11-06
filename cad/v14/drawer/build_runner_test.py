"""Runner test kit, interface 4 (print this first): one drawer's worth of runners.
Right rail (guided) + left rail (floating, mirror), 4 roller stations, 1 guide block.
Mount the floor parts on a board with the rails 600 apart (or any spacing; keep
them parallel), bolt a plank across the two rail tops, load it and pull."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import print_pose, bed_fit, export, grams, render, bbox
import runner as R
import cadquery as cq

OUT = HERE / 'runner_test'
INS = [140, 180, 220, 260]
DET = R.ROLLERS_Y[3] - R.RAIL_Y0_WORLD - 6.0
rail_R = R.rail(insert_ys=INS, detent_y=DET)
rail_L = R.mirror_x(rail_R)
stF, rF, _ = R.station(R.ROLLERS_Y[2:], rail_x_world=300)
stB, rB, _ = R.station(R.ROLLERS_Y[:2], slotted_index=0, rail_x_world=300)
gd, rG, _ = R.guide_block((175.0, 215.0), rail_x_world=300)

def check():
    """sweep the right rail 0..205 past its rollers and blocks."""
    fixed = [('front_station', stF), ('rear_station', stB), ('guide', gd)] + [(f'roller_{i}', r) for i, r in enumerate(rF + rB + rG)]
    out = {}
    for d in (0, 3, 6, 10, 50, 100, 150, 200, 205, 206, 208):
        rr = rail_R.translate((0, R.RAIL_Y0_WORLD + d, 0))
        hits = {}
        for n, f in fixed:
            v = rr.intersect(f)
            vol = v.val().Volume() if v.vals() else 0
            if vol > 0.01: hits[n] = round(vol, 2)
        out[d] = hits
    return out

parts = [('160_rail_R_guided', rail_R, 2, 1), ('161_rail_L_floating', rail_L, 2, 1),
         ('162_station_front_R', stF, 0, 1), ('162_station_front_L', R.mirror_x(stF), 0, 1),
         ('163_station_rear_preload_R', stB, 0, 1), ('163_station_rear_preload_L', R.mirror_x(stB), 0, 1), ('164_guide_block_R', gd, 0, 1)]
report = []
for name, shp, how, qty in parts:
    if how == 2:   # rail on its side, closed web down, slot opening up
        w = shp.rotate((0, 0, 0), (0, 1, 0), -90 if 'R' in name else 90)
        bedp, diag = print_pose(w)
    else:
        bedp, diag = print_pose(shp)
    export(bedp, OUT / f'{name}_PRINT_{qty}.stl')
    report.append({'part': name, 'qty': qty, **bed_fit(bedp), 'diagonal_on_bed': diag, 'grams_each_PETG': grams(shp, 1.27)})
chk = check()
(OUT / 'runner_test_parts.json').write_text(json.dumps({'parts': report, 'sweep_check_right_rail': chk,
    'bought': [{'item': '625ZZ', 'qty': 10}, {'item': 'M5 x 25 screw + nut', 'qty': 8}, {'item': 'M5 x 16 screw', 'qty': 2},
               {'item': 'M3 insert', 'qty': 8}, {'item': 'M3 x 12 screw', 'qty': 2}]}, indent=1))
for r in report: print(r)
print(chk)
items = [(rail_R.translate((300, R.RAIL_Y0_WORLD + 205, 0)), (0.95, 0.55, 0.15), 1), (rail_L.translate((-300, R.RAIL_Y0_WORLD + 205, 0)), (0.95, 0.55, 0.15), 1)]
for s in (stF, stB, gd):
    items.append((s.translate((300, 0, 0)), (0.25, 0.45, 0.75), 1))
for s in (stF, stB):
    items.append((R.mirror_x(s).translate((-300, 0, 0)), (0.25, 0.45, 0.75), 1))
for r in rF + rB + rG:
    items.append((r.translate((300, 0, 0)), (0.75, 0.75, 0.78), 1))
for r in rF + rB:
    items.append((R.mirror_x(r).translate((-300, 0, 0)), (0.75, 0.75, 0.78), 1))
render(items, OUT / 'runner_test_extended.png', cam=(900, -500, 450), focal=(0, 250, 20), title='Runner test (interface 4): rails 160/161 at the 205 mm stop, roller stations 162/163, guide 164')
sec = cq.Workplane().box(60, 4, 60).translate((300, 225, 20))
render([(rail_R.translate((300, R.RAIL_Y0_WORLD, 0)).intersect(sec), (0.95, 0.55, 0.15), 1), (stF.translate((300, 0, 0)).intersect(sec), (0.25, 0.45, 0.75), 1),
        (rF[1].translate((300, 0, 0)).intersect(sec), (0.75, 0.75, 0.78), 1)], OUT / 'runner_section.png', cam=(300, -300, 20), focal=(300, 225, 20), ortho=24,
       title='Section at the front roller: 16.5 slot, 625ZZ on an M5 axle in the floor station')
