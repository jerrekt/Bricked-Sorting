"""Re-pose print STLs for no supports. For each STL, try the 6 face-down orientations; keep the designer's pose if it already
needs at most 50 mm2 more support than the best pose and its steep (45-79 deg) area is within 300 mm2 of the best; otherwise
take the best one that fits the bed (support, then steep area, then height). Rewrites the STL in place and prints a report.
Usage: python3 auto_orient.py [--dry] files..."""
import sys, json, numpy as np, trimesh
sys.path.insert(0, __import__('os').path.dirname(__file__))
from orient_search import ROTS, score

# designer's pose kept on purpose: leaf springs (layer lines along the blade), stud 130 (45 deg ledge is fine), box-beam
# segments (25 mm end-cap bridge is fine), drawer faces and skin tiles (smooth outer face on the bed)
KEEP = ('207_leaf_spring', '130_stud', '180_beam_seg', '167_face', '168_face', '110_tile', '111_tile', '112_tile', '113_tile', '114_roof', '115_')
dry = '--dry' in sys.argv
files = [f for f in sys.argv[1:] if not f.startswith('--')]
report = {}
for f in files:
    if '_ink_' in f or f.split('/')[-1].startswith(KEEP): continue                 # inlays ride with their face
    base = trimesh.load(f, force='mesh')
    res = []
    for nm, R in ROTS.items():
        m = base.copy(); m.apply_transform(R)
        b, s, w, ext = score(m)
        fits = max(ext[0], ext[1]) <= 248 and ext[2] <= 248
        if not fits and min(ext[0], ext[1]) <= 248 and np.hypot(*ext[:2]) / np.sqrt(2) <= 248: fits = True   # diagonal
        res.append(dict(name=nm, R=R, support=b, steep=s, h=ext[2], fits=fits))
    cand = [r for r in res if r['fits']]
    best = min(cand, key=lambda r: (round(r['support']), r['steep'] * 0.3 + r['h']))
    posed = res[0]
    keep = posed['fits'] and posed['support'] <= best['support'] + 50 and posed['steep'] <= best['steep'] + 300
    pick = posed if keep else best
    report[f.split('/')[-1]] = dict(pose=pick['name'], support=round(pick['support']), steep=round(pick['steep']),
                                     was=dict(support=round(posed['support']), steep=round(posed['steep'])))
    if not keep and not dry:
        m = base.copy(); m.apply_transform(pick['R'])
        b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        m.export(f)
        ink = f.replace('_PRINT', '_ink_PRINT')
if not dry and files:
    out = __import__('pathlib').Path(files[0]).parent / 'ORIENT.json'
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update({k: {kk: vv for kk, vv in v.items()} for k, v in report.items()}); out.write_text(json.dumps(old, indent=1))
for k, v in report.items():
    flag = '' if v['pose'] == 'as posed' else '  <- re-posed'
    print(f"{k:55s} {v['pose']:20s} support {v['support']:6d} steep {v['steep']:6d}  (was {v['was']['support']}/{v['was']['steep']}){flag}")
