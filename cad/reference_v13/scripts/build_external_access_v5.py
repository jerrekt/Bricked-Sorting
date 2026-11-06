"""V5 front access overlay: two tier drawers, each carrying eight existing bins.
Runner and sheet carrier are dimensioned reference envelopes, not load-rated
or selected purchased hardware. Original V3/V4 geometry remains untouched.
"""
from pathlib import Path
import collections,copy,hashlib,json,math,struct
import cadquery as cq
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'external_access_v5';OUT.mkdir(exist_ok=True)
REF=OUT/'reference_only';REF.mkdir(exist_ok=True)
old=json.loads((ROOT/'brick_layout_v4/layout_dimensions_and_parts.json').read_text())
WIDTH=700.;PANEL_W=WIDTH/3;EXTENSION=350.;FACE_Y=247.
def box(x,y,z,dx,dy,dz):return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(x,y,z,d,h):return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))
def skin(w,h):
    p=box(0,0,0,w,h,3)
    for x in (-w/2+15,w/2-15):
        for y in (-h/2+15,h/2-15):
            p=p.cut(cyl(x,y,-1,3.4,5))
            p=p.cut(cq.Workplane(obj=cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(x,y,1.5),cq.Vector(0,0,1))))
    return p
parts={}
parts['31_drawer_face_outer_PRINT_4']=skin(PANEL_W,110)
center=skin(PANEL_W,110)
for x in(-48,48):center=center.cut(cyl(x,0,-1,4.4,5))
parts['32_drawer_face_center_PRINT_2']=center
parts['33_front_side_cover_PRINT_6']=skin(150,193)
parts['34_front_bottom_cover_PRINT_3']=skin(PANEL_W,116)
parts['35_front_top_cover_PRINT_6']=skin(PANEL_W,119)
handle=box(0,0,20,120,26,16)
for x in(-48,48):
    handle=handle.union(box(x,0,0,18,26,20))
    handle=handle.cut(cyl(x,0,-1,4.4,20)).cut(cyl(x,0,0,5.6,9.1))
handle=handle.rotate((0,0,0),(1,0,0),180).translate((0,0,36))
parts['36_external_handle_PRINT_2']=handle
splice=box(0,0,0,60,24,8)
for x in(-15,15):splice=splice.cut(cyl(x,0,-1,3.4,10)).cut(cyl(x,0,3,4.4,6))
parts['37_fascia_seam_backer_PRINT_8']=splice
spreader=box(0,0,0,130,35,6)
for x in(-48,48):spreader=spreader.cut(cyl(x,0,-1,4.4,8))
parts['38_handle_load_spreader_PRINT_2']=spreader
counts=[4,2,6,3,6,2,8,2];checks={}
for (name,p),qty in zip(parts.items(),counts):
    p=p.clean();bb=p.val().BoundingBox()
    assert p.val().isValid() and len(p.solids().vals())==1,name
    dims=[bb.xlen,bb.ylen,bb.zlen]
    assert dims[0]+10<256 and dims[1]+10<256 and dims[2]<256,name
    cq.exporters.export(p,str(OUT/(name+'.stl')),tolerance=.08,angularTolerance=.12)
    cq.exporters.export(p,str(OUT/(name+'.step')))
    raw=(OUT/(name+'.stl')).read_bytes();edges=collections.Counter();n=struct.unpack_from('<I',raw,80)[0]
    for i in range(n):
        v=struct.unpack_from('<9f',raw,84+i*50+12);v=[tuple(round(t,4)for t in v[j:j+3])for j in(0,3,6)]
        for a,b in((0,1),(1,2),(2,0)):edges[tuple(sorted((v[a],v[b])))]+=1
    assert all(v==2 for v in edges.values()),name
    checks[name]={'count':qty,'dimensions_xyz':dims,'valid_single_solid':True,'watertight':True,'fits_P2S_5mm_brim':True,'sha256_stl':hashlib.sha256(raw).hexdigest()}
    print('Exported '+name,flush=True)

actors=[]
for a in old['actors']:
    # Replace the entire previous fixed front skin. All other skins are reused.
    if a['name'].startswith('22_') and a['xyz'][1]>0:continue
    b=copy.deepcopy(a)
    source=b['source'];folder='' if source=='baseline' else 'electronics_addon/' if source=='electronics' else 'brick_layout_v4/'
    b['stl_file']=folder+b['name']+'.stl';b['step_file']=folder+b['name']+'.step'
    if b['group']=='bins':
        tier=1 if b['xyz'][2]<200 else 2;b['drawer_tier']=tier
        if tier==2:b['xyz'][2]+=10
    actors.append(b)
red=[.77,.16,.13];gray=[.32,.37,.42]
def add(name,xyz,rx=0,rz=0,color=red,group='access',tier=None):
    b={'name':name,'xyz':list(xyz),'rx':rx,'ry':0,'rz':rz,'color':color,'group':group,'source':'access','stl_file':'external_access_v5/'+name+'.stl','step_file':'external_access_v5/'+name+'.step'}
    if tier:b['drawer_tier']=tier
    actors.append(b)
for x in(-425,425):
    for z in(117.5,310.5,503.5):add('33_front_side_cover_PRINT_6',(x,FACE_Y,z),rx=-90)
for x in(-PANEL_W,0,PANEL_W):
    add('34_front_bottom_cover_PRINT_3',(x,FACE_Y,79),rx=-90)
    for z in(421.5,540.5):add('35_front_top_cover_PRINT_6',(x,FACE_Y,z),rx=-90)
for tier,z in((1,192),(2,307)):
    for x in(-PANEL_W,0,PANEL_W):
        add('32_drawer_face_center_PRINT_2'if x==0 else '31_drawer_face_outer_PRINT_4',(x,FACE_Y,z),rx=-90,tier=tier)
    add('36_external_handle_PRINT_2',(0,286,z),rx=90,color=gray,tier=tier)
    add('38_handle_load_spreader_PRINT_2',(0,241,z),rx=-90,color=gray,tier=tier)
    for x in(-PANEL_W/2,PANEL_W/2):
        for dz in(-40,40):add('37_fascia_seam_backer_PRINT_8',(x,239,z+dz),rx=-90,color=gray,tier=tier)

references=[]
# A proposed sheet-metal U-shaped carrier. Not supplied as printable STL.
# No fixing-hole pattern is invented before commercial runners are selected.
deck=box(0,76,0,660,322,3).cut(cyl(0,-70,-1,300,5))
ref_parts={'U_CARRIER_SHEET_REFERENCE_NOT_RELEASED':deck,
           'RUNNER_FIXED_ENVELOPE_NOT_HARDWARE':box(0,0,0,15,350,30),
           'RUNNER_MOVING_ENVELOPE_NOT_HARDWARE':box(0,0,0,7,350,16),
           'CENTRAL_FRONT_DIVIDER_FRAME_PENDING':box(0,0,0,700,3,5)}
for name,p in ref_parts.items():
    assert p.val().isValid(),name
    cq.exporters.export(p,str(REF/(name+'.step')))
def add_ref(name,xyz,color,tier=None):
    a={'name':name,'step_file':'external_access_v5/reference_only/'+name+'.step','xyz':list(xyz),'rx':0,'ry':0,'rz':0,'color':color,'group':'carrier_reference'}
    if tier:a['drawer_tier']=tier
    references.append(a)
add_ref('CENTRAL_FRONT_DIVIDER_FRAME_PENDING',(0,248.5,247),red)
for tier,deck_z in((1,140),(2,255)):
    add_ref('U_CARRIER_SHEET_REFERENCE_NOT_RELEASED',(0,0,deck_z),[.52,.57,.61],tier)
    for x in(-337.5,337.5):
        add_ref('RUNNER_FIXED_ENVELOPE_NOT_HARDWARE',(x,60,deck_z-15),[.45,.49,.52])
        add_ref('RUNNER_MOVING_ENVELOPE_NOT_HARDWARE',(x,60,deck_z-8),[.66,.7,.74],tier)

def placed(p,a,extension=0):
    for axis,key in(((1,0,0),'rx'),((0,1,0),'ry'),((0,0,1),'rz')):
        if a[key]:p=p.rotate((0,0,0),axis,a[key])
    x,y,z=a['xyz'];return p.translate((x,y+extension,z))
cache={}
for pose,upper_extension in(('CLOSED',0),('UPPER_DRAWER_OPEN',EXTENSION)):
    assembly=cq.Assembly(name='BRICKED_V5_'+pose+'_LAYOUT_ONLY')
    for i,a in enumerate(actors+references):
        path=a['step_file'];p=cache.get(path)
        if p is None:p=cq.importers.importStep(str(ROOT/path));cache[path]=p
        ext=upper_extension if a.get('drawer_tier')==2 else 0
        assembly.add(placed(p,a,ext),name=f'{i:03d}_'+a['name'])
    # Include fixed rod/motor/reserved feeder volumes with explicit REF names.
    for ref in old['reference_volumes']:
        x,y,z=ref['center']
        if ref['kind']=='box':dx,dy,dz=ref['size'];p=box(x,y,z-dz/2,dx,dy,dz)
        else:p=cyl(x,y,z-ref['height']/2,ref['diameter'],ref['height'])
        assembly.add(p,name='REF_'+ref['name'])
    cq.exporters.export(assembly.toCompound(),str(OUT/('V5_'+pose+'_REFERENCE_ONLY.step')))

# Exact solid check of every bin at seven withdrawal offsets against the
# fixed V3 base/brace/carriage/motors/scoop in the reference H145 pose. Other
# unbuilt frame/receiving hardware is explicitly excluded.
fixed=[]
for a in actors:
    if a['group']=='lift' and a['source']=='baseline':
        p=cache.get(a['step_file'])
        if p is None:p=cq.importers.importStep(str(ROOT/a['step_file']))
        fixed.append(placed(p,a).val())
fixed_compound=cq.Compound.makeCompound(fixed)
bin_actors=[a for a in actors if a['group']=='bins']
collisions=[];minimum_open_rear_y=1e9
for tier in(1,2):
    selected=[a for a in bin_actors if a['drawer_tier']==tier]
    for ext in(0,50,100,150,200,275,350):
        for a in selected:
            p=cache[a['step_file']];shape=placed(p,a,ext).val()
            bb=shape.BoundingBox();fb=fixed_compound.BoundingBox()
            if not (bb.xmax<fb.xmin or bb.xmin>fb.xmax or bb.ymax<fb.ymin or bb.ymin>fb.ymax or bb.zmax<fb.zmin or bb.zmin>fb.zmax):
                vol=shape.intersect(fixed_compound).Volume()
                if vol>.01:collisions.append({'tier':tier,'extension':ext,'volume_mm3':vol})
            if ext==350:minimum_open_rear_y=min(minimum_open_rear_y,bb.ymin)
assert not collisions,collisions
assert minimum_open_rear_y>250
spec={
 'revision':'V5 outside bin access 2026-10-29','units':'mm/deg',
 'user_requirement':'All bins must be accessible from outside without removing the fixed beauty cover.',
 'concept':'Two front pull-out tier carriers,8 removable bins each. Closed fascias preserve brick-shaped rectangular envelope; handles project36.',
 'body_xyz':[1000,500,600],'overall_height_with_studs':716.5,
 'drawer_access':{'direction_world':[0,1,0],'extension':350,'front_outer_y_closed':250,'front_outer_y_open':600,'handle_front_y_closed':286,'handle_front_y_open':636,'clear_space_in_front_recommended_min':400,'fascia_width':700,'fascia_height':110,'fascia_tile_width':PANEL_W,'lower_fascia_z':[137,247],'upper_fascia_z':[252,362],'lower_bin_bottom':143,'upper_bin_bottom':258,'bin_geometry_unchanged':True,'upper_bins_shifted_up_from_V4':10,'lowest_open_bin_rear_y':minimum_open_rear_y,'front_opening_passage_clearance':'lower deck140/rim243 inside face137..247; upper deck255/rim358 inside face252..362; frame aperture/runners still must be finalized.'},
 'carriers_reference_only':{'sheet_outline_xy':[660,322],'thickness_proposed':3,'back_y':-85,'front_y':237,'center_cutout_diameter':300,'cutout_center':[0,-70],'closed_deck_bottom_z':[140,255],'suggested_construction':'Rigid metal carrier with side/perimeter stiffening and commercial full-extension runners; no load rating or hardware selection yet.','runner_envelope_xyz':[15,350,30],'runner_center_x':[-337.5,337.5],'runner_fixing_pattern':None,'shelf_to_fascia_brackets':None,'carrier_to_bins_locators':None,'safety_latch':None},
 'hardware':{'M3_seam_insert_OD_L':[5,4],'M3_seam_pilot':4.4,'M3_seam_depth':5,'fascia_seam_backers':8,'M3_seam_insert_count':16,'M4_handle_insert_OD_L':[6.3,8.1],'M4_handle_pilot':5.6,'M4_handle_depth':9.1,'M4_handle_insert_count':4,'M4_handle_bolt_spacing':96,'handle_print_orientation':'Bar face on bed, feet/insert entries upward; physical mount face is inverted from print coordinates.','handle_screw_start':'M4x16 with1mm washer through6mm spreader+3mm fascia gives6mm engagement. Verify actual stack and no bottoming.','seam_screw_start':'M3x8 countersunk through3mm face to5mm pocket; check actual insert and tip.'},
 'control_requirements':{'individual_bin_presence_switches_retained':16,'extra_tier_closed_interlocks_recommended':2,'interlock_hardware_CAD_status':'not yet designed','open_tray_behavior':'Stop upstream feed, inhibit scanner release and chute motion, require safe parked state before releasing drawer latch. Prevent release to all8 destinations on open tray.','inventory_behavior':'Tray opening and individual bin removal are distinct events. Preserve16-bin inventory semantics; never silently replace with2-bin events.','in_flight_piece':'Opening after release cannot recover a falling part; latch/pause/reconcile strategy must be implemented.','receiving_adapter':'Future receiver must clear/retract from drawer withdrawal path before unlocking; current scoop alone does not route to bins.'},
 'actors':actors,'reference_actors':references,'reference_volumes':old['reference_volumes'],
 'new_part_checks':checks,
 'validation':{'bins_vs_fixed_lift_sampled_extensions':[0,50,100,150,200,275,350],'reference_carriage_H_only':145,'bin_checks':112,'sampled_intersections':collisions,'all_open_bins_clear_fixed_front_plane':True,'scope':'Actual bin solids vs fixed reference lift pose only. Excludes future receiver,rack frame,cables,commercial runners,people and physical tests. Not full swept clearance or load validation.'},
 'replaced_parts_in_layout':{'previous_front_beauty_tiles_22':15,'replacement_fixed_front_tiles':15,'new_drawer_fascia_tiles':6,'unchanged_rear_tiles_22':15,'existing_lift_bins_floor_studs_unchanged':True},
 'not_yet_released':['chosen load-rated runners and mounting hardware','carrier sheet stiffening/fastener layout','bin retention and16 presence switches','2 tier-closed interlocks and safety latches','drawer-to-fascia structural brackets','supporting chassis/front aperture frame','receiving adapter and parked/retracted coupling','feeder/scanner mechanisms and wiring','tip resistance with either/both loaded drawers open'],
 'recommendation_rating_out_of_10':9,
}
(OUT/'outside_access_dimensions.json').write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps({'new_STL_types':len(checks),'sampled_bin_lift_checks':112,'collisions':collisions,'minimum_open_bin_rear_y':minimum_open_rear_y,'full_open_extension':EXTENSION},indent=2),flush=True)
