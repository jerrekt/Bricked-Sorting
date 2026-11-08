"""PETG fit calibration plate for the P2S (BJ calibrated only Inland PLA; the runner rails, stations and guides are PETG).
Same method as the PLA tests in the vault runbook. Each row is labelled with 1-5 dots (dot 1 = first value).
  A  625ZZ pocket 5.2 deep:          15.9 / 16.0 / 16.1 / 16.2 / 16.3  (press a 625 in: pick the one that holds without cracking)
  B  M3 heat-set insert hole 5.7 deep: 3.9 / 4.0 / 4.1 / 4.2 / 4.3    (set an insert with the iron: pick the one with a clean collar, no wobble)
  C  M5 axle hole through 8:         5.0 / 5.1 / 5.2 / 5.3 / 5.4       (push an M5 screw through: snug turn by hand, no slop)
  D  dovetail pairs per side:        0.05 / 0.065 / 0.08 / 0.10 / 0.15  (slide by hand: pick the tightest that goes without forcing)
Run: python3 build_petg_calib.py  -> print/ STLs + README numbers. Print flat, no supports, PETG day profile, textured PEI.
"""
import sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import export, grams, hours

T = 8.0


def dots(w, n, x0, y, z):
    for j in range(n):
        w = w.union(cq.Workplane().circle(0.8).extrude(0.6).translate((x0 + j * 2.6, y, z)))
    return w


def row_holes(vals, d_pitch, depth, w_y, through=False):
    L = d_pitch * len(vals) + 4
    b = cq.Workplane().box(L, w_y, T, centered=False)
    for k, d in enumerate(vals):
        x = 2 + d_pitch * (k + 0.5)
        z0 = -1 if through else T - depth
        b = b.cut(cq.Workplane().circle(d / 2).extrude(T + 2).translate((x, w_y / 2 + 2, z0)))
        b = dots(b, k + 1, x - (k * 2.6) / 2, 2.0, T)
    return b


def dovetail_pair(c):
    """Female block 22 x 20 x 10 with a dovetail slot through z, open on the y = 20 face: 5 wide at the face, 7 wide 5 deep,
    opened by c per side. Male key: the nominal profile, 10 tall, with a 14 x 6 grip tab outside the face. Slide it down along z."""
    H = 10.0
    def prof(e):
        return [(-2.5 - e, 20.01), (2.5 + e, 20.01), (3.5 + e, 15.0 - e), (-3.5 - e, 15.0 - e)]
    fem = cq.Workplane().box(22, 20, H, centered=False).translate((-11, 0, 0))
    fem = fem.cut(cq.Workplane('XY').polyline(prof(c)).close().extrude(H + 2).translate((0, 0, -1)))
    male = cq.Workplane('XY').polyline(prof(0)[:4]).close().extrude(H)
    male = male.union(cq.Workplane().box(14, 6, H, centered=False).translate((-7, 20.0, 0)))
    return fem, male


def main():
    prn = HERE / 'print'; prn.mkdir(exist_ok=True)
    A = row_holes((15.9, 16.0, 16.1, 16.2, 16.3), 21, 5.2, 24)
    B = row_holes((3.9, 4.0, 4.1, 4.2, 4.3), 10, 5.7, 14)
    C = row_holes((5.0, 5.1, 5.2, 5.3, 5.4), 10, 0, 14, through=True)
    parts = [('180_petg_625_pockets', A), ('181_petg_insert_holes', B), ('182_petg_m5_holes', C)]
    for k, c in enumerate((0.05, 0.065, 0.08, 0.10, 0.15)):
        f, m = dovetail_pair(c)
        f = dots(f, k + 1, -8.0, 4.0, 10.0)
        m = dots(m, k + 1, -2.6 * k / 2, 23.0, 10.0)
        parts += [(f'183_petg_dovetail_{k+1}_female', f), (f'183_petg_dovetail_{k+1}_male', m)]
    tot = 0
    for n, p in parts:
        export(p, prn / f'{n}_PRINT_1.stl'); g = grams(p, density=1.27); tot += g
    print(f'{len(parts)} parts, ~{tot:.0f} g, ~{hours(tot) * 60:.0f} min')


if __name__ == '__main__':
    main()
