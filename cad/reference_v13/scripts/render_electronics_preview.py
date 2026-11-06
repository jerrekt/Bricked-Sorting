"""Dimensioned orthographic layout drawing; image is not a fit-test result."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'electronics_addon'
im=Image.new('RGB',(1920,1240),'#f6f7f8');d=ImageDraw.Draw(im)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
def text(x,y,value,n=24,color='#20313f'):
    d.text((x,y),value,font=f(n),fill=color)
scale=6;cx=710;cy=650
def xy(x,y):return(cx+x*scale,cy-y*scale)
def rect(x,y,w,h,fill,outline='#4b6573',width=3):
    x0,y0=xy(x-w/2,y+h/2);x1,y1=xy(x+w/2,y-h/2)
    d.rectangle((x0,y0,x1,y1),fill=fill,outline=outline,width=width)
def circle(x,y,r,fill,outline='#4b6573'):
    a,b=xy(x,y);d.ellipse((a-r*scale,b-r*scale,a+r*scale,b+r*scale),fill=fill,outline=outline,width=2)
def line(a,b,color='#4b6573',width=2):d.line((*xy(*a),*xy(*b)),fill=color,width=width)
def dimension(a,b,label,labelxy):
    line(a,b)
    for x,y in (a,b):
        line((x,y-2),(x,y+2))
    text(*xy(*labelxy),label,22)
text(70,40,'BRICKED SORTING · ADDITIVE POWER PANEL',42)
text(70,108,'Top view · dimensions in mm · original lift geometry unchanged',25,'#4b6573')
rect(0,0,200,130,'#d8e7ec',width=4)
for x in (-88,88):
    for y in (-53,53):circle(x,y,8,'#c4d7dd');circle(x,y,3.2,'#fff7c6')
for x in (-55,55):
    for y in (-48,-2):
        a,b=xy(x-17,y+2.2);c,e=xy(x+17,y-2.2)
        d.rounded_rectangle((a,b,c,e),radius=2.2*scale,fill='#f6f7f8',outline='#4b6573',width=2)
rect(0,-25,141.986,27.94,'#e4e5e6','#7f858b',3)
text(*xy(-67,-16),'PSU RESERVED ENVELOPE',23,'#565e66')
text(*xy(-67,-24),'142.0 L × 27.94 W × 39.88 H',21,'#565e66')
text(*xy(-67,-32),'Actual mounting brackets pending',19,'#565e66')
rect(0,33,51,25,'#f3d9ad','#a16c22')
for x in (-20,20):circle(x,33,5,'#e0b367');circle(x,33,2,'#fff7c6')
rect(0,33,34,25,'#e9a442','#a16c22')
text(*xy(-14,39),'DROK',23,'#44321c')
text(*xy(-14,33),'12 V → 5 V',17,'#44321c')
dimension((-20,52),(20,52),'40 mount centers',(-18,59))
dimension((-100,74),(100,74),'200',(-5,82))
text(70,1090,'Panel: 200 × 130 × 13 · flat base 5 · insert-entry faces upward',24)
text(70,1135,'M3: converter mounts (2)     M5: future frame attachment (4)',24)
text(70,1180,'PSU service/terminal space extends beyond this body outline and is still to be measured.',22,'#7b4d21')
text(1390,245,'PRINTABLE ADDITION',27)
text(1390,295,'16_electronics_layout_panel',20)
text(1390,350,'STEP + STL + source included',21)
text(1390,430,'CONVERTER',27)
text(1390,475,'51 × 25 × 21 overall',23)
text(1390,515,'Body length 34',23)
text(1390,555,'2 × M3 inserts + washers',23)
text(1390,595,'Check mounting-ear thickness',20)
text(1390,690,'PSU — NOT YET RETAINED',24,'#7b4d21')
for i,t in enumerate(['Label: 12 V / 10 A / 120 W','Photo: 5.59 × 1.1 × 1.57 in','Hole spacing not supplied','Separate adapters still needed','Panel is not an enclosure']):
    text(1390,735+42*i,t,21,'#565e66')
im.save(OUT/'electronics_layout_preview.png')
print(OUT/'electronics_layout_preview.png')
