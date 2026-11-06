"""V14 module S: scoop slide (CadQuery 2.8). Units mm, machine coordinates.

Printed beam (V-roof, 5 spliced segments) between the side-wall inserts, a
carriage on six 625ZZ rollers (4 on the 45 deg roof faces, 2 under the beam),
GT2 6 mm belt in a horizontal plane on the +Y side driven by BJ's salvaged
NEMA17 (shaft vertical, motor above the belt) with a printed idler and screw
tensioner, KW11-3Z homing switch at -X, a 236 mm wide V-floor scoop that an
MG996R tilts +-35 deg about X, and a printed cable chain on the -Y side.
Run: python3 build_scoop.py
"""
import json, math, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, print_pose, bed_fit, export, bbox, grams, render

SZ = IF['zones']['S_scoop']; Z_MIN, Z_MAX = SZ['z']
SC = IF['scoop']; XC = IF['bins']['x_centers']
X_RECEIVE = SC['receive_pose']['carriage_x']        # 330
BIN_TOP = 160.0                                      # module D bins (top_z_max 176)
BIN_ROW_Y = IF['bins']['row_y_centers']; BIN_FP = IF['bins']['footprint']
WALL_X = IF['side_walls']['beam_mount_inserts']['x_face_abs']   # 500
MOUNT_YZ = IF['side_walls']['beam_mount_inserts']['points_yz']

# ---------- beam ----------
BEAM_Y = 18.0; BEAM_Z0, BEAM_Z1 = 204.0, 234.0; RIDGE_Z = 252.0
SPLITS = [-WALL_X, -290.0, -90.0, 110.0, 310.0, WALL_X]
BRACKET_T = 10.0
TENON = (12.0, 10.0, 30.0)          # half-y, half-z, length
TENON_ZC = 219.0
# ---------- rollers (625ZZ 5x16x5) ----------
BR_OD, BR_W, BR_ID = 16.0, 5.0, 5.0
GAP = 0.05
ROLL_X = 28.0
# ---------- carriage ----------
CAR_X = 40.0; SIDE_Y0, SIDE_Y1 = 20.0, 27.0; CAR_ZB = 188.0; TOP_Z0, TOP_Z1 = 259.0, 265.0
# ---------- belt ----------
BELT_Z = (211.0, 217.0); BELT_IN_Y = 37.0; PULLEY_PD = 12.73
PULLEY_Y = BELT_IN_Y + PULLEY_PD / 2 + 0.7
MOTOR_X = -476.0; IDLER_X = 476.0
# ---------- scoop ----------
AXIS_Z = 287.0; TILT = 35.0
TR_W = 118.0; TR_X = 37.0; TR_T = 2.4; V_DEG = 4.0; WALL_H_C, WALL_H_E = 25.0, 5.0; END_T = 3.0
# ---------- servo MG996R (body only, BJ owns three) ----------
SV_L, SV_W, SV_D = 40.7, 19.7, 36.5; SV_SHAFT_OFF = 10.2; SV_EAR = 7.0
HORN_X = -(TR_X + END_T) - 2.0           # horn plate at x -42
# ---------- cable chain ----------
CH_Y = (-45.0, -32.0); CH_H = 12.0; CH_R = 25.0; CH_PITCH = 20.0
LEDGE_Z = (186.0, 190.0); FIX_X = 0.0
CH_LEN = 490.0
X_MIN_HOME = -412.0

COL = {'beam': (0.55, 0.57, 0.62), 'car': (0.95, 0.55, 0.15), 'tray': (0.98, 0.80, 0.20), 'brg': (0.75, 0.75, 0.78),
       'motor': (0.2, 0.2, 0.22), 'servo': (0.15, 0.25, 0.6), 'belt': (0.1, 0.1, 0.1), 'chain': (0.3, 0.3, 0.32)}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_axis(p, d, h, axis):
    """cylinder centred at p with axis vector."""
    a = cq.Vector(*axis).normalized()
    pl = cq.Plane(origin=cq.Vector(*p) - a * (h / 2), xDir=_perp(a), normal=a)
    return cq.Workplane(pl).circle(d / 2).extrude(h)


def _perp(a):
    t = cq.Vector(1, 0, 0) if abs(a.x) < 0.9 else cq.Vector(0, 1, 0)
    return (t - a * t.dot(a)).normalized()


def beam_profile():
    return [(-BEAM_Y, BEAM_Z0), (BEAM_Y, BEAM_Z0), (BEAM_Y, BEAM_Z1), (0, RIDGE_Z), (-BEAM_Y, BEAM_Z1)]


def beam_segment(i):
    x0, x1 = SPLITS[i], SPLITS[i + 1]
    prof = cq.Workplane('YZ').polyline(beam_profile()).close()
    s = prof.extrude(x1 - x0).translate((x0, 0, 0))
    ty, tz, tl = TENON
    if i < 4:   # tenon out of the +X end
        s = s.union(box(x1, x1 + tl, -ty, ty, TENON_ZC - tz, TENON_ZC + tz))
    if i > 0:   # socket in the -X end
        s = s.cut(box(x0 - 0.1, x0 + tl + 0.3, -ty - 0.2, ty + 0.2, TENON_ZC - tz - 0.2, TENON_ZC + tz + 0.2))
    for xj in ([x1] if i < 4 else []) + ([x0] if i > 0 else []):
        for dx in (10, 20):
            s = s.cut(cyl_axis((xj + dx, 0, TENON_ZC), M3_CLR, 2 * BEAM_Y + 2, (0, 1, 0)))
    if i in (0, 4):   # wall bracket with the four M3 holes on the side-wall inserts
        sgn = -1 if i == 0 else 1
        xw = sgn * WALL_X; xb = xw - sgn * BRACKET_T
        br = box(min(xw, xb), max(xw, xb), -22, 22, Z_MIN, 240)
        for (y, z) in MOUNT_YZ:
            br = br.cut(cyl_axis((xw - sgn * BRACKET_T / 2, y, z), M3_CLR, BRACKET_T + 2, (1, 0, 0)))
            br = br.cut(cyl_axis((xb, y, z), CB_D, 2 * CB_DEPTH, (1, 0, 0)))
        s = s.union(br)
        # motor plate (-X) or idler slide (+X) on the +Y side
        if i == 0:
            mp = box(-497, -452, 15, 66, 219, 225).union(box(min(xw, xb), max(xw, xb), 15, 22, 186, 225)).union(box(-490, -452, 15, 22, 204, 225))
            mp = mp.cut(cyl_axis((MOTOR_X, PULLEY_Y, 222), 23, 10, (0, 0, 1)))
            for dx in (-15.5, 15.5):
                for dy in (-15.5, 15.5):
                    mp = mp.cut(cyl_axis((MOTOR_X + dx, PULLEY_Y + dy, 222), M3_CLR, 10, (0, 0, 1)))
            # homing switch pocket on the motor plate underside (lever toward +X, hit by the belt clamp)
            mp = mp.union(box(-452, -440, 28, 36, 219, 225))
            s = s.union(mp)
        else:
            ip = box(452, 497, 15, 66, 203, 207).union(box(452, 497, 15, 66, 221, 225)).union(box(min(xw, xb), max(xw, xb), 15, 66, 203, 225))
            ip = ip.union(box(452, 490, 15, 22, 203, 225))
            ip = ip.cut(box(IDLER_X - 9, IDLER_X + 9, PULLEY_Y - 3, PULLEY_Y + 3, 200, 230))   # axle slot, tension along X
            ip = ip.union(box(493, 497, PULLEY_Y - 10, PULLEY_Y + 10, 225, 231))
            ip = ip.cut(cyl_axis((495, PULLEY_Y, 228), M3_CLR, 12, (1, 0, 0)))                  # tension screw
            s = s.union(ip)
    return s


def beam_all():
    return [beam_segment(i) for i in range(5)]


# rollers in carriage-local coordinates (x relative to carriage x)
def roller_specs():
    sp = []
    k = 1 / math.sqrt(2)
    for sx in (-ROLL_X, ROLL_X):
        for sy in (-1, 1):
            # contact at the middle of the roof face
            cy, cz = sy * BEAM_Y / 2, (BEAM_Z1 + RIDGE_Z) / 2
            n = (0, sy * k, k)
            c = (sx, cy + n[1] * (BR_OD / 2 + GAP), cz + n[2] * (BR_OD / 2 + GAP))
            sp.append((c, (0, -sy * k, k)))
        sp.append(((sx, 0, BEAM_Z0 - BR_OD / 2 - GAP), (0, 1, 0)))
    return sp


def rollers_local():
    return [cyl_axis(c, BR_OD, BR_W, a).cut(cyl_axis(c, BR_ID, BR_W + 1, a)) for c, a in roller_specs()]


def carriage_local():
    c = box(-CAR_X, CAR_X, -SIDE_Y1, SIDE_Y1, TOP_Z0, TOP_Z1)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * SIDE_Y0, sy * SIDE_Y1))
        c = c.union(box(-CAR_X, CAR_X, y0, y1, CAR_ZB, TOP_Z1))
    # axle bosses: roof rollers (tilted), outward-down of each roller, and the bottom axles
    for (p, a) in roller_specs():
        av = cq.Vector(*a)
        if abs(a[1]) == 1:   # bottom roller: axle across, bosses are the side plates
            c = c.cut(cyl_axis(p, BR_ID, 2 * SIDE_Y1 + 2, a))
            continue
        out = cq.Vector(*p) - av * 9.0 if (av.y * p[1]) < 0 else cq.Vector(*p) + av * 9.0
        c = c.union(cyl_axis(tuple(out), 12, 9, a))
        inner = cq.Vector(*p) + (cq.Vector(*p) - out).normalized() * 6.0
        c = c.cut(cyl_axis(tuple((out + inner) * 0.5), BR_ID, 30, a))
    # clearance around every roller and the beam
    for (p, a) in roller_specs():
        c = c.cut(cyl_axis(p, BR_OD + 2, BR_W + 1.2, a))
    c = c.cut(cq.Workplane('YZ').polyline([(y * 1.0 + (0.8 if y > 0 else -0.8), z) for y, z in
              [(-BEAM_Y, BEAM_Z0 - 0.8), (BEAM_Y, BEAM_Z0 - 0.8), (BEAM_Y, BEAM_Z1), (0, RIDGE_Z + 1.1), (-BEAM_Y, BEAM_Z1)]]).close()
              .extrude(3 * CAR_X).translate((-1.5 * CAR_X, 0, 0)))
    # belt clamp on +Y (two toothed jaws, belt slot 1.6)
    cl = box(-12, 12, SIDE_Y1, BELT_IN_Y + 4, BELT_Z[0] - 5, BELT_Z[1] + 6)
    cl = cl.cut(box(-13, 13, BELT_IN_Y - 0.2, BELT_IN_Y + 1.6, BELT_Z[0] - 0.5, BELT_Z[1] + 0.5))
    cl = cl.cut(box(-1.5, 1.5, SIDE_Y1 - 1, BELT_IN_Y + 5, BELT_Z[0] - 6, BELT_Z[1] + 7))   # split: belt ends meet here
    c = c.union(cl)
    # servo bracket arm (-X) and pivot arm (+X) up to the tilt axis
    c = c.union(box(-62, -CAR_X, -12, 12, TOP_Z0, TOP_Z1))
    z0, z1 = AXIS_Z - SV_SHAFT_OFF, AXIS_Z - SV_SHAFT_OFF + SV_L      # body points up from the shaft
    ear = box(-62, -58, -SV_W / 2 - 1, SV_W / 2 + 1, TOP_Z0, z1 + SV_EAR)
    ear = ear.cut(box(-63, -57, -SV_W / 2 - 0.3, SV_W / 2 + 0.3, z0 - 0.3, z1 + 0.3))
    for zz in (z0 - SV_EAR / 2, z1 + SV_EAR / 2):
        for yy in (-5, 5):
            ear = ear.cut(cyl_axis((-60, yy, zz), 2.0, 6, (1, 0, 0)))
    c = c.union(ear)
    piv = box(TR_X + END_T + 2, TR_X + END_T + 10, -12, 12, TOP_Z0, AXIS_Z + 12)
    piv = piv.cut(cyl_axis((TR_X + END_T + 6, 0, AXIS_Z), BR_OD + 0.1, 8.2, (1, 0, 0)))   # 625 pocket
    c = c.union(piv)
    # chain mount on -Y, upper run arrives from -X at z ~248
    c = c.union(box(-CAR_X - 10, -CAR_X + 10, CH_Y[0], -SIDE_Y1 + 0.01, 238, 254))
    return c


def servo_local():
    top = HORN_X - 6.0
    z0, z1 = AXIS_Z - SV_SHAFT_OFF, AXIS_Z - SV_SHAFT_OFF + SV_L
    body = box(top - SV_D, top, -SV_W / 2, SV_W / 2, z0, z1)
    ears = box(-58, -55.5, -SV_W / 2, SV_W / 2, z0 - SV_EAR, z1 + SV_EAR)
    return body.union(ears)


def tray_local():
    """V floor (4 deg toward the centre line), end walls; tilt axis = X axis through (0, 0, AXIS_Z)."""
    t = math.tan(math.radians(V_DEG))
    pts = [(-TR_W, AXIS_Z + TR_W * t), (0, AXIS_Z), (TR_W, AXIS_Z + TR_W * t),
           (TR_W, AXIS_Z + TR_W * t - TR_T), (0, AXIS_Z - TR_T), (-TR_W, AXIS_Z + TR_W * t - TR_T)]
    fl = cq.Workplane('YZ').polyline(pts).close().extrude(2 * TR_X).translate((-TR_X, 0, 0))
    wall_pts = [(-TR_W, AXIS_Z + TR_W * t - TR_T), (0, AXIS_Z - TR_T), (TR_W, AXIS_Z + TR_W * t - TR_T),
                (TR_W, AXIS_Z + TR_W * t + WALL_H_E), (60, AXIS_Z + 60 * t + WALL_H_C), (-60, AXIS_Z + 60 * t + WALL_H_C),
                (-TR_W, AXIS_Z + TR_W * t + WALL_H_E)]
    for x0 in (-TR_X - END_T, TR_X):
        fl = fl.union(cq.Workplane('YZ').polyline(wall_pts).close().extrude(END_T).translate((x0, 0, 0)))
    # under-floor keel to stiffen it and carry the pivots
    fl = fl.union(box(-TR_X - END_T, TR_X + END_T, -6, 6, AXIS_Z - TR_T - 6, AXIS_Z - TR_T + 0.01))
    # +X stub axle into the 625 (5 mm) and -X horn hub (MG996R 25T horn screws onto 4 M2 holes)
    fl = fl.union(cyl_axis((TR_X + END_T + 4, 0, AXIS_Z), 4.9, 8, (1, 0, 0)))
    hub = cyl_axis((HORN_X + 1.0 - 0.5, 0, AXIS_Z), 24, 3.0, (1, 0, 0))
    for a in range(4):
        r = 7.0; ang = math.radians(45 + 90 * a)
        hub = hub.cut(cyl_axis((HORN_X + 0.5, r * math.cos(ang), AXIS_Z + r * math.sin(ang)), 2.0, 4, (1, 0, 0)))
    fl = fl.union(hub.union(box(HORN_X - 1, -TR_X - END_T + 0.01, -6, 6, AXIS_Z - 8, AXIS_Z + 6)))
    return fl


def rotate_tilt(w, deg):
    return w.rotate((0, 0, AXIS_Z), (1, 0, AXIS_Z), deg)


def chain_envelope(xc):
    """solid envelope of the cable chain for carriage at xc (lower run on the ledge, bend, upper run)."""
    xa = xc - CAR_X - 10
    xb = (FIX_X + xa - CH_LEN + math.pi * CH_R) / 2
    zl = LEDGE_Z[1] + CH_H / 2; zu = zl + 2 * CH_R; zc = zl + CH_R
    lower = box(min(xb, FIX_X), max(xb, FIX_X) + 0.01, CH_Y[0], CH_Y[1], zl - CH_H / 2, zl + CH_H / 2)
    upper = box(min(xb, xa), max(xb, xa) + 0.01, CH_Y[0], CH_Y[1], zu - CH_H / 2, zu + CH_H / 2)
    bend = (cq.Workplane('XZ').center(xb, zc).circle(CH_R + CH_H / 2).circle(CH_R - CH_H / 2)
            .extrude(CH_Y[1] - CH_Y[0]).translate((0, CH_Y[1], 0)))
    bend = bend.intersect(box(xb - CH_R - CH_H, xb, CH_Y[0], CH_Y[1], 0, 400))
    return lower.union(upper).union(bend), xb


def ledge_part(x0, x1):
    l = box(x0, x1, CH_Y[0] - 4, CH_Y[1] + 3, LEDGE_Z[0], LEDGE_Z[1] + 4)
    l = l.cut(box(x0 - 1, x1 + 1, CH_Y[0] - 0.5, CH_Y[1] + 0.5, LEDGE_Z[1], LEDGE_Z[1] + 5))
    for x in (x0 + 20, (x0 + x1) / 2, x1 - 20):
        l = l.cut(cyl_axis((x, (CH_Y[0] + CH_Y[1]) / 2, LEDGE_Z[0] + 2), M3_CLR, 6, (0, 0, 1)))
    return l


def chain_link():
    """pin-jointed link, pitch 20, M3 x 20 screw as pin; bends one way only (stop faces)."""
    w_out, w_in = CH_Y[1] - CH_Y[0], CH_Y[1] - CH_Y[0] - 4.4
    L = box(-4, CH_PITCH + 4, -w_out / 2, w_out / 2, 0, CH_H)
    L = L.cut(box(-5, CH_PITCH + 5, -w_out / 2 + 2, w_out / 2 - 2, 2, CH_H + 1))      # open channel for the cable
    L = L.cut(box(CH_PITCH - 6, CH_PITCH + 5, -w_out / 2 - 1, -w_in / 2 - 0.2, -1, CH_H + 1))   # inner (narrow) end
    L = L.cut(box(CH_PITCH - 6, CH_PITCH + 5, w_in / 2 + 0.2, w_out / 2 + 1, -1, CH_H + 1))
    L = L.union(box(CH_PITCH - 6, CH_PITCH + 4, -w_in / 2, -w_in / 2 + 2, 0, CH_H)).union(box(CH_PITCH - 6, CH_PITCH + 4, w_in / 2 - 2, w_in / 2, 0, CH_H))
    for x in (0, CH_PITCH):
        L = L.cut(cyl_axis((x, 0, CH_H / 2), M3_CLR, w_out + 2, (0, 1, 0)))
    return L


def idler_part():
    """flanged idler, 11 tall, two 625ZZ pressed in from each end against a 1 mm centre lip."""
    i = cyl_axis((0, 0, 5.5), 18, 11, (0, 0, 1)).union(cyl_axis((0, 0, 0.75), 23, 1.5, (0, 0, 1))).union(cyl_axis((0, 0, 10.25), 23, 1.5, (0, 0, 1)))
    i = i.cut(cyl_axis((0, 0, 2.5), 16.05, 5.2, (0, 0, 1))).cut(cyl_axis((0, 0, 8.5), 16.05, 5.2, (0, 0, 1))).cut(cyl_axis((0, 0, 5.5), 12, 12, (0, 0, 1)))
    return i


def idler_block():
    """slides on the top plate of the +X bracket; the M3 tension screw pulls it toward +X."""
    b = box(IDLER_X - 9, IDLER_X + 9, PULLEY_Y - 10, PULLEY_Y + 10, 225.2, 231)
    b = b.cut(cyl_axis((IDLER_X, PULLEY_Y, 228), 5.3, 10, (0, 0, 1)))
    b = b.cut(cyl_axis((IDLER_X + 9, PULLEY_Y, 228), INSERT_D, 2 * INSERT_DEPTH, (1, 0, 0)))
    return b


def motor_dummy():
    m = box(MOTOR_X - 21, MOTOR_X + 21, PULLEY_Y - 21, PULLEY_Y + 21, 225, 273)
    return m.union(cyl_axis((MOTOR_X, PULLEY_Y, 214), 16, 7, (0, 0, 1)))


def belt_dummy(xc):
    runs = box(MOTOR_X, IDLER_X, BELT_IN_Y, BELT_IN_Y + 1.4, *BELT_Z)
    runs = runs.union(box(MOTOR_X, IDLER_X, BELT_IN_Y + PULLEY_PD + 1.4 - 1.4, BELT_IN_Y + PULLEY_PD + 1.4, *BELT_Z))
    return runs.cut(box(xc - 1.5, xc + 1.5, BELT_IN_Y - 1, BELT_IN_Y + 2, 200, 230))


def poses():
    p = [('receive', X_RECEIVE, 0.0), ('home', X_MIN_HOME, 0.0)]
    for i, x in enumerate(XC):
        p.append((f'dump_front_{i}', x, -TILT))
        p.append((f'dump_back_{i}', x, TILT))
    return p


def moving_at(xc, tilt):
    car = carriage_local().translate((xc, 0, 0))
    rl = [r.translate((xc, 0, 0)) for r in rollers_local()]
    sv = servo_local().translate((xc, 0, 0))
    tr = rotate_tilt(tray_local(), tilt).translate((xc, 0, 0))
    ch, xb = chain_envelope(xc)
    return {'carriage': car, 'rollers': rl, 'servo': sv, 'tray': tr, 'chain': ch}


def brick_landing(xc, tilt):
    """lip point of the downhill side and the brick's crossing of the bin top plane for mu 0 .. 0.45."""
    sgn = 1 if tilt < 0 else -1
    t = math.tan(math.radians(V_DEG)); th = math.radians(abs(tilt))
    z0 = TR_W * t
    ly = sgn * (TR_W * math.cos(th) + z0 * math.sin(th))
    lz = AXIS_Z - TR_W * math.sin(th) + z0 * math.cos(th) + 8.0     # +8: brick centre above the floor
    slope = th - math.radians(V_DEG)
    out = []
    for mu in (0.0, 0.3, 0.45):
        a = 9.81 * (math.sin(slope) - mu * math.cos(slope))
        if a <= 0:
            out.append({'mu': mu, 'slides': False}); continue
        v = math.sqrt(2 * a * TR_W / 1000)
        vy, vz = v * math.cos(slope), -v * math.sin(slope)
        dz = (lz - BIN_TOP) / 1000
        tt = (vz + math.sqrt(vz * vz + 2 * 9.81 * dz)) / 9.81
        y_cross = ly + sgn * vy * tt * 1000
        row = BIN_ROW_Y[1] if sgn > 0 else BIN_ROW_Y[0]
        inner0, inner1 = row - BIN_FP[1] / 2 + 2.0, row + BIN_FP[1] / 2 - 2.0 - 2.4
        if sgn < 0: inner0, inner1 = row - BIN_FP[1] / 2 + 2.0 + 2.4, row + BIN_FP[1] / 2 - 2.0
        out.append({'mu': mu, 'slides': True, 'y_at_bin_top': round(y_cross, 1),
                    'in_bin_opening': inner0 <= y_cross <= inner1})
    return {'lip_y': round(ly, 1), 'lip_z': round(lz - 8.0, 1), 'lip_ok': abs(ly) >= 95 and lz - 8.0 >= Z_MIN, 'drops': out}


def solid_min_z(w):
    return bbox(w)[2]


def clash(a, b):
    ba, bb_ = bbox(a), bbox(b)
    if ba[3] <= bb_[0] or bb_[3] <= ba[0] or ba[4] <= bb_[1] or bb_[4] <= ba[1] or ba[5] <= bb_[2] or bb_[5] <= ba[2]:
        return 0.0
    v = a.intersect(b)
    return round(v.val().Volume(), 2) if v.vals() else 0.0


def main():
    world = HERE / 'world'; prn = HERE / 'print'
    beams = beam_all()
    fixed = {f'180_beam_seg_{i+1}': b for i, b in enumerate(beams)}
    fixed['186_idler_block'] = idler_block()
    fixed['187_idler'] = idler_part().translate((IDLER_X, PULLEY_Y, 208.5))
    fixed['189_ledge_1'] = ledge_part(-450, -220); fixed['189_ledge_2'] = ledge_part(-220, 10)
    dummies = {'motor_NEMA17': motor_dummy()}
    # --- checks ---
    res = {'poses': {}, 'bed_fit': {}}
    D_bins = []
    try:
        dw = sorted((HERE.parent / 'drawer' / 'world').glob('*155_bin_*.step')) + sorted((HERE.parent / 'drawer' / 'world').glob('*15[34]_face_*[0-9].step'))
        D_bins = [cq.importers.importStep(str(p)) for p in dw]
    except Exception as e:
        res['drawer_import_error'] = str(e)
    for name, xc, tilt in poses():
        mv = moving_at(xc, tilt)
        parts = [('carriage', mv['carriage']), ('servo', mv['servo']), ('tray', mv['tray']), ('chain', mv['chain'])] + [(f'roller_{k}', r) for k, r in enumerate(mv['rollers'])]
        zmin = min(solid_min_z(s) for _, s in parts)
        bbs = [bbox(s) for _, s in parts]
        zmax = max(b[5] for b in bbs)
        inside = all(SZ['x'][0] <= b[0] and b[3] <= SZ['x'][1] and SZ['y'][0] <= b[1] and b[4] <= SZ['y'][1] for b in bbs)
        hits = []
        fixed_all = list(fixed.items()) + list(dummies.items()) + [('belt', belt_dummy(xc))]
        for pn, ps in parts:
            for fn, fs in fixed_all:
                if pn == 'chain' and fn.startswith('189_ledge'): continue
                if fn == 'belt' and pn == 'carriage': continue      # the clamp grips the belt by design
                v = clash(ps, fs)
                if v > 0.5: hits.append([pn, fn, v])
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                if {parts[i][0], parts[j][0]} & {'chain'} and 'carriage' in (parts[i][0], parts[j][0]): continue
                if parts[i][0].startswith('roller') and parts[j][0].startswith('roller'): continue
                v = clash(parts[i][1], parts[j][1])
                if v > 0.5: hits.append([parts[i][0], parts[j][0], v])
        dhits = []
        for k, ds in enumerate(D_bins):
            for pn, ps in parts:
                v = clash(ps, ds)
                if v > 0.5: dhits.append([pn, f'drawer_part_{k}', v])
        corner_ok = True
        for b in bbs:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    cx0, cx1 = sorted((sx * 470, sx * 500)); cy0, cy1 = sorted((sy * 210, sy * 240))
                    if not (b[3] <= cx0 or cx1 <= b[0] or b[4] <= cy0 or cy1 <= b[1]): corner_ok = False
        res['poses'][name] = {'carriage_x': xc, 'tilt_deg': tilt, 'min_z': round(zmin, 2), 'max_z': round(zmax, 2),
                              'z_ok': zmin >= Z_MIN - 1e-6 and zmax <= Z_MAX + 1e-6, 'inside_xy': inside, 'corner_columns_clear': corner_ok,
                              'clashes_vs_fixed_or_self': hits, 'clashes_vs_drawers_closed': dhits}
        if tilt != 0:
            res['poses'][name]['brick'] = brick_landing(xc, tilt)
    # receive catch
    tr0 = tray_local()
    res['receive_catch'] = {'funnel_exit': SC['receive_pose']['catch_below'], 'catch_r': SC['receive_pose']['catch_r'],
                            'tray_x_half': TR_X, 'tray_y_half': TR_W, 'tray_floor_z_centre': AXIS_Z,
                            'catch_inside_tray': TR_X >= SC['receive_pose']['catch_r'] + 5 and TR_W >= SC['receive_pose']['catch_r'] + 50,
                            'drop_height_mm': round(SC['receive_pose']['catch_below'][2] - AXIS_Z, 1),
                            'gap_wall_top_to_funnel_mm': round(SC['receive_pose']['catch_below'][2] - bbox(tr0)[5], 1)}
    # --- exports ---
    printable = [(k, v, False, 1, 'PLA') for k, v in fixed.items() if k.startswith(('180', '186', '187', '189'))]
    car0 = carriage_local(); tray0 = tray_local()
    printable += [('181_carriage', car0, False, 1, 'PETG'), ('182_scoop_tray', tray0, False, 1, 'PLA'), ('188_chain_link', chain_link(), False, 26, 'PETG')]
    plist = []
    for name, shp, flip, qty, mat in printable:
        if name.startswith('180'):
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (0, 0, 1), 90), diag=False)   # beam segment lying along Y, roof up
        elif name == '182_scoop_tray':
            bedp, diag = print_pose(shp, diag=False)
        else:
            bedp, diag = print_pose(shp)
        export(bedp, prn / f'{name}_PRINT_{qty}.stl')
        bf = bed_fit(bedp); res['bed_fit'][name] = bf['fits_248']
        plist.append({'label': name, 'part_no': name[:3], 'qty': qty, 'material': mat, **bf, 'diagonal_on_bed': diag,
                      'est_grams_each': grams(shp, density=1.27 if mat == 'PETG' else 1.24)})
    for k, v in fixed.items():
        export(v, world / f'{k}.step')
    mv = moving_at(X_RECEIVE, 0)
    export(mv['carriage'], world / '181_carriage_at_receive.step')
    export(mv['tray'], world / '182_scoop_tray_at_receive.step')
    for k, r in enumerate(mv['rollers']): export(r, world / f'625ZZ_roller_{k+1}_at_receive.step')
    export(mv['servo'], world / 'MG996R_at_receive.step'); export(dummies['motor_NEMA17'], world / 'NEMA17_dummy.step')
    export(mv['chain'], world / '188_chain_envelope_at_receive.step')
    asm = cq.Assembly(name='scoop_module')
    for k, v in fixed.items(): asm.add(v, name=k, color=cq.Color(*COL['beam']))
    asm.add(mv['carriage'], name='181_carriage', color=cq.Color(*COL['car']))
    asm.add(mv['tray'], name='182_scoop_tray', color=cq.Color(*COL['tray']))
    asm.add(mv['servo'], name='MG996R', color=cq.Color(*COL['servo']))
    asm.add(dummies['motor_NEMA17'], name='NEMA17', color=cq.Color(*COL['motor']))
    asm.add(mv['chain'], name='chain', color=cq.Color(*COL['chain']))
    for k, r in enumerate(mv['rollers']): asm.add(r, name=f'625ZZ_{k+1}', color=cq.Color(*COL['brg']))
    asm.save(str(world / 'scoop_assembly.step'))
    bought = [
        {'item': '625ZZ bearing 5x16x5', 'qty': 6 + 2 + 1, 'use': '6 carriage rollers, 2 in the idler, 1 tilt pivot'},
        {'item': 'NEMA17 (BJ salvaged, 48 mm, 5 mm shaft)', 'qty': 1, 'use': 'slide drive'},
        {'item': 'GT2 20T pulley, 5 mm bore, 6 mm belt', 'qty': 1, 'use': 'on the NEMA17'},
        {'item': 'GT2 6 mm belt', 'qty': '2 m', 'use': 'loop ~1.95 m'},
        {'item': 'MG996R servo (BJ owns)', 'qty': 1, 'use': 'scoop tilt'},
        {'item': 'KW11-3Z', 'qty': 1, 'use': 'homing at -X'},
        {'item': 'TMC2209', 'qty': 1, 'use': 'slide driver (on the deck electronics tray)'},
        {'item': 'M5 x 25 screw + nyloc', 'qty': 4, 'use': 'roof roller axles'},
        {'item': 'M5 x 60 screw + nyloc', 'qty': 3, 'use': 'bottom roller axles (2), idler axle (1)'},
        {'item': 'M3 x 12 screw + nut', 'qty': 8 + 4 + 6 + 4, 'use': 'beam splices, wall brackets, ledge, motor'},
        {'item': 'M3 x 20 screw + nut', 'qty': 27, 'use': 'chain pins'},
        {'item': 'M3 x 30 screw', 'qty': 1, 'use': 'belt tensioner'},
        {'item': 'servo extension cable, 3-wire', 'qty': '1.5 m', 'use': 'through the chain to the deck slot L'},
    ]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'S', 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(sum(p['est_grams_each'] * p['qty'] for p in plist))}, indent=1))
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    # --- stills ---
    def scene(xc, tilt, with_bins=True):
        mv = moving_at(xc, tilt)
        it = [(v, COL['beam'], 1) for v in fixed.values()]
        it += [(mv['carriage'], COL['car'], 1), (mv['tray'], COL['tray'], 1), (mv['servo'], COL['servo'], 1), (mv['chain'], COL['chain'], 1),
               (dummies['motor_NEMA17'], COL['motor'], 1), (belt_dummy(xc), COL['belt'], 1)]
        it += [(r, COL['brg'], 1) for r in mv['rollers']]
        if with_bins:
            it += [(d, (0.96, 0.87, 0.65), 0.35) for d in D_bins]
        return it
    render(scene(X_RECEIVE, 0), HERE / 'still_1_receive.png', cam=(1300, 1100, 900), focal=(100, 0, 220), title='Scoop slide at receive (x 330), bins shown faint')
    render(scene(XC[1], -TILT), HERE / 'still_2_dump_front.png', cam=(-700, 900, 520), focal=(-290, 60, 240), title='Dump into a front bin (x -290, tilt 35 deg toward +Y)')
    render(scene(XC[6], TILT, False), HERE / 'still_3_carriage_detail.png', cam=(520, -420, 330), focal=(290, 0, 250), title='Carriage: 6 x 625ZZ on the V-roof beam, belt clamp, MG996R, chain')
    render(scene(XC[6], TILT), HERE / 'still_4_end_view.png', cam=(1600, 0, 260), focal=(0, 0, 200), title='End view, dump toward the back row', ortho=280)
    return res


if __name__ == '__main__':
    r = main()
    bad = {k: v for k, v in r['poses'].items() if not (v['z_ok'] and v['inside_xy'] and v['corner_columns_clear'] and not v['clashes_vs_fixed_or_self'] and not v['clashes_vs_drawers_closed'])}
    print('bad poses:', json.dumps(bad, indent=1)[:3000])
    print('bricks:', [(k, v['brick']['lip_ok'], [d.get('in_bin_opening') for d in v['brick']['drops']]) for k, v in r['poses'].items() if 'brick' in v][:4])
    print('receive', r['receive_catch']); print('bed', r['bed_fit'])
