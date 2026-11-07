"""Shared helpers for the V14 build scripts (CadQuery 2.8). Units mm.
Every module script reads the interface through IF; never retype its numbers."""
from pathlib import Path
import json, math
import cadquery as cq

V14 = Path(__file__).resolve().parent
IF = json.loads((V14 / 'interface.json').read_text())
BED = [248, 248, 248]                # usable P2S bed (runbook)
INSERT_D, INSERT_DEPTH = 4.1, 5.7    # M3 generic insert (runbook: 4.0-4.2, verify with calipers)
M3_CLR = 3.4
CB_D, CB_DEPTH = 6.5, 3.5
FIT = 0.07                           # dovetail / sliding fit per side (runbook)
PRESS = -0.02                        # press pocket per side (runbook)
WOOD_SCREW = 3.6                     # #6 wood screw clearance


def bbox(shape):
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    b = s.BoundingBox()
    return [round(b.xmin, 3), round(b.ymin, 3), round(b.zmin, 3),
            round(b.xmax, 3), round(b.ymax, 3), round(b.zmax, 3)]


def extent(shape):
    b = bbox(shape)
    return [round(b[3] - b[0], 2), round(b[4] - b[1], 2), round(b[5] - b[2], 2)]


def print_pose(shape, flip=False, diag=None):
    """Lay a part on the bed: optional flip (rotate 180 about X), then put
    z min at 0 and center it. diag=True rotates 45 deg about Z (long parts),
    None picks it automatically when the straight footprint does not fit."""
    w = shape if isinstance(shape, cq.Workplane) else cq.Workplane().add(shape)
    if flip:
        w = w.rotate((0, 0, 0), (1, 0, 0), 180)
    e = extent(w)
    if diag is None:
        diag = not (e[0] <= BED[0] and e[1] <= BED[1])
    if diag:
        w = w.rotate((0, 0, 0), (0, 0, 1), 45)
    b = bbox(w)
    w = w.translate((-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]))
    return w, diag


def bed_fit(shape_on_bed):
    e = extent(shape_on_bed)
    return {'bed_extent': e, 'fits_248': all(e[i] <= BED[i] + 1e-6 for i in range(3))}


def export(shape, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    w = shape if isinstance(shape, cq.Workplane) else cq.Workplane().add(shape)
    if path.suffix == '.stl':
        cq.exporters.export(w, str(path), tolerance=0.02, angularTolerance=0.15)
    else:
        cq.exporters.export(w, str(path))


G_PER_H = 45.0   # day profile throughput (runbook backplate timing), 0.4 nozzle


def grams(shape, density=1.24, shell=1.5, infill=0.15):
    """BJ's day profile (vault runbooks/3d-printing.md): 4 walls x 0.42 = 1.68 mm per side, 5 top / 3 bottom layers
    (1.5 mm averaged over the area) solid, 15 % sparse infill inside. Thin parts come out fully solid.
    PLA 1.24, PETG 1.27 g/cm3."""
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    v = s.Volume(); a = s.Area()
    solid = min(v, a * shell)
    return round((solid + (v - solid) * infill) / 1000 * density, 1)


def hours(g):
    return round(g / G_PER_H, 1)


# ---------------- rendering (VTK offscreen) ----------------
def _poly(shape, tol=0.2):
    import vtk, tempfile, os
    w = shape if isinstance(shape, cq.Workplane) else cq.Workplane().add(shape)
    fd, p = tempfile.mkstemp(suffix='.stl'); os.close(fd)
    cq.exporters.export(w, p, tolerance=tol, angularTolerance=0.3)
    r = vtk.vtkSTLReader(); r.SetFileName(p); r.Update()
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.Update()
    os.remove(p)
    return n.GetOutput()


def render(items, path, cam, focal, up=(0, 0, 1), size=(1280, 800), title=None, ortho=None):
    """items: list of (shape or vtkPolyData, (r,g,b), opacity)."""
    import vtk
    ren = vtk.vtkRenderer(); ren.SetBackground(0.965, 0.969, 0.973)
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(8)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(*size)
    rw.SetAlphaBitPlanes(1); rw.SetMultiSamples(0)
    for shp, col, op in items:
        pd = shp if isinstance(shp, vtk.vtkPolyData) else _poly(shp)
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd)
        a = vtk.vtkActor(); a.SetMapper(mp); pr = a.GetProperty()
        pr.SetColor(*col); pr.SetOpacity(op); pr.SetSpecular(.15); pr.SetSpecularPower(20); pr.SetAmbient(.15); pr.SetDiffuse(.85)
        ren.AddActor(a)
    c = ren.GetActiveCamera(); c.SetPosition(*cam); c.SetFocalPoint(*focal); c.SetViewUp(*up)
    if ortho: c.ParallelProjectionOn(); c.SetParallelScale(ortho)
    ren.ResetCameraClippingRange()
    l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetIntensity(0.9); ren.AddLight(l)
    if title:
        t = vtk.vtkTextActor(); t.SetInput(title); tp = t.GetTextProperty(); tp.SetFontSize(22); tp.SetColor(.15, .15, .18)
        t.SetPosition(16, size[1] - 40); ren.AddActor2D(t)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(str(path)); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
