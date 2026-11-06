"""V14 drawer runner, interface 4: rail on the drawer underside, 625ZZ rollers fixed to the floor.

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
from common import IF, M3_CLR, CB_D, CB_DEPTH, INSERT_D, INSERT_DEPTH

RX = IF['drawer']['rails_xy']
TRAVEL = IF['drawer']['travel_y']               # 205
RAIL_W = RX['rail_width']                        # 16
FLOOR = IF['floor']['z'][1]                      # 8
RAIL_Z0 = FLOOR + 0.5                            # 8.5
SLOT_Z0, SLOT_H = RAIL_Z0 + 4.0, 16.5            # 12.5 .. 29.0
RAIL_Z1 = SLOT_Z0 + SLOT_H + 3.5                 # 32.5 = drawer floor underside
SLOT_DEPTH = 6.5
BR_OD, BR_W, BR_ID = 16.0, 5.0, 5.0
AXLE_Z = SLOT_Z0 + SLOT_H / 2                    # 20.75
BR_X = (RAIL_W / 2 - SLOT_DEPTH + 1.0, RAIL_W / 2 - SLOT_DEPTH + 1.0 + BR_W)   # 2.5 .. 7.5 (1 mm off the slot floor)
RAIL_Y0_WORLD = -60.0                            # front rail tail (back rails mirror to +60)
RAIL_L = 316.0                                   # tail -60 .. front 256
ROLLERS_Y = (165.0, 183.0, 207.0, 225.0)        # world y of the 4 rollers (front drawer)
STOP_WALL = ROLLERS_Y[0] - BR_OD / 2 - TRAVEL - RAIL_Y0_WORLD   # 12: slot starts here (rail local)
BUMP_H = 0.4
POST_X0 = RAIL_W / 2 + 0.5                       # 8.5 post face (outside the rail)
POST_X1 = POST_X0 + 13.5
POST_TOP = 30.0
FOOT_T = 4.0
GRID = IF['floor']['grid_M3_inserts_top']
GX = [GRID['x0'] + GRID['pitch'] * k for k in range(GRID['nx'])]
GY = [GRID['y0'] + GRID['pitch'] * k for k in range(GRID['ny'])]


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
        r = r.cut(cyl('z', (-2.0, y, RAIL_Z1 - INSERT_DEPTH / 2 + 0.01), INSERT_D, INSERT_DEPTH + 0.02))
    return r


def mirror_x(w):
    return w.mirror('YZ')


def station(ys, preload_last=False, slotted_index=None, foot_holes=True, rail_x_world=None, world_y0=0.0):
    """floor block for two rollers beside a rail (rail on its -x side, rail centre at x 0).
    ys: roller y (local to this block's frame, i.e. world y). Returns block, roller solids."""
    y0, y1 = min(ys) - 9, max(ys) + 9
    b = box(POST_X0, POST_X1, y0, y1, FLOOR, POST_TOP)
    b = b.union(box(POST_X0, POST_X0 + 86, y0, y1, FLOOR, FLOOR + FOOT_T))
    rollers = []
    for k, y in enumerate(ys):
        # spacer boss into the slot mouth, M5 axle hole with hex nut trap on the outside
        b = b.union(cyl('x', (POST_X0 - 0.45, y, AXLE_Z), 8.0, 0.9))
        if slotted_index is not None and k == slotted_index:
            b = b.cut(box(-1, POST_X1 + 1, y - 2.7, y + 2.7, AXLE_Z - 2.7 - 1.0, AXLE_Z + 2.7 + 1.0))   # 2 mm vertical slot
            b = b.cut(box(POST_X1 - 4, POST_X1 + 1, y - 5, y + 5, AXLE_Z - 6, AXLE_Z + 6))                 # nut/washer seat
            # M3 jack screw from the top to set the preload
            b = b.cut(cyl('z', (POST_X0 + 6, y, POST_TOP - 6), M3_CLR, 14))
        else:
            b = b.cut(cyl('x', (POST_X0 + 6, y, AXLE_Z), 5.3, 40))
            b = b.cut(cq.Workplane(cq.Plane(origin=(POST_X1 - 4, y, AXLE_Z), xDir=(0, 1, 0), normal=(1, 0, 0))).polygon(6, 9.4).extrude(5))
        rollers.append(cyl('x', ((BR_X[0] + BR_X[1]) / 2, y, AXLE_Z), BR_OD, BR_W).cut(cyl('x', ((BR_X[0] + BR_X[1]) / 2, y, AXLE_Z), BR_ID, BR_W + 1)))
    holes = []
    if foot_holes and rail_x_world is not None:
        for gx in GX:
            lx = gx - rail_x_world
            if POST_X1 + 4 <= lx <= POST_X0 + 82:
                for gy in GY:
                    if y0 + 4 <= gy <= y1 - 4:
                        holes.append((lx, gy))
        for (lx, gy) in holes:
            b = b.cut(cyl('z', (lx, gy, FLOOR + FOOT_T / 2), M3_CLR, FOOT_T + 2))
    return b, rollers, holes


def guide_block(ys, rail_x_world=None):
    """two 625ZZ on vertical M5 axles against the rail's inner face (rail on +x side of this block)."""
    face = -RAIL_W / 2                     # rail inner face, local x
    cx = face - BR_OD / 2 - 0.1
    y0, y1 = min(ys) - 10, max(ys) + 10
    b = box(cx - 18, face - 2.0, y0, y1, FLOOR, FLOOR + 8.0)
    rollers = []
    for y in ys:
        b = b.cut(cyl('z', (cx, y, FLOOR + 4), INSERT_D, 9)) if False else b.cut(cyl('z', (cx, y, FLOOR + 4), 4.2, 9))
        rollers.append(cyl('z', (cx, y, FLOOR + 8.5 + BR_W / 2), BR_OD, BR_W).cut(cyl('z', (cx, y, FLOOR + 8.5 + BR_W / 2), BR_ID, BR_W + 1)))
    holes = []
    if rail_x_world is not None:
        for gx in GX:
            lx = gx - rail_x_world
            if cx - 16 <= lx <= face - 6 and abs(lx - cx) > 7:
                for gy in GY:
                    if y0 + 4 <= gy <= y1 - 4 and all(abs(gy - y) > 9 for y in ys):
                        holes.append((lx, gy))
        for (lx, gy) in holes:
            b = b.cut(cyl('z', (lx, gy, FLOOR + 4), M3_CLR, 10)).cut(cyl('z', (lx, gy, FLOOR + 8 - CB_DEPTH / 2), CB_D, CB_DEPTH + 0.02))
    return b, rollers, holes
