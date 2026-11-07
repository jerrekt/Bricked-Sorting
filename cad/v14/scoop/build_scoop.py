"""V14 module S: scoop slide, interface 5.1 (CadQuery 2.8). Machine coordinates (+X = front viewer's left).

Beam: closed PLA box 30 (y) x 50 (z) at y +-15, z 138..188, x +-335, 3 keyed segments (joints at x +-112),
end plates screwed into the 1x2 beam posts (#6, axis x). Carriage: 2 top rollers + 4 side rollers (625ZZ),
PTFE anti-lift hooks under the beam's bottom edges (z 136), nothing below 134. GT2 belt in a horizontal loop
on the +Y side at z 163 (motor at the -X end, shaft up; idler/tensioner at +X), belt clamp on the carriage,
KW11 endstop at -X. Scoop: shallow two-ended cup, pivot z 200 (axis X) on the carriage: flat floor +-65,
lip ramps to y +-88 / +12; MG996R on the -X side, 625ZZ pivot on +X; dump 40 deg. Servo lead as a rolling
loop along the -Y face. Run: python3 build_scoop.py
"""
import json, math, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import IF, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, WOOD_SCREW, FIT, print_pose, bed_fit, export, bbox, grams, hours, render

SZ = IF['zones']['S_scoop']; Z_MIN = SZ['z'][0]            # 134
BM = IF['beam']; BX = BM['span_x']; BY = BM['zone_yz']['y']; BZ = BM['zone_yz']['z']   # +-335, +-15, 138..188
SC = IF['scoop']; X_RECEIVE = SC['receive_pose']['carriage_x']; FUNNEL = SC['receive_pose']['funnel_exit']
XC = IF['bins']['x_centers']; ROWS = IF['bins']['row_y_ranges']; BIN_TOP = IF['bins']['z'][1]
BP = IF['wood']['beam_posts_1x2']
T = 2.4
SEG = [BX[0], -112.0, 112.0, BX[1]]
ROLL_D, ROLL_W = 16.0, 5.0
GAP = 0.05
# carriage
CAR_X = 36.0                        # half length of the roller frame
CAR_TOP_X = 60.0                    # half length of the top plate (carries the pivot towers)
TOWER_X = (46.0, 54.0)              # pivot towers at |x| 46..54 (cup end walls at +-40, crank at -44.5..-40)
TOP_Z = BZ[1] + ROLL_D + GAP + 1    # top plate at 205 .. 208
SIDE_T = 4.0
PIVOT_Z = 222.0                     # cup floor 227 (clears the carriage at 40 deg), keel 219
# belt
PUL_PD = 12.73; BELT_Z = (160.0, 166.0); BELT_Y = 40.0           # inner belt run y (clamp side), outer at BELT_Y + PUL_PD
MOTOR_X = -332.5; IDLER_X = 325.0; PUL_Y = BELT_Y + PUL_PD / 2   # motor body x -353.7..-311.3, outside the cup's reach (-306)
# scoop
FLAT = 65.0; LIP_OUT, LIP_UP = 88.0, 12.0; SC_W = 40.0; SC_T = 2.0; WALL_H = 14.0
TILT = 40.0
X_HOME = -240.0
# tilt linkage: MG996R behind the beam (y -55..-35), shaft along x in the plane of the cup crank (x -47), parallel 4-bar
SERVO_Y = -105.0; CRANK_R = 28.0; CRANK_X = -43.0; ROD_L = -SERVO_Y   # servo outside the cup's sweep (|y| <= 88)
LEAD_L, LEAD_FIX_X = 400.0, 0.0
COL = {'beam': (0.55, 0.57, 0.62), 'car': (0.95, 0.55, 0.15), 'cup': (0.98, 0.80, 0.20), 'brg': (0.75, 0.75, 0.78),
       'motor': (0.2, 0.2, 0.22), 'servo': (0.15, 0.25, 0.6), 'belt': (0.1, 0.1, 0.1), 'wood': (0.85, 0.75, 0.55), 'lead': (0.3, 0.3, 0.32)}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(p, d, r, L):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, L, cq.Vector(*p), cq.Vector(*d)))


def cylc(p, axis, r, L):   # centred
    a = cq.Vector(*axis).normalized()
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, L, cq.Vector(*p) - a * (L / 2), a))


# ---------------- beam ----------------
def beam_segment(i):
    x0, x1 = SEG[i], SEG[i + 1]
    s = box(x0, x1, BY[0], BY[1], BZ[0], BZ[1]).cut(box(x0 - 1, x1 + 1, BY[0] + T, BY[1] - T, BZ[0] + T, BZ[1] - T))
    for x in [x0 + 40 + k * 60 for k in range(int((x1 - x0 - 60) // 60) + 1)]:    # internal diaphragms
        s = s.union(box(x - 1.2, x + 1.2, BY[0], BY[1], BZ[0], BZ[1]))
    # keyed joints: a 20 mm plug (inner box, FIT) out of the +x end, socket at the -x end, 2 x M3 through the sides
    if i < 2:
        s = s.union(box(x1, x1 + 20, BY[0] + T + FIT, BY[1] - T - FIT, BZ[0] + T + FIT, BZ[1] - T - FIT).cut(
            box(x1 - 1, x1 + 21, BY[0] + 2 * T + FIT, BY[1] - 2 * T - FIT, BZ[0] + 2 * T + FIT, BZ[1] - 2 * T - FIT)))
        s = s.cut(box(x1 - 1, x1 + 1, BY[0] - 1, BY[1] + 1, BZ[0] - 1, BZ[1] + 1).intersect(box(x1 - 1, x1 + 1, BY[0] + T, BY[1] - T, BZ[0] + T, BZ[1] - T)))
    for xs in ([x1 + 10] if i < 2 else []) + ([x0 + 10] if i > 0 else []):
        s = s.cut(cylc((xs, 0, 163.0), (0, 1, 0), M3_CLR / 2, 40))
    # end plates: 6 mm plate on the beam end, screwed to the post inner face (x = +-335) with 3 x #6 (axis x)
    if i in (0, 2):
        xe = x0 if i == 0 else x1
        pl = box(xe - (0 if i == 0 else 6), xe + (6 if i == 0 else 0), -19, 19, BZ[0] - 20, BZ[1] + 20)
        for z in (BZ[0] - 10, 163.0, BZ[1] + 10):
            pl = pl.cut(cylc((xe + (3 if i == 0 else -3), 0, z), (1, 0, 0), WOOD_SCREW / 2, 8))
            pl = pl.cut(cylc((xe + (6 if i == 0 else -6), 0, z), (1, 0, 0), 3.6, 3))   # #6 head seat
        s = s.union(pl)
    return s


# ---------------- carriage ----------------
def roller_specs():
    """(centre, axis) in carriage-local x (0 = carriage centre). Top pair on the beam top face at y +-8; side rollers
    (vertical axles) against both y faces at z 150 and 176."""
    sp = []
    for sx in (-24.0, 24.0):
        for sy in (-8.0, 8.0):
            sp.append(((sx, sy, BZ[1] + ROLL_D / 2 + GAP), (0, 1, 0)))
    for sx in (-24.0, 24.0):
        for sy in (-1, 1):
            sp.append(((sx, sy * (BY[1] + ROLL_D / 2 + GAP), 163.0), (0, 0, 1)))
    return sp


def rollers_local():
    return [cylc(c, a, ROLL_D / 2, ROLL_W).cut(cylc(c, a, 2.5, ROLL_W + 1)) for c, a in roller_specs()]


def carriage_local():
    """PETG frame: side plates (y +-33..37, z 136..190) with the 4 side-roller axles, PTFE anti-lift hooks under the beam's
    bottom edges, a shelf at z 186..190 out to the side plates, webs at y +-12..16 up to the top plate (z 205..208, y +-14)
    that carries the 2 top-roller axles and the pivot towers (|x| 43..51, 625 pockets at z PIVOT). Belt clamp on +y,
    servo shelf and ear plate on -y, endstop flag at -x."""
    yo = BY[1] + ROLL_D + GAP + 2.0           # side plate inner face 33.05, outer 37.05
    c = box(-CAR_X, CAR_X, -14, 14, TOP_Z, TOP_Z + 3)
    for sy in (-1, 1):
        c = c.union(box(-CAR_X, CAR_X, *sorted((sy * yo, sy * (yo + SIDE_T))), BZ[0] - 2.0, 190.0))               # side plate
        c = c.union(box(-CAR_X, CAR_X, *sorted((sy * (BY[1] - 4.0), sy * (yo + SIDE_T))), BZ[0] - 2.0, BZ[0] - GAP))   # anti-lift hook
        c = c.union(box(-CAR_X, CAR_X, *sorted((sy * 12.0, sy * (yo + SIDE_T))), 186.0, 190.0))                   # shelf
        c = c.union(box(-CAR_X, CAR_X, *sorted((sy * 12.0, sy * 16.0)), 190.0 - 0.01, TOP_Z + 0.01))              # web
    for (p, a) in roller_specs():
        if a[2] == 1:    # vertical axle: bosses above and below the roller from the side plate
            sgn = 1 if p[1] > 0 else -1
            for z0 in (p[2] - ROLL_W / 2 - 6, p[2] + ROLL_W / 2):
                c = c.union(box(p[0] - 6, p[0] + 6, *sorted((p[1] - sgn * 3, sgn * (yo + SIDE_T))), z0, z0 + 6))
            c = c.cut(cylc((p[0], p[1], p[2]), (0, 0, 1), 2.5, 40))
        else:            # top roller: axle along y through the two webs
            c = c.cut(cylc((p[0], 0, p[2]), (0, 1, 0), 2.5, 40))
    for (p, a) in roller_specs():
        c = c.cut(cylc(p, a, ROLL_D / 2 + 1.0, ROLL_W + 1.2))
    c = c.cut(box(-CAR_X - 1, CAR_X + 1, BY[0] - 0.6, BY[1] + 0.6, BZ[0] - 0.6, BZ[1] + 0.6))
    # belt clamp arm on +y (reaches the inner belt run at y BELT_Y), split so the belt ends meet in it
    cl = box(-10, 10, yo + SIDE_T - 0.01, BELT_Y + 4, BELT_Z[0] - 4, BELT_Z[1] + 4)
    cl = cl.cut(box(-11, 11, BELT_Y - 0.2, BELT_Y + 1.6, BELT_Z[0] - 0.5, BELT_Z[1] + 0.5))
    cl = cl.cut(box(-1.5, 1.5, yo + SIDE_T - 1, BELT_Y + 5, BELT_Z[0] - 5, BELT_Z[1] + 5))
    c = c.union(cl)
    # top plate extension and pivot towers (625 pockets, 5.4 deep, coupon-sized), 0.07 clearance for the stub axles
    c = c.union(box(-CAR_TOP_X, CAR_TOP_X, -14, 14, TOP_Z, TOP_Z + 3))
    for sx in (-1, 1):
        tw = box(*sorted((sx * TOWER_X[0], sx * TOWER_X[1])), -12, 12, TOP_Z, PIVOT_Z + 12)
        tw = tw.cut(cylc((sx * (TOWER_X[0] + 4), 0, PIVOT_Z), (1, 0, 0), 8.05, 5.4)).cut(cylc((sx * (TOWER_X[0] + 4), 0, PIVOT_Z), (1, 0, 0), 3.0, 20))
        c = c.union(tw)
    # servo bracket is a separate part (servo_bracket_local), bolted to the -y side plate: 2 x M3 bosses here
    for xx in (-56.0, -48.0):
        c = c.cut(cylc((xx, -yo - SIDE_T + 2, 170.0), (0, 1, 0), M3_CLR / 2, 10))
    # endstop flag on -x, -y side
    c = c.union(box(-CAR_TOP_X - 4, -CAR_TOP_X, -24, -20, TOP_Z - 6, TOP_Z + 3))
    return c


def servo_bracket_local():
    """MG996R mount outside the cup's sweep (y -117..-93): low arm from the -y side plate, post, shelf, ear tabs, back plate."""
    # servo mount, outside the cup's sweep: a low arm (z 150..160) from the -y side plate out to y -117, a post up to the
    # servo shelf at z PIVOT-10.2, ear tabs at both ends of the body and a back plate behind it (U bracket)
    zs = PIVOT_Z - 10.2
    yo = BY[1] + ROLL_D + GAP + 2.0
    c = box(-60.0, -44.0, SERVO_Y - 12, -yo - SIDE_T - 0.2, 150.0, 160.0)
    c = c.union(box(-60.0, -44.0, -yo - SIDE_T - 3.2, -yo - SIDE_T - 0.2, 160.0, 180.0))   # flange on the side plate, 2 x M3
    for xx in (-56.0, -48.0):
        c = c.cut(cylc((xx, -yo - SIDE_T - 1.7, 170.0), (0, 1, 0), M3_CLR / 2, 10))
    c = c.union(box(-60.0, -44.0, SERVO_Y - 12, SERVO_Y + 12, 160.0 - 0.01, zs - 8))
    c = c.union(box(-87.0, -44.0, SERVO_Y - 12, SERVO_Y + 12, zs - 3, zs).cut(box(-58.5, -54.0, -200, 0, zs - 4, zs + 1)))   # shelf, notched for the lower ear
    c = c.union(box(-54.0, -44.0, SERVO_Y - 12, SERVO_Y + 12, zs - 8, zs - 3 + 0.01)).union(box(-60.0, -58.5, SERVO_Y - 12, SERVO_Y + 12, zs - 8, zs - 3 + 0.01))
    for z0 in (zs - 7, zs + 40.7):                                                                   # ear tabs
        tab = box(-60.0, -57.5, SERVO_Y - 12, SERVO_Y + 12, z0, z0 + 7)
        for yy in (SERVO_Y - 5, SERVO_Y + 5):
            tab = tab.cut(cylc((-58.75, yy, z0 + 3.5), (1, 0, 0), 1.6, 6))
        c = c.union(tab)
    c = c.union(box(-87.0, -84.5, SERVO_Y - 12, SERVO_Y + 12, zs - 3, zs + 47.7))                   # back plate
    c = c.union(box(-87.0, -57.5, SERVO_Y - 12, SERVO_Y + 12, zs + 40.7, zs + 47.7))                # top rail (over the body)
    return c


def servo_local():
    """MG996R behind the beam: shaft along x at (CRANK_X - 2, SERVO_Y, PIVOT_Z); body 36.5 deep toward -x, 40.7 up/down
    (shaft 10.2 from the top of the 40.7 side), 19.7 wide in y; ears at the back."""
    xf = CRANK_X - 2.0 - 2.5                 # horn plate 2.5 thick between the body and the crank plane
    body = box(xf - 36.5, xf, SERVO_Y - 19.7 / 2, SERVO_Y + 19.7 / 2, PIVOT_Z - 10.2, PIVOT_Z - 10.2 + 40.7)
    ears = box(xf - 36.5 + 26.5, xf - 36.5 + 29.0, SERVO_Y - 19.7 / 2 - 0.0, SERVO_Y + 19.7 / 2, PIVOT_Z - 10.2 - 7, PIVOT_Z - 10.2 + 40.7 + 7)
    return body.union(ears)


def linkage_local(tilt):
    """horn (r CRANK_R) on the servo and the pushrod to the cup crank; arms point up at rest, rotate with the cup."""
    th = math.radians(tilt)
    def tip(y0):
        return (CRANK_X, y0 - CRANK_R * math.sin(th), PIVOT_Z + CRANK_R * math.cos(th))
    h = tip(SERVO_Y); k = tip(0.0)
    horn = cq.Workplane(obj=cq.Solid.makeCylinder(4, 3, cq.Vector(CRANK_X - 1.5, SERVO_Y, PIVOT_Z), cq.Vector(1, 0, 0)))
    arm = box(0, 3, -4, 4, 0, CRANK_R).rotate((0, 0, 0), (1, 0, 0), -tilt).translate((CRANK_X - 1.5, SERVO_Y, PIVOT_Z))
    rod = box(CRANK_X - 1.0, CRANK_X + 1.0, h[1], k[1], h[2] - 2.5, h[2] + 2.5)
    return horn.union(arm).union(rod)


def cup_local():
    """profile in the YZ plane about the pivot (0, PIVOT_Z): flat floor y +-FLAT at z PIVOT_Z + 5 (floor top), lip ramps to
    (+-LIP_OUT, +LIP_UP); walls WALL_H at the centre tapering to 4 at the lips; floor SC_T thick; x +-SC_W."""
    zf = PIVOT_Z + 5.0
    top = [(-LIP_OUT, zf + LIP_UP), (-FLAT, zf), (FLAT, zf), (LIP_OUT, zf + LIP_UP)]
    bot = [(LIP_OUT, zf + LIP_UP - SC_T), (FLAT, zf - SC_T), (-FLAT, zf - SC_T), (-LIP_OUT, zf + LIP_UP - SC_T)]
    fl = cq.Workplane('YZ').polyline(top + bot).close().extrude(2 * SC_W).translate((-SC_W, 0, 0))
    wall_top = [(-LIP_OUT, zf + LIP_UP + 4), (-FLAT, zf + WALL_H), (FLAT, zf + WALL_H), (LIP_OUT, zf + LIP_UP + 4)]
    for x0 in (-SC_W, SC_W - SC_T):
        fl = fl.union(cq.Workplane('YZ').polyline(wall_top + bot).close().extrude(SC_T).translate((x0, 0, 0)))
    # keel under the floor (stiffness + pivot hubs): 8 wide, from the pivot down 0, up to the floor
    keel = box(-SC_W + 1, SC_W - 1, -4, 4, PIVOT_Z - 3, zf - SC_T + 0.01)
    fl = fl.union(keel)
    # hubs on the end walls at the pivot, 5 mm stub axles into the tower 625s (both sides, 0.5 off the wall)
    for sx in (-1, 1):
        fl = fl.union(cylc((sx * (SC_W + 3.0), 0, PIVOT_Z), (1, 0, 0), 2.45, 7.0))
    # crank lever on the -x end wall (x -46.5 .. -45): r CRANK_R up from the pivot, M3 pin hole for the pushrod
    crank = box(CRANK_X - 1.5, -SC_W + 0.01, -5, 5, PIVOT_Z - 3, PIVOT_Z + CRANK_R + 5)
    crank = crank.cut(cylc((CRANK_X, 0, PIVOT_Z + CRANK_R), (1, 0, 0), 1.6, 10))
    fl = fl.union(crank)
    return fl


def rotate_tilt(w, deg):
    return w.rotate((0, 0, PIVOT_Z), (1, 0, PIVOT_Z), deg)


# ---------------- fixed: motor bracket, idler, endstop, lead ----------------
def motor_bracket():
    """NEMA17 above a plate at z 172..176 (shaft down to the 20T pulley at z 160..166), the plate carried by a saddle over the
    beam top (2 x M3 + nut inside the beam) and a web down the +y face. x -347..-303, y 15..68."""
    b = box(-354.0, -308.0, BY[1] - 0.01, PUL_Y + 22, 172.0, 176.0)
    b = b.cut(cylc((MOTOR_X, PUL_Y, 174), (0, 0, 1), 11.5, 10))
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            b = b.cut(cylc((MOTOR_X + dx, PUL_Y + dy, 174), (0, 0, 1), 1.7, 10))
    b = b.union(box(-328.0, -308.0, BY[1] - 0.01, BY[1] + 3, 172.0, BZ[1] + 4))                   # web on the +y face
    b = b.union(box(-328.0, -308.0, BY[0], BY[1] + 3, BZ[1] - 0.01, BZ[1] + 4))                   # saddle over the beam top
    for dx in (-6, 6):
        b = b.cut(cylc((-318 + dx, 0, BZ[1] + 2), (0, 0, 1), M3_CLR / 2, 12))
    return b


def motor_dummy():
    return box(MOTOR_X - 21.2, MOTOR_X + 21.2, PUL_Y - 21.2, PUL_Y + 21.2, 176.0, 224.0).union(
        cylc((MOTOR_X, PUL_Y, 166), (0, 0, 1), 2.5, 20)).union(cylc((MOTOR_X, PUL_Y, 163), (0, 0, 1), 8.0, 9))   # shaft + 20T pulley


def idler_block():
    """idler on an M5 axle in a slider on the +x end; the slider sits in a channel on the beam's +y face (x 301..334, clear of
    the carriage rollers and the beam post) and an M3 tension screw pulls it toward +x."""
    ch = box(301.0, 334.0, BY[1] - 0.01, BY[1] + 8, 150.0, 176.0).cut(box(300.0, 335.0, BY[1] + 2, BY[1] + 8.1, 154.0, 172.0))
    sl = box(IDLER_X - 20, IDLER_X + 6, BY[1] + 2 + FIT, BY[1] + 8 - FIT, 154.0 + FIT, 172.0 - FIT)
    arm = box(IDLER_X - 6, IDLER_X + 6, BY[1] + 8 - 0.01, PUL_Y + 8, 154.0, 158.0).union(box(IDLER_X - 6, IDLER_X + 6, BY[1] + 8 - 0.01, PUL_Y + 8, 168.0, 172.0))
    sl = sl.union(arm).cut(cylc((IDLER_X, PUL_Y, 163), (0, 0, 1), 2.65, 40))
    ch = ch.union(box(334.0, 340.0, BY[1] + 8, BY[1] + 20, 154.0, 172.0)).cut(cylc((337, BY[1] + 14, 163), (1, 0, 0), M3_CLR / 2, 8))
    sl = sl.cut(cylc((IDLER_X + 6, BY[1] + 5, 163), (1, 0, 0), INSERT_D / 2, 2 * INSERT_DEPTH))
    return ch, sl


def idler_wheel():
    w = cylc((IDLER_X, PUL_Y, 163), (0, 0, 1), 9, 8).union(cylc((IDLER_X, PUL_Y, 163 - 4.75), (0, 0, 1), 11, 1.5)).union(cylc((IDLER_X, PUL_Y, 163 + 4.75), (0, 0, 1), 11, 1.5))
    return w.cut(cylc((IDLER_X, PUL_Y, 163), (0, 0, 1), 8.05, 12))


def endstop_mount():
    """KW11-3Z on the beam top at the -x end, lever toward +x, pressed by the carriage flag at home (x -250 - 70)."""
    x1 = X_HOME - CAR_TOP_X - 6          # -312: switch body ends 6 before the flag at home; on the -y side of the beam top
    m = box(x1 - 14, x1, -30, -16, TOP_Z - 10, TOP_Z + 2)
    m = m.cut(box(x1 - 13, x1 - 1, -26.6, -20.0, TOP_Z - 9, TOP_Z + 3))
    return m.union(box(x1 - 14, x1, -16.01, BY[0] + 0.01, BZ[1] - 6, TOP_Z - 10 + 0.01)).union(box(x1 - 14, x1, BY[0], -10.0, BZ[1] - 0.01, BZ[1] + 4))


def belt_dummy(xc):
    runs = box(MOTOR_X, IDLER_X, BELT_Y, BELT_Y + 1.4, *BELT_Z).union(box(MOTOR_X, IDLER_X, BELT_Y + PUL_PD, BELT_Y + PUL_PD + 1.4, *BELT_Z))
    return runs.cut(box(xc - 1.5, xc + 1.5, BELT_Y - 1, BELT_Y + 2, 150, 180))


def lead_envelope(xc):
    """servo lead as a flat rolling loop on the -y face: fixed end at x -335, moving end at the carriage; r 12 bend."""
    xa = xc - CAR_X; xf = LEAD_FIX_X
    xb = (xa + xf - LEAD_L + math.pi * 12) / 2
    low = box(min(xb, xf), max(xb, xf) + 0.01, BY[0] - 10, BY[0] - 4, 140, 143)
    high = box(min(xb, xa), max(xb, xa) + 0.01, BY[0] - 10, BY[0] - 4, 164, 167)
    bend = cq.Workplane('XZ').center(xb, 153.5).circle(13.5).circle(10.5).extrude(6).translate((0, BY[0] - 4, 0)).intersect(box(xb - 20, xb, -100, 100, 0, 400))
    return low.union(high).union(bend)


# ---------------- poses, checks ----------------
def poses():
    p = [('receive', X_RECEIVE, 0.0), ('home', X_HOME, 0.0)]
    for i, x in enumerate(XC):
        p.append((f'dump_front_{i+1}', x, -TILT)); p.append((f'dump_back_{i+1}', x, TILT))
    return p


def moving_at(xc, tilt):
    return {'carriage': carriage_local().translate((xc, 0, 0)), 'bracket': servo_bracket_local().translate((xc, 0, 0)), 'rollers': [r.translate((xc, 0, 0)) for r in rollers_local()],
            'servo': servo_local().translate((xc, 0, 0)), 'cup': rotate_tilt(cup_local(), tilt).translate((xc, 0, 0)),
            'link': linkage_local(tilt).translate((xc, 0, 0)), 'lead': lead_envelope(xc)}


def brick_landing(tilt):
    """brick starts at the cup centre, slides down the 40 deg floor (FLAT) then the lip ramp, leaves the lip, falls to the bin top."""
    sgn = 1 if tilt < 0 else -1          # dump toward +y (front) when tilt < 0
    th = math.radians(abs(tilt)); ramp = math.atan2(LIP_UP, LIP_OUT - FLAT)
    zf = PIVOT_Z + 5.0
    lip = (sgn * (LIP_OUT * math.cos(th) + LIP_UP * math.sin(th)), PIVOT_Z + 5 - LIP_OUT * math.sin(th) + LIP_UP * math.cos(th))
    out = {'lip_y': round(lip[0], 1), 'lip_z': round(lip[1], 1), 'lip_ok': abs(lip[0]) >= 75 and lip[1] >= 136,
           'floor_surface_deg': abs(tilt), 'lip_ramp_surface_deg': round(math.degrees(th - ramp), 1), 'drops': []}
    row = ROWS['front'] if sgn > 0 else ROWS['back']
    for mu in (0.0, 0.3, 0.45):
        a1 = 9.81 * (math.sin(th) - mu * math.cos(th)); v2 = 2 * a1 * FLAT / 1000
        s2 = th - ramp; a2 = 9.81 * (math.sin(s2) - mu * math.cos(s2)); L2 = math.hypot(LIP_OUT - FLAT, LIP_UP) / 1000
        v2 = v2 + 2 * a2 * L2
        if a1 <= 0 or v2 <= 0:
            out['drops'].append({'mu': mu, 'leaves': False}); continue
        v = math.sqrt(v2); vy, vz = v * math.cos(s2), -v * math.sin(s2)
        dz = (lip[1] - BIN_TOP) / 1000
        tt = (vz + math.sqrt(vz * vz + 2 * 9.81 * dz)) / 9.81
        y = lip[0] + sgn * vy * tt * 1000
        r0, r1 = sorted((abs(row[0]), abs(row[1])))
        out['drops'].append({'mu': mu, 'leaves': True, 'y_at_bin_top': round(y, 1), 'in_row': r0 + 2 < abs(y) < r1 - 4})
    return out


def _ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def vol(a, b):
    v = a.intersect(b); return round(v.val().Volume(), 2) if v.vals() else 0.0


def main():
    world = HERE / 'world'; prn = HERE / 'print'
    beams = [beam_segment(i) for i in range(3)]
    fixed = {f'180_beam_seg_{i+1}': b for i, b in enumerate(beams)}
    fixed['184_motor_bracket'] = motor_bracket()
    ch, sl = idler_block(); fixed['185_idler_channel'] = ch; fixed['186_idler_slider'] = sl; fixed['187_idler_wheel'] = idler_wheel()
    fixed['188_endstop_mount'] = endstop_mount()
    dummies = {'NEMA17': motor_dummy()}
    posts = {f'beam_post_{s}': box(*sorted((s * BP['x_abs'][0], s * BP['x_abs'][1])), BP['y'][0], BP['y'][1], BP['z'][0], BP['z'][1]) for s in (-1, 1)}
    drawers = []
    try:
        for p in sorted((HERE.parent / 'drawer' / 'world').glob('*.step')):
            if 'assembly' in p.name or '_ink' in p.name: continue
            if any(k in p.name for k in ('169_bin', '167_face', '168_face', '170_bar', '166_tray')):
                drawers.append((p.stem, cq.Workplane().add(cq.importers.importStep(str(p)).val())))
    except Exception as e:
        print('drawer import', e)
    res = {'interface': IF['version'], 'poses': {}, 'bed_fit': {}}
    for name, xc, tilt in poses():
        mv = moving_at(xc, tilt)
        parts = [('carriage', mv['carriage']), ('bracket', mv['bracket']), ('servo', mv['servo']), ('cup', mv['cup']), ('link', mv['link']), ('lead', mv['lead'])] + [(f'roller_{k}', r) for k, r in enumerate(mv['rollers'])]
        bbs = [bbox(s) for _, s in parts]
        zmin = min(b[2] for b in bbs); zmax = max(b[5] for b in bbs)
        inside = all(SZ['x'][0] - .01 <= b[0] and b[3] <= SZ['x'][1] + .01 and SZ['y'][0] - .01 <= b[1] and b[4] <= SZ['y'][1] + .01 for b in bbs)
        hits = []
        fixed_all = list(fixed.items()) + list(dummies.items()) + list(posts.items()) + [('belt', belt_dummy(xc))]
        for pn, ps in parts:
            for fn, fs in fixed_all:
                if fn == 'belt' and pn == 'carriage': continue
                if pn == 'lead' and fn.startswith('180'): continue
                if _ov(bbox(ps), bbox(fs)):
                    v = vol(ps, fs)
                    if v > 0.5: hits.append([pn, fn, v])
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                a, b = parts[i], parts[j]
                if a[0].startswith('roller') and b[0].startswith('roller'): continue
                if {a[0], b[0]} == {'carriage', 'lead'} or {a[0], b[0]} <= {'link', 'cup', 'servo'} or {a[0], b[0]} in ({'carriage', 'bracket'}, {'bracket', 'servo'}, {'bracket', 'lead'}): continue
                if _ov(bbox(a[1]), bbox(b[1])):
                    v = vol(a[1], b[1])
                    if v > 0.5: hits.append([a[0], b[0], v])
        dh = []
        for n, s in drawers:
            for pn, ps in parts:
                if _ov(bbox(ps), bbox(s)):
                    v = vol(ps, s)
                    if v > 0.5: dh.append([pn, n, v])
        ko = None
        if name == 'receive':
            kz = cq.Workplane(obj=cq.Solid.makeCylinder(32, 100, cq.Vector(240, 0, 265), cq.Vector(0, 0, 1)))
            ko = sum(vol(ps, kz) for _, ps in parts)
        res['poses'][name] = {'carriage_x': xc, 'tilt_deg': tilt, 'min_z': round(zmin, 2), 'max_z': round(zmax, 2), 'z_ok': zmin >= Z_MIN - 1e-6 and zmax <= SZ['z'][1] + 1e-6,
                              'inside_xy': inside, 'clashes': hits, 'clashes_vs_drawers_closed': dh, 'funnel_keepout_overlap_mm3': ko}
        if tilt != 0: res['poses'][name]['brick'] = brick_landing(tilt)
    cup0 = cup_local()
    res['receive'] = {'cup_floor_z': PIVOT_Z + 5, 'funnel_exit_z': FUNNEL[2], 'drop_mm': FUNNEL[2] - (PIVOT_Z + 5), 'cup_top_z': round(bbox(cup0)[5], 1),
                      'catch_r': SC['receive_pose']['catch_r'], 'cup_half_x': SC_W, 'cup_flat_half_y': FLAT}
    # exports
    for k, v in fixed.items(): export(v, world / f'{k}.step')
    mv = moving_at(X_RECEIVE, 0)
    export(mv['carriage'], world / '181_carriage_at_receive.step'); export(mv['cup'], world / '182_scoop_cup_at_receive.step')
    export(mv['servo'], world / 'MG996R_at_receive.step'); export(dummies['NEMA17'], world / 'NEMA17_dummy.step'); export(mv['lead'], world / 'lead_loop_at_receive.step')
    export(mv['link'], world / '189_horn_and_pushrod_at_receive.step'); export(mv['bracket'], world / '190_servo_bracket_at_receive.step')
    for k, r in enumerate(mv['rollers']): export(r, world / f'625ZZ_{k+1}_at_receive.step')
    asm = cq.Assembly(name='scoop_module')
    for k, v in fixed.items(): asm.add(v, name=k, color=cq.Color(*COL['beam']))
    asm.add(mv['carriage'], name='181_carriage', color=cq.Color(*COL['car'])); asm.add(mv['cup'], name='182_cup', color=cq.Color(*COL['cup']))
    asm.add(mv['servo'], name='MG996R', color=cq.Color(*COL['servo'])); asm.add(dummies['NEMA17'], name='NEMA17', color=cq.Color(*COL['motor']))
    for k, r in enumerate(mv['rollers']): asm.add(r, name=f'625ZZ_{k+1}', color=cq.Color(*COL['brg']))
    asm.save(str(world / 'scoop_assembly.step'))
    printable = [(k, v, 'PLA', 'end/diaphragm face down (box standing on its -x end)' if k.startswith('180') else 'flat') for k, v in fixed.items()]
    printable += [('181_carriage', carriage_local(), 'PETG', 'top plate down (towers up); tree supports only under the belt-clamp arm if the slicer asks'),
                  ('190_servo_bracket', servo_bracket_local(), 'PETG', 'on its +x face (toward the cup)'), ('182_scoop_cup', cup0, 'PLA', 'floor down (keel up)'), ('183_cup_pad_TPU', None, 'TPU 95A', 'flat'),
                  ('189_pushrod', box(0, 45 - 6, -4, 4, 0, 5).cut(cylc((3, 0, 2.5), (0, 0, 1), 1.6, 6)).cut(cylc((36, 0, 2.5), (0, 0, 1), 1.6, 6)), 'PLA', 'flat')]
    plist = []
    for name, shp, mat, face in printable:
        if shp is None:
            pad = box(-SC_W + SC_T, SC_W - SC_T, -FLAT, FLAT, 0, 1.5); shp = pad; face = 'flat'
        if name.startswith('180'):
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (0, 1, 0), 90), diag=False)
        elif name == '181_carriage':
            bedp, diag = print_pose(shp.translate((0, 0, -TOP_Z)), diag=False)
        elif name == '190_servo_bracket':
            bedp, diag = print_pose(shp.rotate((0, 0, 0), (0, 1, 0), 90), diag=False)
        else:
            bedp, diag = print_pose(shp)
        bf = bed_fit(bedp)
        if not bf['fits_248']:
            for ax in ((1, 0, 0), (0, 1, 0)):
                b2, d2 = print_pose(shp.rotate((0, 0, 0), ax, 90))
                if bed_fit(b2)['fits_248']: bedp, diag, bf = b2, d2, bed_fit(b2); break
        export(bedp, prn / f'{name}_PRINT_1.stl')
        g = grams(shp, 1.27 if mat == 'PETG' else 1.1 if 'TPU' in mat else 1.24)
        res['bed_fit'][name] = bf['fits_248']
        plist.append({'label': name, 'part_no': name[:3], 'qty': 1, 'material': mat, 'bed_face': face, **bf, 'diagonal_on_bed': diag, 'est_grams': g, 'est_hours': hours(g)})
    bought = [{'item': '625ZZ', 'qty': 6 + 1 + 1, 'use': '6 carriage rollers, idler, cup pivot'},
              {'item': 'NEMA17 (salvaged) + GT2 20T pulley 5 mm bore', 'qty': 1, 'use': 'drive'},
              {'item': 'GT2 6 mm belt', 'qty': '1.3 m', 'use': 'loop ~1.24 m'}, {'item': 'MG996R (owned)', 'qty': 1, 'use': 'tilt'},
              {'item': 'KW11-3Z', 'qty': 1, 'use': 'endstop'}, {'item': 'TMC2209 (owned)', 'qty': 1, 'use': 'slide driver'},
              {'item': 'M5 x 50 screw + nyloc', 'qty': 2, 'use': 'top roller axles (through both side plates)'},
              {'item': 'M5 x 25 screw + nyloc', 'qty': 5, 'use': 'side roller axles (4), idler axle (1)'},
              {'item': 'M3 x 12 screw + nut', 'qty': 4 + 2 + 2, 'use': 'beam joints, motor bracket to beam, misc'},
              {'item': 'M3 x 30 screw', 'qty': 1, 'use': 'belt tensioner'}, {'item': 'M3 insert', 'qty': 1, 'use': 'tensioner'},
              {'item': '#6 x 3/4 wood screw', 'qty': 6, 'use': 'end plates into the beam posts'},
              {'item': 'M2 x 8 screw', 'qty': 4 + 2, 'use': 'servo horn to hub, endstop'}, {'item': 'PTFE tape', 'qty': 1, 'use': 'anti-lift hooks'},
              {'item': 'servo extension lead 3-wire', 'qty': '1 m', 'use': 'rolling loop to the deck electronics'}]
    tot = sum(p['est_grams'] for p in plist)
    (HERE / 'parts.json').write_text(json.dumps({'module': 'S', 'interface': IF['version'], 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(tot), 'est_total_hours': round(tot / 45.0, 1)}, indent=1))
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    # stills
    def scene(xc, tilt, with_drawers=True):
        mv = moving_at(xc, tilt)
        it = [(v, COL['beam'], 1) for v in fixed.values()] + [(v, COL['wood'], 0.5) for v in posts.values()]
        it += [(mv['carriage'], COL['car'], 1), (mv['bracket'], COL['car'], 1), (mv['cup'], COL['cup'], 1), (mv['servo'], COL['servo'], 1), (mv['link'], COL['brg'], 1), (dummies['NEMA17'], COL['motor'], 1),
               (belt_dummy(xc), COL['belt'], 1), (mv['lead'], COL['lead'], 1)] + [(r, COL['brg'], 1) for r in mv['rollers']]
        if with_drawers: it += [(s, (0.96, 0.87, 0.65), 0.35) for n, s in drawers if '169_bin' in n]
        return it
    render(scene(X_RECEIVE, 0), HERE / 'still_1_receive.png', cam=(900, 800, 650), focal=(60, 0, 170), title='Scoop slide 5.1 at receive (x 240) under the funnel exit (240, 0, 270); bins faint')
    render(scene(XC[1], -TILT), HERE / 'still_2_dump_front.png', cam=(-500, 650, 420), focal=(-190, 60, 180), title='Dump into F7 (x -190): cup tilted 40 deg to +Y, lip at y 75 / z 153')
    render(scene(XC[6], TILT, False), HERE / 'still_3_carriage_detail.png', cam=(420, -320, 330), focal=(190, 0, 190), title='Carriage: 2 top + 4 side 625ZZ on the 30 x 50 box beam, belt clamp, MG996R, pivot')
    render(scene(XC[6], TILT), HERE / 'still_4_end_view.png', cam=(1200, 0, 200), focal=(0, 0, 180), ortho=200, title='End view, dump toward the back row (lip |y| 75, z 153; bins top 126)')
    return res


if __name__ == '__main__':
    r = main()
    bad = {k: v for k, v in r['poses'].items() if not (v['z_ok'] and v['inside_xy'] and not v['clashes'] and not v['clashes_vs_drawers_closed'])}
    print('bad poses:', json.dumps(bad, indent=1)[:3000])
    print('bricks:', {k: (v['brick']['lip_y'], v['brick']['lip_z'], v['brick']['lip_ramp_surface_deg'], [d.get('in_row') for d in v['brick']['drops']]) for k, v in r['poses'].items() if 'brick' in v and k.endswith('_1')})
    print('receive:', r['receive'], 'keepout', r['poses']['receive']['funnel_keepout_overlap_mm3'])
    print('bed fail:', [k for k, v in r['bed_fit'].items() if not v])
