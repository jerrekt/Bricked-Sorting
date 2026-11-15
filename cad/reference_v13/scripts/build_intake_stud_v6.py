"""V6: left stud is a loading funnel, open through the top cover to the drum.
The drum throat/feeder interface is deliberately provisional. Retains V3 lift,
V5 drawers, right stud and existing cosmetic geometry outside six roof tiles.
"""
from pathlib import Path
import collections,copy,hashlib,json,math,struct
import cadquery as cq
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'intake_stud_v6';OUT.mkdir(exist_ok=True)
old=json.loads((ROOT/'external_access_v5/outside_access_dimensions.json').read_text())
def box(x,y,z,dx,dy,dz):return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(x,y,z,d,h):return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))
SLOPE=80/112.5
outer=cq.Workplane(obj=cq.Solid.makeCone(53.2,133.2,112.5))
inner=cq.Workplane(obj=cq.Solid.makeCone(50-SLOPE,130+SLOPE,114.5,cq.Vector(0,0,-1)))
cone=outer.cut(inner)
wall=cyl(0,0,0,300,112.5).cut(cyl(0,0,-1,293.6,115))
rim=cyl(0,0,109.3,300,3.2).cut(cyl(0,0,108,260,6))
quarter=wall.union(cone).union(rim)
foot=143/math.sqrt(2)
for x in(-foot,foot):
    for y in(-foot,foot):
        quarter=quarter.union(cyl(x,y,0,12,10)).cut(cyl(x,y,-1,3.4,12)).cut(cyl(x,y,0,4.4,5))
quarter=quarter.intersect(box(75,75,0,150,150,112.5))
for x,y in((133.5,4),(141.5,4),(4,133.5),(4,141.5)):
    quarter=quarter.cut(cyl(x,y,100,3.4,14))
backer=box(0,0,0,18,18,8)
for x in(-4,4):
    for y in(-4,4):backer=backer.cut(cyl(x,y,-1,3.4,10)).cut(cyl(x,y,3,4.4,6))
parts={'39_open_funnel_stud_quarter_PRINT_4':quarter,'40_intake_rim_seam_backer_PRINT_4':backer}
base_tile=cq.importers.importStep(str(ROOT/'brick_layout_v4/24_top_cover_tile_PRINT_15.step'))
roof_replacements={}
seq=41
for tile_x in(-400,-200):
    for tile_y in(-500/3,0,500/3):
        name=f'{seq:02d}_intake_roof_tile_x{abs(tile_x)}_'+('rear'if tile_y<0 else 'center'if tile_y==0 else 'front')
        p=base_tile
        if tile_y==0:p=p.cut(cyl(-250-tile_x,0,-1,108,6))
        else:
            world_x=-250+(-foot if tile_x==-400 else foot)
            world_y=-foot if tile_y<0 else foot
            p=p.cut(cyl(world_x-tile_x,world_y-tile_y,-1,3.4,6))
        parts[name]=p;roof_replacements[(tile_x,round(tile_y,6))]=name;seq+=1
checks={}
for name,p in parts.items():
    p=p.clean();bb=p.val().BoundingBox();dims=[bb.xlen,bb.ylen,bb.zlen]
    assert p.val().isValid() and len(p.solids().vals())==1,name
    assert dims[0]+10<256 and dims[1]+10<256 and dims[2]<256,(name,dims)
    cq.exporters.export(p,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.12)
    cq.exporters.export(p,str(OUT/(name+'.step')))
    raw=(OUT/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',raw,80)[0];es=collections.Counter()
    for i in range(n):
        v=struct.unpack_from('<9f',raw,84+i*50+12);v=[tuple(round(t,4)for t in v[j:j+3])for j in(0,3,6)]
        for a,b in((0,1),(1,2),(2,0)):es[tuple(sorted((v[a],v[b])))]+=1
    assert all(v==2 for v in es.values()),(name,collections.Counter(es.values()))
    checks[name]={'count':4 if name.startswith(('39','40'))else 1,'dimensions_xyz':dims,'valid_single_solid':True,'watertight':True,'fits_P2S_with_5mm_brim':True,'sha256_stl':hashlib.sha256(raw).hexdigest()}
    print('Exported '+name,flush=True)
actors=[]
for a in old['actors']:
    if a['name'].startswith(('27_','30_')) and a['xyz'][0]<0:continue
    b=copy.deepcopy(a)
    if b['name'].startswith('24_'):
        key=(b['xyz'][0],round(b['xyz'][1],6))
        if key in roof_replacements:
            name=roof_replacements[key];b['name']=name;b['stl_file']='intake_stud_v6/'+name+'.stl';b['step_file']='intake_stud_v6/'+name+'.step';b['source']='intake'
    actors.append(b)
def add(name,xyz,rz=0):
    actors.append({'name':name,'xyz':list(xyz),'rx':0,'ry':0,'rz':rz,'color':[.83,.21,.15],'group':'intake','source':'intake','stl_file':'intake_stud_v6/'+name+'.stl','step_file':'intake_stud_v6/'+name+'.step'})
for yaw in(0,90,180,270):
    add('39_open_funnel_stud_quarter_PRINT_4',(-250,0,604),yaw)
    t=math.radians(yaw);add('40_intake_rim_seam_backer_PRINT_4',(-250+137.5*math.cos(t),137.5*math.sin(t),705.3),yaw)

# Verify a continuous geometric passage through the actual roof to the intake.
# Cone narrows to100ID atZ604;108 roof bore leaves0.8radial clearance around
# the106.4OD throat. The center80-diameter corridor is clear below/top.
refs=copy.deepcopy(old['reference_actors']);cache={}
def place(p,a,ext=0):
    for axis,key in(((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')):
        if a[key]:p=p.rotate((0,0,0),axis,a[key])
    x,y,z=a['xyz'];return p.translate((x,y+(ext if a.get('drawer_tier')==2 else 0),z))
for pose,ext in(('CLOSED',0),('UPPER_DRAWER_OPEN',350)):
    asm=cq.Assembly(name='BRICKED_V6_INTAKE_'+pose+'_LAYOUT_ONLY')
    for i,a in enumerate(actors+refs):
        path=a['step_file'];p=cache.get(path)
        if p is None:p=cq.importers.importStep(str(ROOT/path));cache[path]=p
        asm.add(place(p,a,ext),name=f'{i:03d}_'+a['name'])
    for ref in old['reference_volumes']:
        x,y,z=ref['center']
        if ref['kind']=='box':
            dx,dy,dz=ref['size'];p=box(x,y,z-dz/2,dx,dy,dz)
        else:p=cyl(x,y,z-ref['height']/2,ref['diameter'],ref['height'])
        asm.add(p,name='REF_'+ref['name'])
    cq.exporters.export(asm.toCompound(),str(OUT/('V6_'+pose+'_REFERENCE_ONLY.step')))
roof_and_intake=[]
for a in actors:
    if a['source']=='intake':roof_and_intake.append(place(cache[a['step_file']],a).val())
compound=cq.Compound.makeCompound(roof_and_intake)
passage=cyl(-250,0,599,80,119).val()
passage_obstruction=compound.intersect(passage).Volume()
assert passage_obstruction<.01,passage_obstruction
spec=copy.deepcopy(old)
spec['revision']='V6 functional loading stud 2026-10-29'
spec['actors']=actors
spec['effective_modeled_print_counts']=dict(collections.Counter(a['stl_file'] for a in actors))
spec['latest_intake']={
 'user_requirement':'One stud is a funnel/hole for loading LEGO.',
 'selected_side':'left stud in world-X sense,center(-250,0)',
 'type':'Open stud with integral tapered funnel quarters; opposite stud retained as cosmetic cap/service-lid concept.',
 'center_xy':[-250,0],'outer_diameter':300,'top_opening_diameter':260,'outlet_inside_diameter_provisional':100,'outlet_outside_diameter':106.4,'roof_through_hole_diameter':108,
 'bottom_z':604,'top_z':716.5,'height':112.5,'wall_radial_thickness':3.2,'rim_thickness':3.2,
 'funnel_slope_to_horizontal_deg':math.degrees(math.atan(112.5/80)),
 'inlet_workflow':['open loading stud','drum/tumbler','V1','V2','scanner hold/classify','position scoop','release','selected bin'],
 'quarter_join_hole_pattern':[8,8],'seam_backer_size':[18,18,8],'seam_backer_centers_radius':137.5,'seam_backer_bottom_z':705.3,
 'M3_insert_profile':{'OD':5,'L':4,'pilot':4.4,'pocket_depth':5},
 'M3_insert_counts':{'rim_backers':16,'roof_mount_feet':4,'total_new_intake':20},
 'rim_screw_start':'16xM3x8 through3.2rim to4.8 pocket depth; verify actual fit',
 'roof_mount_screw_start':'4xM3x8 through4roof into4mm insert engagement from underside',
 'mount_feet_centers_xy':[[-250+x,y]for x in(-foot,foot)for y in(-foot,foot)],
 'roof_tile_replacements':[{'center_xy':[k[0],k[1]],'part':v}for k,v in roof_replacements.items()],
 'reuse_notes':'Retain existing right stud,original lift,bin geometry,drawers,floor and other9 roof tiles. Left4 closed quarters and4 old cross-seam straps are omitted.6 roof tiles havecut/drill variants; already printed roofs may be modified using exact coordinates rather than reprinted.',
 'opposite_stud_retention_status':'Existing closed stud retained. Service-lid fastening and a corresponding access opening have not been finalized; do not claim completed removable service hatch.',
 'drum_connection_status':'Drum opening/position/transition not specified.100 outlet is a proposal. Do not print final funnel until actual drum interface and automatic piece envelope are established.',
 'prior_feeder_placeholders':'Previous V1/V2/scanner volumes are reservations,not resolved gravity-feed mechanisms. Rearrange them with the drum and this inlet before claiming full material-flow clearance.',
 'checks':{'new_printable_types':len(checks),'part_checks':checks,'center80_diameter_passage_through_intake_and_roof_obstruction_mm3':passage_obstruction,'continuous_passage_to_drum':False,'flow_tested':False,'two_box_hopper_capacity_tested':False},
 'recommendation_out_of_10':9,
}
(OUT/'intake_and_access_dimensions.json').write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps({'new_types':len(checks),'continuous_80mm_center_passage_obstruction':passage_obstruction,'opening':260,'throat_provisional':100},indent=2),flush=True)
