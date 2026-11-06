"""Shared helpers for the V14 interface-5 module scripts (CadQuery 2.8). Units mm.
Reads ../interface.json; print rules follow Mnemosyne runbooks/3d-printing.md (BJ's P2S day profile)."""
from pathlib import Path
import json, math
import cadquery as cq

V14 = Path(__file__).resolve().parent.parent
IF = json.loads((V14 / 'interface.json').read_text())
BED = [248.0, 248.0, 248.0]                   # usable bed (runbook: design to ~248)

# runbook fits (per side)
FIT_SLIDE = 0.07          # sliding / dovetail, BJ's "normal"
FIT_PRESS = -0.02         # press pocket (pocket smaller than the piece)
INSERT_M3_D, INSERT_M3_DEPTH = 4.1, 5.8       # generic M3 heat-set, verify with calipers (inventory/parts-owned.md)
M3_CLR, M3_CSK_D = 3.4, 6.4
WOOD_SCREW_CLR = 3.6      # #6 wood screw clearance (interface)
WOOD_SCREW_CSK = 7.0      # #6 flat head
CHAMFER_BED = 0.6         # bed-edge chamfer against elephant foot (interface)

# day profile: 0.4 nozzle, 0.2 layers, 4 walls (1.68 mm), 3 bottom (0.6) / 5 top (1.0) layers, 15 % sparse
WALL_T, TOP_T, BOT_T, INFILL = 1.68, 1.0, 0.6, 0.15
DENSITY = {'PLA': 1.24, 'PETG': 1.27, 'TPU': 1.21}


def bbox(shape):
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    b = s.BoundingBox()
    return [round(b.xmin, 3), round(b.ymin, 3), round(b.zmin, 3), round(b.xmax, 3), round(b.ymax, 3), round(b.zmax, 3)]


def extent(shape):
    b = bbox(shape)
    return [round(b[3] - b[0], 2), round(b[4] - b[1], 2), round(b[5] - b[2], 2)]


def print_pose(shape, flip=False, diag=None, rot=None):
    """Lay a part on the bed: optional rot (axis, deg) then flip (180 about X), then z min = 0, centred.
    diag=True rotates 45 deg about Z; None picks it when the straight footprint does not fit."""
    w = shape if isinstance(shape, cq.Workplane) else cq.Workplane().add(shape)
    if rot:
        w = w.rotate((0, 0, 0), rot[0], rot[1])
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


def grams(shape, material='PLA'):
    """Day-profile estimate: 4 walls solid (1.68 mm per side face), 1.0 top + 0.6 bottom skins, 15 % sparse inside.
    Approximated as a 1.5 mm average solid shell over the whole surface; thin parts (<= 3 mm) come out solid."""
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    v = s.Volume(); a = s.Area()
    solid = min(v, a * 1.5)
    return round((solid + (v - solid) * INFILL) / 1000 * DENSITY.get(material, 1.24), 1)


def hours(g, shape):
    """Print time from BJ's measured day-profile rate: ~49 g/h on a chunky part (120 g in 2 h 26, runbook).
    Flat solid sheets run faster (long straight lines): ~75 g/h."""
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    v = s.Volume(); a = s.Area()
    sheet = v <= a * 1.5 * 1.05     # printed solid -> sheet-like
    return round(g / (75.0 if sheet else 49.0), 2)


def cyl(p, d, r, L):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, L, cq.Vector(*p), cq.Vector(*d)))


def boxc(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def box(cx, cy, z0, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((cx, cy, z0))


def ov(a, b):
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1] or a[5] <= b[2] or b[5] <= a[2])


def vol(a, b):
    try:
        v = a.intersect(b)
        return v.val().Volume() if v.vals() else 0.0
    except Exception:
        return -1.0


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


def render(items, path, cam, focal, up=(0, 0, 1), size=(1280, 800), title=None, ortho=None, bg=(0.965, 0.969, 0.973)):
    """items: list of (shape or vtkPolyData, (r,g,b), opacity)."""
    import vtk
    ren = vtk.vtkRenderer(); ren.SetBackground(*bg)
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(8)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(*size)
    rw.SetAlphaBitPlanes(1); rw.SetMultiSamples(0)
    for shp, col, op in items:
        pd = shp if isinstance(shp, vtk.vtkPolyData) else _poly(shp)
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd)
        a = vtk.vtkActor(); a.SetMapper(mp); pr = a.GetProperty()
        pr.SetColor(*col); pr.SetOpacity(op); pr.SetSpecular(.15); pr.SetSpecularPower(20); pr.SetAmbient(.2); pr.SetDiffuse(.8)
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
