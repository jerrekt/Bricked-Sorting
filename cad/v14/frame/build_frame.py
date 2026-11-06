"""V14 module F: frame and shell (CadQuery 2.8), interface v14-interface-4.1 (frozen).

Ribbed printed panels: 6 mm skin on the outside, 14 mm of ribs inward (perimeter rib 8 thick,
internal ribs 3 thick on a ~60 grid). Panels bolt to each other through their perimeter ribs
(M3 x 14 into inserts, every ~100 mm, screwed from inside: nothing shows on the front), to the
four 50 x 50 corner columns, to the floor (extra insert ring under the walls) and to the roof.
Floor: 4 mm skin on 4 mm underside ribs, M3 insert grid on top. Deck: skin 384..390 on ribs
370..384, sits on ledge ribs in the walls at z 356..370. Spine: box beam y +-66, z 8..184 with
the 24 x 26 rail tunnels at x +-200 / +-300. Roof: skin 714..720, ribs 700..714, hopper hole
r 100 at (-260, 0), hopper inserts at r 108 (180/240/300 deg), two studs (left open ring, right
capped). Machine coordinates (right-handed: +X is the front viewer's left, +Y front, +Z up).
Run: python3 build_frame.py [--quick]   (--quick skips the drawer/deck clash sweep)
"""
import json, math, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f_common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, print_pose, bed_fit, export, bbox, grams, render

E = IF['envelope']; W = IF['walls']
SKIN, RIBS = 1.7, W['ribs_inward']                         # rev 3: 1.7 outer skins (lever 1; interface 4.3 says 2.4), zone 20
DECK_SKIN = 1.3                                           # hidden deck face (lever 2)
NOZ06_FACTOR = 1.6                                        # g/h gain with a 0.6 nozzle on panels and spine
RIB_H = 10.0                                              # rib height used (<= RIBS)
FIT = 0.07                                                # sliding fit per side (vault runbook)
XO, YO = E['x'][1], E['y'][1]                             # 520, 260 outer
XI, YI = W['interior_clear']['x'][1], W['interior_clear']['y'][1]   # 500, 240 interior clear
FLOOR_T = IF['floor']['z'][1]                             # 8
DECK_Z0, DECK_Z1 = IF['deck']['z']                        # 370, 390
ROOF_Z0, ROOF_Z1 = IF['roof']['z']                        # 700, 720
STUD_Z1 = IF['bricks']['studs_z'][1]                      # 780
STUDS = IF['bricks']['stud_centers']; STUD_OD = IF['bricks']['stud_od']; STUD_ID = 290.0
COL = IF['corner_columns_keepout']                        # |x| 470..500, |y| 210..240
CX0, CY0 = COL['x_abs'][0], COL['y_abs'][0]               # 470, 210: column outer block x 470..520, y 210..260
OPEN_Z1 = IF['front_wall']['drawer_opening']['z'][1]      # 186
AP = IF['back_wall']['removable_access_panel']            # x -300..300, z 420..680
SP = IF['center_spine']
SPINE_Z1 = SP['z'][0] + 60.0                              # 60 mm spine (lever 3)
BEAM_PTS = IF['side_walls']['beam_mount_inserts']['points_yz']
FG = IF['floor']['grid_M3_inserts_top']; DG = IF['deck']['grid_M3_inserts_top']
DO = IF['deck']['openings']; RIB_FREE_R = IF['deck']['rib_free_radius_around_drop']
HOP = IF['roof']['hopper_opening']
HOP_INSERTS = [(HOP['center'][0] + 108 * math.cos(math.radians(a)), HOP['center'][1] + 108 * math.sin(math.radians(a))) for a in (180, 240, 300)]
PERIM, RIB_T, RIB_PITCH = 6.4, W.get('rib_thickness', 2.4), W.get('rib_spacing_about', 80)
INSERT_D = 4.1                                            # M3 generic insert, runbook: hole 4.0-4.2, verify with calipers
DECK_BAND = (368.0, 392.0)                                # solid band in the walls around the deck edge, inserts at z 380 facing in
SEAM_PITCH = 100.0
TUN_W, TUN_Z1 = 24.0, 34.0

RED = (0.72, 0.10, 0.10)
COLORS = {'floor': (0.45, 0.45, 0.48), 'deck': (0.55, 0.55, 0.60), 'spine': (0.35, 0.35, 0.40), 'col': (0.60, 0.12, 0.12),
          'wall': RED, 'roof': (0.78, 0.15, 0.15), 'stud': (0.80, 0.18, 0.18), 'panel': (0.55, 0.10, 0.10)}


def boxc(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(axis, c, d, h):
    a = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[axis]
    pl = cq.Plane(origin=(c[0] - a[0] * h / 2, c[1] - a[1] * h / 2, c[2] - a[2] * h / 2), xDir=(0, 1, 0) if axis == 'x' else (1, 0, 0), normal=a)
    return cq.Workplane(pl).circle(d / 2).extrude(h)


def tdrop(axis, c, d, h):
    """horizontal hole for printing: circle plus a 45 deg apex toward +z local (up when the part prints skin-down)."""
    a = {'x': (1, 0, 0), 'y': (0, 1, 0)}[axis]
    xd = (0, 1, 0) if axis == 'x' else (1, 0, 0)
    pl = cq.Plane(origin=(c[0] - a[0] * h / 2, c[1] - a[1] * h / 2, c[2]), xDir=xd, normal=a)
    r = d / 2
    pts = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in range(-45, 226, 15)]
    sy = 1 if axis == 'x' else -1          # plane local y is +z for axis x and -z for axis y
    pts = [(x, sy * y) for x, y in pts] + [(0, sy * r * math.sqrt(2))]
    return cq.Workplane(pl).polyline(pts).close().extrude(h)


def seam_points(a, b, pitch=SEAM_PITCH, margin=20.0):
    """global hole grid (odd multiples of pitch/2) clipped to [a+margin, b-margin], so both sides of any seam agree."""
    g = [(-1000 + pitch / 2) + k * pitch for k in range(int(2000 / pitch) + 1)]
    pts = [x for x in g if a + margin <= x <= b - margin]
    return pts if len(pts) >= 2 else [a + margin, b - margin]


# ---------------- generic ribbed panel ----------------
class Panel:
    """A ribbed panel in a local (u, v, w) frame: skin at w 0..SKIN, ribs at w SKIN..SKIN+RIBS, u0..u1 x v0..v1.
    `place` maps local (u, v, w) to world. Edges: 'u0','u1','v0','v1'. Each edge gets either inserts
    (axis normal to the edge, in the perimeter rib) or clearance holes, per `edge_mode`."""

    def __init__(self, name, u0, u1, v0, v1, place, edge_mode, solid_fill=None, openings=(), zone_holes=(), skin_v0=None, rib_slot=None, skin=None):
        self.name = name; self.u0, self.u1, self.v0, self.v1 = u0, u1, v0, v1
        self.skin = SKIN if skin is None else skin
        self.skin_v0 = skin_v0; self.rib_slot = rib_slot
        self.place = place; self.edge_mode = edge_mode; self.solid_fill = solid_fill or []
        self.openings = list(openings); self.zone_holes = list(zone_holes)

    def local(self):
        u0, u1, v0, v1 = self.u0, self.u1, self.v0, self.v1
        SK = self.skin
        T = SK + RIB_H
        p = boxc(u0, u1, v0, v1, 0, SK)
        # perimeter rib
        p = p.union(boxc(u0, u1, v0, v1, SK - 0.01, T).cut(boxc(u0 + PERIM, u1 - PERIM, v0 + PERIM, v1 - PERIM, SK - 1, T + 1)))
        # internal ribs
        nu = max(1, int(round((u1 - u0) / RIB_PITCH))); nv = max(1, int(round((v1 - v0) / RIB_PITCH)))
        for k in range(1, nu):
            u = u0 + k * (u1 - u0) / nu
            p = p.union(boxc(u - RIB_T / 2, u + RIB_T / 2, v0, v1, SK - 0.01, T))
        for k in range(1, nv):
            v = v0 + k * (v1 - v0) / nv
            p = p.union(boxc(u0, u1, v - RIB_T / 2, v + RIB_T / 2, SK - 0.01, T))
        for (a, b, c, d) in self.solid_fill:
            a, b, c, d = max(a, u0), min(b, u1), max(c, v0), min(d, v1)
            if b > a and d > c: p = p.union(boxc(a, b, c, d, SK - 0.01, T))
        for op in self.openings:
            p = p.cut(op)
        # seam holes in the perimeter ribs, at w = SK + RIBS/2
        wm = SK + RIB_H / 2
        for edge, mode in self.edge_mode.items():
            if mode is None: continue
            if edge in ('u0', 'u1'):
                pts = seam_points(v0, v1); ue = u0 if edge == 'u0' else u1
                for v in pts:
                    if mode == 'insert':
                        p = p.cut(tdrop('x', (ue + (INSERT_DEPTH / 2 if edge == 'u0' else -INSERT_DEPTH / 2), v, wm), INSERT_D, INSERT_DEPTH))
                    else:
                        p = p.cut(tdrop('x', (ue + (15 if edge == 'u0' else -15), v, wm), M3_CLR, 32))
            else:
                pts = seam_points(u0, u1); ve = v0 if edge == 'v0' else v1
                for u in pts:
                    if mode == 'insert':
                        p = p.cut(tdrop('y', (u, ve + (INSERT_DEPTH / 2 if edge == 'v0' else -INSERT_DEPTH / 2), wm), INSERT_D, INSERT_DEPTH))
                    else:
                        p = p.cut(tdrop('y', (u, ve + (15 if edge == 'v0' else -15), wm), M3_CLR, 32))
        for (axis, c, d, h) in self.zone_holes:   # extra holes in local coords (in-plane holes get teardrops)
            p = p.cut(tdrop(axis, c, d, h) if axis in ('x', 'y') else cyl(axis, c, d, h))
        if self.skin_v0 is not None:              # skin continues below the rib zone (deck slot at the bottom edge)
            p = p.union(boxc(u0, u1, self.skin_v0, v0 + 0.01, 0, SK))
        if self.rib_slot is not None:             # horizontal slot through the ribs (the deck passes through a side wall)
            p = p.cut(boxc(u0 - 1, u1 + 1, self.rib_slot[0], self.rib_slot[1], SK - 0.3, T + 1))
        return p

    def world(self):
        return self.place(self.local())


# placements: local (u, v, w) -> world
def place_side(sign):      # side wall, skin at x = sign*520, u = y, v = z, w inward (-sign x)
    def f(w):
        # local box has u along X, v along Y, w along Z; map: X->Y, Y->Z, Z->(-sign)X
        w = w.rotate((0, 0, 0), (1, 0, 0), 90)       # (u, v, w) -> (u, -w, v)
        w = w.rotate((0, 0, 0), (0, 0, 1), 90 if sign > 0 else -90)   # -> (w*sign.., u ..)
        return w.translate((sign * XO, 0, 0)).mirror('YZ', basePointVector=(sign * XO, 0, 0))
    return f


def place_fb(sign):        # front (+1) / back (-1) wall, skin at y = sign*260, u = x, v = z, w inward
    def f(w):
        w = w.rotate((0, 0, 0), (1, 0, 0), 90 if sign < 0 else -90)   # (u,v,w) -> (u, ∓w, ±v)
        if sign > 0:
            w = w.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 0, 1), 180)
        return w.translate((0, sign * YO, 0)).mirror('XZ', basePointVector=(0, sign * YO, 0))
    return f


def place_top(z_out, sign=+1):   # roof (skin up at z_out, ribs below): u = x, v = y, w downward
    def f(w):
        w = w.rotate((0, 0, 0), (1, 0, 0), 180)       # (u, v, w) -> (u, -v, -w)
        w = w.mirror('XZ')                            # -> (u, v, -w)
        return w.translate((0, 0, z_out))
    return f


def place_deck_like(z_bottom):   # skin on top at z_bottom+? no: deck skin 384..390 ribs below -> same as roof with z_out = 390
    return place_top(z_bottom)


def check_place():
    """sanity: probe a marker through each placement."""
    out = {}
    m = boxc(0, 10, 0, 20, 0, 5)
    for n, f in (('side+', place_side(1)), ('side-', place_side(-1)), ('front', place_fb(1)), ('back', place_fb(-1)), ('top', place_top(720))):
        out[n] = bbox(f(m))
    return out


# ---------------- floor ----------------
FX = [-XO, -312.0, -104.0, 104.0, 312.0, XO]
FY = [-YO, -87.0, 87.0, YO]
FLOOR_RING = [(x, y) for x in (-507.0, 507.0) for y in [-180.0, -100.0, -20.0, 60.0, 140.0]]   # side walls stand on the floor; front/back walls hang from the columns
COL_FLOOR = [(sx * 495, sy * 235) for sx in (-1, 1) for sy in (-1, 1)]


PADS = []   # solid 8 mm pads (x0, x1, y0, y1) under the drawer roller stations, the closed switches and the columns
for rx in (300.0, 200.0):
    for sx in (-1, 1):
        for sy in (-1, 1):
            a, b = sorted((sx * (rx + 6), sx * (rx + 94)))       # station feet reach ~90 outward from the rail
            PADS.append((a, b, *sorted((sy * 150.0, sy * 240.0))))
for sx in (-1, 1):
    PADS.append((sx * 400 - 16, sx * 400 + 16, *sorted((sx * 68.0, sx * 112.0))))   # 170 switch mounts (back one mirrored)
for sx in (-1, 1):
    for sy in (-1, 1):
        PADS.append((*sorted((sx * CX0, sx * XO)), *sorted((sy * CY0, sy * YO))))


def floor_tile(i, j):
    """open grid (lever 4, BJ's pick): 2.4 x 8 ribs on the 40 insert grid, 9 mm bosses at every grid point, solid 8 mm pads
    where something stands on the floor (roller stations, switch mounts, columns), 6 mm perimeter rib with half-laps."""
    x0, x1, y0, y1 = FX[i], FX[i + 1], FY[j], FY[j + 1]
    gx = [FG['x0'] + FG['pitch'] * k for k in range(FG['nx'])]; gy = [FG['y0'] + FG['pitch'] * k for k in range(FG['ny'])]
    t = boxc(x0, x1, y0, y1, 0, FLOOR_T).cut(boxc(x0 + 6, x1 - 6, y0 + 6, y1 - 6, -1, FLOOR_T + 1))
    for x in gx:
        if x0 < x < x1: t = t.union(boxc(x - RIB_T / 2, x + RIB_T / 2, y0, y1, 0, FLOOR_T))
    for y in gy:
        if y0 < y < y1: t = t.union(boxc(x0, x1, y - RIB_T / 2, y + RIB_T / 2, 0, FLOOR_T))
    for (a, b, c, d) in PADS:
        a, b, c, d = max(a, x0), min(b, x1), max(c, y0), min(d, y1)
        if b > a and d > c: t = t.union(boxc(a, b, c, d, 0, FLOOR_T))
    pts = [(x, y) for x in gx for y in gy if not (abs(x) >= CX0 and abs(y) >= CY0)] + FLOOR_RING + COL_FLOOR
    for (x, y) in pts:
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01:
            if x0 + 5 < x < x1 - 5 and y0 + 5 < y < y1 - 5:
                t = t.union(cyl('z', (x, y, FLOOR_T / 2), 9, FLOOR_T))
            t = t.cut(cyl('z', (x, y, FLOOR_T - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    # half-laps on the perimeter rib: tongue (lower half) on +x / +y, socket on -x / -y, FIT per side; M3 + nut
    H2 = FLOOR_T / 2
    if i < 4: t = t.union(boxc(x1, x1 + 6, y0 + 25, y1 - 25, 0, H2))
    if i > 0: t = t.cut(boxc(x0 - 1, x0 + 6 + FIT, y0 + 25 - FIT, y1 - 25 + FIT, -1, H2 + FIT))
    if j < 2: t = t.union(boxc(x0 + 10, x1 - 10, y1, y1 + 6, 0, H2))
    if j > 0: t = t.cut(boxc(x0 + 10 - FIT, x1 - 10 + FIT, y0 - 1, y0 + 6 + FIT, -1, H2 + FIT))
    for xs in ([x1 + 3] if i < 4 else []) + ([x0 + 3] if i > 0 else []):
        for y in seam_points(y0, y1, 120, 40): t = t.cut(cyl('z', (xs, y, 4), M3_CLR, 12))
    for ys in ([y1 + 3] if j < 2 else []) + ([y0 + 3] if j > 0 else []):
        for x in seam_points(x0, x1, 120, 40): t = t.cut(cyl('z', (x, ys, 4), M3_CLR, 12))
    return t


# ---------------- deck ----------------
DX = [-XI, -310.0, -110.0, 90.0, 270.0, XI]                     # +-500: the deck stays inside the walls (4.3)
DY = [-YI, -80.0, 80.0, YI]                                     # +-240
DECK_LEDGE_PTS = [(x, y) for y in (-247.0, 247.0) for x in [-440 + 80 * k for k in range(12)]] + \
                 [(x, y) for x in (-507.0, 507.0) for y in [-160.0, -80.0, 0.0, 80.0, 160.0]]


def deck_tile(i, j):
    x0, x1, y0, y1 = DX[i], DX[i + 1], DY[j], DY[j + 1]
    gx = [DG['x0'] + DG['pitch'] * k for k in range(DG['nx'])]; gy = [DG['y0'] + DG['pitch'] * k for k in range(DG['ny'])]
    drop = DO['drop_hole']; dc = drop['center']
    pan = Panel(f'deck_{i}{j}', x0, x1, y0, y1, place_top(DECK_Z1), {}, skin=DECK_SKIN)
    t = pan.local()
    # local w: 0..6 skin (world 384..390 after flip), ribs 6..20 (world 370..384)
    # openings (local z 0..20 = world 390 down to 370): drop hole + rib-free ring, cable slots
    t = t.cut(cyl('z', (dc[0], dc[1], 10), 2 * drop['r'], 30))
    t = t.cut(cyl('z', (dc[0], dc[1], DECK_SKIN + RIBS / 2 + 0.5), 2 * RIB_FREE_R, RIBS + 1).cut(cyl('z', (dc[0], dc[1], 10), 2 * drop['r'] + 2 * 4, 30)))
    for sl in (DO['cable_slot_L'], DO['cable_slot_R']):
        t = t.cut(boxc(sl['x'][0], sl['x'][1], sl['y'][0], sl['y'][1], -1, 30))

    # insert bosses on the grid (skip within 10 of an opening)
    for x in gx:
        for y in gy:
            if not (x0 + 5 < x < x1 - 5 and y0 + 5 < y < y1 - 5): continue
            if math.hypot(x - dc[0], y - dc[1]) < drop['r'] + DG['skip_within_of_openings']: continue
            if any(sl['x'][0] - 10 < x < sl['x'][1] + 10 and sl['y'][0] - 10 < y < sl['y'][1] + 10 for sl in (DO['cable_slot_L'], DO['cable_slot_R'])): continue
            t = t.union(cyl('z', (x, y, 4), 9, 8)).cut(cyl('z', (x, y, INSERT_DEPTH / 2 - 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    # ledge bolts (down into wall ledge inserts) and spine-free; seams: half-laps in the perimeter ribs with M3 + nut
    # the deck edge bolts sideways into inserts in the wall band (z 380): the outer perimeter rib is the full zone deep
    for (edge_on, bx) in ((i == 0, boxc(x0, x0 + 6, y0, y1, DECK_SKIN - 0.01, DECK_SKIN + RIBS)), (i == 4, boxc(x1 - 6, x1, y0, y1, DECK_SKIN - 0.01, DECK_SKIN + RIBS)),
                          (j == 0, boxc(x0, x1, y0, y0 + 6, DECK_SKIN - 0.01, DECK_SKIN + RIBS)), (j == 2, boxc(x0, x1, y1 - 6, y1, DECK_SKIN - 0.01, DECK_SKIN + RIBS))):
        if edge_on: t = t.union(bx)
    wz = DECK_Z1 - 380.0
    if i == 0:
        for y in seam_points(-CY0, CY0):
            if y0 + 2 < y < y1 - 2: t = t.cut(cyl('x', (x0 + 15, y, wz), M3_CLR, 32))
    if i == 4:
        for y in seam_points(-CY0, CY0):
            if y0 + 2 < y < y1 - 2: t = t.cut(cyl('x', (x1 - 15, y, wz), M3_CLR, 32))
    if j == 0:
        for x in seam_points(-CX0, CX0):
            if x0 + 2 < x < x1 - 2: t = t.cut(cyl('y', (x, y0 + 15, wz), M3_CLR, 32))
    if j == 2:
        for x in seam_points(-CX0, CX0):
            if x0 + 2 < x < x1 - 2: t = t.cut(cyl('y', (x, y1 - 15, wz), M3_CLR, 32))
    for sx in (-1, 1):   # corner notches for the columns
        for sy in (-1, 1):
            t = t.cut(boxc(*sorted((sx * (CX0 - 0.3), sx * 600)), *sorted((sy * (CY0 - 0.3), sy * 600)), -1, 30))
    t = t.cut(boxc(-600, 600, -600, 600, DECK_SKIN + RIBS + 0.001, 40))
    for edge, (a, b, fixed) in {'u0': (y0, y1, x0), 'u1': (y0, y1, x1), 'v0': (x0, x1, y0), 'v1': (x0, x1, y1)}.items():
        inner = (edge in ('u0', 'u1') and 0 < i < 5 or edge in ('v0', 'v1') and 0 < j < 3)
        if edge == 'u0' and i == 0 or edge == 'u1' and i == 4 or edge == 'v0' and j == 0 or edge == 'v1' and j == 2: continue
        for s in seam_points(a, b):
            if edge in ('u0', 'u1'):
                t = t.cut(cyl('x', (fixed, s, DECK_SKIN + RIBS / 2), M3_CLR, 2 * PERIM + 2))
            else:
                t = t.cut(cyl('y', (s, fixed, DECK_SKIN + RIBS / 2), M3_CLR, 2 * PERIM + 2))
    return place_top(DECK_Z1)(t)


# ---------------- roof ----------------
RX = [-XO, -380.0, -140.0, 100.0, 310.0, XO]
RY = [-YO, -110.0, 110.0, YO]
ROOF_RING_PTS = [(x, y) for y in (-250.0, 250.0) for x in [-440 + 80 * k for k in range(12)]] + \
                [(x, y) for x in (-510.0, 510.0) for y in [-160.0, -80.0, 0.0, 80.0, 160.0]] + [(sx * 495, sy * 235) for sx in (-1, 1) for sy in (-1, 1)]
STUD_BOLTS = [(c[0] + 150 * math.cos(math.radians(a)), c[1] + 150 * math.sin(math.radians(a))) for c in STUDS for a in (22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5)]


def roof_tile(i, j):
    x0, x1, y0, y1 = RX[i], RX[i + 1], RY[j], RY[j + 1]
    pan = Panel(f'roof_{i}{j}', x0, x1, y0, y1, place_top(ROOF_Z1), {})
    t = pan.local()
    hc = HOP['center']
    if math.hypot(max(abs(hc[0] - x0), abs(hc[0] - x1)), 0) < 1e9 and (x0 - HOP['r'] - 8 < hc[0] < x1 + HOP['r'] + 8) and (y0 - HOP['r'] - 8 < hc[1] < y1 + HOP['r'] + 8):
        t = t.cut(cyl('z', (hc[0], hc[1], 10), 2 * HOP['r'], 30))
        # ring rib around the hole (8 wide) so the cut edge is stiff
        ring = cyl('z', (hc[0], hc[1], SKIN + RIB_H / 2), 2 * HOP['r'] + 16, RIB_H).cut(cyl('z', (hc[0], hc[1], 10), 2 * HOP['r'], 30)).intersect(boxc(x0, x1, y0, y1, 0, 30))
        if ring.vals() and ring.val().Volume() > 1: t = t.union(ring)
    for (x, y) in HOP_INSERTS:
        if x0 + 2 < x < x1 - 2 and y0 + 2 < y < y1 - 2:
            t = t.union(cyl('z', (x, y, SKIN + RIB_H / 2), 12, RIB_H)).cut(cyl('z', (x, y, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    for (x, y) in ROOF_RING_PTS + STUD_BOLTS:
        if x0 + 2 < x < x1 - 2 and y0 + 2 < y < y1 - 2:
            if (x, y) in STUD_BOLTS:   # stud screws come down from above into inserts in the roof skin boss
                t = t.union(cyl('z', (x, y, 4), 10, 8)).cut(cyl('z', (x, y, INSERT_DEPTH / 2 - 0.005), INSERT_D, INSERT_DEPTH + 0.01))
            else:                      # roof-to-wall: counterbored M3 down into the wall-top inserts
                t = t.cut(cyl('z', (x, y, 10), M3_CLR, 30)).cut(cyl('z', (x, y, CB_DEPTH / 2 - 0.01), CB_D, CB_DEPTH))
    for edge, (a, b, fixed) in {'u0': (y0, y1, x0), 'u1': (y0, y1, x1), 'v0': (x0, x1, y0), 'v1': (x0, x1, y1)}.items():
        if edge == 'u0' and i == 0 or edge == 'u1' and i == 4 or edge == 'v0' and j == 0 or edge == 'v1' and j == 2: continue
        for s in seam_points(a, b):
            if edge in ('u0', 'u1'):
                t = t.cut(cyl('x', (fixed, s, SKIN + RIB_H / 2), M3_CLR, 2 * PERIM + 2))
            else:
                t = t.cut(cyl('y', (s, fixed, SKIN + RIB_H / 2), M3_CLR, 2 * PERIM + 2))
    return place_top(ROOF_Z1)(t)


# ---------------- studs ----------------
def stud_quarter(c, k, capped):
    a0 = k * 90
    ring = cyl('z', (c[0], c[1], (ROOF_Z1 + STUD_Z1) / 2), STUD_OD, STUD_Z1 - ROOF_Z1).cut(cyl('z', (c[0], c[1], 750), STUD_ID, 100))
    if capped:
        ring = ring.union(cyl('z', (c[0], c[1], STUD_Z1 - 2), STUD_OD, 4))
    foot = cyl('z', (c[0], c[1], ROOF_Z1 + 2), STUD_OD + 2 * 0, 4).cut(cyl('z', (c[0], c[1], 750), STUD_ID - 22, 100))   # inner flange r 134..156
    ring = ring.union(foot)
    if capped:   # 45 deg brace under the flange so the capped quarters print cap-down without supports
        brace = cq.Workplane('XZ').polyline([(STUD_ID / 2 - 11, ROOF_Z1 + 4), (STUD_ID / 2 + 0.5, ROOF_Z1 + 4), (STUD_ID / 2 + 0.5, ROOF_Z1 + 15.5)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((c[0], c[1], 0))
        ring = ring.union(brace)
    for (x, y) in STUD_BOLTS:
        if math.hypot(x - c[0], y - c[1]) < 160:
            ring = ring.cut(cyl('z', (x, y, ROOF_Z1 + 4), M3_CLR, 12)).cut(cyl('z', (x, y, ROOF_Z1 + 6 - CB_DEPTH / 2), CB_D, CB_DEPTH))
    sector = cq.Workplane().polyline([(0, 0), (200 * math.cos(math.radians(a0)), 200 * math.sin(math.radians(a0))),
                                      (300 * math.cos(math.radians(a0 + 45)), 300 * math.sin(math.radians(a0 + 45))),
                                      (200 * math.cos(math.radians(a0 + 90)), 200 * math.sin(math.radians(a0 + 90)))]).close().extrude(200).translate((c[0], c[1], 700))
    q = ring.intersect(sector)
    # seam lugs on the inside of the ring (r 135..143) either side of each radial edge, M3 + nut tangentially across the seam
    for a in (a0 + 3.0, a0 + 90 - 3.0):
        x, y = c[0] + 139 * math.cos(math.radians(a)), c[1] + 139 * math.sin(math.radians(a))
        lug = boxc(-6, 6, -4, 4, ROOF_Z1 + 4, ROOF_Z1 + 22).rotate((0, 0, 0), (0, 0, 1), a + 90).translate((x, y, 0))
        lug = lug.cut(cq.Workplane(cq.Plane(origin=(x, y, ROOF_Z1 + 14), xDir=(0, 0, 1), normal=(-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))).circle(M3_CLR / 2).extrude(10, both=True))
        q = q.union(lug)
    return q


# ---------------- corner columns ----------------
CZ = [FLOOR_T, 255.0, 480.0, ROOF_Z0]


def column(sx, sy, k):
    x0, x1 = sorted((sx * CX0, sx * XO)); y0, y1 = sorted((sy * CY0, sy * YO))
    z0, z1 = CZ[k], CZ[k + 1]
    tw = 1.7
    c = boxc(x0, x1, y0, y1, z0, z1).cut(boxc(x0 + tw, x1 - tw, y0 + tw, y1 - tw, z0 - 1, z1 + 1))
    # insert bosses along the two inner faces (a 2.4 wall alone cannot hold an insert): 8 x 8 strips the full height at the hole lines
    c = c.union(boxc(*sorted((sx * (XO - SKIN - RIB_H / 2 - 4), sx * (XO - SKIN - RIB_H / 2 + 4))), *sorted((sy * CY0, sy * (CY0 + 8))), z0, z1))
    c = c.union(boxc(*sorted((sx * CX0, sx * (CX0 + 8))), *sorted((sy * (YO - SKIN - RIB_H / 2 - 4), sy * (YO - SKIN - RIB_H / 2 + 4))), z0, z1))
    # tenon up (+z) 10 mm, socket at the bottom
    cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
    if k < 2: c = c.union(boxc(cxm - 12, cxm + 12, cym - 12, cym + 12, z1, z1 + 10))
    if k > 0: c = c.cut(boxc(cxm - 12 - FIT, cxm + 12 + FIT, cym - 12 - FIT, cym + 12 + FIT, z0 - 1, z0 + 10 + FIT))
    # floor foot: inserts in the floor at (sx*495, sy*235) -> clearance from above through a 6 mm foot plate
    if k == 0:
        c = c.union(boxc(x0, x1, y0, y1, z0, z0 + 4)).cut(cyl('z', (sx * 495, sy * 235, z0 + 3), M3_CLR, 8)).cut(cyl('z', (sx * 495, sy * 235, z0 + 6 - CB_DEPTH / 2), CB_D, CB_DEPTH))
    if k == 2:   # roof bolts come down into an insert in the column top
        c = c.union(boxc(x0, x1, y0, y1, z1 - 7, z1)).cut(cyl('z', (sx * 495, sy * 235, z1 - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    # wall inserts: side-wall panels bolt in along Y (face y = sy*CY0), front/back panels along X (face x = sx*CX0)
    zs_side = sorted({z for r in range(3) for z in seam_points(SIDE_Z[r], SIDE_Z[r + 1])})
    zs_fb = sorted({z for r in range(3) for z in seam_points(FB_Z[r], FB_Z[r + 1])})
    for z in zs_side:
        if z0 + 3 < z < z1 - 3:
            c = c.cut(cyl('y', (sx * (XO - SKIN - RIB_H / 2), sy * CY0 - sy * INSERT_DEPTH / 2, z), INSERT_D, INSERT_DEPTH))
    for z in zs_fb:
        if z0 + 3 < z < z1 - 3:
            c = c.cut(cyl('x', (sx * CX0 - sx * INSERT_DEPTH / 2, sy * (YO - SKIN - RIB_H / 2), z), INSERT_D, INSERT_DEPTH))
    return c


# ---------------- walls ----------------
SIDE_Z = CZ                                   # rows 8..255, 255..480, 480..700
SIDE_Y = [-CY0, 0.0, CY0]                     # 2 columns of 210
FB_Z = [OPEN_Z1, DECK_Z0, 535.0, ROOF_Z0]     # rows 186..370, 370..535, 535..700
FB_X = [-CX0, -235.0, 0.0, 235.0, CX0]


def side_wall(sign, i, k):
    """side wall panel: u = y (world), v = z, skin at x = sign*520. Edge modes: insert on u1/v1, clearance on u0/v0;
    the outer edges bolt into the columns (clearance) and floor/roof (none, handled by the floor ring / roof holes)."""
    u0, u1, v0, v1 = SIDE_Y[i], SIDE_Y[i + 1], SIDE_Z[k], SIDE_Z[k + 1]
    modes = {'u0': 'clear' if i == 0 else 'clear', 'u1': 'clear' if i == 1 else 'insert', 'v0': None if k == 0 else 'clear', 'v1': None if k == 2 else 'insert'}
    fill = []; holes = []
    if k == 0:   # beam mount boss: solid rib zone y -30..30, z 180..270 + gusset ribs, inserts along X at the four points
        fill.append((-34.0, 34.0, 180.0, 270.0))
        for (y, z) in BEAM_PTS:
            # local u = sign*? : for +x wall, u = y ; for -x wall the rotation mirrors u -> -y
            uu = y if sign > 0 else -y
            holes.append(('z', (uu, z, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
        for g in (-60.0, 60.0):   # gusset ribs
            fill.append((g - 2, g + 2, 150.0, 300.0))
    slot = None
    if k == 1:   # deck band: solid rib zone z 368..392 with inserts facing inward at z 380 (the deck edge bolts in sideways)
        fill.append((u0, u1, DECK_BAND[0], DECK_BAND[1]))
        for y in seam_points(-CY0, CY0):
            uu = y if sign > 0 else -y
            if u0 + 4 < uu < u1 - 4:
                holes.append(('z', (uu, 380.0, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    if k == 0:   # floor ring bolts: clearance holes down through the bottom rib into the floor ring inserts
        for (x, y) in FLOOR_RING:
            if abs(x - sign * 507) < 0.1:
                uu = y if sign > 0 else -y
                if u0 + 4 < uu < u1 - 4:
                    holes.append(('y', (uu, v0 + 15, SKIN + RIB_H / 2), M3_CLR, 32))
    if k == 2:   # roof bolts: inserts in the top rib
        for (x, y) in ROOF_RING_PTS:
            if abs(x - sign * 510) < 0.1:
                uu = y if sign > 0 else -y
                if u0 + 4 < uu < u1 - 4:
                    holes.append(('y', (uu, v1 - INSERT_DEPTH / 2 + 0.005, SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    pan = Panel(f'side', u0, u1, v0, v1, place_side(sign), modes, fill, zone_holes=holes, rib_slot=slot)
    return pan.world()


def fb_wall(sign, i, k, access=None):
    """front (+1) / back (-1) wall panel: u = x (world for the back wall; mirrored for the front), v = z."""
    u0, u1, v0, v1 = FB_X[i], FB_X[i + 1], FB_Z[k], FB_Z[k + 1]
    modes = {'u0': 'clear', 'u1': 'clear' if i == 3 else 'insert', 'v0': None if k == 0 else 'clear', 'v1': None if k == 2 else 'insert'}
    fill = []; holes = []; openings = []
    if k == 0:   # lintel over the drawer opening
        fill.append((u0, u1, v0, v0 + 12))
    if k == 1:   # deck band with inward inserts at z 380
        fill.append((u0, u1, DECK_BAND[0], DECK_BAND[1]))
        for x in seam_points(-CX0, CX0):
            uu = x if sign < 0 else -x
            if u0 + 4 < uu < u1 - 4:
                holes.append(('z', (uu, 380.0, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    if k == 2:
        for (x, y) in ROOF_RING_PTS:
            if abs(y - sign * 250) < 0.1:
                uu = x if sign < 0 else -x
                if u0 + 4 < uu < u1 - 4:
                    holes.append(('y', (uu, v1 - INSERT_DEPTH / 2 + 0.005, SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    pan = Panel('fb', u0, u1, v0, v1, place_fb(sign), modes, fill, openings, zone_holes=holes)
    return pan.world()


# back wall above the deck: side pieces, strips and the removable access panel
BK_SIDE_X = [(-CX0, AP['x'][0]), (AP['x'][1], CX0)]       # x 300..470 each side
AP_X = [AP['x'][0], -100.0, 100.0, AP['x'][1]]
AP_Z = [AP['z'][0], AP['z'][1]]                 # 420..668: one row of 3 pieces, 200 x 248


def back_upper(i, k):
    """back wall |x| 300..470, rows 370..535, 535..700, u = x, v = z. The inner edge (toward the opening) gets inserts
    for the strips and the access panel."""
    (a, b) = BK_SIDE_X[i]; v0, v1 = FB_Z[k + 1], FB_Z[k + 2]
    u0, u1 = a, b
    modes = {'u0': 'clear' if i == 0 else 'insert', 'u1': 'insert' if i == 0 else 'clear', 'v0': 'clear', 'v1': None if k == 1 else 'insert'}
    holes = []; fill = []
    if k == 0:
        fill.append((u0, u1, DECK_BAND[0], DECK_BAND[1]))
        for x in seam_points(-CX0, CX0):
            if u0 + 4 < x < u1 - 4:
                holes.append(('z', (x, 380.0, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    if k == 1:
        for (x, y) in ROOF_RING_PTS:
            if abs(y + 250) < 0.1 and u0 + 4 < x < u1 - 4:
                holes.append(('y', (x, v1 - INSERT_DEPTH / 2 + 0.005, SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    # access panel bolts: inserts along x in the inner edge rib at z 450, 520, 580, 650
    inner = u1 if i == 0 else u0
    for z in (450.0, 520.0, 580.0, 650.0):
        if v0 < z < v1:
            holes.append(('x', (inner + (-INSERT_DEPTH / 2 if i == 0 else INSERT_DEPTH / 2), z, SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    pan = Panel('bk', u0, u1, v0, v1, place_fb(-1), modes, fill, zone_holes=holes)
    return pan.world()


def back_strip(i, which):
    """strips x -300..300 in three pieces: below (370..420) and above (680..700) the access panel."""
    u0, u1 = AP_X[i], AP_X[i + 1]
    if which == 'low':
        v0, v1 = DECK_Z0, AP['z'][0]; modes = {'u0': 'clear', 'u1': 'insert' if i < 2 else 'clear', 'v0': 'clear', 'v1': None}
    else:
        v0, v1 = AP['z'][1], ROOF_Z0; modes = {'u0': 'clear', 'u1': 'insert' if i < 2 else 'clear', 'v0': None, 'v1': None}
    holes = []
    if which == 'low':
        fill = [(u0, u1, DECK_BAND[0], DECK_BAND[1])]
        for x in seam_points(-CX0, CX0):
            if u0 + 4 < x < u1 - 4:
                holes.append(('z', (x, 380.0, SKIN + RIB_H - INSERT_DEPTH / 2 + 0.005), INSERT_D, INSERT_DEPTH + 0.01))
    else:
        fill = []
    # access panel bolts come up/down (axis z) into inserts in the strip edge rib
    for x in seam_points(u0, u1, 100, 35):
        ve = v1 if which == 'low' else v0
        holes.append(('y', (x, ve + (-INSERT_DEPTH / 2 if which == 'low' else INSERT_DEPTH / 2), SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    if which == 'high':
        for (x, y) in ROOF_RING_PTS:
            if abs(y + 250) < 0.1 and u0 + 4 < x < u1 - 4:
                holes.append(('y', (x, v1 - INSERT_DEPTH / 2 + 0.005, SKIN + RIB_H / 2), INSERT_D, INSERT_DEPTH + 0.01))
    return Panel('strip', u0, u1, v0, v1, place_fb(-1), modes, fill, zone_holes=holes).world()


def access_piece(i, k):
    """removable access panel 600 x 260 in 3 x 2 pieces; outer edges have counterbored clearance holes (screwed from
    the outside, it is the back), inner seams insert/clear like any panel."""
    u0, u1, v0, v1 = AP_X[i], AP_X[i + 1], AP_Z[k], AP_Z[k + 1]
    modes = {'u0': None if i == 0 else 'clear', 'u1': None if i == 2 else 'insert', 'v0': None, 'v1': None}
    holes = []
    if i == 0 or i == 2:
        for z in (450.0, 520.0, 580.0, 650.0):
            if v0 < z < v1:
                holes.append(('x', (u0 + 15 if i == 0 else u1 - 15, z, SKIN + RIB_H / 2), M3_CLR, 32))
    for x in seam_points(u0, u1, 100, 35):
        holes.append(('y', (x, v0 + 15, SKIN + RIB_H / 2), M3_CLR, 32))
        holes.append(('y', (x, v1 - 15, SKIN + RIB_H / 2), M3_CLR, 32))
    return Panel('ap', u0 + 0.3, u1 - 0.3, v0 + 0.3, v1 - 0.3, place_fb(-1), modes, [], zone_holes=holes).world()


# ---------------- spine ----------------
SX_ = [SP['x'][0], -233.0, 0.0, 233.0, SP['x'][1]]
TUNNELS = [-300.0, -200.0, 200.0, 300.0]


def spine_segment(i):
    """Inverted-U box beam, printed top-plate-down (no bridges): top plate 4 at z 180..184, side walls 4 at |y| 62..66,
    X ribs every 60 and a centre web, all vertical when printed. Feet inward at the bottom (y 50..62) carry the
    floor bolts at y +-60. Rail tunnels 24 x 26 (z 8..34) cut through the side walls and the feet."""
    x0, x1 = SX_[i], SX_[i + 1]; y0, y1 = SP['y']; z0, z1 = SP['z'][0], SPINE_Z1
    tp = 2.4
    s = boxc(x0, x1, y0, y1, z1 - tp, z1)
    for ys in (y0, y1 - tp): s = s.union(boxc(x0, x1, ys, ys + tp, z0, z1))
    for ys in (y0 + tp, y1 - tp - 12): s = s.union(boxc(x0, x1, ys, ys + 12, z0, z0 + 4))          # feet
    for x in [x0 + 40 + k * 80 for k in range(int((x1 - x0 - 80) // 80) + 1)]:
        s = s.union(boxc(x - 1.2, x + 1.2, y0, y1, z0, z1))
    for tx in TUNNELS:
        if x0 <= tx - TUN_W / 2 and tx + TUN_W / 2 <= x1:
            s = s.cut(boxc(tx - TUN_W / 2, tx + TUN_W / 2, y0 - 1, y1 + 1, z0 - 1, TUN_Z1))
    gx = [FG['x0'] + FG['pitch'] * k for k in range(FG['nx'])]
    for x in gx:
        if x0 + 10 < x < x1 - 10 and all(abs(x - tx) > TUN_W / 2 + 6 for tx in TUNNELS):
            for y in (-60.0, 60.0):
                s = s.cut(cyl('z', (x, y, z0 + 2), M3_CLR, 6)).cut(cyl('z', (x, y, z0 + 4 - CB_DEPTH / 2), CB_D, CB_DEPTH))
    # seams: tongue (top plate) on +x, socket on -x, FIT per side, 2 M3 + nut through the side walls
    if i < 3: s = s.union(boxc(x1, x1 + 12, y0 + tp, y1 - tp, z1 - tp, z1).cut(boxc(x1 - 1, x1 + 13, y0 + 10, y1 - 10, z1 - tp - 1, z1 + 1)))
    if i > 0: s = s.cut(boxc(x0 - 1, x0 + 12 + FIT, y0 + tp - FIT, y1 - tp + FIT, z1 - tp - FIT, z1 + 1))
    for xs in ([x1 + 6] if i < 3 else []) + ([x0 + 6] if i > 0 else []):
        s = s.cut(cyl('y', (xs, 0, z1 - 2), M3_CLR, 140))
    return s


# ---------------- build ----------------
def build():
    parts = []   # (label, shape, color)
    for i in range(5):
        for j in range(3):
            parts.append((f'100_floor_{i}{j}', floor_tile(i, j), COLORS['floor']))
    for i in range(4): parts.append((f'105_spine_{i+1}', spine_segment(i), COLORS['spine']))
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(3):
                parts.append((f'110_column_{"R" if sx > 0 else "L"}{"F" if sy > 0 else "B"}_{k+1}', column(sx, sy, k), COLORS['col']))
    for sign in (-1, 1):
        for i in range(2):
            for k in range(3):
                parts.append((f'115_side_{"R" if sign > 0 else "L"}_{i}{k}', side_wall(sign, i, k), COLORS['wall']))
    for i in range(4):
        for k in range(3):
            parts.append((f'120_front_{i}{k}', fb_wall(1, i, k), COLORS['wall']))
    for i in range(4): parts.append((f'125_back_low_{i}', fb_wall(-1, i, 0), COLORS['wall']))
    for i in range(2):
        for k in range(2): parts.append((f'126_back_side_{i}{k}', back_upper(i, k), COLORS['wall']))
    for i in range(3):
        parts.append((f'127_back_strip_low_{i}', back_strip(i, 'low'), COLORS['wall']))
        parts.append((f'127_back_strip_high_{i}', back_strip(i, 'high'), COLORS['wall']))
    for i in range(3): parts.append((f'128_access_{i}', access_piece(i, 0), COLORS['panel']))
    for i in range(5):
        for j in range(3): parts.append((f'130_deck_{i}{j}', deck_tile(i, j), COLORS['deck']))
    for i in range(5):
        for j in range(3): parts.append((f'135_roof_{i}{j}', roof_tile(i, j), COLORS['roof']))
    for ci, c in enumerate(STUDS):
        for k in range(4): parts.append((f'140_stud_{"L" if ci == 0 else "R"}_q{k+1}', stud_quarter(c, k, capped=(ci == 1)), COLORS['stud']))
    return parts


G_PER_H = 45.0   # from the runbook timing (left backplate half: ~125 g in 2 h 33 min on the day profile; wall-heavy parts a bit slower)


def grams_day(w, rho=1.24):
    """slicer-like estimate for BJ's day profile: every face gets a solid shell (walls 1.68, top 1.0, bottom 0.6 -> 1.5 mm
    averaged), the rest is 15 % infill. Thin skins (2.4) come out fully solid, as the slicer would print them."""
    sld = w.val(); V = sld.Volume(); A = sld.Area()
    solid = min(V, A * 1.5)
    return round((solid + (V - solid) * 0.15) / 1000 * rho, 1)


def bed_face(lab):
    return {'100': 'floor skin (top) down', '105': 'top plate down (inverted U)', '110': 'foot/plate down, tenon up', '115': 'outer skin down',
            '120': 'outer skin down', '125': 'outer skin down', '126': 'outer skin down', '127': 'outer skin down', '128': 'outer skin down',
            '130': 'deck skin (top) down', '135': 'roof skin (top) down', '140': 'flange down (open ring) / cap down (capped)'}[lab[:3]]


def _ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def vol(a, b):
    v = a.intersect(b)
    return v.val().Volume() if v.vals() else 0.0


def zone_boxes():
    D = IF['zones']['D_drawer']; S = IF['zones']['S_scoop']; K = IF['zones']['K_deck']
    z = {'D_front': boxc(*D['front']['x'], *D['front']['y'], *D['front']['z']), 'D_back': boxc(*D['back']['x'], *D['back']['y'], *D['back']['z'])}
    s = boxc(*S['x'], *S['y'], *S['z']); kk = boxc(*K['x'], *K['y'], *K['z'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            cb = boxc(*sorted((sx * COL['x_abs'][0], sx * COL['x_abs'][1])), *sorted((sy * COL['y_abs'][0], sy * COL['y_abs'][1])), 0, 800)
            s = s.cut(cb); kk = kk.cut(cb)
    z['S'] = s; z['K'] = kk
    # tunnels inside the spine are D's
    for tx in TUNNELS:
        z[f'tunnel_{int(tx)}'] = boxc(tx - TUN_W / 2, tx + TUN_W / 2, SP['y'][0], SP['y'][1], FLOOR_T, TUN_Z1)
    return z


def main(quick=False):
    world = HERE / 'world'; prn = HERE / 'print'
    parts = build()
    asm = cq.Assembly(name='frame_module')
    for lab, w, c in parts:
        export(w, world / f'{lab}.step'); asm.add(w, name=lab, color=cq.Color(*c))
    asm.save(str(world / 'frame_assembly.step'))
    # print files: one STL per unique part (quantities for mirrored / repeated parts are listed in parts.json)
    plist = []
    for lab, w, c in parts:
        if lab.startswith(('115', '120', '125', '126', '127', '128')):
            # panels: skin on the bed
            b = bbox(w)
            if lab.startswith('115'): w2 = w.rotate((0, 0, 0), (0, 1, 0), 90 if b[0] > 0 else -90)
            else: w2 = w.rotate((0, 0, 0), (1, 0, 0), -90 if b[1] > 0 else 90)
            bedp, diag = print_pose(w2)
        elif lab.startswith(('130', '135', '100')):
            bedp, diag = print_pose(w, flip=True)       # skin down
        elif lab.startswith('140'):
            bedp, diag = print_pose(w, flip=True) if 'R' in lab.split('_')[1] else print_pose(w)
        else:
            bedp, diag = print_pose(w)
        bf = bed_fit(bedp)
        if not bf['fits_248']:
            for ax in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
                b2, d2 = print_pose(w.rotate((0, 0, 0), ax, 90))
                if bed_fit(b2)['fits_248']: bedp, diag, bf = b2, d2, bed_fit(b2); break
        export(bedp, prn / f'{lab}_PRINT_1.stl')
        g = grams_day(w)
        noz06 = lab[:3] in ('105', '115', '120', '125', '126', '127', '128', '130', '135')   # panels and spine: 0.6 nozzle candidate
        plist.append({'label': lab, 'part_no': lab[:3], 'qty': 1, 'material': 'PLA red', **bf, 'diagonal_on_bed': diag, 'bed_face': bed_face(lab),
                      'est_grams': g, 'est_hours_0.4': round(g / G_PER_H, 1), 'est_hours_0.6_on_panels': round(g / (G_PER_H * (NOZ06_FACTOR if noz06 else 1.0)), 1)})
    total = round(sum(p['est_grams'] for p in plist))
    h04 = round(sum(p['est_hours_0.4'] for p in plist)); h06 = round(sum(p['est_hours_0.6_on_panels'] for p in plist))
    by = {}
    for p in plist: by[p['part_no']] = by.get(p['part_no'], 0) + p['est_grams']
    bought = [{'item': 'M3 heat-set insert', 'qty': 900, 'use': 'floor + deck grids (~575), seams, ledges, roof ring, studs'},
              {'item': 'M3 x 14 socket screw', 'qty': 420, 'use': 'panel seams and columns'},
              {'item': 'M3 x 10 screw', 'qty': 120, 'use': 'deck to ledges, roof to walls, studs, spine to floor'},
              {'item': 'M3 x 12 screw + nut', 'qty': 90, 'use': 'floor laps, spine seams, stud lugs'}]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'F', 'interface': IF['version'], 'printed': plist, 'bought': bought,
                                                 'est_total_grams': total, 'est_total_hours_0.4': h04, 'est_total_hours_0.6_on_panels_and_spine': h06,
                                                 'estimate_model': 'BJ day profile: 4 walls x 0.42 (1.68 mm per side), 5 top / 3 bottom layers x 0.2, 15 %% infill inside; hours at %d g/h' % G_PER_H,
                                                 'est_grams_by_part_no': {k: round(v) for k, v in by.items()}}, indent=1))
    res = checks(parts, plist, quick)
    stills(parts)
    return res


def load_dir(d, skip=('assembly',)):
    out = []
    for p in sorted(Path(d).glob('*.step')):
        if any(s in p.name for s in skip): continue
        try:
            out.append((p.stem, cq.Workplane().add(cq.importers.importStep(str(p)).val())))
        except Exception as e:
            print('skip', p.name, e)
    return out


MOVING_D = ('160_', '165_', '166_', '167_', '168_', '169_', '171_', '172_', '173_')


def checks(parts, plist, quick):
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}, 'placement_probe': check_place()}
    bbs = [(lab, w, bbox(w)) for lab, w, c in parts]
    env = [min(b[2][0] for b in bbs), min(b[2][1] for b in bbs), min(b[2][2] for b in bbs), max(b[2][3] for b in bbs), max(b[2][4] for b in bbs), max(b[2][5] for b in bbs)]
    res['envelope'] = {'bbox': [round(v, 1) for v in env], 'ok': env[0] >= E['x'][0] - .01 and env[3] <= E['x'][1] + .01 and env[1] >= E['y'][0] - .01 and env[4] <= E['y'][1] + .01 and env[2] >= 0 and env[5] <= E['z'][1] + .01}
    # zones: F must stay out of D, S, K and the rail tunnels
    zb = zone_boxes(); zhits = []
    for lab, w, b in bbs:
        for zn, zs in zb.items():
            if _ov(b, bbox(zs)):
                v = vol(w, zs)
                if v > 0.5: zhits.append([lab, zn, round(v, 1)])
    res['zone_violations'] = zhits
    # self clashes
    self_hits = []
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            if _ov(bbs[i][2], bbs[j][2]):
                v = vol(bbs[i][1], bbs[j][1])
                if v > 0.5: self_hits.append([bbs[i][0], bbs[j][0], round(v, 1)])
    res['self_clashes'] = self_hits
    # roof ribs vs drum top, roof hopper inserts positions
    res['roof_rib_underside_z'] = ROOF_Z0; res['drum_top_z_from_deck'] = 692.6
    res['hopper_insert_xy'] = [[round(x, 1), round(y, 1)] for (x, y) in HOP_INSERTS]
    if quick:
        return res
    # drawers in / out and the deck
    dr = load_dir('/home/claude/wt_all/cad/v14/drawer/world'); dk = load_dir('/home/claude/wt_deck/cad/v14/deck/world')
    res['loaded'] = {'drawer_parts': len(dr), 'deck_parts': len(dk)}

    def sweep(others, name):
        hits = []
        ob = [(n, s, bbox(s)) for n, s in others]
        for lab, w, b in bbs:
            for n, s, sb in ob:
                if _ov(b, sb):
                    v = vol(w, s)
                    if v > 0.5: hits.append([lab, n, round(v, 1)])
        res[name] = hits
    sweep(dr, 'clash_drawers_closed')
    out = []
    for n, s in dr:
        if any(k in n for k in MOVING_D):
            out.append((n, s.translate((0, IF['drawer']['travel_y'] if n.startswith('front') else -IF['drawer']['travel_y'], 0))))
        else:
            out.append((n, s))
    sweep(out, 'clash_drawers_open')
    sweep(dk, 'clash_deck')
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(parts):
    items = [(w, c, 1.0) for lab, w, c in parts]
    render(items, HERE / 'still_1_body_front.png', cam=(-1500, 2200, 1300), focal=(0, 0, 380), title='V14 frame (F): LEGO-red body 1040 x 520 x 720 + studs, drawer openings front and back')
    nofront = [(w, c, 1.0) for lab, w, c in parts if not lab.startswith(('120', '135', '140'))]
    render(nofront, HERE / 'still_2_inside.png', cam=(-1300, 1900, 1500), focal=(0, 0, 350), title='Front wall and roof off: floor grid, spine with rail tunnels, columns, deck on its ledges')
    back = [(w, c, 1.0) for lab, w, c in parts if not lab.startswith('128')]
    render(back, HERE / 'still_3_back_access.png', cam=(1300, -2000, 1200), focal=(0, 0, 400), title='Back: access panel removed (x -300..300, z 420..680), lower drawer opening')
    roof = [(w, c, 1.0) for lab, w, c in parts if lab.startswith(('135', '140'))]
    render(roof, HERE / 'still_4_roof_underside.png', cam=(-400, 600, -900), focal=(0, 0, 720), up=(0, 1, 0), title='Roof from below: ribs, hopper hole r 100 with its 3 inserts, stud bolt bosses')


if __name__ == '__main__':
    r = main(quick='--quick' in sys.argv)
    print(json.dumps({k: v for k, v in r.items() if k not in ('bed_fit',)}, indent=1)[:6000])
    print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
