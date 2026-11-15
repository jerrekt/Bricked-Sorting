"""V7 actual-CAD overall and Isolate close-up; housing hidden for visibility."""
from pathlib import Path
import json,struct
import cadquery as cq
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'isolate_v7'
s=json.loads((OUT/'isolate_and_machine_dimensions.json').read_text())
src=(ROOT/'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
ns={'__file__':str(ROOT/'render_previews_v3.py')};exec(compile(src,'pure_renderer','exec'),ns)
render,cube,cylinder=ns['render'],ns['cube'],ns['cylinder'];cache={}
def mesh(a):
    key=a.get('stl_file',a.get('step_file'))
    if key in cache:return cache[key]
    if a.get('stl_file'):
        raw=(ROOT/key).read_bytes();n=struct.unpack_from('<I',raw,80)[0];dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
        p=np.frombuffer(raw,dtype=dt,count=n,offset=84)['v'].astype(float)
    else:
        vs,ts=cq.importers.importStep(str(ROOT/key)).val().tessellate(.18,.13);p=np.array([v.toTuple()for v in vs])[np.array(ts)]
    cache[key]=p;return p
def transform(p,a):
    if'rotation_matrix'in a:p=p@np.array(a['rotation_matrix']).T
    else:
        for axis,key in((0,'rx'),(1,'ry'),(2,'rz')):
            t=np.radians(a[key]);c,ss=np.cos(t),np.sin(t)
            R=np.array([[1,0,0],[0,c,-ss],[0,ss,c]])if axis==0 else np.array([[c,0,ss],[0,1,0],[-ss,0,c]])if axis==1 else np.array([[c,-ss,0],[ss,c,0],[0,0,1]])
            p=p@R.T
    return p+np.array(a['xyz'])
def scene(close=False):
    result=[]
    for a in s['actors']:
        if a['group']in('shell','shell_extension','access'):continue
        if close and a['group']in('base','bins','lift','electronics'):continue
        color=[.18,.57,.72]if a['group']=='bins'and a.get('drawer_tier')==2 else a['color']
        result.append((transform(mesh(a),a),np.array(color)))
    for a in s['reference_actors']:
        if a['name']=='CENTRAL_FRONT_DIVIDER_FRAME_PENDING':continue
        if close and a['group']!='purchased_reference':continue
        result.append((transform(mesh(a),a),np.array(a['color'])))
    for v in s['reference_volumes']:
        if close and(v['name']in('left_rod','right_rod','lead_screw','lift_motor','rotating_motor','PSU_reserved_not_retained','buck_reserved')or'CHASSIS'in v['name'].upper()or'platform'in v['name']or'stationary_chassis'in v['name']):continue
        if v['kind']=='box':result.append(cube(v['center'],v['size'],v['color']))
        else:
            x,y,z=v['center'];result.append(cylinder(x,y,z,v['diameter']/2,v['height'],v['color']))
    return result
full=scene(False);close=scene(True)
camera=(1300,-1650,1350);focal=(0,40,500);size=(1550,1450)
render(full,OUT/'full_no_walls_cad.png',camera,focal,size)
print('Integrated layout rendered',flush=True)
cam2=(1050,-1350,1200);foc2=(-20,65,745);size2=(1550,1450)
render(close,OUT/'isolate_closeup_cad.png',cam2,foc2,size2)
print('Isolate and scanner close-up rendered',flush=True)
def project(point,actors,cam,foc,sz):
    toward=np.array(cam,float)-np.array(foc);toward/=np.linalg.norm(toward)
    right=np.cross([0,0,1],toward);right/=np.linalg.norm(right);up=np.cross(toward,right)
    v=np.concatenate([a[0].reshape(-1,3)for a in actors]);uv=v@np.array([right,up]).T
    lo,hi=uv.min(axis=0),uv.max(axis=0);mid=(lo+hi)/2;scale=min(sz[0]/(hi[0]-lo[0]),sz[1]/(hi[1]-lo[1]))*.88
    p=(np.array(point)@np.array([right,up]).T-mid)*scale
    return(p[0]+sz[0]/2,sz[1]/2-p[1])
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(3200,1900),'#f6f7f8');d=ImageDraw.Draw(im)
d.text((75,35),'BRICKED SORTING · ISOLATE + SCANNER PROTOTYPE',font=f(53),fill='#20313f')
d.text((75,115),'Proposed hardware · Existing lift / drawers retained · Body 1,000 × 500 × 900 mm',font=f(33),fill='#52636e')
im.paste(Image.open(OUT/'full_no_walls_cad.png'),(25,230));im.paste(Image.open(OUT/'isolate_closeup_cad.png'),(1620,230))
d.text((85,205),'COMPLETE LAYOUT — HOUSING HIDDEN',font=f(30),fill='#20313f')
d.text((1680,205),'DRUM → V1 → V2 → INSPECTION / RELEASE',font=f(29),fill='#20313f')
def label(point,text,x,y,color='#20313f'):
    px,py=project(point,close,cam2,foc2,size2);px+=1620;py+=230
    width=d.textlength(text,font=f(24))
    d.rounded_rectangle((x-8,y-5,x+width+8,y+32),radius=5,fill='#f6f7f8')
    d.text((x,y),text,font=f(24),fill=color);d.line((x+width/2,y+34,px,py),fill=color,width=3);d.ellipse((px-4,py-4,px+4,py+4),fill=color)
label([-250,0,980],'1  LOADING STUD',1710,300,'#a63126')
label([-90,120,760],'2  160 × 180 DRUM',2630,605,'#315e78')
label([75,100,635],'3  V1',2610,1100,'#16764c')
label([35,-20,607],'4  V2',2480,1220,'#168078')
label([0,-70,559.5],'5  HOLD / SCAN / RELEASE',1745,1390,'#8b6525')
d.text((85,1680),'The added upper section provides a descending path above the stationary elevator.',font=f(27),fill='#20313f')
d.text((85,1730),'Red: inlet · Blue: tumbler · Green: V1 · Teal: V2 · Silver: scanner / camera gantry',font=f(26),fill='#52636e')
d.text((85,1780),'25 new STL types + STEP/source. Bearings, motors, actuators and chassis include proposed hardware envelopes.',font=f(26),fill='#52636e')
d.text((85,1840),'PROTOTYPE · Transport, singulation, actuator/suspension selection, full support frame and physical tests remain pending.',font=f(28),fill='#7b4d21')
im.save(OUT/'isolate_full_machine_picture.png')
print('Labeled integrated picture saved',flush=True)
