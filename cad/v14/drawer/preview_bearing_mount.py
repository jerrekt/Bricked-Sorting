"""How one station roller is mounted: section through the axle + exploded stack (rail local: rail centre x 0, post on +x)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import cadquery as cq
import runner as R
from common import render
OUT = HERE / 'runner_test'
y = R.ROLLERS_Y[1]
st, rollers, _ = R.station(R.ROLLERS_Y, slotted_index=0)
rail = R.rail(insert_ys=(-20.0, 60.0, 140.0), detent_y=6.0).translate((0, 0, 0))
z = R.AXLE_Z


def cylx(x0, x1, d):
    return cq.Workplane('YZ').circle(d / 2).extrude(x1 - x0).translate((x0, y, z))


bolt = cylx(R.POST_X1 - 20, R.POST_X1, 4.9).union(cylx(R.POST_X1, R.POST_X1 + 5, 8.5)).cut(
    cq.Workplane('YZ').polygon(6, 4.6).extrude(3).translate((R.POST_X1 + 2.01, y, z)))
nut = cq.Workplane('YZ').polygon(6, 9.2).extrude(5).translate((R.POST_X1 - 4, y, z)).cut(cylx(R.POST_X1 - 5, R.POST_X1 + 2, 5.0))
brg = rollers[1]
cut = R.box(-30, 60, y - 40, y, 0, 60)          # keep the half on -y of the axle: section through the axle centre
ORANGE, BLUE, STEEL, NUT, BRG = (0.95, 0.55, 0.15), (0.25, 0.45, 0.75), (0.55, 0.55, 0.6), (0.8, 0.75, 0.3), (0.85, 0.85, 0.88)
sec = [(st.intersect(cut), BLUE, 1), (rail.intersect(cut), ORANGE, 1), (bolt.intersect(cut), STEEL, 1), (nut.intersect(cut), NUT, 1), (brg.intersect(cut), BRG, 1)]
render(sec, OUT / 'preview_3_roller_section.png', cam=(12, y + 120, 40), focal=(12, y, 24),
       title='Cut through one roller axle: bolt head + nyloc (left), post, bearing inside the rail slot (right)')
dx = 18
exp = [(st, BLUE, 1), (rail.translate((-45, 0, 0)), ORANGE, 0.5), (brg.translate((-22, 0, 0)), BRG, 1), (nut.translate((dx, 0, 0)), NUT, 1), (bolt.translate((2 * dx + 10, 0, 0)), STEEL, 1)]
render(exp, OUT / 'preview_4_roller_exploded.png', cam=(-60, y - 170, 120), focal=(15, y, 22),
       title='Exploded: bolt -> nyloc in hex pocket -> post -> bearing -> rail slot')
