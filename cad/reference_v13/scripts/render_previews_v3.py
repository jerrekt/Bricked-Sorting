"""Optional CPU depth-buffered CAD preview renderer. Requires NumPy and Pillow."""
from pathlib import Path
import numpy as np
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'lego_carriage_v3_heatset'
if not OUT.exists(): OUT=ROOT
BG=(246/255,247/255,248/255)
TEAL=(.08,.58,.62); ORANGE=(.89,.55,.17); GRAY=(.5,.56,.61); STEEL=(.67,.71,.75); MOTOR=(.16,.19,.23)

def actor_data(data,color,xyz=(0,0,0),rx=0):
    angle=np.radians(rx);c,s=np.cos(angle),np.sin(angle)
    rotation=np.array([[1,0,0],[0,c,-s],[0,s,c]])
    return np.asarray(data,dtype=float)@rotation.T+np.array(xyz),np.array(color)

def stl(name,color,xyz=(0,0,0),rx=0):
    raw=(OUT/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
    dtype=np.dtype([('normal','<f4',(3,)),('points','<f4',(3,3)),('attribute','<u2')])
    return actor_data(np.frombuffer(raw,dtype=dtype,count=n,offset=84)['points'],color,xyz,rx)

def cube(center,size,color):
    v=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)*np.array(size)/2+np.array(center)
    faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    return actor_data(v[faces],color)

def cylinder(x,y,z,r,h,color):
    faces=[]
    for i in range(64):
        a,b=i*2*np.pi/64,(i+1)*2*np.pi/64
        p=np.array([r*np.cos(a),r*np.sin(a),-h/2]);q=np.array([r*np.cos(b),r*np.sin(b),-h/2])
        pu=p+[0,0,h];qu=q+[0,0,h]
        faces += [[p,q,qu],[p,qu,pu],[[0,0,-h/2],q,p],[[0,0,h/2],pu,qu]]
    return actor_data(faces,color,(x,y,z))

def render(actors,path,position,focal,size):
    toward=np.array(position,dtype=float)-np.array(focal);toward/=np.linalg.norm(toward)
    right=np.cross([0,0,1],toward);right/=np.linalg.norm(right);up=np.cross(toward,right)
    verts=np.concatenate([a[0].reshape(-1,3) for a in actors]);uv=verts@np.array([right,up]).T
    low,high=uv.min(axis=0),uv.max(axis=0);mid=(low+high)/2
    width,height=size;scale=min(width/(high[0]-low[0]),height/(high[1]-low[1]))*.88
    image=np.empty((height,width,3),dtype=np.uint8);image[:]=np.round(np.array(BG)*255)
    depth=np.full((height,width),-np.inf);light=np.array([-.35,.45,.82]);light/=np.linalg.norm(light)
    for triangles,color in actors:
        for tri in triangles:
            xy=(tri@np.array([right,up]).T-mid)*scale;xy[:,0]+=width/2;xy[:,1]=height/2-xy[:,1]
            z=tri@toward
            lo=np.maximum(np.floor(xy.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(xy.max(axis=0)).astype(int),[width-1,height-1])
            if np.any(hi<lo):continue
            (x0,y0),(x1,y1),(x2,y2)=xy
            den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(den)<1e-7:continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
            a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
            b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;c=1-a-b
            dz=a*z[0]+b*z[1]+c*z[2];area=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            mask=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(dz>area)
            if not np.any(mask):continue
            normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=max(np.linalg.norm(normal),1e-12)
            shade=.58+.42*max(0,float(normal@light))
            pixels=image[lo[1]:hi[1]+1,lo[0]:hi[0]+1];pixels[mask]=np.clip(color*shade*255,0,255).astype(np.uint8);area[mask]=dz[mask]
    Image.fromarray(image).save(path)
    with Image.open(path) as im:im.load()

font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
raw=OUT/'scoop_cad.png'
render([stl('05_open_scoop_PRINT_FLAT',TEAL,(0,0,32),-40),stl('06_angled_shaft_hub',ORANGE),
        cube((0,0,-32),(42,42,48),MOTOR),cylinder(0,0,4,2.5,24,STEEL)],raw,(300,400,280),(0,35,10),(1120,900))
im=Image.new('RGB',(1800,1200),(246,247,248));im.paste(Image.open(raw),(10,180));d=ImageDraw.Draw(im)
d.text((80,45),'OPEN SCOOP · V3 HEAT-SET',font=f(48),fill='#202b38')
d.text((80,115),'Your M2 / M3 / M4 / M5 inserts · 40° open ramp',font=f(26),fill='#4e5d6c')
d.text((1200,225),'P2S · 256 × 256 mm',font=f(26),fill='#202b38')
x0,y0,scale=1190,330,2
d.rectangle((x0,y0,x0+512,y0+512),fill='#e5e9ed',outline='#647383',width=2)
cx,cy=x0+256,y0+256
d.rectangle((cx-132,cy-231.79,cx+132,cy+231.79),fill='#b9dfde')
d.rectangle((cx-122,cy-221.79,cx+122,cy+221.79),fill='#20a3aa')
d.text((1190,915),'122.0 × 221.8 × 48.2 mm',font=f(25),fill='#202b38')
d.text((1190,965),'5 mm brim around footprint',font=f(23),fill='#4e5d6c')
d.text((80,1125),'Print the scoop flat; bolt it onto the angled hub after printing.',font=f(25),fill='#4e5d6c')
im.save(OUT/'open_scoop_preview.png')

actors=[stl('01_ground_base',GRAY),stl('03_top_rod_brace',GRAY,(0,0,342)),
        stl('04_lower_switch_mount',GRAY,(0,0,8)),stl('07_upper_switch_rod_mount',GRAY,(0,0,241)),
        stl('10_M2_switch_backer_PRINT_TWICE',ORANGE,(0,-30,83),-90),
        stl('10_M2_switch_backer_PRINT_TWICE',ORANGE,(0,-30,258),-90),
        stl('02_moving_carriage_v3',ORANGE,(0,0,110)),stl('06_angled_shaft_hub',ORANGE,(0,90,158)),
        stl('05_open_scoop_PRINT_FLAT',TEAL,(0,90,190),-40),cube((0,0,34.35),(42.3,42.3,47.3),MOTOR),
        cube((0,90,126),(42,42,48),MOTOR),cylinder(-45,0,185,6,350,STEEL),cylinder(45,0,185,6,350,STEEL),
        cylinder(0,0,215,4,310,STEEL)]
actors=[(tri+np.array([0,0,10]),color) for tri,color in actors]
for x in [-85,85]:
    for y in [-60,110]: actors.append(stl('15_optional_foot_PRINT_FOUR',MOTOR,(x,y,10),180))
render(actors,OUT/'assembly_cad.png',(480,620,370),(0,50,175),(1300,1370))
im=Image.new('RGB',(1400,1600),(246,247,248));im.paste(Image.open(OUT/'assembly_cad.png'),(50,190));d=ImageDraw.Draw(im)
d.text((70,42),'BRICKED SORTING · HEAT-SET LIFT',font=f(39),fill='#202b38')
d.text((70,110),'M2 switch backing bars / M4 rod bosses / optional M5 feet',font=f(25),fill='#4e5d6c')
im.save(OUT/'assembly_preview.png')
print('Depth-buffered previews rendered and decoded successfully.')
