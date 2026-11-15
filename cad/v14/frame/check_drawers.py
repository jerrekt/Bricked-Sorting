import cadquery as cq, glob, os, json, sys
sys.path.insert(0, '/home/claude/bricked-sorting/cad/v14/deck')
from k_common import bbox, ov, vol, boxc, cyl
IF = json.load(open('/home/claude/bricked-sorting/cad/v14/interface.json'))
OP = IF['skin']['drawer_openings']['front_and_back_walls']
def load(d, skip=()):
    out = []
    for f in sorted(glob.glob(d + '/*.step')):
        n = os.path.basename(f)[:-5]
        if n.endswith('_assembly') or any(s in n for s in skip): continue
        try: out.append((n, cq.importers.importStep(f)))
        except Exception as e: print('skip', n, e)
    return out
D = load('/home/claude/drawer_ref/cad/v14/drawer/world', skip=('_ink',))
F = load('/home/claude/xcheck/cad/v14/frame/world')
K = load('/home/claude/bricked-sorting/cad/v14/deck/world')
print(len(D), 'drawer parts', len(F), 'frame parts', len(K), 'deck parts')
res = {}
for nm, other in (('frame', F), ('deck', K)):
    hits = []
    ob = [(l, w, bbox(w)) for l, w in other]
    for dl, dw in D:
        db = bbox(dw)
        for ol, ow, obb in ob:
            if ov(db, obb):
                v = vol(dw, ow)
                if v > 0.5: hits.append([dl, ol, round(v, 1)])
    res[nm] = hits
    print(nm, 'clashes:', len(hits)); [print('  ', h) for h in hits[:30]]
# drawer travel: translate each drawer +-150 (front +Y, back -Y) through the skin opening and check frame skin + wood
front = [(l, w) for l, w in D if l.startswith('front')]; back = [(l, w) for l, w in D if l.startswith('back')]
Fb = [(l, w, bbox(w)) for l, w in F]
for nm, grp, dy in (('front_open', front, 150.0), ('back_open', back, -150.0)):
    hits = []
    for t in (50.0, 100.0, 150.0):
        for dl, dw in grp:
            if 'rail' in dl or 'station' in dl or 'guide' in dl or '625' in dl or 'KW11' in dl or 'switch' in dl: continue
            mw = dw.translate((0, dy * t / 150.0, 0)); mb = bbox(mw)
            for ol, ow, obb in Fb:
                if ov(mb, obb):
                    v = vol(mw, ow)
                    if v > 0.5: hits.append([round(t), dl, ol, round(v, 1)])
    res[nm] = hits; print(nm, 'clashes while opening:', len(hits)); [print('  ', h) for h in hits[:20]]
# extents vs opening
for nm, grp in (('front', front), ('back', back)):
    body = [bbox(w) for l, w in grp if 'face' not in l and 'rail' not in l and 'station' not in l and 'guide' not in l and '625' not in l and 'KW' not in l and 'switch' not in l]
    face = [bbox(w) for l, w in grp if 'face' in l]
    print(nm, 'body x', min(b[0] for b in body), max(b[3] for b in body), 'z', min(b[2] for b in body), max(b[5] for b in body), '| opening x', OP['x'], 'z', OP['z'])
    print(nm, 'face x', min(b[0] for b in face), max(b[3] for b in face), 'y', min(b[1] for b in face), max(b[4] for b in face), 'z', min(b[2] for b in face), max(b[5] for b in face))
json.dump(res, open('/home/claude/xcheck/drawer_vs_frame_deck.json', 'w'), indent=1)
