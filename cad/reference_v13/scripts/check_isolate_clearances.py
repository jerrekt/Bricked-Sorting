"""Additional sampled CAD clearances for the V7 prototype,not a flow simulation."""
from pathlib import Path
import json
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'isolate_v7'
s=json.loads((OUT/'isolate_and_machine_dimensions.json').read_text());cache={}
def shape(a):
    key=a['step_file']+str(a['xyz'])
    if key in cache:return cache[key]
    p=cq.importers.importStep(str(ROOT/a['step_file']))
    if'rotation_matrix'in a:
        R=np.array(a['rotation_matrix']);p=cq.Workplane(obj=p.val().located(cq.Location(cq.Plane(origin=tuple(a['xyz']),xDir=tuple(R[:,0]),normal=tuple(R[:,2])))))
    else:
        for axis,k in(((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')):
            if a[k]:p=p.rotate((0,0,0),axis,a[k])
        p=p.translate(a['xyz'])
    cache[key]=p;return p
def get(prefix):return[shape(a)for a in s['actors']if a['name'].startswith(prefix)]
def hit(a,b):
    x,y=a.val().BoundingBox(),b.val().BoundingBox()
    if x.xmax<y.xmin or x.xmin>y.xmax or x.ymax<y.ymin or x.ymin>y.ymax or x.zmax<y.zmin or x.zmin>y.zmax:return 0.
    return a.val().intersect(b.val()).Volume()
p=s['proposed_isolate'];origin=np.array(p['drum']['rear_axis_xyz']);axis=np.array(p['drum']['front_axis_xyz'])-origin
errors=[];results=[]
for fixed_prefix,rotating_prefix in(('58_','47_'),('58_','48_'),('59_','47_'),('59_','49_')):
    f=get(fixed_prefix)[0];r=get(rotating_prefix)[0];worst=0.
    for phase in range(0,360,30):
        q=r.rotate(tuple(origin),tuple(origin+axis),phase);v=hit(f,q);worst=max(worst,v)
        if v>.05:errors.append({'fixed':fixed_prefix,'rotating':rotating_prefix,'phase':phase,'volume_mm3':v})
    results.append({'fixed':fixed_prefix,'rotating':rotating_prefix,'phases':12,'max_intersection_mm3':worst})
v=hit(get('59_')[0],get('60_')[0]);results.append({'pair':['V1','V2'],'intersection_mm3':v})
if v>.05:errors.append({'pair':['V1','V2'],'volume_mm3':v})
for prefix in('62_','63_'):
    for i,a in enumerate(get(prefix)):
        for tray in get('59_')+get('60_'):
            v=hit(a,tray)
            if v>.05:errors.append({'motor_mount':prefix,'instance':i,'tray_intersection_mm3':v})
report={'scope':'48 drum/transfer phase checks,V1-V2 interface,and motor-holder/tray static intersections only;not continuous/dynamic/material-flow validation.','results':results,'unexpected_intersections':errors}
(OUT/'additional_clearance_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
if errors:raise SystemExit(1)
