"""V9 packaging study only; no STLs released. Baseline geometry unchanged."""
from pathlib import Path
import math,json,numpy as np,cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Ellipse,FancyArrowPatch
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'compact_v9'
R=np.array([[math.cos(math.radians(8)),0,math.sin(math.radians(8))],[0,1,0],[-math.sin(math.radians(8)),0,math.cos(math.radians(8))]])
rear=np.array([-100.,70.,810.]);front=rear+R@np.array([180,0,0])
paths={'V1':[[105,70,650],[-80,70,635]],'V2':[[-100,70,605],[-65,-70,595]]}
scanner=[0,-70,570];lens=[0,-70,698]
# Actual solid used only for drum envelope and sightline clearance.
drum=cq.importers.importStep(str(ROOT/'isolate_v7/47_tumbler_barrel_160x180.step')).val()
t=math.radians(98);RB=np.array([[math.cos(t),0,math.sin(t)],[0,1,0],[-math.sin(t),0,math.cos(t)]])
drum=drum.located(cq.Location(cq.Plane(origin=tuple(rear),xDir=tuple(RB[:,0]),normal=tuple(RB[:,2]))))
b=drum.BoundingBox();drum_env=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
# Proposed simple trough shells; motors,shelves,suspension and transfers not modeled.
def wire(points):return cq.Wire.makePolygon([cq.Vector(*p)for p in points]+[cq.Vector(*points[0])])
def trough(a,b):
 a,b=np.array(a,float),np.array(b,float);f=(b-a)/np.linalg.norm(b-a);h=math.hypot(f[0],f[1]);ac=np.array([f[1]/h,-f[0]/h,0]);up=np.cross(ac,f)
 profile=[(-35,27),(-8,0),(8,0),(35,27),(32,30),(5,3),(-5,3),(-32,30)]
 w=wire([a+ac*x+up*(z-3)for x,z in profile]);return cq.Solid.extrudeLinear(w,[],cq.Vector(*(b-a)))
trays={k:trough(*p)for k,p in paths.items()}
# 70-square image area tapering to 8-square pupil at128mm nominal distance.
w0=wire([[-35,-105,570],[35,-105,570],[35,-35,570],[-35,-35,570]])
w1=wire([[-4,-74,698],[4,-74,698],[4,-66,698],[-4,-66,698]])
view=cq.Solid.makeLoft([w0,w1],ruled=True)
view_hits={k:p.intersect(view).Volume()for k,p in {'drum':drum,**trays}.items()}
assert max(view_hits.values())<.05,view_hits
# Trapdoors35mm per half atz570,thickness3: conservative sweep lowestZ532.
# Actual scoop pose: original rotated -40 aboutX with zbase171+H+80.
scoop=cq.importers.importStep(str(ROOT/'05_open_scoop_PRINT_FLAT.step')).val().rotate((0,0,0),(1,0,0),-40)
clearances={}
for H in (55,170,185,200):
 p=scoop.translate((0,-70,171+H+80));top=p.BoundingBox().zmax
 clearances[str(H)]={'scoop_top_z':top,'conservative_open_door_bottom_z':532,'vertical_separation_mm':532-top,'release_allowed_in_this_study':H<=185}
assert clearances['185']['vertical_separation_mm']>8
slopes={k:math.degrees(math.atan2(a[2]-b[2],math.hypot(b[0]-a[0],b[1]-a[1])))for k,(a,b) in paths.items()}
register={'status':'PACKAGING STUDY ONLY;not printable release','units':'mm','date':'2026-10-29','baseline_body':[1000,500,900],'candidate_body':[800,500,900],'footprint_reduction_percent':20,'loading_stud_center_xy':[-200,0],'loading_stud_top_z':1016.5,'drum_rear_axis':rear.tolist(),'drum_front_axis':front.tolist(),'drum_actual_bounding_xyz_minmax':drum_env,'drum_fits_body_bounds':b.xmin>-400 and b.xmax<400 and b.ymin>-250 and b.ymax<250 and b.zmax<900,'floor_paths':paths,'floor_slopes_deg':slopes,'scanner_floor_center':scanner,'camera_pupil_center':lens,'view_cone_mm':{'floor_square':70,'pupil_square':8,'height':128},'view_cone_intersections_mm3':view_hits,'trapdoor_half_width':35,'trapdoor_thickness':3,'scoop_vertical_clearance_by_H':clearances,'old_200_release_pose_excluded':True,'check_scope':'Drum envelope,simple trough shells vs optical cone,and conservative Z-separation between actual baseline scoop and doors. No motors,springs,frame,bin mouths,wiring or continuous motion clearance checked.','next_CAD':'Straight funnel,flared transfers,trapdoor/linkage,compact scoop,integral-mouth bins and printed structural joints not released.'}
assert register['drum_fits_body_bounds']
(OUT/'packaging_register.json').write_text(json.dumps(register,indent=2)+'\n')
# Export fit-reference solids as a single STEP; no manufacture claims.
asm=cq.Assembly(name='V9_PACKAGING_STUDY_NOT_PRINT_RELEASE');asm.add(drum,name='repositioned_existing_drum')
for k,v in trays.items():asm.add(v,name=k+'_PATH_SHELL_ONLY')
asm.add(view,name='CAMERA_VIEW_CONE_REFERENCE');asm.export(str(OUT/'PACKAGING_REFERENCE_ONLY.step'))
# Dimensioned planning views distinguish built geometry,paths,and reserved areas.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,axs=plt.subplots(1,2,figsize=(17,9),gridspec_kw={'width_ratios':[1,1.1]});fig.patch.set_facecolor('#f6f7f8')
ax=axs[0];ax.set_facecolor('#f6f7f8');ax.set_title('TOP PLAN — candidate 800 × 500 mm',loc='left',fontweight='bold',pad=20)
ax.add_patch(Rectangle((-500,-250),1000,500,fill=False,ls='--',lw=1.5,ec='#a7b0b7'))
ax.add_patch(Rectangle((-400,-250),800,500,fill=False,lw=2,ec='#20313f'))
# Reserve space; not a routed or capacity-validated bin layout.
for xy,w,h in [((-375,-130),150,355),((225,-130),150,355),((-215,115),430,110)]:
 ax.add_patch(Rectangle(xy,w,h,fc='#cbdce8',ec='#6d91aa',hatch='//',alpha=.6))
ax.text(0,175,'SPACE RESERVED FOR BINS\n8 per tier / 16 total',ha='center',va='center',fontsize=10,color='#315d78')
ax.add_patch(Rectangle((-105,-240),210,210,fc='#f1cc82',ec='#b88328',alpha=.5));ax.text(0,-195,'Lift base\n(existing fit reference)',ha='center',fontsize=9)
ax.add_patch(Rectangle((drum_env[0],-10),drum_env[1]-drum_env[0],160,fc='#407a9f',ec='#254b66',alpha=.85));ax.text(-10,95,'DRUM →',ha='center',color='white',fontweight='bold')
ax.add_patch(Ellipse((-200,0),260,260,fill=False,ec='#bb4335',ls='--',lw=1.5));ax.text(-265,-135,'Loading stud',color='#a43d30',fontsize=9)
colors={'V1':'#159868','V2':'#009da5'}
for k,(a,b)in paths.items():
 ax.add_patch(FancyArrowPatch(a[:2],b[:2],arrowstyle='-|>',mutation_scale=18,lw=4,color=colors[k]));mid=(np.array(a)+b)/2;ax.text(mid[0]-12,mid[1]+12,k,color=colors[k],fontweight='bold')
ax.add_patch(Rectangle((-35,-105),70,70,fc='#e5a246',ec='#8d662e'));ax.text(0,-70,'SCAN',ha='center',va='center',fontsize=8)
ax.annotate('Short guided landing\nneeds detailed CAD',xy=(-35,-70),xytext=(95,-110),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.text(0,285,'Dashed gray: previous 1,000 mm width',ha='center',fontsize=9,color='#737e87')
ax.set(xlim=(-530,530),ylim=(-290,320),xlabel='X (mm)',ylabel='Y (mm)');ax.set_aspect('equal');ax.grid(alpha=.12)
ax=axs[1];ax.set_facecolor('#f6f7f8');ax.set_title('SIDE PACKAGING — depth folded onto X–Z view',loc='left',fontweight='bold',pad=20)
ax.add_patch(Rectangle((-400,0),800,900,fill=False,ec='#20313f',lw=2))
ax.add_patch(Rectangle((-350,904),300,112.5,fill=False,ec='#b94335'));ax.text(-200,965,'OPEN STUD',ha='center',color='#a43d30',fontsize=9)
ax.add_patch(Rectangle((drum_env[0],drum_env[4]),drum_env[1]-drum_env[0],drum_env[5]-drum_env[4],fc='#407a9f',ec='#254b66',alpha=.75));ax.text(-10,810,'DRUM →',ha='center',color='white',fontweight='bold')
ax.add_patch(FancyArrowPatch((-200,1016.5),(-80,807),arrowstyle='-|>',mutation_scale=18,lw=3,color='#b94335'));ax.text(-325,840,'One angled inlet\nroof opening + entry\nclearance pending',fontsize=9,color='#a43d30')
for k,(a,b)in paths.items():
 ax.plot([a[0],b[0]],[a[2],b[2]],lw=5,color=colors[k]);ax.annotate(k,xy=((a[0]+b[0])/2,(a[2]+b[2])/2),xytext=(180,665 if k=='V1' else 610),arrowprops={'arrowstyle':'->','color':colors[k]},fontweight='bold',color=colors[k])
ax.plot([-35,35],[570,570],color='#d68e2d',lw=4);ax.plot([0,0],[570,698],ls=':',color='#6e7482');ax.scatter([0],[698],marker='s',s=70,c='#424955');ax.text(55,707,'Camera + two diffused lights',fontsize=9);ax.text(55,683,'Camera sits forward of drum in Y',fontsize=8,color='#737e87')
ax.plot([-35,0,35],[570,535,570],color='#d68e2d',ls='--',lw=2);ax.text(80,540,'Two downward doors\nservo/linkage pending',fontsize=9)
ax.add_patch(Rectangle((-60,181),120,342,fc='#f3dca7',ec='#b88328',alpha=.7));ax.text(0,380,'LIFT /\nSCOOP',ha='center',color='#94651c')
ax.add_patch(Rectangle((-370,30),740,325,fc='#cbdce8',ec='#6d91aa',hatch='//',alpha=.35));ax.text(-335,245,'LARGER BIN ZONES\nfinal receiving slopes,capacity\nand drawer paths pending',fontsize=9,color='#315d78')
ax.text(0,65,'Lift support and wiring geometry retained as fit references',ha='center',fontsize=8)
ax.set(xlim=(-430,430),ylim=(0,1050),xlabel='X (mm)',ylabel='Z (mm)');ax.grid(alpha=.12)
fig.suptitle('BRICKED SORTING | SELECTED FOLDED LAYOUT',x=.05,ha='left',fontsize=20,fontweight='bold',color='#20313f')
fig.text(.05,.035,'Packaging study only • 20% smaller footprint; height unchanged • Shaded bin zones are reservations, not finished bins',fontsize=11,color='#885b26')
fig.subplots_adjust(top=.89,bottom=.13,wspace=.23);fig.savefig(OUT/'compact_packaging_study.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
print(json.dumps({'slopes':slopes,'optical_hits':view_hits,'scoop185':clearances['185'],'drum_top':b.zmax if hasattr(b,'zmax') else drum_env[-1]},indent=2),flush=True)
