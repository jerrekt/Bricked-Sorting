"""Try the 6 axis-aligned 'face down' orientations (plus 90 deg about z irrelevant) for each STL; report unsupported area
(floating flat area beyond a 20 mm bridge + steep 45-79 deg overhang area) and height, best first."""
import sys, numpy as np, trimesh
sys.path.insert(0, '.')
import support_check as sc

ROTS = {'as posed': np.eye(4),
        'flip (upside down)': trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]),
        '+x down': trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]),
        '-x down': trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),
        '+y down': trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]),
        '-y down': trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])}


def score(m):
    m = m.copy(); m.apply_translation([0, 0, -m.bounds[0][2]])
    tmp = '/tmp/claude-0/-home-claude/38203d7b-0ae1-5337-ba48-005611569a1c/scratchpad/_o.stl'; m.export(tmp)
    w, b, s = sc.check(tmp)
    ext = m.extents
    return b, s, w, ext


if __name__ == '__main__':
    for f in sys.argv[1:]:
        base = trimesh.load(f, force='mesh')
        res = []
        for nm, R in ROTS.items():
            m = base.copy(); m.apply_transform(R)
            b, s, w, ext = score(m)
            fits = max(ext[0], ext[1]) <= 248 and min(ext[0], ext[1]) <= 248 and ext[2] <= 248
            res.append((b + 0.3 * s, b, s, w, nm, ext.round(0), fits))
        res.sort(key=lambda r: (not r[6], r[0]))
        print(f.split('/')[-1].replace('_PRINT', ''))
        for r in res[:3]: print(f'   {r[4]:20s} support {r[1]:7.0f}  steep {r[2]:6.0f}  span {r[3]:5.1f}  size {r[5]}  fits {r[6]}')
