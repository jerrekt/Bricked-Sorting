"""V13 renders and a kinematic animation of one LEGO brick going through the
machine. VTK offscreen (EGL). The brick path is scripted from the CAD
geometry (funnel, drum, V1, V2, scanner, scoop, bin) with simple physics for
the slides and the final drop. It is NOT a physics or flow simulation."""
from pathlib import Path
import json, math, subprocess, sys
import numpy as np
import vtk

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'machine_v13'
A = json.loads((OUT / 'assembly.json').read_text()); L = A['layout']
W, H = 1280, 720

def matrix_vtk(m):
    t = vtk.vtkTransform(); mm = vtk.vtkMatrix4x4()
    for i in range(4):
        for j in range(4): mm.SetElement(i, j, float(m[i][j]))
    t.SetMatrix(mm); return t

class Scene:
    def __init__(self):
        self.ren = vtk.vtkRenderer(); self.ren.SetBackground(0.965, 0.969, 0.973)
        self.ren.SetUseDepthPeeling(1); self.ren.SetMaximumNumberOfPeels(8)
        self.rw = vtk.vtkRenderWindow(); self.rw.SetOffScreenRendering(1); self.rw.AddRenderer(self.ren); self.rw.SetSize(W, H)
        self.rw.SetAlphaBitPlanes(1); self.rw.SetMultiSamples(0)
        self.actors = []; self.cache = {}
        for inst in A['instances']:
            path = str(ROOT / inst['stl']) if not inst['stl'].startswith('machine_v13') else str(ROOT / inst['stl'])
            if path not in self.cache:
                r = vtk.vtkSTLReader(); r.SetFileName(path); r.Update()
                n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.Update()
                self.cache[path] = n.GetOutput()
            mp = vtk.vtkPolyDataMapper(); mp.SetInputData(self.cache[path])
            a = vtk.vtkActor(); a.SetMapper(mp)
            base = matrix_vtk(inst['m']); a.SetUserTransform(base)
            pr = a.GetProperty(); pr.SetColor(*inst['color']); pr.SetSpecular(.15); pr.SetSpecularPower(20); pr.SetAmbient(.12); pr.SetDiffuse(.85)
            self.ren.AddActor(a); self.actors.append((inst, a, np.array(inst['m'])))
        self.light()
        self.dyn = []
    def light(self):
        self.ren.RemoveAllLights()
        for pos, inten in (((900, 1400, 2200), .75), ((-1500, -600, 900), .35), ((300, 2000, -300), .2)):
            l = vtk.vtkLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 400); l.SetIntensity(inten); l.SetLightTypeToSceneLight(); self.ren.AddLight(l)
        self.ren.SetAmbient(.4, .4, .4)
    def group_visible(self, groups, vis):
        for inst, a, _ in self.actors:
            if inst['group'] in groups: a.SetVisibility(vis)
    def hide_labels(self, prefixes, vis=0):
        for inst, a, _ in self.actors:
            if inst['label'].startswith(tuple(prefixes)): a.SetVisibility(vis)
    def group_opacity(self, groups, op):
        for inst, a, _ in self.actors:
            if inst['group'] in groups: a.GetProperty().SetOpacity(op)
    def pose(self, H=None, yaw=0.0, door=0.0, drum=0.0, vib=(0, 0), drawer=None, led=False):
        H = L['H_MIN'] if H is None else H
        dz = H - L['H_MIN']
        hy, hz = L['HINGE']['y'], L['Z_S'] - L['HINGE']['z_below_floor']
        for inst, a, m in self.actors:
            g = inst['group']; T = np.eye(4)
            if g == 'lift_moving': T[2, 3] = dz
            elif g == 'lift_yaw':
                t = math.radians(yaw); R = np.eye(4); R[:2, :2] = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
                T = R.copy(); T[2, 3] += dz
            elif g in ('door1', 'door-1'):
                side = 1 if g == 'door1' else -1; t = math.radians(side * door)
                R = np.eye(4); R[1:3, 1:3] = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
                pre = np.eye(4); pre[1, 3], pre[2, 3] = -side * hy, -hz
                post = np.eye(4); post[1, 3], post[2, 3] = side * hy, hz
                T = post @ R @ pre
            elif g == 'slider': T[2, 3] = slider_z(door) - slider_z(0)
            elif g == 'drum_rot':
                u = np.array(L['U_AX']); c = np.array(L['DRUM_REAR'])
                T = rot_about(c, u, drum)
            elif g == 'V1': T[:3, 3] = vib[0] * np.array([0, 0, 1.0])
            elif g == 'V2': T[:3, 3] = vib[1] * np.array([0, 0, 1.0])
            elif drawer and g in (f'drawer_{drawer}', f'drawer_{drawer}_face'): T[1, 3] = L['TRAVEL']
            a.SetUserTransform(matrix_vtk(T @ m))
            if g == 'led':
                pr = a.GetProperty(); pr.SetAmbient(1.0 if led else .12); pr.SetColor(*((1, 1, .9) if led else inst['color']))
        for d in self.dyn: self.ren.RemoveActor(d)
        self.dyn = []
        self.linkage(door)
    def tube(self, p, q, r, color):
        ls = vtk.vtkLineSource(); ls.SetPoint1(*p); ls.SetPoint2(*q)
        tf = vtk.vtkTubeFilter(); tf.SetInputConnection(ls.GetOutputPort()); tf.SetRadius(r); tf.SetNumberOfSides(16); tf.CappingOn()
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(tf.GetOutputPort()); a = vtk.vtkActor(); a.SetMapper(mp); a.GetProperty().SetColor(*color)
        self.ren.AddActor(a); self.dyn.append(a); return a
    def linkage(self, door):
        x = L['SL_X']; sz = slider_z(door)
        for side in (1, -1):
            tp = tip(side, door); self.tube((x, tp[0], tp[1]), (x, 0, sz), 3.0, (.95, .95, .95))
        th = horn_angle(door); hc = np.array(L['HORN_C']); pin = horn_pin(th)
        self.tube((hc[0] + 2, hc[1], hc[2]), (hc[0] + 2, pin[0], pin[1]), 4.0, (.95, .95, .95))
        self.tube((x + 2, pin[0], pin[1]), (x + 2, L['SL_PIN_DY'], sz), 3.0, (.85, .85, .85))
    def add_mesh(self, poly, m, color, opacity=1.0):
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(poly); a = vtk.vtkActor(); a.SetMapper(mp)
        a.SetUserTransform(matrix_vtk(m)); a.GetProperty().SetColor(*color); a.GetProperty().SetOpacity(opacity); a.GetProperty().SetSpecular(.35)
        self.ren.AddActor(a); self.dyn.append(a); return a
    def camera(self, pos, focal, view_angle=30):
        c = self.ren.GetActiveCamera(); c.SetPosition(*pos); c.SetFocalPoint(*focal); c.SetViewUp(0, 0, 1); c.SetViewAngle(view_angle)
        self.ren.ResetCameraClippingRange()
    def text(self, s, x, y, size=22, color=(.13, .19, .25), bold=False):
        t = vtk.vtkTextActor(); t.SetInput(s); tp = t.GetTextProperty(); tp.SetFontSize(size); tp.SetColor(*color); tp.SetBold(bold); tp.SetFontFamilyToArial()
        t.SetDisplayPosition(x, y); self.ren.AddActor2D(t); self.dyn.append(t); return t
    def save(self, path):
        self.rw.Render(); w = vtk.vtkWindowToImageFilter(); w.SetInput(self.rw); w.ReadFrontBufferOff(); w.Update()
        p = vtk.vtkPNGWriter(); p.SetFileName(str(path)); p.SetInputConnection(w.GetOutputPort()); p.Write()

def rot_about(c, u, deg):
    u = np.array(u) / np.linalg.norm(u); t = math.radians(deg); K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = np.array(c) - R @ np.array(c); return M
def tip(side, a):
    t = math.radians(a); hy, hz = L['HINGE']['y'], L['Z_S'] - L['HINGE']['z_below_floor']
    return np.array([side * (hy + L['LEVER'] * math.cos(t)), hz + L['LEVER'] * math.sin(t)])
def slider_z(a):
    tp = tip(1, a); return tp[1] + math.sqrt(L['L_DOOR'] ** 2 - tp[0] ** 2)
def horn_pin(th):
    hc = L['HORN_C']; return np.array([hc[1] + L['R_HORN'] * math.cos(math.radians(th)), hc[2] + L['R_HORN'] * math.sin(math.radians(th))])
_lt = L['link_table']
def horn_angle(a):
    xs = [r['door_deg'] for r in _lt]; ys = [r['horn_deg'] for r in _lt]; return float(np.interp(a, xs, ys))

def brick_poly():
    app = vtk.vtkAppendPolyData()
    cb = vtk.vtkCubeSource(); cb.SetXLength(32); cb.SetYLength(16); cb.SetZLength(9.6); cb.SetCenter(0, 0, 4.8); cb.Update(); app.AddInputData(cb.GetOutput())
    for i in range(4):
        for j in range(2):
            c = vtk.vtkCylinderSource(); c.SetRadius(2.4); c.SetHeight(1.8); c.SetResolution(24); c.SetCenter(0, 0, 0); c.Update()
            t = vtk.vtkTransform(); t.Translate(-12 + 8 * i, -4 + 8 * j, 10.5); t.RotateX(90)
            tf = vtk.vtkTransformPolyDataFilter(); tf.SetInputData(c.GetOutput()); tf.SetTransform(t); tf.Update(); app.AddInputData(tf.GetOutput())
    app.Update(); n = vtk.vtkPolyDataNormals(); n.SetInputData(app.GetOutput()); n.Update(); return n.GetOutput()

def frame_mat(pos, yawdeg=0.0, rx=0.0, ry=0.0):
    t = vtk.vtkTransform(); t.PostMultiply(); t.RotateX(rx); t.RotateY(ry); t.RotateZ(yawdeg); t.Translate(*pos)
    m = t.GetMatrix(); return [[m.GetElement(i, j) for j in range(4)] for i in range(4)]

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    S = Scene()
    ctr = np.array([0, 70, 560])
    if mode == 'stills':
        S.pose(); S.camera((2300, 2700, 1700), (0, 80, 620)); S.text('BRICKED SORTING V13, closed: two 2x1 bricks stacked', 30, 70, 26, bold=True)
        S.text(f"{A['layout']['X_HALF']*2:.0f} x {A['layout']['Y_FRONT']-A['layout']['Y_BACK']:.0f} mm footprint, {A['layout']['Z_STUD_TOP']:.0f} mm to stud top. Loading stud = open funnel.", 30, 35, 18)
        S.save(OUT / 'v13_closed.png')
        S.group_visible(['shell'], 0); S.pose(); S.camera((2100, 2500, 1600), (0, 80, 620))
        S.text('No shell: drum, V1, V2, scanner, lift and 16 bins', 30, H - 50, 26, bold=True); S.save(OUT / 'v13_no_shell.png')
        S.group_visible(['frame', 'deck', 'drum', 'drum_rot'], 0); S.hide_labels(['52_', '53_', '50_', '51_', '54_', '55_', 'tray-support', 'leaf-spring', 'camera-ref', '61_'])
        S.pose(H=L['H_of']['upper-4'], yaw=L['slot_yaw']['4'], door=55, led=True)
        S.camera((420, 470, 600), (0, 0, 650), 34); S.text('Scanner: doors open 55 deg (camera bridge hidden). Scoop below at the upper bin pose.', 30, 30, 20, bold=True); S.save(OUT / 'v13_scanner.png')
        S.group_visible(['frame', 'deck', 'drum', 'drum_rot'], 1); S.hide_labels(['52_', '53_', '50_', '51_', '54_', '55_', 'tray-support', 'leaf-spring', 'camera-ref', '61_'], 1); S.group_visible(['shell'], 1); S.pose(drawer='upper'); S.camera((1500, 2700, 1200), (0, 260, 400))
        S.text('Upper drawer pulled out 350 mm: lift a bin straight up', 30, H - 50, 24, bold=True); S.save(OUT / 'v13_drawer_open.png')
        S.group_visible(['shell'], 0); S.pose(); S.camera((0, 0, 3600), (0, 80, 400), 24); S.group_visible(['deck'], 0); S.group_visible(['isolate', 'V1', 'V2', 'drum', 'drum_rot', 'spring', 'slider', 'door1', 'door-1', 'led'], 0)
        S.text('Top view without the isolation deck: bins, lift and drawers', 30, H - 50, 24, bold=True); S.save(OUT / 'v13_top.png')
        # V13 close-ups: lift tie, carrier tiles, camera mount, APDS mount, latch, electronics bay
        S.group_visible(['isolate', 'V1', 'V2', 'drum', 'drum_rot', 'spring', 'slider', 'door1', 'door-1', 'led', 'deck'], 1); S.group_visible(['shell'], 0); S.pose()
        S.hide_labels(['52_', '53_', '50_', '51_', '54_', '55_', 'tray-support', 'leaf-spring', '61_', 'drum'])
        S.camera((-700, -900, 700), (0, -110, 520), 30); S.text('71 lift tower tie: cap screws up to the back deck extrusion', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_lift_tie.png')
        S.hide_labels(['52_', '53_', '50_', '51_', '54_', '55_', 'tray-support', 'leaf-spring', '61_', 'drum'], 1)
        S.group_visible(['isolate', 'V1', 'V2', 'drum', 'drum_rot', 'spring', 'slider', 'door1', 'door-1', 'led', 'deck', 'lift', 'lift_moving', 'lift_yaw'], 0); S.pose(drawer='upper')
        S.camera((300, 1500, 900), (0, 420, 250), 32); S.text('72 carrier tiles (8 per tier, 3 mm) with locator and splice holes; 75 latch on the right rail', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_carrier_tiles.png')
        S.group_visible(['isolate', 'V1', 'V2', 'drum', 'drum_rot', 'spring', 'slider', 'door1', 'door-1', 'led', 'deck', 'lift', 'lift_moving', 'lift_yaw'], 1); S.pose()
        S.group_visible(['frame', 'deck', 'drum', 'drum_rot', 'V1', 'V2', 'spring'], 0); S.hide_labels(['52_', '53_', '50_', '51_', 'tray-support', 'led-1', 'led-strip-1'])
        S.camera((-120, -520, 1000), (-10, -20, 760), 26); S.text('73 XIAO Sense camera mount on the bridge; 74 APDS-9960 mount beside the doors', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_camera_mounts.png')
        S.group_visible(['frame', 'deck', 'drum', 'drum_rot', 'V1', 'V2', 'spring'], 1); S.hide_labels(['52_', '53_', '50_', '51_', 'tray-support'], 1)
        S.pose(); S.camera((1150, 900, 420), (430, 80, 120), 30); S.text('76 electronics tray in the +X end bay: PSU, buck, XIAO boards, drivers, MCP23017', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_electronics.png')
        # V13 drum: static outlet plate on the cradles, helical flight inside the barrel (barrel ghosted)
        S.group_visible(['shell', 'frame', 'deck', 'lift', 'lift_moving', 'lift_yaw', 'isolate', 'V1', 'V2', 'spring', 'slider', 'door1', 'door-1', 'led', 'drawer_upper', 'drawer_lower', 'drawer_upper_face', 'drawer_lower_face', 'electronics'], 0)
        for inst, a, _ in S.actors:
            if inst['label'].startswith(('52_', '53_', '50_', '51_')): a.SetVisibility(1)
        S.pose(); dr = np.array(L['DRUM_REAR']); u = np.array(L['U_AX']) / np.linalg.norm(L['U_AX'])
        fc = dr + u * 120
        S.camera(tuple(fc + np.array([560, -520, 120])), tuple(fc), 30)
        S.text('V13 drum: 49b static outlet plate (orange) bolted to the cradles; barrel turns inside it', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_drum_plate.png')
        S.pose()
        for inst, a, m47 in S.actors:
            if inst['label'].startswith('47b'):
                a.GetProperty().SetOpacity(.22)
                r_ = vtk.vtkSTLReader(); r_.SetFileName(str(ROOT / 'isolate_v13' / '47b_flight_only_PREVIEW.stl')); r_.Update()
                n_ = vtk.vtkPolyDataNormals(); n_.SetInputConnection(r_.GetOutputPort()); n_.Update()
                S.add_mesh(n_.GetOutput(), m47, (.9, .55, .12))
            if inst['label'].startswith('49b'): a.SetVisibility(0)
        S.camera(tuple(fc + np.array([380, -480, 240])), tuple(dr + u * 70), 30)
        S.text('V13 drum: 1.75-turn helical flight inside the barrel (barrel ghosted, flight orange) pushes bricks to the outlet', 30, H - 50, 22, bold=True); S.save(OUT / 'v13_drum_flight.png')
        for inst, a, _ in S.actors:
            if inst['label'].startswith('47b'): a.GetProperty().SetOpacity(1)
            if inst['label'].startswith('49b'): a.SetVisibility(1)
        print('stills ok')

    if mode == 'anim':
        FPS = 30
        BR = brick_poly(); BLUE = (.18, .45, .78)
        S.group_visible(['shell'], 0); S.group_opacity(['deck'], .35)
        Lz = L
        fun = Lz['FUNNEL']; A_, B_, C_ = map(np.array, (fun['A'], fun['B'], fun['C']))
        dr0, dr1, u = np.array(Lz['DRUM_REAR']), np.array(Lz['DRUM_FRONT']), np.array(Lz['U_AX'])
        v1a, v1b = map(np.array, Lz['V1']); v2a, v2b = map(np.array, Lz['V2'])
        ZS = Lz['Z_S']; target = ('lower', 4); key = 'lower-4'
        Ht, yawt = Lz['H_of'][key], Lz['slot_yaw']['4']
        Hpark = (Lz['H_MIN'] + Lz['H_MAX']) / 2
        hub_face = lambda Hh: Lz['LIFT_O'][2] + Hh + Lz['HUB_ABOVE_CARRIAGE']
        sc = Lz['scoop']; tan40 = math.tan(math.radians(sc['SLOPE']))
        seg = []                                   # (duration s, function(t in 0..1) -> dict)
        def lerp(a, b, t): return a + (b - a) * t
        def ease(t): return t * t * (3 - 2 * t)
        sx_, sy_ = Lz['STUD_C'][0]
        top = np.array([sx_, sy_, Lz['Z_STUD_TOP'] + 140]); hop = A_ + np.array([0, 0, 18])
        st = {'H': Hpark, 'yaw': 0.0, 'door': 0.0, 'drum': 0.0, 'led': False}
        def S_(d, fn, cap): seg.append((d, fn, cap))
        S_(1.2, lambda t: dict(pos=lerp(top, hop, t * t), rot=(0, 0, 200 * t)), '1  Drop a piece into the open stud (the funnel)')
        S_(0.5, lambda t: dict(pos=lerp(hop, B_ + np.array([0, 0, 10]), t), rot=(0, 0, 200)), '1  Hopper into the straight inlet chute')
        S_(0.6, lambda t: dict(pos=lerp(B_ + np.array([0, 0, 10]), C_ + np.array([0, 0, 6]), ease(t)), rot=(0, -35, 200)), '1  Chute enters the drum through the rear guard')
        def drum_fn(t):
            ax = lerp(20.0, 170.0, t); ang = math.radians(-60 + 40 * math.sin(t * 14))
            perp = np.cross(u, [0, 1, 0]); perp /= np.linalg.norm(perp); side = np.array([0, 1.0, 0])
            p = dr0 + u * ax + (math.cos(ang) * perp + math.sin(ang) * side) * 64
            return dict(pos=p, rot=(360 * t * 3, 140 * t, 90 * t), drum=360 * t * 2.2)
        S_(3.0, drum_fn, '2  Drum tumbles and meters pieces forward (2 to 10 rpm)')
        out = dr1 + u * 6 + np.array([0, 0, -40]); land1 = v1a + (v1b - v1a) * 0.12 + np.array([0, 0, 1])
        S_(0.35, lambda t: dict(pos=lerp(out, land1, t * t), rot=(0, 0, 180), drum=792 + 30 * t), '2  Out of the eccentric cap onto V1')
        S_(1.8, lambda t: dict(pos=lerp(land1, v1b + np.array([0, 0, 1]), t) + np.array([0, 0, 1.5 * abs(math.sin(t * 60))]), rot=(0, 0, 180), vib=(0.7 * math.sin(t * 90), 0)), '3  V1 vibrates the piece along and spreads groups out')
        land2 = v2a + (v2b - v2a) * 0.06 + np.array([0, 0, 1])
        S_(0.3, lambda t: dict(pos=lerp(v1b + np.array([0, 0, 1]), land2, t * t), rot=(0, 0, 180 + 60 * t)), '3  Short drop V1 -> V2 (flared receiving end)')
        S_(1.6, lambda t: dict(pos=lerp(land2, v2b + np.array([0, 0, 1]), t) + np.array([0, 0, 1.2 * abs(math.sin(t * 50))]), rot=(0, 0, 255), vib=(0, 0.6 * math.sin(t * 90))), '4  V2: short pulses, conservative slope')
        ramp0 = np.array([v2b[0] + 2, 0.0, ZS + 30]); onfloor = np.array([0.0, 0.0, ZS])
        S_(0.6, lambda t: dict(pos=lerp(v2b + np.array([0, 0, 1]), ramp0, t) if t < .4 else lerp(ramp0, onfloor, ease((t - .4) / .6)), rot=(0, 0, 270)), '4  Landing ramp turns it onto the scanner doors')
        def scan(t):
            d = dict(pos=onfloor, rot=(0, 0, 270), led=0.15 < t < 0.55)
            d['H'] = lerp(Hpark, Ht, ease(min(1, t / 0.9))); d['yaw'] = lerp(0, yawt, ease(min(1, t / 0.9)))
            return d
        S_(1.6, scan, '5  Hold still, lights on, camera -> Kratos: "Brick 2x4, Blue" -> bin 1-4. Lift and scoop move to 1-4')
        hf = hub_face(Ht); land_s = np.array([0, 0, hf + 4])
        def drop(t):
            d = dict(H=Ht, yaw=yawt, door=lerp(0, 55, ease(min(1, t / .5))))
            p = lerp(onfloor, land_s, (max(0, t - .25) / .75) ** 2) if t > .25 else onfloor
            d['pos'] = p; d['rot'] = (0, 0, 270 + 60 * t); return d
        S_(0.7, drop, '6  One servo opens both doors; the piece drops onto the scoop')
        yr = math.radians(yawt); dirv = np.array([-math.sin(yr), math.cos(yr), 0])
        nose = np.array([0, 0, hf + 4]) + dirv * sc['SC_NOSE'] - np.array([0, 0, sc['SC_NOSE'] * tan40])
        S_(0.45, lambda t: dict(H=Ht, yaw=yawt, door=55, pos=lerp(land_s, nose, t * t), rot=(0, -40, 270 + yawt)), '7  Slides down the 40 deg scoop to the 40 mm outlet')
        v = 1000.0; vh, vz = v * math.cos(math.radians(40)), v * math.sin(math.radians(40))
        floor_z = Lz['TIERS']['lower'] + Lz['bins']['LOWER_SEAT'] + 2.4
        tland = (-vz + math.sqrt(vz * vz + 2 * 9810 * (nose[2] - floor_z))) / 9810
        def fly(t):
            tt = t * tland; p = nose + dirv * vh * tt - np.array([0, 0, vz * tt + 4905 * tt * tt])
            return dict(H=Ht, yaw=yawt, door=55, pos=p, rot=(0, -40 + 40 * t, 270 + yawt))
        S_(max(0.5, tland * 3), fly, f'8  Through the window into bin 1-4 (est. exit 1.0 m/s, lands r = {sc["SC_NOSE"] + vh * tland:.0f} mm)')
        endp = nose + dirv * vh * tland - np.array([0, 0, vz * tland + 4905 * tland * tland])
        S_(1.6, lambda t: dict(H=lerp(Ht, Hpark, ease(t)), yaw=lerp(yawt, 0, ease(t)), door=lerp(55, 0, ease(min(1, t * 2))), pos=endp, rot=(0, 0, 270 + yawt)), '9  Doors close, lift parks. Bin switch + log: 1 piece in 1-4')
        frames = OUT / '_frames'; frames.mkdir(exist_ok=True)
        for f in frames.glob('*.png'): f.unlink()
        S.group_visible(['drawer_lower_face', 'drawer_upper_face'], 0)
        S.group_opacity(['frame'], .18); S.hide_labels(['52_drum_cradle', '53_'], 1)
        for inst, a, _ in S.actors:
            if inst['label'].startswith(('52_drum_cradle', '53_', 'tray-support', 'rod-12mm', 'lift-brace', '61_', 'camera-ref')): a.GetProperty().SetOpacity(.25)
        states = []; total = 0.0
        for d, fn, cap in seg:
            nf = max(2, int(round(d * FPS)))
            for i in range(nf):
                t = i / (nf - 1); s_ = dict(st); s_.update(fn(t)); st.update({k: s_[k] for k in ('H', 'yaw', 'door', 'drum') if k in s_})
                s_['cap'] = cap; s_['T'] = total + t * d; states.append(s_)
            total += d
        P = np.array([x['pos'] for x in states]); Fp = P.copy()
        for i in range(len(P)):
            lo, hi = max(0, i - 18), min(len(P), i + 19); Fp[i] = P[lo:hi].mean(axis=0)
        def phase(x): return int(x['cap'].strip()[0])
        OFF = {1: ((.55, .65, .55), 850), 2: ((.6, .5, .6), 700), 3: ((-.55, .55, .65), 560), 4: ((-.45, -.25, .75), 480),
               5: ((.75, -.35, .5), 420), 6: ((.75, -.35, .45), 430), 7: ((.25, .45, .85), 560), 8: ((.2, .55, .85), 600), 9: ((.2, .55, .85), 650)}
        BIN = np.array([-math.sin(math.radians(yawt)) * 225, math.cos(math.radians(yawt)) * 225, Lz['TIERS']['lower'] + 60])
        CP, CF = [], []
        for i, x in enumerate(states):
            o, dd = OFF[phase(x)]; o = np.array(o) / np.linalg.norm(o)
            f = Fp[i] if phase(x) < 7 else (Fp[i] * .5 + BIN * .5)
            CF.append(f); CP.append(f + o * dd)
        CP, CF = np.array(CP), np.array(CF); CPs, CFs = CP.copy(), CF.copy()
        for i in range(len(CP)):
            lo, hi = max(0, i - 14), min(len(CP), i + 15); CPs[i] = CP[lo:hi].mean(axis=0); CFs[i] = CF[lo:hi].mean(axis=0)
        BR_COL = (1.0, .45, .05)
        n = 0
        for i, s_ in enumerate(states):
            S.pose(H=s_.get('H', Hpark), yaw=s_.get('yaw', 0), door=s_.get('door', 0), drum=s_.get('drum', 0), vib=s_.get('vib', (0, 0)), led=bool(s_.get('led', False)))
            rx, ry, rz = s_['rot']; S.add_mesh(BR, frame_mat(tuple(s_['pos']), rz, rx, ry), BR_COL)
            for q in P[max(0, i - 75):i:3]:
                sp = vtk.vtkSphereSource(); sp.SetRadius(3.0); sp.SetCenter(*q); sp.Update(); S.add_mesh(sp.GetOutput(), np.eye(4), (.95, .55, .1), .55)
            S.group_visible(['drawer_upper'], 0 if phase(s_) >= 6 else 1)
            S.camera(tuple(CPs[i]), tuple(CFs[i]), 32)
            t1 = S.text('BRICKED SORTING V13 - one piece, start to finish. Kinematic animation from the CAD, not a physics test.', 20, H - 36, 17, bold=True)
            t2 = S.text(s_['cap'], 20, 22, 21, color=(.06, .3, .5), bold=True)
            for tt in (t1, t2):
                tp = tt.GetTextProperty(); tp.SetBackgroundColor(1, 1, 1); tp.SetBackgroundOpacity(.85)
            S.text(f"t = {s_['T']:4.1f} s", W - 130, 22, 18)
            S.save(frames / f'f{n:04d}.png'); n += 1
        print('frames', n, 'seconds', round(total, 1))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.png'), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(OUT / 'v13_one_piece_run.mp4')], check=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(OUT / 'v13_one_piece_run.mp4'), '-vf', 'fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer', str(OUT / 'v13_one_piece_run.gif')], check=True)
        print('video ok')
