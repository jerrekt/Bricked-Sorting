"""V14 drawer runner, interface 5.1: PETG rail on the drawer underside, 625ZZ roller stations screwed into the plywood floor.

Rail (PETG, moves with the drawer): 16 wide x 24 tall bar with a 16.5 tall
side slot, 6.5 deep, open toward the outside of the machine. Each rail runs
on two floor stations of two 625ZZ each: the front pair carries the load,
the rear pair takes the lift at full pull; the rearmost roller sits in a
vertical slot so it can be preloaded against the lower slot wall. The slot is
closed at the rail tail: the rear roller hits that wall at full travel (hard
stop). A 0.4 mm bump on the slot ceiling just ahead of the front roller is the
closed detent (the drawer lifts 0.15 to pass it). The rail's open front end
lets the drawer slide onto the rollers from the front. One rail per drawer
also gets a lateral guide block (two 625ZZ on vertical axles against the
rail's inner face); the other rail floats.

Local frame: rail tail at y = 0, rail runs +Y, x = 0 rail centre, the slot
opens toward +x (mirror for the left rail), z = world z.
"""
import cadquery as cq
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import IF, M3_CLR, CB_D, CB_DEPTH, INSERT_D, INSERT_DEPTH, csk_cone

# PETG fits, measured by BJ 2026-11-08 (SUNLU Matte PETG, P2S; vault runbooks/3d-printing.md 'PETG fits')
PETG_INSERT_D = 4.4      # M3 heat-set insert hole (PLA would be 4.1)
PETG_AXLE_D = 5.1        # M5 push-fit axle hole
PETG_TAP_D = 5.0         # M5 screwed straight into PETG
PETG_SLOT_W = 5.5        # M5 sliding in a slot (preload station)

TRAVEL = IF['drawer']['travel_y']               # 150
RAIL_W = 16.0
FLOOR = IF['wood']['floor_ply']['z'][1]          # 12 (plywood top)
RAIL_Z0 = FLOOR + 0.5                            # 12.5
SLOT_Z0, SLOT_H = RAIL_Z0 + 4.0, 16.5            # 16.5 .. 33.0
RAIL_Z1 = SLOT_Z0 + SLOT_H + 4.0                 # 37.0 = drawer tray underside (rail zone ends 38)
RAILS_X = {'front': 200.0, 'back': 120.0}        # keyed: front rails x +-200, back +-120
WOOD_SCREW_CLR = 3.6                             # #6 wood screw
SLOT_DEPTH = 6.5
BR_OD, BR_W, BR_ID = 16.0, 5.0, 5.0
AXLE_Z = SLOT_Z0 + SLOT_H / 2                    # 20.75
BR_X = (RAIL_W / 2 - SLOT_DEPTH + 1.0, RAIL_W / 2 - SLOT_DEPTH + 1.0 + BR_W)   # 2.5 .. 7.5 (1 mm off the slot floor)
RAIL_Y0_WORLD = -40.0                            # front rail tail (back rails mirror to +40)
RAIL_L = 220.0                                   # tail -40 .. front 180
ROLLERS_Y = (124.0, 148.0, 171.0)               # one 3-roller station per rail: anti-lift (slotted) at 124, load pair 148 / 171        # world y of the 4 rollers (front drawer): anti-lift pair, load pair
STOP_WALL = ROLLERS_Y[0] - BR_OD / 2 - TRAVEL - RAIL_Y0_WORLD   # 12: slot starts here (rail local)
BUMP_H = 0.4
POST_X0 = RAIL_W / 2 + 0.5                       # 8.5 post face (outside the rail)
POST_X1 = POST_X0 + 13.5
POST_TOP = 34.0
FOOT_T = 4.0


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(axis, c, d, h):
    a = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[axis]
    pl = cq.Plane(origin=(c[0] - a[0] * h / 2, c[1] - a[1] * h / 2, c[2] - a[2] * h / 2),
                  xDir=(0, 1, 0) if axis == 'x' else (1, 0, 0), normal=a)
    return cq.Workplane(pl).circle(d / 2).extrude(h)


def rail(length=RAIL_L, insert_ys=(), stop=True, detent_y=None):
    """slot toward +x. insert_ys: local y of M3 inserts in the top (drawer floor bolts)."""
    r = box(-RAIL_W / 2, RAIL_W / 2, 0, length, RAIL_Z0, RAIL_Z1)
    y_start = STOP_WALL if stop else -1
    r = r.cut(box(RAIL_W / 2 - SLOT_DEPTH, RAIL_W / 2 + 1, y_start, length + 1, SLOT_Z0, SLOT_Z0 + SLOT_H))
    # lead-in at the open front end
    r = r.cut(cq.Workplane('YZ').polyline([(length - 6, SLOT_Z0 + SLOT_H), (length + 1, SLOT_Z0 + SLOT_H + 1.5),
              (length + 1, SLOT_Z0 - 1.5), (length - 6, SLOT_Z0)]).close().extrude(SLOT_DEPTH + 1).translate((RAIL_W / 2 - SLOT_DEPTH, 0, 0)))
    if detent_y is not None:   # bump on the slot ceiling, ramps 3 mm each side
        y0 = detent_y
        r = r.union(cq.Workplane('YZ').polyline([(y0 - 4, SLOT_Z0 + SLOT_H), (y0 + 4, SLOT_Z0 + SLOT_H),
                    (y0 + 1, SLOT_Z0 + SLOT_H - BUMP_H), (y0 - 1, SLOT_Z0 + SLOT_H - BUMP_H)]).close()
                    .extrude(SLOT_DEPTH).translate((RAIL_W / 2 - SLOT_DEPTH, 0, 0)))
    for y in insert_ys:
        r = r.cut(cyl('z', (-2.0, y, RAIL_Z1 - INSERT_DEPTH / 2 + 0.01), PETG_INSERT_D, INSERT_DEPTH + 0.02))
    return r


def mirror_x(w):
    return w.mirror('YZ')


def station(ys, preload_last=False, slotted_index=None, foot_holes=True, rail_x_world=None, world_y0=0.0):
    """floor block for two rollers beside a rail (rail on its -x side, rail centre at x 0).
    ys: roller y (local to this block's frame, i.e. world y). Returns block, roller solids."""
    y0, y1 = min(ys) - 9, max(ys) + 9
    foot_end = POST_X0 + 50
    b = box(POST_X0, POST_X1, y0, y1, FLOOR, POST_TOP)
    b = b.union(box(POST_X0, foot_end, y0, y1, FLOOR, FLOOR + FOOT_T))
    rollers = []
    for k, y in enumerate(ys):
        # spacer boss into the slot mouth, M5 axle hole with hex nut trap on the outside
        b = b.union(cyl('x', (POST_X0 - 0.45, y, AXLE_Z), 8.0, 0.9))
        if slotted_index is not None and k == slotted_index:
            b = b.cut(box(-1, POST_X1 + 1, y - PETG_SLOT_W / 2, y + PETG_SLOT_W / 2, AXLE_Z - PETG_SLOT_W / 2 - 1.0, AXLE_Z + PETG_SLOT_W / 2 + 1.0))   # 2 mm vertical slot
            b = b.cut(box(POST_X1 - 4, POST_X1 + 1, y - 5, y + 5, AXLE_Z - 6, AXLE_Z + 6))                 # nut/washer seat
            # M3 jack screw from the top to set the preload
            b = b.cut(cyl('z', (POST_X0 + 6, y, POST_TOP - 6), M3_CLR, 14))
        else:
            b = b.cut(cyl('x', (POST_X0 + 6, y, AXLE_Z), PETG_AXLE_D, 40))
            b = b.cut(cq.Workplane(cq.Plane(origin=(POST_X1 - 4, y, AXLE_Z), xDir=(0, 1, 0), normal=(1, 0, 0))).polygon(6, 9.4).extrude(5))
        rollers.append(cyl('x', ((BR_X[0] + BR_X[1]) / 2, y, AXLE_Z), BR_OD, BR_W).cut(cyl('x', ((BR_X[0] + BR_X[1]) / 2, y, AXLE_Z), BR_ID, BR_W + 1)))
    holes = []
    if foot_holes:   # two #6 flat-head wood screws into the plywood, countersunk
        for (lx, gy) in ((POST_X1 + 10, y0 + 9), (foot_end - 8, y1 - 9)):
            holes.append((lx, gy))
            b = b.cut(cyl('z', (lx, gy, FLOOR + FOOT_T / 2), WOOD_SCREW_CLR, FOOT_T + 2)).cut(csk_cone((lx, gy, FLOOR + FOOT_T + 0.01), (0, 0, -1)))
    return b, rollers, holes


def guide_block(ys, rail_x_world=None):
    """two 625ZZ on vertical M5 axles against the rail's inner face (rail on +x side of this block)."""
    face = -RAIL_W / 2                     # rail inner face, local x
    cx = face - BR_OD / 2 - 0.1
    y0, y1 = min(ys) - 10, max(ys) + 10
    b = box(cx - 20, face - 2.0, y0, y1, FLOOR, FLOOR + 8.0)
    rollers = []
    for y in ys:
        b = b.cut(cyl('z', (cx, y, FLOOR + 4), PETG_TAP_D, 9))   # M5 screwed into the PETG block
        rollers.append(cyl('z', (cx, y, FLOOR + 8.5 + BR_W / 2), BR_OD, BR_W).cut(cyl('z', (cx, y, FLOOR + 8.5 + BR_W / 2), BR_ID, BR_W + 1)))
    holes = [(cx - 12, y0 + 6), (cx - 12, y1 - 6)]
    for (lx, gy) in holes:
        b = b.cut(cyl('z', (lx, gy, FLOOR + 4), WOOD_SCREW_CLR, 10)).cut(csk_cone((lx, gy, FLOOR + 8 + 0.01), (0, 0, -1)))
    return b, rollers, holes
