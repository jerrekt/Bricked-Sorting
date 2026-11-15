"""Render actual STL layout with CPU depth buffer; no invented finished mechanisms."""
from pathlib import Path
import json,struct,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'brick_layout_v4'
spec=json.loads((OUT/'layout_dimensions_and_parts.json').read_text())
# Reuse only the renderer's pure function definitions, before its scene script.
source=(ROOT/'render_previews_v3.py').read_text().split("raw=OUT/'scoop_cad.png'")[0]
ns={'__file__':str(ROOT/'render_previews_v3.py')};exec(compile(source,'depth_buffer_renderer','exec'),ns)
render=ns['render'];cube=ns['cube'];cylinder=ns['cylinder']
cache={}
def mesh(name,source):
    key=(name,source)
    if key in cache:return cache[key]
    folder=ROOT if source=='baseline' else ROOT/'electronics_addon' if source=='electronics' else OUT
    raw=(folder/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
    dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
    pts=np.frombuffer(raw,dtype=dt,count=n,offset=84)['v'].astype(float)
    cache[key]=pts;return pts
def transform(pts,a):
    pts=pts.copy()
    for axis,key in ((0,'rx'),(1,'ry'),(2,'rz')):
        angle=np.radians(a[key]);c,s=np.cos(angle),np.sin(angle)
        if axis==0:r=np.array([[1,0,0],[0,c,-s],[0,s,c]])
        elif axis==1:r=np.array([[c,0,s],[0,1,0],[-s,0,c]])
        else:r=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        pts=pts@r.T
    return pts+np.array(a['xyz'])
def scene(mode):
    result=[]
    for a in spec['actors']:
        if mode=='open' and a['group']=='shell':
            # Keep rear and left cover only; remove top/front/right to expose layout.
            if not (a['name'].startswith('22') and a['xyz'][1]<0 or a['name'].startswith('23') and a['xyz'][0]<0):continue
        result.append((transform(mesh(a['name'],a['source']),a),np.array(a['color'])))
    if mode=='open':
        for ref in spec['reference_volumes']:
            c=ref['color']
            if ref['kind']=='box':result.append(cube(ref['center'],ref['size'],c))
            else:
                x,y,z=ref['center'];result.append(cylinder(x,y,z,ref['diameter']/2,ref['height'],c))
    return result
if not (OUT/'closed_cad.png').exists():
    render(scene('closed'),OUT/'closed_cad.png',(1250,1450,1000),(0,0,350),(1600,1200))
print('Closed CAD rendered',flush=True)
if not (OUT/'cutaway_cad.png').exists():
    render(scene('open'),OUT/'cutaway_cad.png',(1100,1450,1150),(0,0,290),(1800,1300))
print('Cutaway CAD rendered',flush=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(3200,1640),'#f6f7f8');d=ImageDraw.Draw(im)
d.text((85,40),'BRICKED SORTING · 2×1 BRICK LAYOUT',font=f(60),fill='#20313f')
d.text((85,125),'1,000 × 500 mm footprint · 600 mm body · 716.5 mm overall with studs',font=f(34),fill='#52636e')
im.paste(Image.open(OUT/'closed_cad.png'),(-10,250))
im.paste(Image.open(OUT/'cutaway_cad.png'),(1420,190))
d.text((90,220),'CLOSED BEAUTY COVER',font=f(36),fill='#20313f')
d.text((1670,220),'CUTAWAY — FRONT / RIGHT / TOP REMOVED',font=f(32),fill='#20313f')
d.text((90,1450),'Red: removable cover panels + two hollow studs',font=f(28),fill='#a62c25')
d.text((90,1498),'Dark base: modular tiles and M5 splice plates',font=f(28),fill='#384652')
d.text((1650,1450),'Gray: 2 × 8 provisional bins · Orange/teal: reused lift',font=f(27),fill='#384652')
d.text((1650,1498),'Purple: V1 / V2 / scanner reserved space; mechanisms pending',font=f(25),fill='#775589')
d.text((90,1570),'LAYOUT PROTOTYPE · Bin supports, receiving adapter, cover frame and feed/release mechanisms still need engineering.',font=f(29),fill='#7b4d21')
im.save(OUT/'full_machine_layout.png')

# Exact plan makes tier, flow path and service space easier to assess.
plan=Image.new('RGB',(1800,1230),'#f6f7f8');d=ImageDraw.Draw(plan);cx,cy,sc=820,610,1.35
def xy(x,y):return(cx+x*sc,cy-y*sc)
d.text((65,35),'BRICKED SORTING · PLAN / BASE LAYOUT',font=f(40),fill='#20313f')
d.text((65,100),'Proposed positions, mm · Both bin tiers share these eight yaw positions',font=f(25),fill='#52636e')
box=(*xy(-500,250),*xy(500,-250));d.rectangle(box,fill='#e3e8eb',outline='#a62c25',width=6)
for x in (-300,-100,100,300):d.line((*xy(x,250),*xy(x,-250)),fill='#b7c1c8',width=2)
for y in (-500/6,500/6):d.line((*xy(-500,y),*xy(500,y)),fill='#b7c1c8',width=2)
for slot in range(1,9):
    yaw=math.radians(78.75-(slot-1)*22.5);pts=[]
    for r,ts in ((305,np.linspace(-10.5,10.5,25)),(160,np.linspace(10.5,-10.5,25))):
        for t in ts:
            a=yaw+math.radians(float(t));pts.append(xy(-r*math.sin(a),-70+r*math.cos(a)))
    d.polygon(pts,fill='#b8c4cd',outline='#52636e',width=2)
    x,y=xy(-237*math.sin(yaw),-70+237*math.cos(yaw))
    d.text((x-8,y-15),str(slot),font=f(27),fill='#20313f')
# Original V3 base transformed to world.
d.rectangle((*xy(-105,-30),*xy(105,-240)),fill='#edc17e',outline='#ad772d',width=3)
x,y=xy(0,-70);d.ellipse((x-7,y-7,x+7,y+7),fill='#087f88')
d.arc((x-110*sc,y-110*sc,x+110*sc,y+110*sc),180,360,fill='#087f88',width=4)
d.rectangle((*xy(335,0),*xy(465,-200)),fill='#6d96a7',outline='#365c6b',width=3)
d.text((65,1050),'1–8: shared color slots, lower = regular bricks / upper = other parts',font=f(25),fill='#20313f')
d.text((65,1095),'Orange: existing lift base on 150 mm risers     Blue: PSU + step-down service panel',font=f(24),fill='#20313f')
d.text((65,1140),'Scoop floor lip r≈110 · Bin inner radius160 · The remaining receiver/extension is not designed.',font=f(24),fill='#7b4d21')
plan.save(OUT/'base_plan.png')
print('Full-machine and plan previews saved',flush=True)
