import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
P={'post':'#c9975b','rail':'#e6c58c','cleat':'#d9a441','bot':'#b9814a','beam':'#8fb86a','cross':'#7aa7d9','ply':'#f0e2c0'}
parts=[]  # name,kind,(x0,x1,y0,y1,z0,z1)
for sx in (1,-1):
    for sy in (1,-1):
        parts.append(('post',sorted((sx*316,sx*354))+sorted((sy*136,sy*174))+[12,612]))
for sy in (1,-1):
    parts.append(('rail',[-316,316]+sorted((sy*155,sy*174))+[574,612]))
    parts.append(('cleat',[-316,316]+sorted((sy*155,sy*174))+[262,300]))
for sx in (1,-1):
    parts.append(('rail',sorted((sx*335,sx*354))+[-136,136,574,612]))
    parts.append(('cleat',sorted((sx*335,sx*354))+[-136,136,262,300]))
    parts.append(('bot',sorted((sx*335,sx*354))+[-136,136,12,50]))
    parts.append(('beam',sorted((sx*335,sx*354))+[-19,19,50,262]))
parts.append(('cross',[-311,-273,-155,155,593,612])); parts.append(('cross',[-87,-49,-155,155,593,612]))
parts.append(('ply',[-360,360,-180,180,0,12]))
deck=('ply',[-354,354,-174,174,300,312])
inch=lambda mm: f'{mm/25.4:.2f}'
def frac(mm):
    v=round(mm/25.4*16); w,n=divmod(v,16)
    if n==0: return f'{w}"'
    from math import gcd
    g=gcd(n,16); return (f'{w} ' if w else '')+f'{n//g}/{16//g}"'
fig=plt.figure(figsize=(18,23),dpi=100)
fig.suptitle('Bricked Sorting V14: wood frame build plan (wood only)',fontsize=26,weight='bold',y=0.995)
# ---- 3D view
ax=fig.add_axes([0.02,0.60,0.60,0.35],projection='3d')
def box(b,c,a=1.0):
    x0,x1,y0,y1,z0,z1=b
    # mirror x so the funnel end (x<0) is on the right when seen from the front
    x0,x1=-x1,-x0
    v=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    f=[[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    ax.add_collection3d(Poly3DCollection([v[i] for i in f],facecolor=c,edgecolor='#4a3a22',linewidth=0.7,alpha=a))
for k,b in parts: box(b,P[k])
box(deck[1],P['ply'],0.45)
ax.set_xlim(-380,380); ax.set_ylim(-380,380); ax.set_zlim(0,640); ax.set_box_aspect((760,760,640)); ax.view_init(20,-62); ax.axis('off')
# y axis: front is +Y; with view azim -62 the -Y side faces the viewer, so flip y too
ax.invert_yaxis()
ax.set_title('1. The whole frame (deck shown see-through)',fontsize=18,weight='bold',loc='left')
ax.text(0,260,-30,'FRONT',fontsize=14,weight='bold',ha='center'); ax.text(180,-170,700,'funnel-stud end (cross rails H)',fontsize=12,ha='center'); ax.text(-330,-170,700,'capped-stud end',fontsize=12,ha='center')
# legend
lg=fig.add_axes([0.63,0.60,0.35,0.36]); lg.axis('off')
rows=[('post','A','Corner post','2x2',600,4),('rail','B','Long top rail','1x2',632,2),('cleat','C','Long deck cleat','1x2',632,2),('rail','D','Short top rail','1x2',272,2),('cleat','E','Short deck cleat','1x2',272,2),('bot','F','Short bottom rail','1x2',272,2),('beam','G','Beam post','1x2',212,2),('cross','H','Roof cross rail (laid flat)','1x2',310,2)]
lg.text(0,0.98,'Cut list',fontsize=18,weight='bold',va='top')
for i,(k,l,n,s,mm,q) in enumerate(rows):
    y=0.88-i*0.085
    lg.add_patch(Rectangle((0,y-0.02),0.05,0.05,fc=P[k],ec='k'))
    lg.text(0.07,y,f'{l}  {n}',fontsize=13,weight='bold',va='bottom'); lg.text(0.07,y-0.005,f'{q} x {s},  {frac(mm)}  ({mm} mm)',fontsize=13,va='top')
y=0.88-8*0.085
lg.add_patch(Rectangle((0,y-0.02),0.05,0.05,fc=P['ply'],ec='k'))
lg.text(0.07,y,'Floor  1/2" ply',fontsize=13,weight='bold',va='bottom'); lg.text(0.07,y-0.005,f'{frac(720)} x {frac(360)}  (720 x 360)',fontsize=13,va='top')
y-=0.085
lg.add_patch(Rectangle((0,y-0.02),0.05,0.05,fc=P['ply'],ec='k'))
lg.text(0.07,y,'Deck  1/2" ply',fontsize=13,weight='bold',va='bottom'); lg.text(0.07,y-0.005,f'{frac(708)} x {frac(348)}  (708 x 348)',fontsize=13,va='top')
lg.text(0,0.0,'Buy: 2 x 2x2x8ft, 3 x 1x2x8ft, 1 x 1/2" ply 2x4 ft\n2x2 = 1 1/2" square, 1x2 = 3/4" x 1 1/2": measure yours',fontsize=12,va='bottom')
lg.set_xlim(0,1); lg.set_ylim(0,1)
# ---- front elevation (screen x = -X)
a=fig.add_axes([0.05,0.33,0.56,0.24])
def r(x0,x1,z0,z1,k,al=1): a.add_patch(Rectangle((-x1,z0),x1-x0,z1-z0,fc=P[k],ec='#4a3a22',lw=1,alpha=al))
r(-360,360,0,12,'ply'); r(-354,354,300,312,'ply')
for sx in (1,-1):
    r(*sorted((sx*316,sx*354)),12,612,'post')
r(-316,316,574,612,'rail'); r(-316,316,262,300,'cleat')
r(-311,-273,593,612,'cross'); r(-87,-49,593,612,'cross')
for x,l in ((335,'A'),(-335,'A')): a.text(-x,440,l,ha='center',fontsize=15,weight='bold')
a.text(-120,593,'B  long top rail',ha='center',va='center',fontsize=13,weight='bold'); a.text(0,281,'C  long deck cleat',ha='center',va='center',fontsize=13,weight='bold')
a.text(0,318,'deck ply sits on the cleats',ha='center',va='bottom',fontsize=12); a.text(0,18,'floor ply',ha='center',va='bottom',fontsize=12)
a.text(292,548,'H',ha='center',fontsize=13,weight='bold',color='#1f4e8c'); a.text(68,548,'H',ha='center',fontsize=13,weight='bold',color='#1f4e8c')
def dim(x,z0,z1,t,side=1):
    a.annotate('',xy=(x,z0),xytext=(x,z1),arrowprops=dict(arrowstyle='<->',lw=1.3)); a.text(x+side*8,(z0+z1)/2,t,fontsize=12,va='center',ha='left' if side>0 else 'right')
dim(385,12,612,f'post\n{frac(600)}')
dim(-385,0,262,f'cleat bottom\n{frac(262)} from\nthe floor bottom',-1)
dim(-385,300,574,f'{frac(274)} open\nabove the deck',-1)
dim(500,0,612,f'rail tops\n{frac(612)}\nfrom the\nfloor bottom')
a.annotate('',xy=(-316,640),xytext=(316,640),arrowprops=dict(arrowstyle='<->',lw=1.3)); a.text(0,650,f'{frac(632)} between posts (rails B, C)',ha='center',va='bottom',fontsize=12)
a.annotate('',xy=(-360,-22),xytext=(360,-22),arrowprops=dict(arrowstyle='<->',lw=1.3)); a.text(0,-28,f'floor {frac(720)}; posts sit {frac(6)} (6 mm) in from every floor edge',ha='center',va='top',fontsize=12)
a.set_xlim(-560,640); a.set_ylim(-70,670); a.set_aspect('equal'); a.axis('off')
a.set_title('2. Front view (funnel-stud end on your right)',fontsize=18,weight='bold',loc='left',pad=22)
# ---- end elevation (looking at a short end; screen x = Y)
e=fig.add_axes([0.66,0.33,0.32,0.24])
def re(y0,y1,z0,z1,k): e.add_patch(Rectangle((y0,z0),y1-y0,z1-z0,fc=P[k],ec='#4a3a22',lw=1))
re(-180,180,0,12,'ply'); re(-174,174,300,312,'ply')
for sy in (1,-1): re(*sorted((sy*136,sy*174)),12,612,'post')
re(-136,136,574,612,'rail'); re(-136,136,262,300,'cleat'); re(-136,136,12,50,'bot'); re(-19,19,50,262,'beam')
e.text(0,593,'D',ha='center',va='center',fontsize=13,weight='bold'); e.text(0,281,'E',ha='center',va='center',fontsize=13,weight='bold'); e.text(0,31,'F',ha='center',va='center',fontsize=13,weight='bold'); e.text(0,150,'G',ha='center',va='center',fontsize=13,weight='bold')
e.annotate('beam post G: centered,\nwide face toward you,\nbetween F and E',xy=(19,170),xytext=(55,120),fontsize=11,arrowprops=dict(arrowstyle='->'))
e.annotate('',xy=(-136,640),xytext=(136,640),arrowprops=dict(arrowstyle='<->',lw=1.3)); e.text(0,650,f'{frac(272)} between posts (D, E, F)',ha='center',va='bottom',fontsize=12)
e.annotate('',xy=(-180,-22),xytext=(180,-22),arrowprops=dict(arrowstyle='<->',lw=1.3)); e.text(0,-28,f'floor {frac(360)}',ha='center',va='top',fontsize=12)
e.set_xlim(-230,260); e.set_ylim(-70,670); e.set_aspect('equal'); e.axis('off')
e.set_title('3. End view (both ends the same)',fontsize=18,weight='bold',loc='left',pad=22)
# ---- top view of rails (screen x = -X, front at bottom => screen y = -Y via inverted axis with +Y down)
t=fig.add_axes([0.04,0.045,0.46,0.25])
def rt(x0,x1,y0,y1,k,al=1): t.add_patch(Rectangle((-x1,y0),x1-x0,y1-y0,fc=P[k],ec='#4a3a22',lw=1,alpha=al))
for sx in (1,-1):
    for sy in (1,-1): rt(*sorted((sx*316,sx*354)),*sorted((sy*136,sy*174)),'post')
    rt(*sorted((sx*335,sx*354)),-136,136,'rail')
for sy in (1,-1): rt(-316,316,*sorted((sy*155,sy*174)),'rail')
rt(-311,-273,-155,155,'cross'); rt(-87,-49,-155,155,'cross')
t.text(292,0,'H',ha='center',va='center',fontsize=14,weight='bold'); t.text(68,0,'H',ha='center',va='center',fontsize=14,weight='bold')
t.text(0,164.5,'B',ha='center',va='center',fontsize=12,weight='bold'); t.text(0,-164.5,'B',ha='center',va='center',fontsize=12,weight='bold')
t.text(180,70,f'outer H: {frac(5)} (5 mm)\ngap to the post',ha='center',fontsize=11)
t.annotate('',xy=(273,-100),xytext=(87,-100),arrowprops=dict(arrowstyle='<->',lw=1.3)); t.text(180,-106,f'{frac(186)} gap',ha='center',va='bottom',fontsize=12)
t.text(-150,0,'Long and short rails:\nouter faces flush with\nthe posts\' outer faces',ha='center',va='center',fontsize=12)
t.text(0,205,'FRONT',ha='center',fontsize=13,weight='bold'); t.text(0,-195,'BACK',ha='center',fontsize=13,weight='bold')
t.set_xlim(-400,400); t.set_ylim(225,-215); t.set_aspect('equal'); t.axis('off')
t.set_title('4. Top rails from above (cross rails H lie flat, flush with the rail tops)',fontsize=16,weight='bold',loc='left')
# ---- deck ply
d=fig.add_axes([0.54,0.045,0.44,0.25])
d.add_patch(Rectangle((-354,-174),708,348,fc=P['ply'],ec='#4a3a22',lw=1.5))
for sx in (1,-1):
    for sy in (1,-1): d.add_patch(Rectangle((min(sx*316,sx*354),min(sy*136,sy*174)),38,38,fc='white',ec='#4a3a22',lw=1.5))
d.add_patch(Circle((-240,0),28,fc='white',ec='#4a3a22',lw=1.5))
d.annotate(f'hole {frac(56)} (56 mm)\nuse a 2 1/4" hole saw',xy=(-212,0),xytext=(-150,-50),fontsize=12,arrowprops=dict(arrowstyle='->'))
d.annotate('',xy=(-354,60),xytext=(-240,60),arrowprops=dict(arrowstyle='<->',lw=1.3)); d.text(-297,56,f'{frac(114)}',ha='center',va='bottom',fontsize=12)
d.plot([-240,-240],[28,75],color='k',lw=0.8,ls=':')
d.text(-240,100,'centered front-to-back',ha='center',fontsize=11)
d.annotate(f'notch {frac(38)} square\nat all 4 corners',xy=(325,-150),xytext=(100,-90),fontsize=12,arrowprops=dict(arrowstyle='->'))
d.annotate('',xy=(-354,-200),xytext=(354,-200),arrowprops=dict(arrowstyle='<->',lw=1.3)); d.text(0,-206,f'{frac(708)}',ha='center',va='bottom',fontsize=12)
d.annotate('',xy=(380,-174),xytext=(380,174),arrowprops=dict(arrowstyle='<->',lw=1.3)); d.text(388,0,f'{frac(348)}',va='center',fontsize=12)
d.text(-200,150,'capped-stud end',ha='center',fontsize=12); d.text(240,150,'funnel-stud end',ha='center',fontsize=12)
d.text(0,200,'FRONT',ha='center',fontsize=13,weight='bold')
d.set_xlim(-400,460); d.set_ylim(225,-230); d.set_aspect('equal'); d.axis('off')
d.set_title('5. Deck ply from above (hole is at the capped-stud end)',fontsize=16,weight='bold',loc='left')
fig.text(0.04,0.008,'Screws:  #8 x 2 1/2" through the posts into the rail and cleat ends, 2 per end (3 mm pilot)   |   #6 x 1 1/4" up through the floor into each post, 4 per post (2.5 mm pilot)\n#6 x 1 1/4" down through the deck into the cleats, 3 per cleat   |   H: #8 x 2 1/2" toe-screwed into the long rails, 2 per end   |   G: one #8 x 2 1/2" up through F and one down through E',fontsize=12.5)
plt.savefig(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'wood_build_plan.png'),facecolor='white')
