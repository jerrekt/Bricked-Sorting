from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'isolate_v8'
src=(ROOT/'render_isolate_v7.py').read_text().split('full=scene(False)')[0]
src=src.replace("OUT=ROOT/'isolate_v7'","OUT=ROOT/'isolate_v8'").replace("isolate_and_machine_dimensions.json","refined_assembly_register.json")
ns={'__file__':str(ROOT/'render_isolate_v7.py')};exec(compile(src,'render_helpers','exec'),ns)
s=ns['s'];render=ns['render'];mesh=ns['mesh'];transform=ns['transform'];scene=[];detail=[]
for a in s['actors']:
 if a['group']=='intake' or (a['group']=='isolate' and not a['name'].startswith(('69_','70_','71_'))):
  item=(transform(mesh(a),a),np.array(a['color']));scene.append(item)
  if not a['name'].startswith('58_') and a['group']!='intake':detail.append(item)
render(scene,OUT/'three_stages.png',(1000,-1500,1400),(0,60,700),(1200,1100))
render(detail,OUT/'drum_v1_v2_detail.png',(950,-1500,1400),(0,60,680),(1200,1000))
f=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
im=Image.new('RGB',(2400,1440),'#f6f7f8');d=ImageDraw.Draw(im)
d.text((45,25),'BRICKED SORTING | REFINED PRINTED ISOLATION — V8',font=f(44),fill='#20313f')
d.text((45,95),'Loading funnel → rotating drum → V1 → V2     |     Existing stage positions retained',font=f(29),fill='#52636e')
im.paste(Image.open(OUT/'three_stages.png'),(0,160));im.paste(Image.open(OUT/'drum_v1_v2_detail.png'),(1200,180))
d.text((1240,1190),'Drum: swap 45 / 55 / 65 mm outlet caps',font=f(29),fill='#20313f')
d.text((1240,1235),'V1: rear catch wall; broad side inlet retained',font=f(29),fill='#20313f')
d.text((1240,1280),'V2: taller walls; original passage width retained',font=f(29),fill='#20313f')
d.text((45,1365),'CAD prototype • Singulation, suspension tuning and throughput require physical tests • 8/10 concept',font=f(28),fill='#865c25')
im.save(OUT/'refined_isolation_preview.png')
