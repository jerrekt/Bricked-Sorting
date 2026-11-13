"""V14 module K, interface 5: deck (drum, hopper, chute, V1/V2 trays, scanner, funnel, electronics) re-fitted
from the interface-4.1 deck (branch cad-v14-deck, rev 2) into 708 x 348 x ~296 (deck ply top z 312, roof z 612).
CadQuery 2.8. Run: python3 build_deck.py

Machine coordinates: origin floor centre, +Y front, +Z up, +X = front viewer's left.
Layout (new in rev 3): the drum axis now runs along X (rear end at x -150, outlet plate at x ~36) at y 40, so the
hopper in the left stud at (-180, 0) can feed its rear end from above-behind through a 52 deg chute, and V1 runs
along +Y in front of the outlet plate, V2 diagonally back to the scanner at (240, 0). Heights are solved from the
drop funnel (exit z 270, tube r 25 through the deck hole) upward; the drum top lands at ~z 603 under the 612 roof.
- Drum: V13 parts reused as-is (47b barrel, 49b static plate, 48 guard, 4 x 50 rollers, 54 core, 55 tire, 56 bracket).
- New: cradles 205 (+ motor wall), hopper 201 with its flange on the stud-ring ledge (frame part 130), chute 202,
  V1 203 / V2 204 on PETG leaf springs 207 with the V7 vibration saddles, scanner 210-218 (V13 rework), funnel 220,
  electronics trays 225. Everything screws to the deck plywood with #6 wood screws.
"""
import json, math, sys
from pathlib import Path
import numpy as np
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from k_common import (IF, BED, INSERT_M3_D, INSERT_M3_DEPTH, M3_CLR, M3_CSK_D, WOOD_SCREW_CLR, WOOD_SCREW_CSK, print_pose, bed_fit,
                      export, bbox, extent, grams, hours, cyl, boxc, box, ov, vol, render)

REF = HERE.parent.parent / 'reference_v13'
A13 = json.loads((REF / 'assembly.json').read_text())
KZ = IF['zones']['K_deck']
DECK_TOP = IF['wood']['deck_ply']['z'][1]                 # 312
DROP = IF['drop_point']                                   # [240, 0]
FUNNEL_EXIT_Z = IF['scoop']['receive_pose']['funnel_exit'][2]   # 270
DECK_HOLE_R = 28.0; FUNNEL_TUBE_R = 25.0                  # interface: cylinder r 25 through a deck hole r 28
STUD_L = IF['studs']['centers'][0]                        # (-180, 0)
STUD_LEDGE_Z, STUD_LEDGE_R, STUD_INSERT_R = 646.0, 85.0, 92.5   # frame part 130: ledge top z 646, ID 170, 4 M3 at r 92.5 (45/135/225/315)
ROOF_Z, STUD_TOP = 612.0, IF['studs']['z'][1]             # 612, 664
ROOF_HOLE_R = 90.0

# ---------------- layout ----------------
TRAY_W, TRAY_WALL = 44.0, 18.0
TRAY_DEG = 4.5
HW, HY, HZ = 35.0, 38.0, 8.0                              # scanner trapdoor geometry (V13)
# funnel: tube r 25 z 270..300, 45 deg taper to r 27.5 at 302.5, tube to 313, 45 deg cone r 25.5 -> 50 (inner)
F_T = 2.0
F_TUBE_TOP = DECK_TOP + 1.0                               # 313
F_MOUTH_R = 50.0
F_CONE_DEG = 55.0
F_MOUTH_Z = F_TUBE_TOP + (F_MOUTH_R - (FUNNEL_TUBE_R + 2.5 - F_T)) / math.tan(math.radians(F_CONE_DEG))   # 330.2
Z_S = F_MOUTH_Z + 1.0 + HZ + HW                           # scanner floor ~374 (open door tips 1 mm above the mouth)
SX = DROP[0]
RAMP_TOP = Z_S + 8.0
V2_B = np.array([172.0, 8.0, RAMP_TOP + 6.0])
V2_A = np.array([75.0, 148.0, 0.0])
V2_A[2] = V2_B[2] + math.hypot(*(V2_B - V2_A)[:2]) * math.tan(math.radians(TRAY_DEG))
V1_X = 60.0                                               # V1 rear wall 1 mm in front of the outlet plate face (x ~36)
V1_B = np.array([V1_X, 145.0, V2_A[2] + 8.0])
V1_A = np.array([V1_X, 5.0, 0.0])
V1_A[2] = V1_B[2] + (V1_B[1] - V1_A[1]) * math.tan(math.radians(TRAY_DEG))
DRUM_Y = 40.0; DRUM_REAR_X = -150.0; TILT = 1.0           # axis along +X, tilted down toward the outlet
OUTLET_GAP = 20.0                                         # V1 floor top (at the window) to the window bottom edge
_win_floor = V1_A[2] - (DRUM_Y - V1_A[1]) * math.tan(math.radians(TRAY_DEG))
_front_axis = _win_floor + OUTLET_GAP + 68.0              # window bottom edge is r 68 below the axis (at local z 175)
DRUM_REAR = np.array([DRUM_REAR_X, DRUM_Y, _front_axis + 175.0 * math.sin(math.radians(TILT))])
HOP_TOP_Z, HOP_TOP_R = 658.0, 75.0                        # ~150 across, centred in the stud ring
HOP_OUT = np.array([-210.0, 40.0, 557.0]); HOP_OUT_R = 30.0
CHUTE_IN = (30.0, 0.0, 12.0)                              # chute end in drum local: 30 below the axis, 12 inside the rear end

COL = {'drum': (0.75, 0.25, 0.20), 'drum_fixed': (0.85, 0.55, 0.45), 'cradle': (0.55, 0.57, 0.62), 'hopper': (0.85, 0.20, 0.20),
       'tray': (0.20, 0.60, 0.40), 'spring': (0.95, 0.75, 0.20), 'scan': (0.45, 0.45, 0.50), 'door': (0.25, 0.25, 0.28),
       'funnel': (0.95, 0.55, 0.15), 'elec': (0.40, 0.35, 0.70), 'board': (0.10, 0.45, 0.25), 'dummy': (0.15, 0.15, 0.17),
       'frame': (0.82, 0.68, 0.45), 'skin': (0.78, 0.10, 0.10)}


def apply(w, M):
    M = np.array(M, float).copy()
    u, _, vt = np.linalg.svd(M[:3, :3]); M[:3, :3] = u @ vt
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(*[float(M[i][j]) for i in range(3) for j in range(4)])
    s = w.val() if isinstance(w, cq.Workplane) else w
    return cq.Workplane().add(s.moved(cq.Location(t)))


def csk_cone(p, d, big):
    return cq.Workplane(obj=cq.Solid.makeCone(big / 2, 0.0, big / 2, cq.Vector(*p), cq.Vector(*d)))


def wood_hole(w, x, y, z_top):
    """#6 wood-screw clearance through a foot whose top face is at z_top, countersunk from the top, into the deck ply."""
    return w.cut(cyl((x, y, DECK_TOP - 1), (0, 0, 1), WOOD_SCREW_CLR / 2, z_top - DECK_TOP + 2)).cut(csk_cone((x, y, z_top + 0.01), (0, 0, -1), WOOD_SCREW_CSK))


# ---------------- drum frame ----------------
c6, s6 = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
F14 = np.eye(4)
F14[:3, 0] = [-s6, 0, -c6]        # local x -> down (outlet side), leaning with the tilt
F14[:3, 1] = [0, 1, 0]            # local y -> +Y (lateral)
F14[:3, 2] = [c6, 0, -s6]         # local z -> drum axis toward the outlet (+X), 2 deg down
F14[:3, 3] = DRUM_REAR
U = F14[:3, 2]


def m13_all(label):
    return [np.array(i['m']) for i in A13['instances'] if i['label'] == label]


F13 = m13_all('47b_tumbler_barrel_helical_flight')[0]
F13_inv = np.linalg.inv(F13)


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
        shp = roller_50b() if lab.startswith('50_') else cq.importers.importStep(str(f))
        for k, m in enumerate(m13_all(lab)):
            rel = F13_inv @ m
            out.append((f'{lab}_{k+1}' if lab.startswith('50_') else lab, apply(shp, F14 @ rel), lab in rot, rel))
    return out


ROLLER_POCKET_D = 16.1   # 625ZZ pocket: BJ's PETG coupon 2026-11-09, dot 3 = 16.1 seats with a light push (V7 roller had 16.2)


def roller_50b():
    """V7 roller 50 (OD 32 x 14, 10 through, a 5.2-deep 625 pocket each end) redrawn with the tested pocket; print in PETG."""
    r = ROLLER_POCKET_D / 2
    w = cq.Workplane().circle(16).extrude(14).cut(cq.Workplane().circle(5).extrude(14))
    w = w.cut(cq.Workplane().circle(r).extrude(5.2)).cut(cq.Workplane().workplane(offset=8.8).circle(r).extrude(5.2))
    return w.val()


def rotate_drum(w, deg):
    return w.rotate(tuple(DRUM_REAR), tuple(DRUM_REAR + U), deg)


def nema_dummy(rel_bracket):
    c = rel_bracket[:3, 3]
    body = box(c[0], c[1], c[2] + 32 - 48, 42.3, 42.3, 48)
    return apply(body, F14)


# ---------------- cradles, motor wall ----------------
def cradle(side, rollers):
    """one cradle per side (side +1 = local +y = world +Y). Two 5 mm fork plates per roller (M5 axle), perpendicular
    to the axis, a cheek that takes the 49b ear, a 4 mm base on the deck with 4 #6 wood screws. Prints base-down."""
    lat = [r for r in rollers if np.sign(r[1]) == side]
    loc = None
    for r in lat:
        for z0 in (r[2] - 4.6, r[2] + 14.6):
            t = box(r[0] + (-9 + 260) / 2, r[1], z0, 269, 24, 4.0)
            t = t.cut(cyl((r[0], r[1], z0 - 1), (0, 0, 1), 2.7, 8))
            loc = t if loc is None else loc.union(t)
    ys = side * (87.5 + 6.0 / 2 + 0.2)
    ch = box(125, ys, 157, 290, 6.0, 28).cut(cyl((0, -120, 166), (0, 1, 0), 1.7, 240)).cut(cyl((0, -120, 178), (0, 1, 0), 1.7, 240))
    loc = loc.union(ch)
    # a 5 mm longitudinal web joins the forks at the bottom (stiffness), 20 tall above the deck
    web = box(0, side * 67.88, 20, 60, 5.0, 150).translate((0, 0, 0))
    w = apply(loc, F14)
    w = w.intersect(boxc(-600, 600, -600, 600, DECK_TOP, 1000))
    b = bbox(w)
    base = boxc(b[0] - 6, b[3] + 6, b[1] - 4, b[4] + 4, DECK_TOP, DECK_TOP + 3)
    w = w.union(base)
    # bottom web along the base joining all forks (vertical plate, 25 tall)
    web = boxc(b[0] - 6, b[3] + 6, side * DRUM_Y * 0 + (b[1] + b[4]) / 2 - 2.5, (b[1] + b[4]) / 2 + 2.5, DECK_TOP, DECK_TOP + 25)
    w = w.union(web)
    holes = [(b[0] - 1, b[1] - 1), (b[3] + 1, b[1] - 1), (b[0] - 1, b[4] + 1), (b[3] + 1, b[4] + 1)]
    for (x, y) in holes:
        w = wood_hole(w, x, y, DECK_TOP + 3)
    return w, holes


def motor_wall(rel_bracket):
    c = rel_bracket[:3, 3]
    wall = box(c[0], c[1] - 32 - 3, c[2] - 2, 70, 6, 44)
    for dx in (-22, 22):
        for dz in (10, 24):
            wall = wall.cut(cyl((c[0] + dx, c[1] - 40, c[2] + dz), (0, 1, 0), 2.7, 20))
    w = apply(wall, F14)
    b = bbox(w)
    leg = boxc(b[0], b[3], b[1], b[4], DECK_TOP, b[2] + 2)
    w = w.union(leg)
    foot = boxc(b[0] - 8, b[3] + 8, b[1] - 10, b[4] + 10, DECK_TOP, DECK_TOP + 4)
    w = w.union(foot)
    holes = [(b[0] - 4, b[1] - 6), (b[3] + 4, b[4] + 6), (b[0] - 4, b[4] + 6), (b[3] + 4, b[1] - 6)]
    for (x, y) in holes:
        w = wood_hole(w, x, y, DECK_TOP + 4)
    return w, holes


# ---------------- hopper and chute ----------------
def hopper():
    """one piece, ~150 across, centred in the left stud: oblique cone from r 75 at z 658 to the outlet r 30 at
    (-190, 40, 570); sloped top ring up to r 100 at z 663 (catches strays inside the stud ring), skirt r 97..100,
    and a flat flange r 85..100 at z 646..651 that sits on the stud-ring ledge (frame 130) with 4 csk M3.
    Rev 2: flat top ring r 75..100 at z 663 and a 45 deg fill between flange and top, so it prints upside down with no supports."""
    cx, cy = STUD_L
    T = 2.0
    o = cq.Solid.makeLoft([cq.Wire.makeCircle(HOP_TOP_R + T, cq.Vector(cx, cy, HOP_TOP_Z), cq.Vector(0, 0, 1)),
                           cq.Wire.makeCircle(HOP_OUT_R + T, cq.Vector(*HOP_OUT), cq.Vector(0, 0, 1))], True)
    i_ = cq.Solid.makeLoft([cq.Wire.makeCircle(HOP_TOP_R, cq.Vector(cx, cy, HOP_TOP_Z + 0.01), cq.Vector(0, 0, 1)),
                            cq.Wire.makeCircle(HOP_OUT_R, cq.Vector(*(HOP_OUT - [0, 0, 0.01])), cq.Vector(0, 0, 1))], True)
    hop = cq.Workplane().add(o).cut(cq.Workplane().add(i_))
    # rev 2 (2026-11-12, BJ printing P11): printed upside down with no supports. The top ring is flat (it is the bed face,
    # r 75..100 at z 663) instead of the 11 deg slope, and the flange + skirt are one solid section whose inner face is a
    # 45 deg cone (85, 651) -> (97, 663), so nothing overhangs flat. Screw access: 6.5 bores from the top down to the csk.
    TOPZ = HOP_TOP_Z + 5
    top = cq.Workplane('XZ').polyline([(HOP_TOP_R, HOP_TOP_Z), (HOP_TOP_R, TOPZ), (100.0, TOPZ), (100.0, HOP_TOP_Z - 3), (HOP_TOP_R + T, HOP_TOP_Z - 3)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, 0))
    body = cq.Workplane('XZ').polyline([(STUD_LEDGE_R, STUD_LEDGE_Z), (100.0, STUD_LEDGE_Z), (100.0, TOPZ), (97.0, TOPZ), (STUD_LEDGE_R, STUD_LEDGE_Z + 5)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, 0))
    hop = hop.union(top).union(body)
    for a in (45, 135, 225, 315):
        px, py = cx + STUD_INSERT_R * math.cos(math.radians(a)), cy + STUD_INSERT_R * math.sin(math.radians(a))
        hop = hop.cut(cyl((px, py, STUD_LEDGE_Z - 1), (0, 0, 1), M3_CLR / 2, 8)).cut(csk_cone((px, py, STUD_LEDGE_Z + 5.01), (0, 0, -1), M3_CSK_D))
        hop = hop.cut(cyl((px, py, STUD_LEDGE_Z + 5.0), (0, 0, 1), M3_CSK_D / 2, TOPZ - STUD_LEDGE_Z))   # driver/head access from the top
    return hop, i_


def chute():
    """U trough from the hopper outlet into the drum's rear opening (CHUTE_IN)."""
    C = drum_world(CHUTE_IN)
    A = HOP_OUT + np.array([0, 0, -2.0])
    f = (C - A) / np.linalg.norm(C - A)
    L = float(np.linalg.norm(C - A))
    side = np.cross([0, 0, 1], f); side /= np.linalg.norm(side)
    W, H, T = 50.0, 24.0, 2.4
    prof = [(-W / 2, H), (-W / 2, 0), (W / 2, 0), (W / 2, H), (W / 2 - T, H), (W / 2 - T, T), (-W / 2 + T, T), (-W / 2 + T, H)]
    pl = cq.Plane(origin=tuple(A), xDir=tuple(side), normal=tuple(f))
    tr = cq.Workplane(pl).polyline([(p[0], p[1] - 12) for p in prof]).close().extrude(L)
    col = cq.Workplane('XY').workplane(offset=HOP_OUT[2] - 14).center(HOP_OUT[0], HOP_OUT[1]).circle(HOP_OUT_R + 2.4 + 2.6).circle(HOP_OUT_R + 2.4 + 0.3).extrude(14)
    tr = tr.union(col)
    return tr, A, C, math.degrees(math.asin(-f[2]))


# ---------------- vibration trays ----------------
def tray(a, b):
    f = (b - a) / np.linalg.norm(b - a); L = float(np.linalg.norm(b - a))
    side = np.cross([0, 0, 1], f); side /= np.linalg.norm(side)
    T = 2.4; F = 3.0
    prof = [(-TRAY_W / 2, TRAY_WALL), (-TRAY_W / 2, -F), (TRAY_W / 2, -F), (TRAY_W / 2, TRAY_WALL), (TRAY_W / 2 - T, TRAY_WALL),
            (TRAY_W / 2 - T, 0), (-TRAY_W / 2 + T, 0), (-TRAY_W / 2 + T, TRAY_WALL)]
    pl = cq.Plane(origin=tuple(a), xDir=tuple(side), normal=tuple(f))
    w = cq.Workplane(pl).polyline(prof).close().extrude(L)
    return w, f, side, L


def _rect(f, w, t):
    side = np.array([-f[1], f[0]]); side /= np.linalg.norm(side); ff = np.array([f[0], f[1]]); ff /= np.linalg.norm(ff)
    return [((side * sx * w / 2 + ff * sy * t / 2)[0], (side * sx * w / 2 + ff * sy * t / 2)[1]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def spring_post(p_top, f, lean=20.0):
    """PETG leaf spring: foot on the deck (#6 wood screw), 2 mm blade leaning 20 deg back along the tray, pad under the tray (2 x M3)."""
    x, y, z = p_top
    pad = box(x, y, z - 4, 30, 30, 4)
    H = z - 4 - (DECK_TOP + 6)
    dxy = -f[:2] / np.linalg.norm(f[:2]) * H * math.tan(math.radians(lean))
    r = _rect(f, 26, 2)
    blade = cq.Solid.makeLoft([cq.Wire.makePolygon([cq.Vector(x + dxy[0] + px, y + dxy[1] + py, DECK_TOP + 6) for px, py in r] + [cq.Vector(x + dxy[0] + r[0][0], y + dxy[1] + r[0][1], DECK_TOP + 6)]),
                               cq.Wire.makePolygon([cq.Vector(x + px, y + py, z - 4) for px, py in r] + [cq.Vector(x + r[0][0], y + r[0][1], z - 4)])], True)
    fx, fy = x + dxy[0], y + dxy[1]
    foot = box(fx, fy, DECK_TOP, 30, 30, 6)
    w = pad.union(cq.Workplane().add(blade)).union(foot)
    for dx, dy in ((-10, -10), (10, 10)):
        w = wood_hole(w, fx + dx, fy + dy, DECK_TOP + 6)
    for dx in (-9, 9):
        w = w.cut(cyl((x + dx, y, z - 5), (0, 0, 1), M3_CLR / 2, 6))
    return w, (fx, fy)


def vib_saddle(p_under, f):
    s = cq.importers.importStep(str(REF / 'drum_v7' / '62_24mm_vibration_motor_saddle.step'))
    c = cq.importers.importStep(str(REF / 'drum_v7' / '63_24mm_vibration_motor_cap.step'))
    ang = math.degrees(math.atan2(f[1], f[0]))
    out = []
    for shp in (s, c):
        w = cq.Workplane().add(shp).rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 0, 1), ang).translate((p_under[0], p_under[1], p_under[2]))
        out.append(w)
    return out


# ---------------- scanner (V13 rework around (SX, 0, Z_S)) ----------------
LEVER, L_DOOR = 25.0, 70.0
SL_X = 41.0
CAM = np.array([0, 0, Z_S + 128.0])
STANDOFFS = [(-90.0, -80.0), (-60.0, 80.0), (90.0, -80.0), (90.0, 80.0)]     # on the deck ply at x 150/180 / 330, y +-80 (the +y front one clears V2 spring 2)
PLATE_X0, PLATE_X1 = -115.0, 105.0                                           # x 125..345 (deck ply ends at 354)


def scanner_parts():
    P = {}
    plate = boxc(PLATE_X0, PLATE_X1, -90, 90, Z_S - 3, Z_S).cut(box(0, 0, Z_S - 5, 71, 71, 6)).cut(box(SL_X, 0, Z_S - 5, 9, 140, 6))
    plate = plate.cut(boxc(PLATE_X0 - 1, PLATE_X0 + 45, 25, 92, Z_S - 5, Z_S + 1))      # notch (x 125..170, y 25..92) under V2's saddle and last spring
    for xs_ in (-1, 1):
        for ys_ in (-1, 1):
            plate = plate.union(box(xs_ * 50, ys_ * HY, Z_S - 14, 5, 12, 10.1))
            plate = plate.cut(cyl((xs_ * 53, ys_ * HY, Z_S - HZ), (-xs_, 0, 0), 1.7, 10))
    for (sx, sy) in STANDOFFS:
        plate = plate.union(box(sx, sy, DECK_TOP, 14, 14, Z_S - 3 - DECK_TOP)).union(box(sx, sy, DECK_TOP, 24, 24, 4))
    P['210_scanner_plate'] = plate
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
    for zz in (Z_S + 30, Z_S + 85):          # webcam cable: zip-tie slot pairs through the post
        for yy in (-24.0, -16.0): cam = cam.cut(box(80, yy, zz, 16, 2.4, 4))
    P['215_camera_bridge'] = cam

    def led(side):
        w = cq.Workplane('YZ').polyline([(side * 52, 0), (side * 75, 0), (side * 75, 46), (side * 52, 23)]).close().extrude(37, both=True).translate((-3, 0, Z_S))
        w = w.cut(box(-3, side * 63.5, Z_S + 30, 70, 12, 3).rotate((0, side * 63.5, Z_S + 31.5), (1, side * 63.5, Z_S + 31.5), side * 45))
        return w
    P['216_led_bar_holder_A'] = led(1); P['216_led_bar_holder_B'] = led(-1)
    # 217: generic USB-webcam plate (electrical update Nov 8, model TBD): 34 mm lens window over the bridge hole, two zip-tie
    # slot pairs to strap the webcam face-down, 2 x M3 to the bridge slots. CAM (Z_S + 128) is the lens-to-trapdoor distance.
    xm = box(0, 0, CAM[2] + 5, 50, 66, 3).cut(cyl((0, 0, CAM[2] + 4), (0, 0, 1), 17, 5))
    for yy in (-28, 28): xm = xm.cut(cyl((5, yy, CAM[2] + 4), (0, 0, 1), 1.7, 5))
    for xx in (-21, 21):
        for yy in (-12, 12): xm = xm.cut(box(xx, yy, CAM[2] + 4, 2.4, 5, 5))
    P['217_webcam_mount_generic'] = xm
    AP_C = (-14.0, -44.0)
    ap = box(AP_C[0], AP_C[1], Z_S, 28, 11, 10)
    ah = box(0, 0, 0, 24, 19, 6).cut(box(0, 0, 3, 20.2, 15.8, 4)).cut(box(0, 2, -1, 9, 7, 8))
    ah = ah.rotate((0, 0, 0), (1, 0, 0), -30).translate((AP_C[0], AP_C[1] + 2, Z_S + 10))
    ap = ap.union(ah).cut(box(AP_C[0], AP_C[1] - 7, Z_S + 2, 6, 4, 6))
    for yy in (-5, 5): ap = ap.cut(cyl((AP_C[0] + 10, AP_C[1] + yy, Z_S - 1), (0, 0, 1), 1.7, 6))
    P['218_apds9960_mount'] = ap
    out = {k: v.translate((SX, 0, 0)) for k, v in P.items()}
    # standoff wood screws (after the translate so the holes are vertical in world)
    holes = []
    for (sx, sy) in STANDOFFS:
        for dx, dy in ((9, 9), (-9, -9)):
            out['210_scanner_plate'] = wood_hole(out['210_scanner_plate'], SX + sx + dx, sy + dy, DECK_TOP + 4); holes.append((SX + sx + dx, sy + dy))
    return out, holes


def door_at(door_w, side, deg):
    return door_w.rotate((SX, side * HY, Z_S - HZ), (SX + 1, side * HY, Z_S - HZ), side * deg)


def drop_funnel():
    """tube OD 25 from z 270 to 300, 45 deg step to OD 27.5 at 302.5, tube to z 313 (through the r 28 deck hole),
    45 deg cone to the mouth r 50 at z 337.5 under the open doors; flange on the deck top with 4 #6 wood screws."""
    x, y = DROP
    r_in_tube, r_in_up = FUNNEL_TUBE_R - F_T, FUNNEL_TUBE_R + 2.5 - F_T     # 23, 25.5
    z_step0, z_step1 = DECK_TOP - 12.0, DECK_TOP - 9.5
    outer = cyl((x, y, FUNNEL_EXIT_Z), (0, 0, 1), FUNNEL_TUBE_R, z_step0 - FUNNEL_EXIT_Z)
    outer = outer.union(cq.Workplane().add(cq.Solid.makeCone(FUNNEL_TUBE_R, FUNNEL_TUBE_R + 2.5, z_step1 - z_step0, cq.Vector(x, y, z_step0), cq.Vector(0, 0, 1))))
    outer = outer.union(cyl((x, y, z_step1), (0, 0, 1), FUNNEL_TUBE_R + 2.5, F_TUBE_TOP - z_step1))
    outer = outer.union(cq.Workplane().add(cq.Solid.makeCone(FUNNEL_TUBE_R + 2.5, F_MOUTH_R + F_T, F_MOUTH_Z - F_TUBE_TOP, cq.Vector(x, y, F_TUBE_TOP), cq.Vector(0, 0, 1))))
    inner = cyl((x, y, FUNNEL_EXIT_Z - 1), (0, 0, 1), r_in_tube, z_step0 - FUNNEL_EXIT_Z + 1)
    inner = inner.union(cq.Workplane().add(cq.Solid.makeCone(r_in_tube, r_in_up, z_step1 - z_step0, cq.Vector(x, y, z_step0), cq.Vector(0, 0, 1))))
    inner = inner.union(cyl((x, y, z_step1), (0, 0, 1), r_in_up, F_TUBE_TOP - z_step1))
    inner = inner.union(cq.Workplane().add(cq.Solid.makeCone(r_in_up, F_MOUTH_R, F_MOUTH_Z - F_TUBE_TOP + 0.5, cq.Vector(x, y, F_TUBE_TOP), cq.Vector(0, 0, 1))))
    f = outer.cut(inner)
    fl = cyl((x, y, DECK_TOP), (0, 0, 1), 60, 4).cut(cyl((x, y, DECK_TOP - 1), (0, 0, 1), FUNNEL_TUBE_R + 2.5 - 0.01, 6))
    holes = [(x + 46 * math.cos(math.radians(a)), y + 46 * math.sin(math.radians(a))) for a in (45, 135, 225, 315)]
    f = f.union(fl)
    for (hx, hy) in holes:
        f = wood_hole(f, hx, hy, DECK_TOP + 4)
    return f, holes, (F_MOUTH_Z, F_MOUTH_R, F_TUBE_TOP, r_in_up, r_in_tube)


# ---------------- electronics (Nov 8 electrical update) ----------------
# Pi 4B is the brain; USB webcam replaces the XIAO S3 Sense; 12 V 10 A PSU (199 x 98 x 42, being measured); two bucks
# (>= 5 A servos + vibration motors, >= 3 A Pi + logic); XT30 + fuse on the 12 V side; deck MCP23017 dropped (Pi GPIO).
# All board sizes are placeholders except the Pi: measure and edit EL. Trays sit at z 334, behind the back access panel.
EL_Z = DECK_TOP + 22.0   # tray top z 334, just above the panel's bottom edge (330)
PSU = dict(x0=-290.0, y0=-165.0, dx=199.0, dy=98.0, dz=42.0)          # AC/DC terminal end at x -294 (under the IEC inlet)
EL = [  # name, x0, y0, dx, dy, dz, tray
    ('buck_5A_servos_vib', -80.0, -168.0, 40.0, 65.0, 22.0, 'b'),
    ('XT30_and_fuse_12V', -80.0, -98.0, 40.0, 25.0, 15.0, 'b'),
    ('buck_3A_pi_logic', -35.0, -168.0, 28.0, 48.0, 20.0, 'b'),
    ('DRV8833', -35.0, -114.0, 20.0, 25.0, 10.0, 'b'),
    ('XIAO_ESP32C3_carrier', -12.0, -114.0, 22.0, 40.0, 12.0, 'b'),
    ('TMC2209_2slot_carrier', 24.0, -103.0, 50.0, 40.0, 22.0, '2'),
]
PI = dict(x0=24.0, y0=-166.0, dx=85.0, dy=56.0, dz=20.0, holes=(58.0, 49.0), inset=3.5)   # USB/Ethernet end at x 105 (faces the camera)
SPOOL_C = (255.0, -133.0)
CLIPS_226 = [(332.0, -112.0, 0.0), (198.0, -140.0, 90.0)]


def _legs_tray(outline, legs):
    """outline: shapely polygon (x, y); 2.4 mm plate at EL_Z, legs to the deck with #6 wood screws."""
    from shapely.geometry import Polygon as SP
    t = cq.Workplane('XY').workplane(offset=EL_Z - 2.4).polyline([(float(a), float(b)) for a, b in list(outline.exterior.coords)[:-1]]).close().extrude(2.4)
    for (gx, gy) in legs:
        t = t.union(box(gx, gy, DECK_TOP, 12, 12, EL_Z - 2.4 - DECK_TOP)).union(box(gx, gy, DECK_TOP, 20, 20, 4))
        t = t.cut(cyl((gx, gy, DECK_TOP - 1), (0, 0, 1), WOOD_SCREW_CLR / 2, EL_Z - DECK_TOP + 2)).cut(csk_cone((gx, gy, EL_Z + 0.01), (0, 0, -1), WOOD_SCREW_CSK))
    return t


def _m3_pads(t, ex, ey, dx, dy):
    for cx in (ex + 4, ex + dx - 4):
        for cy in (ey + 4, ey + dy - 4):
            t = t.union(cyl((cx, cy, EL_Z), (0, 0, 1), 4, 4)).cut(cyl((cx, cy, EL_Z - 2), (0, 0, 1), INSERT_M3_D / 2, 6.5))
    return t


def electronics():
    from shapely.geometry import Polygon as SP, box as sb
    parts, screws = [], []
    # tray 1a: PSU in a 6 mm fence (+0.5 clearance), 2 strap slots (hook-and-loop or zip tie) until its hole pattern is measured
    o = sb(-316.0, -172.0, -86.0, -60.0)
    legs = [(-304.0, -162.0), (-98.0, -162.0), (-304.0, -70.0), (-98.0, -70.0), (-200.0, -162.0), (-200.0, -70.0)]
    t = _legs_tray(o, legs)
    c = 0.5; fx0, fx1, fy0, fy1 = PSU['x0'] - c, PSU['x0'] + PSU['dx'] + c, PSU['y0'] - c, PSU['y0'] + PSU['dy'] + c
    fence = boxc(fx0, fx1 + 2, fy0 - 2, fy1 + 2, EL_Z, EL_Z + 6).cut(boxc(fx0, fx1, fy0, fy1, EL_Z - 1, EL_Z + 7)).cut(boxc(fx0 - 3, fx0 + 12, fy0 - 3, fy1 + 3, EL_Z - 1, EL_Z + 7))
    t = t.union(fence)
    for xs in (-235.0, -150.0):
        for (ya, yb) in ((-170.5, -167.5), (-63.5, -60.8)):
            t = t.cut(boxc(xs - 13, xs + 13, ya, yb, EL_Z - 3, EL_Z + 7))
    for (ix, iy) in ((-311.5, -120.0), (-311.5, -90.0)):          # 2 M3 inserts for the terminal cover tabs (-x end)
        t = t.union(cyl((ix, iy, EL_Z - 2.4), (0, 0, 1), 2.8, 2.4 + 6)).cut(cyl((ix, iy, EL_Z + 6 - INSERT_M3_DEPTH), (0, 0, 1), INSERT_M3_D / 2, INSERT_M3_DEPTH + 1))
    parts.append(('225_electronics_tray_1a_psu', t, 'fixed')); screws += [('225_electronics_tray_1a_psu', x, y) for x, y in legs]
    # tray 1b: bucks, XT30 + fuse, DRV8833, XIAO C3
    o = sb(-82.0, -172.0, 12.0, -60.0)
    legs = [(-72.0, -162.0), (2.0, -162.0), (-72.0, -70.0), (2.0, -70.0)]
    t = _legs_tray(o, legs)
    for (n, ex, ey, dx, dy, dz, tr) in EL:
        if tr == 'b': t = _m3_pads(t, ex, ey, dx, dy)
    for xx in (-56.0, -22.0):
        t = t.cut(boxc(xx, xx + 4, -66.5, -62.5, EL_Z - 4, EL_Z + 1))
    parts.append(('225_electronics_tray_1b_power_io', t, 'fixed')); screws += [('225_electronics_tray_1b_power_io', x, y) for x, y in legs]
    # tray 2: Pi 4B (M2 x 16 + nut trap from below; 58 x 49 holes) + 2-slot TMC2209 carrier; L-shape clears the scanner standoff (150, -80)
    o = SP([(16.0, -172.0), (180.0, -172.0), (180.0, -97.0), (124.0, -97.0), (124.0, -60.0), (16.0, -60.0)])
    legs = [(26.0, -162.0), (170.0, -162.0), (170.0, -107.0), (26.0, -70.0), (114.0, -70.0), (98.0, -162.0)]
    t = _legs_tray(o, legs)
    for hx in (PI['x0'] + PI['inset'], PI['x0'] + PI['inset'] + PI['holes'][0]):
        for hy in (PI['y0'] + PI['inset'], PI['y0'] + PI['inset'] + PI['holes'][1]):
            t = t.union(cyl((hx, hy, EL_Z), (0, 0, 1), 3.0, 6)).cut(cyl((hx, hy, EL_Z - 3), (0, 0, 1), 1.1, 10))
            t = t.cut(cq.Workplane('XY').polygon(6, 4.4).extrude(1.8).translate((hx, hy, EL_Z - 2.41)))
    for (n, ex, ey, dx, dy, dz, tr) in EL:
        if tr == '2': t = _m3_pads(t, ex, ey, dx, dy)
    parts.append(('225_electronics_tray_2_pi', t, 'fixed')); screws += [('225_electronics_tray_2_pi', x, y) for x, y in legs]
    # 227 PSU terminal cover: wraps the terminal end (x -308..-280), slot up for the AC lead to the inlet, slot on +y for DC
    cx0, cx1 = PSU['x0'] - 18.0, PSU['x0'] + 10.0
    cy0, cy1 = fy0 - 2.0, fy1 + 2.0
    cz1 = EL_Z + PSU['dz'] + 1.0 + 2.0
    cov = boxc(cx0, cx1, cy0, cy1, EL_Z, cz1).cut(boxc(cx0 + 2, cx1 + 1, cy0 + 2, cy1 - 2, EL_Z - 1, cz1 - 2))
    cov = cov.cut(boxc(cx0 + 4, cx0 + 16, -132.0, -108.0, cz1 - 3, cz1 + 1))                     # AC slot (top)
    cov = cov.cut(boxc(cx0 + 4, cx0 + 17, cy1 - 3, cy1 + 1, EL_Z + 8, EL_Z + 22))                # DC slot (+y side)
    for (ix, iy) in ((-311.5, -120.0), (-311.5, -90.0)):
        tab = boxc(-314.5, cx0 + 0.01, iy - 5, iy + 5, EL_Z + 6, EL_Z + 9)
        cov = cov.union(tab).cut(cyl((ix, iy, EL_Z + 5), (0, 0, 1), M3_CLR / 2, 6))
    cov = cov.cut(boxc(cx0 - 1, cx1 + 1, fy0 - 2.1, fy0 - 1.9, EL_Z - 1, EL_Z)) if False else cov
    parts.append(('227_psu_terminal_cover', cov, 'fixed'))
    # 228 webcam cable spool: base r 38 (3 #6 inside the core), core r 25, 45 deg flange to r 38, entry slot
    sx, sy = SPOOL_C
    prof = [(0.0, 0.0), (38.0, 0.0), (38.0, 3.0), (25.0, 3.0), (25.0, 24.0), (38.0, 37.0), (38.0, 39.0), (23.0, 39.0), (23.0, 3.0), (0.0, 3.0)]
    sp = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((sx, sy, DECK_TOP))
    sp = sp.cut(boxc(sx - 3, sx + 3, sy + 20, sy + 40, DECK_TOP + 26, DECK_TOP + 40))
    for a in (90, 210, 330):
        hx, hy = sx + 12 * math.cos(math.radians(a)), sy + 12 * math.sin(math.radians(a))
        sp = wood_hole(sp, hx, hy, DECK_TOP + 3); screws.append(('228_webcam_cable_spool', hx, hy))
    parts.append(('228_webcam_cable_spool', sp, 'fixed'))
    # 226 USB cable clips (snap-in, 6.2 bore, 4.2 mouth) with one #6
    for k, (x, y, ang) in enumerate(CLIPS_226):
        cl = box(0, 0, 0, 10, 14, 12).cut(cyl((-6, 0, 7), (1, 0, 0), 3.1, 12)).cut(box(0, 0, 7, 12, 4.2, 6))
        cl = cl.union(box(0, -13, 0, 10, 12, 3))
        cl = cl.cut(cyl((0, -14, -1), (0, 0, 1), WOOD_SCREW_CLR / 2, 5)).cut(csk_cone((0, -14, 3.01), (0, 0, -1), WOOD_SCREW_CSK))
        cl = cl.rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y, DECK_TOP))
        parts.append((f'226_usb_cable_clip_{k + 1}', cl, 'fixed'))
        dx_, dy_ = -14 * -math.sin(math.radians(ang)), -14 * math.cos(math.radians(ang))
        screws.append((f'226_usb_cable_clip_{k + 1}', x + dx_, y + dy_))
    # dummies
    dz = [('PSU_12V_10A_199x98x42', boxc(PSU['x0'], PSU['x0'] + PSU['dx'], PSU['y0'], PSU['y0'] + PSU['dy'], EL_Z, EL_Z + PSU['dz'])),
          ('RPi4B', boxc(PI['x0'], PI['x0'] + PI['dx'], PI['y0'], PI['y0'] + PI['dy'], EL_Z + 6, EL_Z + 6 + PI['dz']))]
    dz += [(n, boxc(ex, ex + dx, ey, ey + dy, EL_Z + 4, EL_Z + 4 + dh)) for (n, ex, ey, dx, dy, dh, tr) in EL]
    return parts, screws, dz


# ---------------- frame reference (for the cross-check) ----------------
def frame_ref_parts():
    """frame parts that neighbour the deck: posts, top rails, roof tiles, left stud ring, C3 roof clips (from the
    cad-v14-frame5 world STEPs if present next to the repo), else the wood boxes from interface.json."""
    out = []
    d = HERE.parent / 'frame' / 'world'
    if not d.exists():
        d = Path('/home/claude/frame_ref')
    if d.exists():
        for f in sorted(d.glob('*.step')):
            if f.name.startswith(('100_', '101_', '102_', '109_', '111_', '114_', '119_', '130_', '123_')):
                out.append((f.stem, cq.importers.importStep(str(f)), 'skin' if f.name.startswith(('114', '130')) else 'frame'))
    return out


# ---------------- build + checks ----------------
def main():
    world = HERE / 'world'; prn = HERE / 'print'
    parts = []
    dparts = load_drum_parts()
    rel_br = [rel for lab, w, r, rel in dparts if lab.startswith('56_')][0]
    for lab, w, r, rel in dparts:
        parts.append((lab, w, 'rot' if r else 'reuse'))
    parts.append(('NEMA17_drum', nema_dummy(rel_br), 'dummy'))
    rollers = [rel[:3, 3] for lab, w, r, rel in dparts if lab.startswith('50_drum')]
    screws = []
    for side, nm in ((1, '205_drum_cradle_A_ypos'), (-1, '205_drum_cradle_B_yneg')):
        w, h = cradle(side, rollers); parts.append((nm, w, 'fixed')); screws += [(nm, x, y) for x, y in h]
    mw, mwh = motor_wall(rel_br); parts.append(('206_motor_wall', mw, 'fixed')); screws += [('206_motor_wall', x, y) for x, y in mwh]
    hop, hop_inner = hopper(); parts.append(('201_hopper', hop, 'fixed'))
    ch, chA, chC, ch_angle = chute(); parts.append(('202_feed_chute', ch, 'fixed'))
    # trays
    v1, f1, s1, L1 = tray(V1_A, V1_B)
    v1 = v1.cut(boxc(V1_X - TRAY_W / 2 - 1, V1_X - TRAY_W / 2 + 2.5, DRUM_Y - 45, DRUM_Y + 45, _win_floor + 2.0, 700))   # low catch lip under the outlet plate
    parts.append(('203_V1_tray', v1, 'fixed'))
    v2, f2, s2, L2 = tray(V2_A, V2_B)
    v2 = v2.cut(boxc(V1_X - TRAY_W / 2 - 2, V1_X + TRAY_W / 2 + 2, V1_B[1] - 45, V1_B[1] + 2.5, V1_B[2] - 3.0 - 1.5, 700))   # notch: V1 drops in
    parts.append(('204_V2_tray', v2, 'fixed'))
    for k, t in enumerate((0.1, 0.85)):
        p = V1_A + f1 * L1 * t + np.array([0, 0, -3.0]); w, g = spring_post(p, f1); parts.append((f'207_leaf_spring_V1_{k+1}', w, 'fixed')); screws += [(f'207_leaf_spring_V1_{k+1}', g[0] + dx, g[1] + dy) for dx, dy in ((-10, -10), (10, 10))]
    for k, t in enumerate((0.16, 0.77)):
        p = V2_A + f2 * L2 * t + np.array([0, 0, -3.0]); w, g = spring_post(p, f2, lean=(10.0 if k == 0 else 20.0)); parts.append((f'207_leaf_spring_V2_{k+1}', w, 'fixed')); screws += [(f'207_leaf_spring_V2_{k+1}', g[0] + dx, g[1] + dy) for dx, dy in ((-10, -10), (10, 10))]
    for nm, (a, f, L, t) in (('V1', (V1_A, f1, L1, 0.45)), ('V2', (V2_A, f2, L2, 0.43))):
        p = a + f * L * t + np.array([0, 0, -3.0])
        for k, w in enumerate(vib_saddle(p, f)):
            parts.append((f'reuse_6{2 + k}_vib_motor_{"saddle" if k == 0 else "cap"}_{nm}', w, 'reuse'))
    sc, sc_holes = scanner_parts(); screws += [('210_scanner_plate', x, y) for x, y in sc_holes]
    for k, v in sc.items():
        parts.append((k, v, 'door' if k.startswith('214') else ('dummy' if k.startswith('MG996R') else 'fixed')))
    fun, fun_holes, fun_geo = drop_funnel(); parts.append(('220_drop_funnel', fun, 'fixed')); screws += [('220_drop_funnel', x, y) for x, y in fun_holes]
    eparts, escrews, dummies = electronics()
    parts += eparts; screws += escrews
    for n, d in dummies: parts.append((f'dummy_{n}', d, 'dummy'))
    parts.append(('dummy_USB_webcam_placeholder', box(SX, 0, CAM[2] + 8, 60, 40, 35), 'dummy'))

    # ---------- exports ----------
    asm = cq.Assembly(name='deck_module')
    for lab, w, kind in parts:
        export(w, world / f'{lab}.step')
        asm.add(w, name=lab, color=cq.Color(*col_of(lab, kind)))
    asm.save(str(world / 'deck_assembly.step'))

    printable = [(lab, w) for lab, w, kind in parts if lab[0] == '2' and lab[1:3].isdigit()]
    plist = []
    pose = {'201': 'flip', '202': 'auto', '203': 'auto', '204': 'auto', '205': 'auto', '206': 'auto', '207': 'side',
            '210': 'flip', '211': 'auto', '212': 'auto', '213': 'auto', '214': 'flip', '215': 'auto', '216': 'auto', '217': 'auto', '218': 'auto', '220': 'flip', '225': 'auto', '226': 'auto', '227': 'flip', '228': 'auto'}
    mat = {'207': 'PETG', '203': 'PETG', '204': 'PETG'}
    notes = {'201': 'rim (flange) down, outlet up; cone walls >= 45 deg', '202': 'laid flat on a side wall', '203': 'walls up (PETG)', '204': 'walls up (PETG)',
             '205': 'base down, forks vertical (teardrop the axle holes if needed)', '206': 'foot down', '207': 'on its side (PETG)', '210': 'upside down',
             '214': 'upside down', '220': 'mouth down (cone inside at 45 deg)', '225': 'tray top up', '226': 'base down', '227': 'top face down', '228': 'base down (45 deg flange)'}
    for lab, w in printable:
        how = pose.get(lab[:3], 'auto')
        if how == 'flip': bedp, diag = print_pose(w, flip=True)
        elif how == 'side': bedp, diag = print_pose(w.rotate((0, 0, 0), (1, 0, 0), 90))
        else: bedp, diag = print_pose(w)
        if not bed_fit(bedp)['fits_248']:
            for ax in ((1, 0, 0), (0, 1, 0)):
                b2, d2 = print_pose(w.rotate((0, 0, 0), ax, 90))
                if bed_fit(b2)['fits_248']: bedp, diag = b2, d2; break
        export(bedp, prn / f'{lab}_PRINT_1.stl')
        m = mat.get(lab[:3], 'PLA'); g = grams(w, m)
        plist.append({'label': lab, 'part_no': lab[:3], 'qty': 1, 'material': m, **bed_fit(bedp), 'diagonal_on_bed': diag,
                      'est_grams_each': g, 'est_hours_each': hours(g, w), 'orientation': notes.get(lab[:3], 'flat')})
    rb = cq.Workplane().add(roller_50b()); g50 = grams(rb, 'PETG')
    export(rb, prn / '50b_drum_625_roller_PETG_pocket16.1_PRINT_4.stl')
    plist.append({'label': '50b_drum_625_roller', 'part_no': '50b', 'qty': 4, 'material': 'PETG', **bed_fit(rb), 'diagonal_on_bed': False,
                  'est_grams_each': g50, 'est_hours_each': hours(g50, rb), 'orientation': 'flat on an end; 625 pockets 16.1 (PETG coupon dot 3)'})
    reuse = sorted(set(lab.rsplit('_', 1)[0] if lab.startswith('50_') else lab for lab, w, kind in parts if kind in ('rot', 'reuse')))
    bought = [
        {'item': 'NEMA17 (BJ salvaged, 5 mm shaft)', 'qty': 1, 'use': 'drum drive on bracket 56'},
        {'item': '625ZZ', 'qty': 8, 'use': '4 drum rollers x 2 (V7 part 50)'},
        {'item': 'M5 x 30 screw + nyloc', 'qty': 4, 'use': 'roller axles through the cradle forks'},
        {'item': 'M5 x 16 screw + nut', 'qty': 4, 'use': 'bracket 56 to motor wall 206'},
        {'item': 'M3 x 12 + nut', 'qty': 4, 'use': '49b ears to the cradle cheeks'},
        {'item': '24 mm coin/vibration motor', 'qty': 2, 'use': 'V1, V2 (DRV8833 channels)'},
        {'item': 'MG996R (BJ owns)', 'qty': 1, 'use': 'scanner doors'},
        {'item': 'USB webcam (model TBD)', 'qty': 1, 'use': 'strapped face-down on 217, cable to the Pi via 215 post slots, clips 226, spool 228'},
        {'item': 'APDS-9960 (GY-9960)', 'qty': 1, 'use': 'colour sensor on 218'},
        {'item': 'LED bar 70 mm', 'qty': 2, 'use': 'on 216'},
        {'item': 'Pi 4B, XIAO ESP32-C3, 2 x TMC2209 (2-slot carrier), DRV8833, buck >= 5 A, buck >= 3 A, 12 V 10 A PSU, XT30 + fuse', 'qty': 1, 'use': 'trays 225 1a / 1b / 2 (deck MCP23017 dropped: Pi GPIO)'},
        {'item': 'IEC C14 fused + switched snap-in inlet', 'qty': 1, 'use': 'frame back tile B c1 r3 (cutout 47.5 x 27.5 placeholder)'},
        {'item': 'M2 x 16 + nut', 'qty': 4, 'use': 'Pi 4B to tray 2 (nut traps underneath)'},
        {'item': 'hook-and-loop strap or 2 zip ties', 'qty': 2, 'use': 'PSU to tray 1a until its hole pattern is measured'},
        {'item': 'M3 heat-set inserts', 'qty': 34, 'use': 'electronics pads (32) + PSU cover (2)'},
        {'item': 'M3 x 8 countersunk', 'qty': 4, 'use': 'hopper flange to the stud-ring ledge (frame 130)'},
        {'item': 'M3 x 10 / x 12 screws', 'qty': 40, 'use': 'springs, saddles, scanner'},
        {'item': '#6 x 3/4 in wood screws', 'qty': len(screws) + 6, 'use': 'everything that stands on the deck ply'},
        {'item': 'PTFE film (optional)', 'qty': 1, 'use': 'thrust ring on 49b (V13 note)'},
    ]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'K', 'interface': IF['version'], 'printed_new': plist,
        'reused_v13_as_is': reuse + ['59_door_link x2', '59b_servo_link', '57d_door_slider', '60_servo_horn_arm (V13 deck_v13 STEPs)'],
        'bought': bought, 'deck_ply_screws': [{'part': p, 'x': round(x, 1), 'y': round(y, 1)} for p, x, y in screws],
        'est_total_grams_new_parts': round(sum(p['est_grams_each'] for p in plist)), 'est_total_hours_new_parts': round(sum(p['est_hours_each'] for p in plist), 1)}, indent=1))
    res = checks(parts, plist, chA, chC, ch_angle, fun_geo)
    stills(parts)
    return res


def col_of(lab, kind):
    return COL['drum'] if kind == 'rot' else COL['drum_fixed'] if lab[:2] in ('47', '48', '49', '50', '54', '55', '56') else \
        COL['hopper'] if lab.startswith(('201', '202')) else COL['tray'] if lab.startswith(('203', '204')) else \
        COL['spring'] if lab.startswith('207') else COL['door'] if kind == 'door' else COL['funnel'] if lab.startswith('220') else \
        COL['elec'] if lab.startswith('225') else COL['dummy'] if kind == 'dummy' else COL['scan'] if lab.startswith('21') else \
        COL.get(kind, COL['cradle'])


def checks(parts, plist, chA, chC, ch_angle, fun_geo):
    res = {'interface': IF['version'], 'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    z = {}
    for lab, w, kind in parts:
        b = bbox(w)
        inside = KZ['x'][0] - .01 <= b[0] and b[3] <= KZ['x'][1] + .01 and KZ['y'][0] - .01 <= b[1] and b[4] <= KZ['y'][1] + .01
        if lab.startswith('220'):
            below = w.intersect(boxc(-600, 600, -600, 600, 0, DECK_TOP)); bb = bbox(below)
            ok = inside and b[2] >= FUNNEL_EXIT_Z - .01 and max(bb[3] - DROP[0], DROP[0] - bb[0], bb[4] - DROP[1], DROP[1] - bb[1]) <= 27.51
            z[lab] = 'in K zone (funnel r <= 27.5 through the r 28 deck hole, z 270..312)' if ok else f'OUTSIDE {b}'
        elif lab.startswith('201'):
            ok = inside and b[2] >= DECK_TOP - .01 and b[5] <= STUD_TOP + .01
            ann = cyl((STUD_L[0], STUD_L[1], ROOF_Z - 2), (0, 0, 1), 300, 2).cut(cyl((STUD_L[0], STUD_L[1], ROOF_Z - 3), (0, 0, 1), ROOF_HOLE_R - 1.0, 4))
            rr = ROOF_HOLE_R - 1.0 if vol(w, ann) < 0.5 else 999.0
            ok = ok and rr <= ROOF_HOLE_R + .01
            z[lab] = 'in K zone (hopper through the roof hole with >= 1 mm to r 90; inside the stud ring above)' if ok else f'OUTSIDE {b} (roof hole r 90 touched: {rr > 500})'
        else:
            ok = inside and b[2] >= KZ['z'][0] - .01 and b[5] <= KZ['z'][1] + .01
            z[lab] = 'in K zone' if ok else f'OUTSIDE {b}'
    res['zones'] = z
    expected = lambda a, b: (('47b' in a or '48_' in a) and ('50_' in b or '55_' in b or '49b' in b)) or \
                            (('47b' in b or '48_' in b) and ('50_' in a or '55_' in a or '49b' in a)) or \
                            ({a[:3], b[:3]} <= {'54_', '55_'}) or ('NEMA17' in a and '56_' in b) or ('NEMA17' in b and '56_' in a) or \
                            ('54_' in a and '56_' in b) or ('54_' in b and '56_' in a) or ('55_' in a and '56_' in b) or ('55_' in b and '56_' in a) or \
                            ('reuse_6' in a and 'reuse_6' in b) or ('dummy_' in a and '225_' in b) or ('dummy_' in b and '225_' in a) or ('MG996R' in (a + b) and '213_' in (a + b)) or \
                            ('207_' in (a + b) and ('203_' in (a + b) or '204_' in (a + b))) or ('reuse_6' in (a + b) and ('203_' in (a + b) or '204_' in (a + b))) or \
                            ('202_' in (a + b) and '201_' in (a + b)) or ('214_' in (a + b) and '210_' in (a + b)) or ('49b' in (a + b) and '205_' in (a + b)) or \
                            ('56_' in (a + b) and '206_' in (a + b)) or ('50_' in a and '205_' in b) or ('50_' in b and '205_' in a) or ('203_' in (a + b) and '204_' in (a + b))
    items = [(lab, w, bbox(w)) for lab, w, kind in parts]
    hits, touches = [], []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if not ov(items[i][2], items[j][2]): continue
            v = vol(items[i][1], items[j][1])
            if v > 0.5:
                (touches if expected(items[i][0], items[j][0]) else hits).append([items[i][0], items[j][0], round(v, 1)])
    res['clashes'] = hits; res['by_design_contacts'] = touches
    rot = [(lab, w) for lab, w, kind in parts if kind == 'rot']
    others = [(lab, w, bbox(w)) for lab, w, kind in parts if kind != 'rot' and not lab.startswith(('50_', '55_', '49b', '54_'))]
    dr = {}
    for k in range(12):
        a = 30 * k; hh = []
        for lab, w in rot:
            wr = rotate_drum(w, a); br = bbox(wr)
            for ol, ow, ob in others:
                if ov(br, ob):
                    v = vol(wr, ow)
                    if v > 0.5: hh.append([lab, ol, round(v, 1)])
        dr[a] = hh
    res['drum_turning_12_angles'] = dr
    scd = {lab: w for lab, w, kind in parts}
    ds = {}
    for deg in (0, 30, 60, 90):
        hh = []
        for dl, side in (('214_trapdoor_A', 1), ('214_trapdoor_B', -1)):
            dw = door_at(scd[dl], side, deg)
            for ol in ('220_drop_funnel', '211_landing_ramp_low', '213_servo_saddle', '218_apds9960_mount', '212_slider_post'):
                v = vol(dw, scd[ol])
                if v > 0.5: hh.append([dl, ol, round(v, 1)])
        ds[deg] = hh
    res['scanner_doors_swing'] = ds
    # cross-check against the frame module (posts, top rails, roof tiles, stud ring, C3 clips)
    fr = frame_ref_parts()
    fh = []
    for fl, fw, fk in fr:
        fb = bbox(fw)
        for lab, w, kind in parts:
            if ov(fb, bbox(w)):
                v = vol(fw, w)
                if v > 0.5: fh.append([fl, lab, round(v, 1)])
    res['vs_frame_module'] = {'checked_parts': len(fr), 'clashes': fh}
    res['funnel'] = {'mouth_z': fun_geo[0], 'mouth_r': fun_geo[1], 'cone_bottom_z': fun_geo[2], 'r_in_above_deck': fun_geo[3], 'r_in_tube': fun_geo[4], 'exit_z': FUNNEL_EXIT_Z,
                     'open_door_tip_z': Z_S - HZ - HW, 'mouth_below_open_doors': fun_geo[0] < Z_S - HZ - HW}
    res['chute'] = {'from': [round(v, 1) for v in chA], 'to_inside_drum_rear': [round(v, 1) for v in chC], 'slope_deg': round(ch_angle, 1)}
    # hopper far-wall angle
    u = (HOP_OUT[:2] - np.array(STUD_L)); un = u / np.linalg.norm(u)
    far_rim = np.array(STUD_L) - HOP_TOP_R * un; far_out = HOP_OUT[:2] - HOP_OUT_R * un
    res['hopper'] = {'rim_r': HOP_TOP_R, 'rim_z': HOP_TOP_Z, 'outlet': HOP_OUT.tolist(), 'outlet_r': HOP_OUT_R,
                     'far_wall_deg': round(math.degrees(math.atan2(HOP_TOP_Z - HOP_OUT[2], float(np.linalg.norm(far_out - far_rim)))), 1)}
    res['flow'] = {'drum_axis': 'along +X at y 40, rear at x -150', 'drum_axis_tilt_deg': TILT, 'drum_rear_axis_z': round(DRUM_REAR[2], 1), 'drum_front_axis_z': round(drum_world((0, 0, 180))[2], 1),
                   'drum_top_rear_z': round(DRUM_REAR[2] + 80, 1), 'plate_top_z': round(drum_world((-86, 0, 160))[2], 1), 'roof_underside_z': ROOF_Z,
                   'outlet_window_bottom_z': round(drum_world((68, 0, 175))[2], 1), 'V1_floor_under_window_z': round(_win_floor, 1),
                   'V1_top_start_end_z': [round(V1_A[2], 1), round(V1_B[2], 1)], 'V2_top_start_end_z': [round(V2_A[2], 1), round(V2_B[2], 1)],
                   'V2_end_over_ramp_xy': [V2_B[0], V2_B[1]], 'ramp_top_z': RAMP_TOP, 'tray_slope_deg': TRAY_DEG, 'scanner_floor_Z_S': Z_S,
                   'drop_point': DROP, 'funnel_exit': [DROP[0], DROP[1], FUNNEL_EXIT_Z], 'deck_top': DECK_TOP}
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(parts):
    deck = boxc(-354, 354, -174, 174, 300, 312).cut(cyl((DROP[0], DROP[1], 290), (0, 0, 1), 28, 30))
    items = [(w, col_of(lab, kind), 1.0) for lab, w, kind in parts]
    fr = [(w, COL[k], 0.18) for lab, w, k in frame_ref_parts() if lab.startswith(('114', '130', '100', '101', '102'))]
    base = items + [(deck, (0.88, 0.80, 0.62), 0.6)]
    render(base + fr, HERE / 'still_1_deck_front.png', cam=(-900, 1500, 1000), focal=(0, 0, 450), title='V14 deck (K, interface 5) from the front-left: hopper in the stud, drum along X, V1 -> V2 -> scanner at (240, 0); frame ghosted')
    render(base + fr, HERE / 'still_2_deck_back.png', cam=(600, -1500, 900), focal=(0, 0, 450), title='From the back: electronics trays behind the access panel, drum motor, feed chute')
    render(items + [(deck, (0.88, 0.80, 0.62), 0.5)], HERE / 'still_3_top.png', cam=(0, 0, 2200), focal=(0, 0, 0), up=(0, 1, 0), ortho=330, title='Top view (front at top; +X = front viewer\'s left is on the right here)')
    sc = [(w, col_of(lab, kind), 1.0) for lab, w, kind in parts if lab.startswith(('21', '220', 'MG996R', '204'))]
    render(sc + [(deck.intersect(boxc(100, 354, -120, 120, 300, 312)), (0.88, 0.80, 0.62), 0.5)],
           HERE / 'still_4_scanner.png', cam=(520, 420, 600), focal=(240, 0, 400), title='Scanner (V13 rework) on standoffs over the deck hole; funnel exit z 270')
    hp = [(w, col_of(lab, kind), 1.0) for lab, w, kind in parts if lab.startswith(('201', '202', '47b', '48', '49b', '50', '54', '55', '56', '205', '206', '203', 'NEMA'))]
    render(hp + [(w, COL[k], 0.25) for lab, w, k in frame_ref_parts() if lab.startswith(('114', '130'))], HERE / 'still_5_hopper_drum.png', cam=(-700, 500, 1000), focal=(-120, 40, 520),
           title='Hopper (flange on the stud-ring ledge) -> 47 deg chute -> drum rear; outlet plate over V1')


if __name__ == '__main__':
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ('zones', 'bed_fit', 'by_design_contacts')}, indent=1)[:5000])
    print(sorted(set(r['zones'].values())))
    print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
    # re-pose print STLs for no supports (../tools/auto_orient.py; keeps the designer's pose when it already needs none)
    import subprocess, glob as _g
    _p = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(_p.parent / 'tools' / 'auto_orient.py')] + sorted(_g.glob(str(_p / 'print' / '*.stl'))), check=False)
