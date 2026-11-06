"""V14 module D: two opposing 8-bin drawers, bins and runners (CadQuery 2.8).

Front drawer is built in world coordinates; the back drawer is the same parts
turned 180 deg about Z (only the face inlay letters change F -> B).
Run: python3 build_drawer.py   (writes world/, print/, parts.json, checks.json, stills)
"""
import json, math, sys
from pathlib import Path
import cadquery as cq
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from common import IF, BED, M3_CLR, INSERT_D, INSERT_DEPTH, CB_D, CB_DEPTH, print_pose, bed_fit, export, bbox, extent, grams, render
import runner as R

D = IF['drawer']; B = IF['bins']; Z = IF['zones']['D_drawer']
FLOOR_TOP = IF['floor']['z'][1]                  # 8
TRAVEL = D['travel_y']                           # 220
XC = B['x_centers']; ROW_Y = B['row_y_centers'][1]   # +150 front row
CELL_X, CELL_Y = B['footprint']                  # 108, 150
FX = Z['front']['x']; FY = Z['front']['y']; FZ = Z['front']['z']
GRID = IF['floor']['grid_M3_inserts_top']
GRID_Y = [GRID['y0'] + GRID['pitch'] * k for k in range(GRID['ny'])]

# ---------- layout (front drawer, world) ----------
RAIL_X = [-400, -160, 80, 440]          # 4 runners; turned 180 deg they land at 400,160,-80,-440 (no clash)
RAIL_Y0 = -62.0                          # fixed rail rear end (spine strip), front end at 256
BAR_Y0 = RAIL_Y0 + R.BAR_OFFSET          # -60
Z_RAIL = FLOOR_TOP                       # rail underside on the floor
Z_TRAY0 = Z_RAIL + R.FLANGE_Z1           # 34: bar flange top = tray underside
TRAY_T = 6.0
Z_TRAY1 = Z_TRAY0 + TRAY_T               # 40: bins stand here
TRAY_Y = (70.0, 238.0)
FACE_Y = (238.0, 258.0); FACE_SKIN = 3.0
FACE_Z = (10.0, 184.0)
SPLIT_X = [-466.0, -232.0, 0.0, 232.0, 466.0]   # 4 tiles / 4 face pieces, splits in bin gaps
BAR_INSERTS = [140, 180, 220, 260, 300]  # bar local y (world -60 + y)
# bins
BIN_CLR = 0.6
BIN_W = CELL_X - 2 * BIN_CLR             # 106.8
BIN_H = 120.0                            # top at z 160 (max 176); see README for why not taller
BIN_WALL, BIN_FLOOR, BIN_R = 1.26, 1.6, 6.0
LABEL_DEPTH = 2.4                        # label holder sticks out of the bin front wall
BIN_Y0 = ROW_Y - CELL_Y / 2 + BIN_CLR    # 75.6
BIN_Y1 = ROW_Y + CELL_Y / 2 - BIN_CLR - LABEL_DEPTH   # 222.0 body front, holder to 224.4
RIB_T, RIB_H = 8.0, 6.0
# switches (KW11-3Z, body NOT measured: edit here after calipers)
SW_L, SW_W, SW_H = 20.0, 6.4, 10.3
SW_CLR = 0.2
SW_HOLE_PITCH, SW_HOLE_D = 9.5, 2.2
SW_DX = {-406: 35, -174: -35, 58: -35, 406: -35}   # dodge the runners
CABLE_X = 262.0                           # rolling ribbon loop lane (front drawer); back uses -280
CLOSED_SW_X = -306.0                      # drawer-closed switch on the floor (screw at grid -320, 60)

COL = {'rail': (0.25, 0.45, 0.75), 'bar': (0.95, 0.55, 0.15), 'tray': (0.80, 0.80, 0.82),
       'face_F': (0.10, 0.35, 0.70), 'face_B': (0.10, 0.55, 0.30), 'bin': (0.96, 0.87, 0.65),
       'ink': (0.97, 0.97, 0.97), 'sw': (0.2, 0.2, 0.2)}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(x, y, z0, h, d):
    return cq.Workplane().circle(d / 2).extrude(h).translate((x, y, z0))


def rail_world(x):
    holes = R.rail_floor_holes(RAIL_Y0, GRID_Y)
    return R.fixed_rail(hole_ys=holes).translate((x, RAIL_Y0, Z_RAIL))


def bar_world(x):
    return R.moving_bar(insert_ys=BAR_INSERTS).translate((x, BAR_Y0, Z_RAIL))


def switch_xy():
    out = []
    for x in XC:
        out.append((x + SW_DX.get(x, 0), ROW_Y))
    return out


def tray_tile(i):
    x0, x1 = SPLIT_X[i], SPLIT_X[i + 1]
    t = box(x0, x1, TRAY_Y[0], TRAY_Y[1], Z_TRAY0, Z_TRAY1)
    # tongue under the face foot (lower half of the plate)
    t = t.union(box(x0 + 5, x1 - 5, TRAY_Y[1], FACE_Y[1] - FACE_SKIN - 1, Z_TRAY0, Z_TRAY0 + 3))
    # rear stop wall
    t = t.union(box(x0, x1, TRAY_Y[0], TRAY_Y[0] + 4, Z_TRAY1, Z_TRAY1 + 30))
    # bin ribs in the gaps, and edge ribs at the drawer sides
    gaps = [(XC[k] + XC[k + 1]) / 2 for k in range(len(XC) - 1)]
    for g in gaps + [-463.0, 463.0]:
        w = RIB_T if abs(g) < 460 else 6.0
        a, b = max(g - w / 2, x0), min(g + w / 2, x1)
        if b - a > 0.5:
            t = t.union(box(a, b, BIN_Y0, BIN_Y1, Z_TRAY1, Z_TRAY1 + RIB_H))
    # front stops (two small blocks per bin, leave the label holder free)
    for x in XC:
        if x0 < x < x1:
            for dx in (-44, 44):
                t = t.union(box(x + dx - 4, x + dx + 4, BIN_Y1 + LABEL_DEPTH + 0.6, BIN_Y1 + LABEL_DEPTH + 4.6, Z_TRAY1, Z_TRAY1 + RIB_H))
    # bar bolts: counterbored M3 down into the bar flange inserts
    for rx in RAIL_X:
        if x0 < rx < x1:
            for ly in BAR_INSERTS:
                y = BAR_Y0 + ly
                if TRAY_Y[0] + 6 < y < TRAY_Y[1] - 4:
                    t = t.cut(cyl(rx, y, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR))
                    t = t.cut(cyl(rx, y, Z_TRAY1 - CB_DEPTH, CB_DEPTH + 1, CB_D))
    # seam half-laps: +X edge keeps the lower half 12 mm further, -X edge the upper half
    if i < 3:
        t = t.union(box(x1, x1 + 12, TRAY_Y[0] + 6, TRAY_Y[1] - 6, Z_TRAY0, Z_TRAY0 + 3))
    if i > 0:
        t = t.cut(box(x0 - 0.01, x0 + 12.3, TRAY_Y[0] + 5.7, TRAY_Y[1] - 5.7, Z_TRAY0 - 1, Z_TRAY0 + 3.2))
    for xs in ([x1] if i < 3 else []) + ([x0] if i > 0 else []):
        for y in (100, 154, 208):
            t = t.cut(cyl(xs + 6, y, Z_TRAY0 - 1, TRAY_T + 2, M3_CLR))
    # per-bin presence switch: window + boss below the tray with M2 holes
    for (sx, sy) in switch_xy():
        if x0 < sx < x1:
            bl, bw = SW_L + 2 * SW_CLR, SW_W + 2 * SW_CLR
            t = t.union(box(sx - bw / 2 - 2, sx + bw / 2 + 2, sy - bl / 2 - 2, sy + bl / 2 + 2, Z_TRAY0 - SW_H, Z_TRAY0))
            t = t.cut(box(sx - bw / 2, sx + bw / 2, sy - bl / 2, sy + bl / 2, Z_TRAY0 - SW_H - 1, Z_TRAY0 + 0.01))
            t = t.cut(box(sx - 2.3, sx + 2.3, sy - 12, sy + 12, Z_TRAY0 - 1, Z_TRAY1 + 1))   # lever window
            for dy in (-SW_HOLE_PITCH / 2, SW_HOLE_PITCH / 2):
                t = t.cut(cq.Workplane('YZ').circle(SW_HOLE_D / 2).extrude(bw + 6).translate((sx - bw / 2 - 3, sy + dy, Z_TRAY0 - SW_H / 2)))
    # MCP23017 board mount (tile 3) and the moving end of the ribbon loop (tile 3, x 280)
    if x0 < 140 < x1:
        for (mx, my) in ((125, 110), (125, 135), (155, 110), (155, 135)):
            t = t.union(cyl(mx, my, Z_TRAY0 - 8, 8, 7))
            t = t.cut(cyl(mx, my, Z_TRAY0 - 8.5, INSERT_DEPTH + 0.5, INSERT_D))
    if x0 < CABLE_X < x1:
        t = t.union(box(CABLE_X - 12, CABLE_X + 12, TRAY_Y[0] + 4, TRAY_Y[0] + 14, Z_TRAY0 - 6, Z_TRAY0))
        t = t.cut(box(CABLE_X - 4, CABLE_X + 4, TRAY_Y[0] + 3, TRAY_Y[0] + 15, Z_TRAY0 - 4, Z_TRAY0 - 2.6))   # ribbon slot
    # drawer-closed switch actuator tab (tile 1) hits the floor switch at the rear
    if x0 < CLOSED_SW_X < x1:
        t = t.union(box(CLOSED_SW_X - 6, CLOSED_SW_X + 6, TRAY_Y[0], TRAY_Y[0] + 10, Z_TRAY0 - 8, Z_TRAY0))
    return t


def face_piece(i, letter):
    x0, x1 = SPLIT_X[i] + (0.0 if i > 0 else 0.0), SPLIT_X[i + 1]
    xa, xb = x0 + (0.25 if i > 0 else 0), x1 - (0.25 if i < 3 else 0)   # 0.5 seam gap
    y0, y1 = FACE_Y
    f = box(xa, xb, y1 - FACE_SKIN, y1, FACE_Z[0], FACE_Z[1])
    # perimeter + rib frame behind the skin
    f = f.union(box(xa, xb, y0, y1, FACE_Z[1] - 4, FACE_Z[1]))
    f = f.union(box(xa, xb, y0, y1, Z_TRAY0 + 3, Z_TRAY1))           # foot over the tray tongue
    f = f.union(box(xa, xa + 4, y0, y1, Z_TRAY1, FACE_Z[1]))
    f = f.union(box(xb - 4, xb, y0, y1, Z_TRAY1, FACE_Z[1]))
    for x in XC:
        if xa < x < xb:
            for dx in (-30, 30):
                f = f.union(box(x + dx - 1.5, x + dx + 1.5, y0, y1, Z_TRAY1, FACE_Z[1]))
    f = f.union(box(xa, xb, y0, y1, 108, 111))                        # mid rib
    # notches for the fixed rails + bar flange
    for rx in RAIL_X:
        if xa - 17 < rx < xb + 17:
            f = f.cut(box(rx - 17, rx + 17, y0 - 1, y1 + 1, FACE_Z[0] - 1, Z_TRAY0 + 0.5))
    # bolts: face foot to tray tongue (M3 + nut), face foot to bar insert at y 240
    for x in [xa + 30, (xa + xb) / 2, xb - 30]:
        if all(abs(x - rx) > 22 for rx in RAIL_X):
            f = f.cut(cyl(x, 246, Z_TRAY0 - 1, 10, M3_CLR))
    for rx in RAIL_X:
        if xa < rx < xb:
            f = f.cut(cyl(rx, BAR_Y0 + 300, Z_TRAY0 + 3 - 1, 10, M3_CLR))
    # finger pull: one recessed pocket in each middle piece
    if i in (1, 2):
        cx = (xa + xb) / 2
        f = f.cut(box(cx - 50, cx + 50, y1 - FACE_SKIN - 1, y1 + 1, 122, 142))   # grip slot, fingers hook the skin
    # marks: inlay pocket 0.6 deep, text body returned separately (AMS second colour)
    ink = None
    for x in XC:
        if xa < x < xb:
            n = number_for(x, letter)
            txt = text_body(f'{letter}{n}', x)
            f = f.cut(txt)
            ink = txt if ink is None else ink.union(txt)
    return f, ink


def number_for(x, letter):
    """F1..F8 left to right for a person at the front (+Y, looking -Y), so F1 is at +X.
    The back drawer is this drawer turned 180 deg, so the same piece reads B1..B8
    left to right for a person at the back. B1 ends up behind F8."""
    order = sorted(XC, reverse=True)
    return order.index(x) + 1


def text_body(s, x):
    pl = cq.Plane(origin=(x, FACE_Y[1] - 0.6, 160), xDir=(-1, 0, 0), normal=(0, 1, 0))
    return cq.Workplane(pl).text(s, 30, 0.6, kind='bold', halign='center', valign='center')


def bin_part():
    x0, x1 = -BIN_W / 2, BIN_W / 2
    y0, y1 = BIN_Y0 - ROW_Y, BIN_Y1 - ROW_Y        # local, bin centered on its cell
    b = cq.Workplane().box(x1 - x0, y1 - y0, BIN_H, centered=False).translate((x0, y0, 0))
    b = b.edges('|Z').fillet(BIN_R)
    b = b.faces('>Z').shell(-BIN_WALL)
    # floor thicker than the walls
    b = b.union(cq.Workplane().box(x1 - x0 - 2 * BIN_WALL, y1 - y0 - 2 * BIN_WALL, BIN_FLOOR, centered=False)
                .translate((x0 + BIN_WALL, y0 + BIN_WALL, 0)).edges('|Z').fillet(BIN_R - BIN_WALL))
    # stiff top rim (inward, keeps the footprint)
    rim = (cq.Workplane().box(x1 - x0, y1 - y0, 4, centered=False).translate((x0, y0, BIN_H - 4)).edges('|Z').fillet(BIN_R)
           .cut(cq.Workplane().box(x1 - x0 - 6, y1 - y0 - 6, 6, centered=False).translate((x0 + 3, y0 + 3, BIN_H - 5)).edges('|Z').fillet(BIN_R - 3)))
    b = b.union(rim)
    # handle slot in the front wall (toward the drawer face), 16 below the rim
    b = b.cut(box(-30, 30, y1 - 5, y1 + 1, BIN_H - 34, BIN_H - 16).edges('|Y').fillet(6))
    # label card holder on the front wall: 70 x 32 card, 0.8 slot, open at the top
    lw, lh, lz = 74.0, 34.0, 30.0
    holder = box(-lw / 2, lw / 2, y1, y1 + LABEL_DEPTH, lz, lz + lh)
    holder = holder.cut(box(-lw / 2 + 2, lw / 2 - 2, y1 + 0.6, y1 + 1.6, lz + 2, lz + lh + 1))   # card slot
    holder = holder.cut(box(-lw / 2 + 5, lw / 2 - 5, y1 + 1.5, y1 + LABEL_DEPTH + 1, lz + 5, lz + lh + 1))  # window
    b = b.union(holder)
    return b


def floor_switch_mount():
    """drawer-closed KW11-3Z on the floor, bolted to grid hole (-320, 60)."""
    x, y = CLOSED_SW_X, 60.0
    m = box(-330, x + 8, y - 14, y + 8, FLOOR_TOP, FLOOR_TOP + 18)
    m = m.cut(box(x - SW_W / 2 - SW_CLR, x + SW_W / 2 + SW_CLR, y - 12, y - 12 + SW_L + 2 * SW_CLR, FLOOR_TOP + 6, FLOOR_TOP + 19))
    m = m.cut(cyl(-320, 60, FLOOR_TOP - 1, 30, M3_CLR))
    m = m.cut(cyl(-320, 60, FLOOR_TOP + 18 - CB_DEPTH, 10, CB_D))
    for dy in (-SW_HOLE_PITCH / 2, SW_HOLE_PITCH / 2):
        m = m.cut(cq.Workplane('YZ').circle(SW_HOLE_D / 2).extrude(30).translate((x - 15, y - 2 + dy, FLOOR_TOP + 11)))
    return m


def cable_clip():
    """fixed end of the 4-wire ribbon loop (I2C + 3V3/GND to the MCP23017 on the drawer)."""
    x, y = CABLE_X, -20.0
    c = box(x - 8, 290, y - 10, y + 10, FLOOR_TOP, FLOOR_TOP + 6)
    c = c.cut(box(x - 4, x + 4, y - 11, y + 11, FLOOR_TOP + 2, FLOOR_TOP + 3.4))
    c = c.cut(cyl(280, y, FLOOR_TOP - 1, 10, M3_CLR))
    return c


def rot180(w):
    return w.rotate((0, 0, 0), (0, 0, 1), 180)


def switch_dummy(x, y):
    return box(x - SW_W / 2, x + SW_W / 2, y - SW_L / 2, y + SW_L / 2, Z_TRAY0 - SW_H, Z_TRAY0)


# ---------------- build ----------------
def build():
    world = HERE / 'world'; prn = HERE / 'print'
    parts = {}      # name -> dict(shape_front, group, printable, flip, qty)
    rails = [rail_world(x) for x in RAIL_X]
    bars = [bar_world(x) for x in RAIL_X]
    tiles = [tray_tile(i) for i in range(4)]
    faces_F = [face_piece(i, 'F') for i in range(4)]
    faces_B = [face_piece(i, 'B') for i in range(4)]
    bin0 = bin_part()
    bins = [bin0.translate((x, ROW_Y, Z_TRAY1)) for x in XC]
    fsw = floor_switch_mount(); clip = cable_clip()

    inst = []    # (label, part_no, shape_world_front_closed, group, drawer)
    for k, x in enumerate(RAIL_X):
        inst.append((f'150_runner_rail_{k+1}', '150', rails[k], 'fixed'))
        inst.append((f'151_runner_bar_{k+1}', '151', bars[k], 'moving'))
    for i in range(4):
        inst.append((f'152_tray_tile_{i+1}', f'152.{i+1}', tiles[i], 'moving'))
    for k, b in enumerate(bins):
        inst.append((f'155_bin_{k+1}', '155', b, 'moving'))
    inst.append(('156_closed_switch_mount', '156', fsw, 'fixed'))
    inst.append(('157_ribbon_clip', '157', clip, 'fixed'))
    sw = [switch_dummy(*p) for p in switch_xy()]

    # world STEPs: both drawers, closed
    asm = cq.Assembly(name='drawer_module')
    shapes = {'front': [], 'back': []}
    for side in ('front', 'back'):
        T = (lambda w: w) if side == 'front' else rot180
        for lab, pn, shp, grp in inst:
            s = T(shp); shapes[side].append((lab, pn, s, grp))
        letter = 'F' if side == 'front' else 'B'
        for i in range(4):
            f, ink = (faces_F if side == 'front' else faces_B)[i]
            shapes[side].append((f'15{3 if side=="front" else 4}_face_{letter}{i+1}', f'15{3 if side=="front" else 4}.{i+1}', T(f), 'moving'))
            shapes[side].append((f'15{3 if side=="front" else 4}_face_{letter}{i+1}_ink', f'15{3 if side=="front" else 4}.{i+1}i', T(ink), 'moving'))
    for side in shapes:
        for lab, pn, s, grp in shapes[side]:
            export(s, world / f'{side}_{lab}.step')
            col = COL['ink'] if lab.endswith('_ink') else COL['rail'] if '150' in lab else COL['bar'] if '151' in lab else \
                COL['tray'] if '152' in lab else COL['face_F'] if '153' in lab else COL['face_B'] if '154' in lab else COL['bin'] if '155' in lab else COL['sw']
            asm.add(s, name=f'{side}_{lab}', color=cq.Color(*col))
    asm.save(str(world / 'drawer_assembly.step'))

    # print STLs + parts.json
    printable = [
        ('150_runner_rail', rails[0].translate((-RAIL_X[0], 0, 0)), False, 8, 'PETG'),
        ('151_runner_bar', bars[0].translate((-RAIL_X[0], 0, 0)), True, 8, 'PETG'),
        ('155_bin', bin0, False, 16, 'PLA'),
        ('156_closed_switch_mount', fsw, False, 2, 'PLA'),
        ('157_ribbon_clip', clip, False, 2, 'PLA'),
    ]
    for i in range(4):
        printable.append((f'152_tray_tile_{i+1}', tiles[i], False, 2, 'PLA'))
        printable.append((f'153_face_F{i+1}', faces_F[i][0], 'face', 1, 'PLA front colour'))
        printable.append((f'153_face_F{i+1}_ink', faces_F[i][1], 'face', 1, 'PLA white (AMS, same plate as 153)'))
        printable.append((f'154_face_B{i+1}', faces_B[i][0], 'face', 1, 'PLA back colour'))
        printable.append((f'154_face_B{i+1}_ink', faces_B[i][1], 'face', 1, 'PLA white (AMS, same plate as 154)'))
    plist = []
    for name, shp, flip, qty, mat in printable:
        if flip == 'face':   # skin on the bed: rotate so the outer face (+Y) points down
            w = shp.rotate((0, 0, 0), (1, 0, 0), -90)
            if name.endswith('_ink'):   # keep the ink aligned with its face: use the face's transform
                base = faces_F[int(name[10]) - 1][0] if name.startswith('153') else faces_B[int(name[10]) - 1][0]
                bw = base.rotate((0, 0, 0), (1, 0, 0), -90); bb = bbox(bw)
                bedp = w.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2])); diag = False
            else:
                bedp, diag = print_pose(w)
        else:
            bedp, diag = print_pose(shp, flip=flip)
        export(bedp, prn / f'{name}_PRINT_{qty}.stl')
        plist.append({'label': name, 'part_no': name[:3], 'qty': qty, 'material': mat,
                      **bed_fit(bedp), 'diagonal_on_bed': diag,
                      'est_grams_each': grams(shp, density=1.27 if 'PETG' in mat else 1.24)})
    bought = [
        {'item': 'KW11-3Z roller lever switch', 'qty': 18, 'use': '16 bin presence + 2 drawer closed'},
        {'item': 'MCP23017 breakout', 'qty': 2, 'use': 'one rides on each drawer (9 inputs)'},
        {'item': '4-wire flat ribbon, ~450 mm', 'qty': 2, 'use': 'rolling loop, drawer to deck'},
        {'item': 'M3 heat-set insert', 'qty': 8 * 5 + 2 * 4 * 2, 'use': 'bar flanges, MCP bosses'},
        {'item': 'M3 x 10 socket screw', 'qty': 2 * (4 * 6 + 4 * 4), 'use': 'rails to floor, tray to bars'},
        {'item': 'M3 x 12 screw + nut', 'qty': 2 * (9 + 12 + 4), 'use': 'tray seams, face to tray, face to bar'},
        {'item': 'M2 x 12 screw + nut', 'qty': 36, 'use': 'switches'},
        {'item': 'PTFE tape (optional)', 'qty': 1, 'use': 'rail floors'},
    ]
    total = sum(p['est_grams_each'] * p['qty'] for p in plist)
    (HERE / 'parts.json').write_text(json.dumps({'module': 'D', 'printed': plist, 'bought': bought,
                                                 'est_total_grams': round(total)}, indent=1))
    return shapes, sw, plist


def checks(shapes, plist):
    res = {'bed_fit': {p['label']: p['fits_248'] for p in plist}}
    zone = Z
    spine = IF['center_spine']
    def inside(bb, z, extra_y=None):
        ok = z['x'][0] - 0.01 <= bb[0] and bb[3] <= z['x'][1] + 0.01 and z['z'][0] - 0.01 <= bb[2] and bb[5] <= z['z'][1] + 0.01
        y0, y1 = z['y']
        if extra_y: y0, y1 = min(y0, extra_y[0]), max(y1, extra_y[1])
        return ok and y0 - 0.01 <= bb[1] and bb[4] <= y1 + 0.01
    zc = {}
    for side in ('front', 'back'):
        for lab, pn, s, grp in shapes[side]:
            bb = bbox(s)
            z = zone[side]
            strict = inside(bb, z)
            with_spine = inside(bb, z, extra_y=(spine['y'][0], spine['y'][1]))
            zc[f'{side}_{lab}'] = 'in D zone' if strict else ('D zone + center spine strip (INTERFACE REQUEST 1)' if with_spine else f'OUTSIDE {bb}')
    res['zone_closed'] = zc
    # clashes: everything, both drawers closed; then each drawer open with the other closed
    def solids(side, opened):
        out = []
        for lab, pn, s, grp in shapes[side]:
            if lab.endswith('_ink'): continue
            if opened and grp == 'moving':
                s = s.translate((0, TRAVEL if side == 'front' else -TRAVEL, 0))
            out.append((f'{side}_{lab}', s))
        return out
    def clash(lst):
        hits = []
        bbs = [(n, s, bbox(s)) for n, s in lst]
        for i in range(len(bbs)):
            for j in range(i + 1, len(bbs)):
                a, b = bbs[i][2], bbs[j][2]
                if a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2]:
                    continue
                v = bbs[i][1].intersect(bbs[j][1])
                vol = v.val().Volume() if v.vals() else 0
                if vol > 0.5:
                    hits.append([bbs[i][0], bbs[j][0], round(vol, 1)])
        return hits
    res['clash_both_closed'] = clash(solids('front', False) + solids('back', False))
    res['clash_front_open_back_closed'] = clash(solids('front', True) + solids('back', False))
    res['clash_back_open_front_closed'] = clash(solids('front', False) + solids('back', True))
    # open drawer: bins fully clear of the face plane (y 260 front)
    fb = [bbox(s) for lab, pn, s, g in shapes['front'] if lab.startswith('155_bin')]
    res['front_open_bin_rear_y'] = round(min(b[1] for b in fb) + TRAVEL, 1)
    res['front_open_bins_clear_envelope'] = res['front_open_bin_rear_y'] >= IF['envelope']['y'][1]
    res['bin_top_z'] = round(max(b[5] for b in fb), 1)
    res['bin_top_ok'] = res['bin_top_z'] <= B['top_z_max']
    res['runner_engaged_at_full_pull_mm'] = round(RAIL_Y0 + R.RAIL_L - (BAR_Y0 + TRAVEL), 1)
    res['runner_slide_check'] = 'bar sweeps 0..220 inside rail with 0 overlap except the detent (2..8) and the stop (>220); see runner.py test'
    (HERE / 'checks.json').write_text(json.dumps(res, indent=1))
    return res


def stills(shapes, sw):
    def items(front_open=False, back_open=False, alpha_face=1.0):
        out = []
        for side in ('front', 'back'):
            op = front_open if side == 'front' else back_open
            for lab, pn, s, grp in shapes[side]:
                if op and grp == 'moving':
                    s = s.translate((0, TRAVEL if side == 'front' else -TRAVEL, 0))
                col = COL['ink'] if lab.endswith('_ink') else COL['rail'] if lab.startswith('150') else COL['bar'] if lab.startswith('151') else \
                    COL['tray'] if lab.startswith('152') else COL['face_F'] if lab.startswith('153') else COL['face_B'] if lab.startswith('154') else \
                    COL['bin'] if lab.startswith('155') else COL['sw']
                out.append((s, col, alpha_face if lab.startswith(('153', '154')) else 1.0))
        return out
    render(items(), HERE / 'still_1_closed_front.png', cam=(700, 1500, 650), focal=(0, 0, 90), title='V14 drawers closed: front face (F1-F8)')
    render(items(front_open=True), HERE / 'still_2_front_open.png', cam=(1100, 1300, 700), focal=(0, 150, 60), title='Front drawer pulled 220 mm (bins clear the face), back closed')
    render(items(back_open=True, alpha_face=0.25), HERE / 'still_3_back_open.png', cam=(-900, -1400, 650), focal=(0, -150, 60), title='Back drawer pulled 220 mm: B1-B8 read left to right from the back')
    low = [(s, c, a) for s, c, a in items() if c in (COL['rail'], COL['bar'], COL['sw'])]
    render(low, HERE / 'still_4_runners_top.png', cam=(0, 0, 1600), focal=(0, 0, 0), up=(0, 1, 0), title='Runners from above: 4 per drawer, interleaved in the spine strip (front at top)', ortho=330)


if __name__ == '__main__':
    shapes, sw, plist = build()
    res = checks(shapes, plist)
    print(json.dumps({k: v for k, v in res.items() if k != 'zone_closed'}, indent=1))
    print(sorted(set(res['zone_closed'].values())))
    stills(shapes, sw)
