"""Bricked Sorting V4 modular 2x1-style housing/layout. CadQuery2.7.

Adds layout parts; never modifies the original V3 lift/electronics geometry.
Unspecified feeder/scanner/PSU attachments remain explicit reference volumes.
"""
from pathlib import Path
import collections,hashlib,json,math,struct
import cadquery as cq
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'brick_layout_v4';OUT.mkdir(exist_ok=True)
W,D,BODY_H,STUD_D,STUD_H=1000.,500.,600.,300.,112.5
TW,TD=200.,500./3
FLOOR_Z=13.;FLOOR_T=8.;LIFT_Z=171.;YAW_Y=-70.;LIFT_Y=YAW_Y-90
COLORS={'base':[.20,.25,.30],'cover':[.77,.16,.13],'stud':[.83,.21,.15],'bin':[.69,.73,.77],'lift':[.90,.58,.18],'scoop':[.08,.58,.62],'electronics':[.24,.43,.53],'reference':[.66,.49,.72]}
def box(x,y,z,dx,dy,dz):return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(x,y,z,d,h):return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))
def pocket(part,x,y,z,size,up=False):
    pilot,depth,core={'M3':(4.4,5.,3.4),'M5':(6.4,10.5,5.4)}[size]
    direction=cq.Vector(0,0,1 if up else -1)
    return part.cut(cq.Workplane(obj=cq.Solid.makeCylinder(pilot/2,depth,cq.Vector(x,y,z),direction))).cut(cyl(x,y,-1,core,210))
def tile(riser_y=None):
    p=box(0,0,0,TW,TD,FLOOR_T)
    for x in (-85,85):
        for y in (-TD/2+15,TD/2-15):
            p=p.cut(cyl(x,y,-1,5.4,10)).cut(cyl(x,y,2.5,10,6.5))
    if riser_y is not None:
        for x in (-85,85):p=p.cut(cyl(x,riser_y,-1,5.4,10)).cut(cyl(x,riser_y,-1,10,6.5))
    return p
def splice(quad=False):
    p=box(0,0,0,60,60 if quad else 30,13)
    for x in (-15,15):
        for y in ((-15,15) if quad else (0,)):p=pocket(p,x,y,13,'M5')
    return p
def skin(width,height,thickness=3.):
    p=box(0,0,0,width,height,thickness)
    for x in (-width/2+15,width/2-15):
        for y in (-height/2+15,height/2-15):
            p=p.cut(cyl(x,y,-1,3.4,thickness+2))
            p=p.cut(cq.Workplane(obj=cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(x,y,thickness-1.5),cq.Vector(0,0,1))))
    return p

parts={}
parts['17_floor_tile_A_PRINT_13']=tile()
parts['18_floor_tile_B_REAR_RISERS']=tile(-220-(-D/3))
parts['19_floor_tile_C_FRONT_RISERS']=tile(-50)
parts['20_floor_quad_splice_PRINT_8']=splice(True)
parts['21_floor_edge_splice_PRINT_12']=splice(False)
parts['22_front_back_beauty_panel_PRINT_30']=skin(200,193)
parts['23_side_beauty_panel_PRINT_18']=skin((D-6)/3,193)
parts['24_top_cover_tile_PRINT_15']=skin(TW,TD,4)

# Stand-offs mate to existing base without a 150mm long screw. Side window
# allows an L-key into the recessed upper screw head; verify access physically.
riser=box(0,0,0,36,36,150)
riser=riser.cut(box(0,-1,16,24,40,120))
riser=pocket(riser,0,0,0,'M5',True)
riser=riser.cut(cyl(0,0,135,5.4,16)).cut(cyl(0,0,132,10,12))
parts['25_lift_riser_PRINT_4']=riser

# Generic reusable backing strap for future stationary brackets.
strap=box(0,0,0,40,14,8)
for x in (-12,12):strap=pocket(strap,x,0,8,'M3')
parts['26_M3_backing_strap']=strap

# Hollow quarter stud, exported cap-down. Joining holes on each internal
# radial flange; use M3 bolts into separate backing straps, no captive nuts.
quarter=(cyl(0,0,0,STUD_D,STUD_H).intersect(box(75,75,0,150,150,STUD_H)))
quarter=quarter.cut(cyl(0,0,3.2,STUD_D-6.4,STUD_H))
for x,y,dx,dy in ((71,4,142,8),(4,71,8,142)):
    quarter=quarter.union(box(x,y,3.2,dx,dy,8))
for x,y in ((55,4),(79,4),(4,55),(4,79)):
    quarter=quarter.cut(cyl(x,y,-1,3.4,14))
# Flange material is clipped to the quarter exterior envelope.
quarter=quarter.intersect(box(75,75,0,150,150,STUD_H))
parts['27_stud_quarter_CAP_DOWN_PRINT_8']=quarter

# Generic flat M3 support block for later stationary cover frame. It defines
# one mating interface; positions on a structural frame remain to be chosen.
cleat=box(0,0,0,30,30,13)
for x in (-8,8):cleat=pocket(cleat,x,0,13,'M3')
parts['28_M3_frame_insert_block']=cleat
studstrap=box(0,0,0,40,20,8)
for x in (-12,12):
    for y in (-4,4):studstrap=pocket(studstrap,x,y,8,'M3')
parts['30_stud_cross_seam_strap_PRINT_8']=studstrap

# One repeatable bin prototype: 21deg angular body,2.4walls,3floor,100high.
# Inner wall is lowered to45 to preserve a potential receiving path. Capacity
# below that lip, not the full sidewall height, is the conservative fill volume.
def sector(ri,ro,half=10.5,n=24):
    pts=[]
    for i in range(n+1):
        t=math.radians(-half+2*half*i/n);pts.append((ro*math.sin(t),ro*math.cos(t)))
    for i in range(n,-1,-1):
        t=math.radians(-half+2*half*i/n);pts.append((ri*math.sin(t),ri*math.cos(t)))
    return pts
wire=cq.Workplane('XY').polyline(sector(160,305)).close().val()
inside=cq.Workplane('XY').add(wire).toPending().offset2D(-2.4).extrude(110).translate((0,0,3))
binpart=cq.Workplane('XY').add(wire).toPending().extrude(100).cut(inside)
binpart=binpart.cut(cyl(0,0,45,326,65))
bbin=binpart.val().BoundingBox();BIN_Y=(bbin.ymin+bbin.ymax)/2
binpart=binpart.translate((0,-BIN_Y,0))
parts['29_wedge_bin_LAYOUT_PROTOTYPE']=binpart

checks={};printables={};counts={
 '17_floor_tile_A_PRINT_13':13,'18_floor_tile_B_REAR_RISERS':1,'19_floor_tile_C_FRONT_RISERS':1,
 '20_floor_quad_splice_PRINT_8':8,'21_floor_edge_splice_PRINT_12':12,
 '22_front_back_beauty_panel_PRINT_30':30,'23_side_beauty_panel_PRINT_18':18,
 '24_top_cover_tile_PRINT_15':15,'25_lift_riser_PRINT_4':4,
 '26_M3_backing_strap':None,'27_stud_quarter_CAP_DOWN_PRINT_8':8,
 '28_M3_frame_insert_block':None,'29_wedge_bin_LAYOUT_PROTOTYPE':16,
 '30_stud_cross_seam_strap_PRINT_8':8}
for name,p in parts.items():
    p=p.clean();bb=p.val().BoundingBox();p=p.translate((0,0,-bb.zmin))
    assert p.val().isValid() and len(p.solids().vals())==1,name
    dims=[bb.xlen,bb.ylen,bb.zlen]
    assert dims[0]+10<256 and dims[1]+10<256 and dims[2]<256,(name,dims)
    cq.exporters.export(p,str(OUT/(name+'.stl')),tolerance=.08,angularTolerance=.12)
    cq.exporters.export(p,str(OUT/(name+'.step')))
    raw=(OUT/(name+'.stl')).read_bytes();num=struct.unpack_from('<I',raw,80)[0];edges=collections.Counter()
    for i in range(num):
        values=struct.unpack_from('<9f',raw,84+i*50+12)
        v=[tuple(round(t,4) for t in values[j:j+3]) for j in (0,3,6)]
        for a,b in ((0,1),(1,2),(2,0)):edges[tuple(sorted((v[a],v[b])))]+=1
    assert all(v==2 for v in edges.values()),name
    checks[name]={'size_mm_xyz':dims,'solid_count':1,'valid':True,'watertight':True,'fits_P2S_with_5mm_brim':True,'copies_for_layout':counts[name],'volume_cm3_each':p.val().Volume()/1000,'sha256_stl':hashlib.sha256(raw).hexdigest()}
    printables[name]=p
    print('Exported '+name,flush=True)

# Assembly actors store exact print-to-world rigid transforms. Angles are
# applied X, then Y, then Z; origin is floor-splice underside z0.
actors=[]
def add(name,xyz=(0,0,0),rx=0,ry=0,rz=0,color='base',group='base',source='new'):
    actors.append({'name':name,'xyz':list(xyz),'rx':rx,'ry':ry,'rz':rz,'color':COLORS.get(color,color),'group':group,'source':source})
xs=[-400,-200,0,200,400];ys=[-D/3,0,D/3]
for x in xs:
    for y in ys:
        name='18_floor_tile_B_REAR_RISERS' if x==0 and y<0 else '19_floor_tile_C_FRONT_RISERS' if x==0 and y==0 else '17_floor_tile_A_PRINT_13'
        add(name,(x,y,FLOOR_Z))
        add('24_top_cover_tile_PRINT_15',(x,y,600),color='cover',group='shell')
for x in (-300,-100,100,300):
    for y in (-D/6,D/6):add('20_floor_quad_splice_PRINT_8',(x,y,0))
for x in (-300,-100,100,300):
    for y in (-D/2+15,D/2-15):add('21_floor_edge_splice_PRINT_12',(x,y,0))
for x in (-W/2+15,W/2-15):
    for y in (-D/6,D/6):add('21_floor_edge_splice_PRINT_12',(x,y,0),rz=90)
for x in xs:
    for z in (117.5,310.5,503.5):
        add('22_front_back_beauty_panel_PRINT_30',(x,-250,z),rx=-90,color='cover',group='shell')
        add('22_front_back_beauty_panel_PRINT_30',(x,250,z),rx=90,color='cover',group='shell')
for y in (-(D-6)/3,0,(D-6)/3):
    for z in (117.5,310.5,503.5):
        add('23_side_beauty_panel_PRINT_18',(-500,y,z),rx=90,rz=90,color='cover',group='shell')
        add('23_side_beauty_panel_PRINT_18',(500,y,z),rx=90,rz=-90,color='cover',group='shell')
for x in (-250,250):
    for yaw in (0,90,180,270):
        # Cap-down file rotated180aboutX, so cap becomes upper stud surface.
        add('27_stud_quarter_CAP_DOWN_PRINT_8',(x,0,604+STUD_H),rx=180,rz=yaw,color='stud',group='shell')
        a=math.radians(yaw)
        add('30_stud_cross_seam_strap_PRINT_8',(x+67*math.cos(a),67*math.sin(a),604+STUD_H-11.2-8),rz=yaw,color='stud',group='shell')
for x in (-85,85):
    for y in (-220,-50):add('25_lift_riser_PRINT_4',(x,y,FLOOR_Z+8),color='lift',group='lift')

# Reuse original baseline files with documented transforms.
H=145.
for name,xyz,rx in [
 ('01_ground_base',(0,LIFT_Y,LIFT_Z),0),
 ('03_top_rod_brace',(0,LIFT_Y,LIFT_Z+342),0),
 ('04_lower_switch_mount',(0,LIFT_Y,LIFT_Z+8),0),
 ('07_upper_switch_rod_mount',(0,LIFT_Y,LIFT_Z+241),0),
 ('02_moving_carriage_v3',(0,LIFT_Y,LIFT_Z+H),0),
 ('06_angled_shaft_hub',(0,YAW_Y,LIFT_Z+H+48),0),
 ('05_open_scoop_PRINT_FLAT',(0,YAW_Y,LIFT_Z+H+80),-40),
 ('10_M2_switch_backer_PRINT_TWICE',(0,LIFT_Y-30,LIFT_Z+83),-90),
 ('10_M2_switch_backer_PRINT_TWICE',(0,LIFT_Y-30,LIFT_Z+258),-90)]:
    add(name,xyz,rx=rx,color='scoop' if name.startswith('05') else 'lift',group='lift',source='baseline')
bin_map=[]
for floor,z in ((1,143),(2,248)):
    for slot in range(1,9):
        # Slot1 is at -X in plan. Front-view sign and electrical direction
        # must be confirmed; these values are not controller calibration.
        yaw=78.75-(slot-1)*22.5
        theta=math.radians(yaw)
        xyz=(-BIN_Y*math.sin(theta),YAW_Y+BIN_Y*math.cos(theta),z)
        add('29_wedge_bin_LAYOUT_PROTOTYPE',xyz,rz=yaw,color='bin',group='bins')
        bin_map.append({'code':f'{floor}-{slot}','yaw_deg_proposed':yaw,'bottom_z':z,'outer_rim_z':z+100,'receiving_lip_z':z+45,'status':'layout only; not controller calibration'})
add('16_electronics_layout_panel',(400,-100,35),rz=90,color='electronics',group='electronics',source='electronics')

references=[
 {'name':'left_rod','kind':'cylinder','center':[-45,LIFT_Y,LIFT_Z+185],'diameter':12,'height':350,'color':[.6,.64,.68]},
 {'name':'right_rod','kind':'cylinder','center':[45,LIFT_Y,LIFT_Z+185],'diameter':12,'height':350,'color':[.6,.64,.68]},
 {'name':'lead_screw','kind':'cylinder','center':[0,LIFT_Y,LIFT_Z+215],'diameter':8,'height':310,'color':[.6,.64,.68]},
 {'name':'lift_motor','kind':'box','center':[0,LIFT_Y,LIFT_Z+34.35],'size':[42.3,42.3,47.3],'color':[.15,.18,.21]},
 {'name':'rotating_motor','kind':'box','center':[0,YAW_Y,LIFT_Z+H+16],'size':[42,42,48],'color':[.15,.18,.21]},
 {'name':'PSU_reserved_not_retained','kind':'box','center':[425,-100,67.94],'size':[27.94,141.986,39.878],'color':[.28,.31,.34]},
 {'name':'buck_reserved','kind':'box','center':[367,-100,58.5],'size':[25,51,21],'color':[.82,.52,.16]},
 {'name':'V1_RESERVED_NOT_BUILT','kind':'box','center':[-265,25,552],'size':[220,70,48],'color':[.66,.49,.72]},
 {'name':'V2_RESERVED_NOT_BUILT','kind':'box','center':[-110,-35,535],'size':[170,60,35],'color':[.66,.49,.72]},
 {'name':'SCANNER_RESERVED_NOT_BUILT','kind':'box','center':[0,YAW_Y,545],'size':[100,90,18],'color':[.66,.49,.72]},
]

def path_for(a):
    if a['source']=='baseline':return ROOT/(a['name']+'.step')
    if a['source']=='electronics':return ROOT/'electronics_addon'/(a['name']+'.step')
    return OUT/(a['name']+'.step')
cache={};assembly=cq.Assembly(name='BRICKED_V4_LAYOUT_REFERENCE_NOT_RELEASED')
for i,a in enumerate(actors):
    p=cache.setdefault(a['name'],None)
    if p is None:p=cq.importers.importStep(str(path_for(a)));cache[a['name']]=p
    for axis,key in [((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')]:
        if a[key]:p=p.rotate((0,0,0),axis,a[key])
    p=p.translate(a['xyz']);assembly.add(p,name=f"{i:03d}_{a['name']}")
for ref in references:
    x,y,z=ref['center']
    if ref['kind']=='box':
        dx,dy,dz=ref['size'];p=box(x,y,z-dz/2,dx,dy,dz)
    else:p=cyl(x,y,z-ref['height']/2,ref['diameter'],ref['height'])
    assembly.add(p,name='REF_'+ref['name'])
cq.exporters.export(assembly.toCompound(),str(OUT/'V4_FULL_LAYOUT_REFERENCE_ONLY.step'))

spec={
 'revision':'V4 brick-style layout 2026-10-29','units':'mm/deg',
 'status':'Layout prototype; original lift unchanged. Cover supporting frame, routed receivers, rack, and feeder/scanner mechanisms not released.',
 'outer_body_xyz':[W,D,BODY_H],
 'shell_details':{'wall_thickness':3,'top_thickness':4,'top_surface_z':604,'stud_diameter':STUD_D,'stud_height':STUD_H,'stud_centers_xy':[[-250,0],[250,0]],'overall_max_height':604+STUD_H,'intent':'2:1 footprint with two studs, LEGO-like cosmetic proportions; not a stackable licensed brick'},
 'floor':{'tile_size_xy':[TW,TD],'columns':5,'rows':3,'underside_z':13,'top_z':21,'seam_gap_nominal':0,'fit_allowance_status':'No panel seam gap built in; shrink/tune after fit coupons','grid_centers_x':xs,'grid_centers_y':ys,'M5_corner_local_x':[-85,85],'M5_corner_local_y':[-TD/2+15,TD/2-15],'counterbore_diameter':10,'counterbore_depth':5.5,'fastener_start':'M5x12 through2.5 remaining tile into9.5 insert; verify actual engagement','inserts_in_splices':56,'splices_are_structural_prototypes_not_load_rated':True},
 'lift':{'original_parts_reused':True,'baseline_to_world_translation':[0,LIFT_Y,LIFT_Z],'yaw_axis_xy':[0,YAW_Y],'base_underside_z':LIFT_Z,'riser_height':150,'riser_bottom_z':21,'riser_centers_xy':[[x,y] for x in(-85,85) for y in(-220,-50)],'riser_M5_insert_entry_bottom':True,'riser_top_head_recess_diameter':10,'riser_top_recess_depth':12,'riser_top_screw_plate_thickness':6,'riser_top_screw_start':'M5x16 through6 top plate plus2.5 unthreaded original base into approx7.5 insert engagement; verify actual fit and bottoming','carriage_H_range_relative_original_base':[95,200],'world_outlet_floor_z_approx':[253.7,358.7],'reference_carriage_H':H},
 'bins':{'count':16,'tiers':2,'inner_radius':160,'outer_radius':305,'body_angle_deg':21,'pitch_deg':22.5,'wall':2.4,'floor':3,'height':100,'inner_receiving_lip_height':45,'retained_interior_depth_to_lip':42,'theoretical_void_to_lip_liters':inside.val().Volume()/110*42/1000000,'print_local_y_translation_removed':BIN_Y,'poses':bin_map,'maximum_retained_fill_height':'Conservative fill at low inner lip45 (42 above internal floor), not100; test actual loose-fill volume.','routing_status':'Existing scoop radius110 leaves50 radial gap. Removable narrowing/extension receiver not designed. Bin prototype is not a final routed bin.'},
 'electronics':{'panel_world_xyz':[400,-100,35],'panel_yaw':90,'PSU_retention':'pending','mount_to_floor':'brackets/spacers pending; reference panel currently floats above floor'},
 'interfaces':{'new_M3_pilot':4.4,'new_M3_depth':5,'new_M5_pilot':6.4,'new_M5_depth':10.5,'beauty_panel_bolts':'M3 countersunk3.4 clearance; insert backing frame not dimensioned','beauty_panel_heights':193,'beauty_panel_bottom_z':21,'front_back_panel_size':[200,193,3],'side_panel_size':[(D-6)/3,193,3],'backing_strap_hole_spacing':24,'cover_insert_block_hole_spacing':16,'stud_cross_seam_pattern':[24,8],'stud_cross_seam_M3_insert_count':32,'stud_cross_seam_screw_start':'32xM3x16 through11.2 cap/flange into4.8 engagement; check insert bottom','stud_quarter_join_holes':'Two pairs24 spacing on inward radial flanges. Part30 bridges BOTH sides of each seam with24x8 four-hole pattern. Final stud-to-lid retention pending.'},
 'actors':actors,'reference_volumes':references,'print_checks':checks,
 'not_yet_designed':['load-rated cover supporting frame and its exact panel backing locations','bin shelf/rack supports','removable narrowed scoop/receiver and physical flow tests','bin presence-switch brackets','drum/hopper interface','V1/V2 motors, mounts, isolation and trays','scanner camera/lighting/release gate','angular home sensor and cabling','PSU retention/guard and power-panel supports','stud-to-lid fasteners and feed opening'],
 'validation_scope':'Individual exported new solids and meshes checked. No full-machine continuous collision or stress validation. Reserved feed/scanner volumes are NOT functional mechanisms.',
 'recommendation':{'rating_out_of_10':9,'scope':'modular brick-shaped housing with internal semicircle; rating is design judgement, not tested reliability'},
}
(OUT/'layout_dimensions_and_parts.json').write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps({'new_STL_types':len(checks),'body':[W,D,BODY_H],'overall_height':604+STUD_H,'all_new_meshes_valid':True,'new_material_volume_cm3_if_all_fixed_counts_printed':sum(c['volume_cm3_each']*(c['copies_for_layout'] or 0) for c in checks.values())},indent=2),flush=True)
