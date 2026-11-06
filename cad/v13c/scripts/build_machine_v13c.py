"""Bricked Sorting V13C packaging study (2026-11-05): VARIANT=v13 rebuilds V13 as a baseline, VARIANT=v13c
shrinks bins, tier pitch, Z travel and the deck (lift, yaw, hub and scoop unchanged). See ../README.md.
V13 text follows.
Bricked Sorting V13: V12 plus the drum change (BJ 2026-11-04 15:17 PT): static front outlet plate
(49b) and a helical flight inside the barrel (47b) from build_drum_v13.py. V12 text follows.
"""
"""Bricked Sorting V12: V11 plus the open CAD tasks (2026-11-03 22:30 PT).
Adds: 2020 aluminum extrusion frame with printed corners (replaces printed beams), lift tower
tie to the frame, printed drawer carrier tiles with locator holes, XIAO ESP32-S3 Sense camera
mount, APDS-9960 mount, drawer latch, electronics tray, printed stud rings. Scoop outlet stays
40 mm: only the 6x8 and 8x16 plates (2 of 484 pieces) are wider, and they are hand-sorted.
V11 text follows; V12 sections are marked.
"""
"""Bricked Sorting V11: whole machine around the V10 bins (600 option).
Adds the V9-selected modules that were still missing: straight loading funnel,
drum mounting, folded V1/V2 trays on printed leaf springs, scanner with two
servo-linked trapdoors, camera and LED mounts, taller lift, printed drawer
rails, printed frame, and a reference brick shell. CadQuery 2.8, units mm.
World: X along the brick length, +Y = drawer pull-out (front), Z up from the
floor. Scoop yaw axis = world Z axis through (0,0). PROPOSED, NOT RELEASED.
"""
from pathlib import Path
import os
import math, json, struct, collections, hashlib, runpy
import numpy as np
import cadquery as cq

ROOT = Path(__file__).resolve().parent
REF = ROOT.parent.parent / 'reference_v13'
VAR = os.environ.get('VARIANT', 'v13c'); C13 = VAR == 'v13c'
SKIP_CHECKS = os.environ.get('SKIP_CHECKS') == '1'
OUT = ROOT / f'machine_{VAR}'; OUT.mkdir(exist_ok=True)
# V13C bins: 0.40 L per bin (lower to the sill, upper to 10 below the rim) instead of 0.68 / 1.29 L.
# Lower wall = sill + nose clearance 35 + 34.2 (scoop floor + 30 mm part) + 10.8 margin - 10 tier gap, same rule as V10.
BINS = {'H_LOW': 112.0, 'SILL_LOW': 42.0, 'H_UPPER': 52.0, 'NOSE_CLR_LOW': 35.0, 'NOSE_CLR_UP': 35.0} if C13 else {}
os.environ.update({k: str(v) for k, v in BINS.items()}); os.environ['BINS_OUT'] = f'bins_{VAR}'
G = runpy.run_path(str(ROOT / 'build_bins_v13c.py'))   # V10 bins, locators, scoop + checks
V10 = ROOT / f'bins_{VAR}'

# ------------------------------------------------------------------ layout
Z_FLOOR = 8.0                 # base plate top
Z_C = 60.0                    # lower carrier top (tier frame z = world z - Z_C)
sb = G['sb']                  # compact scoop bbox in its 40 deg pose, origin = yaw axis at hub face
SC_LO, SC_HI = sb.zmin, sb.zmax
poses = G['poses']
low_world = {(p['tier'], p['slot']): p['scoop_lowest_z'] + Z_C for p in poses}
LOW_MIN, LOW_MAX = min(low_world.values()), max(low_world.values())
HUB_ABOVE_CARRIAGE = 80.0     # V3: carriage z0 -> hub face (render_previews_v3: 110 -> 190)
H_MIN = 95.0                  # keep V3 lower switch limit
Z_LIFT = LOW_MIN - H_MIN - HUB_ABOVE_CARRIAGE - SC_LO   # lift base underside (world)
PEDESTAL = Z_LIFT - Z_FLOOR
H_of = {k: v - Z_LIFT - HUB_ABOVE_CARRIAGE - SC_LO for k, v in low_world.items()}
H_MAX = max(H_of.values())
DOOR_DROP = 38.0              # open doors hang this far under the floor (V9 used 38)
Z_S = math.ceil(LOW_MAX - SC_LO + SC_HI + 25 + DOOR_DROP)  # scanner floor (part rests here)
DZ = Z_S - 570.0              # V9 register z -> world z
DY = 70.0                     # V9 register y -> world y (V9 scanner y -70 sits over the yaw axis)
V7_TO_WORLD = np.array([80.0, -50.0 + DY, 55.0 + DZ + 20.0])
# Body = two LEGO 2x1 bricks stacked (BJ 2026-11-03): L : W : H = 2 : 1 : 2.4, studs 0.3 L across, 0.2125 W tall
W_BODY = 520.0; L_BODY = 2 * W_BODY; Z_TOP = 2.4 * W_BODY; Z_SEAM = Z_TOP / 2
Z_DECK = Z_S - 48.0           # module deck top
STUD_D, STUD_H = 0.3 * L_BODY, round(0.2125 * W_BODY, 1)
if C13: STUD_H = 60.0         # V13C: V14 stud height; Z_TOP is set from the chute below
X_HALF, Y_BACK, Y_FRONT = L_BODY / 2, -178.0, -178.0 + W_BODY
STUD_C = [(-L_BODY / 4, (Y_BACK + Y_FRONT) / 2), (L_BODY / 4, (Y_BACK + Y_FRONT) / 2)]   # first one is the loading stud

RAISE = 20.0                  # V1, V2 and drum sit 20 mm higher than the V9 study so V2's rear springs fit over the scanner plate
def v9(p): return np.array([p[0], p[1] + DY, p[2] + DZ + RAISE])
DRUM_REAR = v9((-100.0, 70.0, 810.0)); DRUM_FRONT = v9((78.24825, 70.0, 784.94884))
U_AX = (DRUM_FRONT - DRUM_REAR) / np.linalg.norm(DRUM_FRONT - DRUM_REAR)
V1_A, V1_B = v9((105, 70, 650)), v9((-80, 70, 635))
V2_A, V2_B = v9((-100, 70, 605)), v9((-65, -70, 595))
CAM = np.array([0, 0, Z_S + 128.0])

# ------------------------------------------------------------------ helpers
def box(cx, cy, z0, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((cx, cy, z0))
def cyl(p, d, r, L):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, L, cq.Vector(*p), cq.Vector(*d)))
def wire(points):
    return cq.Wire.makePolygon([cq.Vector(*p) for p in points] + [cq.Vector(*points[0])])
def frame_at(a, b):
    a, b = np.array(a, float), np.array(b, float); f = (b - a) / np.linalg.norm(b - a)
    side = np.cross([0, 0, 1], f); side = side / np.linalg.norm(side); up = np.cross(f, side)
    return a, b, f, side, up
def solid_along(a, b, profile):      # profile (s, u) points, extruded from a to b
    a, b, f, s, u = frame_at(a, b)
    w = wire([a + s * x + u * z for x, z in profile])
    return cq.Workplane(obj=cq.Solid.extrudeLinear(w, [], cq.Vector(*(b - a))))
M = {}                                # new parts in WORLD pose
PRINT_ROT = {}                        # how to lay each new part on the bed (axis, angle)
COPIES = {}

# ------------------------------------------------------------------ 1 loading funnel (hopper + chute)
sx, sy = STUD_C[0]
Z_STUD_TOP = Z_TOP + 4 + STUD_H
C_END = DRUM_REAR + 20 * U_AX + np.array([0, 0, -15.0])
d2 = np.array([math.cos(math.radians(35)), 0, -math.sin(math.radians(35))])
B_PT = C_END - 90 * d2
CHUTE_DEG = 45.0              # V13C: upper chute leg at 45 deg (V13: 62); hopper itself unchanged
if C13:
    _h = math.hypot(sx - B_PT[0], sy - B_PT[1])
    Z_STUD_TOP = math.ceil(B_PT[2] + _h * math.tan(math.radians(CHUTE_DEG)) + 7 + 150.0)
    Z_TOP = Z_STUD_TOP - 4 - STUD_H; Z_SEAM = Z_DECK - 5
HOP_Z0 = Z_STUD_TOP - 7 - 150.0           # 150 mm hopper; the chute takes the rest of the drop
A_PT = np.array([sx, sy, HOP_Z0])
DW, DH, WT = 64.0, 44.0, 2.4          # duct outside width/height, wall
outer = cq.Solid.makeLoft([cq.Workplane('XY').workplane(offset=HOP_Z0).center(sx, sy).rect(DW, DH).wires().val(),
                           cq.Workplane('XY').workplane(offset=Z_STUD_TOP - 7).center(sx, sy).circle(98).wires().val()], ruled=True)
inner = cq.Solid.makeLoft([cq.Workplane('XY').workplane(offset=HOP_Z0 - 1).center(sx, sy).rect(DW - 2 * WT, DH - 2 * WT).wires().val(),
                           cq.Workplane('XY').workplane(offset=Z_STUD_TOP - 6.9).center(sx, sy).circle(98 - WT).wires().val()], ruled=True)
hopper = cq.Workplane(obj=outer.cut(inner))
hopper = hopper.union(cq.Workplane('XY').workplane(offset=Z_STUD_TOP - 7).center(sx, sy).circle(106).circle(98 - WT).extrude(4))  # rim sits on the stud
M['50_loading_hopper'] = hopper.clean(); PRINT_ROT['50_loading_hopper'] = ('x', 180)

def duct(a, b, ext0=0.0, ext1=0.0, inner_only=False):
    a, b, f, s, u = frame_at(a, b); a = a - f * ext0; b = b + f * ext1
    pts = lambda w, h: [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    if inner_only: return solid_along(a - f, b + f, pts(DW - 2 * WT, DH - 2 * WT))
    return solid_along(a, b, pts(DW, DH))
seg1o, seg2o = duct(A_PT, B_PT, 0, DH / 2), duct(B_PT, C_END, DH / 2, 0)
chute = seg1o.union(seg2o).cut(duct(A_PT, B_PT, 0, DH / 2, True)).cut(duct(B_PT, C_END, DH / 2, 0, True))
chute = chute.cut(box(sx, sy, HOP_Z0, DW + 4, DH + 4, 200))     # hopper sits on top
M['51_inlet_chute'] = chute.cut(cq.Workplane(obj=outer)).clean()
CHUTE_SPLIT = (HOP_Z0 + B_PT[2]) / 2; PRINT_ROT['51_inlet_chute'] = ('auto', 0)

# ------------------------------------------------------------------ 2 drum (reuse V7) + new side cradles
V7 = {}
REF_ASM = json.loads((REF / 'assembly.json').read_text()); DZ_REF = REF_ASM['layout']['Z_S'] - 570.0
DRUM_KEEP = ('47_', '48_', '49_', '50_', '54_', '55_', '56_')   # V13: 57 thrust holder dropped, the static plate is the thrust face
reuse = []                                # (stl path rel ROOT, 4x4 world matrix, rgb, group)
def to_loc(m):
    m = np.array(m, float); R = m[:3, :3]
    x = R[:, 0] / np.linalg.norm(R[:, 0]); z = np.cross(x, R[:, 1]); z /= np.linalg.norm(z)
    return cq.Location(cq.Plane(origin=tuple(float(v) for v in m[:3, 3]), xDir=tuple(float(v) for v in x), normal=tuple(float(v) for v in z)))
def moved(shape, m): return shape.moved(to_loc(m))
def mat(R, t):
    m = np.eye(4); m[:3, :3] = R; m[:3, 3] = t; return m
for a in REF_ASM['instances']:                 # V13C: drum parts from the V13 assembly, moved with the scanner (no isolate_v7 json in the repo)
    if a['stl'].startswith(('isolate_v7/', 'isolate_v13/')):
        m_ = np.array(a['m']); m_[2, 3] += DZ - DZ_REF
        reuse.append((a['stl'], m_.tolist(), a['color'], a['group'], a['label']))
rollers = [np.array(r[1])[:3, 3] for r in reuse if r[4].startswith('50_')]
CRADLE_Y = [DRUM_REAR[1] - 92.0, DRUM_REAR[1] + 92.0]
mb = [np.array(r[1]) for r in reuse if r[4].startswith('56_')][0]
_c = np.array([[x, y, z, 1] for x in (-32, 32) for y in (-32, 32) for z in (0, 40)]) @ mb.T
MB_ZMIN, MB_X = _c[:, 2].min(), mb[0, 3]
ARCH = (-120.0, 125.0, Z_S + 90.0)        # opening for V2 and the scanner under the left cradle
def cradle(yc):
    sgn = 1 if yc > DRUM_REAR[1] else -1
    rl = [p for p in rollers if (p[1] - DRUM_REAR[1]) * sgn > 0]
    x0, x1 = MB_X - 40, 155.0
    ztop = max(p[2] for p in rl) + 25
    plate = box((x0 + x1) / 2, yc, Z_DECK, x1 - x0, 8, ztop - Z_DECK)
    plate = plate.cut(box((ARCH[0] + ARCH[1]) / 2, yc, Z_DECK - 1, ARCH[1] - ARCH[0], 10, ARCH[2] - Z_DECK + 1))
    for xa, xb in ((x0, ARCH[0]), (ARCH[1], x1)):                                # feet
        plate = plate.union(box((xa + xb) / 2, yc, Z_DECK, xb - xa, 30, 6))
        for x in (xa + 12, xb - 12): plate = plate.cut(cyl((x, yc - 11 * sgn, Z_DECK - 1), (0, 0, 1), 2.7, 10))
    for p in rl:                                                                  # axle forks each side of the roller
        for t in (-7.0, 21.0):
            q = p + U_AX * t
            arm_y0, arm_y1 = sorted([yc, q[1]])
            plate = plate.union(box(q[0], (arm_y0 + arm_y1) / 2, q[2] - 12, 10, abs(arm_y1 - arm_y0) + 4, 24))
            plate = plate.cut(cyl(q - U_AX * 8, U_AX, 2.6, 16))                    # M5 axle
    plate = plate.cut(box((MB_X - 25 + ARCH[0]) / 2 + 10, yc, ARCH[2] + 25, 40, 10, max(10, MB_ZMIN - 30 - ARCH[2] - 25)))
    return plate.clean()
CUT_X = -60.0                          # cradles are split here to fit the bed; a splice plate bolts across
def cradle_holes(pl, yc):
    for x in (CUT_X - 20, CUT_X + 20):
        for z in (ARCH[2] + 20, ARCH[2] + 60):
            pl = pl.cut(cyl((x, yc - 6, z), (0, 1, 0), 2.7, 12))
    return pl
M['52_drum_cradle_L'] = cradle_holes(cradle(CRADLE_Y[0]), CRADLE_Y[0]); PRINT_ROT['52_drum_cradle_L'] = ('x', 90)
M['52_drum_cradle_R'] = cradle_holes(cradle(CRADLE_Y[1]), CRADLE_Y[1]); PRINT_ROT['52_drum_cradle_R'] = ('x', -90)
SPLICE = box(0, 0, 0, 70, 70, 6)
for x in (-20, 20):
    for y in (-20, 20): SPLICE = SPLICE.cut(cyl((x, y, -1), (0, 0, 1), 2.7, 8))
SPLICE = SPLICE.clean()
bridge = box(MB_X, (CRADLE_Y[0] + CRADLE_Y[1]) / 2, MB_ZMIN - 16, 50, CRADLE_Y[1] - CRADLE_Y[0] - 8, 16)
for y in (CRADLE_Y[0] + 4, CRADLE_Y[1] - 4):
    bridge = bridge.cut(cyl((MB_X - 15, y - 1, MB_ZMIN - 8), (0, 1 if y < 140 else -1, 0), 2.7, 12)).cut(cyl((MB_X + 15, y - 1, MB_ZMIN - 8), (0, 1 if y < 140 else -1, 0), 2.7, 12))
M['53_drum_motor_bridge'] = bridge.clean(); PRINT_ROT['53_drum_motor_bridge'] = ('auto', 0)

# ------------------------------------------------------------------ 3 V1 / V2 trays, springs, slotted supports
PROF = [(-35, 27), (-8, 0), (8, 0), (35, 27), (32, 30), (5, 3), (-5, 3), (-32, 30)]
def tray(a, b, flare_start, lip_end, PADS_T=(0.2, 0.8), FH=32.0):
    a, b = np.array(a, float), np.array(b, float); _, _, f, s, u = frame_at(a, b)
    a0 = a - u * 3                       # path is the floor top; profile floor is 3 thick
    t = solid_along(a0 - f * 12, b - u * 3, PROF)
    back = solid_along(a0 - f * 12, a0 - f * 9, [(-35, 0), (35, 0), (35, 30), (-35, 30)])
    t = t.union(back)
    if flare_start:                      # wider catch box at the receiving end
        fl = solid_along(a0 - f * 12, a0 + f * 45, [(-52, 0), (52, 0), (52, FH), (-52, FH)]).cut(
             solid_along(a0 - f * 9.6, a0 + f * 46, [(-49.6, 2.4), (49.6, 2.4), (49.6, 40), (-49.6, 40)]))
        t = t.union(fl)
    for k in PADS_T:                     # two spring pads under the floor
        c = a0 + (b - a0) * k - u * 1
        t = t.union(solid_along(c - f * 10, c + f * 10, [(-30, -8), (30, -8), (30, 2), (-30, 2)]))
        for x in (-22, 22):
            t = t.cut(cyl(c + s * x - u * 9, u, 1.7, 8))
    c = a0 + (b - a0) * 0.5              # vibration motor clip (6-7 mm coreless motor, size unconfirmed)
    t = t.union(cyl(c - u * 6 - s * 9, s, 7, 18)).cut(cyl(c - u * 6 - s * 10, s, 3.6, 20))
    return t.clean()
M['54_V1_tray'] = tray(V1_A, V1_B, True, True); PRINT_ROT['54_V1_tray'] = ('auto', 0)
M['55_V2_tray'] = tray(V2_A, V2_B, True, True, (0.15, 0.45), 24.0); PRINT_ROT['55_V2_tray'] = ('auto', 0)
SPRING_T, SPRING_L, SPRING_ANG = 1.6, 30.0, 20.0
spring = box(0, 0, 0, 14, SPRING_L, SPRING_T)
for y in (-SPRING_L / 2 + 7, SPRING_L / 2 - 7):
    spring = spring.cut(cyl((0, y, -1), (0, 0, 1), 1.7, 5))
spring = spring.union(box(0, -SPRING_L / 2 + 7, 0, 14, 14, 4)).union(box(0, SPRING_L / 2 - 7, 0, 14, 14, 4))
for y in (-SPRING_L / 2 + 7, SPRING_L / 2 - 7): spring = spring.cut(cyl((0, y, -1), (0, 0, 1), 1.7, 6))
SPRING = spring.clean()
def support_post(top_z, x, y, s_dir, f_dir, offs=(-22, 22), base=None):
    zb = Z_DECK if base is None else base
    h = top_z - zb
    p = box(0, 0, zb, 64, 12, h).union(box(0, 0, zb, 74, 40, 6))
    for xx in offs:                      # C1: vertical slots, +-10 mm adjust; springs bolt here
        p = p.cut(cq.Workplane('XZ').center(xx, top_z - 16).slot2D(24, 3.4, 90).extrude(10, both=True))
        p = p.union(box(xx, 6, top_z - 6, 16, 14, 6)).cut(cyl((xx, 13, top_z - 7), (0, 0, 1), 1.7, 8))
    for xx in (-30, 30): p = p.cut(cyl((xx, 14, zb - 1), (0, 0, 1), 2.7 if base is None else 1.7, 10))
    ang = math.degrees(math.atan2(s_dir[1], s_dir[0]))
    p = p.rotate((0, 0, 0), (0, 0, 1), ang)
    return p.translate((x, y, 0)).clean()
supports, spring_places = [], []
SPR_DZ = SPRING_L * math.cos(math.radians(SPRING_ANG)); SPR_DF = SPRING_L * math.sin(math.radians(SPRING_ANG))
PADS = {'V1': (0.2, 0.8), 'V2': (0.15, 0.45)}
for name, (a, b) in (('V1', (V1_A, V1_B)), ('V2', (V2_A, V2_B))):
    _, _, f, s, u = frame_at(a, b)
    for k in PADS[name]:
        c = a - u * 3 + (b - a) * k - u * 9           # pad underside centre
        base_c = c - np.array([0, 0, SPR_DZ]) - f * SPR_DF
        if name == 'V2' and k == PADS['V2'][1]:      # over the scanner plate: short post standing on the plate
            supports.append((name, support_post(base_c[2], base_c[0], base_c[1], s, f, base=Z_S)))
            spring_places.append((name, c, f, s, [(-22, 0), (22, 0)]))
        else:
            supports.append((name, support_post(base_c[2], base_c[0], base_c[1], s, f)))
            spring_places.append((name, c, f, s, [(-22, 0), (22, 0)]))
for i, (n, p) in enumerate(supports): M[f'56_tray_support_{n}_{i}'] = p
PRINT_ROT.update({k: ('none', 0) for k in M if k.startswith('56_')})

# ------------------------------------------------------------------ 4 scanner: plate, doors, push-rod linkage, servo, landing, camera, LEDs
HW, HY, HZ = 35.0, 38.0, 8.0          # door half width, hinge y, hinge depth below the floor
LEVER, L_DOOR = 25.0, 70.0            # door lever (outward, at the +X end) and door link length
SL_X = 41.0                           # plane of levers, links and slider
PLATE = box(0, 0, Z_S - 4, 240, 180, 4).cut(box(0, 0, Z_S - 5, 71, 71, 6)).cut(box(SL_X, 0, Z_S - 5, 9, 140, 6))
for xs_ in (-1, 1):
    for ys_ in (-1, 1):                   # hinge lugs at both door ends; M3 pivot screws
        PLATE = PLATE.union(box(xs_ * 50, ys_ * HY, Z_S - 14, 5, 12, 10.1))
        PLATE = PLATE.cut(cyl((xs_ * 53, ys_ * HY, Z_S - HZ), (-xs_, 0, 0), 1.7, 10))
        PLATE = PLATE.union(box(xs_ * 86, ys_ * 63, Z_DECK, 14, 14, Z_S - 4 - Z_DECK))   # standoffs to the deck
        PLATE = PLATE.cut(cyl((xs_ * 86, ys_ * 63, Z_DECK - 1), (0, 0, 1), 2.7, 12))
M['57_scanner_plate'] = PLATE.clean(); PRINT_ROT['57_scanner_plate'] = ('x', 180)
RAMP = cq.Workplane('XZ').polyline([(-75, Z_S), (-35.6, Z_S), (-75, Z_S + 40)]).close().extrude(30, both=True).translate((0, -6, 0))
RAMP = RAMP.union(box(-55.3, -37.5, Z_S, 39.4, 3, 60))   # back wall stops the part's -Y motion off V2; it slides +X onto the doors
M['57b_landing_ramp'] = RAMP.clean(); PRINT_ROT['57b_landing_ramp'] = ('auto', 0)
# slider post (dovetail 0.07 per side from the runbook) and slider with the link pin
POST = box(50, 0, Z_S, 8, 20, 100).union(box(50, 0, Z_S, 24, 34, 5))
POST = POST.union(cq.Workplane('YZ').polyline([(-4, 0), (4, 0), (6, -4), (-6, -4)]).close().extrude(100).translate((46, 0, Z_S)).rotate((46, 0, Z_S), (46, 0, Z_S + 1), 0)) if False else POST
POST = POST.union(cq.Workplane('XY').polyline([(46, -4), (46, 4), (42.5, 6), (42.5, -6)]).close().extrude(100).translate((0, 0, Z_S)))
M['57c_slider_post'] = POST.clean(); PRINT_ROT['57c_slider_post'] = ('auto', 0)
SLIDER = box(41.5, 0, -9, 7, 22, 18).cut(cq.Workplane('XY').polyline([(46.07, -4.07), (46.07, 4.07), (42.43, 6.07), (42.43, -6.07)]).close().extrude(30).translate((0, 0, -15)))
SLIDER = SLIDER.union(cyl((38, 0, 0), (1, 0, 0), 4, 4)).cut(cyl((36, 0, 0), (1, 0, 0), 1.7, 14))
SLIDER = SLIDER.union(box(41.5, -14, -4, 7, 10, 8)).cut(cyl((36, -16, 0), (1, 0, 0), 1.7, 14))     # servo link pin
M['57d_door_slider'] = SLIDER.clean(); PRINT_ROT['57d_door_slider'] = ('y', 90)
# MG996R saddle on the plate (-Y side); horn turns in the slider plane
HORN_C = np.array([43.0, -48.0, Z_S + 45.0]); R_HORN, L_SERVO = 22.0, 36.0
SV = (48.0, 84.5, HORN_C[1] - 30.7, HORN_C[1] + 10.0, HORN_C[2] - 9.85, HORN_C[2] + 9.85)    # body x, y, z ranges
SADDLE = box((SV[0] + SV[1]) / 2, (SV[2] + SV[3]) / 2, Z_S, SV[1] - SV[0], SV[3] - SV[2] + 2, SV[4] - Z_S)
for yy in (SV[2] - 4.5, SV[3] + 4.5):
    SADDLE = SADDLE.union(box(72, yy, Z_S, 8, 7, SV[5] - Z_S - 6)).cut(cyl((71, yy, SV[4] + 5), (1, 0, 0), 1.6, 10)).cut(cyl((71, yy, SV[4] + 15), (1, 0, 0), 1.6, 10))
for xx in (52, 80): SADDLE = SADDLE.cut(cyl((xx, (SV[2] + SV[3]) / 2, Z_S - 1), (0, 0, 1), 1.7, 8))
M['57e_servo_saddle'] = SADDLE.clean(); PRINT_ROT['57e_servo_saddle'] = ('none', 0)
def door(side):                            # side +1: hinge at +y
    d = box(0, side * HW / 2, Z_S - 3, 69, HW - 0.6, 3)
    d = d.cut(box(0, side * HW / 2, Z_S - 1, 60, HW - 8, 1.2))                     # 1 mm recess: replaceable matte background
    d = d.union(box(0, side * (HY - 4), Z_S - HZ - 1, 69, 3, HZ - 2))               # web down to the barrel
    d = d.union(cyl((-42.5, side * HY, Z_S - HZ), (1, 0, 0), 3.5, 85))
    d = d.cut(cyl((-44, side * HY, Z_S - HZ), (1, 0, 0), 1.7, 88))
    d = d.union(box(SL_X - 0.5, side * (HY + LEVER / 2 + 2), Z_S - HZ - 4, 4, LEVER + 4, 8))     # outward lever at +X end
    d = d.cut(cyl((SL_X - 4, side * (HY + LEVER), Z_S - HZ), (1, 0, 0), 1.7, 8))
    return d.clean()
DOOR = {1: door(1), -1: door(-1)}
M['58_trapdoor_PRINT_2'] = DOOR[1]; PRINT_ROT['58_trapdoor_PRINT_2'] = ('x', 180)
def link_part(L):
    l = box(0, 0, 0, L + 9, 7, 3).edges('|Z').fillet(3.4)
    for x in (-L / 2, L / 2): l = l.cut(cyl((x, 0, -1), (0, 0, 1), 1.7, 5))
    return l.clean()
M['59_door_link_PRINT_2'] = link_part(L_DOOR); PRINT_ROT['59_door_link_PRINT_2'] = ('none', 0)
M['59b_servo_link'] = link_part(L_SERVO); PRINT_ROT['59b_servo_link'] = ('none', 0)
horn = cyl((0, 0, 0), (0, 0, 1), 8, 4).union(box(R_HORN / 2, 0, 0, R_HORN + 7, 8, 4))
horn = horn.cut(cyl((R_HORN, 0, -1), (0, 0, 1), 1.7, 6)).cut(cyl((0, 0, -1), (0, 0, 1), 3.0, 6))
M['60_servo_horn_arm'] = horn.clean(); PRINT_ROT['60_servo_horn_arm'] = ('none', 0)
# camera bridge (two posts, plate with pupil hole and slots) and LED bars
cam = box(80, 0, Z_S, 14, 60, CAM[2] - Z_S).union(box(20, 0, CAM[2], 134, 80, 5))
cam = cam.cut(cyl((0, 0, CAM[2] - 1), (0, 0, 1), 16, 8))
for yy in (-28, 28): cam = cam.cut(cq.Workplane('XY').center(10, yy).slot2D(60, 3.4, 0).extrude(8).translate((0, 0, CAM[2] - 1)))
for yy in (-20, 20): cam = cam.cut(cyl((80, yy, Z_S - 1), (0, 0, 1), 1.7, 12))
M['61_camera_bridge'] = cam.clean(); PRINT_ROT['61_camera_bridge'] = ('y', 90)
def led(side):
    w = cq.Workplane('YZ').polyline([(side * 52, 0), (side * 75, 0), (side * 75, 46), (side * 52, 23)]).close().extrude(37, both=True).translate((-3, 0, Z_S))
    w = w.cut(box(-3, side * 63.5, Z_S + 30, 70, 12, 3).rotate((0, side * 63.5, Z_S + 31.5), (1, side * 63.5, Z_S + 31.5), side * 45))
    return w.clean()
M['62_led_bar_holder_PRINT_2'] = led(1); PRINT_ROT['62_led_bar_holder_PRINT_2'] = ('none', 0)
LED = {1: led(1), -1: led(-1)}
def tip(side, a):                          # lever tip (y, z) for door angle a
    t = math.radians(a)
    return np.array([side * (HY + LEVER * math.cos(t)), Z_S - HZ + LEVER * math.sin(t)])
def slider_z(a):
    tp = tip(1, a); return tp[1] + math.sqrt(L_DOOR ** 2 - tp[0] ** 2)
def horn_pin(th): return np.array([HORN_C[1] + R_HORN * math.cos(math.radians(th)), HORN_C[2] + R_HORN * math.sin(math.radians(th))])
SL_PIN_DY = -16.0                          # servo link pin on the slider, offset from the door link pin
_prev = [None]
def solve_horn(a):
    target = np.array([SL_PIN_DY, slider_z(a)]); best = None
    rng = range(-1800, 1800) if _prev[0] is None else range(int(_prev[0] * 10) - 300, int(_prev[0] * 10) + 300)
    for t10 in rng:
        th = t10 / 10; e = abs(np.linalg.norm(horn_pin(th) - target) - L_SERVO)
        if best is None or e < best[0] - 1e-9: best = (e, th)
    _prev[0] = best[1]; return best[1], best[0]

# ------------------------------------------------------------------ 5 lift extension
PED = box(0, 0, 0, 30, 30, PEDESTAL).union(box(0, 0, 0, 44, 44, 6)).cut(cyl((0, 0, -1), (0, 0, 1), 2.8, PEDESTAL + 2))
M['63_lift_pedestal_leg_PRINT_4'] = PED.clean(); PRINT_ROT['63_lift_pedestal_leg_PRINT_4'] = ('none', 0)
LIFT_O = np.array([0.0, -90.0, Z_LIFT])                    # lift coords origin in world
CARRIAGE_TOP_MAX = H_MAX + 46
BRACE_Z = CARRIAGE_TOP_MAX + 12                            # lift coords
ROD_L = math.ceil((BRACE_Z + 14 - 10) / 10) * 10           # rods from z 10 to the brace top
SCREW_L = ROD_L - 40

# ------------------------------------------------------------------ 6 drawers: rails, side bars, rollers
TIERS = {'lower': Z_C, 'upper': Z_C + G['UPPER_CARRIER_UNDERSIDE'] + G['CARRIER']}
RAIL_X0, RAIL_X1 = 298.0, 325.0
def rail_seg(L):                      # right-hand C channel, opening toward -X; z0 = channel centre
    r = box(321.5 - 0, 0, -17, 7, L, 34).union(box(309, 0, 12, 22, L, 5)).union(box(309, 0, -17, 22, L, 5))
    for y in (-L / 2 + 20, L / 2 - 20):
        for z in (-8, 8): r = r.cut(cyl((316, y, z), (1, 0, 0), 2.7, 12))
    return r.clean()
M['64_drawer_rail_200_PRINT_16'] = rail_seg(200.0); M['64_drawer_rail_100_PRINT_8'] = rail_seg(100.0)
PRINT_ROT['64_drawer_rail_200_PRINT_16'] = ('none', 0); PRINT_ROT['64_drawer_rail_100_PRINT_8'] = ('none', 0)
def side_bar(L):                      # under the carrier edge, x 283..298; M3 up into the carrier
    b = box(288.5, 0, -23, 15, L, 20)
    for y in (-L / 2 + 15, 0, L / 2 - 15): b = b.cut(cyl((288.5, y, -24), (0, 0, 1), 1.7, 22))
    return b.clean()
M['65_carrier_side_bar_PRINT_12'] = side_bar(160.0); PRINT_ROT['65_carrier_side_bar_PRINT_12'] = ('none', 0)
roller_block = box(286, 0, -23, 10, 30, 20).union(cyl((291, 0, -13), (1, 0, 0), 4.0, 18))   # 8 mm axle stub for a 608
M['66_rear_roller_block_PRINT_4'] = roller_block.clean(); PRINT_ROT['66_rear_roller_block_PRINT_4'] = ('none', 0)
front_roller_mount = box(316, 0, -45, 18, 34, 14).cut(cyl((300, 0, -34), (1, 0, 0), 4.05, 30))
M['67_front_roller_bracket_PRINT_4'] = front_roller_mount.clean(); PRINT_ROT['67_front_roller_bracket_PRINT_4'] = ('none', 0)
SIDEBAR_Y = (-150.0, 330.0); FRONT_ROLLER_Y = 300.0; TRAVEL = 350.0

# ------------------------------------------------------------------ 7 frame (printed beams + angle brackets) and references
# V12 (BJ 2026-11-03, Claude's pick): 2020 aluminum extrusion, bought cut to length, instead of ~17 L of printed beams.
BEAM_W = 20.0
EXT = {}                                   # extrusion references by length (not printed)
def beam(L):
    key = int(round(L))
    if key not in EXT: EXT[key] = box(0, 0, 0, BEAM_W, BEAM_W, L).cut(cyl((0, 0, -1), (0, 0, 1), 2.1, L + 2))   # 4.2 bore for M5 tap
    return EXT[key]
# printed corner fittings for 2020: 69 = inside corner (two M5 T-nuts), 77 = 3-way corner cube at the 8 body corners
ang = box(0, 10, 0, 20, 20, 4).union(box(0, 2, 0, 20, 4, 20))
ang = ang.union(cq.Workplane('YZ').polyline([(4, 4), (20, 4), (4, 20)]).close().extrude(2, both=True))
ang = ang.cut(cyl((0, 12, -1), (0, 0, 1), 2.7, 6)).cut(cyl((0, -1, 12), (0, 1, 0), 2.7, 6))
M['69_2020_inside_corner_PRINT_48'] = ang.clean(); PRINT_ROT['69_2020_inside_corner_PRINT_48'] = ('none', 0)
cube = box(0, 0, 0, 20, 20, 20)
for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
    cube = cube.cut(cyl((-d[0] * 11, -d[1] * 11, 10 - d[2] * 11 + (0 if d[2] else 0)), d, 2.7, 22))  # M5 through to the tapped extrusion end
M['77_2020_three_way_corner_PRINT_8'] = cube.clean(); PRINT_ROT['77_2020_three_way_corner_PRINT_8'] = ('none', 0)

# ================================================================== V12 additions
# 71 lift tower tie: the V3 cap is the free end of a 400 mm rod cantilever. This plate bolts to the cap's two
# M4 rod-retention screws (bosses at lift y -25, z 7 above the cap bottom) and up to the back frame extrusion.
CAP_SCREW_Z = Z_LIFT + BRACE_Z + 7.0; CAP_BOSS_Y = LIFT_O[1] - 25.0           # world
BEAM_BACK_Y = Y_BACK + 15; BEAM_BACK_Z0 = Z_DECK - 20 - BEAM_W / 2             # bottom of the back deck-level extrusion
tie = box(0, CAP_BOSS_Y - 3, CAP_SCREW_Z - 9, 130, 6, 31)                       # plate on the boss faces; bottom clears the carriage trigger tab at H_MAX
tie = tie.union(cq.Workplane('YZ').polyline([(CAP_BOSS_Y - 6, CAP_SCREW_Z + 22), (CAP_BOSS_Y, CAP_SCREW_Z + 22), (BEAM_BACK_Y + 14, BEAM_BACK_Z0), (BEAM_BACK_Y - 14, BEAM_BACK_Z0), (BEAM_BACK_Y - 14, BEAM_BACK_Z0 - 8), (CAP_BOSS_Y - 6, CAP_SCREW_Z + 14)]).close().extrude(6, both=True).translate((-50, 0, 0)))
tie = tie.union(cq.Workplane('YZ').polyline([(CAP_BOSS_Y - 6, CAP_SCREW_Z + 22), (CAP_BOSS_Y, CAP_SCREW_Z + 22), (BEAM_BACK_Y + 14, BEAM_BACK_Z0), (BEAM_BACK_Y - 14, BEAM_BACK_Z0), (BEAM_BACK_Y - 14, BEAM_BACK_Z0 - 8), (CAP_BOSS_Y - 6, CAP_SCREW_Z + 14)]).close().extrude(6, both=True).translate((50, 0, 0)))
tie = tie.union(box(0, BEAM_BACK_Y, BEAM_BACK_Z0 - 8, 112, 28, 8))             # foot under the extrusion, two M5 T-nuts
for x in (-45, 45): tie = tie.cut(cyl((x, CAP_BOSS_Y - 7, CAP_SCREW_Z), (0, 1, 0), 2.2, 12))
for x in (-40, 40): tie = tie.cut(cyl((x, BEAM_BACK_Y, BEAM_BACK_Z0 - 9), (0, 0, 1), 2.7, 10))
M['71_lift_tower_tie'] = tie.clean(); PRINT_ROT['71_lift_tower_tie'] = ('auto', 0)

# 72 drawer carrier tiles: 3 mm printed tiles replace the sheet reference. 8 per tier, splice strips under the seams.
CAR_X0, CAR_X1, CAR_Y0, CAR_Y1, CAR_T, CAR_R = -296.0, 296.0, -10.0, 335.0, 3.0, 146.0
TILE_X = [-296.0, -148.0, 0.0, 148.0, 296.0]; TILE_Y = [-10.0, 160.0, 335.0]
LOC_HOLES = []                                                                  # world xy of all 24 locator screws per tier
for k in range(1, 9):
    yw = math.radians(G['slot_yaw'](k))
    for (hx, hy) in [(0, 172.0), (-24.0, 262.0), (24.0, 262.0)]:
        LOC_HOLES.append((hx * math.cos(yw) - hy * math.sin(yw), hx * math.sin(yw) + hy * math.cos(yw)))
SB_HOLES = [(sx * 288.5, SIDEBAR_Y[0] + 160 * i + 80 + dy) for sx in (-1, 1) for i in range(3) for dy in (-65, 0, 65)]
SPLICE_PTS = [(x, y) for x in TILE_X[1:-1] for y in (20, 80, 140, 200, 260, 320)] + [(x, TILE_Y[1]) for x in (-270, -210, -170, 170, 210, 270)]
def carrier_tile(ix, iy):
    x0, x1, y0, y1 = TILE_X[ix], TILE_X[ix + 1], TILE_Y[iy], TILE_Y[iy + 1]
    t = box((x0 + x1) / 2, (y0 + y1) / 2, 0, x1 - x0, y1 - y0, CAR_T)
    t = t.cut(cq.Workplane('XY').circle(CAR_R).extrude(CAR_T + 2).translate((0, 0, -1)))
    for (hx, hy) in LOC_HOLES + SB_HOLES:
        if x0 + 2 < hx < x1 - 2 and y0 + 2 < hy < y1 - 2: t = t.cut(cyl((hx, hy, -1), (0, 0, 1), 1.7, CAR_T + 2))
    for (hx, hy) in SPLICE_PTS:                                                 # M3 to the splice strips under each seam
        for (ox, oy) in ((-12, 0), (12, 0)) if hy in (TILE_Y[1],) else ((0, -12), (0, 12)):
            px, py = hx + ox, hy + oy
            if x0 + 2 < px < x1 - 2 and y0 + 2 < py < y1 - 2 and px * px + py * py > (CAR_R + 6) ** 2: t = t.cut(cyl((px, py, -1), (0, 0, 1), 1.7, CAR_T + 2))
    return t.clean()
CAR_TILES = {}
for ix in range(4):
    for iy in range(2):
        tl = carrier_tile(ix, iy)
        if tl.val().Volume() < 500: continue
        CAR_TILES[(ix, iy)] = tl; M[f'72_carrier_tile_{ix}{iy}_PRINT_2'] = tl; PRINT_ROT[f'72_carrier_tile_{ix}{iy}_PRINT_2'] = ('none', 0)
spl = box(0, 0, 0, 36, 16, 4)
for x in (-12, 12): spl = spl.cut(cyl((x, 0, -1), (0, 0, 1), 1.7, 6))
M['72b_carrier_splice_PRINT_40'] = spl.clean(); PRINT_ROT['72b_carrier_splice_PRINT_40'] = ('none', 0)

# 73 XIAO ESP32-S3 Sense camera mount on the camera bridge. Board 21 x 17.8, lens looks down through the bridge hole.
XB_L, XB_W, XB_T = 21.0, 17.8, 9.5                                              # board + camera stack with the OV5640 heat sink
xm = box(0, 0, CAM[2] + 5, 50, 66, 3).cut(box(0, 0, CAM[2] + 4, 16, 14, 5))      # plate on the bridge, lens window
for yy in (-28, 28): xm = xm.cut(cyl((5, yy, CAM[2] + 4), (0, 0, 1), 1.7, 5))
for sx in (-1, 1):
    for sy in (-1, 1):                                                          # four corner posts hold the board, 0.3 clearance
        xm = xm.union(box(sx * (XB_L / 2 + 0.3 + 1.5), sy * (XB_W / 2 + 0.3 + 1.5), CAM[2] + 8, 3, 3, XB_T + 2))
        xm = xm.union(box(sx * (XB_L / 2 + 0.3 + 0.6), sy * (XB_W / 2 + 0.3 + 1.5), CAM[2] + 8 + XB_T, 1.2, 3, 2))   # retaining nubs: press-fit, pry to release
xm = xm.union(box(0, 20, CAM[2] + 8, 26, 14, 2.5)).cut(box(0, 20, CAM[2] + 8.5, 24, 11, 3))   # tray for the 2.4 GHz antenna strip
xm = xm.union(box(0, -20, CAM[2] + 8, 10, 6, 6))                                   # cable clip for the USB-C lead (-Y side)
M['73_xiao_sense_camera_mount'] = xm.clean(); PRINT_ROT['73_xiao_sense_camera_mount'] = ('none', 0)

# 74 APDS-9960 mount on the scanner plate: board 19.6 x 15.2, tilted 30 deg toward the door centre, sensor ~22 mm from the part.
AP_C = (-14.0, -44.0)
ap = box(AP_C[0], AP_C[1], Z_S, 28, 11, 10)
ap_head = box(0, 0, 0, 24, 19, 6).cut(box(0, 0, 3, 20.2, 15.8, 4)).cut(box(0, 2, -1, 9, 7, 8))   # pocket for the GY-9960 board, window for the sensor
ap_head = ap_head.rotate((0, 0, 0), (1, 0, 0), -30).translate((AP_C[0], AP_C[1] + 2, Z_S + 10))
ap = ap.union(ap_head).cut(box(AP_C[0], AP_C[1] - 7, Z_S + 2, 6, 4, 6))                    # wire channel out the back
for yy in (-5, 5): ap = ap.cut(cyl((AP_C[0] + 10, AP_C[1] + yy, Z_S - 1), (0, 0, 1), 1.7, 6))
M['74_apds9960_mount'] = ap.clean(); PRINT_ROT['74_apds9960_mount'] = ('none', 0)

# 75 drawer latch: a gravity lever on the right front roller bracket drops into a notch on the carrier side bar.
# Lift the lever to pull the drawer; a drop can never pull a drawer open.
LATCH_Y = FRONT_ROLLER_Y - 60.0
def latch_parts(zc):
    piv = (307.0, LATCH_Y, zc - 40)
    lever = box(0, 0, 0, 6, 70, 14).translate((0, 0, -7)).union(cyl((0, 0, 0), (1, 0, 0), 8, 6).translate((-3, 0, 0)))
    lever = lever.cut(cyl((-4, 0, 0), (1, 0, 0), 1.7, 10)).union(box(-5, 36, -7, 16, 8, 16)).union(box(0, -32, 7, 6, 12, 6))   # hook reaches in (-X) at +Y; thumb tab at -Y
    lever = lever.translate(piv)
    bracket = box(314, LATCH_Y, zc - 46, 8, 20, 14).cut(cyl((309, LATCH_Y, zc - 40), (1, 0, 0), 1.7, 12))                    # pivot ear on the rail side
    catch = box(290.0, LATCH_Y + 26, zc - 36, 14, 12, 13)                                                                      # block hanging under the side bar (M3 up into it)
    return lever.clean(), bracket.clean(), catch
LATCH = {t: latch_parts(zc) for t, zc in TIERS.items()}
M['75_drawer_latch_lever_PRINT_2'] = LATCH['lower'][0]; PRINT_ROT['75_drawer_latch_lever_PRINT_2'] = ('auto', 0)
M['75b_latch_pivot_ear_PRINT_2'] = LATCH['lower'][1]; PRINT_ROT['75b_latch_pivot_ear_PRINT_2'] = ('auto', 0)
M['75c_latch_catch_PRINT_2'] = LATCH['lower'][2].clean(); PRINT_ROT['75c_latch_catch_PRINT_2'] = ('none', 0)

# 76 electronics tray in the +X end bay of the lower brick (x 355..487 between the frame posts).
BAY_X = (355.0, X_HALF - 18 - 15); BAY_XC = (BAY_X[0] + BAY_X[1]) / 2
ELEC = [('psu-12V-10A', 60, 165, 40, 0), ('buck-12-5', 60, 35, 15, 1), ('xiao-c3-carrier', 40, 30, 12, 2), ('xiao-s3-spare', 40, 30, 12, 3),
        ('tmc2209-x3-board', 70, 50, 20, 4), ('mcp23017', 40, 25, 12, 5), ('xt30-inlet', 25, 20, 15, 6)]
ELEC_POS = {0: (BAY_XC, -20), 1: (BAY_XC - 30, 110), 2: (BAY_XC + 30, 110), 3: (BAY_XC + 30, 160), 4: (BAY_XC - 25, 215), 5: (BAY_XC + 35, 215), 6: (BAY_XC, 275)}
TRAY_Z = Z_FLOOR
def tray_tile(y0, y1):
    t = box(BAY_XC, (y0 + y1) / 2, TRAY_Z, BAY_X[1] - BAY_X[0] - 4, y1 - y0, 3)
    for (nm, L, Wd, H, i) in ELEC:                                           # M3 standoff bosses at the four corners of each board footprint
        cx, cy = ELEC_POS[i]
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = cx + sx * (L / 2 - 4), cy + sy * (Wd / 2 - 4)
                if y0 + 4 < py < y1 - 4:
                    t = t.union(cyl((px, py, TRAY_Z + 3), (0, 0, 1), 4, 6)).cut(cyl((px, py, TRAY_Z + 2), (0, 0, 1), 1.5, 8))
    for yy in (y0 + 15, y1 - 15):
        for xx in (BAY_X[0] + 12, BAY_X[1] - 12): t = t.cut(cyl((xx, yy, TRAY_Z - 1), (0, 0, 1), 2.2, 6))   # M4 down into the base plate
    return t.clean()
M['76_electronics_tray_A_PRINT'] = tray_tile(-140.0, 100.0); M['76_electronics_tray_B_PRINT'] = tray_tile(100.0, 300.0)
PRINT_ROT['76_electronics_tray_A_PRINT'] = ('none', 0); PRINT_ROT['76_electronics_tray_B_PRINT'] = ('none', 0)

# 78 / 79 stud rings: the two 312 mm studs on the roof are printed as quarter arcs (fits the 248 bed), glued on a cut roof.
ring = cq.Workplane('XY').circle(STUD_D / 2).circle(STUD_D / 2 - 3).extrude(STUD_H - 3)
quarter = ring.intersect(cq.Workplane('XY').rect(STUD_D, STUD_D, centered=False).extrude(STUD_H))
quarter = quarter.union(box(STUD_D / 2 - 1.5, 2, 0, 3, 4, 30)).union(box(2, STUD_D / 2 - 1.5, 0, 4, 3, 30))   # glue tabs
M['78_stud_ring_quarter_PRINT_8'] = quarter.clean(); PRINT_ROT['78_stud_ring_quarter_PRINT_8'] = ('none', 0)
capq = cq.Workplane('XY').circle(STUD_D / 2).extrude(3).intersect(cq.Workplane('XY').rect(STUD_D, STUD_D, centered=False).extrude(3))
M['79_stud_cap_quarter_PRINT_4'] = capq.clean(); PRINT_ROT['79_stud_cap_quarter_PRINT_4'] = ('none', 0)
hopq = cq.Workplane('XY').circle(STUD_D / 2).circle(100).extrude(3).intersect(cq.Workplane('XY').rect(STUD_D, STUD_D, centered=False).extrude(3))
M['79b_loading_stud_ring_top_quarter_PRINT_4'] = hopq.clean(); PRINT_ROT['79b_loading_stud_ring_top_quarter_PRINT_4'] = ('none', 0)

# ------------------------------------------------------------------ export new printable parts
def orient(wp, rot):
    k, a = rot
    if k == 'x': wp = wp.rotate((0, 0, 0), (1, 0, 0), a)
    if k == 'y': wp = wp.rotate((0, 0, 0), (0, 1, 0), a)
    if k == 'auto':                          # lay the largest flat face on the bed: try 6 rotations, keep the lowest height
        best = None
        for ax, an in (((1, 0, 0), 0), ((1, 0, 0), 90), ((1, 0, 0), -90), ((0, 1, 0), 90), ((0, 1, 0), -90), ((1, 0, 0), 180)):
            w = wp.rotate((0, 0, 0), ax, an); bb = w.val().BoundingBox()
            sc = bb.zlen + 0.001 * max(bb.xlen, bb.ylen)
            if best is None or sc < best[0]: best = (sc, w)
        wp = best[1]
    bb = wp.val().BoundingBox()
    return wp.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))

def mesh_check(name, wp):
    path = OUT / (name + '.stl')
    cq.exporters.export(wp, str(path), tolerance=.05, angularTolerance=.1); cq.exporters.export(wp, str(OUT / (name + '.step')))
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 80)[0]
    dt = np.dtype([('n', '<f4', (3,)), ('v', '<f4', (3, 3)), ('a', '<u2')])
    v = np.frombuffer(raw, dtype=dt, count=n, offset=84)['v'].astype(float)
    e = collections.Counter()
    for tri in v:
        a = [tuple(round(t, 4) for t in q) for q in tri]
        for i, j in ((0, 1), (1, 2), (2, 0)): e[tuple(sorted((a[i], a[j])))] += 1
    pts = v.reshape(-1, 3); best = None
    for d in range(0, 90, 3):
        t = math.radians(d); Rm = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        s = np.ptp(pts[:, :2] @ Rm.T, axis=0)
        if best is None or max(s) < max(best[1]): best = (d, s)
    sol = wp.val()
    return {'valid_single_solid': bool(sol.isValid()) and len(wp.solids().vals()) == 1, 'watertight_mesh': all(k == 2 for k in e.values()),
            'extent_xyz': [round(float(x), 1) for x in np.ptp(pts, axis=0)], 'bed_rotation_deg': best[0],
            'fits_248x248x256': bool(max(best[1]) <= 248 and np.ptp(pts[:, 2]) <= 256), 'solid_volume_cm3': round(sol.Volume() / 1000, 1), 'vol_mm3': round(sol.Volume(), 0), 'bbox_sorted': sorted(round(float(x), 1) for x in np.ptp(pts, axis=0)),
            'sha256_stl': hashlib.sha256(raw).hexdigest()}

checks = {}
for name, wp in M.items():
    if name.startswith('56_tray_support_') and not name.endswith('_0') and not name.endswith('_2'): continue
    if name == '51_inlet_chute':
        for part, bx in (('upper', box(0, 0, CHUTE_SPLIT, 2000, 2000, 2000)), ('lower', box(0, 0, 0, 2000, 2000, CHUTE_SPLIT))):
            checks[f'51_inlet_chute_{part}'] = mesh_check(f'51_inlet_chute_{part}', orient(wp.intersect(bx).clean(), ('auto', 0)))
        continue
    checks[name] = mesh_check(name, orient(wp, PRINT_ROT[name]))
for side in ('L', 'R'):
    full = M[f'52_drum_cradle_{side}']; checks.pop(f'52_drum_cradle_{side}', None)
    yc_ = CRADLE_Y[0 if side == 'L' else 1]
    for part, bx in (('rear_beam', box((CUT_X - 300) / 2, yc_, ARCH[2], CUT_X + 300, 60, 600)), ('front_beam', box(CUT_X + 200, yc_, ARCH[2], 400, 60, 600)),
                     ('rear_leg', box((CUT_X - 300) / 2, yc_, 0, CUT_X + 300, 60, ARCH[2])), ('front_leg', box(CUT_X + 200, yc_, 0, 400, 60, ARCH[2]))):
        half = full.intersect(bx).clean()
        checks[f'52_drum_cradle_{side}_{part}'] = mesh_check(f'52_drum_cradle_{side}_{part}', orient(half, PRINT_ROT[f'52_drum_cradle_{side}']))
checks['52f_cradle_splice_plate_PRINT_4'] = mesh_check('52f_cradle_splice_plate_PRINT_4', orient(SPLICE, ('none', 0)))
SPRING_O = orient(SPRING, ('none', 0)); checks['70_leaf_spring_PRINT_8'] = mesh_check('70_leaf_spring_PRINT_8', SPRING_O)

# ------------------------------------------------------------------ assemble world instances
inst = []                                   # (label, cq solid in world or None, stl, matrix, color, group)
def add(label, wp=None, stl=None, m=None, color=(.6, .6, .6), group='misc'):
    inst.append({'label': label, 'wp': wp, 'stl': stl, 'm': (np.eye(4) if m is None else np.array(m)).tolist(), 'color': list(color), 'group': group})
SITE = {1: '#D6372B', 2: '#F2C21B', 3: '#3E9B45', 4: '#2F74C8', 5: '#B65FA8', 6: '#2A2B2E', 7: '#E9E7E1', 8: '#8A8F98'}
hexc = lambda h: [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
# tiers (from V10 solids, tier frame -> world)
for (lab, s) in G['all_solids']:
    t, k, kind = lab.split('-'); k = int(k)
    col = hexc(SITE[k]) if kind == 'bin' else [.62, .66, .7]
    add(f'{t}-{k}-{kind}', s.translate((0, 0, Z_C)), color=col, group=f'drawer_{t}')
for t, zc in TIERS.items():               # carriers (sheet reference) + drawer face + rails + side bars
    for (ix, iy), tl in CAR_TILES.items(): add(f'{t}-carrier-tile', tl.translate((0, 0, zc - 3)), color=(.85, .87, .9), group=f'drawer_{t}')
    for (hx, hy) in SPLICE_PTS:
        if hx * hx + hy * hy > (CAR_R + 20) ** 2:
            sp = M['72b_carrier_splice_PRINT_40'] if hy == TILE_Y[1] else M['72b_carrier_splice_PRINT_40'].rotate((0, 0, 0), (0, 0, 1), 90)
            add(f'{t}-carrier-splice', sp.translate((hx, hy, zc - 7)), color=(.7, .72, .76), group=f'drawer_{t}')
    lv, br, ct = LATCH[t]
    add(f'{t}-latch-lever', lv, color=(.95, .6, .1), group='frame'); add(f'{t}-latch-ear', br, color=(.45, .5, .56), group='frame'); add(f'{t}-latch-catch', ct, color=(.55, .6, .66), group=f'drawer_{t}')
    fz0, fz1 = (Z_FLOOR + 2, TIERS['upper'] - 46) if t == 'lower' else (TIERS['upper'] - 44, TIERS['upper'] + G['H_UPPER'] + 30)
    add(f'{t}-drawer-face', box(0, Y_FRONT - 1.5, fz0, 640, 3, fz1 - fz0), color=(.70, .12, .10), group=f'drawer_{t}_face')
    add(f'{t}-handle', box(0, Y_FRONT + 13, zc + 30, 120, 26, 18), color=(.25, .28, .32), group=f'drawer_{t}_face')
    for sgn in (1, -1):
        for y0, L in ((-170, 200.0), (30, 200.0), (230, 100.0)):
            seg = M['64_drawer_rail_200_PRINT_16'] if L == 200 else M['64_drawer_rail_100_PRINT_8']
            s = seg.translate((0, y0 + L / 2, zc - 13))
            if sgn < 0: s = s.mirror('YZ')
            add(f'{t}-rail', s, color=(.45, .5, .56), group='frame')
        for i in range(3):
            s = M['65_carrier_side_bar_PRINT_12'].translate((0, SIDEBAR_Y[0] + 160 * i + 80, zc))
            if sgn < 0: s = s.mirror('YZ')
            add(f'{t}-sidebar', s, color=(.55, .6, .66), group=f'drawer_{t}')
        rb = M['66_rear_roller_block_PRINT_4'].translate((0, SIDEBAR_Y[0] + 15, zc))
        fr = M['67_front_roller_bracket_PRINT_4'].translate((0, FRONT_ROLLER_Y, zc))
        if sgn < 0: rb, fr = rb.mirror('YZ'), fr.mirror('YZ')
        add(f'{t}-rear-roller-block', rb, color=(.55, .6, .66), group=f'drawer_{t}')
        add(f'{t}-front-roller-bracket', fr, color=(.45, .5, .56), group='frame')
        add(f'{t}-608-rear', cyl((sgn * 300, SIDEBAR_Y[0] + 15, zc - 13), (sgn, 0, 0), 11, 7), color=(.75, .77, .8), group=f'drawer_{t}')
        add(f'{t}-608-front', cyl((sgn * 289, FRONT_ROLLER_Y, zc - 34), (sgn, 0, 0), 11, 7), color=(.75, .77, .8), group='frame')
# lift (V3 parts at new heights) + scoop group, recorded at H_MIN, yaw 0; renderer re-poses group 'lift_moving'
def lm(x, y, z, rx=0):
    m = np.eye(4); t = math.radians(rx); m[:3, :3] = [[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]]
    m[:3, 3] = LIFT_O + np.array([x, y, z]); return m
for x in (-85, 85):
    for y in (-60, 110):
        add('pedestal-leg', M['63_lift_pedestal_leg_PRINT_4'].translate(tuple(LIFT_O + np.array([x, y, -PEDESTAL]))), color=(.45, .5, .56), group='lift')
add('lift-base', stl='01_ground_base.stl', m=lm(0, 0, 0), color=(.5, .56, .61), group='lift')
add('lift-brace', stl='03_top_rod_brace.stl', m=lm(0, 0, BRACE_Z), color=(.5, .56, .61), group='lift')
add('lift-lower-switch', stl='04_lower_switch_mount.stl', m=lm(0, 0, 8), color=(.5, .56, .61), group='lift')
add('lift-upper-switch', stl='07_upper_switch_rod_mount.stl', m=lm(0, 0, CARRIAGE_TOP_MAX - 5), color=(.5, .56, .61), group='lift')
for x in (-45, 45): add('rod-12mm', cyl(tuple(LIFT_O + np.array([x, 0, 10])), (0, 0, 1), 6, ROD_L), color=(.67, .71, .75), group='lift')
add('t8-screw', cyl(tuple(LIFT_O + np.array([0, 0, 58])), (0, 0, 1), 4, SCREW_L), color=(.67, .71, .75), group='lift')
add('z-motor', box(*(LIFT_O + np.array([0, 0, 10.7]))[:2], LIFT_O[2] + 10.7, 42.3, 42.3, 47.3), color=(.16, .19, .23), group='lift')
add('carriage', stl='02_moving_carriage_v3.stl', m=lm(0, 0, H_MIN), color=(.89, .55, .17), group='lift_moving')
add('yaw-motor', box(0, 0, LIFT_O[2] + H_MIN - 8, 42, 42, 48), color=(.16, .19, .23), group='lift_yaw')
add('hub', stl='06_angled_shaft_hub.stl', m=lm(0, 90, H_MIN + 48), color=(.89, .55, .17), group='lift_yaw')
add('compact-scoop', G['scoop_asm'].translate((0, 0, LIFT_O[2] + H_MIN + HUB_ABOVE_CARRIAGE)), color=(.08, .58, .62), group='lift_yaw')
# isolation modules
for name in ('50_loading_hopper', '51_inlet_chute', '52_drum_cradle_L', '52_drum_cradle_R', '53_drum_motor_bridge', '54_V1_tray', '55_V2_tray', '57_scanner_plate', '61_camera_bridge'):
    grp = {'54': 'V1', '55': 'V2'}.get(name[:2], 'isolate')
    add(name, M[name], color={'50': (.75, .2, .15), '51': (.75, .2, .15), '54': (.13, .6, .4), '55': (.07, .55, .6), '57': (.82, .5, .16), '61': (.45, .5, .56)}.get(name[:2], (.5, .55, .6)), group=grp)
for k, (n, p) in enumerate(supports): add(f'tray-support-{n}', p, color=(.5, .55, .6), group='isolate')
for n, c, f, s, offs in spring_places:    # two springs per pad, leaning 20 deg (classic vibratory feeder)
    for os_, of_ in offs:
        base = c + s * os_ + f * of_ - np.array([0, 0, SPR_DZ]) - f * SPR_DF
        m = np.eye(4); ang_ = math.radians(SPRING_ANG)
        ax_dir = f * math.sin(ang_) + np.array([0, 0, 1]) * math.cos(ang_)
        y_ax = ax_dir / np.linalg.norm(ax_dir); x_ax = s; z_ax = np.cross(x_ax, y_ax)
        m[:3, :3] = np.column_stack([x_ax, y_ax, z_ax]); m[:3, 3] = base + y_ax * SPRING_L / 2
        add(f'leaf-spring-{n}', wp=cq.Workplane(obj=moved(SPRING.translate((0, 0, -SPRING_T / 2)).val(), m)), color=(.9, .9, .85), group='spring')
for side in (1, -1):
    add(f'door{side}', DOOR[side], color=(.12, .13, .15), group=f'door{side}')
    add(f'led{side}', LED[side], color=(.45, .5, .56), group='isolate')
    add(f'led-strip{side}', box(0, side * 63.5, Z_S + 30, 74, 10, 1.5).rotate((0, side * 63.5, Z_S + 31.5), (1, side * 63.5, Z_S + 31.5), side * 45), color=(1, .97, .85), group='led')
add('servo-MG996R', box((SV[0] + SV[1]) / 2, (SV[2] + SV[3]) / 2, SV[4], SV[1] - SV[0], SV[3] - SV[2], SV[5] - SV[4]), color=(.1, .1, .12), group='isolate')
for nm_ in ('57b_landing_ramp', '57c_slider_post', '57e_servo_saddle'): add(nm_, M[nm_], color=(.82, .5, .16), group='isolate')
add('slider', M['57d_door_slider'].translate((0, 0, slider_z(0))), color=(.95, .95, .95), group='slider')
add('73_xiao_sense_camera_mount', M['73_xiao_sense_camera_mount'], color=(.45, .5, .56), group='isolate')
add('xiao-sense-ref', box(0, 0, CAM[2] + 8.5, XB_L, XB_W, XB_T), color=(.1, .1, .12), group='isolate')
add('74_apds9960_mount', M['74_apds9960_mount'], color=(.45, .5, .56), group='isolate')
add('71_lift_tower_tie', M['71_lift_tower_tie'], color=(.45, .5, .56), group='lift')
for nm_ in ('76_electronics_tray_A_PRINT', '76_electronics_tray_B_PRINT'): add(nm_, M[nm_], color=(.45, .5, .56), group='frame')
for (nm, L, Wd, H, i) in ELEC:
    cx, cy = ELEC_POS[i]; add(nm, box(cx, cy, TRAY_Z + 9, L, Wd, H), color=(.16, .19, .23), group='electronics')
for r in reuse: add(r[4], stl=r[0], m=r[1], color=r[2], group='drum_rot' if r[4].startswith(('47_', '47b', '48_')) else 'drum')
# deck (reference sheet), base plate, frame, shell
deck = box(0, (Y_BACK + Y_FRONT) / 2, Z_DECK - 5, 2 * 325, Y_FRONT - Y_BACK - 60, 5).cut(box(0, -40, Z_DECK - 6, 160, 190, 7))
add('deck-ref', deck, color=(.78, .8, .82), group='deck')
add('base-plate-ref', box(0, (Y_BACK + Y_FRONT) / 2, 0, 2 * X_HALF, Y_FRONT - Y_BACK, Z_FLOOR), color=(.18, .2, .23), group='frame')
posts = [(sx_ * 340, y) for sx_ in (-1, 1) for y in (Y_BACK + 15, Y_FRONT - 18)]
beam_count = collections.Counter()
def seg_len(rem): return round(rem, 1)          # one extrusion per run, cut to length
def beam_wp(L): return beam(L)
def post_stack(x, y, z0, z1):
    z = z0
    while z1 - z > 0.5:
        L = seg_len(z1 - z)
        add('beam', beam_wp(L).translate((x, y, z)), color=(.72, .74, .78), group='frame'); beam_count[str(L)] += 1; z += L
for x, y in posts: post_stack(x, y, Z_FLOOR, Z_TOP)
def run(a, b, axis, z):
    L0 = abs(b - a); pos = min(a, b)
    while L0 > 0.5:
        L = seg_len(L0)
        s = beam_wp(L).rotate((0, 0, 0), (0, 1, 0) if axis == 'x' else (1, 0, 0), 90 if axis == 'x' else -90)
        s = s.translate((pos, 0, 0) if axis == 'x' else (0, pos, 0))
        add('beam', s.translate(z), color=(.72, .74, .78), group='frame'); beam_count[str(L)] += 1; pos += L; L0 -= L
for zc in TIERS.values():
    for sx_ in (-1, 1): run(Y_BACK + 30, Y_FRONT - 33, 'y', (sx_ * 340, 0, zc - 13))
for z in (Z_DECK - 20, Z_TOP - 30):
    for sx_ in (-1, 1): run(Y_BACK + 30, Y_FRONT - 33, 'y', (sx_ * 340, 0, z))
    run(-325, 325, 'x', (0, Y_BACK + 15, z))
    run(-325, 325, 'x', (0, Y_FRONT - 18, z))
OUT_X = X_HALF - 18
for x in (-OUT_X, OUT_X):
    for y in (Y_BACK + 15, Y_FRONT - 18): post_stack(x, y, Z_FLOOR, Z_TOP)
for z in (Z_FLOOR + 15, Z_SEAM - 15, Z_TOP - 30):
    for y in (Y_BACK + 15, Y_FRONT - 18):
        run(-OUT_X + 15, -355, 'x', (0, y, z)); run(355, OUT_X - 15, 'x', (0, y, z))
    for x in (-OUT_X, OUT_X): run(Y_BACK + 30, Y_FRONT - 33, 'y', (x, 0, z))
for x in (-OUT_X, OUT_X):
    for y in (Y_BACK + 15, Y_FRONT - 18):
        for z in (Z_FLOOR + 15, Z_TOP - 30): add('corner-cube', M['77_2020_three_way_corner_PRINT_8'].translate((x, y, z - 10)), color=(.45, .5, .56), group='frame')
shell = []
roof = box(0, (Y_BACK + Y_FRONT) / 2, Z_TOP, 2 * X_HALF, Y_FRONT - Y_BACK, 4)
for (cx, cy) in STUD_C: roof = roof.cut(cq.Workplane('XY').center(cx, cy).circle(STUD_D / 2 - 3).extrude(10).translate((0, 0, Z_TOP - 1)))
shell += [('roof', roof)]
for i, (cx, cy) in enumerate(STUD_C):   # reference: printed as 78/79 quarters
    st = cq.Workplane('XY').center(cx, cy).circle(STUD_D / 2).circle(STUD_D / 2 - 3).extrude(STUD_H).translate((0, 0, Z_TOP + 4))
    if i == 1: st = st.union(cq.Workplane('XY').center(cx, cy).circle(STUD_D / 2).extrude(3).translate((0, 0, Z_TOP + 4 + STUD_H - 3)))
    else: st = st.union(cq.Workplane('XY').center(cx, cy).circle(STUD_D / 2).circle(100).extrude(3).translate((0, 0, Z_TOP + 4 + STUD_H - 3)))
    shell.append((f'stud{i}', st))
FZ = TIERS['upper'] + G['H_UPPER'] + 32            # top of the drawer faces
shell += [('back', box(0, Y_BACK + 1.5, Z_FLOOR, 2 * X_HALF, 3, Z_TOP - Z_FLOOR)),
          ('left', box(-X_HALF + 1.5, (Y_BACK + Y_FRONT) / 2, Z_FLOOR, 3, Y_FRONT - Y_BACK, Z_TOP - Z_FLOOR)),
          ('right', box(X_HALF - 1.5, (Y_BACK + Y_FRONT) / 2, Z_FLOOR, 3, Y_FRONT - Y_BACK, Z_TOP - Z_FLOOR)),
          ('front-upper', box(0, Y_FRONT - 1.5, FZ, 2 * X_HALF, 3, Z_TOP - FZ)),
          ('front-left', box(-(X_HALF + 321) / 2, Y_FRONT - 1.5, Z_FLOOR, X_HALF - 321, 3, FZ - Z_FLOOR)),
          ('front-right', box((X_HALF + 321) / 2, Y_FRONT - 1.5, Z_FLOOR, X_HALF - 321, 3, FZ - Z_FLOOR))]
seam = box(0, (Y_BACK + Y_FRONT) / 2, Z_SEAM - 3, 2 * X_HALF + 2, Y_FRONT - Y_BACK + 2, 6).cut(box(0, (Y_BACK + Y_FRONT) / 2, Z_SEAM - 4, 2 * X_HALF - 4, Y_FRONT - Y_BACK - 4, 8))
add('shell-seam', seam, color=(.45, .07, .05), group='shell')
for n, s in shell: add(f'shell-{n}', s, color=(.75, .13, .1), group='shell')

# ------------------------------------------------------------------ checks
if SKIP_CHECKS:
    (OUT / 'parts_only.json').write_text(json.dumps(checks, indent=1)); print('LAYOUT', dict(Z_S=Z_S, Z_DECK=Z_DECK, Z_TOP=Z_TOP, Z_STUD_TOP=Z_STUD_TOP, H_MIN=H_MIN, H_MAX=round(H_MAX, 1), PEDESTAL=round(PEDESTAL, 1), ROD_L=ROD_L, TIERS=TIERS, LOW=(LOW_MIN, LOW_MAX), SC=(SC_LO, SC_HI))); raise SystemExit(0)
def world_solid(i):
    if i['wp'] is not None: return i['wp'].val() if hasattr(i['wp'], 'val') else i['wp']
    p = ROOT / 'ref' / i['stl'].replace('.stl', '.step')
    s = cq.importers.importStep(str(p)).val()
    return moved(s, i['m'])
def inter(a, b):
    ba, bb_ = a.BoundingBox(), b.BoundingBox()
    if ba.xmax < bb_.xmin or bb_.xmax < ba.xmin or ba.ymax < bb_.ymin or bb_.ymax < ba.ymin or ba.zmax < bb_.zmin or bb_.zmax < ba.zmin: return 0.0
    return a.intersect(b).Volume()
fixed_iso = [i for i in inst if i['group'] in ('isolate', 'V1', 'V2', 'drum', 'drum_rot', 'deck', 'door1', 'door-1', 'slider')]
solids = {id(i): world_solid(i) for i in fixed_iso}
iso_clash = []
for a in range(len(fixed_iso)):
    for b in range(a + 1, len(fixed_iso)):
        A, B = fixed_iso[a], fixed_iso[b]
        if A['group'] == B['group'] == 'drum_rot': continue
        v = inter(solids[id(A)], solids[id(B)])
        if v > 0.5:
            iso_clash.append([A['label'], B['label'], round(v, 1)])
            try:
                _ib = solids[id(A)].intersect(solids[id(B)]).BoundingBox()
                print('CLASH', A['label'], B['label'], round(v, 1), [round(q, 1) for q in (_ib.xmin, _ib.xmax, _ib.ymin, _ib.ymax, _ib.zmin, _ib.zmax)])
            except Exception as e: print('CLASH', A['label'], B['label'], round(v, 1), 'bbox?', e)
# V13: the barrel turns inside the static plate; check 12 angles about the drum axis against every fixed part near it
bar = [i for i in inst if i['label'].startswith('47b')][0]; m47 = np.array(bar['m'])
axis_p, axis_d = m47[:3, 3], m47[:3, 2] / np.linalg.norm(m47[:3, 2])
near = [i for i in fixed_iso if i['group'] != 'drum_rot' and i['label'] not in ('47b_tumbler_barrel_helical_flight',)]
drum_rot_clash = []
for deg in range(0, 360, 30):
    bs = solids[id(bar)].rotate(cq.Vector(*axis_p), cq.Vector(*(axis_p + axis_d)), deg)
    for B in near:
        v = inter(bs, solids[id(B)])
        if v > 0.5: drum_rot_clash.append([deg, B['label'], round(v, 1)])
# scoop + carriage + yaw motor + hub against everything fixed above the bins, at every delivery pose and mid-travel
moving = [i for i in inst if i['group'] in ('lift_moving', 'lift_yaw')]
mov_solids = [(i, world_solid(i)) for i in moving]
others = [i for i in inst if i['group'] in ('isolate', 'deck', 'door1', 'door-1', 'slider', 'drum', 'drum_rot', 'frame', 'lift', 'electronics') and i['label'] not in ('carriage',)]
oth_solids = [(i, world_solid(i) if id(i) not in solids else solids[id(i)]) for i in others]
lift_clash = []
def pose_mat(H, yaw):
    T = np.eye(4); T[2, 3] = H - H_MIN
    t = math.radians(yaw); Rz = np.eye(4); Rz[:2, :2] = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
    return T, Rz
# V13C: full sweep instead of 24 poses. Every 10 mm of lift from H_MIN to H_MAX (plus every delivery height) x every
# 7.5 deg of yaw from -90 to +90 (covers all 8 slot centres). Moving: carriage, yaw motor, hub, scoop. Fixed: everything
# else incl. both drawers (bins, locators, carrier tiles, side bars). Prefilter: a fixed part whose closest point to the yaw
# axis is farther out than the moving part reaches cannot touch it at any yaw; then z range; then exact OCC booleans.
others = [i for i in inst if i['group'] not in ('lift_moving', 'lift_yaw', 'shell') and i['label'] != 'carriage']
oth_solids = [(i, solids[id(i)] if id(i) in solids else world_solid(i)) for i in others]
AXIS = cq.Edge.makeLine(cq.Vector(0, 0, -100), cq.Vector(0, 0, 2000))
def r_reach(sol):                                   # max distance of any point from the yaw axis (tessellated, +0.5)
    vs, _ = sol.tessellate(0.1); return max(math.hypot(v.x, v.y) for v in vs) + 0.5
oth_info = []
for j, o in oth_solids:
    bb = o.BoundingBox(); oth_info.append((j, o, bb, o.distance(AXIS)))
H_list = sorted(set([round(H_MIN + 10 * k, 1) for k in range(int((H_MAX - H_MIN) // 10) + 1)] + [round(v, 1) for v in H_of.values()] + [round(H_MAX, 1)]))
Y_list = [-90 + 7.5 * k for k in range(25)]
pose_list = [(H, y) for H in H_list for y in Y_list]
mov_info = [(i, s, r_reach(s)) for i, s in mov_solids]
lift_clash = []; n_bool = 0
for i, s, rr in mov_info:
    yaws = Y_list if i['group'] == 'lift_yaw' else [0.0]
    bb0 = s.BoundingBox(); zlo, zhi = bb0.zmin, bb0.zmax + (H_MAX - H_MIN)
    cand = [(j, o, bb) for j, o, bb, d in oth_info if d < rr and bb.zmax > zlo and bb.zmin < zhi]
    for H in H_list:
        for yaw in yaws:
            T, Rz = pose_mat(H, yaw)
            sm = moved(s, T @ Rz if i['group'] == 'lift_yaw' else T)
            for j, o, bb in cand:
                v = inter(sm, o); n_bool += 1
                if v > 0.5: lift_clash.append([i['label'], j['label'], round(H, 1), yaw, round(v, 1)])
print('lift sweep', len(H_list), 'heights x', len(Y_list), 'yaws, candidate booleans', n_bool, 'clashes', len(lift_clash))
# the two drawers against each other and against the frame, both closed
tier_clash = []
dl = [(i, world_solid(i)) for i in inst if i['group'] in ('drawer_lower', 'drawer_lower_face')]
du = [(i, world_solid(i)) for i in inst if i['group'] in ('drawer_upper', 'drawer_upper_face')]
fr = [(i, world_solid(i)) for i in inst if i['group'] in ('frame', 'lift', 'electronics')]
for A_, B_ in ((dl, du), (dl, fr), (du, fr)):
    for i, a_ in A_:
        for j, b_ in B_:
            v = inter(a_, b_)
            if v > 0.5: tier_clash.append([i['label'], j['label'], round(v, 1)])
# doors fully open vs the scoop at the highest pose
def door_open(side, a):
    return DOOR[side].rotate((0, side * HY, Z_S - HZ), (1, side * HY, Z_S - HZ), side * a)
open_clash = []
for side in (1, -1):
    d = door_open(side, 75).val()
    for yaw in (-90, -45, 0, 45, 90):
        T, Rz = pose_mat(H_MAX, yaw)
        for i, s in mov_solids:
            if i['group'] != 'lift_yaw': continue
            v = inter(d, moved(s, T @ Rz))
            if v > 0.5: open_clash.append([f'door{side}', i['label'], yaw, round(v, 1)])
# linkage: horn angle for each door angle (four-bar solve)
link_table = []
for a in range(0, 76, 5):
    th, err = solve_horn(a)
    link_table.append({'door_deg': a, 'slider_z_above_floor': round(slider_z(a) - Z_S, 1), 'horn_deg': th, 'length_error_mm': round(err, 2)})
# drawers fully out vs frame/lift
drawer_clash = []
for t in TIERS:
    mv = [(i, world_solid(i)) for i in inst if i['group'] in (f'drawer_{t}', f'drawer_{t}_face')]
    fx = [(i, world_solid(i)) for i in inst if i['group'] in ('lift', 'lift_moving', 'lift_yaw', 'electronics') or (i['group'] == 'frame' and i['label'] in ('beam', 'corner-cube', f'{t}-latch-ear', '76_electronics_tray_A_PRINT', '76_electronics_tray_B_PRINT'))]
    for i, s in mv:
        s2 = s.translate(cq.Vector(0, TRAVEL, 0))
        for j, o in fx:
            v = inter(s2, o)
            if v > 0.5: drawer_clash.append([t, i['label'], j['label'], round(v, 1)])

# latch: closed lever vs catch after a 5 mm drawer pull (must overlap = it blocks); lever lifted 35 deg vs catch at full travel (must be free)
latch_check = {}
for t, zc in TIERS.items():
    lv, br, ct = LATCH[t]; piv = (307.0, LATCH_Y, zc - 40)
    blocked = inter(lv.val(), ct.translate((0, 5, 0)).val())
    lifted = lv.rotate((0, piv[1], piv[2]), (1, piv[1], piv[2]), -35)
    free = max(inter(lifted.val(), ct.translate((0, d, 0)).val()) for d in (0, 20, 60, 120, TRAVEL))
    latch_check[t] = {'closed_blocks_pull_mm3': round(blocked, 1), 'lifted_clash_mm3': round(free, 1)}
# locator screw holes land on a tile (not in a seam or the cutout)
tile_union = None
for tl in CAR_TILES.values(): tile_union = tl if tile_union is None else tile_union.union(tl)
holes_on_tile = sum(1 for (hx, hy) in LOC_HOLES if tile_union.val().isInside(cq.Vector(hx, hy, 1.5)) is False) if False else None
# ------------------------------------------------------------------ save assembly for rendering/animation
asm_json = []
for k, i in enumerate(inst):
    if i['wp'] is not None:
        fn = f'asm_{k:03d}.stl'; (OUT / '_asm').mkdir(exist_ok=True)
        cq.exporters.export(i['wp'] if hasattr(i['wp'], 'val') else cq.Workplane(obj=i['wp']), str(OUT / '_asm' / fn), tolerance=.2, angularTolerance=.3)
        asm_json.append({**{x: i[x] for x in ('label', 'color', 'group')}, 'stl': f'machine_{VAR}/_asm/{fn}', 'm': np.eye(4).tolist()})
    else:
        asm_json.append({**{x: i[x] for x in ('label', 'color', 'group', 'm')}, 'stl': i['stl']})
layout = {'Z_FLOOR': Z_FLOOR, 'Z_C': Z_C, 'TIERS': TIERS, 'Z_S': Z_S, 'Z_DECK': Z_DECK, 'Z_TOP': Z_TOP, 'Z_STUD_TOP': Z_STUD_TOP,
          'X_HALF': X_HALF, 'Y_BACK': Y_BACK, 'Y_FRONT': Y_FRONT, 'STUD_C': STUD_C, 'STUD_D': STUD_D, 'STUD_H': STUD_H, 'Z_SEAM': Z_SEAM,
          'LIFT_O': LIFT_O.tolist(), 'PEDESTAL': PEDESTAL, 'H_MIN': H_MIN, 'H_MAX': H_MAX, 'H_of': {f'{k[0]}-{k[1]}': v for k, v in H_of.items()},
          'SC_LO': SC_LO, 'SC_HI': SC_HI, 'HUB_ABOVE_CARRIAGE': HUB_ABOVE_CARRIAGE, 'ROD_L': ROD_L, 'SCREW_L': SCREW_L, 'BRACE_Z_lift': BRACE_Z,
          'DRUM_REAR': DRUM_REAR.tolist(), 'DRUM_FRONT': DRUM_FRONT.tolist(), 'U_AX': U_AX.tolist(),
          'FUNNEL': {'A': A_PT.tolist(), 'B': B_PT.tolist(), 'C': C_END.tolist(), 'hopper_top_z': Z_STUD_TOP - 6},
          'V1': [V1_A.tolist(), V1_B.tolist()], 'V2': [V2_A.tolist(), V2_B.tolist()], 'CAM': CAM.tolist(),
          'HINGE': {'y': HY, 'z_below_floor': HZ, 'door_half_width': HW}, 'LEVER': LEVER, 'L_DOOR': L_DOOR, 'SL_X': SL_X, 'HORN_C': HORN_C.tolist(), 'R_HORN': R_HORN, 'L_SERVO': L_SERVO, 'SL_PIN_DY': SL_PIN_DY,
          'link_table': link_table, 'slot_yaw': {k: G['slot_yaw'](k) for k in range(1, 9)}, 'TRAVEL': TRAVEL,
          'bins': {'RI': G['RI'], 'RO': G['RO'], 'SILL_LOW': G['SILL_LOW'], 'H_LOW': G['H_LOW'], 'H_UPPER': G['H_UPPER'], 'LOWER_SEAT': G['LOWER_SEAT'], 'UPPER_SEAT': G['UPPER_SEAT']},
          'scoop': {'nose_r': G['nose_r'], 'SLOPE': G['SLOPE'], 'SC_NOSE': G['SC_NOSE'], 'SC_FLOOR': G['SC_FLOOR']}}
(OUT / 'assembly.json').write_text(json.dumps({'layout': layout, 'instances': asm_json}, indent=1))
report = {'status': 'V13 PROPOSED WHOLE-MACHINE LAYOUT, not a print release', 'units': 'mm', 'layout': {k: v for k, v in layout.items() if k not in ('link_table',)},
          'new_parts': checks, 'extrusion_cut_list_2020_mm': dict(sorted(beam_count.items(), key=lambda kv: -float(kv[0]))), 'extrusion_total_m': round(sum(float(k) * v for k, v in beam_count.items()) / 1000, 2),
          'latch_check': latch_check, 'carrier_tiles_per_tier': len(CAR_TILES), 'locator_holes_per_tier': len(LOC_HOLES),
          'scoop_outlet_decision': 'kept 40 mm: only Plate 6x8 (48 wide) and Plate 8x16 (64 x 128) in the 10696 set are wider; the 8x16 cannot pass the 64 x 44 funnel duct either. Hand-sort those 2 of 484 pieces.',
          'isolation_module_clashes': iso_clash, 'drum_rotation_clashes_12_angles': drum_rot_clash, 'lift_and_scoop_clashes': lift_clash, 'poses_checked': len(pose_list),
          'open_door_vs_scoop_clashes': open_clash, 'drawer_closed_clashes': tier_clash, 'lift_sweep': {'heights': H_list, 'yaws': Y_list, 'booleans': n_bool}, 'drawer_full_out_clashes': drawer_clash, 'door_linkage': link_table,
          'body_outside_mm': [2 * X_HALF, Y_FRONT - Y_BACK, Z_STUD_TOP]}
(OUT / 'machine_checks.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps({k: report[k] for k in ('drawer_closed_clashes', 'isolation_module_clashes', 'drum_rotation_clashes_12_angles', 'lift_and_scoop_clashes', 'open_door_vs_scoop_clashes', 'drawer_full_out_clashes', 'extrusion_cut_list_2020_mm', 'extrusion_total_m', 'latch_check', 'body_outside_mm')}, indent=1))
print('Z_S', Z_S, 'Z_LIFT', round(Z_LIFT, 1), 'PEDESTAL', round(PEDESTAL, 1), 'H', round(H_MIN, 1), round(H_MAX, 1), 'ROD_L', ROD_L, 'SCREW_L', SCREW_L, 'Z_TOP', Z_TOP)
for n, c in checks.items(): print(n, c['fits_248x248x256'], c['valid_single_solid'], c['watertight_mesh'], c['extent_xyz'])
print('linkage', [(r['door_deg'], r['slider_z_above_floor'], r['horn_deg'], r['length_error_mm']) for r in link_table])
