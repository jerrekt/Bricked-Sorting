"""Team logo (web/assets/logo-720.png, BJ 2026-11-26) as 0.6 mm colour inlays in the front wall's top row.
The logo sits on a white card 587 x 185 mm (viewer X -293.5..293.5, z 395..580). build_frame.py cuts the card pocket out of
tiles 110_tile_F_c1..c4_r3; this script fills it: white (card), red, blue, black, green, one STL per colour per tile, in the
tile's print frame (outer face on the bed), so make_plate.py can group them ("tile.stl+ink.stl+...").
Run after build_frame.py:  python3 make_logo_inks.py [logo.png]   -> print/110_tile_F_c*_r3_ink{w,r,b,k,g}_PRINT_1.stl, logo_preview.png
"""
import sys, json
from pathlib import Path
import numpy as np, cv2, trimesh
from PIL import Image, ImageFilter
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'logo-720.png'
CARD_X, CARD_Z, INK_T = (-293.5, 293.5), (395.0, 580.0), 0.6
ROW_Z = (373.0, 612.0); COLS_F = [(-336.0, -180.0), (-180.0, 0.0), (0.0, 180.0), (180.0, 336.0)]     # world x
PAL = {'r': [(228, 35, 28), (150, 40, 40), (225, 110, 40)], 'b': [(25, 120, 235), (30, 60, 150)], 'k': [(35, 35, 38), (90, 90, 95)],
       'g': [(165, 200, 70), (120, 150, 50)], 'w': [(255, 255, 255), (225, 225, 230)]}
RGB = {'w': (245, 245, 245), 'r': (201, 26, 9), 'b': (30, 95, 201), 'k': (27, 27, 27), 'g': (120, 170, 50)}
UP = 4


def labels():
    im = Image.open(SRC).convert('RGBA')
    im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    keys = [k for k, v in PAL.items() for _ in v]; cols = np.array([c for v in PAL.values() for c in v], float)
    d = ((a[:, :, None, :3] - cols[None, None]) ** 2).sum(-1)
    lab = np.array([list(PAL).index(k) for k in keys])[d.argmin(-1)]
    lab[a[:, :, 3] < 128] = list(PAL).index('w')
    lab = np.asarray(Image.fromarray(lab.astype(np.uint8)).filter(ImageFilter.ModeFilter(9)))
    return lab


def polys(mask, sx, sz):
    cs, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    if hier is None: return out
    for i, c in enumerate(cs):
        if hier[0][i][3] != -1 or len(c) < 4: continue
        holes = []; j = hier[0][i][2]
        while j != -1:
            if len(cs[j]) >= 4: holes.append(cs[j][:, 0, :])
            j = hier[0][j][0]
        p = Polygon(c[:, 0, :], holes).buffer(0)
        if p.area > 4: out.append(p)
    g = unary_union(out) if out else None
    if g is None: return None
    from shapely.affinity import affine_transform
    return affine_transform(g, [sx, 0, 0, -sz, CARD_X[0], CARD_Z[1]])     # pixel (col, row) -> viewer (X, z)


def main():
    lab = labels(); H, Wd = lab.shape
    sx = (CARD_X[1] - CARD_X[0]) / Wd; sz = (CARD_Z[1] - CARD_Z[0]) / H
    card = sbox(CARD_X[0], CARD_Z[0], CARD_X[1], CARD_Z[1])
    geo, used = {}, None
    for k in ('k', 'b', 'r', 'g'):                      # priority order; each grows 0.15 mm so no gap is left between colours
        g = polys(lab == list(PAL).index(k), sx, sz)
        if g is None: continue
        g = g.buffer(0.15).simplify(0.05).intersection(card)
        if used is not None: g = g.difference(used)
        g = g.buffer(-0.2).buffer(0.2)                  # drop slivers thinner than a nozzle line
        geo[k] = g; used = g if used is None else unary_union([used, g])
    geo['w'] = card.difference(used)
    prn = HERE / 'print'; info = {}
    for f in prn.glob('110_tile_F_c*_r3_ink*_PRINT_1.stl'): f.unlink()
    meshes_prev = []
    for ci, (x0, x1) in enumerate(COLS_F):
        xc = (x0 + x1) / 2; zc = (ROW_Z[0] + ROW_Z[1]) / 2
        col = sbox(-x1, 0, -x0, 1000)                    # viewer X = -x
        kept = {}
        for k, g in geo.items():
            if k == 'w': continue
            part = g.intersection(col)
            ps = [p for p in (part.geoms if hasattr(part, 'geoms') else [part]) if p.geom_type == 'Polygon' and p.area > 0.3]
            if ps and sum(p.area for p in ps) >= 20: kept[k] = unary_union(ps)       # crumbs stay the card colour
        kept['w'] = card.intersection(col).difference(unary_union(list(kept.values())).buffer(0)) if kept else card.intersection(col)
        for k, part in kept.items():
            ps = [p for p in (part.geoms if hasattr(part, 'geoms') else [part]) if p.geom_type == 'Polygon' and p.area > 0.3]
            if not ps: continue
            ms = []
            for p in ps:
                m = trimesh.creation.extrude_polygon(p, INK_T)
                v = m.vertices.copy(); v[:, 0] = -v[:, 0] - xc; v[:, 1] = v[:, 1] - zc     # viewer (X, z) -> the tile's bed frame (x - xc, z - zc)
                m.vertices = v; m.invert(); ms.append(m)                                    # mirrored in x: flip the winding back
            m = trimesh.util.concatenate(ms)
            m.export(prn / f'110_tile_F_c{ci + 1}_r3_ink{k}_PRINT_1.stl')
            info[f'c{ci + 1}_{k}'] = dict(bodies=len(ps), area_mm2=round(sum(p.area for p in ps)))
            meshes_prev.append((k, part))
    (HERE / 'logo_inks.json').write_text(json.dumps(dict(card_X=CARD_X, card_z=CARD_Z, ink_t=INK_T, source=SRC.name, parts=info), indent=1))
    # flat preview of what prints (viewer's view), tile seams as thin lines
    S = 3.0; W_, H_ = int(672 * S), int((ROW_Z[1] - ROW_Z[0]) * S)
    img = np.full((H_, W_, 3), (201, 26, 9), np.uint8)
    for k, part in meshes_prev:
        for p in (part.geoms if hasattr(part, 'geoms') else [part]):
            if p.geom_type != 'Polygon': continue
            ext = np.array([[(x + 336) * S, (ROW_Z[1] - z) * S] for x, z in p.exterior.coords], np.int32)
            cv2.fillPoly(img, [ext], RGB[k])
            for h in p.interiors:
                pass
    # holes: repaint in priority order instead (white first, then colours)
    img[:] = (201, 26, 9)
    for k in ('w', 'r', 'g', 'b', 'k'):
        for kk, part in meshes_prev:
            if kk != k: continue
            for p in (part.geoms if hasattr(part, 'geoms') else [part]):
                if p.geom_type != 'Polygon': continue
                rings = [p.exterior] + list(p.interiors)
                cv2.fillPoly(img, [np.array([[(x + 336) * S, (ROW_Z[1] - z) * S] for x, z in r.coords], np.int32) for r in rings], RGB[k])
    for xs in (-180, 0, 180):
        cv2.line(img, (int((xs + 336) * S), 0), (int((xs + 336) * S), H_), (120, 12, 5), 2)
    Image.fromarray(img).save(HERE / 'logo_preview.png')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
