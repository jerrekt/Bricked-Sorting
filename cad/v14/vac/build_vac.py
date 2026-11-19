"""V14 accessory V: vacuum canister that docks on the hopper stud (parts 250-269). CadQuery 2.8, units mm.

Collect: shop-vac hose plugs into the top port, a wand plugs onto the mouth; a tilted slotted screen keeps every
piece in the canister. Feed: pull the hose and wand off, set the canister on the machine's left stud, give the body
half a turn: the gate disc is held by 4 pins in the hopper's screw bores, so the body's drop hole lines up with it.

Everything is built in the canister frame (origin on the stud axis at the stud rim, +Y = mouth, +Z up) and moved to
machine coordinates (stud centre, z 664) for world/. Fits and print rules: vault runbooks/3d-printing.md (PETG).
Run: python3 build_vac.py            -> world/ STEP (docked), collect/ STEP (the wand, same frame), print/ STL,
                                        parts.json, checks.json, stills
"""
import json, math, sys
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import IF, BED, bbox, extent, bed_fit, export, hours, render   # noqa: E402

V = cq.Vector
# ---------------- machine interface (as built, handoff-vacuum-canister.md) ----------------
STUD_C = IF['studs']['centers'][0]            # (-180, 0)
STUD_R = IF['studs']['od'] / 2                # 108
STUD_TOP = IF['studs']['z'][1]                # 664
ORIGIN = (STUD_C[0], STUD_C[1], STUD_TOP)     # canister frame -> machine frame
HOP_MOUTH_R = 75.0                            # hopper mouth (deck5 k HOP_TOP_R)
HOP_RING_Z = -1.0                             # hopper flat top ring r 75..100, 1 mm under the stud rim
BORE_R, BORE_D, BORE_DEPTH = 92.5, 6.4, 12.0  # 4 hopper screw bores at 45/135/225/315, heads at z -13

# ---------------- PETG fits (runbook, SUNLU PETG Matte) ----------------
SLIDE = 0.20                                  # sliding fit per side
INS_D, INS_DEPTH = 4.4, 5.8                   # M3 heat-set insert hole
M3_CLR = 3.6                                  # M3 clearance (radial holes get a teardrop)
M3_HEAD = 6.5                                 # socket head / driver access bore
DENSITY = 1.27

# ---------------- hose (NOT measured yet: BJ said 2.5 in; print the hose coupon 266 first) ----------------
# Default = a common 2-1/2 in shop-vac cuff: tapered male end about 57.0 at the tip to 58.5 at the base.
CUFF_TIP, CUFF_BASE, CUFF_LEN = 57.0, 58.5, 40.0
SOCK_TOP_R = (CUFF_BASE + 0.2) / 2            # female socket: entry radius
SOCK_BOT_R = (CUFF_TIP - 0.15) / 2            # radius 36 mm in: the cuff wedges ~3 mm before the bottom
SOCK_DEPTH = 36.0
FLOW_R = 26.0                                 # bore of the wand parts (52 mm)
WAND_T = 2.0                                  # wand wall

# ---------------- body ----------------
R_OUT = 112.0                                 # shell outside radius (224 across)
COLLAR_R = 116.0                              # base collar (thicker socket wall, takes the handle and the stop screw)
COLLAR_TOP, COLLAR_CH = 10.0, 4.0
SOCK_R = STUD_R + SLIDE                       # 108.2 socket bore
DOCK_DEPTH = 20.0                             # socket depth over the stud
DISC_T, DISC_R, PLAY = 5.0, 107.8, 0.3
FUN_Z0 = DISC_T + PLAY                        # funnel underside 5.3
FLOOR_T, FUN_H = 3.0, 80.0
FUN_ZH = FUN_Z0 + FLOOR_T                     # hole rim plane 8.3
FUN_ZT = FUN_ZH + FUN_H                       # funnel top 88.3
FUN_R = SOCK_R - 0.3                          # funnel insert outside radius 107.9
R_MID = 105.6                                 # inside radius from the funnel stop up to the screen
BEAD = SOCK_R - R_MID                         # 2.6 (45 deg stop for the funnel insert)
FUN_TOP_R = R_MID - 0.3 - 1.0                 # funnel surface at its top, 104.3
BAND_Z0 = 64.0                                # funnel insert is full radius from here up (screws at 76)
FUN_FOOT_R, FUN_FOOT_Y = 66.0, -11.0          # its foot on the gate disc
HOLE_E, HOLE_R = 42.0, 30.0                   # drop hole: 60 across (same as the hopper outlet), 42 off the axis
FUN_SCREW_Z, FUN_SCREW_A = 76.0, (20.0, 160.0, 270.0)
R_IN = 109.0                                  # inside radius above the screen (3 mm wall)
THETA = 25.0                                  # screen tilt
TT, CT, ST = math.tan(math.radians(THETA)), math.cos(math.radians(THETA)), math.sin(math.radians(THETA))
SCR_ZC = 96.0 + R_IN * TT                     # screen plane z = SCR_ZC + y tan(25): 96 at the back wall
SCR_T, SCR_R = 3.0, R_IN - 0.4
SPIG_H0, SEAM_H = SCR_T + 0.2, 15.0           # lid spigot end / outside seam, measured square to the screen plane
SPIG_R = R_IN - SLIDE                         # 108.8
LID_IN_R = 106.0
ROOF_T, ROOF_CH = 3.0, 6.0
SEAM_A = (45.0, 135.0, 225.0, 315.0)
SEAM_SCREW_H = 9.0
MOUTH_Z, MOUTH_R = 122.0, 27.0                # mouth bore 54
PAD_R, PAD_Y = 50.0, COLLAR_R                 # flat pad for the mouthpiece flange
FLANGE_R, FLANGE_T, FLANGE_PCD_R = 49.0, 4.0, 41.0
PORT_R, PORT_H, PORT_PCD_R = 52.0, 36.0, 42.0
STOP_Z, STOP_A, STOP_PROTR = 2.5, 0.0, 4.2    # stop / detent screw M3 x 12 through the collar
RECESS_R = SOCK_R - STOP_PROTR - 0.6          # 103.4 floor of the disc's rim recess
HANDLE_W = 20.0
FOOT_LO_Z, FOOT_HI_Z = (-20.0, 10.0), (180.0, 214.0)
FOOT_LO_SCREW, FOOT_HI_SCREW = (-12.0, 3.0), (189.0, 205.0)
PIN_D, PIN_L = 5.6, 9.0
ELBOW_DEG, ELBOW_R = 42.0, 55.0
TUBE_L = 240.0

SEAM_FRONT_Z = SCR_ZC + R_OUT * TT + SEAM_H / CT
ROOF_Z = math.ceil(SEAM_FRONT_Z + 5.0 + ROOF_CH)      # outside roof height


# ---------------- helpers ----------------
def W(s):
    return s if isinstance(s, cq.Workplane) else cq.Workplane(obj=s)


def cyl(p, d, r, h):
    return W(cq.Solid.makeCylinder(r, h, V(*p), V(*d)))


def ring(r0, r1, z0, z1):
    return cyl((0, 0, z0), (0, 0, 1), r1, z1 - z0).cut(cyl((0, 0, z0 - 1), (0, 0, 1), r0, z1 - z0 + 2))


def rev(pts):
    """revolve an (r, z) profile about Z."""
    return cq.Workplane('XZ').polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))


def loft(c0, r0, c1, r1):
    return W(cq.Solid.makeLoft([cq.Wire.makeCircle(r0, V(*c0), V(0, 0, 1)), cq.Wire.makeCircle(r1, V(*c1), V(0, 0, 1))], True))


def slab(h0, h1):
    """everything between two planes parallel to the screen, h mm above the screen plane (square to it)."""
    b = cq.Workplane('XY').box(700, 900, h1 - h0, centered=(True, True, False)).translate((0, 0, h0))
    return b.rotate((0, 0, 0), (1, 0, 0), THETA).translate((0, 0, SCR_ZC))


def pol(r, a, z=0.0):
    return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)


def tear(p, d, dia, depth, up=(0, 0, 1), tad=0.5):
    """horizontal round hole with the runbook teardrop top (45 deg lines from the tangent points, cut off `tad` above
    the circle). p = start, d = unit direction into the part, up = print-up direction."""
    r = dia / 2
    dv, uv = V(*d).normalized(), V(*up).normalized()
    c = W(cq.Solid.makeCylinder(r, depth, V(*p), dv))
    h = min(r * math.sqrt(2), r + tad); a = r / math.sqrt(2); top = math.sqrt(2) * r - h
    side = dv.cross(uv).normalized()
    pl = cq.Plane(origin=tuple(p), xDir=side.toTuple(), normal=dv.toTuple())
    if pl.yDir.dot(uv) < 0:
        pl = cq.Plane(origin=tuple(p), xDir=(side * -1).toTuple(), normal=dv.toTuple())
    return c.union(cq.Workplane(pl).polyline([(0, 0), (a, a), (top, h), (-top, h), (-a, a)]).close().extrude(depth))


def radial_hole(a, z, r_from, depth, dia, up=(0, 0, 1)):
    """teardrop hole going inward from radius r_from at angle a."""
    p = pol(r_from, a, z); d = (-math.cos(math.radians(a)), -math.sin(math.radians(a)), 0)
    return tear(p, d, dia, depth, up)


def seam_z(a, r=SPIG_R, h=SEAM_SCREW_H):
    return SCR_ZC + r * math.sin(math.radians(a)) * TT + h / CT


# ---------------- 250 lower shell ----------------
def shell_lower():
    top = ROOF_Z + 5
    s = rev([(0, -DOCK_DEPTH), (COLLAR_R - 0.6, -DOCK_DEPTH), (COLLAR_R, -DOCK_DEPTH + 0.6), (COLLAR_R, COLLAR_TOP),
             (R_OUT, COLLAR_TOP + COLLAR_CH), (R_OUT, top), (0, top)])
    # flat pad for the mouthpiece: a disc on the plane y = PAD_Y swept back and down at 45 deg (no supports)
    face = cq.Face.makeFromWires(cq.Wire.makeCircle(PAD_R, V(0, PAD_Y, MOUTH_Z), V(0, 1, 0)))
    s = s.union(W(cq.Solid.extrudeLinear(face, V(0, -34, -34))))
    # inside: socket bore, 45 deg stop for the funnel insert, thick wall up to the screen, thin wall above it
    zb = FUN_ZT - BEAD - PLAY
    s = s.cut(rev([(0, -DOCK_DEPTH - 1), (SOCK_R + 2.5, -DOCK_DEPTH - 1), (SOCK_R, -DOCK_DEPTH + 1.5), (SOCK_R, zb),
                   (R_MID, zb + BEAD), (R_MID, top + 1), (0, top + 1)]))
    s = s.cut(cyl((0, 0, 0), (0, 0, 1), R_IN, top + 1).intersect(slab(0, 400)))
    s = s.cut(slab(SEAM_H, 500))
    # mouth: 54 bore with a peaked top, 4 inserts for the mouthpiece flange
    s = s.cut(tear((0, PAD_Y + 1, MOUTH_Z), (0, -1, 0), 2 * MOUTH_R, 40, tad=6.0))
    for a in (45, 135, 225, 315):
        x, z = FLANGE_PCD_R * math.cos(math.radians(a)), MOUTH_Z + FLANGE_PCD_R * math.sin(math.radians(a))
        s = s.cut(tear((x, PAD_Y + 0.01, z), (0, -1, 0), INS_D, INS_DEPTH)).cut(tear((x, PAD_Y, z), (0, -1, 0), 3.4, 9.0))
    # radial screws into the funnel insert, seam screws into the lid spigot, stop screw through the collar
    for a in FUN_SCREW_A:
        s = s.cut(radial_hole(a, FUN_SCREW_Z, R_OUT + 1, 6, M3_CLR))
    for a in SEAM_A:
        s = s.cut(radial_hole(a, seam_z(a), R_OUT + 1, 5, M3_CLR))
    s = s.cut(radial_hole(STOP_A, STOP_Z, COLLAR_R + 0.01, INS_DEPTH, INS_D)).cut(radial_hole(STOP_A, STOP_Z, COLLAR_R, 9, 3.4))
    # handle foot: a small flat on the collar at the back, 2 inserts
    fy = -math.sqrt(COLLAR_R ** 2 - (HANDLE_W / 2 + 1) ** 2)
    s = s.cut(cq.Workplane('XY').box(HANDLE_W + 2, 10, COLLAR_TOP - FOOT_LO_Z[0] + 2, centered=(True, False, False)).translate((0, fy - 10, FOOT_LO_Z[0] - 1)))
    for z in FOOT_LO_SCREW:
        s = s.cut(tear((0, fy - 0.01, z), (0, 1, 0), INS_D, INS_DEPTH))
    return s, fy


# ---------------- 251 funnel insert ----------------
def funnel():
    zc = FUN_ZT - BEAD
    s = rev([(0, BAND_Z0), (FUN_R, BAND_Z0), (FUN_R, zc), (FUN_R - BEAD, FUN_ZT), (0, FUN_ZT)])
    s = s.union(loft((0, FUN_FOOT_Y, FUN_Z0), FUN_FOOT_R, (0, 0, BAND_Z0 + 0.01), FUN_R))
    inner = loft((0, -HOLE_E, FUN_ZH), HOLE_R, (0, 0, FUN_ZT + 0.01), FUN_TOP_R)
    s = s.cut(inner).cut(cyl((0, -HOLE_E, FUN_Z0 - 1), (0, 0, 1), HOLE_R, FLOOR_T + 1.01))
    s = s.cut(cyl((0, 0, FUN_Z0 - 0.01), (0, 0, 1), INS_D / 2, INS_DEPTH)).cut(cyl((0, 0, FUN_Z0), (0, 0, 1), 1.7, 8.5))   # pivot insert
    for a in FUN_SCREW_A:
        s = s.cut(radial_hole(a, FUN_SCREW_Z, FUN_R + 0.01, INS_DEPTH, INS_D)).cut(radial_hole(a, FUN_SCREW_Z, FUN_R, 7.5, 3.4))
    return s, inner


# ---------------- 252 gate disc ----------------
def gate_disc():
    s = cyl((0, 0, 0), (0, 0, 1), DISC_R, DISC_T)
    # drop hole (closed pose: at the front, opposite the body's hole); it widens downward so nothing wedges in it
    s = s.cut(W(cq.Solid.makeCone(HOLE_R + 1.6, HOLE_R + 0.6, DISC_T + 0.02, V(0, HOLE_E, -0.01), V(0, 0, 1))))
    s = s.cut(cyl((0, 0, -1), (0, 0, 1), 7.2, DISC_T + 2))
    # rim recess for the stop screw: the body turns 180 deg (stop screw travels 0 -> 180 through the back)
    rec = ring(RECESS_R, DISC_R + 2, -1, DISC_T + 1).intersect(cq.Workplane('XY').box(300, 150, 20, centered=(True, False, True)).translate((0, -150, 0)))
    for sx in (1, -1):           # end pockets: half of the 3 mm screw tip sits past the y = 0 line at 0 and 180 deg
        rec = rec.union(cq.Workplane('XY').box(DISC_R + 2 - RECESS_R, 1.8, DISC_T + 2, centered=(False, False, False)).translate((RECESS_R if sx > 0 else -DISC_R - 2, -0.1, -1)))
    s = s.cut(rec)
    # detents: a bump on the recess floor 6 deg before each end, on a 2 mm spring beam (relief slot behind it)
    for a in (-6.0, -174.0):
        bump = cq.Workplane('XY').polyline([pol(RECESS_R - 0.2, a - 3.2), pol(RECESS_R + 1.2, a - 0.4), pol(RECESS_R + 1.2, a + 0.4), pol(RECESS_R - 0.2, a + 3.2)]).close().extrude(DISC_T)
        s = s.union(bump)
        slot = ring(RECESS_R - 3.5, RECESS_R - 2.0, -1, DISC_T + 1)
        wedge = cq.Workplane('XY').polyline([(0, 0)] + [pol(200, a + k) for k in (-13, -6.5, 0, 6.5, 13)]).close().extrude(DISC_T + 4).translate((0, 0, -2))
        s = s.cut(slot.intersect(wedge))
    # 4 pins into the hopper's screw bores
    for a in (45, 135, 225, 315):
        p = pol(BORE_R, a, 0)
        s = s.union(W(cq.Solid.makeCylinder(PIN_D / 2, PIN_L - 1.0, V(p[0], p[1], -PIN_L + 1.0), V(0, 0, 1))))
        s = s.union(W(cq.Solid.makeCone(PIN_D / 2 - 1.0, PIN_D / 2, 1.0, V(p[0], p[1], -PIN_L), V(0, 0, 1))))
    return s


def pivot_cap():
    s = cyl((0, 0, -2.5), (0, 0, 1), 10.0, 2.5).union(cyl((0, 0, 0), (0, 0, 1), 7.0, FUN_Z0))
    return s.cut(cyl((0, 0, -3), (0, 0, 1), 1.7, 10))


# ---------------- 254 screen ----------------
def screen():
    """flat plate (printed flat) cut to the cylinder, 2.4 mm slots running down the slope, # ribs on the clean side.
    Built in its own frame (u = x, v = up the slope, w = square to it) and returned in the canister frame."""
    cylr = W(cq.Solid.makeCylinder(SCR_R, 600, V(0, -300 * ST, -300 * CT), V(0, ST, CT)))
    plate = cylr.intersect(cq.Workplane('XY').box(400, 400, SCR_T, centered=(True, True, False)))
    a_u, a_v = 99.0, 99.0 / CT                       # slots stay inside this ellipse (ledge + spigot land outside it)
    SL_W, SL_L, PITCH_U, PITCH_V = 2.4, 26.0, 4.6, 30.0
    RIBS_U, RIBS_V = (-41.4, 41.4), (-45.0, 45.0)    # rib centre lines (on slot-free strips)
    pts = []
    for i in range(-21, 22):
        u = i * PITCH_U
        if any(abs(u - ru) < 3.5 for ru in RIBS_U):
            continue
        for j in range(-4, 5):
            v = j * PITCH_V
            if all((uu / a_u) ** 2 + (vv / a_v) ** 2 <= 1.0 for uu in (u - SL_W / 2, u + SL_W / 2) for vv in (v - SL_L / 2, v + SL_L / 2)):
                pts.append((u, v))
    slots = cq.Workplane('XY').pushPoints(pts).slot2D(SL_L, SL_W, 90).extrude(SCR_T + 2).translate((0, 0, -1))
    plate = plate.cut(slots)
    ribs = None
    for ru in RIBS_U:
        b = cq.Workplane('XY').box(2.4, 2 * a_v, 8.0, centered=(True, True, False)).translate((ru, 0, SCR_T - 0.01))
        ribs = b if ribs is None else ribs.union(b)
    for rv in RIBS_V:
        ribs = ribs.union(cq.Workplane('XY').box(2 * a_u, 2.4, 8.0, centered=(True, True, False)).translate((0, rv, SCR_T - 0.01)))
    lim = cq.Workplane('XY').ellipse(a_u, a_v).extrude(20)
    plate = plate.union(ribs.intersect(lim))
    open_area = len(pts) * ((SL_L - SL_W) * SL_W + math.pi * SL_W ** 2 / 4)
    real = plate.rotate((0, 0, 0), (1, 0, 0), THETA).translate((0, 0, SCR_ZC))
    return real, plate, {'slots': len(pts), 'slot_w': SL_W, 'slot_l': SL_L, 'open_area_mm2': round(open_area)}


# ---------------- 255 lid ----------------
def lid():
    zs = ROOF_Z - ROOF_CH - 2.0           # bottom of the chamfered shoulder
    s = rev([(0, ROOF_Z - ROOF_T), (0, ROOF_Z), (R_OUT - ROOF_CH, ROOF_Z), (R_OUT, ROOF_Z - ROOF_CH), (R_OUT, zs), (LID_IN_R, zs), (LID_IN_R, ROOF_Z - ROOF_T)])
    wall = ring(LID_IN_R, R_OUT, 60, zs + 0.01).intersect(slab(SEAM_H, 500))
    spig = ring(LID_IN_R, SPIG_R, 60, zs + 0.01).intersect(slab(SPIG_H0, SEAM_H + 1))
    s = s.union(wall).union(spig)
    for a in SEAM_A + (270.0,):          # ribs behind the seam screws and the handle screws (full height: no overhang)
        rib = cq.Workplane('XY').box(7.0, 12.0, 220, centered=(False, True, False)).translate((LID_IN_R - 6.0, 0, 40)).rotate((0, 0, 0), (0, 0, 1), a)
        s = s.union(rib.intersect(slab(SPIG_H0, 500)).intersect(cyl((0, 0, 0), (0, 0, 1), LID_IN_R + 0.5, ROOF_Z - ROOF_T + 0.01)))
    # 8 ribs under the flat roof: a blocked nozzle puts the whole chamber at full vac suction (up to ~20 kPa), and a
    # plain 3 mm roof 212 across would dish several mm. Between the port screws; printed standing on the roof.
    for k in range(8):
        rr = cq.Workplane('XY').box(LID_IN_R + 0.5 - 31.0, 2.4, 12.0, centered=(False, True, False)).translate((31.0, 0, ROOF_Z - ROOF_T - 11.99))
        s = s.union(rr.rotate((0, 0, 0), (0, 0, 1), 22.5 + 45 * k))
    s = s.cut(cyl((0, 0, ROOF_Z - ROOF_T - 1), (0, 0, 1), 28.0, ROOF_T + 2))
    for a in (45, 135, 225, 315):
        s = s.cut(cyl(pol(PORT_PCD_R, a, ROOF_Z - ROOF_T - 1), (0, 0, 1), 1.7, ROOF_T + 2))
    up = (0, 0, -1)                       # printed roof-down
    for a in SEAM_A:
        s = s.cut(radial_hole(a, seam_z(a), SPIG_R + 0.01, INS_DEPTH, INS_D, up)).cut(radial_hole(a, seam_z(a), SPIG_R, 7.8, 3.4, up))
    fy = -math.sqrt(R_OUT ** 2 - (HANDLE_W / 2 + 1) ** 2)
    s = s.cut(cq.Workplane('XY').box(HANDLE_W + 2, 10, FOOT_HI_Z[1] - FOOT_HI_Z[0] + 2, centered=(True, False, False)).translate((0, fy - 10, FOOT_HI_Z[0] - 1)))
    for z in FOOT_HI_SCREW:
        s = s.cut(tear((0, fy - 0.01, z), (0, 1, 0), INS_D, INS_DEPTH, up)).cut(tear((0, fy, z), (0, 1, 0), 3.4, 9.0, up))
    return s, fy


# ---------------- 256 hose port (the stud on top) ----------------
def socket_cut(z0, flip=False):
    """tapered female socket for the hose cuff, entry at the top (or at the bottom when flip)."""
    r0, r1 = (SOCK_TOP_R, SOCK_BOT_R) if flip else (SOCK_BOT_R, SOCK_TOP_R)
    return W(cq.Solid.makeCone(r0, r1, SOCK_DEPTH, V(0, 0, z0), V(0, 0, 1)))


def hose_port():
    s = rev([(0, ROOF_Z), (PORT_R, ROOF_Z), (PORT_R, ROOF_Z + PORT_H - 2), (PORT_R - 2, ROOF_Z + PORT_H), (0, ROOF_Z + PORT_H)])
    s = s.cut(socket_cut(ROOF_Z))
    s = s.cut(W(cq.Solid.makeCone(SOCK_TOP_R, SOCK_TOP_R + 1.5, 1.5, V(0, 0, ROOF_Z + PORT_H - 1.5), V(0, 0, 1))))   # lead-in
    for a in (45, 135, 225, 315):
        s = s.cut(cyl(pol(PORT_PCD_R, a, ROOF_Z - 0.01), (0, 0, 1), INS_D / 2, INS_DEPTH)).cut(cyl(pol(PORT_PCD_R, a, ROOF_Z), (0, 0, 1), 1.7, 8.0))
    return s


# ---------------- 257 mouthpiece, 258 elbow, 259 wand tube ----------------
def male(p, d, length=CUFF_LEN):
    """a copy of the hose cuff: tapered male end, base at p, tip along d."""
    return W(cq.Solid.makeCone(CUFF_BASE / 2, CUFF_TIP / 2, length, V(*p), V(*d)))


def mouthpiece():
    s = cyl((0, PAD_Y, MOUTH_Z), (0, 1, 0), FLANGE_R, FLANGE_T).union(male((0, PAD_Y + FLANGE_T - 0.01, MOUTH_Z), (0, 1, 0)))
    s = s.cut(cyl((0, PAD_Y - 1, MOUTH_Z), (0, 1, 0), FLOW_R, FLANGE_T + CUFF_LEN + 2))
    for a in (45, 135, 225, 315):
        x, z = FLANGE_PCD_R * math.cos(math.radians(a)), MOUTH_Z + FLANGE_PCD_R * math.sin(math.radians(a))
        s = s.cut(cyl((x, PAD_Y - 1, z), (0, 1, 0), 1.7, FLANGE_T + 2))
    return s


def socket_body(z_len=40.0):
    """female end of a wand part, standing on the bed with the entry down."""
    ro = SOCK_TOP_R + 2.6
    s = rev([(0, 0), (ro, 0), (ro, z_len), (FLOW_R + WAND_T, z_len + (ro - FLOW_R - WAND_T)), (0, z_len + (ro - FLOW_R - WAND_T))])
    s = s.cut(socket_cut(-0.01, flip=True))
    s = s.cut(W(cq.Solid.makeCone(SOCK_BOT_R, FLOW_R, SOCK_BOT_R - FLOW_R, V(0, 0, SOCK_DEPTH - 0.02), V(0, 0, 1))))
    s = s.cut(cyl((0, 0, SOCK_DEPTH), (0, 0, 1), FLOW_R, 60))
    return s, z_len + (ro - FLOW_R - WAND_T)


def wand_tube():
    s, z0 = socket_body()
    zm = TUBE_L - CUFF_LEN
    fl = CUFF_BASE / 2 - FLOW_R - WAND_T                               # 45 deg flare from the tube wall out to the cuff base
    s = s.union(ring(FLOW_R, FLOW_R + WAND_T, z0 - 0.5, zm + 0.01))
    s = s.union(W(cq.Solid.makeCone(FLOW_R + WAND_T, CUFF_BASE / 2, fl, V(0, 0, zm - fl), V(0, 0, 1))).cut(cyl((0, 0, zm - fl - 1), (0, 0, 1), FLOW_R, fl + 2)))
    s = s.union(male((0, 0, zm - 0.01), (0, 0, 1)).cut(cyl((0, 0, zm - 1), (0, 0, 1), FLOW_R, CUFF_LEN + 2)))
    return s.clean()


def wand_elbow():
    s, z0 = socket_body()
    prof = cq.Workplane('XY').workplane(offset=z0 - 0.01).circle(CUFF_BASE / 2).circle(FLOW_R)
    bend = prof.revolve(ELBOW_DEG, (ELBOW_R, 0, 0), (ELBOW_R, 1, 0))
    if bbox(bend)[5] < z0 + 5:
        bend = prof.revolve(ELBOW_DEG, (ELBOW_R, 1, 0), (ELBOW_R, 0, 0))
    a = math.radians(ELBOW_DEG)
    c = (ELBOW_R - ELBOW_R * math.cos(a), 0, z0 + ELBOW_R * math.sin(a)); d = (math.sin(a), 0, math.cos(a))
    c2 = (c[0] - 0.05 * d[0], 0, c[2] - 0.05 * d[2])                 # 0.05 into the bend so the three pieces fuse
    end = male(c2, d, CUFF_LEN + 0.05).cut(W(cq.Solid.makeCylinder(FLOW_R, CUFF_LEN + 2, V(c[0] - d[0], 0, c[2] - d[2]), V(*d))))
    return s.union(bend).union(end).clean(), c, d


# ---------------- 260 handle ----------------
def handle(fy_lo, fy_hi):
    """D handle at the back, printed on its side. Feet on the collar (2 x M3) and on the lid (2 x M3): it also ties
    the two shell halves together. Screws go in through 6.5 access bores from the grip side."""
    y_out, y_grip = -172.0, -156.0
    z0, z1 = FOOT_LO_Z[0], FOOT_HI_Z[1]
    o = cq.Workplane('YZ').polyline([(y_out, z0), (fy_lo, z0), (fy_lo, FOOT_LO_Z[1]), (y_grip, FOOT_LO_Z[1]), (y_grip, FOOT_HI_Z[0]),
                                     (fy_hi, FOOT_HI_Z[0]), (fy_hi, z1), (y_out, z1)]).close().extrude(HANDLE_W).translate((-HANDLE_W / 2, 0, 0))
    o = o.edges('|X').edges(cq.selectors.BoxSelector((-50, y_out - 1, z0 - 1), (50, y_grip + 1, z1 + 1))).fillet(6.0)
    up = (1, 0, 0)                         # printed lying on its side
    for fy, zs in ((fy_lo, FOOT_LO_SCREW), (fy_hi, FOOT_HI_SCREW)):
        for z in zs:
            o = o.cut(tear((0, fy + 1, z), (0, -1, 0), 3.4, 12.0, up))
            o = o.cut(tear((0, fy - 8.0, z), (0, -1, 0), M3_HEAD, 80.0, up))
    return o


# ---------------- 265 / 266 coupons ----------------
def coupon_socket():
    s = ring(SOCK_R, R_OUT, 0, 10.0)
    return s.cut(W(cq.Solid.makeCone(SOCK_R + 1.5, SOCK_R, 1.5, V(0, 0, -0.01), V(0, 0, 1))))


def coupon_hose():
    return W(cq.Solid.makeCone(SOCK_BOT_R + 2.4, SOCK_TOP_R + 2.4, SOCK_DEPTH, V(0, 0, 0), V(0, 0, 1))).cut(socket_cut(0))


# ---------------- estimate ----------------
def grams(shape, shell=1.5, infill=0.15):
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    v, a = s.Volume(), s.Area()
    solid = min(v, a * shell)
    return round((solid + (v - solid) * infill) / 1000 * DENSITY, 1)


def flipx(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


def on_bed(s):
    b = bbox(s)
    return s.translate((-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]))


def vol_common(a, b):
    c = a.intersect(b)
    return round(c.val().Volume(), 2) if c.vals() else 0.0


def main():
    world, prn, col = HERE / 'world', HERE / 'print', HERE / 'collect'
    for d in (world, prn, col):
        d.mkdir(exist_ok=True)
        for f in d.glob('*'):
            f.unlink()
    sh, fy_lo = shell_lower()
    fu, fun_void = funnel()
    disc = gate_disc(); cap = pivot_cap()
    scr, scr_flat, scr_info = screen()
    ld, fy_hi = lid()
    port = hose_port(); mp = mouthpiece()
    hd = handle(fy_lo, fy_hi)
    tube = wand_tube(); elb, e_c, e_d = wand_elbow()
    c_sock, c_hose = coupon_socket(), coupon_hose()

    # name: (shape in canister frame, print pose, qty, colour, bed face)
    yaw = lambda s, a: s.rotate((0, 0, 0), (0, 0, 1), a)
    parts = {
        '250_vac_shell_lower': (sh, on_bed(sh), 1, 'yellow', 'collar (socket end) down, as it stands'),
        '251_vac_funnel': (fu, on_bed(fu), 1, 'black', 'foot (gate face) down'),
        '252_vac_gate_disc': (disc, on_bed(flipx(disc)), 1, 'black', 'top face down, pins up'),
        '253_vac_pivot_cap': (cap, on_bed(cap), 1, 'black', 'flange down'),
        '254_vac_screen': (scr, on_bed(scr_flat), 1, 'black', 'flat, ribs up'),
        '255_vac_lid': (ld, on_bed(flipx(ld)), 1, 'yellow', 'roof down'),
        '256_vac_hose_port': (port, on_bed(port), 1, 'yellow', 'base (insert face) down'),
        '257_vac_mouthpiece': (mp, on_bed(mp.rotate((0, 0, 0), (1, 0, 0), 90)), 1, 'black', 'flange down'),
        '258_vac_wand_elbow': (None, on_bed(elb), 2, 'black', 'socket end down'),
        '259_vac_wand_tube': (None, on_bed(tube), 3, 'black', 'socket end down, 5 mm brim'),
        '260_vac_handle': (hd, on_bed(hd.rotate((0, 0, 0), (0, 1, 0), -90)), 1, 'black', 'on its side'),
        '265_vac_coupon_socket_ring': (None, on_bed(c_sock), 1, 'any', 'flat'),
        '266_vac_coupon_hose_socket': (None, on_bed(c_hose), 1, 'any', 'small end down'),
    }
    plist, tot = [], 0.0
    for name, (real, bed, qty, colour, face) in parts.items():
        export(bed, prn / f'{name}_PRINT_1.stl')
        if real is not None:
            export(real.translate(ORIGIN), world / f'{name}.step')
        g = grams(bed); bf = bed_fit(bed)
        plist.append({'label': name, 'part_no': name[:3], 'qty': qty, 'material': 'PETG', 'colour': colour, 'bed_face': face, **bf,
                      'diagonal_on_bed': False, 'est_grams': g, 'est_hours': hours(g)})
        tot += g * qty
    # collect pose: mouthpiece + 2 elbows + 3 tubes (canister frame), for the stills and collect/ only
    def frame(shape, c, zx, xx):
        """move a wand part (socket entry at the origin, axis +Z, bend toward +X) to entry c, axis zx, bend toward xx."""
        return W(shape.val().moved(cq.Location(cq.Plane(origin=c.toTuple(), xDir=xx.toTuple(), normal=zx.toTuple()))))
    SEAT = 33.0                                    # a socket goes about 33 mm onto a cuff
    wand = []
    c0 = V(0, PAD_Y + FLANGE_T + CUFF_LEN - SEAT, MOUTH_Z); d0 = V(0, 1, 0)
    for k in range(2):
        dn = V(0, 0, -1) - d0 * V(0, 0, -1).dot(d0); xx = dn.normalized()
        wand.append((f'258_vac_wand_elbow_{k + 1}', frame(elb, c0, d0, xx)))
        base = c0 + xx * e_c[0] + d0 * e_c[2]
        d1 = (xx * e_d[0] + d0 * e_d[2]).normalized()
        c0 = base + d1 * (CUFF_LEN - SEAT); d0 = d1
    for k in range(3):
        ref = V(1, 0, 0); xx = (ref - d0 * ref.dot(d0)).normalized()
        wand.append((f'259_vac_wand_tube_{k + 1}', frame(tube, c0, d0, xx)))
        c0 = c0 + d0 * (TUBE_L - SEAT)
    c0 = c0 + d0 * SEAT                            # tip of the last tube
    wand_reach = round(MOUTH_Z - c0.z, 0)
    for n, s in wand:                              # same machine frame as world/, wand pushed onto the mouth
        export(s.translate(ORIGIN), col / f'{n}.step')

    # ---------------- checks ----------------
    res = {'interface': IF['version'], 'frame': {'origin_machine': list(ORIGIN), 'mouth': '+Y (front) when docked and closed'}}
    body = [(n, p[0]) for n, p in parts.items() if p[0] is not None]
    self_hits = []
    for i in range(len(body)):
        for j in range(i + 1, len(body)):
            v = vol_common(body[i][1], body[j][1])
            if v > 0.5: self_hits.append([body[i][0], body[j][0], v])
    res['self_clashes'] = self_hits
    # gate: closed = body hole (back) vs disc hole (front); open = body turned 180 deg on the held disc
    hole_body = cyl((0, -HOLE_E, -5), (0, 0, 1), HOLE_R, 20)
    disc_open_hole = cyl((0, HOLE_E, -5), (0, 0, 1), HOLE_R + 0.6, 20)
    res['gate'] = {'closed_overlap_mm2': round(vol_common(hole_body, disc_open_hole) / 20, 1),
                   'open_overlap_mm2': round(vol_common(hole_body.rotate((0, 0, 0), (0, 0, 1), 180), disc_open_hole) / 20, 1),
                   'hole_d': 2 * HOLE_R, 'hopper_outlet_d': 60.0,
                   'turn_deg_before_any_opening': round(180 - 2 * math.degrees(math.asin((HOLE_R + 0.5) / HOLE_E)), 1),
                   'drop_max_radius': HOLE_E + HOLE_R + 1.6, 'hopper_mouth_r': HOP_MOUTH_R,
                   'drop_inside_hopper_mouth': HOLE_E + HOLE_R + 1.6 <= HOP_MOUTH_R - 1.0}
    opened = [(n, yaw(s, 180) if not n.startswith(('252', '253')) else s) for n, s in body]
    open_hits = []
    for n, s in opened:
        if n.startswith(('252', '253')): continue
        for m_, t in (('252_vac_gate_disc', disc), ('253_vac_pivot_cap', cap)):
            v = vol_common(s, t)
            if v > 0.5: open_hits.append([n, m_, v])
    res['gate']['open_pose_clashes'] = open_hits
    # stop screw (on the body, tip 3 dia reaching r 104.0) against the disc as the body turns 0 -> -180 deg
    tip = lambda a: W(cq.Solid.makeCylinder(1.5, STOP_PROTR, V(*pol(SOCK_R - STOP_PROTR, a, STOP_Z)), V(math.cos(math.radians(a)), math.sin(math.radians(a)), 0)))
    path = {a: vol_common(tip(a), disc) for a in (4, 2, 0, -2, -4, -6, -8, -12, -30, -90, -150, -168, -172, -174, -176, -178, -180, -182, -184)}
    res['gate']['stop_screw'] = {'free_travel_deg': [0, -180], 'interference_mm3_by_angle': path,
                                 'rest_pockets_clear': path[0] < 0.05 and path[-180] < 0.05, 'detent_bumps_at': [-6, -174],
                                 'hard_stops_beyond_travel': path[4] > 1.0 and path[-184] > 1.0,
                                 'mid_travel_clear': all(path[a] < 0.05 for a in (-12, -30, -90, -150, -168))}
    res['gate']['closed_hole_fully_covered'] = abs(vol_common(cyl((0, -HOLE_E, 0), (0, 0, 1), HOLE_R, DISC_T), disc) - math.pi * HOLE_R ** 2 * DISC_T) < 5.0
    res['pins'] = {'d': PIN_D, 'bore_d': BORE_D, 'tip_z_machine': STUD_TOP - PIN_L, 'screw_heads_z_machine': STUD_TOP - 1 - BORE_DEPTH,
                   'clear_of_heads_mm': round((STUD_TOP - PIN_L) - (STUD_TOP - 1 - BORE_DEPTH), 1), 'in_bore_mm': PIN_L - 1.0}
    res['dock'] = {'socket_id': 2 * SOCK_R, 'stud_od': 2 * STUD_R, 'fit_per_side': SLIDE, 'depth': DOCK_DEPTH,
                   'socket_wall': round(COLLAR_R - SOCK_R, 1), 'skirt_bottom_z_machine': STUD_TOP - DOCK_DEPTH, 'roof_top_z_machine': 614.0,
                   'clear_above_roof': STUD_TOP - DOCK_DEPTH - 614.0}
    hose_area = math.pi * (CUFF_TIP / 2 - 2.5) ** 2
    res['screen'] = {**scr_info, 'limit_slot_w': 2.5, 'tilt_deg': THETA, 'hose_bore_area_mm2': round(hose_area),
                     'open_to_hose_ratio': round(scr_info['open_area_mm2'] / hose_area, 1)}
    fun_l = fun_void.val().Volume() / 1e6
    extra_l = math.pi * R_MID ** 2 * (MOUTH_Z - MOUTH_R - FUN_ZT) / 1e6
    res['capacity'] = {'funnel_L': round(fun_l, 2), 'to_mouth_lip_L': round(fun_l + extra_l, 2), 'hopper_L': 0.93,
                       'far_wall_deg': round(math.degrees(math.atan2(FUN_H, FUN_TOP_R + HOLE_E - HOLE_R)), 1)}
    top_z = ROOF_Z + PORT_H
    res['size'] = {'body_od': 2 * R_OUT, 'collar_od': 2 * COLLAR_R, 'height_above_stud': top_z, 'overall_height': top_z + DOCK_DEPTH,
                   'machine_height_docked': STUD_TOP + top_z, 'wand_reach_below_mouth': wand_reach}
    res['hose'] = {'status': 'NOT MEASURED: default 2-1/2 in cuff', 'cuff_tip_od': CUFF_TIP, 'cuff_base_od': CUFF_BASE,
                   'socket_entry_d': round(2 * SOCK_TOP_R, 2), 'socket_d_at_36': round(2 * SOCK_BOT_R, 2),
                   'mm_of_depth_per_mm_of_diameter': round(SOCK_DEPTH / (2 * SOCK_TOP_R - 2 * SOCK_BOT_R), 1)}
    res['bed_fit'] = {p['label']: {'extent': p['bed_extent'], 'ok': p['fits_248']} for p in plist}
    res['filament'] = {'grams': round(tot), 'hours': round(tot / 45.0, 1),
                       'canister_only_grams': round(sum(p['est_grams'] * p['qty'] for p in plist if p['part_no'] in ('250', '251', '252', '253', '254', '255', '256', '257', '260')))}
    bought = [{'item': 'M3 heat-set insert', 'qty': 20, 'use': 'mouth pad 4, funnel 3 + pivot 1, stop 1, collar handle foot 2, lid seam 4, lid handle 2, hose port 4 (rounded up 1)'},
              {'item': 'M3 x 8 socket', 'qty': 11, 'use': 'funnel 3, seam 4, hose port 4'},
              {'item': 'M3 x 12 socket', 'qty': 10, 'use': 'mouthpiece 4, handle 4, stop 1, pivot 1'}]
    (HERE / 'parts.json').write_text(json.dumps({'module': 'V', 'interface': IF['version'], 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(tot, 1), 'est_total_hours': round(tot / 45.0, 1)}, indent=1))
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))

    # ---------------- stills ----------------
    Y, K, G = (0.96, 0.78, 0.10), (0.13, 0.13, 0.14), (0.55, 0.57, 0.62)
    cmap = {'250': Y, '255': Y, '256': Y}
    def c_of(n): return cmap.get(n[:3], K)
    try:
        fr, dk = Path('/home/claude/wt_frame5/cad/v14/frame/world'), Path('/home/claude/wt_deck5/cad/v14/deck/world')
        mach = []
        for p in sorted(fr.glob('114_roof_tile_*.step')) + [fr / '130_stud_ring_left_hopper.step', fr / '131_stud_cap_right.step']:
            mach.append((W(cq.importers.importStep(str(p)).val()), (0.78, 0.12, 0.10), 1.0))
        mach.append((W(cq.importers.importStep(str(dk / '201_hopper.step')).val()), (0.85, 0.2, 0.2), 1.0))
        items = mach + [(s.translate(ORIGIN), c_of(n), 1.0) for n, s in body]
        render(items, HERE / 'still_1_docked.png', cam=(-1150, 950, 1200), focal=(-150, 0, 760), title=f'Docked on the left stud: machine + canister = {STUD_TOP + top_z:.0f} mm tall')
        cutb = cq.Workplane('XY').box(400, 800, 900, centered=(False, True, True)).translate((0, 0, 100))
        sec = [(s.cut(cutb).translate(ORIGIN), c_of(n) if not n.startswith('251') else (0.35, 0.36, 0.40), 1.0) for n, s in body]
        mcut = cq.Workplane('XY').box(400, 800, 900, centered=(False, True, True)).translate((ORIGIN[0], 0, 600))
        msec = [(W(cq.importers.importStep(str(p)).val()).cut(mcut), c, 1.0) for p, c in ((fr / '130_stud_ring_left_hopper.step', (0.78, 0.12, 0.10)), (dk / '201_hopper.step', (0.9, 0.45, 0.4)))]
        render(sec + msec, HERE / 'still_2_section.png', cam=(-180 + 700, 60, 790), focal=(-180, 10, 760), size=(1100, 1000),
               title='Section: mouth -> tilted screen -> top port; funnel -> gate disc -> hopper')
    except Exception as e:
        print('machine stills skipped:', e)
    render([(s, c_of(n), 1.0) for n, s in body] + [(s, K, 1.0) for n, s in wand], HERE / 'still_3_collect.png', cam=(1500, 1500, 500), focal=(0, 80, -230),
           size=(1000, 1100), title=f'Collect pose: hose on the top port, wand on the mouth (reach {wand_reach:.0f} mm below the mouth)')
    ex = {'250': 0, '251': -130, '252': -230, '253': -290, '254': 130, '255': 230, '256': 330, '257': 0, '260': 0}
    exy = {'257': 90, '260': -90}
    render([(s.translate((0, exy.get(n[:3], 0), ex[n[:3]])), c_of(n), 1.0) for n, s in body], HERE / 'still_4_exploded.png', cam=(1500, 1150, 700), focal=(0, 0, 40),
           size=(1000, 1200), title='Exploded: port, lid, screen, shell, mouthpiece, handle, funnel, gate disc, pivot cap')
    return res, plist


if __name__ == '__main__':
    r, pl = main()
    for k in ('self_clashes', 'gate', 'pins', 'dock', 'screen', 'capacity', 'size', 'filament'):
        print(k, r[k])
    for p in pl:
        print(f"{p['label']:32s} x{p['qty']} {p['bed_extent']} fits={p['fits_248']} {p['est_grams']} g {p['est_hours']} h")
