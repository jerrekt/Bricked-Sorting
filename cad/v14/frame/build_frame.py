"""V14 module F (interface 5): wood frame, 2 mm red PLA skin on printed clips, roof, studs, corner caps.
CadQuery 2.8. Run: python3 build_frame.py   (writes world/, print/, parts.json, checks.json, cut_list.md,
drilling_map.md/.json/.png and 4 stills).

Machine coordinates (interface.json): origin floor centre, +Y front, +Z up, +X = front viewer's left.

Skin system (all printed, no visible screws except the 8 access-panel screws):
- tile = 2.0 mm face, printed face-down, with 1.6 x 2.8 mm ribs on the back (border ribs follow the outline,
  plus a rib on every wood line it crosses). Face outer at |x| 360 / |y| 180; ribs reach 4.8 in; the wood is 6 in.
- C1 clip: channel block screwed to the wood (#6 x 3/4) that grips one rib (slot = rib + 2 x 0.07, runbook sliding fit).
- C2 clip: same, slot for the two ribs at a tile seam over wood (beam posts).
- H clip: unscrewed channel over the two ribs at a seam with no wood behind it (joins tiles into one wall panel).
- C3 clip: screwed to the inner face of a top rail, upward slot for the rib hanging from a roof tile.
- 116/117 keeper bars: screwed to the deck cleat / top rail, carry M3 inserts for the removable back access panel.
Assembly: screw all C clips and keeper bars to the wood; H-clip each wall's tiles into one panel face-down on a
table; press the panel onto the clips (ribs drop into the channels). Tiles lift off again the same way.
"""
import json, math, sys
from pathlib import Path
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union
from shapely.affinity import scale as sscale
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f_common import (IF, BED, FIT_SLIDE, INSERT_M3_D, INSERT_M3_DEPTH, M3_CLR, M3_CSK_D, WOOD_SCREW_CLR, WOOD_SCREW_CSK,
                      CHAMFER_BED, print_pose, bed_fit, export, bbox, extent, grams, hours, cyl, boxc, box, ov, vol, render)

W = IF['wood']; SK = IF['skin']; ST = IF['studs']
XO, YO = 360.0, 180.0                                            # outer skin faces (interface skin.outer_faces; the 5.1 envelope y +-192 includes the drawer faces)
Z_ROOF = 612.0; T_SKIN = 2.0; GAP = 4.0; D_WOOD = T_SKIN + GAP    # roof skin z 612..614; wood faces 6 in from the skin
RIB_T, RIB_H = 1.6, 2.8                                           # rib thickness / height off the face back
SLOT1 = RIB_T + 2 * FIT_SLIDE; SLOT2 = 2 * RIB_T + 2 * FIT_SLIDE
CLIP_H = 3.4; SLOT_DEPTH = 2.4                                    # clip height off the wood (0.6 under the face), rib engagement
OPEN = SK['drawer_openings']['front_and_back_walls']              # x -300..300, z 12..134
PANEL = SK['back_access_panel']                                   # x -200..200, z 330..560
STUD_C = ST['centers']; STUD_R = ST['od'] / 2; STUD_Z = ST['z']   # (-180,0),(180,0); 108; 614..664
ROOF_HOLE_R = 90.0; STUD_ID_R = 100.0
CAP_LEG = 24.0; CAP_RIB = 346.0; CAP_RIB_Y = 167.0                # corner cap leg width and rib lines (over the posts)
PANEL_SCREW_X = (-150.0, -50.0, 50.0, 150.0)
CROSS_X = (STUD_C[0][0] - 112.0, STUD_C[0][0] + 112.0)          # interface 5.1: 1x2 cross rails under the hopper stud at x -292 / -68
CROSS_W, CROSS_H = 38.0, 19.0                                     # laid FLAT (38 wide, 19 tall, z 593..612) to clear the drum top (589)
PANEL_SCREW_Z = (PANEL['z'][0] + 8.0, PANEL['z'][1] - 8.0)        # 338, 552
BAR_W = 16.0

COL = {'wood': (0.82, 0.68, 0.45), 'ply': (0.88, 0.80, 0.62), 'skin': (0.78, 0.10, 0.10), 'panel': (0.55, 0.08, 0.08),
       'clip': (0.25, 0.25, 0.28), 'stud': (0.80, 0.12, 0.12), 'cap': (0.70, 0.08, 0.08), 'bar': (0.30, 0.30, 0.34)}


# ---------------- small helpers ----------------
def ring_pts(coords):
    pts = [(float(x), float(y)) for x, y in coords]
    if pts[0] == pts[-1]: pts = pts[:-1]
    return pts


def poly_to_cq(poly, h, z0=0.0):
    w = cq.Workplane('XY').workplane(offset=z0).polyline(ring_pts(poly.exterior.coords)).close().extrude(h)
    for hole in poly.interiors:
        w = w.cut(cq.Workplane('XY').workplane(offset=z0 - 1).polyline(ring_pts(hole.coords)).close().extrude(h + 2))
    return w


def multi_to_cq(geom, h, z0=0.0):
    if geom is None or geom.is_empty: return None
    polys = [geom] if geom.geom_type == 'Polygon' else [g for g in geom.geoms if g.geom_type == 'Polygon']
    out = None
    for p in polys:
        if p.is_empty or p.area < 1e-6: continue
        q = poly_to_cq(p, h, z0)
        out = q if out is None else out.union(q)
    return out


def apply_m(w, M):
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(*[float(M[i][j]) for i in range(3) for j in range(4)])
    s = w.val() if isinstance(w, cq.Workplane) else w
    return cq.Workplane().add(s.moved(cq.Location(t)))


def csk_cone(p, d, big):
    """90 deg countersink cone of top diameter big, apex along d"""
    return cq.Workplane(obj=cq.Solid.makeCone(big / 2, 0.0, big / 2, cq.Vector(*p), cq.Vector(*d)))


# wall frames: local (u, v, d) -> world; u along the wall (signed so the frame is right-handed), v = z, d = inward depth
WALLS = {
    'F': dict(sgn=+1, M=[[1, 0, 0, 0], [0, 0, -1, YO], [0, 1, 0, 0]]),      # (u,v,d) -> (u, 180-d, v)         u = x
    'B': dict(sgn=-1, M=[[-1, 0, 0, 0], [0, 0, 1, -YO], [0, 1, 0, 0]]),     # (u,v,d) -> (-u, -180+d, v)       u = -x
    'L': dict(sgn=-1, M=[[0, 0, -1, XO], [-1, 0, 0, 0], [0, 1, 0, 0]]),     # x = +360 face: (u,v,d) -> (360-d, -u, v)   u = -y
    'R': dict(sgn=+1, M=[[0, 0, 1, -XO], [1, 0, 0, 0], [0, 1, 0, 0]]),      # x = -360 face: (u,v,d) -> (-360+d, u, v)   u = y
}


def to_world(w, wall):
    return apply_m(w, WALLS[wall]['M'])


def wall_point(wall, wcoord, z, d):
    s = WALLS[wall]['sgn']
    M = np.array(WALLS[wall]['M'], float)
    p = M[:, :3] @ np.array([s * wcoord, z, d]) + M[:, 3]
    return [round(float(v), 2) for v in p]


def loc2d(wall, geom):
    return sscale(geom, xfact=WALLS[wall]['sgn'], yfact=1, origin=(0, 0))


# ---------------- 2D tile outlines (w, z) ----------------
def tile_poly(w0, w1, z0, z1, cuts=()):
    p = sbox(w0, z0, w1, z1)
    for c in cuts:
        p = p.difference(c)
    return p


def rib_ring(poly):
    return poly.difference(poly.buffer(-RIB_T, join_style='mitre'))


def build_tile(wall, poly, extra_ribs=(), notch_strips=(), face_cuts=()):
    """poly in (w, z). extra_ribs: (w0, w1, z0, z1) rectangles in (w, z) for ribs on wood lines.
    notch_strips: (w0, w1) vertical strips where no rib may be (keeper bars pass behind). face_cuts: (w, z) csk M3 holes."""
    face = multi_to_cq(loc2d(wall, poly), T_SKIN, 0.0)
    ribs2d = rib_ring(poly)
    for (w0, w1, z0, z1) in extra_ribs:
        ribs2d = ribs2d.union(sbox(w0, z0, w1, z1).intersection(poly.buffer(-RIB_T * 0.5, join_style='mitre')))
    for (w0, w1) in notch_strips:
        ribs2d = ribs2d.difference(sbox(w0, -10, w1, 1000))
    ribs = multi_to_cq(loc2d(wall, ribs2d), RIB_H, T_SKIN - 0.01)
    body = face.union(ribs) if ribs is not None else face
    s = WALLS[wall]['sgn']
    for (cw, cz) in face_cuts:
        body = body.cut(cyl((s * cw, cz, -1), (0, 0, 1), M3_CLR / 2, 10)).cut(csk_cone((s * cw, cz, -0.01), (0, 0, 1), M3_CSK_D))
    return to_world(body, wall)


# ---------------- clips ----------------
def clip_C(slot, L=24.0):
    """channel clip, local: base on z 0 (wood), channel block centred on y 0, slot opens to +z (toward the skin).
    One #6 countersunk screw in the -y wing. Returns (solid, screw_offset_y)."""
    bw = slot + 2 * 1.6
    base = box(0, -2.0, 0, L, 9 + bw, 1.8)
    blk = box(0, 0, 0, L, bw, CLIP_H)
    w = base.union(blk).cut(box(0, 0, CLIP_H - SLOT_DEPTH, L + 2, slot, SLOT_DEPTH + 1))
    w = w.cut(cq.Workplane('YZ').polyline([(-slot / 2 - 0.6, CLIP_H + 0.01), (slot / 2 + 0.6, CLIP_H + 0.01), (slot / 2, CLIP_H - 0.6), (-slot / 2, CLIP_H - 0.6)]).close().extrude(L + 2, both=True))
    sy = -(bw / 2 + 4.0)
    w = w.cut(cyl((0, sy, -1), (0, 0, 1), WOOD_SCREW_CLR / 2, 5)).cut(csk_cone((0, sy, 1.8 + 0.01), (0, 0, -1), WOOD_SCREW_CSK))
    return w, sy


def clip_H(slot=SLOT2, L=24.0):
    bw = slot + 2 * 1.6
    w = box(0, 0, 0, L, bw, CLIP_H).cut(box(0, 0, CLIP_H - SLOT_DEPTH, L + 2, slot, SLOT_DEPTH + 1))
    w = w.cut(cq.Workplane('YZ').polyline([(-slot / 2 - 0.6, CLIP_H + 0.01), (slot / 2 + 0.6, CLIP_H + 0.01), (slot / 2, CLIP_H - 0.6), (-slot / 2, CLIP_H - 0.6)]).close().extrude(L + 2, both=True))
    return w


C3_H = 33.8


def clip_C3(L=24.0):
    """roof clip, local: plate y 0..1.6 against the rail inner face (rail at y < 0), z 0..33.8; bridge z 20..22 out to y 4.94;
    jaw y 3.34..4.94, z 22..33.8 -> upward slot 1.74 wide (y 1.6..3.34) for the rib hanging from the roof tile. Screw at z 8."""
    pl = boxc(-L / 2, L / 2, 0, 1.6, 0, C3_H)
    br = boxc(-L / 2, L / 2, 0, 1.6 + SLOT1 + 1.6, 20, 22)
    jaw = boxc(-L / 2, L / 2, 1.6 + SLOT1, 1.6 + SLOT1 + 1.6, 22, C3_H)
    w = pl.union(br).union(jaw)
    w = w.cut(cyl((0, -1, 8), (0, 1, 0), WOOD_SCREW_CLR / 2, 5)).cut(csk_cone((0, 1.6 + 0.01, 8), (0, -1, 0), WOOD_SCREW_CSK))
    return w


def place_clip(kind, wall, wcoord, z, along='h', wing=-1):
    """C1/C2 clip on a wall wood face, slot centred on the rib at (w, z). along 'h' = horizontal rib, 'v' = vertical rib.
    wing: which side (in u for 'v', in z for 'h') the screw wing goes. Returns (world solid, screw world point)."""
    slot = SLOT1 if kind == 'C1' else SLOT2
    w, sy = clip_C(slot)
    if wing > 0:
        w = w.rotate((0, 0, 0), (0, 0, 1), 180); sy = -sy            # wing to +y
    if along == 'v':
        w = w.rotate((0, 0, 0), (0, 0, 1), 90)                        # wing (y = sy) -> x = -sy
    w = w.rotate((0, 0, 0), (0, 1, 0), 180)                           # (x,y,z) -> (-x, y, -z): clip grows toward smaller d
    s = WALLS[wall]['sgn']
    w = w.translate((s * wcoord, z, D_WOOD))
    if along == 'v':
        screw = wall_point(wall, wcoord + sy * s, z, D_WOOD)          # wing at x = -sy before the Y flip -> +sy after
    else:
        screw = wall_point(wall, wcoord, z + sy, D_WOOD)
    return to_world(w, wall), screw


# ---------------- wood ----------------
def wood_parts():
    P = []
    px, py = W['posts_2x2']['x_abs'], W['posts_2x2']['y_abs']; pz = W['posts_2x2']['z']

    def sb(sgn, a, b):
        return (min(sgn * a, sgn * b), max(sgn * a, sgn * b))
    for sx in (-1, 1):
        for sy in (-1, 1):
            X, Y = sb(sx, *px), sb(sy, *py)
            P.append((f'100_post_2x2_{"L" if sx > 0 else "R"}{"F" if sy > 0 else "B"}', boxc(X[0], X[1], Y[0], Y[1], pz[0], pz[1]), 'wood'))
    for nm, spec, pn in (('top_rail', W['top_rails_1x2'], 101), ('deck_cleat', W['deck_cleats_1x2'], 103)):
        lg, sh = spec['long'], spec['short']
        for sy in (-1, 1):
            Y = sb(sy, *lg['y_abs'])
            P.append((f'{pn}_{nm}_long_{"F" if sy > 0 else "B"}', boxc(-px[0], px[0], Y[0], Y[1], lg['z'][0], lg['z'][1]), 'wood'))
        for sx in (-1, 1):
            X = sb(sx, *sh['x_abs'])
            P.append((f'{pn + 1}_{nm}_short_{"L" if sx > 0 else "R"}', boxc(X[0], X[1], -py[0], py[0], sh['z'][0], sh['z'][1]), 'wood'))
    br = W['bottom_rails_1x2_short_walls']
    for sx in (-1, 1):
        X = sb(sx, *br['x_abs'])
        P.append((f'105_bottom_rail_short_{"L" if sx > 0 else "R"}', boxc(X[0], X[1], -py[0], py[0], br['z'][0], br['z'][1]), 'wood'))
    bp = W['beam_posts_1x2']
    for sx in (-1, 1):
        X = sb(sx, *bp['x_abs'])
        P.append((f'106_beam_post_{"L" if sx > 0 else "R"}', boxc(X[0], X[1], bp['y'][0], bp['y'][1], bp['z'][0], bp['z'][1]), 'wood'))
    for k, xc in enumerate(CROSS_X):
        P.append((f'109_roof_cross_rail_{k + 1}', boxc(xc - CROSS_W / 2, xc + CROSS_W / 2, -py[1] + 19, py[1] - 19, pz[1] - CROSS_H, pz[1]), 'wood'))
    fp = W['floor_ply']
    P.append(('107_floor_ply', boxc(fp['x'][0], fp['x'][1], fp['y'][0], fp['y'][1], fp['z'][0], fp['z'][1]), 'ply'))
    dp = W['deck_ply']; hx, hy = dp['size'][0] / 2, dp['size'][1] / 2
    deck = boxc(-hx, hx, -hy, hy, dp['z'][0], dp['z'][1])
    for sx in (-1, 1):
        for sy in (-1, 1):
            X, Y = sb(sx, hx, hx - 38), sb(sy, hy, hy - 38)
            deck = deck.cut(boxc(X[0], X[1], Y[0], Y[1], 290, 320))
    d = IF['drop_point']
    deck = deck.cut(cyl((d[0], d[1], 290), (0, 0, 1), 28, 30))
    P.append(('108_deck_ply', deck, 'ply'))
    return P


# ---------------- skin layout ----------------
ROWS = [(12.0, 212.0), (212.0, 412.0), (412.0, Z_ROOF)]
COLS_F = [(-336.0, -180.0), (-180.0, 0.0), (0.0, 180.0), (180.0, 336.0)]
COLS_B = [(-336.0, -200.0), (-200.0, 0.0), (0.0, 200.0), (200.0, 336.0)]
ROWS_B_MID = [(12.0, 212.0), (212.0, PANEL['z'][0]), (PANEL['z'][1], Z_ROOF)]
COLS_S = [(-156.0, 0.0), (0.0, 156.0)]
CLEAT_Z = sum(W['deck_cleats_1x2']['long']['z']) / 2             # 281
RAIL_Z = sum(W['top_rails_1x2']['long']['z']) / 2                 # 593
BRAIL_Z = sum(W['bottom_rails_1x2_short_walls']['z']) / 2         # 31
POST_X = sum(W['posts_2x2']['x_abs']) / 2                         # 335
POST_Y = sum(W['posts_2x2']['y_abs']) / 2                         # 155
OPEN_CUT = sbox(OPEN['x'][0], 0, OPEN['x'][1], OPEN['z'][1])
PANEL_CUT = sbox(PANEL['x'][0], PANEL['z'][0], PANEL['x'][1], PANEL['z'][1])


def hribs(z0, z1, w0, w1, extra=()):
    out = []
    for zl in list((CLEAT_Z, RAIL_Z)) + list(extra):
        if z0 + 4 < zl < z1 - 4: out.append((w0, w1, zl - RIB_T / 2, zl + RIB_T / 2))
    return out


def skin_parts():
    P, clips = [], []     # clips: dict(kind, wall, w, z, along, wing, what)

    def add_clips_h(wall, w0, w1, z0, z1, extra=()):
        off = 70 if (wall == 'B' and abs(w0) <= 200 and abs(w1) <= 200) else 35     # clear of the keeper bars at x +-50 / +-150
        for zl in list((CLEAT_Z, RAIL_Z)) + list(extra):
            if z0 + 4 < zl < z1 - 4:
                for wc in (w0 + off, w1 - off):
                    nm = 'cleat' if abs(zl - CLEAT_Z) < 1 else ('top rail' if abs(zl - RAIL_Z) < 1 else 'bottom rail')
                    clips.append(dict(kind='C1', wall=wall, w=wc, z=zl, along='h', wing=-1, what=f'{nm}, tile rib'))

    def add_post_clips(wall, wedge, z0, z1):
        wr = wedge + (RIB_T / 2 if wedge < 0 else -RIB_T / 2)          # the edge rib's centre line
        for zc in (z0 + 50, z1 - 50):
            clips.append(dict(kind='C1', wall=wall, w=wr, z=zc, along='v', wing=(1 if (WALLS[wall]['sgn'] * wr) < 0 else -1), what='post, tile edge rib'))

    for wall, cols in (('F', COLS_F), ('B', COLS_B)):
        for ci, (w0, w1) in enumerate(cols):
            outer = ci in (0, 3)
            rows = ROWS if (outer or wall == 'F') else ROWS_B_MID
            for ri, (z0, z1) in enumerate(rows):
                poly = tile_poly(w0, w1, z0, z1, cuts=[OPEN_CUT] + ([PANEL_CUT] if wall == 'B' else []))
                if poly.is_empty or poly.area < 100: continue
                notches = [(x - 9, x + 9) for x in PANEL_SCREW_X if w0 < x < w1] if (wall == 'B' and not outer and ri > 0) else []
                lab = f'{110 if wall == "F" else 111}_tile_{wall}_c{ci + 1}_r{ri + 1}'
                P.append((lab, build_tile(wall, poly, hribs(z0, z1, w0, w1), notches), 'skin'))
                add_clips_h(wall, w0, w1, z0, z1)
                if outer: add_post_clips(wall, w0 if ci == 0 else w1, z0, z1)
            if not outer and wall == 'B':   # access panel halves 115
                z0, z1 = PANEL['z']
                poly = tile_poly(w0, w1, z0, z1)
                cuts = [(x, z) for x in PANEL_SCREW_X if w0 < x < w1 for z in PANEL_SCREW_Z]
                ring = rib_ring(poly)
                for (cw, cz) in cuts:
                    ring = ring.difference(sbox(cw - 9, cz - 12, cw + 9, cz + 12))
                face = multi_to_cq(loc2d(wall, poly), T_SKIN, 0.0)
                body = face.union(multi_to_cq(loc2d(wall, ring), RIB_H, T_SKIN - 0.01))
                s = WALLS[wall]['sgn']
                for (cw, cz) in cuts:
                    body = body.cut(cyl((s * cw, cz, -1), (0, 0, 1), M3_CLR / 2, 10)).cut(csk_cone((s * cw, cz, -0.01), (0, 0, 1), M3_CSK_D))
                P.append((f'115_access_panel_{"x_neg" if ci == 1 else "x_pos"}', to_world(body, wall), 'panel'))
    # side walls (x = +360 is 'L', the front viewer's left)
    for wall in ('L', 'R'):
        for ci, (w0, w1) in enumerate(COLS_S):
            for ri, (z0, z1) in enumerate(ROWS):
                poly = tile_poly(w0, w1, z0, z1)
                lab = f'{112 if wall == "L" else 113}_tile_{wall}_c{ci + 1}_r{ri + 1}'
                P.append((lab, build_tile(wall, poly, hribs(z0, z1, w0, w1, extra=(BRAIL_Z,))), 'skin'))
                add_clips_h(wall, w0, w1, z0, z1, extra=(BRAIL_Z,))
                add_post_clips(wall, w0 if ci == 0 else w1, z0, z1)
                if ci == 0 and ri == 0:
                    for zc in (110.0, 185.0): clips.append(dict(kind='C2', wall=wall, w=0.0, z=zc, along='v', wing=-1, what='beam post, seam ribs'))
                if ci == 0 and ri == 1: clips.append(dict(kind='C2', wall=wall, w=0.0, z=240.0, along='v', wing=-1, what='beam post, seam ribs'))
    return P, clips


def keeper_bars():
    """116 bottom / 117 top keeper bars for the access panel: 16 wide, 3.4 thick (d 2.2..5.6) where they pass behind
    tiles, 5.8 thick (d 2.2..8.0) at the M3 insert behind the panel edge. Screwed to the deck cleat / top rail (#6)."""
    P, screws = [], []
    y_out = -YO + 2.2                      # -177.8 outer face
    for x in PANEL_SCREW_X:
        # bottom bar: cleat (262..300) up to z 346, insert at z 338 (panel screw 8 above the panel's bottom edge 330)
        zb0, zb1 = 268.0, 346.0
        bar = boxc(x - BAR_W / 2, x + BAR_W / 2, y_out, y_out + 3.4, zb0, zb1)
        bar = bar.union(boxc(x - BAR_W / 2, x + BAR_W / 2, y_out, y_out + 5.8, PANEL['z'][0] + 0.5, zb1))
        bar = bar.cut(cyl((x, y_out + 10, PANEL_SCREW_Z[0]), (0, -1, 0), INSERT_M3_D / 2, 12))
        bar = bar.cut(cyl((x, y_out - 1, CLEAT_Z), (0, 1, 0), WOOD_SCREW_CLR / 2, 8)).cut(csk_cone((x, y_out - 0.01, CLEAT_Z), (0, 1, 0), WOOD_SCREW_CSK))
        P.append((f'116_panel_keeper_bottom_x{int(x)}', bar, 'bar'))
        screws.append(dict(part='keeper bar 116', on='y -174 (deck cleat outer face)', what='access panel keeper', xyz=[x, -YO + D_WOOD, CLEAT_Z]))
        zt0, zt1 = 544.0, 600.0
        bar = boxc(x - BAR_W / 2, x + BAR_W / 2, y_out, y_out + 3.4, zt0, zt1)
        bar = bar.union(boxc(x - BAR_W / 2, x + BAR_W / 2, y_out, y_out + 5.8, zt0, PANEL['z'][1] - 0.5))
        bar = bar.cut(cyl((x, y_out + 10, PANEL_SCREW_Z[1]), (0, -1, 0), INSERT_M3_D / 2, 12))
        bar = bar.cut(cyl((x, y_out - 1, RAIL_Z), (0, 1, 0), WOOD_SCREW_CLR / 2, 8)).cut(csk_cone((x, y_out - 0.01, RAIL_Z), (0, 1, 0), WOOD_SCREW_CSK))
        P.append((f'117_panel_keeper_top_x{int(x)}', bar, 'bar'))
        screws.append(dict(part='keeper bar 117', on='y -174 (top rail outer face)', what='access panel keeper', xyz=[x, -YO + D_WOOD, RAIL_Z]))
    return P, screws


# ---------------- roof, studs, corner caps ----------------
def roof_parts():
    P, clips = [], []
    cols = [(-360.0, -180.0), (-180.0, 0.0), (0.0, 180.0), (180.0, 360.0)]
    rows = [(-180.0, 0.0), (0.0, 180.0)]
    hole = Point(STUD_C[0][0], STUD_C[0][1]).buffer(ROOF_HOLE_R, 64)
    inner = sbox(-330.0, -150.0, 330.0, 150.0)       # ribs stay inside the rails
    for ci, (x0, x1) in enumerate(cols):
        for ri, (y0, y1) in enumerate(rows):
            poly = sbox(x0, y0, x1, y1).difference(hole)
            face = poly_to_cq(poly, T_SKIN, Z_ROOF)
            seams = []
            for xs in (x0, x1):
                if abs(xs) < 300:
                    seams.append(sbox(xs - RIB_T, y0, xs, y1) if xs > (x0 + x1) / 2 else sbox(xs, y0, xs + RIB_T, y1))
            for ys in (y0, y1):
                if abs(ys) < 100:
                    seams.append(sbox(x0, ys - RIB_T, x1, ys) if ys > (y0 + y1) / 2 else sbox(x0, ys, x1, ys + RIB_T))
            yr = (POST_Y - 1.6 - RIB_T) if y1 > 0 else -(POST_Y - 1.6)          # hanging ribs: y 151.8..153.4 / -153.4..-151.8
            seams.append(sbox(max(x0, -310), yr, min(x1, 310), yr + RIB_T))                                         # stop before the posts (|x| 316)
            if ci == 0: seams.append(sbox(-(POST_X - 1.6 - RIB_T) - RIB_T, -130, -(POST_X - 1.6 - RIB_T), 130))      # x -333.4..-331.8, |y| < 130 (posts at 136)
            if ci == 3: seams.append(sbox(POST_X - 1.6 - RIB_T, -130, POST_X - 1.6, 130))                             # x 331.8..333.4
            for xc in CROSS_X:        # locator ribs hugging both sides of the flat cross rail (0.2 clearance each side)
                for sx_ in (-1, 1):
                    xr = xc + sx_ * (CROSS_W / 2 + 0.2)
                    seams.append(sbox(min(xr, xr + sx_ * RIB_T), max(y0, -140), max(xr, xr + sx_ * RIB_T), min(y1, 140)))
            rp = unary_union(seams).intersection(poly.buffer(-0.01)).intersection(sbox(-333.5, -153.5, 333.5, 153.5))
            for xc in CROSS_X:        # no ribs over the cross rails themselves
                rp = rp.difference(sbox(xc - CROSS_W / 2 - 0.1, -200, xc + CROSS_W / 2 + 0.1, 200))
            ribs = multi_to_cq(rp, RIB_H, Z_ROOF - RIB_H + 0.01)
            w = face.union(ribs) if ribs is not None else face
            for (sx, sy) in STUD_C:      # csk M3 from below into the stud inserts
                r_hole = 104.0 if sx < 0 else 102.0
                for a in (45, 135, 225, 315):
                    bx, by = sx + r_hole * math.cos(math.radians(a)), sy + r_hole * math.sin(math.radians(a))
                    if x0 < bx < x1 and y0 < by < y1:
                        w = w.cut(cyl((bx, by, Z_ROOF - 1), (0, 0, 1), M3_CLR / 2, 5)).cut(csk_cone((bx, by, Z_ROOF - 0.01), (0, 0, 1), M3_CSK_D))
            P.append((f'114_roof_tile_c{ci + 1}_r{ri + 1}', w, 'skin'))
            for xc in (max(x0, -310) + 30, min(x1, 310) - 30):
                if any(abs(xc - cx_) < CROSS_W / 2 + 14 for cx_ in CROSS_X): xc += 36 if xc < (x0 + x1) / 2 else -36   # clear of the cross rail ends
                clips.append(dict(kind='C3', face='long', x=xc, y=(POST_Y if y1 > 0 else -POST_Y), what='top rail inner face, roof rib'))
            if ci in (0, 3):
                for yc in (y0 + 60, y1 - 60):
                    clips.append(dict(kind='C3', face='short', x=(-POST_X if ci == 0 else POST_X), y=yc, what='short top rail inner face, roof rib'))
    return P, clips


def stud_parts():
    P = []
    z0, z1 = STUD_Z
    # left stud: open ring ID 200 with an internal ledge ID 170 at z 640..646 (45 deg wedge under it) and 4 M3 inserts
    # in the ledge (hopper collar) and 4 M3 inserts up into the foot at r 104 (roof screws from below).
    cx, cy = STUD_C[0]
    ring = cyl((cx, cy, z0), (0, 0, 1), STUD_R, z1 - z0).cut(cyl((cx, cy, z0 - 1), (0, 0, 1), STUD_ID_R, z1 - z0 + 2))
    ledge = cq.Workplane('XZ').polyline([(85, 26), (100.01, 11), (100.01, 32), (85, 32)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, z0))
    ring = ring.union(ledge)
    for a in (45, 135, 225, 315):
        px, py = cx + 92.5 * math.cos(math.radians(a)), cy + 92.5 * math.sin(math.radians(a))
        ring = ring.cut(cyl((px, py, z0 + 32 - INSERT_M3_DEPTH), (0, 0, 1), INSERT_M3_D / 2, INSERT_M3_DEPTH + 1))
        px, py = cx + 104 * math.cos(math.radians(a)), cy + 104 * math.sin(math.radians(a))
        ring = ring.cut(cyl((px, py, z0 - 1), (0, 0, 1), INSERT_M3_D / 2, INSERT_M3_DEPTH + 1))
    ring = ring.cut(cq.Workplane('XZ').polyline([(STUD_R + 0.01, 0), (STUD_R + 0.01, CHAMFER_BED), (STUD_R - CHAMFER_BED, 0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, z0)))
    P.append(('130_stud_ring_left_hopper', ring, 'stud'))
    # right stud: capped, 2.4 wall, 2 mm top, 8 mm foot ring r 96..108 with 4 M3 inserts at r 102 (roof screws from below)
    cx, cy = STUD_C[1]
    cap = cyl((cx, cy, z0), (0, 0, 1), STUD_R, z1 - z0).cut(cyl((cx, cy, z0 - 1), (0, 0, 1), STUD_R - 2.4, z1 - z0 - 2.0 + 1))
    cap = cap.union(cyl((cx, cy, z0), (0, 0, 1), STUD_R, 8.0).cut(cyl((cx, cy, z0 - 1), (0, 0, 1), 96, 10)))
    for a in (45, 135, 225, 315):
        px, py = cx + 102 * math.cos(math.radians(a)), cy + 102 * math.sin(math.radians(a))
        cap = cap.cut(cyl((px, py, z0 - 1), (0, 0, 1), INSERT_M3_D / 2, INSERT_M3_DEPTH + 1))
    cap = cap.cut(cq.Workplane('XZ').polyline([(STUD_R + 0.01, z1 - z0), (STUD_R + 0.01, z1 - z0 - CHAMFER_BED), (STUD_R - CHAMFER_BED, z1 - z0)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, z0)))
    P.append(('131_stud_cap_right', cap, 'stud'))
    return P


def corner_caps():
    """L caps at the 4 vertical corners, 3 segments each (rows). Legs 24 wide, 2 thick, outer faces at |x| 360 / |y| 180.
    One rib per leg over the post (front/back leg rib at |x| 346, side leg rib at |y| 167). Printed standing on its
    end (200 tall L section), so both ribs are vertical walls and nothing overhangs; use a brim."""
    P, clips = [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for ri, (z0, z1) in enumerate(ROWS):
                xo, yo = sx * XO, sy * YO

                def sb(a, b): return (min(a, b), max(a, b))
                X1, Y1 = sb(xo, xo - sx * CAP_LEG), sb(yo, yo - sy * T_SKIN)
                legA = boxc(X1[0], X1[1], Y1[0], Y1[1], z0, z1)                                   # along x on the y face
                X2, Y2 = sb(xo, xo - sx * T_SKIN), sb(yo, yo - sy * CAP_LEG)
                legB = boxc(X2[0], X2[1], Y2[0], Y2[1], z0, z1)                                   # along y on the x face
                XA, YA = sb(sx * CAP_RIB - RIB_T / 2, sx * CAP_RIB + RIB_T / 2), sb(yo - sy * T_SKIN, yo - sy * (T_SKIN + RIB_H))
                ribA = boxc(XA[0], XA[1], YA[0], YA[1], z0 + 2, z1 - 2)
                ya = sy * CAP_RIB_Y
                XB, YB = sb(xo - sx * T_SKIN, xo - sx * (T_SKIN + RIB_H)), sb(ya - RIB_T / 2, ya + RIB_T / 2)
                ribB = boxc(XB[0], XB[1], YB[0], YB[1], z0 + 2, z1 - 2)
                w = legA.union(legB).union(ribA).union(ribB)
                lab = f'135_corner_cap_{"L" if sx > 0 else "R"}{"F" if sy > 0 else "B"}_r{ri + 1}'
                P.append((lab, w, 'cap'))
                wallA, wallB = ('F' if sy > 0 else 'B'), ('L' if sx > 0 else 'R')
                for zc in (z0 + 100,):
                    clips.append(dict(kind='C1', wall=wallA, w=sx * CAP_RIB, z=zc, along='v', wing=(1 if WALLS[wallA]['sgn'] * sx * CAP_RIB < 0 else -1), what='post, corner cap rib'))
                    clips.append(dict(kind='C1', wall=wallB, w=sy * CAP_RIB_Y, z=zc, along='v', wing=(1 if WALLS[wallB]['sgn'] * sy * CAP_RIB_Y < 0 else -1), what='post, corner cap rib'))
    return P, clips


# ---------------- clip instances ----------------
def clip_instances(wall_clips, roof_clips):
    P, screws = [], []
    n = {'C1': 0, 'C2': 0, 'C3': 0}
    face_name = {'F': 'y +174 (post / cleat / rail outer face)', 'B': 'y -174 (post / cleat / rail outer face)', 'L': 'x +354 (post / rail outer face)', 'R': 'x -354 (post / rail outer face)'}
    for c in wall_clips:
        w, sc = place_clip(c['kind'], c['wall'], c['w'], c['z'], c['along'], c.get('wing', -1))
        n[c['kind']] += 1
        P.append((f'{120 if c["kind"] == "C1" else 121}_clip_{c["kind"]}_{c["wall"]}_{n[c["kind"]]}', w, 'clip'))
        screws.append(dict(part='clip ' + c['kind'], on=face_name[c['wall']], what=c['what'], xyz=sc))
    for c in roof_clips:
        w = clip_C3()
        if c['face'] == 'long':
            if c['y'] > 0: w = w.rotate((0, 0, 0), (0, 0, 1), 180)
            w = w.translate((c['x'], c['y'], Z_ROOF - C3_H))
            on = 'long top rail inner face y ' + ('+155' if c['y'] > 0 else '-155')
        else:
            w = w.rotate((0, 0, 0), (0, 0, 1), 90 if c['x'] > 0 else -90).translate((c['x'], c['y'], Z_ROOF - C3_H))
            on = 'short top rail inner face x ' + ('+335' if c['x'] > 0 else '-335')
        n['C3'] += 1
        P.append((f'123_clip_C3_roof_{n["C3"]}', w, 'clip'))
        screws.append(dict(part='clip C3', on=on, what=c['what'], xyz=[round(c['x'], 1), round(c['y'], 1), round(Z_ROOF - C3_H + 8, 1)]))
    return P, screws, n


def h_clip_plan():
    """H bridge clips at seams with no wood behind them (loose parts): positions for assembly."""
    pos = []
    for wall, cols in (('F', COLS_F), ('B', COLS_B), ('L', COLS_S), ('R', COLS_S)):
        rows = ROWS
        for ci in range(len(cols) - 1):          # vertical seams
            xs = cols[ci][1]
            for (z0, z1) in rows:
                if wall in ('L', 'R') and z1 <= 412 and z0 < 262: continue       # beam post seam: C2 clips (rows 1-2 lower part)
                zz0 = max(z0, OPEN['z'][1]) if wall in ('F', 'B') else z0
                for zc in (zz0 + 25, z1 - 25):
                    if wall == 'B' and PANEL['z'][0] - 5 < zc < PANEL['z'][1] + 5 and abs(xs) <= 200: continue
                    pos.append(dict(wall=wall, w=xs, z=zc))
        for ci, (w0, w1) in enumerate(cols):     # horizontal seams
            seam_z = [212.0, 412.0]
            if wall == 'B' and ci in (1, 2): seam_z = [212.0]
            for zs in seam_z:
                for wc in (w0 + 25, w1 - 25):
                    pos.append(dict(wall=wall, w=wc, z=zs))
    for xs in (-180.0, 0.0, 180.0):          # roof seams
        for yc in (-120.0, 120.0):
            pos.append(dict(wall='roof', w=xs, z=yc))
    for (x0, x1) in ((-360.0, -180.0), (-180.0, 0.0), (0.0, 180.0), (180.0, 360.0)):
        for xc in (x0 + 35, x1 - 35):
            if abs(xc + 180) < 95: continue
            pos.append(dict(wall='roof', w=xc, z=0.0))
    return pos


# ---------------- cut list and drilling map ----------------
def cut_list(screws):
    L = ['# V14 frame: wood cut list (interface 5)', '',
         'All straight crosscuts. Nominal 2x2 = 38 x 38 actual, 1x2 = 19 x 38 actual (check the actual lumber; the skin clips assume 6 mm from wood face to skin). The store cuts the plywood.', '',
         '| # | Piece | Stock | Cut (mm) | Cut (in) | Qty | Position |', '|---|---|---|---|---|---|---|']
    rows = [
        ('100', 'corner post', '2x2', 600, 4, '|x| 316..354, |y| 136..174, z 12..612'),
        ('101', 'top rail, long', '1x2 (38 tall)', 632, 2, 'y +-155..174, z 574..612, between the posts'),
        ('102', 'top rail, short', '1x2 (38 tall)', 272, 2, 'x +-335..354, z 574..612, between the posts'),
        ('103', 'deck cleat, long', '1x2 (38 tall)', 632, 2, 'y +-155..174, z 262..300'),
        ('104', 'deck cleat, short', '1x2 (38 tall)', 272, 2, 'x +-335..354, z 262..300'),
        ('105', 'bottom rail, short walls', '1x2 (38 tall)', 272, 2, 'x +-335..354, z 12..50'),
        ('106', 'beam post', '1x2', 212, 2, 'x +-335..354, y -19..19, z 50..262 (vertical, 19 face toward the wall)'),
        ('109', 'roof cross rail (under the hopper stud)', '1x2 laid FLAT', 310, 2, 'x -292 and -68 (centres), y -155..155 between the long top rails, z 593..612; 38 face up'),
    ]
    for pn, nm, st, cut, q, pos in rows:
        L.append(f'| {pn} | {nm} | {st} | {cut} | {cut / 25.4:.2f} | {q} | {pos} |')
    L.append('| 107 | floor plywood | 1/2 in ply | 720 x 360 | 28.35 x 14.17 | 1 | z 0..12 |')
    L.append('| 108 | deck plywood | 1/2 in ply | 708 x 348 | 27.87 x 13.70 | 1 | z 300..312; 38 x 38 notch at each corner; 56 mm (2 3/16 in) hole at (240, 0) for the drop funnel |')
    L += ['', 'Stock: 2x2 x 8 ft x 1 (4 x 600 = 2400 of 2438, cut carefully), 1x2 x 8 ft x 3 (632 + 632 + 272 + 272 + 272 = 2080; 632 + 632 + 272 + 272 + 212 + 212 = 2232; 310 + 310 = 620), 1/2 in plywood 2 x 4 ft handy panel x 1.',
          '', '## Wood-to-wood screws (pilot 2.5 mm for #6, 3 mm for #8)', '',
          '| Joint | Screw | Qty | Where |', '|---|---|---|---|',
          '| posts to floor ply | #8 x 2 in, up from below the ply | 8 | 2 per post, at the post centre (x +-335, y +-155) +-10 along y |',
          '| long rails 101 / cleats 103 to posts | #8 x 2.5 in, through the post outer x face (+-354) into the rail end grain | 8 | 2 per rail end: y +-164.5, z 584 and 602 (rail) / 272 and 290 (cleat) |',
          '| short rails 102 / cleats 104 / bottom rails 105 to posts | #8 x 2.5 in, through the post outer y face (+-174) into the end grain | 24 | 2 per end: x +-344.5, z 584/602, 272/290, 22/40 |',
          '| beam post 106 to bottom rail 105 | #8 x 2.5 in, up from below the floor ply through rail 105 | 2 | at (+-344.5, 0) |',
          '| beam post 106 to deck cleat 104 | #8 x 2.5 in, down through the cleat top | 2 | at (+-344.5, 0), before the deck ply goes on |',
          '| deck ply 108 to cleats | #6 x 1.25 in, from above | 12 | 3 per cleat, on the cleat centreline (y +-164.5 / x +-344.5) |',
          '| cross rails 109 to long top rails | #8 x 2.5 in toe-screwed (pocket style) down from the cross rail top face into the long rail, 2 per end, before the roof goes on | 8 | at x -292 / -68, y +-140, ~15 deg off vertical toward the long rail |',
          '', 'Order: posts onto the floor ply; bottom rails 105; beam posts 106; cleats 103/104; top rails 101/102; drill the clip pilots (drilling_map.md); clips; deck ply last (after the drawer rails, which screw into the floor).']
    (HERE / 'cut_list.md').write_text('\n'.join(L) + '\n')


def drilling_map(screws, wood):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    L = ['# V14 frame: drilling map for the printed clips and keeper bars (interface 5)', '',
         'Every hole: 2.5 mm pilot for a #6 x 3/4 in wood screw, drilled perpendicular to the face named, at the machine coordinates given (mm; origin floor centre, +Y front, +X the front viewer\'s left). Post outer faces are at y = +-174 (front/back) and x = +-354 (sides); the rail and cleat outer faces share those planes. The C3 roof clips go on the INNER faces of the top rails (y = +-155, x = +-335) at z 586: drill and fit them before the roof goes on.',
         '', '| # | Part | Face | x | y | z | Holds |', '|---|---|---|---|---|---|---|']
    for i, s in enumerate(screws):
        x, y, z = s['xyz']
        L.append(f'| {i + 1} | {s["part"]} | {s["on"]} | {x:.1f} | {y:.1f} | {z:.1f} | {s["what"]} |')
    L += ['', f'Total: {len(screws)} #6 screws. Wood-to-wood screws are in cut_list.md; deck-module screws into the deck ply are in the deck README.']
    (HERE / 'drilling_map.md').write_text('\n'.join(L) + '\n')
    (HERE / 'drilling_map.json').write_text(json.dumps(screws, indent=1))
    fig, axs = plt.subplots(2, 2, figsize=(16, 11))
    views = [('F', 'front face (y = +174): x, z', lambda s: 'y +1' in s['on'], 0),
             ('B', 'back face (y = -174): x, z', lambda s: 'y -1' in s['on'], 0),
             ('L', 'left face (x = +354, the front viewer\'s left): y, z', lambda s: 'x +3' in s['on'], 1),
             ('R', 'right face (x = -354): y, z', lambda s: 'x -3' in s['on'], 1)]
    for ax, (wall, title, sel, i0) in zip(axs.flat, views):
        for lab, w, kind in wood:
            b = bbox(w)
            if wall in ('F', 'B'):
                if not ((b[4] > 100) if wall == 'F' else (b[1] < -100)): continue
                ax.add_patch(plt.Rectangle((b[0], b[2]), b[3] - b[0], b[5] - b[2], fc='#e8d7b0', ec='#8a6d3b', lw=0.8))
            else:
                if not ((b[3] > 300) if wall == 'L' else (b[0] < -300)): continue
                ax.add_patch(plt.Rectangle((b[1], b[2]), b[4] - b[1], b[5] - b[2], fc='#e8d7b0', ec='#8a6d3b', lw=0.8))
        for s in screws:
            if not sel(s): continue
            x, z = s['xyz'][i0], s['xyz'][2]
            mk, c = ('s', '#2980b9') if 'C3' in s['part'] else (('D', '#27ae60') if 'keeper' in s['part'] else (('o', '#c0392b') if 'C1' in s['part'] else ('o', '#2c3e50')))
            ax.plot(x, z, mk, ms=5, color=c)
            ax.annotate(f'{x:.0f},{z:.0f}', (x, z), fontsize=5, xytext=(2, 2), textcoords='offset points')
        ax.set_aspect('equal'); ax.set_title(title + '   (red C1, black C2, green keeper bar, blue C3 on the inner face)', fontsize=9)
        ax.set_xlim(-380, 380); ax.set_ylim(-10, 680); ax.grid(True, lw=0.3)
    fig.suptitle('V14 frame drilling map: 2.5 mm pilots for #6 clip screws (machine coordinates, mm). Wood: posts, rails, cleats, beam posts.')
    fig.tight_layout(); fig.savefig(HERE / 'drilling_map.png', dpi=130)


# ---------------- build + checks ----------------
def main():
    world = HERE / 'world'; prn = HERE / 'print'
    wood = wood_parts()
    skin, wall_clips = skin_parts()
    bars, bar_screws = keeper_bars()
    roof, roof_clips = roof_parts()
    studs = stud_parts()
    caps, cap_clips = corner_caps()
    clipsP, screws, ncl = clip_instances(wall_clips + cap_clips, roof_clips)
    screws += bar_screws
    hpos = h_clip_plan()
    parts = wood + skin + bars + roof + studs + caps + clipsP
    masters = [('120_clip_C1_single', clip_C(SLOT1)[0], 'clip'), ('121_clip_C2_seam', clip_C(SLOT2)[0], 'clip'),
               ('122_clip_H_bridge', clip_H(), 'clip'), ('123_clip_C3_roof', clip_C3(), 'clip')]

    asm = cq.Assembly(name='frame_module')
    for lab, w, kind in parts:
        export(w, world / f'{lab}.step')
        asm.add(w, name=lab, color=cq.Color(*COL[kind]))
    asm.save(str(world / 'frame_assembly.step'))

    plist = []

    def add_print(lab, w, qty, pose_fn, note, material='PLA'):
        bedp, diag = pose_fn(w)
        g = grams(w, material); h = hours(g, w)
        export(bedp, prn / f'{lab}_PRINT_{qty}.stl')
        f = bed_fit(bedp)
        plist.append({'label': lab, 'part_no': lab[:3], 'qty': qty, 'material': material, **f, 'diagonal_on_bed': diag,
                      'est_grams_each': g, 'est_hours_each': h, 'orientation': note})

    def face_down(wall):
        rot = {'F': ((1, 0, 0), -90), 'B': ((1, 0, 0), 90), 'L': ((0, 1, 0), 90), 'R': ((0, 1, 0), -90), 'roof': ((1, 0, 0), 180)}[wall]
        return lambda w: print_pose(w, rot=rot)

    for lab, w, kind in skin:
        wall = 'B' if lab.startswith('115') else lab.split('_')[2]
        add_print(lab, w, 1, face_down(wall), 'outer face on the bed, ribs up')
    for lab, w, kind in roof:
        add_print(lab, w, 1, face_down('roof'), 'top face on the bed, ribs up')
    for lab, w, kind in bars:
        add_print(lab, w, 1, lambda w: print_pose(w, rot=((1, 0, 0), 90)), 'outer (countersunk) face on the bed')
    for lab, w, kind in studs:
        if lab.startswith('130'): add_print(lab, w, 1, lambda w: print_pose(w), 'foot on the bed; the ledge has a 45 deg underside')
        else: add_print(lab, w, 1, lambda w: print_pose(w, flip=True), 'top face on the bed, open end up')
    for lab, w, kind in caps:
        add_print(lab, w, 1, lambda w: print_pose(w), 'standing on its end (200 tall L), ribs vertical; brim')
    qty = {'120': ncl['C1'], '121': ncl['C2'], '122': len(hpos), '123': ncl['C3']}
    for lab, w, kind in masters:
        add_print(lab, w, qty[lab[:3]], lambda w: print_pose(w), 'base on the bed, slot up (print 20-30 per plate)')

    # ---- checks ----
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    env = IF['envelope']; zz = {}
    for lab, w, kind in parts:
        b = bbox(w)
        ok = env['x'][0] - .01 <= b[0] and b[3] <= env['x'][1] + .01 and env['y'][0] - .01 <= b[1] and b[4] <= env['y'][1] + .01 and -.01 <= b[2] and b[5] <= env['z'][1] + .01
        zz[lab] = 'in envelope' if ok else f'OUTSIDE {b}'
    res['envelope'] = zz
    KZ = IF['zones']['K_deck']; SZ = IF['zones']['S_scoop']; DZ = IF['zones']['D_drawers']
    zones = {'K': boxc(KZ['x'][0], KZ['x'][1], KZ['y'][0], KZ['y'][1], KZ['z'][0], KZ['z'][1]),
             'S': boxc(SZ['x'][0], SZ['x'][1], SZ['y'][0], SZ['y'][1], SZ['z'][0], SZ['z'][1]),
             'Dfront': boxc(*[DZ['front'][k][i] for k in ('x', 'y', 'z') for i in (0, 1)][::1][::1]) if False else boxc(DZ['front']['x'][0], DZ['front']['x'][1], DZ['front']['y'][0], DZ['front']['y'][1], DZ['front']['z'][0], DZ['front']['z'][1]),
             'Dback': boxc(DZ['back']['x'][0], DZ['back']['x'][1], DZ['back']['y'][0], DZ['back']['y'][1], DZ['back']['z'][0], DZ['back']['z'][1])}
    intr = []
    for lab, w, kind in parts:
        if kind in ('wood', 'ply'): continue
        b = bbox(w)
        for zn, zb in zones.items():
            if ov(b, bbox(zb)):
                v = vol(w, zb)
                if v > 0.5: intr.append([lab, zn, round(v, 1)])
    res['zone_intrusions'] = intr
    items = [(lab, w, bbox(w), kind) for lab, w, kind in parts]
    hits, touches = [], []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if not ov(items[i][2], items[j][2]): continue
            v = vol(items[i][1], items[j][1])
            if v > 0.5:
                a, b_ = items[i], items[j]
                hits.append([a[0], b_[0], round(v, 1)])
    res['clashes'] = hits
    front_open = boxc(OPEN['x'][0] + 1, OPEN['x'][1] - 1, YO - 3, YO + 1, OPEN['z'][0] + 1, OPEN['z'][1] - 1)
    back_open = boxc(OPEN['x'][0] + 1, OPEN['x'][1] - 1, -YO - 1, -YO + 3, OPEN['z'][0] + 1, OPEN['z'][1] - 1)
    panel_vol = boxc(PANEL['x'][0] + 1, PANEL['x'][1] - 1, -YO - 1, -YO + 1.9, PANEL['z'][0] + 1, PANEL['z'][1] - 1)
    skinw = [(lab, w) for lab, w, kind in parts if kind in ('skin', 'cap')]
    res['openings'] = {'front_drawer_opening_clear': all(vol(w, front_open) < 0.5 for _, w in skinw),
                       'back_drawer_opening_clear': all(vol(w, back_open) < 0.5 for _, w in skinw),
                       'back_panel_region_free_of_fixed_tiles': all(vol(w, panel_vol) < 0.5 for _, w in skinw),
                       'roof_hole_r90_clear': all(vol(w, cyl((STUD_C[0][0], STUD_C[0][1], 600), (0, 0, 1), ROOF_HOLE_R - 0.5, 30)) < 0.5 for _, w in skinw)}
    inner = boxc(-355.0, 355.0, -175.0, 175.0, 13, Z_ROOF - 0.5)
    res['skin_inside_wood_faces'] = [[lab, round(vol(w, inner), 1)] for lab, w, kind in parts if kind in ('skin', 'panel', 'cap') and not lab.startswith('114') and vol(w, inner) > 0.5]
    tot_g = sum(p['est_grams_each'] * p['qty'] for p in plist); tot_h = sum(p['est_hours_each'] * p['qty'] for p in plist)
    byg = {}
    for p in plist:
        k = {'110': 'skin walls', '111': 'skin walls', '112': 'skin walls', '113': 'skin walls', '114': 'roof', '115': 'access panel', '116': 'keeper bars', '117': 'keeper bars',
             '120': 'clips', '121': 'clips', '122': 'clips', '123': 'clips', '130': 'studs', '131': 'studs', '135': 'corner caps'}[p['part_no']]
        byg[k] = round(byg.get(k, 0) + p['est_grams_each'] * p['qty'])
    res['totals'] = {'printed_grams': round(tot_g), 'printed_hours': round(tot_h, 1), 'grams_by_group': byg, 'clips_screwed': ncl, 'H_bridge_clips': len(hpos),
                     'tiles': len([p for p in plist if p['part_no'] in ('110', '111', '112', '113', '114', '115')]), 'wood_screws_for_clips': len(screws)}
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    (HERE / 'parts.json').write_text(json.dumps({'module': 'F', 'interface': IF['version'], 'printed': plist,
        'wood': [{'label': lab, 'bbox': bbox(w)} for lab, w, kind in wood],
        'bought': [{'item': '2x2 x 8 ft', 'qty': 1}, {'item': '1x2 x 8 ft', 'qty': 3}, {'item': '1/2 in plywood 2 x 4 ft', 'qty': 1},
                   {'item': '#6 x 3/4 in wood screws (clips, keeper bars)', 'qty': len(screws) + 10}, {'item': '#8 x 2.5 in wood screws', 'qty': 44}, {'item': '#8 x 2 in', 'qty': 8}, {'item': '#6 x 1.25 in', 'qty': 12},
                   {'item': 'M3 heat-set inserts', 'qty': 16, 'use': 'stud feet (8), stud ledge (4) [+8 in keeper bars]'}, {'item': 'M3 heat-set inserts', 'qty': 8, 'use': 'keeper bars'},
                   {'item': 'M3 x 8 countersunk', 'qty': 16, 'use': 'stud feet through the roof (8), access panel (8)'}, {'item': 'red PLA', 'qty': f'~{tot_g / 1000:.1f} kg'}],
        'h_clip_positions': hpos, 'totals': res['totals']}, indent=1))
    cut_list(screws); drilling_map(screws, wood)
    stills(parts)
    return res


def stills(parts):
    items = [(w, COL[kind], 1.0) for lab, w, kind in parts]
    render(items, HERE / 'still_1_front_left.png', cam=(1500, 1500, 1200), focal=(0, 0, 330), title='V14 frame + skin (F, interface 5.1): 720 x 360 x 664, 2 mm red PLA tiles on a wood frame; drawer openings x +-310; studs')
    render(items, HERE / 'still_2_back_right.png', cam=(-1500, -1500, 1100), focal=(0, 0, 330), title='Back: removable access panel (2 halves, 8 screws), drawer opening, corner caps')
    inner = [(w, COL[kind], 1.0) for lab, w, kind in parts if kind in ('wood', 'ply', 'clip', 'bar')] + [(w, COL[kind], 0.15) for lab, w, kind in parts if kind in ('skin', 'panel', 'cap', 'stud')]
    render(inner, HERE / 'still_3_wood_and_clips.png', cam=(1400, 1300, 1000), focal=(0, 0, 320), title='Wood (2x2 posts, 1x2 rails, cleats, beam posts, 1/2 in ply) with the clips and keeper bars; skin ghosted')
    det = [(w, COL[kind], 1.0) for lab, w, kind in parts if kind in ('wood', 'clip') and bbox(w)[3] > 250 and bbox(w)[4] > 100]
    det += [(w, COL[kind], 0.55) for lab, w, kind in parts if lab.startswith(('110_tile_F_c4_r2', '112_tile_L_c2_r2', '135_corner_cap_LF_r2'))]
    render(det, HERE / 'still_4_clip_detail.png', cam=(700, 560, 520), focal=(345, 165, 330), title='Corner detail, row 2: tile ribs in C1 channel clips on the post and cleat; corner cap (tiles ghosted)')


if __name__ == '__main__':
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ('envelope', 'bed_fit')}, indent=1)[:6000])
    print('env:', sorted(set(r['envelope'].values())))
    print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
