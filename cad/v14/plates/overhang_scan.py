"""Scan print STLs for unsupported downward faces (steeper than 45 deg from vertical, i.e. normal z < -0.71) above the first layer."""
import sys, glob, numpy as np
sys.path.insert(0, '.')
import make_plate as mp
rows = []
for f in sys.argv[1:]:
    t = mp.read_stl(f)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); a = np.linalg.norm(n, axis=1); ok = a > 1e-9
    n, a, t = n[ok] / a[ok][:, None], a[ok] / 2, t[ok]
    zc = t[:, :, 2].mean(1)
    m = (n[:, 2] < -0.71) & (zc > 0.3)
    flat = (n[:, 2] < -0.98) & (zc > 0.3)
    rows.append((a[m].sum(), a[flat].sum(), f.split('/')[-1].replace('_PRINT', '')))
for ov, fl, nm in sorted(rows, reverse=True):
    if ov > 30: print(f'{ov:8.0f} {fl:8.0f}  {nm}')
