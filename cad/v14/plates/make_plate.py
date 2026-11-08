"""Pack print-ready STLs onto P2S plates and write one .3mf per plate (separate objects, already arranged).
Bambu Studio opens it as a project-less 3MF ("load geometry only" is fine); every part stays its own object.
Usage: python3 make_plate.py OUT_NAME file1.stl[:qty] file2.stl[:qty] ...   -> OUT_NAME.3mf (or _plate1/_plate2 if it spills)
"""
import sys, struct, zipfile
from pathlib import Path
import numpy as np

BED = 240.0; GAP = 6.0       # usable 248 minus a margin for skirt/purge


def read_stl(p):
    b = Path(p).read_bytes()
    if b[:5] == b'solid' and b'facet' in b[:300]:
        v = [list(map(float, l.split()[1:4])) for l in b.decode(errors='ignore').splitlines() if l.strip().startswith('vertex')]
        tri = np.array(v, dtype=float).reshape(-1, 3, 3)
    else:
        n = struct.unpack('<I', b[80:84])[0]
        a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
        tri = a['v'].reshape(-1, 3, 3).astype(float)
    tri[:, :, 2] -= tri[:, :, 2].min()
    return tri


def mesh_xml(tri):
    verts, idx = np.unique(np.round(tri.reshape(-1, 3), 5), axis=0, return_inverse=True)
    faces = idx.reshape(-1, 3)
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    vx = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    fx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return f'<mesh><vertices>{vx}</vertices><triangles>{fx}</triangles></mesh>'


def pack(items):
    """shelf packing, biggest first. items: (name, tri). returns list of plates, each a list of (name, tri moved)."""
    items = sorted(items, key=lambda t: -(np.ptp(t[1][:, :, 1]) * 1000 + np.ptp(t[1][:, :, 0])))
    plates, cur, x, y, shelf = [], [], 0.0, 0.0, 0.0
    for name, tri in items:
        w, d = np.ptp(tri[:, :, 0]), np.ptp(tri[:, :, 1])
        if w > BED and d <= BED and w <= 248: pass
        if x + w > BED:
            x, y, shelf = 0.0, y + shelf + GAP, 0.0
        if y + d > BED:
            plates.append(cur); cur, x, y, shelf = [], 0.0, 0.0, 0.0
        t = tri.copy()
        t[:, :, 0] += x - tri[:, :, 0].min(); t[:, :, 1] += y - tri[:, :, 1].min()
        cur.append((name, t)); x += w + GAP; shelf = max(shelf, d)
    if cur: plates.append(cur)
    out = []
    for pl in plates:            # centre each plate on the 256 bed
        allv = np.concatenate([t.reshape(-1, 3) for _, t in pl])
        cx = 128 - (allv[:, 0].min() + allv[:, 0].max()) / 2; cy = 128 - (allv[:, 1].min() + allv[:, 1].max()) / 2
        out.append([(n, t + np.array([cx, cy, 0])) for n, t in pl])
    return out


def write_3mf(path, plate):
    objs, build = [], []
    for k, (name, tri) in enumerate(plate, 1):
        objs.append(f'<object id="{k}" name="{name}" type="model">{mesh_xml(tri)}</object>')
        build.append(f'<item objectid="{k}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>' + ''.join(objs) +
             '</resources><build>' + ''.join(build) + '</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct); z.writestr('_rels/.rels', rels); z.writestr('3D/3dmodel.model', model)


def make(out, specs):
    items = []
    for s in specs:
        f, q = (s.rsplit(':', 1) + ['1'])[:2] if ':' in Path(s).name else (s, '1')
        tri = read_stl(f); stem = Path(f).stem.split('_PRINT')[0]
        for i in range(int(q)): items.append((stem if int(q) == 1 else f'{stem}_{i+1}', tri))
    plates = pack(items)
    paths = []
    for k, pl in enumerate(plates, 1):
        p = Path(f'{out}.3mf' if len(plates) == 1 else f'{out}_plate{k}.3mf'); write_3mf(p, pl); paths.append(p)
        print(p, len(pl), 'parts')
    return paths


if __name__ == '__main__':
    make(sys.argv[1], sys.argv[2:])
