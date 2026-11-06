"""Copy the V13 STEPs that the V13 assembly loads by file (carriage V3, drum V7/V13) into ref/ under the
names assembly.json uses, plus an STL of each for rendering."""
from pathlib import Path
import json, shutil
import cadquery as cq
ROOT = Path(__file__).resolve().parent; REF = ROOT.parent.parent / 'reference_v13'
A = json.loads((REF / 'assembly.json').read_text())
src = {'isolate_v7/': 'drum_v7/', 'isolate_v13/': 'drum_v13/'}
for i in A['instances']:
    s = i['stl']
    if s.startswith('machine_v13'): continue
    rel = next((v + s[len(k):] for k, v in src.items() if s.startswith(k)), 'carriage_v3/' + s)
    dst = ROOT / 'ref' / s.replace('.stl', '.step'); dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists(): continue
    shutil.copy(REF / rel.replace('.stl', '.step'), dst)
    w = cq.importers.importStep(str(dst)); bb = w.val().BoundingBox()
    cq.exporters.export(w, str(dst.with_suffix('.stl')), tolerance=.1, angularTolerance=.2)
    print(s, [round(x, 1) for x in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
