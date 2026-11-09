"""V14 module D, interface 5.1: two opposing 8-bin drawers on under-drawer roller rails (CadQuery 2.8).

Front drawer in world coordinates; the back drawer is the same design turned 180 deg about Z with its rails
at x +-120 (front +-200), so the drawers are keyed. Tray 2.4 plate + ribs on the rail tops (z 37..39.4, bin
floor at 41), 4 tiles; overlay face (x +-330, y 180..192, z 8..140) in 3 pieces with an F/B + number inlay;
8 bins 70 x 95 x 85 (0.84 walls); retaining bar over the inner rims; one KW11-3Z closed switch on the floor;
a reed switch in the tray under every bin (magnet in the bin floor) wired to one MCP23017 per drawer.
Run: python3 build_drawer.py
"""
import json, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import csk_cone
from common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, WOOD_SCREW, print_pose, bed_fit, export, bbox, grams, hours, render
import runner as R

D = IF['drawer']; B = IF['bins']; Z = IF['zones']['D_drawers']
FLOOR_TOP = IF['wood']['floor_ply']['z'][1]      # 12
TRAVEL = D['travel_y']                           # 150
XC = B['x_centers']; ROW_Y = B['row_y_centers'][1]   # 102.5
CELL_X, CELL_Y = 76.0, B['footprint_xy'][1]      # pitch 76, 95
BIN_W, BIN_L, BIN_H = B['footprint_xy'][0], B['footprint_xy'][1], B['height']   # 70, 95, 85
Z_TRAY0 = R.RAIL_Z1                              # 37
TRAY_T = 2.4; RIB_H = 6.0; RIB_T = 2.4
Z_TRAY1 = B['z'][0]                              # 41 = bin floor (tray plate 37..39.4, locators to 41? no: plate top 39.4 + 1.6 shim)
Z_PLATE1 = Z_TRAY0 + TRAY_T                      # 39.4
TRAY_Y = (52.0, 180.0)
FACE = Z['front']['face']; FACE_Y = tuple(FACE['y']); FACE_Z = tuple(FACE['z']); FACE_X = FACE['x'][1]   # y 180..192, z 8..140, x +-330
FACE_SKIN = 2.0
TRAY_SPLITS = [-306.0, -152.0, 0.0, 152.0, 306.0]
FACE_SPLITS = [-330.0, -95.0, 95.0, 330.0]
RAIL_INSERTS = (60.0, 100.0, 140.0, 175.0)       # rail local y (world -40 + y) -> world 20 (under the tray? no: 20 < 54, skip), 60, 100, 135
FACE_RAIL_INSERT = 214.0                         # world 174: face foot bolts into the rail front
BIN_CLR = 0.6; BIN_WALL = 0.84; BIN_FLOOR = 1.2; BIN_R = 5.0
LABEL_DEPTH = 2.4
BIN_X0 = -BIN_W / 2 + BIN_CLR; BIN_X1 = BIN_W / 2 - BIN_CLR                      # local
BIN_Y0 = ROW_Y - BIN_L / 2 + BIN_CLR; BIN_Y1 = ROW_Y + BIN_L / 2 - BIN_CLR - LABEL_DEPTH   # 55.6 .. 147.5 (world, front)
LOC_T, LOC_H = 4.0, 6.0
BAR_Y = (55.0, 60.0); BAR_Z = (126.3, 130.3); POST_W = 6.0
SW_L, SW_W, SW_H = 20.0, 6.4, 10.3; SW_CLR = 0.2; SW_HOLE_PITCH, SW_HOLE_D = 9.5, 2.2
CLOSED_SW_X = -250.0
# per-bin presence (docs/electrical V14 plan): 2 x 14 mm glass reed (N/O) in the tray under each bin, 6 x 2 mm magnet in the bin floor
REED_DX = 25.0                                   # same bin-local x in every bin: clears the rails at +-200 (front) and +-120 (back) by >= 4 mm
REED_D, REED_L, REED_LEAD = 2.0, 14.0, 9.0       # glass, body, lead groove past each end
REED_GROOVE_W = 2.6; REED_FLOOR_Z = 38.0         # glass 38.0..40.0 (+0.5 slack under the bin floor at 41)
MAG_D, MAG_T = 6.0, 2.0; MAG_DY = 5.0            # magnet over one end of the reed (a disc over the middle can sit in the null)
MAG_HOLE = MAG_D - 2 * 0.02                      # press fit per the runbook (-0.02 per side); CA glue if loose
MCP = dict(x=(-75.0, -35.0), y=(117.2, 142.8), pcb=1.6)   # MCP23017 module 40 x 25 (assumed), slides into hooks under tile 2

COL = {'rail': (0.95, 0.55, 0.15), 'station': (0.25, 0.45, 0.75), 'brg': (0.75, 0.75, 0.78), 'tray': (0.80, 0.80, 0.82),
       'face_F': (0.10, 0.35, 0.70), 'face_B': (0.10, 0.55, 0.30), 'bin': (0.96, 0.87, 0.65), 'ink': (0.97, 0.97, 0.97),
       'sw': (0.2, 0.2, 0.2), 'bar': (0.85, 0.2, 0.2)}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(x, y, z0, h, d):
    return cq.Workplane().circle(d / 2).extrude(h).translate((x, y, z0))


def rot180(w):
    return w.rotate((0, 0, 0), (0, 0, 1), 180)


# ---------------- runners ----------------
def rail_parts(rail_x):
    det = R.ROLLERS_Y[-1] - R.RAIL_Y0_WORLD - 6.0
    base = R.rail(insert_ys=RAIL_INSERTS + (FACE_RAIL_INSERT,), detent_y=det)
    moving, fixed, bearings = [], [], []
    for x in (-rail_x, rail_x):
        right = x > 0
        r = base if right else R.mirror_x(base)
        moving.append(('160_rail_' + ('R' if right else 'L'), r.translate((x, R.RAIL_Y0_WORLD, 0))))
        stF, rF, _ = R.station(R.ROLLERS_Y, slotted_index=0)
        fixed.append(('162_station' + ('_R' if right else '_L'), (stF if right else R.mirror_x(stF)).translate((x, 0, 0))))
        for rr in rF:
            bearings.append((rr if right else R.mirror_x(rr)).translate((x, 0, 0)))
        if right:
            g, rg, _ = R.guide_block((134.0, 162.0))
            fixed.append(('164_guide_R', g.translate((x, 0, 0))))
            bearings += [b.translate((x, 0, 0)) for b in rg]
    return moving, fixed, bearings


# ---------------- tray ----------------
def tray_tile(i, rail_x):
    x0, x1 = TRAY_SPLITS[i], TRAY_SPLITS[i + 1]
    t = box(x0, x1, TRAY_Y[0], TRAY_Y[1], Z_TRAY0, Z_PLATE1)
    # bin shim strips so the bins stand at z 41 (plate top 39.4): 1.6 tall pads under each bin edge
    t = t.union(box(x0, x1, BIN_Y0 - 2, BIN_Y1 + LABEL_DEPTH + 2, Z_PLATE1, Z_TRAY1).cut(
        box(x0 - 1, x1 + 1, BIN_Y0 + 6, BIN_Y1 - 6, Z_PLATE1 - 1, Z_TRAY1 + 1)))
    # locators between bins (4 wide in the 6.6 gaps), rear stop wall, front stops (clear of the label holder)
    gaps = [(XC[k] + XC[k + 1]) / 2 for k in range(len(XC) - 1)] + [XC[0] - CELL_X / 2, XC[-1] + CELL_X / 2]
    for g in gaps:
        a, b = max(g - LOC_T / 2, x0), min(g + LOC_T / 2, x1)
        if b - a > 0.5: t = t.union(box(a, b, BIN_Y0 - 2, BIN_Y1 + 2, Z_TRAY1 - 0.01, Z_TRAY1 + LOC_H))
    t = t.union(box(x0, x1, TRAY_Y[0], TRAY_Y[0] + 2.4, Z_PLATE1, Z_TRAY1 + 12))
    for x in XC:
        if x0 < x < x1:
            for dx in (-26, 26):
                t = t.union(box(x + dx - 3, x + dx + 3, BIN_Y1 + LABEL_DEPTH + 0.6, BIN_Y1 + LABEL_DEPTH + 3.0, Z_TRAY1 - 0.01, Z_TRAY1 + LOC_H))
    # ribs under the plate: along x at y 70, 110, 150 and along y at the tile edges, 6 tall (rail zone ends 38? ribs are at z 31..37
    # between the rails only where no rail: ribs must stay above the stations -> ribs only inside |x| < rail_x - 12)
    for yr in (70.0, 110.0, 150.0):
        a, b = max(x0, -rail_x + 12), min(x1, rail_x - 12)
        if b - a > 10: t = t.union(box(a, b, yr - RIB_T / 2, yr + RIB_T / 2, Z_TRAY0 - RIB_H, Z_TRAY0 + 0.01))
    for xr in (x0 + 1.2, x1 - 1.2):
        if abs(xr) < rail_x - 12 or abs(xr) > rail_x + 12:
            t = t.union(box(xr - RIB_T / 2, xr + RIB_T / 2, TRAY_Y[0], 172.0, Z_TRAY0 - RIB_H, Z_TRAY0 + 0.01))
    # bolts down into the rail-top inserts (counterbored from the top)
    for rx in (-rail_x, rail_x):
        if x0 < rx < x1:
            ox = -2.0 if rx > 0 else 2.0
            for ly in RAIL_INSERTS:
                y = R.RAIL_Y0_WORLD + ly
                if TRAY_Y[0] + 4 < y < TRAY_Y[1] - 4:
                    t = t.cut(cylz(rx + ox, y, Z_TRAY0 - 1, 10, M3_CLR)).cut(cylz(rx + ox, y, Z_TRAY1 - 1.2, 5, CB_D))
    # seams: half-lap 10 mm (lower half of the plate) + 2 x M3 + nut
    if i < 3: t = t.union(box(x1, x1 + 10, TRAY_Y[0] + 6, TRAY_Y[1] - 6, Z_TRAY0, Z_TRAY0 + 1.2))
    if i > 0: t = t.cut(box(x0 - 0.01, x0 + 10.07, TRAY_Y[0] + 5.93, TRAY_Y[1] - 5.93, Z_TRAY0 - 1, Z_TRAY0 + 1.27))
    for xs in ([x1 + 5] if i < 3 else []) + ([x0 + 5] if i > 0 else []):
        for y in (80.0, 160.0): t = t.cut(cylz(xs, y, Z_TRAY0 - 7, 12, M3_CLR))
    # retaining-bar posts at the tile seams and ends, closed-switch tab
    for px in (TRAY_SPLITS[0] + 2.5, -152.0, 0.0, 152.0, TRAY_SPLITS[-1] - 2.5):
        pw = 5.0 if abs(px) > 300 else POST_W
        a, b = max(px - pw / 2, x0), min(px + pw / 2, x1)
        if b - a > 0.5:
            t = t.union(box(a, b, TRAY_Y[0], BAR_Y[1] + 2.4, Z_PLATE1, BAR_Z[1] + 1.2))
            t = t.cut(box(a - 1, b + 1, BAR_Y[0] - 0.3, BAR_Y[1] + 0.3, BAR_Z[0] - 0.3, BAR_Z[1] + 2))
    if x0 < CLOSED_SW_X < x1:
        t = t.union(box(CLOSED_SW_X - 5, CLOSED_SW_X + 5, TRAY_Y[0], TRAY_Y[0] + 5, FLOOR_TOP + SW_H + 0.8, Z_TRAY0 + 0.01))
    # reed switch per bin: boss under the plate, groove in the plate top, lead slots and wire holes at both ends
    for x in XC:
        rx = x + REED_DX
        if x0 + 4 < rx < x1 - 4:
            yl = REED_L / 2 + REED_LEAD
            t = t.union(box(rx - 3.5, rx + 3.5, ROW_Y - yl - 3, ROW_Y + yl + 3, Z_TRAY0 - 2.0, Z_TRAY0 + 0.01))
            t = t.cut(box(rx - REED_GROOVE_W / 2, rx + REED_GROOVE_W / 2, ROW_Y - REED_L / 2 - 0.5, ROW_Y + REED_L / 2 + 0.5, REED_FLOOR_Z, Z_TRAY1 + 1))
            t = t.cut(box(rx - 0.75, rx + 0.75, ROW_Y - yl, ROW_Y + yl, REED_FLOOR_Z + 0.2, Z_TRAY1 + 1))
            for yy in (ROW_Y - yl, ROW_Y + yl): t = t.cut(cylz(rx, yy, Z_TRAY0 - 3, 10, 2.5))
    # MCP23017 module hooks under the plate (board slides in along x, components up, wires soldered, no headers)
    if x0 < MCP['x'][0] and MCP['x'][1] < x1:
        (a, b), (c, d) = MCP['x'], MCP['y']; zb = Z_TRAY0 - 12.0                     # pcb bottom at z 25
        for (w0, w1) in ((c - 2.0, c + 1.2), (d - 1.2, d + 2.0)):
            hook = box(a, b, w0, w1, zb - 1.6, Z_TRAY0 + 0.01)
            hook = hook.cut(box(a - 1, b + 1, c + 1.2 - 0.01, d - 1.2 + 0.01, zb + 0.01, Z_TRAY0 + 1))   # clear the board area above the lip
            t = t.union(hook)
        t = t.cut(box(a - 1, b + 1, c - 0.07, d + 0.07, zb - 0.07, zb + MCP['pcb'] + 0.2))           # slot for the pcb edges
        t = t.union(box(b, b + 2.0, c - 2.0, d + 2.0, zb - 1.6, Z_TRAY0 + 0.01))                     # end stop at +x
    return t


def bar_piece(i):
    posts = [TRAY_SPLITS[0] + 2.5, -152.0, 0.0, 152.0, TRAY_SPLITS[-1] - 2.5]
    x0, x1 = posts[i] + POST_W / 2 + 0.4, posts[i + 1] - POST_W / 2 - 0.4
    b = box(x0 - POST_W / 2 - 0.2, x1 + POST_W / 2 + 0.2, BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1])
    return b


# ---------------- face ----------------
def number_for(x):
    return sorted(XC, reverse=True).index(x) + 1


def text_body(s, x, z, size):
    pl = cq.Plane(origin=(x, FACE_Y[1] - 0.6, z), xDir=(-1, 0, 0), normal=(0, 1, 0))
    return cq.Workplane(pl).text(s, size, 0.6, kind='bold', halign='center', valign='center')


def face_piece(i, letter, rail_x):
    xa = FACE_SPLITS[i] + (0.25 if i > 0 else 0); xb = FACE_SPLITS[i + 1] - (0.25 if i < 2 else 0)
    y0, y1 = FACE_Y; z0, z1 = FACE_Z
    f = box(xa, xb, y1 - FACE_SKIN, y1, z0, z1)
    # rib frame behind the skin, inside the opening only (|x| <= 306, z 12..134) so the face sits flat on the skin
    xi0, xi1 = max(xa, -304.0), min(xb, 304.0)
    for (a, b, c, d) in ((xi0, xi1, 14.0, 16.4), (xi0, xi1, 131.6, 134.0), (xi0, xi0 + 2.4, 14.0, 134.0), (xi1 - 2.4, xi1, 14.0, 134.0),
                         (xi0, xi1, 72.0, 74.4)):
        if b > a: f = f.union(box(a, b, y1 - FACE_SKIN - 6.0, y1 - FACE_SKIN + 0.01, c, d))
    for x in XC:
        if xi0 < x - 20 and x + 20 < xi1:
            f = f.union(box(x - 1.2, x + 1.2, y1 - FACE_SKIN - 6.0, y1 - FACE_SKIN + 0.01, 14.0, 134.0))
    # foot onto the tray front edge (tray y 180 = face y0): a 6 x 20 ledge under the tray plate level, bolts up into tray inserts
    f = f.union(box(xi0, xi1, y0, y0 + 6.0, Z_TRAY0 - 6, Z_TRAY0 + 0.01)) if False else f
    f = f.union(box(xi0, xi1, y0 - 6.0, y1 - FACE_SKIN + 0.01, Z_TRAY0 - RIB_H, Z_TRAY0))     # tongue under the tray front edge
    # notches for the rails and bolts into the rail front inserts
    for rx in (-rail_x, rail_x):
        if xa - 12 < rx < xb + 12:
            f = f.cut(box(rx - 26, rx + 26, y0 - 9, y1 - FACE_SKIN - 0.5, z0 - 1, Z_TRAY0 + 0.5))
            f = f.cut(cylz(rx + (-2.0 if rx > 0 else 2.0), R.RAIL_Y0_WORLD + FACE_RAIL_INSERT, z0 - 1, 40, M3_CLR))
    # grip slot in the middle piece
    if i == 1:
        f = f.cut(box(-45, 45, y1 - FACE_SKIN - 1, y1 + 1, 100, 118))
    ink = None
    for x in XC:
        if xa < x < xb:
            txt = text_body(f'{letter}{number_for(x)}', x, 48.0, 22)
            f = f.cut(txt); ink = txt if ink is None else ink.union(txt)
    return f, ink


# ---------------- bins, switch ----------------
def bin_part():
    x0, x1 = BIN_X0, BIN_X1
    y0, y1 = BIN_Y0 - ROW_Y, BIN_Y1 - ROW_Y
    b = cq.Workplane().box(x1 - x0, y1 - y0, BIN_H, centered=False).translate((x0, y0, 0))
    b = b.edges('|Z').fillet(BIN_R).faces('>Z').shell(-BIN_WALL)
    b = b.union(cq.Workplane().box(x1 - x0 - 2 * BIN_WALL, y1 - y0 - 2 * BIN_WALL, BIN_FLOOR, centered=False)
                .translate((x0 + BIN_WALL, y0 + BIN_WALL, 0)).edges('|Z').fillet(BIN_R - BIN_WALL))
    rim = (cq.Workplane().box(x1 - x0, y1 - y0, 3, centered=False).translate((x0, y0, BIN_H - 3)).edges('|Z').fillet(BIN_R)
           .cut(cq.Workplane().box(x1 - x0 - 4, y1 - y0 - 4, 5, centered=False).translate((x0 + 2, y0 + 2, BIN_H - 4)).edges('|Z').fillet(BIN_R - 2)))
    b = b.union(rim)
    b = b.cut(box(-18, 18, y1 - 4, y1 + 1, BIN_H - 26, BIN_H - 12).edges('|Y').fillet(4))   # finger slot (front wall)
    lw, lh, lz = 50.0, 26.0, 20.0                                                            # label card 46 x 24
    holder = box(-lw / 2, lw / 2, y1, y1 + LABEL_DEPTH, lz, lz + lh)
    holder = holder.cut(box(-lw / 2 + 2, lw / 2 - 2, y1 + 0.6, y1 + 1.5, lz + 2, lz + lh + 1))
    holder = holder.cut(box(-lw / 2 + 5, lw / 2 - 5, y1 + 1.4, y1 + LABEL_DEPTH + 1, lz + 5, lz + lh + 1))
    b = b.union(holder)
    # magnet boss inside the floor, pocket open to the bottom (bed face) under the reed's +y end
    mx, my = REED_DX, MAG_DY
    b = b.union(cylz(mx, my, 0, MAG_T + 0.6, MAG_D + 2.4))
    b = b.cut(cylz(mx, my, -0.01, MAG_T + 0.01, MAG_HOLE))
    return b


def closed_switch_mount():
    x, y = CLOSED_SW_X, 70.0
    m = box(x - 11, x + 11, 56.0, 92.0, FLOOR_TOP, FLOOR_TOP + 10.3)
    m = m.cut(box(x - SW_W / 2 - SW_CLR, x + SW_W / 2 + SW_CLR, y - SW_L / 2 - SW_CLR, y + SW_L / 2 + SW_CLR, FLOOR_TOP + 0.8, FLOOR_TOP + 12))
    for dy in (-SW_HOLE_PITCH / 2, SW_HOLE_PITCH / 2):
        m = m.cut(cq.Workplane('YZ').circle(SW_HOLE_D / 2).extrude(30).translate((x - 15, y + dy, FLOOR_TOP + 6)))
    m = m.cut(cylz(x, 87, FLOOR_TOP - 1, 20, WOOD_SCREW)).cut(cylz(x, 87, FLOOR_TOP + 10.3 - 1.5, 5, 7.0)).cut(csk_cone((x, 87, FLOOR_TOP + 10.3 - 1.5 + 0.01), (0, 0, -1)))   # flat-head seat
    return m


def reed_dummies():
    out = []
    for x in XC:
        rx = x + REED_DX
        out.append(cq.Workplane('XZ').circle(REED_D / 2).extrude(REED_L / 2, both=True).translate((rx, ROW_Y, REED_FLOOR_Z + REED_D / 2)))
    return out


def magnet_dummy(x):
    return cylz(x + REED_DX, ROW_Y + MAG_DY, Z_TRAY1, MAG_T, MAG_D)


def mcp_dummy():
    (a, b), (c, d) = MCP['x'], MCP['y']
    zb = Z_TRAY0 - 12.0
    return box(a + 0.3, b - 0.3, c + 0.1, d - 0.1, zb, zb + MCP['pcb']).union(box(a + 10, b - 10, c + 6, d - 6, zb + MCP['pcb'], zb + MCP['pcb'] + 2.5))


def reed_coupon():
    """172: a 44 x 60 piece of tray (plate, shim pads, boss, groove, holes) + a 44 x 44 bin-floor disc with the magnet boss."""
    rx, y0 = 0.0, 0.0
    yl = REED_L / 2 + REED_LEAD
    t = box(-22, 22, -30, 30, Z_TRAY0, Z_PLATE1).union(box(-22, 22, -30, -24, Z_PLATE1, Z_TRAY1)).union(box(-22, 22, 24, 30, Z_PLATE1, Z_TRAY1))
    t = t.union(box(-3.5, 3.5, -yl - 3, yl + 3, Z_TRAY0 - 2.0, Z_TRAY0 + 0.01))
    t = t.cut(box(-REED_GROOVE_W / 2, REED_GROOVE_W / 2, -REED_L / 2 - 0.5, REED_L / 2 + 0.5, REED_FLOOR_Z, Z_TRAY1 + 1))
    t = t.cut(box(-0.75, 0.75, -yl, yl, REED_FLOOR_Z + 0.2, Z_TRAY1 + 1))
    for yy in (-yl, yl): t = t.cut(cylz(0, yy, Z_TRAY0 - 3, 10, 2.5))
    f = box(-22, 22, -22, 22, 0, BIN_FLOOR).union(cylz(0, MAG_DY, 0, MAG_T + 0.6, MAG_D + 2.4)).cut(cylz(0, MAG_DY, -0.01, MAG_T + 0.01, MAG_HOLE))
    return t.translate((0, 0, -Z_TRAY0 + 2.0)), f


def switch_dummy():
    x, y = CLOSED_SW_X, 70.0
    return box(x - SW_W / 2, x + SW_W / 2, y - SW_L / 2, y + SW_L / 2, FLOOR_TOP + 0.8, FLOOR_TOP + 0.8 + SW_H)


# ---------------- build ----------------
def drawer(side):
    rail_x = R.RAILS_X[side]
    letter = 'F' if side == 'front' else 'B'
    moving, fixed, brg = rail_parts(rail_x)
    parts = []
    for n, s in moving: parts.append((n, s, 'moving'))
    for n, s in fixed: parts.append((n, s, 'fixed'))
    for k, s in enumerate(brg): parts.append((f'625ZZ_{k+1}', s, 'fixed'))
    tiles = [tray_tile(i, rail_x) for i in range(4)]
    for i, t in enumerate(tiles): parts.append((f'166_tray_tile_{i+1}', t, 'moving'))
    faces = [face_piece(i, letter, rail_x) for i in range(3)]
    pn = '167' if side == 'front' else '168'
    for i, (f, ink) in enumerate(faces):
        parts.append((f'{pn}_face_{letter}{i+1}', f, 'moving')); parts.append((f'{pn}_face_{letter}{i+1}_ink', ink, 'moving'))
    b0 = bin_part()
    for k, x in enumerate(XC): parts.append((f'169_bin_{k+1}', b0.translate((x, ROW_Y, Z_TRAY1)), 'moving'))
    for i in range(4): parts.append((f'170_bar_{i+1}', bar_piece(i), 'moving'))
    parts.append(('171_closed_switch_mount', closed_switch_mount(), 'fixed'))
    parts.append(('KW11_closed', switch_dummy(), 'fixed'))
    for k, r in enumerate(reed_dummies()): parts.append((f'REED_{k+1}', r, 'moving'))
    for k, x in enumerate(XC): parts.append((f'MAGNET_{k+1}', magnet_dummy(x), 'moving'))
    parts.append(('MCP23017_dummy', mcp_dummy(), 'moving'))
    if side == 'back':
        parts = [(n, rot180(s), g) for n, s, g in parts]
    return parts, tiles, faces, b0


def color(lab):
    for k, c in (('_ink', 'ink'), ('REED', 'brg'), ('MAGNET', 'brg'), ('MCP', 'sw'), ('160', 'rail'), ('162', 'station'), ('163', 'station'), ('164', 'station'), ('625', 'brg'),
                 ('166', 'tray'), ('167', 'face_F'), ('168', 'face_B'), ('169', 'bin'), ('170', 'bar')):
        if k in lab: return COL[c]
    return COL['sw']


def main():
    world = HERE / 'world'; prn = HERE / 'print'
    allp = {}; extra = {}
    for side in ('front', 'back'):
        parts, tiles, faces, b0 = drawer(side)
        allp[side] = parts; extra[side] = (tiles, faces, b0)
    asm = cq.Assembly(name='drawer_module')
    for side in allp:
        for lab, s, g in allp[side]:
            export(s, world / f'{side}_{lab}.step'); asm.add(s, name=f'{side}_{lab}', color=cq.Color(*color(lab)))
    asm.save(str(world / 'drawer_assembly.step'))
    printable = []
    det = R.ROLLERS_Y[-1] - R.RAIL_Y0_WORLD - 6.0
    base = R.rail(insert_ys=RAIL_INSERTS + (FACE_RAIL_INSERT,), detent_y=det)
    printable += [('160_rail_R', base, 'rail_R', 2, 'PETG', 'closed web down'), ('161_rail_L', R.mirror_x(base), 'rail_L', 2, 'PETG', 'closed web down')]
    stF = R.station(R.ROLLERS_Y, slotted_index=0)[0]
    printable += [('162_station_R', stF, None, 2, 'PETG', 'foot down'), ('162_station_L', R.mirror_x(stF), None, 2, 'PETG', 'foot down'),
                  ('164_guide_R', R.guide_block((134.0, 162.0))[0], None, 2, 'PETG', 'foot down')]
    for side, pn, letter in (('front', '167', 'F'), ('back', '168', 'B')):
        tiles, faces, b0 = extra[side]
        for i, t in enumerate(tiles): printable.append((f'166_tray_tile_{side}_{i+1}', t, 'flip', 1, 'PLA', 'plate top down, ribs up'))
        for i, (f, ink) in enumerate(faces):
            printable.append((f'{pn}_face_{letter}{i+1}', f, ('face', f), 1, 'PLA red', 'outer face down'))
            printable.append((f'{pn}_face_{letter}{i+1}_ink', ink, ('face', f), 1, 'PLA black (AMS, same plate)', 'with its face'))
    printable += [('169_bin', extra['front'][2], None, 16, 'PLA', 'floor down')]
    for i in range(4): printable.append((f'170_bar_{i+1}', bar_piece(i), None, 2, 'PLA', 'flat'))
    printable.append(('171_closed_switch_mount', closed_switch_mount(), None, 2, 'PLA', 'foot down'))
    ct, cf = reed_coupon()
    printable.append(('172_reed_coupon_tray', ct, 'flip', 1, 'PLA', 'plate top down (test first)'))
    printable.append(('172_reed_coupon_floor', cf, None, 1, 'PLA', 'floor down, magnet pocket on the bed'))
    plist = []
    for name, shp, how, qty, mat, face in printable:
        if how in ('rail_R', 'rail_L'):
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (0, 1, 0), -90 if how == 'rail_R' else 90), diag=False)
        elif how == 'flip':
            bedp, diag = print_pose(shp, flip=True)
        elif isinstance(how, tuple):
            w = shp.rotate((0, 0, 0), (1, 0, 0), -90); bb = bbox(how[1].rotate((0, 0, 0), (1, 0, 0), -90))
            bedp = w.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2])); diag = False
        else:
            bedp, diag = print_pose(shp)
        export(bedp, prn / f'{name}_PRINT_{qty}.stl')
        g = grams(shp, density=1.27 if 'PETG' in mat else 1.24)
        plist.append({'label': name, 'part_no': name[:3], 'qty': qty, 'material': mat, 'bed_face': face, **bed_fit(bedp), 'diagonal_on_bed': diag,
                      'est_grams_each': g, 'est_hours_each': hours(g)})
    bought = [
        {'item': '625ZZ bearing', 'qty': 16, 'use': '6 roller + 2 guide per drawer'},
        {'item': 'M5 x 20 screw + nyloc', 'qty': 12, 'use': 'station roller axles (3 per station); head outside, nyloc in the trap; tip ends 0.5 short of the rail slot floor, so NOT longer than 20'},
        {'item': 'M5 x 16 screw', 'qty': 4, 'use': 'guide roller axles'},
        {'item': '#6 x 3/4 wood screw', 'qty': 2 * (8 + 2 + 1), 'use': 'stations, guides, switch mounts into the plywood'},
        {'item': 'M3 heat-set insert', 'qty': 4 * 5, 'use': 'rail tops'},
        {'item': 'M3 x 10 screw', 'qty': 2 * 8 + 4, 'use': 'tray to rails, face feet to rail fronts'},
        {'item': 'M3 x 12 screw + nut', 'qty': 2 * 6, 'use': 'tray laps'},
        {'item': 'M3 x 16 screw', 'qty': 4, 'use': 'rear roller preload jacks'},
        {'item': 'KW11-3Z', 'qty': 2, 'use': 'drawer closed'}, {'item': 'M2 x 12 screw + nut', 'qty': 4, 'use': 'switches'},
        {'item': 'reed switch N/O, glass 2 x 14 mm', 'qty': 16 + 2, 'use': 'one per bin (+2 spares, glass breaks)'},
        {'item': 'neodymium magnet 6 x 2 mm disc', 'qty': 16 + 2, 'use': 'one per bin floor (+2 for the coupon)'},
        {'item': 'MCP23017 I2C module (~40 x 25)', 'qty': 2, 'use': 'one per drawer, under tray tile 2'},
        {'item': '4-core flexible cable (3V3, GND, SDA, SCL)', 'qty': '2 x 1 m', 'use': 'drawer to deck, service loop for 150 travel'},
        {'item': '26-28 AWG hookup wire', 'qty': '~6 m', 'use': 'reeds to the MCP23017'},
    ]
    tot = sum(p['est_grams_each'] * p['qty'] for p in plist)
    (HERE / 'parts.json').write_text(json.dumps({'module': 'D', 'interface': IF['version'], 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(tot), 'est_total_hours': round(tot / 45.0)}, indent=1))
    res = checks(allp, plist); stills(allp)
    return res


def _ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def clash(lst, skip=lambda a, b: False):
    hits = []; bbs = [(n, s, bbox(s)) for n, s in lst]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            if not _ov(bbs[i][2], bbs[j][2]) or skip(bbs[i][0], bbs[j][0]): continue
            v = bbs[i][1].intersect(bbs[j][1]); vol = v.val().Volume() if v.vals() else 0
            if vol > 0.5: hits.append([bbs[i][0], bbs[j][0], round(vol, 1), bbox(v)])
    return hits


def checks(allp, plist):
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    zc = {}
    for side in allp:
        z = Z[side]; fz = z['face']
        for lab, s, g in allp[side]:
            if lab.startswith(('625', 'KW11', 'REED', 'MAGNET', 'MCP')) or lab.endswith('_ink'): continue
            b = bbox(s)
            def inside(zz):
                return zz['x'][0] - .01 <= b[0] and b[3] <= zz['x'][1] + .01 and zz['y'][0] - .01 <= b[1] and b[4] <= zz['y'][1] + .01 and zz['z'][0] - .01 <= b[2] and b[5] <= zz['z'][1] + .01
            if inside(z): zc[f'{side}_{lab}'] = 'in D zone'
            elif lab.startswith(('167', '168')) and inside({'x': fz['x'], 'y': [min(z['y'][0], fz['y'][0]), max(z['y'][1], fz['y'][1])], 'z': [min(fz['z'][0], z['z'][0]), max(fz['z'][1], z['z'][1])]}): zc[f'{side}_{lab}'] = 'D zone + face zone'
            elif lab.startswith('160') and z['x'][0] - .01 <= b[0] and b[3] <= z['x'][1] + .01 and 12 - .01 <= b[2] and b[5] <= 38.01 and (b[1] >= -40.01 if side == 'front' else b[4] <= 40.01): zc[f'{side}_{lab}'] = 'D zone + rail strip (allowed)'
            else: zc[f'{side}_{lab}'] = f'OUTSIDE {b}'
    res['zones'] = zc
    def state(fo, bo):
        out = []
        for side, op in (('front', fo), ('back', bo)):
            dy = TRAVEL if side == 'front' else -TRAVEL
            for lab, s, g in allp[side]:
                if lab.endswith('_ink'): continue
                out.append((f'{side}_{lab}', s.translate((0, dy, 0)) if (op and g == 'moving') else s))
        return out
    def skip(a, b):
        pair = (a, b)
        if any('KW11' in u for u in pair) and any('166_tray' in u for u in pair): return True
        if any('MAGNET' in u for u in pair) and any('169_bin' in u for u in pair): return True   # press fit (-0.02/side)
        return False
    res['clash_both_closed'] = clash(state(False, False), skip)
    res['clash_front_open'] = clash(state(True, False), skip); res['clash_back_open'] = clash(state(False, True), skip); res['clash_both_open'] = clash(state(True, True), skip)
    fb = [bbox(s) for lab, s, g in allp['front'] if lab.startswith('169_bin')]
    res['bin_top_z'] = round(max(b[5] for b in fb), 2); res['bin_top_ok'] = res['bin_top_z'] <= B['z'][1] + 1e-6
    res['front_open_bin_rear_y'] = round(min(b[1] for b in fb) + TRAVEL, 1)
    res['open_bins_clear_skin'] = res['front_open_bin_rear_y'] > 180.0
    res['keyed'] = {'front_rails_x': R.RAILS_X['front'], 'back_rails_x': R.RAILS_X['back']}
    res['runner_sweep'] = json.loads((HERE / 'runner_test' / 'runner_test_parts.json').read_text())['sweep_check_right_rail_mm']
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(allp):
    ply = box(-360, 360, -180, 180, 0, 12)
    def items(fo=False, bo=False, face_op=1.0, only=None):
        out = [(ply, (0.85, 0.75, 0.55), 0.4)]
        for side, op in (('front', fo), ('back', bo)):
            dy = TRAVEL if side == 'front' else -TRAVEL
            for lab, s, g in allp[side]:
                if only and not lab.startswith(only): continue
                s2 = s.translate((0, dy, 0)) if (op and g == 'moving') else s
                out.append((s2, color(lab), face_op if lab.startswith(('167', '168')) else 1.0))
        return out
    render(items(), HERE / 'still_1_closed_front.png', cam=(500, 1100, 480), focal=(0, 0, 70), title='V14 drawers 5.1 closed: overlay face F1-F8 (x +-330)')
    render(items(fo=True), HERE / 'still_2_front_open.png', cam=(800, 950, 520), focal=(0, 120, 50), title='Front drawer out 150: bins clear the skin, retaining bar on the inner rims')
    render(items(bo=True, face_op=0.3), HERE / 'still_3_back_open.png', cam=(-650, -1000, 480), focal=(0, -120, 50), title='Back drawer out 150: B1-B8 from the back')
    render(items(only=('160', '162', '164', '625', '171', 'KW11')), HERE / 'still_4_rails_top.png', cam=(0, 0, 1200), focal=(0, 0, 0), up=(0, 1, 0), ortho=230,
           title='Rails and stations on the plywood (front at top): front x +-200, back x +-120')


if __name__ == '__main__':
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ('zones', 'bed_fit', 'runner_sweep')}, indent=1))
    print(sorted(set(r['zones'].values()))); print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
