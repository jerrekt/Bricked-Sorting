"""Housing-hidden view of the actual V6 CAD; no geometry or dimensions change."""
from pathlib import Path
import json,struct
import cadquery as cq
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'intake_stud_v6'
spec=json.loads((OUT/'intake_and_access_dimensions.json').read_text())
source=(ROOT/'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
ns={'__file__':str(ROOT/'render_previews_v3.py')};exec(compile(source,'pure_renderer','exec'),ns)
render,cube,cylinder=ns['render'],ns['cube'],ns['cylinder'];cache={}
def mesh(a):
    key=a.get('stl_file',a.get('step_file'))
    if key in cache:return cache[key]
    if a.get('stl_file'):
        raw=(ROOT/key).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
        dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
        p=np.frombuffer(raw,dtype=dt,count=n,offset=84)['v'].astype(float)
    else:
        vs,ts=cq.importers.importStep(str(ROOT/key)).val().tessellate(.15,.12)
        p=np.array([v.toTuple()for v in vs])[np.array(ts)]
    cache[key]=p;return p
def transform(p,a,extension):
    p=p.copy()
    for axis,key in((0,'rx'),(1,'ry'),(2,'rz')):
        t=np.radians(a[key]);c,s=np.cos(t),np.sin(t)
        r=np.array([[1,0,0],[0,c,-s],[0,s,c]])if axis==0 else np.array([[c,0,s],[0,1,0],[-s,0,c]])if axis==1 else np.array([[c,-s,0],[s,c,0],[0,0,1]])
        p=p@r.T
    x,y,z=a['xyz'];return p+np.array([x,y+(extension if a.get('drawer_tier')==2 else 0),z])
def scene(extension):
    result=[]
    for a in spec['actors']:
        if a['group']in('shell','access','intake'):continue
        color=[.18,.57,.72]if a['group']=='bins'and a.get('drawer_tier')==2 else a['color']
        result.append((transform(mesh(a),a,extension),np.array(color)))
    for a in spec['reference_actors']:
        if a['name']=='CENTRAL_FRONT_DIVIDER_FRAME_PENDING':continue
        color=[.3,.5,.62]if a.get('drawer_tier')==2 else a['color']
        result.append((transform(mesh(a),a,extension),np.array(color)))
    for a in spec['reference_volumes']:
        if 'RESERVED_NOT_BUILT'in a['name']:continue
        if a['kind']=='box':result.append(cube(a['center'],a['size'],a['color']))
        else:
            x,y,z=a['center'];result.append(cylinder(x,y,z,a['diameter']/2,a['height'],a['color']))
    return result
camera=(1100,-1450,1150);focal=(0,80,250);size=(1550,1150)
closed=scene(0);opened=scene(350)
render(closed,OUT/'no_walls_closed_cad.png',camera,focal,size)
print('Housing-hidden closed view rendered',flush=True)
render(opened,OUT/'no_walls_drawer_open_cad.png',camera,focal,size)
print('Housing-hidden withdrawal view rendered',flush=True)
def project(point,actors):
    toward=np.array(camera,float)-np.array(focal);toward/=np.linalg.norm(toward)
    right=np.cross([0,0,1],toward);right/=np.linalg.norm(right);up=np.cross(toward,right)
    v=np.concatenate([a[0].reshape(-1,3)for a in actors]);uv=v@np.array([right,up]).T
    lo,hi=uv.min(axis=0),uv.max(axis=0);mid=(lo+hi)/2
    scale=min(size[0]/(hi[0]-lo[0]),size[1]/(hi[1]-lo[1]))*.88
    p=(np.array(point)@np.array([right,up]).T-mid)*scale
    return(p[0]+size[0]/2,size[1]/2-p[1])
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(3200,1580),'#f6f7f8');d=ImageDraw.Draw(im)
d.text((75,35),'BRICKED SORTING · NO WALLS / ROOF',font=f(59),fill='#20313f')
d.text((75,118),'Same CAD layout · Rear three-quarter view exposes the elevator inside the semicircle',font=f(32),fill='#52636e')
im.paste(Image.open(OUT/'no_walls_closed_cad.png'),(30,240))
im.paste(Image.open(OUT/'no_walls_drawer_open_cad.png'),(1620,240))
d.text((85,205),'BOTH BIN TIERS IN SORTING POSITION',font=f(31),fill='#20313f')
d.text((1680,205),'UPPER TIER WITHDRAWN 350 mm',font=f(31),fill='#20313f')
for actors,offset in((closed,30),(opened,1620)):
    x,y=project((0,-160,486),actors);x+=offset;y+=240
    tx,ty=offset+65,315
    d.rounded_rectangle((tx-10,ty-8,tx+435,ty+42),radius=8,fill='#f6f7f8')
    d.text((tx,ty),'ELEVATOR TOWER STAYS FIXED',font=f(24),fill='#a86d22')
    d.line((tx+425,ty+22,x,y),fill='#a86d22',width=4)
    d.ellipse((x-6,y-6,x+6,y+6),fill='#a86d22')
d.text((85,1385),'Orange/steel: fixed tower + vertically moving carriage',font=f(27),fill='#a86d22')
d.text((85,1430),'Gray: lower 8 bins · Blue: upper 8 bins and moving tray',font=f(27),fill='#315e70')
d.text((1680,1385),'Only the blue tier moves outward; the elevator stays inside.',font=f(26),fill='#20313f')
d.text((1680,1430),'Housing, roof, studs, drawer fronts and feeder placeholders hidden.',font=f(24),fill='#52636e')
d.text((85,1510),'LAYOUT PROTOTYPE · Carrier/slides are reference geometry. Receiver, frame, latches and load validation remain pending.',font=f(28),fill='#7b4d21')
im.save(OUT/'no_walls_elevator_and_drawers.png')
(OUT/'NO_WALLS_VIEW.txt').write_text('NO-WALLS CAD VIEW\nView-only change; all geometry and dimensions unchanged.\nHousing,roof,studs,drawer fronts and V1/V2/scanner reservation blocks hidden for visibility.\nBoth views use the same rear three-quarter camera. Left: closed tiers. Right: upper tier+350Y.\nTower remains stationary; carriage moves vertically during sorting. Blue upper bins/tray move for access.\nCarrier and runner shapes remain reference hardware; receiver/frame/latches and load tests pending.\n')
print('No-walls full picture saved',flush=True)
