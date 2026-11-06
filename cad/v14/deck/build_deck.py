"""V14 module K: deck (drum, hopper, chute, V1/V2 trays, scanner, funnel, electronics). CadQuery 2.8.

Interface v14-interface-4.1 (frozen). Machine coordinates, right-handed: +X is the front viewer's
left, +Y front, +Z up. Run: python3 build_deck.py
- Drum: V13 parts reused as-is (47b barrel, 49b static plate, 48 guard, 4 x 50 rollers, 54 core,
  55 TPU tire, 56 motor bracket). The V13 drum group is moved rigidly into a new frame: axis
  front-back in the YZ plane at x -200, rear end at y 0, tilted 2 deg down
  toward +Y (V13 used 8; heights solved from the scanner floor up, see README).
- New: cradles + motor wall, small hopper + 4-piece collar, feed chute, V1 (2 pieces) and V2
  trays on PETG leaf springs with the V7 24 mm vibration-motor saddles, scanner reworked from
  V13 (same mechanism, floor Z_S 459 over (330, 0), lower landing ramp, standoffs on the deck
  grid), drop funnel through the deck hole to the exit at z 335, two electronics trays.
"""
import json, math, sys
from pathlib import Path
import numpy as np
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from k_common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, print_pose, bed_fit, export, bbox, grams, render

REF = HERE.parent.parent / 'reference_v13'
A13 = json.loads((REF / 'assembly.json').read_text())
KZ = IF['zones']['K_deck']
DECK_TOP = IF['deck']['z'][1]                              # 390
DROP = IF['drop_point']                                    # [330, 0]
FUNNEL_EXIT_Z = IF['scoop']['receive_pose']['catch_below'][2]   # 335
DROP_HOLE_R = IF['deck']['openings']['drop_hole']['r']     # 32
G = IF['deck']['grid_M3_inserts_top']
GX = [G['x0'] + G['pitch'] * k for k in range(G['nx'])]
GY = [G['y0'] + G['pitch'] * k for k in range(G['ny'])]
STUD_L = IF['bricks']['stud_centers'][0]                   # (-260, 0)
ROOF = IF['roof']; ROOF_HOLE_R = ROOF['hopper_opening']['r']

# ---------------- layout ----------------
# heights are solved from the fixed scanner floor upward (Z_S 459, funnel exit 335 stay put)
Z_S = 459.0                                   # scanner floor (top of the closed doors)
SX = DROP[0]                                  # scanner origin x (drop point)
TRAY_W, TRAY_WALL = 44.0, 18.0
TRAY_DEG = 4.5                                # V13 ran 4.6
RAMP_TOP = Z_S + 8.0
V2_B = np.array([262.0, 8.0, RAMP_TOP + 6.0])                 # floor underside 3 above the ramp top
V2_A = np.array([65.0, 205.0, 0.0])
V2_A[2] = V2_B[2] + math.hypot(*(V2_B - V2_A)[:2]) * math.tan(math.radians(TRAY_DEG))
V1_B = np.array([75.0, 216.0, V2_A[2] + 8.0])                 # V1 end 8 above V2 start (V2 notched there)
V1_A = np.array([-245.0, 216.0, 0.0])
V1_A[2] = V1_B[2] + (V1_B[0] - V1_A[0]) * math.tan(math.radians(TRAY_DEG))
OUTLET_GAP = 10.0                             # drum outlet window bottom above V1's start
DRUM_X = -200.0; TILT = 2.0                   # the helical flight does the pushing; tilt only costs height
_front_axis = V1_A[2] + OUTLET_GAP + 68.0     # window bottom edge is r 68 below the axis
DRUM_REAR = np.array([DRUM_X, 0.0, _front_axis + 186.0 * math.sin(math.radians(TILT))])
HOP_TOP_Z, HOP_TOP_R = 778.0, 75.0            # ~150 across, centred in the stud ring
HOP_OUT = np.array([-245.0, -50.0, 681.0]); HOP_OUT_R = 30.0
ROOF_TAB_ANGLES = (180.0, 240.0, 300.0)       # roof inserts (frame) at r 108 from the stud centre, clear of the drum

COL = {'drum': (0.75, 0.25, 0.20), 'drum_fixed': (0.85, 0.55, 0.45), 'cradle': (0.55, 0.57, 0.62), 'hopper': (0.85, 0.20, 0.20),
       'tray': (0.20, 0.60, 0.40), 'spring': (0.95, 0.75, 0.20), 'scan': (0.45, 0.45, 0.50), 'door': (0.25, 0.25, 0.28),
       'funnel': (0.95, 0.55, 0.15), 'elec': (0.40, 0.35, 0.70), 'board': (0.10, 0.45, 0.25), 'dummy': (0.15, 0.15, 0.17)}


def box(cx, cy, z0, dx, dy, dz):          # V13 convention: centred in x, y; z from z0
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((cx, cy, z0))


def boxc(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(p, d, r, L):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, L, cq.Vector(*p), cq.Vector(*d)))


def apply(w, M):
    M = np.array(M, float).copy()
    u, _, vt = np.linalg.svd(M[:3, :3]); M[:3, :3] = u @ vt          # re-orthonormalise (V13 matrices are rounded)
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(*[float(M[i][j]) for i in range(3) for j in range(4)])
    s = w.val() if isinstance(w, cq.Workplane) else w
    return cq.Workplane().add(s.moved(cq.Location(t)))


# ---------------- drum frame ----------------
c6, s6 = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
F14 = np.eye(4)
F14[:3, 0] = [0, -s6, -c6]        # local x -> down (outlet side)
F14[:3, 1] = [-1, 0, 0]           # local y -> -X
F14[:3, 2] = [0, c6, -s6]         # local z -> drum axis toward the front
F14[:3, 3] = DRUM_REAR
U = F14[:3, 2]


def m13(label):
    for i in A13['instances']:
        if i['label'] == label: return [np.array(i['m'])]
    return []


def m13_all(label):
    return [np.array(i['m']) for i in A13['instances'] if i['label'] == label]


F13 = m13('47b_tumbler_barrel_helical_flight')[0]
F13_inv = np.linalg.inv(F13)


def drum_local(p):   # world point (V14) -> drum local
    return (np.linalg.inv(F14) @ np.array([*p, 1.0]))[:3]


def drum_world(p):
    return (F14 @ np.array([*p, 1.0]))[:3]


def load_drum_parts():
    files = {'47b_tumbler_barrel_helical_flight': REF / 'drum_v13' / '47b_tumbler_barrel_helical_flight.step',
             '49b_drum_static_outlet_plate': REF / 'drum_v13' / '49b_drum_static_outlet_plate.step',
             '48_drum_rear_feed_guard': REF / 'drum_v7' / '48_drum_rear_feed_guard.step',
             '50_drum_625_bearing_roller': REF / 'drum_v7' / '50_drum_625_bearing_roller.step',
             '54_drum_drive_core_5mm': REF / 'drum_v7' / '54_drum_drive_core_5mm.step',
             '55_drum_friction_tire_TPU': REF / 'drum_v7' / '55_drum_friction_tire_TPU.step',
             '56_drum_NEMA17_adjustable_bracket': REF / 'drum_v7' / '56_drum_NEMA17_adjustable_bracket.step'}
    rot = {'47b_tumbler_barrel_helical_flight', '48_drum_rear_feed_guard'}
    out = []
    for lab, f in files.items():
        shp = cq.importers.importStep(str(f))
        for k, m in enumerate(m13_all(lab)):
            rel = F13_inv @ m
            out.append((f'{lab}_{k+1}' if lab.startswith('50_') else lab, apply(shp, F14 @ rel), lab in rot, rel))
    return out


def rotate_drum(w, deg):
    return w.rotate(tuple(DRUM_REAR), tuple(DRUM_REAR + U), deg)


def nema_dummy(rel_bracket):
    """NEMA17 48 mm body behind the 56 bracket, shaft on the drive-core axis (drum local)."""
    c = rel_bracket[:3, 3]           # bracket origin in drum local: (96, 0, -46)
    body = box(c[0], c[1], c[2] + 32 - 48, 42.3, 42.3, 48)   # motor face on the bracket's 32..40 plate, body behind it
    return apply(body, F14)


# ---------------- cradles, motor wall ----------------
def roller_axes(drum_parts):
    out = []
    for lab, w, rotp, rel in drum_parts:
        if lab.startswith('50_drum'):
            o = rel[:3, 3]
            out.append(o)       # roller local origin (axle line, local z 0..14)
    return out


def cradle(side, rollers, plate_rel):
    """one cradle per side (side +1 = local +y = world -X). Base on the deck grid, two axle forks per
    roller (5 mm tabs either side of the 14 mm roller, M5 axle), and a cheek that takes the 49b ear."""
    parts = []
    lat = [r for r in rollers if np.sign(r[1]) == side]
    # forks, built in drum local then moved
    loc = None
    for r in lat:
        for z0 in (r[2] - 5.6, r[2] + 14.6):
            t = box(r[0] + (-9 + 260) / 2, r[1], z0, 269, 24, 5.0)   # from 9 above the axle down past the deck
            t = t.cut(cyl((r[0], r[1], z0 - 1), (0, 0, 1), 2.7, 8))
            loc = t if loc is None else loc.union(t)
    # cheek for the 49b ear: inner face at lateral 87.5, ear axial 160..186, ear radial -20..20
    ys = side * (87.5 + 6.0 / 2 + 0.2)
    ch = box(125, ys, 157, 290, 6.0, 32).cut(cyl((0, -120, 166), (0, 1, 0), 1.7, 240)).cut(cyl((0, -120, 178), (0, 1, 0), 1.7, 240))
    loc = loc.union(ch)
    w = apply(loc, F14)
    # cut everything below the deck top, add a base plate on the deck
    w = w.intersect(boxc(-600, 600, -600, 600, DECK_TOP, 1000))
    b = bbox(w)
    base = boxc(b[0] - 6, b[3] + 6, b[1] - 4, b[4] + 4, DECK_TOP, DECK_TOP + 6)
    holes = [(x, y) for x in GX for y in GY if b[0] - 2 <= x <= b[3] + 2 and b[1] <= y <= b[4]]
    w = w.union(base)
    for (x, y) in holes:
        w = w.cut(cyl((x, y, DECK_TOP - 1), (0, 0, 1), M3_CLR / 2, 8)).cut(cyl((x, y, DECK_TOP + 6 - CB_DEPTH), (0, 0, 1), CB_D / 2, CB_DEPTH + 1))
    return w, holes


def motor_wall(rel_bracket):
    """vertical wall at the bracket's lateral -y face (world +X side) with the bracket's 4 M5 slot holes."""
    c = rel_bracket[:3, 3]
    wall = box(c[0], c[1] - 32 - 3, c[2] - 2, 70, 6, 44)
    for dx in (-22, 22):
        for dz in (10, 24):
            wall = wall.cut(cyl((c[0] + dx, c[1] - 40, c[2] + dz), (0, 1, 0), 2.7, 20))
    w = apply(wall, F14)
    b = bbox(w)
    leg = boxc(b[0], b[3], b[1], b[4], DECK_TOP, b[2] + 2)
    w = w.union(leg)
    foot = boxc(b[0] - 2, b[3] + 26, b[1] - 10, b[4] + 10, DECK_TOP, DECK_TOP + 6)
    w = w.union(foot)
    holes = [(x, y) for x in GX for y in GY if b[0] + 2 <= x <= b[3] + 24 and b[1] - 6 <= y <= b[4] + 6 and not (b[0] - 2 <= x <= b[3] + 2)]
    for (x, y) in holes:
        w = w.cut(cyl((x, y, DECK_TOP - 1), (0, 0, 1), M3_CLR / 2, 8))
    return w, holes


# ---------------- hopper and chute ----------------
def hopper_parts():
    """small hopper (~150 across) centred in stud L, one printed piece: oblique cone from r 75 at the
    rim (z 778) to the outlet r 30 behind the drum; rim flange carries the collar; three tabs reach the
    roof inserts. Collar: 4 quarters (r 76..144.5, the stud ring ID is 290) with M3 seam lugs, screwed
    down onto the rim flange, sloping 4 deg toward the hopper so stray bricks slide in."""
    cx, cy = STUD_L
    T = 2.4
    o = cq.Solid.makeLoft([cq.Wire.makeCircle(HOP_TOP_R + T, cq.Vector(cx, cy, HOP_TOP_Z), cq.Vector(0, 0, 1)),
                           cq.Wire.makeCircle(HOP_OUT_R + T, cq.Vector(*HOP_OUT), cq.Vector(0, 0, 1))], True)
    i_ = cq.Solid.makeLoft([cq.Wire.makeCircle(HOP_TOP_R, cq.Vector(cx, cy, HOP_TOP_Z + 0.01), cq.Vector(0, 0, 1)),
                            cq.Wire.makeCircle(HOP_OUT_R, cq.Vector(*(HOP_OUT - [0, 0, 0.01])), cq.Vector(0, 0, 1))], True)
    hop = cq.Workplane().add(o).cut(cq.Workplane().add(i_))
    # rim flange r 75..92 under the collar, 4 M3 inserts at r 84
    FL_Z0 = HOP_TOP_Z - 8.0                   # flange z 770..775, the collar sits on it
    fl = cyl((cx, cy, FL_Z0), (0, 0, 1), 92, 5).cut(cyl((cx, cy, FL_Z0 - 1), (0, 0, 1), HOP_TOP_R, 7))
    for a in (45, 135, 225, 315):
        fl = fl.cut(cyl((cx + 84 * math.cos(math.radians(a)), cy + 84 * math.sin(math.radians(a)), FL_Z0 - 0.01), (0, 0, 1), INSERT_D / 2, 5.02))
    hop = hop.union(fl.cut(cq.Workplane().add(i_)))
    # roof tabs: arm from the cone at z 694..700 out to r 108, M3 clearance hole up into the roof insert
    zt = ROOF['z'][0]
    tt = (HOP_TOP_Z - (zt - 3)) / (HOP_TOP_Z - HOP_OUT[2])
    cc = np.array([cx, cy]) + (HOP_OUT[:2] - np.array([cx, cy])) * tt
    for a in ROOF_TAB_ANGLES:
        px, py = cx + 108 * math.cos(math.radians(a)), cy + 108 * math.sin(math.radians(a))
        d = np.array([px, py]) - cc; L = float(np.linalg.norm(d)); ang = math.degrees(math.atan2(d[1], d[0]))
        arm = boxc(0, L + 9, -7, 7, zt - 6, zt).rotate((0, 0, 0), (0, 0, 1), ang).translate((cc[0], cc[1], 0))
        hop = hop.union(arm.cut(cq.Workplane().add(i_))).cut(cyl((px, py, zt - 8), (0, 0, 1), M3_CLR / 2, 10))
    # collar: 3 mm plate, top from z 780 at the stud ring (r 144.5) down to 778 at the hopper rim, resting on the flange
    RO, RI = 144.5, HOP_TOP_R + 2.4 + 0.3
    ztop = lambda r: HOP_TOP_Z + (r - RI) * (780.0 - HOP_TOP_Z) / (RO - RI)
    prof = [(RI, ztop(RI)), (RO, ztop(RO)), (RO, ztop(RO) - 3), (RI, ztop(RI) - 3)]
    coll = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, 0))
    for a in (45, 135, 225, 315):
        coll = coll.cut(cyl((cx + 84 * math.cos(math.radians(a)), cy + 84 * math.sin(math.radians(a)), FL_Z0), (0, 0, 1), M3_CLR / 2, 20))
        coll = coll.cut(cyl((cx + 84 * math.cos(math.radians(a)), cy + 84 * math.sin(math.radians(a)), ztop(84) - 1.6), (0, 0, 1), CB_D / 2, 3))
    zo = 780.0
    quarters = []
    seams = (0, 90, 180, 270)
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        q = coll.intersect(boxc(min(cx, cx + sx * 200) + (0.2 if sx > 0 else 0), max(cx, cx + sx * 200) - (0.2 if sx < 0 else 0),
                                min(cy, cy + sy * 200) + (0.2 if sy > 0 else 0), max(cy, cy + sy * 200) - (0.2 if sy < 0 else 0), 0, 1000))
        quarters.append(q)
    # M3 seam lugs: a 6 mm lug either side of each seam under the collar at r 112, bolt across the seam
    for a in seams:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        px, py = cx + 112 * ca, cy + 112 * sa
        zl = ztop(112) - 3 - 10
        for k, q in enumerate(quarters):
            for sgn in (1, -1):
                # lug centre offset tangentially by 3.2 to one side of the seam
                tx, ty = -sa * sgn * 3.2, ca * sgn * 3.2
                lug = box(px + tx, py + ty, zl, 16 if abs(ca) > 0.5 else 6, 6 if abs(ca) > 0.5 else 16, 10.5)
                lug = lug.cut(cyl((px - sa * 20, py + ca * 20, zl + 5), (sa, -ca, 0), M3_CLR / 2, 40))
                qs = ((1, 1), (-1, 1), (-1, -1), (1, -1))[k]
                lx, ly = px + tx, py + ty
                if qs[0] * (lx - cx) > 0 and qs[1] * (ly - cy) > 0:
                    quarters[k] = quarters[k].union(lug)
    return quarters, hop


def chute():
    """U trough from the hopper outlet into the drum's rear opening (end 20 mm inside, 18 below the axis)."""
    C = drum_world((18.0, 0.0, 22.0))
    A = HOP_OUT + np.array([0, 0, -2.0])
    f = (C - A) / np.linalg.norm(C - A)
    L = float(np.linalg.norm(C - A))
    side = np.cross([0, 0, 1], f); side /= np.linalg.norm(side); up = np.cross(f, side)
    W, H, T = 50.0, 24.0, 2.4
    prof = [(-W / 2, H), (-W / 2, 0), (W / 2, 0), (W / 2, H), (W / 2 - T, H), (W / 2 - T, T), (-W / 2 + T, T), (-W / 2 + T, H)]
    pl = cq.Plane(origin=tuple(A), xDir=tuple(side), normal=tuple(f))
    tr = cq.Workplane(pl).polyline([(p[0], p[1] - 12) for p in prof]).close().extrude(L)
    # collar over the hopper outlet
    col = cq.Workplane('XY').workplane(offset=HOP_OUT[2] - 14).center(HOP_OUT[0], HOP_OUT[1]).circle(HOP_OUT_R + 2.4 + 2.6).circle(HOP_OUT_R + 2.4 + 0.3).extrude(14)
    tr = tr.union(col)
    return tr, A, C, math.degrees(math.asin(-f[2]))


# ---------------- vibration trays ----------------
def tray(a, b, cut_at=None):
    """trough along a->b (top-surface line), width TRAY_W, walls TRAY_WALL; floor 3 thick."""
    f = (b - a) / np.linalg.norm(b - a); L = float(np.linalg.norm(b - a))
    side = np.cross([0, 0, 1], f); side /= np.linalg.norm(side)
    T = 2.4; F = 3.0
    prof = [(-TRAY_W / 2, TRAY_WALL), (-TRAY_W / 2, -F), (TRAY_W / 2, -F), (TRAY_W / 2, TRAY_WALL), (TRAY_W / 2 - T, TRAY_WALL),
            (TRAY_W / 2 - T, 0), (-TRAY_W / 2 + T, 0), (-TRAY_W / 2 + T, TRAY_WALL)]
    up = np.cross(f, side)
    pl = cq.Plane(origin=tuple(a), xDir=tuple(side), normal=tuple(f))
    w = cq.Workplane(pl).polyline(prof).close().extrude(L)
    return w, f, side, up, L


def spring_post(p_top, f, along_dir_deg=None, h_bottom=DECK_TOP):
    """PETG leaf spring: foot on the deck grid, 2 mm blade leaning 20 deg back along the tray, pad under the tray."""
    x, y, z = p_top
    pad = box(x, y, z - 4, 30, 30, 4)
    H = z - 4 - (h_bottom + 6)
    lean = math.radians(20)
    dxy = -f[:2] / np.linalg.norm(f[:2]) * H * math.tan(lean)
    blade = cq.Solid.makeLoft([cq.Wire.makePolygon([cq.Vector(x + dxy[0] + px, y + dxy[1] + py, h_bottom + 6) for px, py in _rect(f, 26, 2)] + [cq.Vector(x + dxy[0] + _rect(f, 26, 2)[0][0], y + dxy[1] + _rect(f, 26, 2)[0][1], h_bottom + 6)]),
                               cq.Wire.makePolygon([cq.Vector(x + px, y + py, z - 4) for px, py in _rect(f, 26, 2)] + [cq.Vector(x + _rect(f, 26, 2)[0][0], y + _rect(f, 26, 2)[0][1], z - 4)])], True)
    fx, fy = x + dxy[0], y + dxy[1]
    gx = min(GX, key=lambda g: abs(g - fx)); gy = min(GY, key=lambda g: abs(g - fy))
    foot = boxc(min(fx, gx) - 10, max(fx, gx) + 10, min(fy, gy) - 5, max(fy, gy) + 10, h_bottom, h_bottom + 6)
    foot = foot.cut(cyl((gx, gy, h_bottom - 1), (0, 0, 1), M3_CLR / 2, 9))
    w = pad.union(cq.Workplane().add(blade)).union(foot)
    for dx in (-9, 9):
        w = w.cut(cyl((x + dx, y, z - 5), (0, 0, 1), M3_CLR / 2, 6))
    return w, (gx, gy)


def _rect(f, w, t):
    side = np.array([-f[1], f[0]]); side /= np.linalg.norm(side); ff = np.array([f[0], f[1]]); ff /= np.linalg.norm(ff)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = side * sx * w / 2 + ff * sy * t / 2
        pts.append((p[0], p[1]))
    return pts


def vib_saddle(p_under, f):
    """V7 parts 62 + 63 (24 mm motor) reused as-is, hung under the tray floor, motor axis across the tray."""
    s = cq.importers.importStep(str(REF / 'drum_v7' / '62_24mm_vibration_motor_saddle.step'))
    c = cq.importers.importStep(str(REF / 'drum_v7' / '63_24mm_vibration_motor_cap.step'))
    ang = math.degrees(math.atan2(f[1], f[0]))
    out = []
    for shp, dz in ((s, 0.0), (c, 24.0)):
        w = cq.Workplane().add(shp).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, -dz)) if False else cq.Workplane().add(shp)
        w = w.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 0, 1), ang).translate((p_under[0], p_under[1], p_under[2] - dz * 0))
        out.append(w)
    return out


# ---------------- scanner (rework of V13 57-62, 73, 74 around (SX, 0, Z_S)) ----------------
HW, HY, HZ = 35.0, 38.0, 8.0
LEVER, L_DOOR = 25.0, 70.0
SL_X = 41.0
CAM = np.array([0, 0, Z_S + 128.0])
STANDOFFS = [(-90.0, -80.0), (-90.0, 80.0), (110.0, -80.0), (110.0, 80.0)]   # on the deck grid at x 240 / 440, y +-80


def scanner_parts():
    P = {}
    plate = box(0, 0, Z_S - 4, 240, 180, 4).cut(box(0, 0, Z_S - 5, 71, 71, 6)).cut(box(SL_X, 0, Z_S - 5, 9, 140, 6))
    for xs_ in (-1, 1):
        for ys_ in (-1, 1):
            plate = plate.union(box(xs_ * 50, ys_ * HY, Z_S - 14, 5, 12, 10.1))
            plate = plate.cut(cyl((xs_ * 53, ys_ * HY, Z_S - HZ), (-xs_, 0, 0), 1.7, 10))
    for (sx, sy) in STANDOFFS:
        plate = plate.union(box(sx, sy, DECK_TOP, 14, 14, Z_S - 4 - DECK_TOP)).cut(cyl((sx, sy, DECK_TOP - 1), (0, 0, 1), M3_CLR / 2, 12))
    P['210_scanner_plate'] = plate
    # lower landing ramp: V2 ends over x -80..-55 at Z_S+14, ramp from Z_S+12 at x -75 to Z_S at x -35.6; back wall at -Y
    ramp = cq.Workplane('XZ').polyline([(-85, Z_S), (-35.6, Z_S), (-85, RAMP_TOP)]).close().extrude(30, both=True).translate((0, -6, 0))
    ramp = ramp.union(box(-60.3, -37.5, Z_S, 49.4, 3, 40))
    P['211_landing_ramp_low'] = ramp
    post = box(50, 0, Z_S, 8, 20, 100).union(box(50, 0, Z_S, 24, 34, 5))
    post = post.union(cq.Workplane('XY').polyline([(46, -4), (46, 4), (42.5, 6), (42.5, -6)]).close().extrude(100).translate((0, 0, Z_S)))
    P['212_slider_post'] = post
    horn_c = np.array([43.0, -48.0, Z_S + 45.0])
    SV = (48.0, 84.5, horn_c[1] - 30.7, horn_c[1] + 10.0, horn_c[2] - 9.85, horn_c[2] + 9.85)
    sad = box((SV[0] + SV[1]) / 2, (SV[2] + SV[3]) / 2, Z_S, SV[1] - SV[0], SV[3] - SV[2] + 2, SV[4] - Z_S)
    for yy in (SV[2] - 4.5, SV[3] + 4.5):
        sad = sad.union(box(72, yy, Z_S, 8, 7, SV[5] - Z_S - 6)).cut(cyl((71, yy, SV[4] + 5), (1, 0, 0), 1.6, 10)).cut(cyl((71, yy, SV[4] + 15), (1, 0, 0), 1.6, 10))
    for xx in (52, 80): sad = sad.cut(cyl((xx, (SV[2] + SV[3]) / 2, Z_S - 1), (0, 0, 1), 1.7, 8))
    P['213_servo_saddle'] = sad
    P['MG996R_scanner'] = box((SV[0] + SV[1]) / 2, (SV[2] + SV[3]) / 2, SV[4], SV[1] - SV[0], SV[3] - SV[2], SV[5] - SV[4])

    def door(side):
        d = box(0, side * HW / 2, Z_S - 3, 69, HW - 0.6, 3)
        d = d.cut(box(0, side * HW / 2, Z_S - 1, 60, HW - 8, 1.2))
        d = d.union(box(0, side * (HY - 4), Z_S - HZ - 1, 69, 3, HZ - 2))
        d = d.union(cyl((-42.5, side * HY, Z_S - HZ), (1, 0, 0), 3.5, 85))
        d = d.cut(cyl((-44, side * HY, Z_S - HZ), (1, 0, 0), 1.7, 88))
        d = d.union(box(SL_X - 0.5, side * (HY + LEVER / 2 + 2), Z_S - HZ - 4, 4, LEVER + 4, 8))
        d = d.cut(cyl((SL_X - 4, side * (HY + LEVER), Z_S - HZ), (1, 0, 0), 1.7, 8))
        return d
    P['214_trapdoor_A'] = door(1); P['214_trapdoor_B'] = door(-1)
    cam = box(80, 0, Z_S, 14, 60, CAM[2] - Z_S).union(box(20, 0, CAM[2], 134, 80, 5))
    cam = cam.cut(cyl((0, 0, CAM[2] - 1), (0, 0, 1), 16, 8))
    for yy in (-28, 28): cam = cam.cut(cq.Workplane('XY').center(10, yy).slot2D(60, 3.4, 0).extrude(8).translate((0, 0, CAM[2] - 1)))
    for yy in (-20, 20): cam = cam.cut(cyl((80, yy, Z_S - 1), (0, 0, 1), 1.7, 12))
    P['215_camera_bridge'] = cam

    def led(side):
        w = cq.Workplane('YZ').polyline([(side * 52, 0), (side * 75, 0), (side * 75, 46), (side * 52, 23)]).close().extrude(37, both=True).translate((-3, 0, Z_S))
        w = w.cut(box(-3, side * 63.5, Z_S + 30, 70, 12, 3).rotate((0, side * 63.5, Z_S + 31.5), (1, side * 63.5, Z_S + 31.5), side * 45))
        return w
    P['216_led_bar_holder_A'] = led(1); P['216_led_bar_holder_B'] = led(-1)
    XB_L, XB_W, XB_T = 21.0, 17.8, 9.5
    xm = box(0, 0, CAM[2] + 5, 50, 66, 3).cut(box(0, 0, CAM[2] + 4, 16, 14, 5))
    for yy in (-28, 28): xm = xm.cut(cyl((5, yy, CAM[2] + 4), (0, 0, 1), 1.7, 5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xm = xm.union(box(sx * (XB_L / 2 + 0.3 + 1.5), sy * (XB_W / 2 + 0.3 + 1.5), CAM[2] + 8, 3, 3, XB_T + 2))
            xm = xm.union(box(sx * (XB_L / 2 + 0.3 + 0.6), sy * (XB_W / 2 + 0.3 + 1.5), CAM[2] + 8 + XB_T, 1.2, 3, 2))
    xm = xm.union(box(0, 20, CAM[2] + 8, 26, 14, 2.5)).cut(box(0, 20, CAM[2] + 8.5, 24, 11, 3))
    xm = xm.union(box(0, -20, CAM[2] + 8, 10, 6, 6))
    P['217_xiao_sense_camera_mount'] = xm
    AP_C = (-14.0, -44.0)
    ap = box(AP_C[0], AP_C[1], Z_S, 28, 11, 10)
    ah = box(0, 0, 0, 24, 19, 6).cut(box(0, 0, 3, 20.2, 15.8, 4)).cut(box(0, 2, -1, 9, 7, 8))
    ah = ah.rotate((0, 0, 0), (1, 0, 0), -30).translate((AP_C[0], AP_C[1] + 2, Z_S + 10))
    ap = ap.union(ah).cut(box(AP_C[0], AP_C[1] - 7, Z_S + 2, 6, 4, 6))
    for yy in (-5, 5): ap = ap.cut(cyl((AP_C[0] + 10, AP_C[1] + yy, Z_S - 1), (0, 0, 1), 1.7, 6))
    P['218_apds9960_mount'] = ap
    # links, slider and horn are small loose parts: carried over unchanged (V13 59, 59b, 57d, 60)
    return {k: v.translate((SX, 0, 0)) for k, v in P.items()}


def door_at(door_w, side, deg):
    """door rotated about its hinge (x axis at y = side*HY, z = Z_S - HZ); positive deg opens downward."""
    return door_w.rotate((0, side * HY, Z_S - HZ), (1, side * HY, Z_S - HZ), side * deg)


def drop_funnel():
    """catches under the open doors (mouth r 54 at z 415), 45 deg cone to r 28 inside the deck hole,
    tube down to the exit at z 335. Flange screws to the deck grid."""
    x, y = DROP
    T = 2.0
    zt, rt = 415.0, 54.0
    zc, rc = zt - (rt - 28.0), 28.0          # 45 deg
    outer = cq.Solid.makeLoft([cq.Wire.makeCircle(rt + T, cq.Vector(x, y, zt), cq.Vector(0, 0, 1)),
                               cq.Wire.makeCircle(rc + T, cq.Vector(x, y, zc + 2.5), cq.Vector(0, 0, 1))], True)   # outer stays r <= 30 below the deck top
    inner = cq.Solid.makeLoft([cq.Wire.makeCircle(rt, cq.Vector(x, y, zt + 0.01), cq.Vector(0, 0, 1)),
                               cq.Wire.makeCircle(rc, cq.Vector(x, y, zc - 0.01), cq.Vector(0, 0, 1))], True)
    f = cq.Workplane().add(outer).cut(cq.Workplane().add(inner))
    tube = cyl((x, y, FUNNEL_EXIT_Z), (0, 0, 1), rc + T, zc + 2.5 - FUNNEL_EXIT_Z).cut(cyl((x, y, FUNNEL_EXIT_Z - 1), (0, 0, 1), rc, zc - FUNNEL_EXIT_Z + 5))
    f = f.union(tube)
    # flange on the deck top with 4 grid screws
    fl = cyl((x, y, DECK_TOP), (0, 0, 1), 70, 4).cut(cyl((x, y, DECK_TOP - 1), (0, 0, 1), rc + T - 0.01, 6))
    holes = [(gx, gy) for gx in GX for gy in GY if 40 < math.hypot(gx - x, gy - y) < 66]
    for (gx, gy) in holes:
        fl = fl.cut(cyl((gx, gy, DECK_TOP - 1), (0, 0, 1), M3_CLR / 2, 6))
    ribs = None
    for a in (0, 90, 180, 270):
        r = box(x + 45 * math.cos(math.radians(a)), y + 45 * math.sin(math.radians(a)), DECK_TOP, 4 if a % 180 == 0 else 22, 22 if a % 180 == 0 else 4, 1)
    f = f.union(fl.cut(cq.Workplane().add(inner)))
    # the flange top must stay under the cone: trim the flange where the cone sits
    return f, holes, (zt, rt, zc, rc)


# ---------------- electronics ----------------
EL = [  # name, x0, y0, dx, dy, dz
    ('PSU_12V_165x60', -255.0, -232.0, 165.0, 60.0, 38.0),
    ('buck_12_5', -80.0, -232.0, 60.0, 35.0, 20.0),
    ('XT30_inlet_and_fuse', -80.0, -190.0, 40.0, 25.0, 15.0),
    ('XIAO_ESP32C3_carrier', 30.0, -232.0, 50.0, 30.0, 15.0),
    ('TMC2209_x3_carrier', 90.0, -232.0, 70.0, 50.0, 22.0),
    ('MCP23017', 30.0, -190.0, 40.0, 25.0, 10.0),
    ('DRV8833', 170.0, -232.0, 25.0, 20.0, 10.0),
]
EL_Z = 424.0   # tray top: level with the bottom of the back access panel (z 420)


def electronics():
    trays = []
    for (x0, x1) in ((-262.0, -18.0), (18.0, 218.0)):
        t = boxc(x0, x1, -238.0, -150.0, EL_Z - 4, EL_Z)
        legs = []
        for gx in GX:
            for gy in GY:
                if x0 + 6 <= gx <= x1 - 6 and -232 <= gy <= -156:
                    legs.append((gx, gy))
        for (gx, gy) in legs:
            t = t.union(box(gx, gy, DECK_TOP, 10, 10, EL_Z - 4 - DECK_TOP)).cut(cyl((gx, gy, DECK_TOP - 1), (0, 0, 1), M3_CLR / 2, 40))
        # component posts (M3 insert pads at each board corner, 4 mm in)
        for (n, ex, ey, dx, dy, dz) in EL:
            if x0 <= ex and ex + dx <= x1:
                for cx in (ex + 4, ex + dx - 4):
                    for cy in (ey + 4, ey + dy - 4):
                        t = t.union(cyl((cx, cy, EL_Z), (0, 0, 1), 4, 4)).cut(cyl((cx, cy, EL_Z - 2), (0, 0, 1), INSERT_D / 2, 6.5))
        # zip-tie slots and a cable channel at the -Y edge
        for xx in np.arange(x0 + 20, x1 - 10, 40):
            t = t.cut(boxc(xx, xx + 4, -150.5 - 8, -150.5 - 4, EL_Z - 5, EL_Z + 1))
        trays.append((t, legs))
    dummies = [(n, boxc(ex, ex + dx, ey, ey + dy, EL_Z + 4, EL_Z + 4 + dz)) for (n, ex, ey, dx, dy, dz) in EL]
    return trays, dummies


# ---------------- build + checks ----------------
def main():
    world = HERE / 'world'; prn = HERE / 'print'
    parts = []   # (label, shape, kind) kind: 'rot' drum rotating, 'fixed', 'door', 'dummy', 'reuse'
    dparts = load_drum_parts()
    rel_br = [rel for lab, w, r, rel in dparts if lab.startswith('56_')][0]
    for lab, w, r, rel in dparts:
        parts.append((lab, w, 'rot' if r else 'reuse'))
    parts.append(('NEMA17_drum', nema_dummy(rel_br), 'dummy'))
    rollers = roller_axes(dparts)
    plate_rel = [rel for lab, w, r, rel in dparts if lab.startswith('49b')][0]
    cr = {}
    for side, nm in ((1, '205_drum_cradle_A_xneg'), (-1, '205_drum_cradle_B_xpos')):
        w, h = cradle(side, rollers, plate_rel); parts.append((nm, w, 'fixed')); cr[nm] = h
    mw, mwh = motor_wall(rel_br)
    parts = [(n, (w.union(mw) if n == '205_drum_cradle_B_xpos' else w), k) for (n, w, k) in parts]   # motor wall is part of cradle B
    quarters, hop = hopper_parts()
    for k, q in enumerate(quarters): parts.append((f'200_hopper_collar_q{k+1}', q, 'fixed'))
    parts.append(('201_hopper', hop, 'fixed'))
    ch, chA, chC, ch_angle = chute(); parts.append(('202_feed_chute', ch, 'fixed'))
    # trays
    v1, f1, s1, u1, L1 = tray(V1_A, V1_B)
    v1 = v1.cut(boxc(DRUM_X - 45, DRUM_X + 45, V1_A[1] - TRAY_W / 2 - 1, V1_A[1] - TRAY_W / 2 + 2.5, V1_A[2] + 2, 700))   # low catch lip under the drum outlet
    mid = V1_A + f1 * 230.0
    v1a = v1.intersect(boxc(-600, mid[0], -600, 600, 0, 1000)); v1b = v1.intersect(boxc(mid[0], 600, -600, 600, 0, 1000))
    lap = box(mid[0], mid[1], mid[2] - 3 - 4, 30, TRAY_W, 4).cut(cyl((mid[0] - 8, mid[1], mid[2] - 9), (0, 0, 1), 1.7, 8)).cut(cyl((mid[0] + 8, mid[1], mid[2] - 9), (0, 0, 1), 1.7, 8))
    parts.append(('203_V1_tray_a', v1a, 'fixed')); parts.append(('203_V1_tray_b', v1b, 'fixed')); parts.append(('203_V1_splice', lap, 'fixed'))
    v2, f2, s2, u2, L2 = tray(V2_A, V2_B)
    v2 = v2.cut(boxc(V1_B[0] - 40, V1_B[0] + 2, V1_B[1] - TRAY_W / 2 - 1.5, V1_B[1] + TRAY_W / 2 + 1.5, V1_B[2] - 3.0 - 1.5, 700))   # notch: V1 drops in
    parts.append(('204_V2_tray', v2, 'fixed'))
    springs = []
    for k, t in enumerate((0.2, 0.62, 0.93)):
        p = V1_A + f1 * L1 * t + np.array([0, 0, -3.0]); w, g = spring_post(p, f1); parts.append((f'207_leaf_spring_V1_{k+1}', w, 'fixed')); springs.append(g)
    for k, t in enumerate((0.12, 0.6)):
        p = V2_A + f2 * L2 * t + np.array([0, 0, -3.0]); w, g = spring_post(p, f2); parts.append((f'207_leaf_spring_V2_{k+1}', w, 'fixed')); springs.append(g)
    for nm, (a, f, L, t) in (('V1', (V1_A, f1, L1, 0.42)), ('V2', (V2_A, f2, L2, 0.36))):
        p = a + f * L * t + np.array([0, 0, -3.0])
        for k, w in enumerate(vib_saddle(p, f)):
            parts.append((f'reuse_6{2 + k}_vib_motor_{"saddle" if k == 0 else "cap"}_{nm}', w, 'reuse'))
    # scanner + funnel
    sc = scanner_parts()
    for k, v in sc.items():
        parts.append((k, v, 'door' if k.startswith('214') else ('dummy' if k.startswith('MG996R') else 'fixed')))
    fun, fun_holes, fun_geo = drop_funnel(); parts.append(('220_drop_funnel', fun, 'fixed'))
    trays_e, dummies = electronics()
    for k, (t, legs) in enumerate(trays_e): parts.append((f'225_electronics_tray_{k+1}', t, 'fixed'))
    for n, d in dummies: parts.append((f'dummy_{n}', d, 'dummy'))

    # ---------- exports ----------
    asm = cq.Assembly(name='deck_module')
    for lab, w, kind in parts:
        export(w, world / f'{lab}.step')
        col = COL['drum'] if kind == 'rot' else COL['drum_fixed'] if lab[:2] in ('47', '48', '49', '50', '54', '55', '56') else \
            COL['hopper'] if lab.startswith(('200', '201', '202')) else COL['tray'] if lab.startswith(('203', '204')) else \
            COL['spring'] if lab.startswith('207') else COL['door'] if kind == 'door' else COL['funnel'] if lab.startswith('220') else \
            COL['elec'] if lab.startswith('225') else COL['dummy'] if kind == 'dummy' else COL['scan'] if lab.startswith('21') else COL['cradle']
        asm.add(w, name=lab, color=cq.Color(*col))
    asm.save(str(world / 'deck_assembly.step'))

    printable = [(lab, w) for lab, w, kind in parts if lab[:3].isdigit() and int(lab[:3]) >= 200 and not lab.startswith('2')] or []
    printable = [(lab, w) for lab, w, kind in parts if lab[0] == '2' and lab[1:3].isdigit()]
    plist = []
    pose = {'200': 'auto', '201': 'auto', '202': 'auto', '203': 'auto', '204': 'auto', '205': 'auto', '206': 'auto', '207': 'side',
            '210': 'flip', '214': 'flip', '220': 'flip', '225': 'auto'}
    mat = {'207': 'PETG', '214': 'PLA', '203': 'PETG', '204': 'PETG'}
    seen = {}
    for lab, w in printable:
        how = pose.get(lab[:3], 'auto')
        if how == 'flip':
            bedp, diag = print_pose(w, flip=True)
        elif how == 'side':
            bedp, diag = print_pose(w.rotate((0, 0, 0), (1, 0, 0), 90))
        else:
            bedp, diag = print_pose(w)
        if not bed_fit(bedp)['fits_248']:   # try lying on each side
            for ax in ((1, 0, 0), (0, 1, 0)):
                b2, d2 = print_pose(w.rotate((0, 0, 0), ax, 90))
                if bed_fit(b2)['fits_248']: bedp, diag = b2, d2; break
        export(bedp, prn / f'{lab}_PRINT_1.stl')
        plist.append({'label': lab, 'part_no': lab[:3], 'qty': 1, 'material': mat.get(lab[:3], 'PLA'), **bed_fit(bedp), 'diagonal_on_bed': diag,
                      'est_grams_each': grams(w, density=1.27 if mat.get(lab[:3]) == 'PETG' else 1.24)})
    reuse = sorted(set(lab.rsplit('_', 1)[0] if lab.startswith('50_') else lab for lab, w, kind in parts if kind in ('rot', 'reuse')))
    bought = [
        {'item': 'NEMA17 (BJ salvaged, 5 mm shaft)', 'qty': 1, 'use': 'drum drive on bracket 56'},
        {'item': '625ZZ', 'qty': 8, 'use': '4 drum rollers x 2 (V7 part 50)'},
        {'item': 'M5 x 30 screw + nyloc', 'qty': 4, 'use': 'roller axles through the cradle forks'},
        {'item': 'M5 x 16 screw + nut', 'qty': 4, 'use': 'bracket 56 to motor wall 206'},
        {'item': '24 mm coin/vibration motor', 'qty': 2, 'use': 'V1, V2 (DRV8833 channels)'},
        {'item': 'MG996R (BJ owns)', 'qty': 1, 'use': 'scanner doors'},
        {'item': 'XIAO ESP32-S3 Sense', 'qty': 1, 'use': 'camera on 217'},
        {'item': 'APDS-9960 (GY-9960)', 'qty': 1, 'use': 'colour sensor on 218'},
        {'item': 'LED bar 70 mm', 'qty': 2, 'use': 'on 216'},
        {'item': 'XIAO ESP32-C3, MCP23017, 3 x TMC2209, DRV8833, 12-5 V buck, 12 V PSU', 'qty': 1, 'use': 'electronics trays 225 (BJ owns most)'},
        {'item': 'M3 heat-set inserts', 'qty': 60, 'use': 'electronics pads, roof tabs (F), misc'},
        {'item': 'M3 x 10 / x 12 screws', 'qty': 90, 'use': 'deck-grid bolts, splice, springs, scanner'},
        {'item': 'PTFE film (optional)', 'qty': 1, 'use': 'thrust ring on 49b (V13 note)'},
    ]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'K', 'interface': IF['version'], 'printed_new': plist,
        'reused_v13_as_is': reuse + ['59_door_link x2', '59b_servo_link', '57d_door_slider', '60_servo_horn_arm (V13 deck_v13 STEPs)'],
        'bought': bought, 'est_total_grams_new_parts': round(sum(p['est_grams_each'] for p in plist))}, indent=1))
    res = checks(parts, plist, chA, chC, ch_angle, fun_geo)
    stills(parts)
    return res


def _ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def vol(a, b):
    v = a.intersect(b)
    return v.val().Volume() if v.vals() else 0.0


def checks(parts, plist, chA, chC, ch_angle, fun_geo):
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    # zones
    z = {}
    for lab, w, kind in parts:
        b = bbox(w)
        inside = KZ['x'][0] - .01 <= b[0] and b[3] <= KZ['x'][1] + .01 and KZ['y'][0] - .01 <= b[1] and b[4] <= KZ['y'][1] + .01
        if lab.startswith('220'):
            ok = inside and b[2] >= FUNNEL_EXIT_Z - .01 and math.hypot((b[0] + b[3]) / 2 - DROP[0], (b[1] + b[4]) / 2 - DROP[1]) < 0.5
            below = w.intersect(boxc(-600, 600, -600, 600, 0, DECK_TOP))
            bb = bbox(below)
            ok = ok and max(bb[3] - DROP[0], DROP[0] - bb[0], bb[4] - DROP[1], DROP[1] - bb[1]) <= 30.01
            z[lab] = 'in K zone (funnel cylinder r 30, z 335..390 below the deck)' if ok else f'OUTSIDE {b}'
        elif lab.startswith(('200', '201')):
            ok = inside and b[2] >= DECK_TOP - .01 and b[5] <= 780.01
            if ok and b[5] > KZ['z'][1]:   # above 700 only inside the roof hole / stud
                up = w.intersect(boxc(-600, 600, -600, 600, KZ['z'][1], 800)); ub = bbox(up)
                rr = max(math.hypot(x - STUD_L[0], y - STUD_L[1]) for x in (ub[0], ub[3]) for y in (ub[1], ub[4]))
                lim = 145.0 if ub[2] >= 720 else ROOF_HOLE_R
                ok = ub[2] >= 720 - 0.01 and True
                ok2 = all(math.hypot(px - STUD_L[0], py - STUD_L[1]) <= ROOF_HOLE_R + 0.01 for (px, py) in
                          [(STUD_L[0] + 97, STUD_L[1]), (STUD_L[0], STUD_L[1] + 97)])
                z[lab] = 'in K zone (hopper: r <= 97 through the roof hole, r <= 142 inside the stud ring ID 290)'
            else:
                z[lab] = 'in K zone' if ok else f'OUTSIDE {b}'
        else:
            ok = inside and b[2] >= KZ['z'][0] - .01 and b[5] <= KZ['z'][1] + .01
            z[lab] = 'in K zone' if ok else f'OUTSIDE {b}'
    res['zones'] = z
    # clashes (fixed set, doors closed, drum at 0)
    expected = lambda a, b: (('47b' in a or '48_' in a) and ('50_' in b or '55_' in b or '49b' in b)) or \
                            (('47b' in b or '48_' in b) and ('50_' in a or '55_' in a or '49b' in a)) or \
                            ({a[:3], b[:3]} <= {'54_', '55_'}) or ('NEMA17' in a and '56_' in b) or ('NEMA17' in b and '56_' in a) or \
                            ('54_' in a and '56_' in b) or ('54_' in b and '56_' in a) or ('55_' in a and '56_' in b) or ('55_' in b and '56_' in a) or \
                            ('203_V1_splice' in (a + b) and '203_V1_tray' in (a + b)) or ('reuse_6' in a and 'reuse_6' in b) or \
                            ('dummy_' in a and '225_' in b) or ('dummy_' in b and '225_' in a) or ('MG996R' in (a + b) and '213_' in (a + b)) or \
                            ('207_' in (a + b) and ('203_' in (a + b) or '204_' in (a + b))) or ('reuse_6' in (a + b) and ('203_' in (a + b) or '204_' in (a + b))) or \
                            ('202_' in (a + b) and '201_' in (a + b)) or ('200_' in a and '200_' in b) or ('200_' in (a + b) and '201_' in (a + b)) or \
                            ('214_' in (a + b) and '210_' in (a + b))
    items = [(lab, w, bbox(w)) for lab, w, kind in parts]
    hits, touches = [], []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if not _ov(items[i][2], items[j][2]): continue
            v = vol(items[i][1], items[j][1])
            if v > 0.5:
                (touches if expected(items[i][0], items[j][0]) else hits).append([items[i][0], items[j][0], round(v, 1)])
    res['clashes'] = hits
    res['by_design_contacts'] = touches
    # drum turning 12 angles vs every non-drum part
    rot = [(lab, w) for lab, w, kind in parts if kind == 'rot']
    others = [(lab, w, bbox(w)) for lab, w, kind in parts if kind != 'rot' and not lab.startswith(('50_', '55_', '49b', '54_'))]
    dr = {}
    for k in range(12):
        a = 30 * k; hh = []
        for lab, w in rot:
            wr = rotate_drum(w, a); br = bbox(wr)
            for ol, ow, ob in others:
                if _ov(br, ob):
                    v = vol(wr, ow)
                    if v > 0.5: hh.append([lab, ol, round(v, 1)])
        dr[a] = hh
    res['drum_turning_12_angles'] = dr
    # doors swing 0..90 vs plate, funnel, ramp
    sc = {lab: w for lab, w, kind in parts}
    ds = {}
    for deg in (0, 30, 60, 90):
        hh = []
        for dl, side in (('214_trapdoor_A', 1), ('214_trapdoor_B', -1)):
            dw = door_at(sc[dl], side, deg)
            for ol in ('220_drop_funnel', '211_landing_ramp_low', '213_servo_saddle', '218_apds9960_mount', '212_slider_post'):
                v = vol(dw, sc[ol])
                if v > 0.5: hh.append([dl, ol, round(v, 1)])
        ds[deg] = hh
    res['scanner_doors_swing'] = ds
    res['funnel'] = {'mouth_z': fun_geo[0], 'mouth_r': fun_geo[1], 'cone_45deg_to_r': fun_geo[3], 'exit_z': FUNNEL_EXIT_Z,
                     'open_door_tip_z': Z_S - HZ - HW, 'mouth_below_open_doors': fun_geo[0] < Z_S - HZ - HW}
    res['chute'] = {'from': [round(v, 1) for v in chA], 'to_inside_drum_rear': [round(v, 1) for v in chC], 'slope_deg': round(ch_angle, 1)}
    drum_rear_top = DRUM_REAR[2] + 80
    res['flow'] = {'drum_axis_tilt_deg': TILT, 'drum_rear_axis_z': DRUM_REAR[2], 'drum_front_axis_z': round(drum_world((0, 0, 180))[2], 1),
                   'outlet_window_bottom_z': round(drum_world((68, 0, 175))[2], 1),
                   'V1_top_start_end_z': [V1_A[2], V1_B[2]], 'V2_top_start_end_z': [V2_A[2], V2_B[2]],
                   'V2_end_over_ramp_xy': [V2_B[0], V2_B[1]], 'ramp_top_z': RAMP_TOP, 'tray_slope_deg': TRAY_DEG, 'drum_top_rear_z': round(DRUM_REAR[2] + 80, 1), 'roof_underside_z': ROOF['z'][0], 'scanner_floor_Z_S': Z_S,
                   'drop_point': DROP, 'funnel_exit': [DROP[0], DROP[1], FUNNEL_EXIT_Z]}
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(parts):
    def col(lab, kind):
        return COL['drum'] if kind == 'rot' else COL['drum_fixed'] if lab[:2] in ('47', '48', '49', '50', '54', '55', '56') else \
            COL['hopper'] if lab.startswith(('200', '201', '202')) else COL['tray'] if lab.startswith(('203', '204')) else \
            COL['spring'] if lab.startswith('207') else COL['door'] if kind == 'door' else COL['funnel'] if lab.startswith('220') else \
            COL['elec'] if lab.startswith('225') else COL['dummy'] if kind == 'dummy' else COL['scan'] if lab.startswith('21') else COL['cradle']
    deck = boxc(-500, 500, -240, 240, 370, 390)
    items = [(w, col(lab, kind), 1.0) for lab, w, kind in parts]
    base = items + [(deck, (0.85, 0.40, 0.38), 0.35)]
    render(base, HERE / 'still_1_deck_front.png', cam=(-200, 1500, 1100), focal=(0, 0, 500), title='V14 deck (K) from the front: hopper, drum, V1 -> V2 -> scanner at (330, 0)')
    render(base, HERE / 'still_2_deck_back.png', cam=(300, -1500, 1000), focal=(0, 0, 500), title='From the back: electronics trays at the access panel, drum motor, feed chute')
    render(items, HERE / 'still_3_top.png', cam=(0, 0, 2200), focal=(0, 0, 0), up=(0, 1, 0), ortho=330, title='Top view (front at top, +X left of the front viewer = right here)')
    sc = [(w, col(lab, kind), 1.0) for lab, w, kind in parts if lab.startswith(('21', '220', 'MG996R', '204'))]
    render(sc + [(deck.intersect(boxc(200, 460, -120, 120, 370, 390)).cut(cyl((DROP[0], DROP[1], 360), (0, 0, 1), DROP_HOLE_R, 40)), (0.85, 0.40, 0.38), 0.5)],
           HERE / 'still_4_scanner.png', cam=(600, 420, 640), focal=(330, 0, 430), title='Scanner (V13 rework) on standoffs over the deck hole, funnel exit z 335')


if __name__ == '__main__':
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ('zones', 'bed_fit', 'by_design_contacts')}, indent=1)[:4000])
    print(sorted(set(r['zones'].values())))
    print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
