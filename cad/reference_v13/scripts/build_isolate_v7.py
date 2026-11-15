"""V7 proposed Isolate + inspection prototype integrated with existing lift.
CadQuery2.7; no original geometry overwritten. Dynamic feeding remains untested.
"""
from pathlib import Path
import collections,copy,hashlib,json,math,struct
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'isolate_v7';OUT.mkdir(exist_ok=True)
REF=OUT/'reference_only';REF.mkdir(exist_ok=True)
old=json.loads((ROOT/'intake_stud_v6/intake_and_access_dimensions.json').read_text())
def box(x,y,z,dx,dy,dz):return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(x,y,z,d,h):return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))
def directed(origin,direction,d,h):return cq.Workplane(obj=cq.Solid.makeCylinder(d/2,h,cq.Vector(*origin),cq.Vector(*direction)))
def insert(p,size,origin,axis):
    pilot,depth,core={'M3':(4.4,5,3.4),'M4':(5.6,9.1,4.4),'M5':(6.4,10.5,5.4)}[size]
    return p.cut(directed(origin,axis,pilot,depth)).cut(directed(origin,axis,core,18))
def ry(deg):
    t=math.radians(deg);c,s=math.cos(t),math.sin(t);return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rx(deg):
    t=math.radians(deg);c,s=math.cos(t),math.sin(t);return np.array([[1,0,0],[0,c,-s],[0,s,c]])
RDRUM=ry(8);DRUM_ORIGIN=np.array([-180.,120.,755.]);U=RDRUM[:,0];V=RDRUM[:,1];WW=RDRUM[:,2]
def dw(u,v,w):return DRUM_ORIGIN+RDRUM@np.array([u,v,w],float)
parts={};notes={};counts={}
def part(name,p,count,note=''):
    parts[name]=p;counts[name]=count;notes[name]=note

drum=cyl(0,0,0,160,180).cut(cyl(0,0,-1,152,182))
for deg in(0,120,240):
    rib=box(71,0,5,10,4,170).rotate((0,0,0),(0,0,1),deg)
    drum=drum.union(rib)
for deg in(90,210,330):
    t=math.radians(deg);x,y=74*math.cos(t),74*math.sin(t)
    for z in(0,170):drum=drum.union(cyl(x,y,z,12,10))
    drum=insert(drum,'M3',(x,y,0),(0,0,1))
    drum=insert(drum,'M3',(x,y,180),(0,0,-1))
part('47_tumbler_barrel_160x180',drum,1,'3 internal10mm lifting ribs;6 M3 end inserts. Rotation/tilt do not guarantee singulation.')
rear=cyl(0,0,0,160,4).cut(cyl(0,0,-1,136,6))
front=cyl(0,0,0,160,4).cut(cyl(40,0,-1,65,6))
for deg in(90,210,330):
    t=math.radians(deg);x,y=74*math.cos(t),74*math.sin(t)
    rear=rear.cut(cyl(x,y,-1,3.4,6));front=front.cut(cyl(x,y,-1,3.4,6))
part('48_drum_rear_feed_guard',rear,1,'136mm rear opening clears stationary feed loft;M3x8 starting end screws. Rear spill containment must be tested.')
part('49_drum_eccentric_outlet_cap',front,1,'65mm aperture offset40mm. Intermittent discharge; test throughput and part clearance.')
roller=cyl(0,0,0,32,14).cut(cyl(0,0,-1,10,16)).cut(cyl(0,0,-1,16.2,6.2)).cut(cyl(0,0,8.8,16.2,6.2))
part('50_drum_625_bearing_roller',roller,4,'Two625ZZ bearings5x16x5 per roller.16.2 pockets5.2 deep;fit-test. M5 axle and inner-race spacers required.')
RC=96/math.sqrt(2);ZC=130-RC
cradle=box(0,0,0,35,210,16)
for y in(-RC,RC):
    cradle=cradle.union(box(-10,y,16,12,25,54))
    cradle=insert(cradle,'M5',(-4,y,ZC),(-1,0,0))
for x in(-10,10):
    for y in(-100,100):cradle=cradle.cut(cyl(x,y,-1,5.4,18))
part('51_drum_roller_cradle',cradle,2,'M5 roller axles enter rear posts; four M5 fixture holes. Top level/tilt set by wedges.')
for index,u in enumerate((20,160)):
    center=dw(u,0,-130);h=float(center[2]-583)
    p=cq.Workplane('XZ').polyline([(-21,0),(21,0),(21,h-math.tan(math.radians(8))*21),(-21,h+math.tan(math.radians(8))*21)]).close().extrude(105,both=True)
    for x in(-10,10):
        for y in(-100,100):p=insert(p,'M5',(math.cos(math.radians(8))*x,y,h-math.sin(math.radians(8))*x),tuple(-WW))
    for x in(-12,12):
        for y in(-70,70):p=insert(p,'M5',(x,y,0),(0,0,1))
    part(f'{52+index:02d}_drum_support_wedge_'+('rear'if index==0 else'front'),p,1,'Base plane583; four M5 top inserts and four underside inserts. Not load-rated.')
hub=cyl(0,0,0,24,14).cut(cyl(0,0,-1,5.2,16))
hub=insert(hub,'M3',(12,0,7),(-1,0,0))
tire=cyl(0,0,0,32,14).cut(cyl(0,0,-1,23.8,16))
part('54_drum_drive_core_5mm',hub,1,'5.2 shaft bore; one radial M3 heat insert/set screw. Match third NEMA17,not either existing motor.')
part('55_drum_friction_tire_TPU',tire,1,'TPU suggested;23.8 press-fit ID for24core is a starting fit. Contact pressure requires adjustment.')
motor=box(0,0,0,64,64,8).cut(cyl(0,0,-1,22.6,10))
for x in(-15.5,15.5):
    for y in(-15.5,15.5):motor=motor.cut(cyl(x,y,-1,3.4,10))
motor=motor.union(box(0,-28,-32,64,8,32))
for x in(-22,22):
    slot=cq.Workplane('XZ').center(x,-15).slot2D(16,5.4,90).extrude(10,both=True).translate((0,-28,0));motor=motor.cut(slot)
part('56_drum_NEMA17_adjustable_bracket',motor,1,'31x31 motor holes,22.6pilot;two M5 fixture slots. Main chassis attachment/drive preload must be engineered.')
thrust=box(15,0,0,40,40,8).union(box(0,12,8,14,12,40))
thrust=insert(thrust,'M5',(0,6,32),(0,1,0))
for x in(5,25):
    for y in(-12,12):thrust=thrust.cut(cyl(x,y,-1,3.4,10))
part('57_drum_front_thrust_bearing_holder',thrust,1,'One additional625 bearing contacts front cap face;M5 axle. Chassis mounting bracket still required.')

# A stationary supported loft enters the open rear drum,not its rotating wall.
top=np.array([-250.,0.,900.]);mid=np.array([-235.,75.,815.]);out=dw(20,0,0)
plane=cq.Plane(origin=cq.Vector(*out),xDir=cq.Vector(*V),normal=cq.Vector(*U))
ow=[cq.Workplane('XY',origin=tuple(top)).circle(58.2).val(),cq.Workplane('XY',origin=tuple(mid)).rect(86.4,76.4).val(),cq.Workplane(plane).rect(66.4,46.4).val()]
iw=[cq.Workplane('XY',origin=tuple(top+[0,0,1])).circle(55).val(),cq.Workplane('XY',origin=tuple(mid)).rect(80,70).val(),cq.Workplane(cq.Plane(origin=cq.Vector(*(out+U)),xDir=cq.Vector(*V),normal=cq.Vector(*U))).rect(60,40).val()]
feed=cq.Workplane(obj=cq.Solid.makeLoft(ow,ruled=False)).cut(cq.Workplane(obj=cq.Solid.makeLoft(iw,ruled=False)))
fb=feed.val().BoundingBox();FEED_SHIFT=np.array([fb.xmin,fb.ymin,fb.zmin]);feed=feed.translate(tuple(-FEED_SHIFT))
part('58_stationary_intake_to_drum_chute',feed,1,'Support-required loft prototype.110top opening,60x40 outlet. Fixed support/guard required before use.')

def path_frame(a,b):
    a,b=np.array(a,float),np.array(b,float);delta=b-a;length=float(np.linalg.norm(delta));h=math.hypot(delta[0],delta[1])
    across=np.array([delta[1]/h,-delta[0]/h,0]);forward=delta/length;normal=np.cross(across,forward)
    return np.column_stack([across,forward,normal]),a,length
R1,A1,L1=path_frame([75,160,635],[75,40,610]);R2,A2,L2=path_frame([75,28,595],[0,-70,585])
def vprofile(narrow=False,catch=False):
    if catch:return [(-47,31),(-9,0),(9,0),(88,16),(85,19),(6,3),(-6,3),(-44,34)]
    return [(-35,27),(-8,0),(8,0),(35,27),(32,30),(5,3),(-5,3),(-32,30)]if narrow else[(-47,31),(-9,0),(9,0),(47,31),(44,34),(6,3),(-6,3),(-44,34)]
def wire_at(points,y):return cq.Wire.makePolygon([cq.Vector(x,y,z)for x,z in points]+[cq.Vector(points[0][0],y,points[0][1])])
def tray(length,narrow=False,catch=False,cap_start=True,cap_end=True):
    profile=vprofile(narrow)
    if catch:
        p=cq.Workplane(obj=cq.Solid.extrudeLinear(wire_at(vprofile(catch=True),0),[],cq.Vector(0,length,0)))
        p=p.union(box(0,length+4,0,12,8,3))
    else:p=cq.Workplane(obj=cq.Solid.extrudeLinear(wire_at(profile,0),[],cq.Vector(0,length,0)))
    for y in(length*.2,length*.8):
        p=p.union(box(0,y,-8,110,22,8))
        for x in(-45,45):p=insert(p,'M3',(x,y,-8),(0,0,1))
    # Motor rides on a side shelf ABOVE the trough floor so it cannot hang
    # into the rotating scoop's high-position envelope.
    p=p.union(box(-60,length/2,26,60,55,8))
    for x in(-80,-40):
        for y in(length/2-16,length/2+16):p=insert(p,'M3',(x,y,34),(0,0,-1))
    # Flush joint holes on V2 flat floor;12mm source floor is widened locally.
    if narrow:
        p=p.cut(box(27,8,12,40,16,50))
        for y in(([8]if cap_start else[])+([length-8]if cap_end else[])):
            p=p.union(box(0,y,-5,32,16,5))
            p=p.cut(cyl(0,y,-6,3.4,12))
            p=p.cut(cq.Workplane(obj=cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(0,y,1.5),cq.Vector(0,0,1))))
    return p
part('59_V1_catch_and_vibration_tray',tray(L1,catch=True),1,'120mm horizontal run,25drop. Asymmetric V side ramp catches drum discharge and slopes into12mm floor. Transport untested.')
part('60_V2_vibration_tray',tray(L2,True,cap_start=False,cap_end=False),1,'64top,10floor;positive-X inlet wall relieved above12 for first16 length to clear V1. Transport/singulation untested.')
join=box(0,0,0,32,32,8)
for y in(-8,8):join=insert(join,'M3',(0,y,8),(0,0,-1))
part('61_optional_M3_joint_backer',join,0,'Optional generic two-hole M3 backer16apart;NOT used in current single-piece V2.')
base=box(0,0,0,50,45,8).union(box(0,0,8,50,24,16)).cut(directed((0,-24,24),(0,1,0),24.4,48))
for x in(-19,19):base=insert(base,'M3',(x,0,24),(0,0,-1))
for x in(-20,20):
    for y in(-16,16):base=base.cut(cyl(x,y,-1,3.4,10))
cap=box(0,0,0,50,24,16).cut(directed((0,-24,0),(0,1,0),24.4,48))
for x in(-19,19):cap=cap.cut(cyl(x,0,-1,3.4,18))
cap=cap.rotate((0,0,0),(1,0,0),180).translate((0,0,16))
part('62_24mm_vibration_motor_saddle',base,2,'Nominal24mm diameter motor,24.4 saddle. One under each V stage. Proposed motor specification,not a selected product.')
part('63_24mm_vibration_motor_cap',cap,2,'Print cap outer-face-down. TwoM3 bolts into saddle;do not clamp an eccentric weight.')

# Inspection tray above the ACTUAL maximum scoop solid,including rear walls.
frame=box(45,0,0,230,140,8).cut(box(0,0,-1,70,70,10))
for y in(-46,46):frame=frame.cut(box(45,y,-1,232,12.4,7.2))
for x in(-45,135):
    for y in(-60,60):frame=insert(frame,'M3',(x,y,0),(0,0,1))
for x,y in((-60,-60),(60,-60),(-60,60)):
    frame=frame.cut(cyl(x,y,-1,3.4,10))
frame=frame.union(box(-68.5,0,8,3,140,15)).union(box(158.5,0,8,3,140,15)).union(box(45,-68.5,8,230,3,15))
part('64_scanner_fixed_aperture_frame',frame,1,'World bottom560;70x70 release aperture.230x140 plate and two rail-relief grooves;incoming+X/+Y corner remains open.')
gate=box(0,0,0,100,90,3).union(box(60,0,0,20,12,3)).cut(cyl(60,0,-1,3.4,5))
part('65_scanner_sliding_release_blade',gate,1,'Closed part-supporting plane559.5;90mm travel+X clears70 aperture.100mm-stroke actuator remains a procurement proposal.')
rail=box(0,0,0,220,12,14).cut(box(0,-2,4.2,222,10,3.6))
for x in(-90,90):rail=rail.union(box(x,12,0,20,24,6)).cut(cyl(x,14,-1,3.4,9))
part('66_scanner_blade_guide_rail',rail,2,'3.6mm channel for3mm blade. Four2mm spacers needed between mounting pads and frame;M3x12 starts.')
post=box(0,0,0,12,12,140)
post=insert(post,'M3',(0,0,0),(0,0,1));post=insert(post,'M3',(0,0,140),(0,0,-1))
part('67_camera_gantry_post',post,3,'Three posts keep incoming corner clear;M3 inserts at both ends. Rigidly mount separately from feeder suspension.')
camera=box(0,0,0,140,140,6).cut(box(0,0,-1,40,40,8))
for x,y in((-60,-60),(60,-60),(-60,60)):camera=camera.cut(cyl(x,y,-1,3.4,8))
for x,y,ang in((30,0,0),(-30,0,0),(0,30,90),(0,-30,90)):
    slot=cq.Workplane('XY').center(x,y).slot2D(14,3.4,ang).extrude(8).translate((0,0,-1));camera=camera.cut(slot)
part('68_universal_camera_top_plate',camera,1,'Central40opening and radialM3 slots;actual camera adapter/lens/light mounting pending. Proposed lens working distance128.5.')
stop=cq.Workplane(obj=cq.Solid.extrudeLinear(wire_at([(-31,29.6),(-5,3.6),(5,3.6),(31,29.6),(31,60),(-31,60)],0),[],cq.Vector(0,3,0)))
for x in(-16,16):stop=stop.cut(directed((x,-1,50),(0,1,0),3.4,5))
part('69_V2_proposed_escapement_stop_blade',stop,1,'Proposal for closed stop80mm before V2 exit;35mm lift actuator/guide NOT yet designed. Do not claim automatic singulation.')
def extension_panel(width):
    p=box(0,0,0,width,150,3)
    for x in(-width/2+15,width/2-15):
        for y in(-60,60):
            p=p.cut(cyl(x,y,-1,3.4,5)).cut(cq.Workplane(obj=cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(x,y,1.5),cq.Vector(0,0,1))))
    return p
part('70_extension_front_back_cover_150high',extension_panel(200),20,'Adds two150mm rows;four M3 countersunk holes170x120. Supporting frame/insert backing pending.')
part('71_extension_end_cover_150high',extension_panel(494/3),12,'Four M3 countersunk holes134.667x120. Existing end panels retained.')

checks={}
for name,p in parts.items():
    p=p.clean();bb=p.val().BoundingBox();shift=np.array([0,0,-bb.zmin]);printable=p.translate(tuple(shift))
    assert printable.val().isValid() and len(printable.solids().vals())==1,name
    dims=[bb.xlen,bb.ylen,bb.zlen]
    assert dims[0]+10<256 and dims[1]+10<256 and dims[2]<256,(name,dims)
    cq.exporters.export(printable,str(OUT/(name+'.stl')),tolerance=.07,angularTolerance=.12)
    cq.exporters.export(printable,str(OUT/(name+'.step')))
    raw=(OUT/(name+'.stl')).read_bytes();edges=collections.Counter();n=struct.unpack_from('<I',raw,80)[0]
    for i in range(n):
        vs=struct.unpack_from('<9f',raw,84+i*50+12);v=[tuple(round(t,4)for t in vs[j:j+3])for j in(0,3,6)]
        for a,b in((0,1),(1,2),(2,0)):edges[tuple(sorted((v[a],v[b])))]+=1
    assert all(v==2 for v in edges.values()),(name,collections.Counter(edges.values()))
    checks[name]={'dimensions_xyz':dims,'count':counts[name],'source_to_print_z_shift':float(shift[2]),'valid_single_solid':True,'watertight':True,'fits_P2S_5mm_brim':True,'sha256_stl':hashlib.sha256(raw).hexdigest(),'note':notes[name]}
    print('Exported '+name,flush=True)

actors=[]
for a in old['actors']:
    b=copy.deepcopy(a)
    if b['group']=='intake'or(b['group']=='shell'and b['xyz'][2]>=600):b['xyz'][2]+=300
    actors.append(b)
def add(name,xyz,R=np.eye(3),color=(.24,.52,.65),group='isolate',source_raw=True):
    xyz=np.array(xyz,float)
    if source_raw:xyz=xyz-R@np.array([0,0,checks[name]['source_to_print_z_shift']])
    actors.append({'name':name,'xyz':xyz.tolist(),'rotation_matrix':np.array(R).tolist(),'color':list(color),'group':group,'source':'v7','stl_file':'isolate_v7/'+name+'.stl','step_file':'isolate_v7/'+name+'.step'})
RBAR=ry(98)
add('47_tumbler_barrel_160x180',DRUM_ORIGIN,RBAR,(.27,.48,.65))
add('48_drum_rear_feed_guard',dw(-4,0,0),RBAR,(.20,.36,.50))
add('49_drum_eccentric_outlet_cap',dw(180,0,0),RBAR,(.20,.36,.50))
for i,u in enumerate((20,160)):
    basepoint=dw(u,0,-130);add('51_drum_roller_cradle',basepoint,RDRUM,(.50,.55,.6))
    add(f'{52+i:02d}_drum_support_wedge_'+('rear'if i==0 else'front'),[basepoint[0],120,583],color=(.50,.55,.6))
    for v in(-RC,RC):add('50_drum_625_bearing_roller',dw(u,0,-130)+RDRUM@np.array([0,v,ZC]),RBAR,(.32,.35,.38))
add('54_drum_drive_core_5mm',dw(-4,0,-96),RBAR,(.78,.53,.17))
add('55_drum_friction_tire_TPU',dw(-4,0,-96),RBAR,(.12,.15,.18))
add('56_drum_NEMA17_adjustable_bracket',dw(-14,0,-96),RBAR,(.48,.53,.58))
add('57_drum_front_thrust_bearing_holder',dw(192,67.5,-32),RDRUM,(.5,.55,.6))
add('58_stationary_intake_to_drum_chute',FEED_SHIFT,color=(.82,.39,.16))
T1=A1-R1@np.array([0,0,3]);T2=A2-R2@np.array([0,0,3])
add('59_V1_catch_and_vibration_tray',T1,R1,(.16,.62,.48))
add('60_V2_vibration_tray',T2,R2,(.22,.65,.63))
for R,T,L in((R1,T1,L1),(R2,T2,L2)):
    point=T+R@np.array([-60,L/2,34])
    add('62_24mm_vibration_motor_saddle',point,R,(.27,.32,.37))
    add('63_24mm_vibration_motor_cap',T+R@np.array([-60,L/2,74]),R@rx(180),(.27,.32,.37))
add('64_scanner_fixed_aperture_frame',[0,-70,560],color=(.7,.72,.75),group='scanner')
add('65_scanner_sliding_release_blade',[0,-70,556.5],color=(.85,.55,.18),group='gate')
add('66_scanner_blade_guide_rail',[45,-24,552],color=(.46,.5,.54),group='scanner')
add('66_scanner_blade_guide_rail',[45,-116,552],rx(0)@np.diag([-1,-1,1]),(.46,.5,.54),'scanner')
for x,y in((-60,-60),(60,-60),(-60,60)):add('67_camera_gantry_post',[x,-70+y,568],color=(.72,.74,.76),group='scanner')
add('68_universal_camera_top_plate',[0,-70,708],color=(.72,.74,.76),group='scanner')
add('69_V2_proposed_escapement_stop_blade',T2+R2@np.array([0,L2-80,0]),R2,(.87,.57,.22),'escapement_proposal')
for x in(-400,-200,0,200,400):
    for z in(675,825):
        add('70_extension_front_back_cover_150high',[x,-247,z],rx(90),(.77,.16,.13),'shell_extension')
        add('70_extension_front_back_cover_150high',[x,247,z],rx(-90),(.77,.16,.13),'shell_extension')
for y in(-494/3,0,494/3):
    for z in(675,825):
        add('71_extension_end_cover_150high',[-497,y,z],np.array([[0,0,-1],[-1,0,0],[0,1,0]]),(.77,.16,.13),'shell_extension')
        add('71_extension_end_cover_150high',[497,y,z],np.array([[0,0,1],[1,0,0],[0,1,0]]),(.77,.16,.13),'shell_extension')

refs=copy.deepcopy(old['reference_actors']);volumes=[v for v in old['reference_volumes']if'RESERVED_NOT_BUILT'not in v['name']]
ref_models={
 '625ZZ_BEARING_REFERENCE_DO_NOT_PRINT':cyl(0,0,0,16,5).cut(cyl(0,0,-1,5,7)),
 'THIRD_NEMA17_REFERENCE_DO_NOT_PRINT':box(0,0,-48,42,42,48).union(cyl(0,0,0,22,2)).union(cyl(0,0,0,5,24)),
 'ERM24_CASE_AND_WEIGHT_REFERENCE_DO_NOT_PRINT':directed((0,-17.5,0),(0,1,0),24,35).union(directed((0,17.5,0),(0,1,0),3,12)).union(directed((0,24.5,4),(0,1,0),24,8)),
}
for name,p in ref_models.items():cq.exporters.export(p,str(REF/(name+'.step')))
def purchased(name,xyz,R,color):
    refs.append({'name':name,'step_file':'isolate_v7/reference_only/'+name+'.step','xyz':np.array(xyz).tolist(),'rotation_matrix':np.array(R).tolist(),'color':list(color),'group':'purchased_reference'})
for u in(20,160):
    for v in(-RC,RC):
        for offset in(0,9):purchased('625ZZ_BEARING_REFERENCE_DO_NOT_PRINT',dw(u+offset,v,-RC),RBAR,(.65,.68,.71))
purchased('625ZZ_BEARING_REFERENCE_DO_NOT_PRINT',dw(192,67.5,0),RDRUM@rx(-90),(.65,.68,.71))
purchased('THIRD_NEMA17_REFERENCE_DO_NOT_PRINT',dw(-14,0,-96),RBAR,(.16,.18,.21))
for R,T,L in((R1,T1,L1),(R2,T2,L2)):
    purchased('ERM24_CASE_AND_WEIGHT_REFERENCE_DO_NOT_PRINT',T+R@np.array([-60,L/2,58]),R,(.18,.20,.23))
def refbox(name,center,size,color):volumes.append({'name':name,'kind':'box','center':list(center),'size':list(size),'color':list(color)})
refbox('drum_support_platform_REFERENCE',[-90,120,576.5],[300,220,13],[.46,.49,.52])
refbox('camera_PCB_envelope_NOT_SELECTED',[0,-70,711],[30,30,6],[.15,.27,.22])
volumes.append({'name':'camera_lens_envelope_NOT_SELECTED','kind':'cylinder','center':[0,-70,698],'diameter':12,'height':20,'color':[.12,.14,.16]})
refbox('100mm_stroke_gate_actuator_PROPOSED',[260,-70,558],[180,35,35],[.22,.25,.28])
refbox('gate_actuator_rod_PROPOSED',[110,-70,558],[120,4,4],[.65,.68,.71])
for x in(-450,450):
    for y in(-200,200):refbox('stationary_chassis_post_REFERENCE',[x,y,460.5],[20,20,879],[.55,.58,.62])
# Reference supports terminate under mounts; exact joints and stiffness require design.
refbox('left_upper_chassis_beam_REFERENCE',[-450,0,560],[20,420,20],[.55,.58,.62])
for y in(40,210):refbox('drum_platform_cantilever_REFERENCE',[-195,y,560],[510,20,20],[.55,.58,.62])
for R,T,L in((R1,T1,L1),(R2,T2,L2)):
    for x in(-45,45):
        for yy in(L*.2,L*.8):
            pp=T+R@np.array([x,yy,-15.5]);volumes.append({'name':'feeder_isolator_20x15_PROPOSED','kind':'cylinder','center':pp.tolist(),'diameter':20,'height':15,'color':[.12,.14,.16]})

def shape_of(a):
    p=cq.importers.importStep(str(ROOT/a['step_file']))
    if'rotation_matrix'in a:
        R=np.array(a['rotation_matrix'])
        loc=cq.Location(cq.Plane(origin=tuple(a['xyz']),xDir=tuple(R[:,0]),normal=tuple(R[:,2])))
        return cq.Workplane(obj=p.val().located(loc))
    for axis,k in(((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')):
        if a[k]:p=p.rotate((0,0,0),axis,a[k])
    return p.translate(a['xyz'])
cache={}
for pose,extension in(('CLOSED',0),('UPPER_DRAWER_OPEN',350)):
    asm=cq.Assembly(name='BRICKED_V7_ISOLATE_'+pose+'_PROTOTYPE')
    for i,a in enumerate(actors+refs):
        p=cache.get(i)
        if p is None:p=shape_of(a);cache[i]=p
        if extension and a.get('drawer_tier')==2:p=p.translate((0,extension,0))
        asm.add(p,name=f'{i:03d}_'+a['name'])
    for i,v in enumerate(volumes):
        if v['kind']=='box':x,y,z=v['center'];dx,dy,dz=v['size'];p=box(x,y,z-dz/2,dx,dy,dz)
        else:x,y,z=v['center'];p=cyl(x,y,z-v['height']/2,v['diameter'],v['height'])
        asm.add(p,name=f'REF_{i:03d}_'+v['name'])
    cq.exporters.export(asm.toCompound(),str(OUT/('V7_'+pose+'_REFERENCE_ONLY.step')))

# Key clearance tests are engineering checks,not conveyor-performance simulation.
scoop=cq.importers.importStep(str(ROOT/'05_open_scoop_PRINT_FLAT.step')).rotate((0,0,0),(1,0,0),-40).translate((0,-70,171+200+80))
scoop_zmax=scoop.val().BoundingBox().zmax
assert scoop_zmax<552
gate_index=next(i for i,a in enumerate(actors)if a['name'].startswith('65_'))
fixed_scanner=cq.Compound.makeCompound([cache[i].val()for i,a in enumerate(actors)if a['group']=='scanner'])
gate_hits=[]
for travel in(0,15,30,45,60,75,90):
    moving=cache[gate_index].translate((travel,0,0)).val()
    hit=moving.intersect(fixed_scanner).Volume()
    if hit>.01:gate_hits.append({'travel':travel,'intersection_mm3':hit})
assert not gate_hits,gate_hits
scanner_vs_feeders=[]
for i,a in enumerate(actors):
    if a['name'].startswith(('59_','60_')):
        hit=cache[i].val().intersect(fixed_scanner).Volume()
        if hit>.01:
            pairs=[]
            for j,b in enumerate(actors):
                if b['group']=='scanner':
                    v=cache[i].val().intersect(cache[j].val()).Volume()
                    if v>.01:pairs.append({'scanner_part':b['name'],'volume':v})
            scanner_vs_feeders.append({'part':a['name'],'intersection_mm3':hit,'pairs':pairs})
assert not scanner_vs_feeders,scanner_vs_feeders
spec=copy.deepcopy(old)
spec['revision']='V7 proposed Isolate and scanner 2026-10-29';spec['actors']=actors;spec['reference_actors']=refs;spec['reference_volumes']=volumes
spec['body_xyz']=[1000,500,900];spec['overall_height_with_studs']=1016.5
for key in('bottom_z','top_z','seam_backer_bottom_z'):spec['latest_intake'][key]+=300
spec['latest_intake']['drum_connection_status']='V7 stationary loft to rear opening,prototype CAD only;flow and fixed support untested.'
spec['latest_intake']['prior_feeder_placeholders']='Replaced by V7 actual prototype drum,trays and inspection-frame parts;actuation and transport testing remain pending.'
spec['proposed_isolate']={
 'status':'Actual prototype part geometry; supports/hardware envelopes noted. Not a validated singulator or complete machine.',
 'body_xyz':[1000,500,900],'roof_top_z':904,'overall_stud_top_z':1016.5,'existing_top_shift':300,
 'reuse':'Existing lift,drawers,bins,floor,600mm lower cover,roof and studs retained. Add300mm upper section;translate existing top pieces up300.',
 'drum':{'OD':160,'ID':152,'length':180,'tilt_deg':8,'rear_axis_xyz':DRUM_ORIGIN.tolist(),'front_axis_xyz':dw(180,0,0).tolist(),'inside_lift_rib_height':10,'rear_opening':136,'outlet_hole':65,'outlet_offset':40,'roller_OD':32,'bearings':'9x625ZZ5x16x5:8 in4 rollers+1 axial guide','speed_trial_rpm':[2,10],'drive':'Third NEMA17+TPU friction wheel32OD,not the two existing motors. Speed and torque unverified.','axial_retention':'Front625 guide proposed;mount/support load path and reverse retention pending'},
 'intake':{'existing_stud_bottom_z':904,'feed_top_xyz':top.tolist(),'feed_outlet_xyz':out.tolist(),'feed_top_ID':110,'feed_outlet_W_H':[60,40],'feed_part_print_world_shift':FEED_SHIFT.tolist(),'drum_entry':'Stationary outlet through rear guard,20mm inside barrel at axis center;no entry through rotating wall'},
 'V1':{'start_inner_floor':A1.tolist(),'end_inner_floor':[75,40,610],'length_3d':L1,'floor_drop':25,'slope_deg':math.degrees(math.asin(25/L1)),'length_single_part':True,'cross_section':'Asymmetric V;12flat floor;left lip(-44,34),right lip(85,19);side ramp16rise over79run catches side discharge.','proposed_motor':'12V ERM24mm body diameter x35case;clamp24.4;weight envelope and ratings TBD'},
 'V2':{'start_inner_floor':A2.tolist(),'end_inner_floor':[0,-70,585],'length_3d':L2,'single_piece':True,'slope_deg':math.degrees(math.asin(10/L2)),'clear_top_width':64,'proposed_motor':'One same24mm ERM motor on raised side shelf. Direction/transport not established.','escapement':'Stop blade80mm before exit;35mm lift actuator/guide still pending. Do not claim one-part-only delivery'},
 'scanner':{'frame_bottom_z':560,'blade_bottom_z':556.5,'object_support_plane':559.5,'aperture':[70,70],'blade_travel_X':90,'guide_bottom_z':552,'camera_plate_bottom_z':708,'proposed_lens_face_z':688,'nominal_working_distance':128.5,'camera_mount':'Universal plate withslots;selected PCB/lens adapter pending','release_actuator':'100mm stroke linear actuator proposal;mount/coupler/model not finalized','incoming_corner':'PositiveX/positiveY kept open;three camera posts avoid incoming V2'},
 'transfers':[{'from':'stud','to':'feedchute','z':[904,900],'drop':4},{'from':'drum','to':'V1 asymmetric side ramp','note':'Side-entry onto inclined broad wall near worldY120;actual drop depends rotating65mm outlet phase. Prove with LEGO.'},{'from':'V1','to':'V2','z':[610,595],'drop':15,'plan_gap_Y_before_apron':12,'V1_apron_extension':8},{'from':'V2','to':'scanner blade','z':[585,559.5],'drop':25.5}],
 'automatic_piece_envelope_proposal':'Start testing loose parts fitting65 outlet and70scanner;no proven maximum or10696 coverage yet. Oversize/manual exclusions logged.',
 'required_additional_hardware':['Third NEMA17+driver for drum','9x625ZZ bearings','M5 axles and correct inner-race spacers','2 proposed24mm ERM motors+drivers','feeder suspension/isolation and tuning hardware','100mm-stroke gate actuator','35mm-stroke escapement actuator/guide or equivalent','camera/lens/light adapter','frame,guards,position/occupancy sensors and wiring'],
 'validation':{'new_STL_types':len(checks),'part_checks':checks,'actual_max_scoop_Z_at_H200':scoop_zmax,'minimum_scanner_module_Z':552,'vertical_clearance_bound_to_scoop':552-scoop_zmax,'blade_scanner_samples':7,'blade_hits':gate_hits,'scanner_feeder_intersections':scanner_vs_feeders,'scope':'Individual meshes,key static clearances and blade travel only;no material-flow,dynamic-vibration,torque,capacity or full load/stability validation'},
 'remaining':['Full stationary structural supports/fasteners and guards','ERM procurement,eccentric clearances,suspension and vibration tuning','Escapement guides/actuation and double-feed sensing','Scanner actuator mounting/coupler and camera/lens/light adapter','intake support/removable joints and barrel reverse thrust retention','Receiver from existing scoop tobins','Drawer runners/latches/individual-bin retention/switches','Power budget and electronics mounting/wiring'],
 'recommendation_rating_out_of_10':8,
 'sources':{'625bearing':'https://bearingfinder.ntnamericas.com/item/deep-groove-ball-bearings/single-row-radial-ball-bearings/625zz','linear_feeder_design_reference':'https://www.rnaautomation.com/products/feeding-and-handling/spares-standard-equipment/linears/','servo_reference_not_used_for90mm_gate':'https://towerpro.com.tw/product/sg90-7/'},
}
spec['effective_modeled_print_counts']=dict(collections.Counter(a['stl_file']for a in actors))
(OUT/'isolate_and_machine_dimensions.json').write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps({'new_types':len(checks),'body':[1000,500,900],'drum':[160,180],'actual_scoop_zmax':scoop_zmax,'scanner_clearance_bound':552-scoop_zmax,'blade_samples_clear':not gate_hits},indent=2),flush=True)
