"""V14 (5.1) 'one brick' video: hopper -> chute -> drum -> V1 -> V2 -> scanner -> funnel -> scoop cup -> bin.
Static parts are tessellated once; the drum, carriage group, cup and brick are moved with VTK actor transforms.
Output: one_brick.mp4 (1280x720, 30 fps, ~25 s). Run: python3 build_video.py [preview]  (preview = 6 full-size frames only)
"""
import math, sys, importlib.util, subprocess, shutil
from pathlib import Path
import cadquery as cq, vtk
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import IF, _poly
from build_integration import load_dir, WT_FRAME, WT_DECK, DRAWER, SCOOP

FPS = 30; SIZE = (1280, 720)
spec = importlib.util.spec_from_file_location('bs', SCOOP / 'build_scoop.py'); bs = importlib.util.module_from_spec(spec)
sys.argv = ['x']; spec.loader.exec_module(bs)
XC = IF['bins']['x_centers']; TARGET = XC[2]            # bin 3, front row
DRUM_AXIS = (40.0, 508.9)                                 # y, z (axis along +X)


def col(n):
    if n.startswith(('110', '111', '112', '113', '114', '115', '135')): return (0.72, 0.10, 0.10)
    if n.startswith(('130', '131')): return (0.80, 0.18, 0.18)
    if n.startswith('10') or 'ply' in n: return (0.85, 0.75, 0.55)
    if n.startswith(('12',)): return (0.4, 0.4, 0.42)
    if n.startswith(('47', '48', '49')): return (0.75, 0.25, 0.2)
    if n.startswith(('201', '202')): return (0.85, 0.2, 0.2)
    if n.startswith(('203', '204', '211')): return (0.2, 0.6, 0.4)
    if n.startswith('2'): return (0.45, 0.45, 0.5)
    if '169_bin' in n: return (0.96, 0.87, 0.65)
    if '167_' in n: return (0.1, 0.35, 0.7)
    if '168_' in n: return (0.1, 0.55, 0.3)
    return (0.6, 0.62, 0.66)


def actor(pd, c, op=1.0):
    mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd); a = vtk.vtkActor(); a.SetMapper(mp); p = a.GetProperty()
    p.SetColor(*c); p.SetOpacity(op); p.SetSpecular(.15); p.SetSpecularPower(20); p.SetAmbient(.15); p.SetDiffuse(.85)
    return a


def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def ease(t): return t * t * (3 - 2 * t)


def path_at(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1: return lerp(p0, p1, ease((t - t0) / (t1 - t0)))
    return keys[-1][1]


def main(preview=False):
    F = load_dir(WT_FRAME / 'world'); K = load_dir(WT_DECK / 'world'); D = load_dir(DRAWER / 'world'); S = load_dir(SCOOP / 'world')
    drum_names = ('47b', '54_', '55_')
    ren = vtk.vtkRenderer(); ren.SetBackground(0.965, 0.969, 0.973); ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(6)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(*SIZE); rw.SetAlphaBitPlanes(1); rw.SetMultiSamples(0)
    drum_actors = []
    for n, s in F + K + D + S:
        if n.endswith('_at_receive') or n == 'NEMA17_dummy': continue
        if n.startswith(('110', '111', '112', '113', '114', '13', '101', '109')): continue  # skins, roof, studs, top rails: off
        a = actor(_poly(s), col(n), 0.35 if n.startswith('100') else 1.0)
        if n.startswith(drum_names): drum_actors.append(a)
        ren.AddActor(a)
    for n, s in F:                                        # studs + roof as a faint ghost so the brick shape still reads
        if n.startswith(('13', '114')): ren.AddActor(actor(_poly(s, 0.5), (0.8, 0.2, 0.2), 0.12))
    ren.AddActor(actor(_poly(bs.motor_dummy()), (0.3, 0.3, 0.32)))
    mv0 = bs.moving_at(0.0, 0.0)                          # moving scoop group, carriage-local (xc = 0)
    car_actors = [actor(_poly(mv0['carriage']), (0.95, 0.55, 0.15)), actor(_poly(mv0['bracket']), (0.95, 0.55, 0.15)),
                  actor(_poly(mv0['servo']), (0.15, 0.25, 0.6))] + [actor(_poly(r), (0.5, 0.5, 0.55)) for r in mv0['rollers']]
    cup_actor = actor(_poly(mv0['cup']), (0.98, 0.8, 0.2))
    for a in car_actors + [cup_actor]: ren.AddActor(a)
    link_cache = {}; link_actor = None
    brick = actor(_poly(cq.Workplane().box(16, 32, 10).edges('|Z').fillet(1)), (0.1, 0.4, 0.9)); ren.AddActor(brick)
    # ---------- timeline (s) ----------
    T_SCAN1 = 12.5; T_CUP = 14.0; T_ARRIVE = 16.5; T_TILT = 17.5; T_SLIDE = 18.3; T_LAND = 19.0; T_BACK = 20.0; T_HOME = 23.0; T_END = 25.0
    PZ = bs.PIVOT_Z + 10
    brick_keys = [(0.0, (-180, 0, 668)), (0.8, (-190, 15, 600)), (1.6, (-210, 40, 560)), (2.6, (-140, 40, 480)),
                  (3.4, (-110, 55, 445)), (4.2, (-70, 20, 448)), (5.0, (-20, 60, 446)), (5.8, (30, 40, 447)), (6.4, (45, 40, 440)),
                  (7.0, (60, 15, 428)), (8.0, (60, 140, 416)), (8.4, (75, 146, 408)), (9.6, (172, 10, 393)), (10.2, (204, 0, 384)),
                  (10.8, (240, 0, 381)), (T_SCAN1, (240, 0, 381)), (13.0, (240, 0, 320)), (13.6, (240, 0, 272)), (T_CUP, (240, 0, PZ))]

    def xc_at(t):
        if t < T_CUP: return bs.X_RECEIVE
        if t < T_ARRIVE: return bs.X_RECEIVE + (TARGET - bs.X_RECEIVE) * ease((t - T_CUP) / (T_ARRIVE - T_CUP))
        if t < T_BACK: return TARGET
        if t < T_HOME: return TARGET + (bs.X_RECEIVE - TARGET) * ease((t - T_BACK) / (T_HOME - T_BACK))
        return bs.X_RECEIVE

    def tilt_at(t):
        if t < T_ARRIVE: return 0.0
        if t < T_TILT: return -bs.TILT * ease((t - T_ARRIVE) / (T_TILT - T_ARRIVE))
        if t < T_LAND + 0.3: return -bs.TILT
        if t < T_BACK: return -bs.TILT * (1 - ease((t - T_LAND - 0.3) / (T_BACK - T_LAND - 0.3)))
        return 0.0

    def brick_at(t):
        if t < T_CUP: return path_at(brick_keys, t)
        xc = xc_at(t)
        if t < T_TILT:
            th = math.radians(-tilt_at(t)); return (xc, 10 * math.sin(th), bs.PIVOT_Z + 10 * math.cos(th))
        if t < T_SLIDE:
            u = ease((t - T_TILT) / (T_SLIDE - T_TILT)); return (xc, 10 + 70 * u, PZ - 50 * u)
        if t < T_LAND:
            u = (t - T_SLIDE) / (T_LAND - T_SLIDE); return (xc, 80 + 22 * u, PZ - 50 - (PZ - 50 - 60) * u * u)
        return (xc, 102, 60)

    def captions(t):
        if t < 2.0: return 'drop a brick in the hopper'
        if t < 7.0: return 'tumbler drum singulates it'
        if t < 10.6: return 'trays V1 / V2 feed the scanner'
        if t < 13.0: return 'scanner: colour + size -> bin choice'
        if t < 14.2: return 'trapdoor -> funnel -> scoop cup'
        if t < 17.5: return 'scoop carriage drives to bin 3'
        if t < 20.0: return 'cup tilts 40 deg, brick lands in the bin'
        return 'scoop returns under the funnel'
    txt = vtk.vtkTextActor(); tp = txt.GetTextProperty(); tp.SetFontSize(26); tp.SetColor(.15, .15, .18); txt.SetPosition(20, SIZE[1] - 44); ren.AddActor2D(txt)
    sub = vtk.vtkTextActor(); sp = sub.GetTextProperty(); sp.SetFontSize(18); sp.SetColor(.4, .4, .45); sub.SetPosition(20, 16)
    sub.SetInput('Bricked Sorting V14 (interface 5.1) - CAD animation, skin and roof removed'); ren.AddActor2D(sub)
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1)
    lt = vtk.vtkLight(); lt.SetLightTypeToCameraLight(); lt.SetIntensity(0.9); ren.AddLight(lt)
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.ReadFrontBufferOff()
    tmp = HERE / '_frames'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    n_frames = int(T_END * FPS)
    frames = [int(s * FPS) for s in (0.5, 4.5, 9, 12, 15.5, 18.6)] if preview else range(n_frames)
    for k in frames:
        t = k / FPS
        ang = math.radians(135 - 70 * t / T_END); r = 1350
        b = brick_at(t); foc = (0.2 * b[0], 20, 300 + 0.25 * (b[2] - 300))
        cam.SetPosition(foc[0] + r * math.cos(ang), foc[1] + r * math.sin(ang), 650 + 150 * (1 - t / T_END)); cam.SetFocalPoint(*foc)
        ren.ResetCameraClippingRange()
        tr = vtk.vtkTransform(); tr.Translate(0, DRUM_AXIS[0], DRUM_AXIS[1]); tr.RotateX(-120 * t); tr.Translate(0, -DRUM_AXIS[0], -DRUM_AXIS[1])
        for a in drum_actors: a.SetUserTransform(tr)
        xc = xc_at(t); tilt = tilt_at(t)
        for a in car_actors: a.SetPosition(xc, 0, 0)
        tc = vtk.vtkTransform(); tc.Translate(xc, 0, bs.PIVOT_Z); tc.RotateX(tilt); tc.Translate(0, 0, -bs.PIVOT_Z); cup_actor.SetUserTransform(tc)
        key = round(tilt / 4) * 4
        if key not in link_cache: link_cache[key] = _poly(bs.linkage_local(float(key)))
        if link_actor is not None: ren.RemoveActor(link_actor)
        link_actor = actor(link_cache[key], (0.75, 0.75, 0.78)); link_actor.SetPosition(xc, 0, 0); ren.AddActor(link_actor)
        brick.SetPosition(*b); brick.SetOrientation(0, 0, 25 * math.sin(t * 3) if t < 7 else 0)
        txt.SetInput(captions(t))
        rw.Render(); w2i.Modified(); w2i.Update()
        wr = vtk.vtkPNGWriter(); wr.SetFileName(str(tmp / f'f_{k:04d}.png')); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
        if k % 60 == 0: print('frame', k, '/', n_frames, flush=True)
    if preview: print('preview frames in', tmp); return
    out = HERE / 'one_brick.mp4'; part = HERE / 'one_brick_part.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-framerate', str(FPS), '-i', str(tmp / 'f_%04d.png'), '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', str(part)], capture_output=True)
    if r.returncode == 0: part.rename(out); shutil.rmtree(tmp); print('wrote', out)
    else: print(r.stderr.decode()[-2000:])


if __name__ == '__main__':
    main(preview='preview' in sys.argv)
