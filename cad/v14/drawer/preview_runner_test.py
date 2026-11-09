"""Preview stills of the runner killer test: overview at the 150 stop with a load board + weight, and a station close-up."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import cadquery as cq
import runner as R
from common import render
OUT = HERE / 'runner_test'
rail_R = R.rail(insert_ys=(-20.0, 60.0, 140.0), detent_y=6.0)
rail_L = R.mirror_x(rail_R)
stF, rF, _ = R.station(R.ROLLERS_Y, slotted_index=0)
gd, rG, _ = R.guide_block((134.0, 162.0))
ORANGE, BLUE, STEEL, WOOD = (0.95, 0.55, 0.15), (0.25, 0.45, 0.75), (0.75, 0.75, 0.78), (0.85, 0.75, 0.55)


def scene(travel, load=True, rail_op=1.0):
    it = [(rail_R.translate((200, travel, 0)), ORANGE, rail_op), (rail_L.translate((-200, travel, 0)), ORANGE, rail_op)]
    it += [(stF.translate((200, 0, 0)), BLUE, 1), (gd.translate((200, 0, 0)), BLUE, 1), (R.mirror_x(stF).translate((-200, 0, 0)), BLUE, 1)]
    it += [(r.translate((200, 0, 0)), STEEL, 1) for r in rF + rG] + [(R.mirror_x(r).translate((-200, 0, 0)), STEEL, 1) for r in rF]
    it.append((cq.Workplane().box(600, 300, 12, centered=(True, True, False)).translate((0, 60, 0)), WOOD, 0.55))   # test board on the bench
    if load:
        y0, y1 = -40 + travel, 180 + travel
        it.append((cq.Workplane().box(440, y1 - y0, 12, centered=(True, False, False)).translate((0, y0, R.RAIL_Z1)), WOOD, 0.9))   # load board on the rail tops
        it.append((cq.Workplane().box(200, 150, 80, centered=(True, True, False)).translate((0, (y0 + y1) / 2 + 20, R.RAIL_Z1 + 12)), (0.3, 0.3, 0.32), 1))  # 6-8 kg
    return it


render(scene(150), OUT / 'preview_1_killer_test.png', cam=(900, 900, 650), focal=(0, 150, 40),
       title='Killer test: rails out 150 on the 3-roller stations, load board + 6-8 kg; measure the front-edge droop')
render(scene(0, load=False, rail_op=0.35), OUT / 'preview_2_station_closeup.png', cam=(420, 330, 150), focal=(200, 150, 25),
       title='Right station: anti-lift roller (slotted, M3 preload) + 2 load rollers on M5 x 20, guide block with 2 vertical rollers; rail see-through')
