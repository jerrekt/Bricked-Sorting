"""V14 integration, interface 5.1: load every module's world/ STEPs and check the whole machine.
Modules: F from cad-v14-frame5, K from cad-v14-deck5 (worktrees given below), D and S from this branch.
Checks: cross-module clashes (drawers closed / both open, scoop at 17 poses, deck, frame), envelope, totals
(grams/hours from each parts.json), merged buy list, stills and a one-brick animation (GIF).
Run: python3 build_integration.py
"""
import json, math, sys, importlib.util
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import IF, bbox, render

WT_FRAME = Path('/home/claude/wt_frame5/cad/v14/frame'); WT_DECK = Path('/home/claude/wt_deck5/cad/v14/deck')
DRAWER = HERE.parent / 'drawer'; SCOOP = HERE.parent / 'scoop'
E = IF['envelope']; TRAVEL = IF['drawer']['travel_y']


def load_dir(d, skip=('assembly', '_ink')):
    out = []
    for p in sorted(Path(d).glob('*.step')):
        if any(s in p.name for s in skip): continue
        try:
            out.append((p.stem, cq.Workplane().add(cq.importers.importStep(str(p)).val())))
        except Exception as e:
            print('skip', p.name, e)
    return out


def _ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def clash(A, B, thr=0.5):
    hits = []
    bb = [(n, s, bbox(s)) for n, s in B]
    for n, s in A:
        b = bbox(s)
        for m, t, bt in bb:
            if _ov(b, bt):
                v = s.intersect(t); vol = v.val().Volume() if v.vals() else 0
                if vol > thr: hits.append([n, m, round(vol, 1)])
    return hits


def main():
    F = load_dir(WT_FRAME / 'world'); K = load_dir(WT_DECK / 'world'); D = load_dir(DRAWER / 'world'); S = load_dir(SCOOP / 'world')
    # scoop poses: rebuild moving parts from the scoop script
    spec = importlib.util.spec_from_file_location('bs', SCOOP / 'build_scoop.py'); bs = importlib.util.module_from_spec(spec)
    sys.argv = ['x']; spec.loader.exec_module(bs)
    S_fixed = [(n, s) for n, s in S if not n.endswith('_at_receive') and n not in ('NEMA17_dummy',)] + [('NEMA17', bs.motor_dummy())]
    moving_D = ('160_', '166_', '167_', '168_', '169_', '170_')
    D_open = [(n, s.translate((0, TRAVEL if n.startswith('front') else -TRAVEL, 0)) if any(k in n for k in moving_D) else s) for n, s in D]
    res = {'interface': IF['version'], 'modules': {'F': len(F), 'K': len(K), 'D': len(D), 'S_fixed': len(S_fixed)}}
    res['F_vs_D_closed'] = clash(F, D); res['F_vs_D_open'] = clash(F, D_open)
    res['F_vs_K'] = clash(F, K); res['F_vs_S_fixed'] = clash(F, S_fixed)
    res['K_vs_S_fixed'] = clash(K, S_fixed); res['K_vs_D_closed'] = clash(K, D); res['D_vs_S_fixed'] = clash(D, S_fixed)
    poses = {}
    for name, xc, tilt in bs.poses():
        mv = bs.moving_at(xc, tilt)
        parts = [('carriage', mv['carriage']), ('bracket', mv['bracket']), ('servo', mv['servo']), ('cup', mv['cup']), ('link', mv['link']), ('lead', mv['lead'])] + [(f'roller_{k}', r) for k, r in enumerate(mv['rollers'])]
        poses[name] = {'vs_F': clash(parts, F), 'vs_K': clash(parts, K), 'vs_D_closed': clash(parts, D)}
    res['scoop_poses'] = poses
    allp = F + K + D + S_fixed
    bbs = [bbox(s) for n, s in allp]
    env = [min(b[0] for b in bbs), min(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs), max(b[4] for b in bbs), max(b[5] for b in bbs)]
    res['envelope'] = {'bbox': [round(v, 1) for v in env], 'limit': E, 'ok': env[0] >= E['x'][0] - .01 and env[3] <= E['x'][1] + .01 and env[1] >= E['y'][0] - .01 and env[4] <= E['y'][1] + .01 and env[2] >= -0.01 and env[5] <= E['z'][1] + .01}
    # totals
    pf = json.loads((WT_FRAME / 'parts.json').read_text()); pk = json.loads((WT_DECK / 'parts.json').read_text())
    pd = json.loads((DRAWER / 'parts.json').read_text()); ps = json.loads((SCOOP / 'parts.json').read_text())
    tot = {'F_frame_skin': (pf['totals']['printed_grams'], pf['totals']['printed_hours']), 'K_deck': (pk['est_total_grams_new_parts'], pk['est_total_hours_new_parts']),
           'D_drawers': (pd['est_total_grams'], pd['est_total_hours']), 'S_scoop': (ps['est_total_grams'], ps['est_total_hours'])}
    res['printed_totals'] = {k: {'grams': v[0], 'hours': v[1]} for k, v in tot.items()}
    res['printed_totals']['ALL'] = {'grams': round(sum(v[0] for v in tot.values())), 'hours': round(sum(v[1] for v in tot.values()), 1),
                                    'budget': IF['budget']}
    bought = {}
    for mod, p in (('F', pf), ('K', pk), ('D', pd), ('S', ps)):
        for b in p.get('bought', []):
            bought.setdefault(b['item'], []).append({'module': mod, 'qty': b.get('qty'), 'use': b.get('use', '')})
    res['bought_merged'] = bought
    res['wood'] = pf.get('wood')
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    # ---------- stills ----------
    def col(n):
        if n.startswith(('110', '111', '112', '113', '114', '115', '135')): return (0.72, 0.10, 0.10)
        if n.startswith(('130', '131')): return (0.80, 0.18, 0.18)
        if n.startswith('100') or 'ply' in n: return (0.85, 0.75, 0.55)
        if n.startswith(('12',)): return (0.4, 0.4, 0.42)
        if n.startswith(('47', '48', '49')): return (0.75, 0.25, 0.2)
        if n.startswith(('201', '202')): return (0.85, 0.2, 0.2)
        if n.startswith(('203', '204')): return (0.2, 0.6, 0.4)
        if n.startswith('2'): return (0.45, 0.45, 0.5)
        if '169_bin' in n: return (0.96, 0.87, 0.65)
        if '167_' in n: return (0.1, 0.35, 0.7)
        if '168_' in n: return (0.1, 0.55, 0.3)
        if n.startswith(('180', '18', '19')): return (0.55, 0.57, 0.62)
        return (0.8, 0.8, 0.82)
    skin = lambda n: n.startswith(('110', '111', '112', '113', '114', '115', '13'))
    full = [(s, col(n), 1.0) for n, s in allp]
    render(full, HERE / 'still_1_machine.png', cam=(-1100, 1500, 900), focal=(0, 0, 330), title='V14 (5.1): 720 x 360 x 664, wood frame + red skin, drawers F/B, hopper stud left')
    inside = [(s, col(n), 1.0) for n, s in allp if not skin(n)] + [(s, col(n), 0.25) for n, s in F if n.startswith(('110', '111', '112', '113'))]
    mv = bs.moving_at(bs.X_RECEIVE, 0)
    inside += [(mv['carriage'], (0.95, 0.55, 0.15), 1), (mv['cup'], (0.98, 0.8, 0.2), 1), (mv['bracket'], (0.95, 0.55, 0.15), 1), (mv['servo'], (0.15, 0.25, 0.6), 1)]
    render(inside, HERE / 'still_2_inside.png', cam=(-1000, 1300, 800), focal=(0, 0, 320), title='Skin and roof off: drawers on the plywood floor, scoop beam, deck with drum / trays / scanner')
    openD = [(s, col(n), 1.0) for n, s in D_open] + [(s, col(n), 1.0) for n, s in F if n.startswith(('100', '110', '112', '135'))]
    render(openD, HERE / 'still_3_drawers_open.png', cam=(900, 1500, 700), focal=(0, 0, 120), title='Both drawers out 150 through the skin openings')
    # ---------- one-brick animation ----------
    try:
        from PIL import Image
        frames = []
        steps = [('receive', bs.X_RECEIVE, 0.0), ('carry', (bs.X_RECEIVE + bs.XC[2]) / 2, 0.0), ('arrive', bs.XC[2], 0.0), ('tilt', bs.XC[2], -20.0),
                 ('dump', bs.XC[2], -40.0), ('drop', bs.XC[2], -40.0), ('back', bs.XC[2], 0.0), ('return', (bs.X_RECEIVE + bs.XC[2]) / 2, 0.0), ('park', bs.X_RECEIVE, 0.0)]
        base = [(s, col(n), 1.0) for n, s in allp if not skin(n) and not n.endswith('_at_receive')]
        for k, (nm, xc, tilt) in enumerate(steps):
            mv = bs.moving_at(xc, tilt)
            it = base + [(mv['carriage'], (0.95, 0.55, 0.15), 1), (mv['cup'], (0.98, 0.8, 0.2), 1), (mv['bracket'], (0.95, 0.55, 0.15), 1), (mv['servo'], (0.15, 0.25, 0.6), 1), (mv['link'], (0.75, 0.75, 0.78), 1)]
            if nm in ('receive', 'carry', 'arrive', 'tilt'):
                it.append((cq.Workplane().box(16, 32, 10).translate((xc, 0, bs.PIVOT_Z + 5 + 5)), (0.1, 0.4, 0.9), 1))
            elif nm == 'dump':
                it.append((cq.Workplane().box(16, 32, 10).translate((xc, 60, 195)), (0.1, 0.4, 0.9), 1))
            elif nm == 'drop':
                it.append((cq.Workplane().box(16, 32, 10).translate((xc, 102, 60)), (0.1, 0.4, 0.9), 1))
            f = HERE / f'anim_{k:02d}.png'
            render(it, f, cam=(-700, 1100, 600), focal=(0, 40, 250), title=f'one brick: {nm}')
            frames.append(Image.open(f).convert('P', palette=Image.ADAPTIVE))
        frames[0].save(HERE / 'one_brick.gif', save_all=True, append_images=frames[1:], duration=700, loop=0)
        for k in range(len(steps)): (HERE / f'anim_{k:02d}.png').unlink()
    except Exception as e:
        print('animation skipped:', e)
    return res


if __name__ == '__main__':
    r = main()
    for k in ('F_vs_D_closed', 'F_vs_D_open', 'F_vs_K', 'F_vs_S_fixed', 'K_vs_S_fixed', 'K_vs_D_closed', 'D_vs_S_fixed'):
        print(k, len(r[k]), r[k][:6])
    bad = {k: v for k, v in r['scoop_poses'].items() if v['vs_F'] or v['vs_K'] or v['vs_D_closed']}
    print('scoop pose hits:', {k: {kk: vv[:3] for kk, vv in v.items() if vv} for k, v in bad.items()})
    print('envelope', r['envelope']); print('totals', r['printed_totals'])
