"""Three V13C stills (VTK offscreen): closed, no shell at the upper dump pose, side elevation with the 762 mm line."""
from pathlib import Path
import json, math, sys
import numpy as np
import vtk
ROOT = Path(__file__).resolve().parent
VAR = sys.argv[1] if len(sys.argv) > 1 else 'v13c'
A = json.loads((ROOT / f'machine_{VAR}' / 'assembly.json').read_text()); L = A['layout']
OUT = ROOT.parent / 'stills'; OUT.mkdir(exist_ok=True)
W, H = 1600, 1000
cache = {}
def poly(stl):
    p = str(ROOT / stl) if stl.startswith('machine_') else str(ROOT / 'ref' / stl)
    if p not in cache:
        r = vtk.vtkSTLReader(); r.SetFileName(p); r.Update()
        n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.Update(); cache[p] = n.GetOutput()
    return cache[p]
def mat(m):
    t = vtk.vtkTransform(); mm = vtk.vtkMatrix4x4()
    for i in range(4):
        for j in range(4): mm.SetElement(i, j, float(m[i][j]))
    t.SetMatrix(mm); return t
def pose_m(inst, Hh, yaw):
    m = np.array(inst['m']); g = inst['group']
    if g in ('lift_moving', 'lift_yaw'):
        T = np.eye(4); T[2, 3] = Hh - L['H_MIN']; Rz = np.eye(4)
        if g == 'lift_yaw':
            t = math.radians(yaw); Rz[:2, :2] = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
        m = T @ Rz @ m
    return m
def shot(name, hide=(), Hh=None, yaw=0.0, cam=((1900, 2300, 1500), (0, 60, 520)), title='', line762=False, parallel=False):
    Hh = L['H_MIN'] if Hh is None else Hh
    ren = vtk.vtkRenderer(); ren.SetBackground(.965, .969, .973)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(W, H); rw.SetMultiSamples(8)
    for inst in A['instances']:
        if inst['group'] in hide or inst['label'] in hide: continue
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(poly(inst['stl']))
        a = vtk.vtkActor(); a.SetMapper(mp); a.SetUserTransform(mat(pose_m(inst, Hh, yaw)))
        pr = a.GetProperty(); pr.SetColor(*inst['color']); pr.SetSpecular(.15); pr.SetAmbient(.15); pr.SetDiffuse(.85); ren.AddActor(a)
    if line762:
        for z, col in ((762.0, (.85, .1, .1)), (L['Z_STUD_TOP'], (.1, .1, .1))):
            src = vtk.vtkCubeSource(); src.SetBounds(-700, 700, -300, 300, z - 1.5, z + 1.5)
            mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(src.GetOutputPort()); a = vtk.vtkActor(); a.SetMapper(mp)
            a.GetProperty().SetColor(*col); a.GetProperty().SetOpacity(.55 if z == 762 else .25); ren.AddActor(a)
    c = ren.GetActiveCamera(); c.SetPosition(*cam[0]); c.SetFocalPoint(*cam[1]); c.SetViewUp(0, 0, 1)
    if parallel: c.ParallelProjectionOn()
    ren.ResetCamera(); c.Zoom(1.25 if not parallel else 1.4)
    t = vtk.vtkTextActor(); t.SetInput(title); t.GetTextProperty().SetFontSize(28); t.GetTextProperty().SetColor(.1, .1, .12); t.SetDisplayPosition(24, H - 50); ren.AddActor2D(t)
    rw.Render(); w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(str(OUT / f'{VAR}_{name}.png')); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
tot = L['Z_STUD_TOP']
up3 = L['H_of']['upper-3']; lo6 = L['H_of']['lower-6']
shot('1_closed', title=f'{VAR.upper()} closed: {tot:.0f} mm tall (target 762)')
shot('2_no_shell_upper_dump', hide=('shell', 'drawer_lower_face', 'drawer_upper_face'), Hh=up3, yaw=L['slot_yaw']['3'],
     title=f'No shell, scoop at upper slot 3 (lift {up3:.0f}, yaw {L["slot_yaw"]["3"]})')
shot('3_side_762_line', hide=('shell', 'drawer_lower_face', 'drawer_upper_face'), Hh=lo6, yaw=L['slot_yaw']['6'], cam=((2600, 60, 560), (0, 60, 560)),
     title=f'Side, scoop at lower slot 6. Red = 762 mm, grey = top {tot:.0f} mm', line762=True, parallel=True)
print('stills in', OUT)
