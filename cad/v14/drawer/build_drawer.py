"""V14 module D, interface 4.1: two 8-bin drawers on under-drawer roller rails (CadQuery 2.8).

Each drawer: 2 PETG rails (runner.py) on its underside that run back through
the spine tunnels, 4 floor roller stations + 1 lateral guide, a 4-tile tray
with ribs below and bin locators on top, 4 face pieces with an F/B inlay,
8 bins, a retaining bar over the bins' inner rims, and one drawer-closed
KW11-3Z on the floor. The back drawer is the same design with its rails at
+-200 (front at +-300), turned 180 deg about Z, so the drawers are keyed.
Run: python3 build_drawer.py
"""
import json, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, print_pose, bed_fit, export, bbox, grams, render
import runner as R

D = IF['drawer']; B = IF['bins']; Z = IF['zones']['D_drawer']; RX = D['rails_xy']
FLOOR_TOP = IF['floor']['z'][1]
TRAVEL = D['travel_y']                           # 205
XC = B['x_centers']; ROW_Y = B['row_y_centers'][1]
CELL_X, CELL_Y = B['footprint']
GRID = IF['floor']['grid_M3_inserts_top']
GX = [GRID['x0'] + GRID['pitch'] * k for k in range(GRID['nx'])]
GY = [GRID['y0'] + GRID['pitch'] * k for k in range(GRID['ny'])]

Z_TRAY0 = R.RAIL_Z1                              # 32.5, tray sits on the rail tops
TRAY_T = 5.0
Z_TRAY1 = Z_TRAY0 + TRAY_T                       # 37.5
TRAY_Y = (70.0, 238.0)
FACE_Y = (238.0, 258.0); FACE_SKIN = 3.0; FACE_Z = (10.0, 184.0)
SPLITS = {'front': [-466.0, -232.0, 0.0, 232.0, 466.0],             # tile / face splits, all in bin gaps
          'back': [-466.0, -348.0, -116.0, 116.0, 348.0, 466.0]}     # back seams keep clear of its x+-200 stations
GRIPS = {'front': (-116.0, 116.0), 'back': (-232.0, 232.0)}
RIB_Z0 = 20.0; RIB_YS = (82.0, 150.0, 222.0); RIB_T = 6.0
# rib bars under the tray, only where nothing fixed sits on the floor along the drawer's travel (own frame)
RIB_SPANS = {'front': [(-264.0, -88.0), (-88.0, 88.0), (88.0, 264.0)],
             'back': [(-466.0, -418.0), (-382.0, -290.0), (-164.0, 0.0), (0.0, 164.0), (290.0, 382.0), (418.0, 466.0)]}
RIB_INS_PITCH = 40.0
RAIL_INSERTS = (140, 180, 220, 260)              # rail local y (world -60 + y)
FACE_RAIL_INSERT = 302.0
# bins
BIN_CLR = 0.6
BIN_W = CELL_X - 2 * BIN_CLR
BIN_TOP = B['top_z_max']                          # 176
BIN_H = BIN_TOP - Z_TRAY1                        # 138.5
BIN_WALL, BIN_FLOOR, BIN_R = 1.26, 1.6, 6.0
LABEL_DEPTH = 2.4
BIN_Y0 = ROW_Y - CELL_Y / 2 + BIN_CLR
BIN_Y1 = ROW_Y + CELL_Y / 2 - BIN_CLR - LABEL_DEPTH
LOC_T, LOC_H = 8.0, 6.0
# retaining bar over the bins' inner rims
BAR_Y = (72.0, 82.0); BAR_Z = (176.5, 182.5)
POST_W = 6.0
# switches
SW_L, SW_W, SW_H = 20.0, 6.4, 10.3
SW_CLR = 0.2; SW_HOLE_PITCH, SW_HOLE_D = 9.5, 2.2
CLOSED_SW_X = -400.0

COL = {'rail': (0.95, 0.55, 0.15), 'station': (0.25, 0.45, 0.75), 'brg': (0.75, 0.75, 0.78), 'tray': (0.80, 0.80, 0.82),
       'face_F': (0.10, 0.35, 0.70), 'face_B': (0.10, 0.55, 0.30), 'bin': (0.96, 0.87, 0.65),
       'ink': (0.97, 0.97, 0.97), 'sw': (0.2, 0.2, 0.2), 'bar': (0.85, 0.2, 0.2)}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(x, y, z0, h, d):
    return cq.Workplane().circle(d / 2).extrude(h).translate((x, y, z0))


def cyly(x, y0, z, h, d):
    return cq.Workplane('XZ').center(x, z).circle(d / 2).extrude(-h).translate((0, y0, 0))


# ---------------- rails, stations, guide ----------------
def rail_parts(rail_xs):
    """moving rails and fixed floor parts for one drawer in its own (front) frame."""
    det = R.ROLLERS_Y[3] - R.RAIL_Y0_WORLD - 6.0
    base = R.rail(insert_ys=RAIL_INSERTS + (FACE_RAIL_INSERT,), detent_y=det)
    moving, fixed, bearings = [], [], []
    for x in rail_xs:
        right = x > 0
        r = base if right else R.mirror_x(base)
        moving.append(('rail_' + ('R' if right else 'L'), r.translate((x, R.RAIL_Y0_WORLD, 0))))
        stF, rF, _ = R.station(R.ROLLERS_Y[2:], rail_x_world=abs(x))
        stB, rB, _ = R.station(R.ROLLERS_Y[:2], slotted_index=0, rail_x_world=abs(x))
        for nm, s in (('station_front', stF), ('station_rear', stB)):
            s2 = s if right else R.mirror_x(s)
            fixed.append((nm + ('_R' if right else '_L'), s2.translate((x, 0, 0))))
        for rr in rF + rB:
            bearings.append((rr if right else R.mirror_x(rr)).translate((x, 0, 0)))
        if right:
            g, rg, _ = R.guide_block((175.0, 215.0), rail_x_world=x)
            fixed.append(('guide_R', g.translate((x, 0, 0))))
            bearings += [b.translate((x, 0, 0)) for b in rg]
    return moving, fixed, bearings


# ---------------- tray ----------------
def tray_tile(i, rail_xs, sp, side):
    x0, x1 = sp[i], sp[i + 1]; n = len(sp) - 1
    t = box(x0, x1, TRAY_Y[0], TRAY_Y[1], Z_TRAY0, Z_TRAY1)
    t = t.union(box(x0 + 5, x1 - 5, TRAY_Y[1], FACE_Y[1] - FACE_SKIN - 1, Z_TRAY0, Z_TRAY0 + 2.5))   # tongue under the face foot
    t = t.union(box(x0, x1, TRAY_Y[0], TRAY_Y[0] + 3.5, Z_TRAY1, Z_TRAY1 + 30))                   # rear stop wall
    gaps = [(XC[k] + XC[k + 1]) / 2 for k in range(len(XC) - 1)]
    for g in gaps + [-463.0, 463.0]:
        w = LOC_T if abs(g) < 460 else 6.0
        a, b = max(g - w / 2, x0), min(g + w / 2, x1)
        if b - a > 0.5:
            t = t.union(box(a, b, BIN_Y0, BIN_Y1, Z_TRAY1, Z_TRAY1 + LOC_H))
    for x in XC:
        if x0 < x < x1:
            for dx in (-44, 44):
                t = t.union(box(x + dx - 4, x + dx + 4, BIN_Y1 + LABEL_DEPTH + 0.6, BIN_Y1 + LABEL_DEPTH + 4.6, Z_TRAY1, Z_TRAY1 + LOC_H))
    # bar posts (separate parts 171) screw up from below: clearance holes, and room for the post
    for px in post_xs(sp):
        if x0 - POST_W <= px <= x1 + POST_W:
            t = t.cut(box(px - POST_W / 2 - 0.2, px + POST_W / 2 + 0.2, TRAY_Y[0] - 1, TRAY_Y[0] + 18.2, Z_TRAY1, Z_TRAY1 + 40))
        if x0 - 0.01 <= px <= x1 + 0.01:
            for dy in (4.0, 14.0):
                xx = min(max(px, x0 + 3.5), x1 - 3.5)
                t = t.cut(cylz(xx, TRAY_Y[0] + dy, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR))
    # rib bars (separate parts 172) bolt from the top: counterbored holes
    for (a, b) in RIB_SPANS[side]:
        for yr in RIB_YS:
            for xh in rib_insert_xs(a, b):
                if x0 + 4 < xh < x1 - 4:
                    t = t.cut(cylz(xh, yr + RIB_T / 2, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR)).cut(cylz(xh, yr + RIB_T / 2, Z_TRAY1 - CB_DEPTH, CB_DEPTH + 1, CB_D))
    # bolts down into the rail-top inserts (counterbored)
    for rx in rail_xs:
        if x0 < rx < x1:
            ox = -2.0 if rx > 0 else 2.0
            for ly in RAIL_INSERTS:
                y = R.RAIL_Y0_WORLD + ly
                if TRAY_Y[0] + 6 < y < TRAY_Y[1] - 4:
                    t = t.cut(cylz(rx + ox, y, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR)).cut(cylz(rx + ox, y, Z_TRAY1 - CB_DEPTH, CB_DEPTH + 1, CB_D))
    # plate half-laps at the seams + 2 bolts
    if i < n - 1:
        t = t.union(box(x1, x1 + 12, TRAY_Y[0] + 20, TRAY_Y[1] - 6, Z_TRAY0, Z_TRAY0 + 2.5))
    if i > 0:
        t = t.cut(box(x0 - 0.01, x0 + 12.3, TRAY_Y[0] + 19.7, TRAY_Y[1] - 5.7, Z_TRAY0 - 1, Z_TRAY0 + 2.7))
    for xs in ([x1] if i < n - 1 else []) + ([x0] if i > 0 else []):
        for y in (116, 186):
            t = t.cut(cylz(xs + 6, y, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR))
    if x0 < CLOSED_SW_X < x1:   # holes for the switch tab (part 173)
        for dx in (-9, 9):
            t = t.cut(cylz(CLOSED_SW_X + dx, TRAY_Y[0] + 9, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR)).cut(cylz(CLOSED_SW_X + dx, TRAY_Y[0] + 9, Z_TRAY1 - CB_DEPTH, CB_DEPTH + 1, CB_D))
    return t


def switch_tab():
    t = box(CLOSED_SW_X - 14, CLOSED_SW_X + 14, TRAY_Y[0] + 3, TRAY_Y[0] + 15, Z_TRAY0 - 4, Z_TRAY0)
    t = t.union(box(CLOSED_SW_X - 6, CLOSED_SW_X + 6, TRAY_Y[0], TRAY_Y[0] + 6, 22.0, Z_TRAY0))
    for dx in (-9, 9):
        t = t.cut(cylz(CLOSED_SW_X + dx, TRAY_Y[0] + 9, Z_TRAY0 - INSERT_DEPTH, INSERT_DEPTH + 0.01, INSERT_D))
    return t


def post_xs(sp):
    return [sp[0] + 3.0] + sp[1:-1] + [sp[-1] - 3.0]


def rib_insert_xs(a, b):
    n = max(2, int((b - a) // RIB_INS_PITCH) + 1)
    return [a + 10 + k * (b - a - 20) / (n - 1) for k in range(n)]


def rib_bar(a, b, yr):
    r = box(a + 0.3, b - 0.3, yr, yr + RIB_T, RIB_Z0, Z_TRAY0)
    for xh in rib_insert_xs(a, b):
        r = r.cut(cylz(xh, yr + RIB_T / 2, Z_TRAY0 - INSERT_DEPTH, INSERT_DEPTH + 0.01, INSERT_D))
    return r


def bar_post(px):
    """retaining-bar post, screws up from under the tray (2 inserts in its foot)."""
    p = box(px - POST_W / 2, px + POST_W / 2, TRAY_Y[0], TRAY_Y[0] + 18, Z_TRAY1, Z_TRAY1 + 6)
    p = p.union(box(px - POST_W / 2, px + POST_W / 2, TRAY_Y[0] + 0.5, BAR_Y[1] + 3, Z_TRAY1, BAR_Z[1] + 1))
    p = p.cut(box(px - POST_W, px + POST_W, BAR_Y[0] - 0.3, BAR_Y[1] + 0.3, BAR_Z[0] - 0.3, BAR_Z[1] + 1.5))
    for dy in (4.0, 14.0):
        p = p.cut(cylz(px, TRAY_Y[0] + dy, Z_TRAY1 - 0.01, INSERT_DEPTH, INSERT_D))
    return p


def bar_piece(i, sp):
    """retaining bar: one piece per tile, ends rest in the post seats."""
    ps = post_xs(sp)
    x0, x1 = ps[i] + POST_W / 2 + 0.4, ps[i + 1] - POST_W / 2 - 0.4
    b = box(x0, x1, BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1])
    for xe in (x0, x1):   # end tongues sit in the post seats
        sgn = -1 if xe == x0 else 1
        b = b.union(box(min(xe, xe + sgn * (POST_W / 2 - 0.2)), max(xe, xe + sgn * (POST_W / 2 - 0.2)), BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1]))
    b = b.union(box(x0 + 20, x1 - 20, BAR_Y[0] + 2, BAR_Y[1] - 2, BAR_Z[1], BAR_Z[1] + 1.5))   # finger ridge
    return b


# ---------------- face ----------------
def number_for(x):
    return sorted(XC, reverse=True).index(x) + 1


def text_body(s, x):
    pl = cq.Plane(origin=(x, FACE_Y[1] - 0.6, 160), xDir=(-1, 0, 0), normal=(0, 1, 0))
    return cq.Workplane(pl).text(s, 30, 0.6, kind='bold', halign='center', valign='center')


def face_piece(i, letter, rail_xs, sp, side):
    n = len(sp) - 1
    xa = sp[i] + (0.25 if i > 0 else 0); xb = sp[i + 1] - (0.25 if i < n - 1 else 0)
    y0, y1 = FACE_Y
    f = box(xa, xb, y1 - FACE_SKIN, y1, FACE_Z[0], FACE_Z[1])
    f = f.union(box(xa, xb, y0, y1, FACE_Z[1] - 4, FACE_Z[1]))
    f = f.union(box(xa, xb, y0, y1, Z_TRAY0 + 2.5, Z_TRAY1))
    f = f.union(box(xa, xa + 4, y0, y1, Z_TRAY1, FACE_Z[1])).union(box(xb - 4, xb, y0, y1, Z_TRAY1, FACE_Z[1]))
    for x in XC:
        if xa < x < xb:
            for dx in (-30, 30):
                f = f.union(box(x + dx - 1.5, x + dx + 1.5, y0, y1, Z_TRAY1, FACE_Z[1]))
    f = f.union(box(xa, xb, y0, y1, 108, 111))
    for rx in rail_xs:
        if xa - 14 < rx < xb + 14:
            f = f.cut(box(rx - 12, rx + 12, y0 - 1, y1 + 1, FACE_Z[0] - 1, Z_TRAY0 + 0.5))
    for x in [xa + 30, (xa + xb) / 2, xb - 30]:
        if all(abs(x - rx) > 20 for rx in rail_xs):
            f = f.cut(cylz(x, 246, Z_TRAY0 - 1, 10, M3_CLR))
    for rx in rail_xs:
        if xa < rx < xb:
            f = f.cut(cylz(rx + (-2.0 if rx > 0 else 2.0), R.RAIL_Y0_WORLD + FACE_RAIL_INSERT, Z_TRAY0 + 1, 10, M3_CLR))
    for cx in GRIPS[side]:
        if xa + 50 < cx < xb - 50:
            f = f.cut(box(cx - 50, cx + 50, y1 - FACE_SKIN - 1, y1 + 1, 122, 142))
    ink = None
    for x in XC:
        if xa < x < xb:
            txt = text_body(f'{letter}{number_for(x)}', x)
            f = f.cut(txt); ink = txt if ink is None else ink.union(txt)
    return f, ink


# ---------------- bins, switch ----------------
def bin_part():
    x0, x1 = -BIN_W / 2, BIN_W / 2
    y0, y1 = BIN_Y0 - ROW_Y, BIN_Y1 - ROW_Y
    b = cq.Workplane().box(x1 - x0, y1 - y0, BIN_H, centered=False).translate((x0, y0, 0))
    b = b.edges('|Z').fillet(BIN_R).faces('>Z').shell(-BIN_WALL)
    b = b.union(cq.Workplane().box(x1 - x0 - 2 * BIN_WALL, y1 - y0 - 2 * BIN_WALL, BIN_FLOOR, centered=False)
                .translate((x0 + BIN_WALL, y0 + BIN_WALL, 0)).edges('|Z').fillet(BIN_R - BIN_WALL))
    rim = (cq.Workplane().box(x1 - x0, y1 - y0, 4, centered=False).translate((x0, y0, BIN_H - 4)).edges('|Z').fillet(BIN_R)
           .cut(cq.Workplane().box(x1 - x0 - 6, y1 - y0 - 6, 6, centered=False).translate((x0 + 3, y0 + 3, BIN_H - 5)).edges('|Z').fillet(BIN_R - 3)))
    b = b.union(rim)
    b = b.cut(box(-30, 30, y1 - 5, y1 + 1, BIN_H - 34, BIN_H - 16).edges('|Y').fillet(6))   # handle slot
    lw, lh, lz = 74.0, 34.0, 30.0
    holder = box(-lw / 2, lw / 2, y1, y1 + LABEL_DEPTH, lz, lz + lh)
    holder = holder.cut(box(-lw / 2 + 2, lw / 2 - 2, y1 + 0.6, y1 + 1.6, lz + 2, lz + lh + 1))
    holder = holder.cut(box(-lw / 2 + 5, lw / 2 - 5, y1 + 1.5, y1 + LABEL_DEPTH + 1, lz + 5, lz + lh + 1))
    return b.union(holder)


def closed_switch_mount():
    x, y = CLOSED_SW_X, 84.0
    m = box(x - 12, x + 12, 72.5, 108, FLOOR_TOP, FLOOR_TOP + 11)
    m = m.cut(box(x - SW_W / 2 - SW_CLR, x + SW_W / 2 + SW_CLR, y - SW_L / 2 - SW_CLR, y + SW_L / 2 + SW_CLR, FLOOR_TOP + 0.8, FLOOR_TOP + 12))
    for dy in (-SW_HOLE_PITCH / 2, SW_HOLE_PITCH / 2):
        m = m.cut(cq.Workplane('YZ').circle(SW_HOLE_D / 2).extrude(30).translate((x - 15, y + dy, FLOOR_TOP + 6)))
    m = m.cut(cylz(x, 100, FLOOR_TOP - 1, 20, M3_CLR)).cut(cylz(x, 100, FLOOR_TOP + 11 - CB_DEPTH, 10, CB_D))
    return m


def switch_dummy():
    x, y = CLOSED_SW_X, 84.0
    body = box(x - SW_W / 2, x + SW_W / 2, y - SW_L / 2, y + SW_L / 2, FLOOR_TOP + 0.8, FLOOR_TOP + 0.8 + SW_H)
    lever = box(x - 2, x + 2, y - SW_L / 2 - 4, y + 2, FLOOR_TOP + 0.8 + SW_H, FLOOR_TOP + 0.8 + SW_H + 2.0)   # pressed state
    return body.union(lever)


def rot180(w):
    return w.rotate((0, 0, 0), (0, 0, 1), 180)


# ---------------- build ----------------
def drawer(side):
    rail_xs = RX['front_drawer_rails_x'] if side == 'front' else RX['back_drawer_rails_x']
    letter = 'F' if side == 'front' else 'B'
    moving, fixed, brg = rail_parts(rail_xs)
    parts = []   # (label, shape, group)
    for n, s in moving: parts.append((f'160_{n}', s, 'moving'))
    for n, s in fixed:  parts.append((f'162_{n}', s, 'fixed'))
    for k, s in enumerate(brg): parts.append((f'625ZZ_{k+1}', s, 'fixed'))
    sp = SPLITS[side]; n = len(sp) - 1
    tiles = [tray_tile(i, rail_xs, sp, side) for i in range(n)]
    for i, t in enumerate(tiles): parts.append((f'165_tray_tile_{i+1}', t, 'moving'))
    ribs = [rib_bar(a, b, yr) for (a, b) in RIB_SPANS[side] for yr in RIB_YS]
    for k, rb in enumerate(ribs): parts.append((f'172_rib_{k+1}', rb, 'moving'))
    for k, px in enumerate(post_xs(sp)): parts.append((f'171_bar_post_{k+1}', bar_post(px), 'moving'))
    faces = [face_piece(i, letter, rail_xs, sp, side) for i in range(n)]
    pn = '166' if side == 'front' else '167'
    for i, (f, ink) in enumerate(faces):
        parts.append((f'{pn}_face_{letter}{i+1}', f, 'moving')); parts.append((f'{pn}_face_{letter}{i+1}_ink', ink, 'moving'))
    b0 = bin_part()
    for k, x in enumerate(XC): parts.append((f'168_bin_{k+1}', b0.translate((x, ROW_Y, Z_TRAY1)), 'moving'))
    for i in range(n): parts.append((f'169_bar_{i+1}', bar_piece(i, sp), 'moving'))
    parts.append(('170_closed_switch_mount', closed_switch_mount(), 'fixed'))
    parts.append(('173_switch_tab', switch_tab(), 'moving'))
    parts.append(('KW11_closed', switch_dummy(), 'fixed'))
    if side == 'back':
        parts = [(n, rot180(s), g) for n, s, g in parts]
    return parts, tiles, faces, b0, ribs


def color(lab):
    for k, c in (('_ink', 'ink'), ('160', 'rail'), ('162', 'station'), ('625', 'brg'), ('165', 'tray'), ('172', 'tray'), ('173', 'tray'), ('171', 'bar'), ('166', 'face_F'),
                 ('167', 'face_B'), ('168', 'bin'), ('169', 'bar')):
        if k in lab: return COL[c]
    return COL['sw']


def main():
    world = HERE / 'world'; prn = HERE / 'print'
    allp = {}; extra = {}
    for side in ('front', 'back'):
        parts, tiles, faces, b0, ribs = drawer(side)
        allp[side] = parts; extra[side] = (tiles, faces, b0, ribs)
    asm = cq.Assembly(name='drawer_module')
    for side in allp:
        for lab, s, g in allp[side]:
            export(s, world / f'{side}_{lab}.step')
            asm.add(s, name=f'{side}_{lab}', color=cq.Color(*color(lab)))
    asm.save(str(world / 'drawer_assembly.step'))
    # ---- print files ----
    printable = []
    base = R.rail(insert_ys=RAIL_INSERTS + (FACE_RAIL_INSERT,), detent_y=R.ROLLERS_Y[3] - R.RAIL_Y0_WORLD - 6.0)
    printable += [('160_rail_R', base, 'rail_R', 2, 'PETG'), ('161_rail_L', R.mirror_x(base), 'rail_L', 2, 'PETG')]
    stF = R.station(R.ROLLERS_Y[2:], rail_x_world=300)[0]; stB = R.station(R.ROLLERS_Y[:2], slotted_index=0, rail_x_world=300)[0]
    stF2 = R.station(R.ROLLERS_Y[2:], rail_x_world=200)[0]; stB2 = R.station(R.ROLLERS_Y[:2], slotted_index=0, rail_x_world=200)[0]
    printable += [('162_station_front_x300', stF, None, 2, 'PETG (1 R + 1 mirrored L)'), ('163_station_rear_x300', stB, None, 2, 'PETG (1 R + 1 mirrored L)'),
                  ('162_station_front_x200', stF2, None, 2, 'PETG (1 R + 1 mirrored L)'), ('163_station_rear_x200', stB2, None, 2, 'PETG (1 R + 1 mirrored L)'),
                  ('164_guide_x300', R.guide_block((175.0, 215.0), rail_x_world=300)[0], None, 1, 'PETG'),
                  ('164_guide_x200', R.guide_block((175.0, 215.0), rail_x_world=200)[0], None, 1, 'PETG')]
    for side, pn, letter in (('front', '166', 'F'), ('back', '167', 'B')):
        tiles, faces, b0, ribs = extra[side]
        for i, t in enumerate(tiles):
            printable.append((f'165_tray_tile_{side}_{i+1}', t, None, 1, 'PLA'))
        lens = {}
        for (a, b) in RIB_SPANS[side]:
            lens.setdefault(round(b - a), (a, b)); 
        for L, (a, b) in lens.items():
            q = len(RIB_YS) * sum(1 for (aa, bb) in RIB_SPANS[side] if round(bb - aa) == L)
            printable.append((f'172_rib_{side}_{L}mm', rib_bar(a, b, 0.0), 'side', q, 'PLA'))
        for k, px in enumerate(post_xs(SPLITS[side])):
            if k == 0 or k == len(SPLITS[side]) - 1 or k == 1:
                pass
        for k in range(len(SPLITS[side]) - 1):
            printable.append((f'169_bar_{side}_{k+1}', bar_piece(k, SPLITS[side]), None, 1, 'PLA'))
        for i, (f, ink) in enumerate(faces):
            printable.append((f'{pn}_face_{letter}{i+1}', f, ('face', f), 1, 'PLA ' + ('front colour' if side == 'front' else 'back colour')))
            printable.append((f'{pn}_face_{letter}{i+1}_ink', ink, ('face', f), 1, 'PLA white (AMS, same plate)'))
    printable += [('168_bin', extra['front'][2], None, 16, 'PLA')]
    printable.append(('171_bar_post', bar_post(0.0), None, 12, 'PLA'))
    printable.append(('170_closed_switch_mount', closed_switch_mount(), None, 2, 'PLA'))
    printable.append(('173_switch_tab', switch_tab(), None, 2, 'PLA'))
    plist = []
    for name, shp, how, qty, mat in printable:
        if how in ('rail_R', 'rail_L'):
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (0, 1, 0), -90 if how == 'rail_R' else 90))
        elif how == 'side':
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (1, 0, 0), 90))   # rib bar on its side
        elif isinstance(how, tuple):
            w = shp.rotate((0, 0, 0), (1, 0, 0), -90); bb = bbox(how[1].rotate((0, 0, 0), (1, 0, 0), -90))
            bedp = w.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2])); diag = False
        else:
            bedp, diag = print_pose(shp)
        export(bedp, prn / f'{name}_PRINT_{qty}.stl')
        plist.append({'label': name, 'part_no': name[:3], 'qty': qty, 'material': mat, **bed_fit(bedp), 'diagonal_on_bed': diag,
                      'est_grams_each': grams(shp, density=1.27 if 'PETG' in mat else 1.24)})
    bought = [
        {'item': '625ZZ bearing', 'qty': 20, 'use': '8 roller + 2 guide per drawer'},
        {'item': 'M5 x 25 screw + nut', 'qty': 16, 'use': 'station roller axles'},
        {'item': 'M5 x 16 screw', 'qty': 4, 'use': 'guide roller axles'},
        {'item': 'M3 heat-set insert', 'qty': 4 * 5 + 12 * 2 + 4 + 120, 'use': 'rail tops, bar posts, switch tabs, rib bars (~40 mm pitch)'},
        {'item': 'M3 x 10 screw', 'qty': 4 * 4 + 2 * 12 + 2 * 2 + 2, 'use': 'tray to rails, stations + guides to floor, switch mounts'},
        {'item': 'M3 x 12 screw + nut', 'qty': 2 * (3 * 2 + 3 * 3 * 2 + 4 * 2), 'use': 'plate laps, rib laps, face to tray'},
        {'item': 'M3 x 16 screw', 'qty': 4, 'use': 'face foot into the rail front insert'},
        {'item': 'M3 x 16 screw (jack)', 'qty': 4, 'use': 'rear roller preload'},
        {'item': 'KW11-3Z', 'qty': 2, 'use': 'drawer closed, front and back'},
        {'item': 'M2 x 12 screw + nut', 'qty': 4, 'use': 'switches'},
    ]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'D', 'interface': IF['version'], 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(sum(p['est_grams_each'] * p['qty'] for p in plist))}, indent=1))
    res = checks(allp, plist)
    stills(allp)
    return res


def _bb_overlap(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def clash(lst, skip=lambda a, b: False):
    hits = []; bbs = [(n, s, bbox(s)) for n, s in lst]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            if not _bb_overlap(bbs[i][2], bbs[j][2]) or skip(bbs[i][0], bbs[j][0]): continue
            v = bbs[i][1].intersect(bbs[j][1]); vol = v.val().Volume() if v.vals() else 0
            if vol > 0.5: hits.append([bbs[i][0], bbs[j][0], round(vol, 1)])
    return hits


def checks(allp, plist):
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    zc = {}
    for side in allp:
        z = Z[side]
        for lab, s, g in allp[side]:
            if lab.startswith(('625', 'KW11')) or lab.endswith('_ink'): continue
            b = bbox(s)
            inz = z['x'][0] - .01 <= b[0] and b[3] <= z['x'][1] + .01 and z['y'][0] - .01 <= b[1] and b[4] <= z['y'][1] + .01 and z['z'][0] - .01 <= b[2] and b[5] <= z['z'][1] + .01
            if not inz and lab.startswith('160'):
                sp = IF['center_spine']; tz = RX['rail_zone_z']
                yl = min(z['y'][0], sp['y'][0]); yh = max(z['y'][1], sp['y'][1])
                inz = yl - .01 <= b[1] and b[4] <= yh + .01 and tz[0] - .01 <= b[2] and b[5] <= tz[1] + .01
                zc[f'{side}_{lab}'] = 'D zone + spine tunnel (rails, allowed)' if inz else f'OUTSIDE {b}'
            else:
                zc[f'{side}_{lab}'] = 'in D zone' if inz else f'OUTSIDE {b}'
    res['zones'] = zc
    # roller/rail contact is by design at 0.25 mm gaps: skip rail-vs-625 pairs only if volume tiny (handled by threshold)
    def state(fo, bo):
        out = []
        for side, op in (('front', fo), ('back', bo)):
            dy = TRAVEL if side == 'front' else -TRAVEL
            for lab, s, g in allp[side]:
                if lab.endswith('_ink'): continue
                out.append((f'{side}_{lab}', s.translate((0, dy, 0)) if (op and g == 'moving') else s))
        return out
    skip = lambda a, b: ('KW11' in a and '165_tray' in b) or ('KW11' in b and '165_tray' in a)   # tab presses the lever when closed
    res['clash_both_closed'] = clash(state(False, False), skip)
    res['clash_front_open'] = clash(state(True, False))
    res['clash_back_open'] = clash(state(False, True))
    res['clash_both_open'] = clash(state(True, True))
    fb = [bbox(s) for lab, s, g in allp['front'] if lab.startswith('168_bin')]
    res['bin_top_z'] = round(max(b[5] for b in fb), 2); res['bin_top_ok'] = res['bin_top_z'] <= B['top_z_max'] + 1e-6
    res['bin_height'] = round(BIN_H, 1)
    res['front_open_bin_rear_y'] = round(min(b[1] for b in fb) + TRAVEL, 1)
    res['open_bins_clear_face'] = res['front_open_bin_rear_y'] > IF['envelope']['y'][1]
    res['keyed'] = {'front_rails_x': RX['front_drawer_rails_x'], 'back_rails_x': RX['back_drawer_rails_x'],
                    'note': 'each drawer only fits the roller stations at its own rail spacing'}
    res['runner_sweep'] = json.loads((HERE / 'runner_test' / 'runner_test_parts.json').read_text())['sweep_check_right_rail']
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(allp):
    def items(fo=False, bo=False, face_op=1.0, only=None):
        out = []
        for side, op in (('front', fo), ('back', bo)):
            dy = TRAVEL if side == 'front' else -TRAVEL
            for lab, s, g in allp[side]:
                if only and not lab.startswith(only): continue
                s2 = s.translate((0, dy, 0)) if (op and g == 'moving') else s
                out.append((s2, color(lab), face_op if lab.startswith(('166', '167')) else 1.0))
        return out
    render(items(), HERE / 'still_1_closed_front.png', cam=(700, 1500, 650), focal=(0, 0, 90), title='V14 drawers closed (interface 4.1): front face F1-F8')
    render(items(fo=True), HERE / 'still_2_front_open.png', cam=(1100, 1300, 700), focal=(0, 150, 60), title='Front drawer out 205 mm: bins clear the face, retaining bar on the inner rims')
    render(items(bo=True, face_op=0.3), HERE / 'still_3_back_open.png', cam=(-900, -1400, 650), focal=(0, -150, 60), title='Back drawer out 205 mm: B1-B8 left to right from the back')
    render(items(only=('160', '162', '625', '170', 'KW11')), HERE / 'still_4_rails_top.png', cam=(0, 0, 1600), focal=(0, 0, 0), up=(0, 1, 0), ortho=330,
           title='Rails and floor stations from above (front at top): front rails x +-300, back x +-200, tails cross in the spine')


if __name__ == '__main__':
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ('zones', 'bed_fit', 'runner_sweep')}, indent=1))
    print(sorted(set(r['zones'].values()))); print('bed all fit:', all(r['bed_fit'].values()), [k for k, v in r['bed_fit'].items() if not v])
