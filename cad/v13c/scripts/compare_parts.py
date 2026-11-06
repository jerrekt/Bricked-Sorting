"""V13 vs V13C printed-part survival. A part 'survives unchanged' when its print-pose STEP has the same volume
(+-1 mm3) and the same sorted bounding box (+-0.1 mm) as the V13 baseline rebuild (which matches the repo's V13
STEPs exactly). Parts loaded from V13 STEPs unchanged (carriage V3, drum V7/V13) survive by construction.
Counts: unique designs, and printed pieces (PRINT_n multiplicity)."""
from pathlib import Path
import json, re
import cadquery as cq
ROOT = Path(__file__).resolve().parent
def sig(p):
    s = cq.importers.importStep(str(p)).val(); bb = s.BoundingBox()
    return round(s.Volume()), sorted(round(x, 1) for x in (bb.xlen, bb.ylen, bb.zlen))
def same(a, b): return abs(a[0] - b[0]) <= 1 and all(abs(x - y) <= 0.1 for x, y in zip(a[1], b[1]))
def qty(n):
    m = re.search(r'PRINT_(\d+)', n); return int(m.group(1)) if m else (2 if n.endswith('_PRINT_TWICE') else 1)
rows = []
for d0, d1 in (('machine_v13', 'machine_v13c'), ('bins_v13', 'bins_v13c')):
    for f in sorted((ROOT / d0).glob('*.step')):
        n = f.stem
        if n.startswith('V10_TIERS') or n in ('52_drum_cradle_L', '52_drum_cradle_R'): continue
        g = ROOT / d1 / f.name
        q = qty(n)
        if n.startswith('52_drum_cradle'): q = 1
        if n.startswith('56_tray_support'): q = 2         # V13 print list: 2 of each exported post design
        rows.append({'part': n, 'qty': q, 'unchanged': g.exists() and same(sig(f), sig(g)), 'source': 'generated'})
for n in ('01_ground_base', '02_moving_carriage_v3', '03_top_rod_brace', '04_lower_switch_mount', '06_angled_shaft_hub',
          '07_upper_switch_rod_mount', '10_M2_switch_backer_PRINT_TWICE', '47b_tumbler_barrel_helical_flight', '49b_drum_static_outlet_plate',
          '48_drum_rear_feed_guard', '50_drum_625_bearing_roller', '54_drum_drive_core_5mm', '55_drum_friction_tire_TPU', '56_drum_NEMA17_adjustable_bracket'):
    rows.append({'part': n, 'qty': 4 if n.startswith('50_') else qty(n), 'unchanged': True, 'source': 'V13 STEP reused'})
u = [r for r in rows if r['unchanged']]
res = {'rule': __doc__.strip(), 'designs_total': len(rows), 'designs_unchanged': len(u), 'designs_pct': round(100 * len(u) / len(rows), 1),
       'pieces_total': sum(r['qty'] for r in rows), 'pieces_unchanged': sum(r['qty'] for r in u),
       'changed': [r['part'] for r in rows if not r['unchanged']], 'rows': rows}
res['pieces_pct'] = round(100 * res['pieces_unchanged'] / res['pieces_total'], 1)
(ROOT.parent / 'part_survival.json').write_text(json.dumps(res, indent=1) + '\n')
print({k: res[k] for k in ('designs_total', 'designs_unchanged', 'designs_pct', 'pieces_total', 'pieces_unchanged', 'pieces_pct')}); print('changed:', res['changed'])
