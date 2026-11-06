"""Three progressive actual-CAD views; shared camera, scale and world bounds."""
from pathlib import Path
import json, numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'isolate_v8'
src=(ROOT/'render_isolate_v7.py').read_text().split('full=scene(False)')[0]
src=src.replace("OUT=ROOT/'isolate_v7'","OUT=ROOT/'isolate_v8'").replace('isolate_and_machine_dimensions.json','refined_assembly_register.json')
ns={'__file__':str(ROOT/'render_isolate_v7.py')};exec(compile(src,'helpers','exec'),ns)
s=ns['s'];scenes=[[],[],[]]
for a in s['actors']:
 item=(ns['transform'](ns['mesh'](a),a),np.array(a['color']))
 scenes[0].append(item)
 if a['group'] not in ('shell','shell_extension','access'):scenes[1].append(item)
 if a['group'] not in ('shell','shell_extension','access','bins'):scenes[2].append(item)
for a in s['reference_actors']:
 if a['name']=='CENTRAL_FRONT_DIVIDER_FRAME_PENDING':continue
 item=(ns['transform'](ns['mesh'](a),a),np.array(a['color']))
 scenes[0].append(item);scenes[1].append(item)
 if a['group']=='purchased_reference':scenes[2].append(item)
for v in s['reference_volumes']:
 if v['kind']=='box':item=ns['cube'](v['center'],v['size'],v['color'])
 else:
  x,y,z=v['center'];item=ns['cylinder'](x,y,z,v['diameter']/2,v['height'],v['color'])
 scenes[0].append(item);scenes[1].append(item)
 name=v['name'].lower()
 if not any(t in name for t in ('chassis','cantilever','support_platform')):scenes[2].append(item)
# Renderer normally auto-fits; use identical world bounds in all views.
rns={'__file__':str(ROOT/'render_previews_v3.py')}
r=(ROOT/'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
r=r.replace('verts=np.concatenate([a[0].reshape(-1,3) for a in actors])','verts=FIT_VERTICES')
rns['FIT_VERTICES']=np.concatenate([a[0].reshape(-1,3)for a in scenes[0]])
exec(compile(r,'fixed_camera_renderer','exec'),rns)
render=rns['render'];font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=lambda n:ImageFont.truetype(font,n)
labels=[('1  COMPLETE SHELL','Two studs; one is the loading inlet.'),('2  WALLS & ROOF REMOVED','Bin tiers, stationary lift and upper feeders.'),('3  BINS & RACK HIDDEN','Drum, V1, V2, scanner and sorting scoop.')]
board=Image.new('RGB',(3300,1700),'#f6f7f8');d=ImageDraw.Draw(board)
d.text((65,30),'BRICKED SORTING | COMPLETE MACHINE → CORE MECHANISMS',font=f(49),fill='#20313f')
d.text((65,110),'V8 CAD • Same camera and scale • 1,000 × 500 mm footprint • 900 mm body / 1,016.5 mm to stud top',font=f(31),fill='#52636e')
for i,scene in enumerate(scenes):
 path=OUT/f'overall_{i+1:02d}.png'
 render(scene,path,(1500,2050,1550),(0,0,500),(1100,1220))
 im=Image.new('RGB',(1100,1450),'#f6f7f8');im.paste(Image.open(path),(0,120));di=ImageDraw.Draw(im)
 di.text((40,25),labels[i][0],font=f(34),fill='#20313f');di.text((40,80),labels[i][1],font=f(23),fill='#52636e')
 im.save(path);board.paste(im,(i*1100,200))
d.text((65,1590),'Prototype layout. Frame, runners, suspension, actuators and scoop-to-bin receivers still need detailing/testing.',font=f(31),fill='#865c25')
board.save(OUT/'overall_three_views.png')
print('Three matching views rendered',flush=True)
