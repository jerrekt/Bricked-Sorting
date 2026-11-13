"""Support check for print-ready STLs (as posed on the bed).
For every flat down-facing area (normal within ~11 deg of straight down) above the first layer, take the part's cross-section
just below it: what is NOT over material below is a floating area. A floating area is fine as a bridge if every point is
within BRIDGE/2 of material below (Bambu bridges ~20-25 mm in PLA cleanly). Steep overhangs (45-79 deg) are listed separately
by area. Output per part: worst bridge span (mm), floating area beyond the bridge limit (mm2), steep-overhang area (mm2).
Usage: python3 support_check.py files...
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

BRIDGE = 20.0


def tri_polys(tris):
    out = []
    for t in tris:
        p = Polygon(t[:, :2])
        if p.is_valid and p.area > 1e-4: out.append(p)
    return unary_union(out) if out else Polygon()


def section_below(mesh, z):
    try:
        s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if s is None: return Polygon()
        p, _ = s.to_planar(to_2D=np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -z], [0, 0, 0, 1]]))
        return unary_union([g for g in p.polygons_full]) if p.polygons_full else Polygon()
    except Exception:
        return Polygon()


def check(f):
    m = trimesh.load(f, force='mesh')
    m.apply_translation([0, 0, -m.bounds[0][2]])
    n = m.face_normals; t = m.triangles; zc = t[:, :, 2].mean(1)
    flat = (n[:, 2] < -0.98) & (zc > 0.25)
    steep = (n[:, 2] < -0.71) & (n[:, 2] >= -0.98) & (zc > 0.25)
    worst, bad = 0.0, 0.0
    for z in np.unique(np.round(zc[flat], 2)):
        reg = tri_polys(t[flat & (np.round(zc, 2) == z)])
        if reg.is_empty: continue
        below = section_below(m, z - 0.3)
        floating = reg.difference(below.buffer(0.01))
        if floating.is_empty or floating.area < 1: continue
        # max distance from floating area to supported edge ~ half the bridge span
        d, lo, hi = 0.0, 0.0, 200.0
        for _ in range(14):
            mid = (lo + hi) / 2
            if floating.buffer(-mid).is_empty: hi = mid
            else: lo = mid
        span = 2 * lo
        worst = max(worst, span)
        if span > BRIDGE: bad += floating.area
    st = m.area_faces[steep].sum()
    return worst, bad, st


if __name__ == '__main__':
    rows = []
    for f in sys.argv[1:]:
        try: w, b, s = check(f)
        except Exception as e: print('ERR', f, e); continue
        rows.append((b, w, s, f.split('/')[-1].replace('_PRINT', '').replace('.stl', '')))
    print(f'{"needs support mm2":>17} {"worst span mm":>13} {"steep mm2":>9}  part')
    for b, w, s, nm in sorted(rows, reverse=True):
        print(f'{b:17.0f} {w:13.1f} {s:9.0f}  {nm}')
