"""Close-up stills of the per-bin reed switch, the bin magnet and the MCP23017 hooks (front drawer, from below and in section)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import build_drawer as bd
from common import render

parts, tiles, faces, b0 = bd.drawer('front')
pick = lambda pre: [s for n, s, g in parts if n.startswith(pre)]
x = bd.XC[2]; rx = x + bd.REED_DX
cut = bd.box(rx - 60, rx + 200, 40, 170, 0, 140)          # keep the region around bin 3 and the MCP
items = [(t.intersect(cut), (0.80, 0.80, 0.82), 1.0) for t in pick('166_tray') if t.intersect(cut).vals()]
items += [(s, (0.75, 0.75, 0.78), 1) for s in pick('REED')] + [(s, (0.2, 0.2, 0.25), 1) for s in pick('MAGNET')] + [(s, (0.15, 0.45, 0.2), 1) for s in pick('MCP')]
bins = [s for n, s, g in parts if n.startswith('169_bin')]
items += [(bins[2], (0.96, 0.87, 0.65), 0.35)]
render(items, HERE / 'still_5_bin_switch.png', cam=(rx - 220, -260, -160), focal=(rx + 40, 110, 40),
       title='Under the front tray: reed groove + boss under each bin, magnet in the bin floor, MCP23017 in its hooks')
sec = bd.box(rx - 40, rx, 60, 150, 0, 140)
items2 = [(t.intersect(sec), (0.80, 0.80, 0.82), 1.0) for t in pick('166_tray') if t.intersect(sec).vals()]
items2 += [(bins[2].intersect(bd.box(rx - 40, rx, 60, 150, 0, 60)), (0.96, 0.87, 0.65), 1.0)]
items2 += [(s, (0.75, 0.75, 0.78), 1) for s in [r.intersect(sec) for r in pick('REED')[2:3]]] + [(s, (0.2, 0.2, 0.25), 1) for s in [m.intersect(sec) for m in pick('MAGNET')[2:3]]]
render(items2, HERE / 'still_6_reed_section.png', cam=(rx + 200, 102.5 + 20, 45), focal=(rx, 102.5, 40),
       title='Section: reed glass (z 38-40) in the tray groove, magnet in the bin floor boss 1 mm above')
