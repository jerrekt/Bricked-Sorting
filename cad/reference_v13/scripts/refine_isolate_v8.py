"""V8 targeted refinement; original V7 files remain immutable. Units mm."""
from pathlib import Path
import json, hashlib, math, collections, struct
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'build_isolate_v7.py')}
exec(compile((ROOT/'build_isolate_v7.py').read_text().split('checks={}')[0], 'v7_geometry', 'exec'), ns)
OUT=ROOT/'isolate_v8';OUT.mkdir(exist_ok=True)
box,cyl,parts=ns['box'],ns['cyl'],ns['parts']
new={};old_to_new={}
# Same disk thickness, screw pattern, phase and offset as V7. No insert changes.
for diameter in (45,55):
 p=cyl(0,0,0,160,4).cut(cyl(40,0,-1,diameter,6))
 for deg in (90,210,330):
  t=math.radians(deg);p=p.cut(cyl(74*math.cos(t),74*math.sin(t),-1,3.4,6))
 new[f'72_drum_cap_{diameter}mm']=p
# Rear wall prevents upstream escape while preserving broad right-side drum entry.
p=parts['59_V1_catch_and_vibration_tray']
p=p.union(box(0.5,1.5,3,89,3,31))
new['73_V1_rear_containment']=p
# Walls rise only downstream of inlet relief, preserve 64mm top width.
p=parts['60_V2_vibration_tray']
for x in (-33.5,33.5):p=p.union(box(x,(55+ns['L2'])/2,27,3,ns['L2']-55,18))
p=p.cut(box(-30.5,ns['L2']-80+1.5,25,3,4.2,12))
new['74_V2_tall_containment']=p
old_to_new={'49_drum_eccentric_outlet_cap':'72_drum_cap_55mm','59_V1_catch_and_vibration_tray':'73_V1_rear_containment','60_V2_vibration_tray':'74_V2_tall_containment'}
checks={}
for name,p in new.items():
 p=p.clean();b=p.val().BoundingBox();shift=-b.zmin;p=p.translate((0,0,shift))
 assert p.val().isValid() and len(p.solids().vals())==1,name
 dims=[b.xlen,b.ylen,b.zlen];assert dims[0]+10<=256 and dims[1]+10<=256 and dims[2]<=256
 cq.exporters.export(p,str(OUT/(name+'.step')))
 cq.exporters.export(p,str(OUT/(name+'.stl')),tolerance=.07,angularTolerance=.12)
 raw=(OUT/(name+'.stl')).read_bytes();edges=collections.Counter();n=struct.unpack_from('<I',raw,80)[0]
 for i in range(n):
  vs=struct.unpack_from('<9f',raw,84+i*50+12);v=[tuple(round(t,4)for t in vs[j:j+3])for j in(0,3,6)]
  for a,b in ((0,1),(1,2),(2,0)):edges[tuple(sorted((v[a],v[b])))]+=1
 assert all(v==2 for v in edges.values()),name
 checks[name]={'dimensions_xyz':dims,'source_to_print_z_shift':shift,'valid_single_solid':True,'watertight':True,'fits_256_bed_with_5mm_brim':True,'sha256':hashlib.sha256(raw).hexdigest()}
 print('Exported',name,flush=True)
s=json.loads((ROOT/'isolate_v7/isolate_and_machine_dimensions.json').read_text())
for a in s['actors']:
 if a['name'] in old_to_new:
  old=a['name'];name=old_to_new[old];oldshift=-parts[old].val().BoundingBox().zmin
  a['xyz']=(np.array(a['xyz'])+np.array(a['rotation_matrix'])@np.array([0,0,oldshift-checks[name]['source_to_print_z_shift']])).tolist()
  a.update(name=name,source='v8',stl_file='isolate_v8/'+name+'.stl',step_file='isolate_v8/'+name+'.step')
s['revision']='V8 targeted isolation refinement';s['v8_changes']={'parts':checks,'replacement_mapping':old_to_new,'alternative_cap':'72_drum_cap_45mm','unchanged_65mm_cap':'isolate_v7/49_drum_eccentric_outlet_cap.stl','ratings':'8/10 untested integration concept','dimensions_note':'V7 dimensions remain authoritative except V8 replacement envelopes; full register is inherited, v8_changes supersedes conflicting fields.'}
(OUT/'refined_assembly_register.json').write_text(json.dumps(s,indent=2)+'\n')
# Check replacements against all other integrated physical parts (not reference envelopes).
def world(a):
 p=cq.importers.importStep(str(ROOT/a['step_file'])).val()
 if 'rotation_matrix' in a:
  R=np.array(a['rotation_matrix']);return p.located(cq.Location(cq.Plane(origin=tuple(a['xyz']),xDir=tuple(R[:,0]),normal=tuple(R[:,2]))))
 for axis,k in (((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')):
  if a.get(k,0):p=p.rotate((0,0,0),axis,a[k])
 return p.translate(tuple(a['xyz']))
def hit(p,q):
 a,b=p.BoundingBox(),q.BoundingBox()
 if a.xmax<=b.xmin or a.xmin>=b.xmax or a.ymax<=b.ymin or a.ymin>=b.ymax or a.zmax<=b.zmin or a.zmin>=b.zmax:return 0.
 return p.intersect(q).Volume()
actors=s['actors'];shapes={};results=[];errors=[]
for a in actors:
 if a['source']=='v8':
  p=world(a)
  for i,b in enumerate(actors):
   if a is b:continue
   if i not in shapes:shapes[i]=world(b)
   v=hit(p,shapes[i]);results.append({'a':a['name'],'b':b['name'],'intersection_mm3':v})
   if v>.05:errors.append(results[-1])
# Rear wall versus rotating barrel/cap: 24 phases each, cap alternatives nested in 65 opening.
v1=world(next(a for a in actors if a['name']=='73_V1_rear_containment'))
o=np.array(ns['DRUM_ORIGIN']);axis=ns['U'];phase=[]
for prefix in ('47_','72_'):
 p=world(next(a for a in actors if a['name'].startswith(prefix)))
 for deg in range(0,360,15):
  v=hit(v1,p.rotate(tuple(o),tuple(o+axis),deg));phase.append({'part':prefix,'phase':deg,'intersection_mm3':v})
  if v>.05:errors.append(phase[-1])
report={'scope':'Replacement parts against integrated actors in reference pose; V1 versus drum and selected cap at 15 degree increments. No dynamic feeding/suspension simulation. Existing V7 unchecked/reference interfaces remain pending.','static_pair_checks':len(results),'phase_checks':len(phase),'max_static_intersection_mm3':max(x['intersection_mm3'] for x in results),'max_phase_intersection_mm3':max(x['intersection_mm3'] for x in phase),'unexpected':errors}
(OUT/'clearance_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
assert not errors
assembly=cq.Assembly(name='V8_isolation_reference_only')
for i,a in enumerate(actors):
 if a['group'] in ('isolate','intake'):
  assembly.add(world(a),name=f"p{i}_{a['name']}",color=cq.Color(*a['color']))
assembly.export(str(OUT/'ISOLATION_ASSEMBLY_REFERENCE_ONLY.step'))
