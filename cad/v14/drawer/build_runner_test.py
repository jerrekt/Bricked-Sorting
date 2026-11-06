"""Runner test kit for the V14 drawer killer test (print this first).
1) fit coupon: 60 mm rail + three 50 mm bars at 0.20 / 0.30 / 0.40 per side
   (2 / 3 / 4 notches on the flange edge). Pick the one that slides freely
   with no wobble; tell Claude, and the full rails get that number.
2) full-length pair: 2 fixed rails (318) + 2 moving bars (314), the exact
   runner the drawers use (stop groove, detent, holes on the 40 mm grid).
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import print_pose, bed_fit, export, extent, grams
import runner as R

OUT = HERE / 'runner_test'
holes = [42 + 40*k for k in range(7)]          # local y, same pitch as the floor grid
inserts = [140, 180, 220, 260, 300]
parts = {
  '150_runner_rail': (R.fixed_rail(hole_ys=holes), False, 2),
  '151_runner_bar': (R.moving_bar(insert_ys=inserts), True, 2),
  '150c_coupon_rail_60': (R.fixed_rail(60, stop=False, detent=False, hole_ys=[30]), False, 1),
}
for clr, n in ((0.20, 2), (0.30, 3), (0.40, 4)):
    parts[f'151c_coupon_bar_{int(clr*100):02d}'] = (R.moving_bar(50, clr=clr, tooth=False, notches=n), True, 1)

report = []
for name, (shape, flip, qty) in parts.items():
    bedp, diag = print_pose(shape, flip=flip)
    export(bedp, OUT / f'{name}_PRINT_{qty}.stl')
    export(shape, OUT / f'{name}.step')
    report.append({'part': name, 'qty': qty, 'orientation': ('flange down' if flip else 'base down') + (', 45 deg on the bed' if diag else ''),
                   **bed_fit(bedp), 'grams_each_PETG': grams(shape)})
(OUT / 'runner_test_parts.json').write_text(json.dumps(report, indent=1))
for r in report: print(r)
