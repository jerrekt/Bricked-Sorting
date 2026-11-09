"""Pack print-ready STLs onto P2S plates and write one .3mf per plate (separate objects, already arranged).
Bambu Studio opens it as a project-less 3MF ("load geometry only" is fine); every part stays its own object.
Usage: python3 make_plate.py OUT_NAME file1.stl[:qty] file2.stl[:qty] ...   -> OUT_NAME.3mf (or _plate1/_plate2 if it spills)
"""
import sys, struct, zipfile
from pathlib import Path
import numpy as np

BED = 240.0; GAP = 6.0       # usable 248 minus a margin for skirt/purge


def read_stl(p, keep_z=False):
    b = Path(p).read_bytes()
    if b[:5] == b'solid' and b'facet' in b[:300]:
        v = [list(map(float, l.split()[1:4])) for l in b.decode(errors='ignore').splitlines() if l.strip().startswith('vertex')]
        tri = np.array(v, dtype=float).reshape(-1, 3, 3)
    else:
        n = struct.unpack('<I', b[80:84])[0]
        a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
        tri = a['v'].reshape(-1, 3, 3).astype(float)
    if not keep_z: tri[:, :, 2] -= tri[:, :, 2].min()
    return tri


def mesh_xml(tri):
    verts, idx = np.unique(np.round(tri.reshape(-1, 3), 5), axis=0, return_inverse=True)
    faces = idx.reshape(-1, 3)
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    vx = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    fx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return f'<mesh><vertices>{vx}</vertices><triangles>{fx}</triangles></mesh>'


def pack(items):
    """shelf packing, biggest first. items: (name, [(part, tri), ...]); a group moves as one.
    returns list of plates, each a list of (name, [(part, tri moved), ...])."""
    def bb(parts):
        a = np.concatenate([t.reshape(-1, 3) for _, t in parts]); return a.min(0), a.max(0)
    items = sorted(items, key=lambda it: -((bb(it[1])[1] - bb(it[1])[0])[1] * 1000 + (bb(it[1])[1] - bb(it[1])[0])[0]))
    plates, cur, x, y, shelf = [], [], 0.0, 0.0, 0.0
    for name, parts in items:
        lo, hi = bb(parts); w, d = hi[0] - lo[0], hi[1] - lo[1]
        if x + w > BED:
            x, y, shelf = 0.0, y + shelf + GAP, 0.0
        if y + d > BED and cur:
            plates.append(cur); cur, x, y, shelf = [], 0.0, 0.0, 0.0
        off = np.array([x - lo[0], y - lo[1], 0.0])
        cur.append((name, [(pn, t + off) for pn, t in parts])); x += w + GAP; shelf = max(shelf, d)
    if cur: plates.append(cur)
    out = []
    for pl in plates:            # centre each plate on the 256 bed
        allv = np.concatenate([t.reshape(-1, 3) for _, ps in pl for _, t in ps])
        c = np.array([128 - (allv[:, 0].min() + allv[:, 0].max()) / 2, 128 - (allv[:, 1].min() + allv[:, 1].max()) / 2, 0])
        out.append([(n, [(pn, t + c) for pn, t in ps]) for n, ps in pl])
    return out


def write_3mf(path, plate):
    """one build object per group; a group of 2+ parts is an object with components (Bambu: one object, several parts,
    each part can get its own filament, e.g. the white inlay on a drawer face)."""
    objs, build, k = [], [], 0
    for name, parts in plate:
        ids = []
        for pn, tri in parts:
            k += 1; objs.append(f'<object id="{k}" name="{pn}" type="model">{mesh_xml(tri)}</object>'); ids.append(k)
        if len(ids) == 1:
            build.append(f'<item objectid="{ids[0]}"/>')
        else:
            k += 1
            objs.append(f'<object id="{k}" name="{name}" type="model"><components>' + ''.join(f'<component objectid="{i}"/>' for i in ids) + '</components></object>')
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
    for s in specs:                       # "a.stl", "a.stl:3" (qty) or "a.stl+b.stl" (parts kept together, same frame)
        q = 1
        if ':' in Path(s).name: s, q = s.rsplit(':', 1); q = int(q)
        files = s.split('+')
        tris = [read_stl(f, keep_z=(len(files) > 1)) for f in files]
        if len(files) > 1:                 # drop the group as a whole onto the bed
            z0 = min(t[:, :, 2].min() for t in tris); tris = [t - np.array([0, 0, z0]) for t in tris]
        stems = [Path(f).stem.split('_PRINT')[0] for f in files]
        for i in range(q):
            nm = stems[0] if q == 1 else f'{stems[0]}_{i+1}'
            items.append((nm, [(st if q == 1 else f'{st}_{i+1}', t) for st, t in zip(stems, tris)]))
    plates = pack(items)
    paths = []
    for k, pl in enumerate(plates, 1):
        p = Path(f'{out}.3mf' if len(plates) == 1 else f'{out}_plate{k}.3mf'); write_3mf(p, pl); paths.append(p)
        print(p, len(pl), 'parts')
    return paths


if __name__ == '__main__':
    make(sys.argv[1], sys.argv[2:])
