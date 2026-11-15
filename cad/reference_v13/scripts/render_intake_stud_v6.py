"""Exact CAD preview: brick cover closed and upper8-bin tier pulled outside."""
from pathlib import Path
import json,struct
import cadquery as cq
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'intake_stud_v6'
spec=json.loads((OUT/'intake_and_access_dimensions.json').read_text())
src=(ROOT/'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
ns={'__file__':str(ROOT/'render_previews_v3.py')};exec(compile(src,'pure_renderer','exec'),ns)
render,cube,cylinder=ns['render'],ns['cube'],ns['cylinder'];cache={}
def mesh(a):
    key=a.get('stl_file',a.get('step_file'))
    if key in cache:return cache[key]
    if a.get('stl_file'):
        raw=(ROOT/key).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
        dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
        p=np.frombuffer(raw,dtype=dt,count=n,offset=84)['v'].astype(float)
    else:
        shape=cq.importers.importStep(str(ROOT/key)).val();vs,ts=shape.tessellate(.15,.12)
        p=np.array([v.toTuple()for v in vs])[np.array(ts)]
    cache[key]=p;return p
def transform(p,a,extension):
    p=p.copy()
    for axis,key in((0,'rx'),(1,'ry'),(2,'rz')):
        t=np.radians(a[key]);c,s=np.cos(t),np.sin(t)
        r=np.array([[1,0,0],[0,c,-s],[0,s,c]])if axis==0 else np.array([[c,0,s],[0,1,0],[-s,0,c]])if axis==1 else np.array([[c,-s,0],[s,c,0],[0,0,1]])
        p=p@r.T
    x,y,z=a['xyz'];return p+np.array([x,y+(extension if a.get('drawer_tier')==2 else 0),z])
def scene(ext):
    result=[]
    for a in spec['actors']+spec['reference_actors']:
        result.append((transform(mesh(a),a,ext),np.array(a['color'])))
    for ref in spec['reference_volumes']:
        if ref['kind']=='box':result.append(cube(ref['center'],ref['size'],ref['color']))
        else:
            x,y,z=ref['center'];result.append(cylinder(x,y,z,ref['diameter']/2,ref['height'],ref['color']))
    return result
render(scene(0),OUT/'intake_closed_cad.png',(1150,1750,1150),(0,0,350),(1550,1250))
print('Outside closed rendered',flush=True)
render(scene(350),OUT/'intake_drawer_open_cad.png',(1150,1750,1350),(0,150,320),(1800,1300))
print('Upper tier pulled outside rendered',flush=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(3200,1700),'#f6f7f8');d=ImageDraw.Draw(im)
d.text((80,45),'BRICKED SORTING · OPEN LOADING STUD',font=f(60),fill='#20313f')
d.text((80,130),'One stud: open loading funnel · Other stud: closed cap · Outside bin access retained',font=f(34),fill='#52636e')
im.paste(Image.open(OUT/'intake_closed_cad.png'),(0,245))
im.paste(Image.open(OUT/'intake_drawer_open_cad.png'),(1400,210))
d.text((90,225),'CLOSED — ONE STUD IS THE LOADING INLET',font=f(31),fill='#20313f')
d.text((1670,225),'UPPER TIER OPEN — ALL 8 BINS OUTSIDE',font=f(31),fill='#20313f')
d.text((90,1495),'Loading opening Ø260 mm · Provisional outlet Ø100 mm.',font=f(29),fill='#20313f')
d.text((90,1543),'Funnel and roof opened; drum connection remains to be fitted.',font=f(29),fill='#52636e')
d.text((1660,1495),'350 mm tray travel · Reserve at least 400 mm in front.',font=f(27),fill='#20313f')
d.text((1660,1543),'Drum transition and remaining frame mechanisms pending.',font=f(27),fill='#52636e')
d.text((90,1620),'LAYOUT PROTOTYPE · Drum interface and flow are unverified; prior drawer/frame hardware still needs engineering.',font=f(28),fill='#7b4d21')
im.save(OUT/'intake_full_picture.png')
print('Outside-access full picture saved',flush=True)
