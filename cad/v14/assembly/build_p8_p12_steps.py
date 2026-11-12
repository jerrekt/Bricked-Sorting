"""Assembly pictures for plates P8-P12: stud inserts, studs on the roof, hopper on the left stud, chute on the hopper."""
import math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import cadquery as cq
from common import render
FR = Path('/home/claude/wt_frame5/cad/v14/frame/world'); DK = Path('/home/claude/wt_deck5/cad/v14/deck/world')
ld = lambda p: cq.Workplane().add(cq.importers.importStep(str(p)).val())
s130, s131, hop, chute = ld(FR / '130_stud_ring_left_hopper.step'), ld(FR / '131_stud_cap_right.step'), ld(DK / '201_hopper.step'), ld(DK / '202_feed_chute.step')
roof = [ld(p) for p in sorted(FR.glob('114_roof_tile_*.step'))]
RED, GOLD, STEEL, GHOST, ORNG = (0.79, 0.1, 0.04), (0.95, 0.75, 0.2), (0.55, 0.55, 0.6), (0.85, 0.85, 0.88), (0.95, 0.55, 0.15)
Z0 = 614.0
def cyl(x, y, z, h, d): return cq.Workplane().circle(d / 2).extrude(h).translate((x, y, z))
def ins(x, y, z): return cyl(x, y, z, 5.7, 4.6)
def screw(x, y, ztop, L, down=True):          # countersunk M3: head (6 dia, 1.7) at ztop, shank going away
    head = cq.Workplane().circle(3.0).workplane(offset=1.7).circle(1.5).loft().translate((x, y, ztop - 1.7)) if down else \
        cq.Workplane().circle(1.5).workplane(offset=1.7).circle(3.0).loft().translate((x, y, ztop))
    shank = cyl(x, y, ztop - L, L, 3.0) if down else cyl(x, y, ztop, L, 3.0)
    return head.union(shank)
A = (45, 135, 225, 315)
pol = lambda c, r, a: (c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
L, R = (-180.0, 0.0), (180.0, 0.0)
foot_L = [ins(*pol(L, 104, a), Z0) for a in A]              # into the foot from below
ledge_L = [ins(*pol(L, 92.5, a), Z0 + 32 - 5.7) for a in A]  # into the ledge from above
foot_R = [ins(*pol(R, 102, a), Z0) for a in A]
# 1: inserts, shown lifted 8 mm out of their holes (press them straight down with the iron)
lift = lambda w, dz: w.translate((0, 0, dz))
it = [(s130, RED, 1)] + [(lift(i, 8), GOLD, 1) for i in ledge_L]
render(it, HERE / 'p8p12_1a_left_stud_ledge_top.png', cam=(-180, -260, 980), focal=(-180, 0, 640),
       title='Step 1a - left stud (P8), from the top: 4 inserts into the inner ledge holes')
it = [(s130, RED, 1)] + [(lift(i, -8), GOLD, 1) for i in foot_L]
render(it, HERE / 'p8p12_1b_left_stud_foot_bottom.png', cam=(-180, -260, 300), focal=(-180, 0, 620),
       title='Step 1b - left stud, flipped, from the bottom: 4 inserts into the foot holes (screws come from under the roof)')
it = [(s131, RED, 1)] + [(lift(i, -8), GOLD, 1) for i in foot_R]
render(it, HERE / 'p8p12_1c_right_stud_foot_bottom.png', cam=(180, -260, 300), focal=(180, 0, 620),
       title='Step 1c - right stud (P9), flipped, from the bottom: 4 inserts into the screw-ring holes')
# 2: studs onto the roof, screws from below through the roof
up = 60
it = [(t, GHOST, 0.55) for t in roof] + [(s130.translate((0, 0, up)), RED, 1), (s131.translate((0, 0, up)), RED, 1)]
it += [(screw(*pol(L, 104, a), 612 - 25, 8, down=False), STEEL, 1) for a in A] + [(screw(*pol(R, 102, a), 612 - 25, 8, down=False), STEEL, 1) for a in A]
render(it, HERE / 'p8p12_2_studs_on_roof.png', cam=(-200, -900, 300), focal=(0, 0, 620),
       title='Step 2 - set each stud on the roof tiles (grey), 4 x M3x8 countersunk up from under the roof into the foot inserts')
# 3: hopper into the left stud: flange on the ledge, 4 csk M3 down into the ledge inserts; chute slides up onto the outlet
it = [(s130, RED, 0.45), (hop.translate((0, 0, 70)), ORNG, 1)] + [(screw(*pol(L, 92.5, a), 646 + 5 + 110, 8), STEEL, 1) for a in A]
it += [(chute.translate((0, 0, -70)), (0.85, 0.3, 0.2), 1)]
render(it, HERE / 'p8p12_3_hopper_and_chute.png', cam=(-650, -700, 760), focal=(-190, 20, 600),
       title='Step 3 - hopper drops into the left stud (flange on the ledge), 4 x M3x8 csk; chute collar slides up over the hopper outlet')
