"""One small preview PNG + printed size (mm) per part in print_status.json, for the website Prints page.
Writes OUT/<part>.png and OUT/previews.json {part: {"dims": [x, y, z], "png": "previews/<part>.png"}} (sizes as printed on the bed).
Usage: python3 make_previews.py OUT_DIR
"""
import glob, json, sys
from pathlib import Path
import numpy as np, trimesh, vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

HERE = Path(__file__).resolve().parent
ROOTS = ['/home/claude/wt_frame5/cad/v14/frame/print', '/home/claude/wt_deck5/cad/v14/deck/print',
         '/home/claude/wt_all/cad/v14/drawer/print', '/home/claude/wt_all/cad/v14/scoop/print', '/home/claude/wt_all/cad/v14/vac/print', str(HERE / 'v13_reuse')]
COL = {'PETG': (0.30, 0.32, 0.36), 'PLA': (0.80, 0.10, 0.06), 'TPU': (0.15, 0.15, 0.15), 'YEL': (0.96, 0.78, 0.10), 'BLK': (0.16, 0.16, 0.17)}


def find(part):
    for r in ROOTS:
        hits = sorted(glob.glob(f'{r}/{part}_PRINT_*.stl')) or sorted(glob.glob(f'{r}/{part}_*PRINT_*.stl'))
        if hits: return hits[0]
    return None


def render(m, png, col):
    V = m.vertices.astype(np.float64); T = m.faces.astype(np.int64)
    pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(V, deep=True))
    ca = vtk.vtkCellArray(); ca.SetCells(len(T), numpy_to_vtkIdTypeArray(np.hstack([np.full((len(T), 1), 3), T]).ravel(), deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(ca)
    nm = vtk.vtkPolyDataNormals(); nm.SetInputData(pd); nm.SetFeatureAngle(35)
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nm.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(mp); a.GetProperty().SetColor(*col); a.GetProperty().SetSpecular(0.25); a.GetProperty().SetSpecularPower(20)
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1); ren.SetBackgroundAlpha(0.0); ren.AddActor(a)
    c = m.bounds.mean(0); r = np.linalg.norm(m.extents)
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*c); cam.SetPosition(*(c + np.array([0.9, -1.3, 1.0]) * r)); cam.SetViewUp(0, 0, 1)
    ren.ResetCamera(); cam.Zoom(1.25); ren.ResetCameraClippingRange()
    w = vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.SetAlphaBitPlanes(1); w.AddRenderer(ren); w.SetSize(320, 240); w.Render()
    g = vtk.vtkWindowToImageFilter(); g.SetInput(w); g.SetInputBufferTypeToRGBA(); g.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(str(png)); wr.SetInputConnection(g.GetOutputPort()); wr.Write()


def main(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    st = json.loads((HERE / 'print_status.json').read_text())
    res = {}
    for p in st['parts']:
        f = find(p['part'])
        if not f: print('no STL', p['part']); continue
        m = trimesh.load(f); m.apply_translation(-m.bounds[0])
        # colour = what BJ loads: red PLA for the visible shell (skin, studs, hopper, faces), TPU black, everything else PETG
        red = p['part'].startswith(('11', '12', '13', '201_', '168_face')) and '_ink' not in p['part']
        mat = 'TPU' if 'TPU' in p['part'] or 'TPU' in p['material'] else ('PLA' if red else 'PETG')
        if '_vac_' in p['part']:          # vacuum canister: yellow shell, black everything else
            mat = 'YEL' if p['part'].startswith(('250_', '255_', '256_')) else 'BLK'
        render(m, out / f"{p['part']}.png", COL[mat])
        res[p['part']] = {'dims': [round(float(v), 1) for v in m.extents], 'png': f"previews/{p['part']}.png"}
    (out / 'previews.json').write_text(json.dumps(res, indent=1))
    print(len(res), 'previews')


if __name__ == '__main__':
    main(sys.argv[1])
