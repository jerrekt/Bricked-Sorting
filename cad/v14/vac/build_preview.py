"""How the vacuum canister works: a 9-frame GIF from the real CAD, cut in half along the mouth axis.
Frames 1-4 collect (in the hand, vac on / off), frames 5-9 feed (on the left stud: dock, half turn, drop, close).
The loose pieces are plain coloured blocks placed by hand for the picture; nothing here is simulated.
Run: python3 build_preview.py   -> how_it_works.gif (+ preview_frames/ PNGs)
"""
import math, sys
from pathlib import Path
import cadquery as cq
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import build_vac as b            # noqa: E402
from common import render        # noqa: E402

Y, K, GREY, HOSE, AIR = (0.96, 0.78, 0.10), (0.13, 0.13, 0.14), (0.36, 0.37, 0.41), (0.55, 0.57, 0.62), (0.25, 0.55, 0.95)
RED, BLUE, GRN, WHT, ORG = (0.80, 0.12, 0.10), (0.10, 0.35, 0.80), (0.10, 0.55, 0.25), (0.92, 0.92, 0.90), (0.95, 0.50, 0.10)
CUT = cq.Workplane('XY').box(600, 1200, 1400, centered=(False, True, True))        # removes the x > 0 half


def half(s):
    return s.cut(CUT)


def brick(p, size=(16, 32, 10), yaw=0, tilt=0):
    s = cq.Workplane('XY').box(*size)
    if tilt: s = s.rotate((0, 0, 0), (1, 0, 0), tilt)
    if yaw: s = s.rotate((0, 0, 0), (0, 0, 1), yaw)
    return s.translate(p)


def arrow(pts, r=2.5):
    """air path: thin rods through pts with a cone at the end (kept just behind the cut plane)."""
    out = None
    for p0, p1 in zip(pts, pts[1:]):
        d = cq.Vector(*p1) - cq.Vector(*p0)
        seg = cq.Workplane(obj=cq.Solid.makeCylinder(r, d.Length, cq.Vector(*p0), d.normalized()))
        out = seg if out is None else out.union(seg)
    d = (cq.Vector(*pts[-1]) - cq.Vector(*pts[-2])).normalized()
    return out.union(cq.Workplane(obj=cq.Solid.makeCone(3 * r, 0.0, 7 * r, cq.Vector(*pts[-1]), d)))


def main():
    sh, fy_lo = b.shell_lower(); fu, _ = b.funnel(); disc = b.gate_disc(); cap = b.pivot_cap()
    scr, _, _ = b.screen(); ld, fy_hi = b.lid(); port = b.hose_port(); mp = b.mouthpiece(); hd = b.handle(fy_lo, fy_hi)
    eyes = b.eye(1, b.EYE_CLR, b.EYE_T).union(b.eye(-1, b.EYE_CLR, b.EYE_T))
    turning = [(sh, Y), (fu, GREY), (scr, K), (ld, Y), (port, Y), (mp, K), (hd, K), (eyes, K)]      # turns with the body
    held = [(disc, K), (cap, K)]                                                              # stays on the pins

    def canister(turn=0.0, lift=0.0):
        its = [(half(s.rotate((0, 0, 0), (0, 0, 1), turn) if turn else s).translate((0, 0, lift)), c, 1.0) for s, c in turning]
        return its + [(half(s).translate((0, 0, lift)), c, 1.0) for s, c in held]

    # machine parts in the canister frame
    fr, dk = Path('/home/claude/wt_frame5/cad/v14/frame/world'), Path('/home/claude/wt_deck5/cad/v14/deck/world')
    off = (-b.ORIGIN[0], -b.ORIGIN[1], -b.ORIGIN[2])
    ld_ = lambda p: cq.Workplane().add(cq.importers.importStep(str(p)).val()).translate(off)
    # cut on the mesh: the hopper STEP is not a valid solid, so OCC cannot cut it
    machine = [(b.mesh_half(ld_(fr / '130_stud_ring_left_hopper.step')), (0.78, 0.12, 0.10), 1.0), (b.mesh_half(ld_(dk / '201_hopper.step')), (0.90, 0.45, 0.40), 1.0)]
    hose = [(half(b.ring(25.0, 28.4, b.ROOF_Z + 4, b.ROOF_Z + 85)), HOSE, 1.0)]
    wand = [(half(cq.Workplane(obj=cq.Solid.makeCylinder(31.5, 70, cq.Vector(0, b.PAD_Y + 12, b.MOUTH_Z), cq.Vector(0, 1, 0)))
                  .cut(cq.Workplane(obj=cq.Solid.makeCylinder(28.6, 80, cq.Vector(0, b.PAD_Y + 6, b.MOUTH_Z), cq.Vector(0, 1, 0))))), HOSE, 1.0)]
    air = [(arrow([(-3, 185, 122), (-3, 60, 122), (-3, 5, 150), (-3, 0, 205), (-3, 0, b.ROOF_Z + 95)]), AIR, 1.0)]

    X = -12    # blocks sit just behind the cut plane
    pile = [((X, -42, 16), RED, (16, 32, 10), 20, 0), ((X - 20, -30, 26), BLUE, (16, 16, 10), 50, 10), ((X, -62, 30), GRN, (16, 32, 10), 80, 25),
            ((X - 8, -14, 30), WHT, (16, 16, 10), 10, 30), ((X - 26, -55, 40), ORG, (8, 16, 10), 0, 0), ((X, -38, 40), BLUE, (16, 32, 10), 60, 5),
            ((X - 10, 8, 44), RED, (16, 16, 10), 30, 34), ((X, -20, 50), GRN, (8, 16, 10), 0, 20)]

    def blocks(lst, turn=0.0, lift=0.0):
        out = []
        for p, c, size, yaw, tilt in lst:
            s = brick(p, size, yaw, tilt)
            if turn: s = s.rotate((0, 0, 0), (0, 0, 1), turn)
            out.append((s.translate((0, 0, lift)), c, 1.0))
        return out

    flying = [((X, 165, 122), RED, (16, 32, 10), 90, 0), ((X, 100, 124), BLUE, (16, 16, 10), 30, 20)]
    glancing = [((X, -20, 124), RED, (16, 32, 10), 90, 25), ((X, -70, 96), BLUE, (16, 16, 10), 30, 60), ((X, 150, 122), GRN, (8, 16, 10), 0, 0)]
    stuck = [((X, 20, 148), WHT, (16, 16, 10), 0, 25), ((X, -55, 113), ORG, (8, 16, 10), 0, 25)]
    falling = [((X, 14, 105), WHT, (16, 16, 10), 20, 50), ((X, -52, 78), ORG, (8, 16, 10), 0, 70)]
    drop = [((X, 42, -8), RED, (16, 32, 10), 20, 60), ((X - 8, 36, -38), BLUE, (16, 16, 10), 40, 30), ((X - 16, 40, -66), GRN, (16, 32, 10), 70, 70),
            ((X - 24, 40, -98), WHT, (16, 16, 10), 0, 20), ((X - 28, 40, -128), ORG, (8, 16, 10), 0, 0)]
    left = [((X, 30, 22), BLUE, (16, 32, 10), 60, 30), ((X - 14, 48, 30), GRN, (8, 16, 10), 0, 20), ((X, 52, 16), RED, (16, 16, 10), 30, 10)]

    frames = [
        ('1/9  Vac on. Pieces come in through the mouth with the air', canister() + hose + wand + air + blocks(flying), 'hand'),
        ('2/9  They glance off the tilted screen and drop into the funnel', canister() + hose + wand + air + blocks(glancing) + blocks(pile[:3]), 'hand'),
        ('3/9  Air leaves through the slots to the hose. A few light pieces cling to the screen', canister() + hose + wand + air + blocks(pile) + blocks(stuck), 'hand'),
        ('4/9  Vac off: whatever was on the screen falls. Pull the hose and the wand off', canister() + blocks(pile) + blocks(falling), 'hand'),
        ('5/9  Carry it by the handle and lower it onto the left stud', canister(lift=70) + machine + blocks(pile, lift=70), 'dock'),
        ('6/9  Turn it until the 4 pins drop into the hopper screw bores. The gate is still shut', canister() + machine + blocks(pile), 'dock'),
        ('7/9  Turn the body. The disc is held by the pins, so only the body moves (here: quarter turn)', canister(turn=-90) + machine + blocks(pile, turn=-90), 'dock'),
        ('8/9  Half turn: the body hole is over the disc hole and the pieces drop into the hopper', canister(turn=-180) + machine + blocks(left) + blocks(drop), 'dock'),
        ('9/9  Empty. Turn it back to close and lift it off', canister() + machine, 'dock'),
    ]
    out = HERE / 'preview_frames'; out.mkdir(exist_ok=True)
    imgs = []
    for k, (title, items, scene) in enumerate(frames, 1):
        cam, focal = ((1050, 60, 250), (0, 25, 150)) if scene == 'hand' else ((1000, 60, 200), (0, 10, 85))
        f = out / f'frame_{k}.png'
        render(items, f, cam=cam, focal=focal, size=(1100, 900), title=title)
        imgs.append(Image.open(f).convert('P', palette=Image.ADAPTIVE)); print(f.name)
    imgs[0].save(HERE / 'how_it_works.gif', save_all=True, append_images=imgs[1:], duration=2600, loop=0)
    print(HERE / 'how_it_works.gif')


if __name__ == '__main__':
    main()


def gate_still():
    """still_6_gate.png: what turns and what does not. Left: the canister's underside. Right: the stud and hopper from above."""
    from PIL import ImageDraw, ImageFont
    sh, _ = b.shell_lower(); fu, _ = b.funnel(); disc = b.gate_disc(); cap = b.pivot_cap()
    low = cq.Workplane('XY').box(400, 400, 60, centered=(True, True, False)).translate((0, 0, -25))
    pins = None
    for a in (45, 135, 225, 315):
        p = b.pol(b.BORE_R, a, -b.PIN_L - 0.2)
        c = b.cyl(p, (0, 0, 1), b.PIN_D / 2 + 0.15, b.PIN_L + 0.1); pins = c if pins is None else pins.union(c)
    stop = b.cyl(b.pol(b.SOCK_R - b.STOP_PROTR, b.STOP_A, b.STOP_Z), (1, 0, 0), 1.6, b.STOP_PROTR + 8.2).union(b.cyl(b.pol(b.COLLAR_R, b.STOP_A, b.STOP_Z), (1, 0, 0), 2.9, 3.0))
    capc = b.cyl((0, 0, -2.8), (0, 0, 1), 10.2, 2.6)
    left = [(sh.intersect(low), Y, 1.0), (fu.intersect(low), GREY, 1.0), (disc, (0.30, 0.31, 0.34), 1.0), (pins, ORG, 1.0), (capc, BLUE, 1.0), (stop, RED, 1.0)]
    render(left, HERE / 'preview_frames' / 'gate_left.png', cam=(150, -260, -560), focal=(0, 0, -5), up=(0, 1, 0), size=(800, 760))
    fr, dk = Path('/home/claude/wt_frame5/cad/v14/frame/world'), Path('/home/claude/wt_deck5/cad/v14/deck/world')
    off = (-b.ORIGIN[0], -b.ORIGIN[1], -b.ORIGIN[2])
    ld_ = lambda p: cq.Workplane().add(cq.importers.importStep(str(p)).val()).translate(off)
    rings = None
    for a in (45, 135, 225, 315):
        r = b.ring(b.BORE_D / 2 + 0.4, b.BORE_D / 2 + 2.6, -0.95, -0.6).translate(b.pol(b.BORE_R, a, 0)); rings = r if rings is None else rings.union(r)
    right = [(ld_(fr / '130_stud_ring_left_hopper.step'), (0.78, 0.12, 0.10), 1.0), (ld_(dk / '201_hopper.step'), (0.90, 0.45, 0.40), 1.0), (rings, ORG, 1.0)]
    render(right, HERE / 'preview_frames' / 'gate_right.png', cam=(150, 260, 520), focal=(0, 0, -30), up=(0, 0, 1), size=(800, 760))
    im = Image.new('RGB', (1600, 900), (246, 247, 248))
    im.paste(Image.open(HERE / 'preview_frames' / 'gate_left.png').convert('RGB'), (0, 50)); im.paste(Image.open(HERE / 'preview_frames' / 'gate_right.png').convert('RGB'), (800, 50))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22); fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except Exception:
        f = fb = ImageFont.load_default()
    d.text((24, 14), 'Underside of the canister', font=fb, fill=(30, 30, 34)); d.text((824, 14), 'Left stud and hopper from above', font=fb, fill=(30, 30, 34))
    rows = [(ORG, '4 pins under the gate disc drop into the 4 screw bores in the hopper top: the disc cannot turn'),
            (BLUE, 'pivot cap + 1 screw: holds the disc up and lets the body spin around it'),
            (RED, 'stop screw in the collar: its tip rides in the half-circle recess on the disc rim (half-turn limit, click at each end)')]
    for k, (c, t) in enumerate(rows):
        y = 812 + 28 * k
        d.rectangle([24, y + 4, 46, y + 22], fill=tuple(int(255 * v) for v in c)); d.text((58, y), t, font=f, fill=(30, 30, 34))
    im.save(HERE / 'still_6_gate.png'); print(HERE / 'still_6_gate.png')
