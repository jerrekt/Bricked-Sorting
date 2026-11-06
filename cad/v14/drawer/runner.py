"""V14 drawer runner: single-stage printed undermount slide (PETG).

Two members only (single stage). The fixed rail is a 30 x 20 channel bolted
to the floor grid with 45 deg dovetail lips; the moving bar is an upside-down
T (foot under the lips, neck through the 10 mm gap, flange on top that the
drawer tray bolts to). To get 220 mm of travel out of a 190 mm drawer zone,
both members run back into the center-spine strip (y -62..0), so 96 mm stay
engaged at full extension. Hard stop: a tooth under the bar tail runs in a
groove in the rail floor and hits the groove's front wall at 220. Closed
detent: a flexing tongue with a 1.0 mm bump just ahead of the tooth.

Local frame: rail rear end at y = 0, rail runs +Y (toward the drawer face),
x = 0 rail center, z = 0 rail underside (sits on the floor at world z 8).
"""
import math
import cadquery as cq
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import IF, M3_CLR, CB_D, CB_DEPTH, INSERT_D, INSERT_DEPTH

TRAVEL = IF['drawer']['travel_y']          # 220
RAIL_L = 318.0      # fixed rail length (prints diagonally: 246 x 246)
BAR_L = 314.0       # moving bar length (prints diagonally: 243 x 243)
BAR_OFFSET = 2.0    # bar tail sits 2 mm in front of the rail tail when closed
CLR = 0.30          # sliding clearance per side (PETG on PETG, PTFE tape optional)
NECK_CLR = 0.40
# rail section
W, H = 30.0, 20.0
BASE = 6.0
CAV = 9.0           # cavity half width
LIP_GAP = 5.0       # half width of the slot the neck passes through
SLOPE_Z0, SLOPE_Z1 = 12.0, 16.0   # 45 deg lip underside
# bar section
FLANGE_Z0, FLANGE_Z1 = 22.0, 26.0
FLANGE_W = 30.0
# hard stop + detent
GROOVE_X = (3.8, 7.6); GROOVE_D = 2.0
TOOTH_X = (4.2, 7.2); TOOTH_H = 1.8; TOOTH_L = 6.0
BUMP_Y = (9.0, 15.0); BUMP_H = 1.0
TONGUE_X = GROOVE_X; TONGUE_Y = (8.0, 28.0); TONGUE_T = 3.0; SLOT = 0.6


def rail_profile_pts():
    s = SLOPE_Z1 - SLOPE_Z0
    return [(-W/2, 0), (W/2, 0), (W/2, H), (LIP_GAP, H), (LIP_GAP, SLOPE_Z1),
            (CAV, SLOPE_Z0), (CAV, BASE), (-CAV, BASE), (-CAV, SLOPE_Z0),
            (-LIP_GAP, SLOPE_Z1), (-LIP_GAP, H), (-W/2, H)]


def bar_profile_pts(clr=CLR, neck_clr=NECK_CLR):
    fh = CAV - clr                         # foot half width
    off = clr * math.sqrt(2)               # 45 deg face offset, horizontal
    nh = LIP_GAP - neck_clr                # neck half width
    # slope line of the lip underside: x = CAV - (z - SLOPE_Z0); bar's is shifted by off
    z_at = lambda x: SLOPE_Z0 + (CAV - off) - x
    return [(-fh, BASE), (fh, BASE), (fh, z_at(fh)), (nh, z_at(nh)), (nh, FLANGE_Z0),
            (FLANGE_W/2, FLANGE_Z0), (FLANGE_W/2, FLANGE_Z1), (-FLANGE_W/2, FLANGE_Z1),
            (-FLANGE_W/2, FLANGE_Z0), (-nh, FLANGE_Z0), (-nh, z_at(nh)), (-fh, z_at(fh))]


def _prism(pts, length):
    return cq.Workplane('XZ').polyline(pts).close().extrude(-length)   # y 0..length


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))


def fixed_rail(length=RAIL_L, hole_ys=(), stop=True, detent=True):
    r = _prism(rail_profile_pts(), length)
    if stop:   # groove open at the rear (bar goes in from the rear), front wall = hard stop
        g_end = BAR_OFFSET + TOOTH_L + TRAVEL
        r = r.cut(_box(GROOVE_X[0], GROOVE_X[1], -1, g_end, BASE - GROOVE_D, BASE + 1))
    if detent:
        t0, t1 = TONGUE_Y
        x0, x1 = TONGUE_X
        z_floor = BASE - GROOVE_D
        # U slot through the base around the tongue (root at t1)
        r = r.cut(_box(x0 - SLOT, x0, t0 - SLOT, t1, -1, BASE + 1))
        r = r.cut(_box(x1, x1 + SLOT, t0 - SLOT, t1, -1, BASE + 1))
        r = r.cut(_box(x0 - SLOT, x1 + SLOT, t0 - SLOT, t0, -1, BASE + 1))
        # relief under the tongue so it is TONGUE_T thick and can flex down
        r = r.cut(_box(x0 - SLOT, x1 + SLOT, t0 - SLOT, t1, -1, z_floor - TONGUE_T))
        # detent bump with 30 deg-ish ramps, in the groove
        b0, b1 = BUMP_Y
        bump = (cq.Workplane('YZ').polyline([(b0, z_floor), (b1, z_floor),
                (b1 - 2.0, z_floor + BUMP_H), (b0 + 2.0, z_floor + BUMP_H)]).close()
                .extrude(GROOVE_X[1] - GROOVE_X[0]).translate((GROOVE_X[0], 0, 0)))
        r = r.union(bump)
    for y in hole_ys:
        r = r.cut(cq.Workplane().circle(M3_CLR/2).extrude(BASE + 2).translate((0, y, -1)))
        r = r.cut(cq.Workplane().circle(CB_D/2).extrude(CB_DEPTH + 1).translate((0, y, BASE - CB_DEPTH)))
    return r


def moving_bar(length=BAR_L, clr=CLR, insert_ys=(), tooth=True, notches=0):
    b = _prism(bar_profile_pts(clr), length)
    if tooth:
        b = b.union(_box(TOOTH_X[0], TOOTH_X[1], 0, TOOTH_L, BASE - TOOTH_H, BASE + 0.5))
    for y in insert_ys:
        b = b.cut(cq.Workplane().circle(INSERT_D/2).extrude(INSERT_DEPTH + 1)
                  .translate((0, y, FLANGE_Z1 - INSERT_DEPTH)))
    for k in range(notches):   # clearance marker notches on the flange edge
        b = b.cut(_box(FLANGE_W/2 - 2, FLANGE_W/2 + 1, 6 + 5*k, 8 + 5*k, FLANGE_Z0 - 1, FLANGE_Z1 + 1))
    return b


def rail_floor_holes(rail_world_y0, world_hole_ys):
    """local y of floor-grid holes that fall on a rail starting at world y rail_world_y0."""
    return [y - rail_world_y0 for y in world_hole_ys if 12 <= y - rail_world_y0 <= RAIL_L - 12]
