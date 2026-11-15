"""Additive electronics layout panel. CadQuery 2.7; dimensions from user images.

PSU mounting holes are UNKNOWN. This panel provides adapter slots, not a
finished PSU attachment or electrical enclosure. Existing lift files untouched.
"""
from pathlib import Path
import collections
import hashlib
import json
import struct
import cadquery as cq

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'electronics_addon'
OUT.mkdir(exist_ok=True)
def box(x,y,z,dx,dy,dz):
    return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(x,y,z,d,h):
    return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))

psu_size=[5.59*25.4,1.1*25.4,1.57*25.4]
panel=box(0,0,0,200,130,5).edges('|Z').fillet(4)
frame_xy=[(x,y) for x in (-88,88) for y in (-53,53)]
for x,y in frame_xy:
    panel=panel.union(cyl(x,y,5,16,8))
    panel=panel.cut(cyl(x,y,-1,5.4,15)).cut(cyl(x,y,2.5,6.4,11.5))
# Buck mounting boss center spacing40 from the photo, not its body length34.
for x in (-20,20):
    panel=panel.union(cyl(x,33,5,10,8))
    panel=panel.cut(cyl(x,33,-1,3.4,15)).cut(cyl(x,33,8,4.4,6))
# Slots are NEW adapter interfaces, not a guessed PSU screw-hole pattern.
for x in (-55,55):
    for y in (-48,-2):
        slot=cq.Workplane('XY').center(x,y).slot2D(34,4.4,0).extrude(7).translate((0,0,-1))
        panel=panel.cut(slot)
panel=panel.clean()
assert panel.val().isValid() and len(panel.solids().vals())==1
bb=panel.val().BoundingBox()
assert bb.xlen+10<256 and bb.ylen+10<256 and bb.zlen<256
name='16_electronics_layout_panel'
cq.exporters.export(panel,str(OUT/(name+'.stl')),tolerance=.05,angularTolerance=.12)
cq.exporters.export(panel,str(OUT/(name+'.step')))

# Reference-only blocks: labels in the preview make their limitations explicit.
psu=box(0,-25,13,*psu_size)
buck_body=box(0,33,13,34,25,21)
buck_flange=box(0,33,13,51,25,2)
for x in (-20,20):
    buck_flange=buck_flange.cut(cyl(x,33,12,4,4))
buck=buck_body.union(buck_flange)
assembly=cq.Assembly(name='Electronics_Layout_REFERENCE_ONLY')
assembly.add(panel,name='printable_panel')
assembly.add(psu,name='PSU_RESERVED_ENVELOPE_NOT_MOUNTED')
assembly.add(buck,name='BUCK_APPROX_ENVELOPE_EAR_THICKNESS_UNKNOWN')
cq.exporters.export(assembly.toCompound(),str(OUT/'ELECTRONICS_LAYOUT_REFERENCE_ONLY.step'))

raw=(OUT/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
edges=collections.Counter()
for i in range(n):
    values=struct.unpack_from('<9f',raw,84+i*50+12)
    pts=[tuple(round(v,4) for v in values[j:j+3]) for j in (0,3,6)]
    for a,b in ((0,1),(1,2),(2,0)):
        edges[tuple(sorted((pts[a],pts[b])))]+=1
assert all(v==2 for v in edges.values())
spec={
  'revision':'V3 additive electronics layout 2026-10-29',
  'status':'Buck mounting geometry provided; PSU adapter/guard/frame attachment not yet completed.',
  'units':'mm',
  'coordinate_system':'Independent electronics-local frame; not positioned in full machine. X along PSU length, Y across panel, Z up from panel underside.',
  'source_images':[
    {'file':'../handoff_references/stepdown_dimensions_user.png','sha256':hashlib.sha256((ROOT/'handoff_references/stepdown_dimensions_user.png').read_bytes()).hexdigest()},
    {'file':'../handoff_references/psu_dimensions_user.png','sha256':hashlib.sha256((ROOT/'handoff_references/psu_dimensions_user.png').read_bytes()).hexdigest()},
  ],
  'psu':{
    'label':'S-120-12; generic label, manufacturer not established',
    'label_ratings':{'ac_input_label':'100-250 V','dc_output_v':12,'dc_output_a':10,'power_w':120},
    'photo_dimensions_inches_LWH':[5.59,1.1,1.57],
    'converted_mm_LWH':psu_size,
    'dimension_status':'Converted from rounded image dimensions; confirm actual caliper dimensions and whether tabs/terminals are included.',
    'reference_bottom_xyz':[0,-25,13],
    'mounting_hole_pattern':None,'mounting_tab_thickness':None,'permitted_screw_penetration':None,
    'body_orientation_status':'Uses pictured orientation:1.57in tall,1.1in wide. Confirm intended installation orientation.',
    'retention':'Not designed. Reserved envelope is elevated13 above panel datum; actual spacers/brackets still required.',
  },
  'stepdown':{
    'label':'DROK 12 V to 5 V; 3 A max;15 W',
    'body_length':34,'overall_length_with_tabs':51,'width':25,'height':21,
    'mount_center_spacing':40,'ear_slot_nominal_width':4,
    'dimensions_status':'As labeled in user image; ear thickness and complete wire envelope unknown.',
    'center_xy':[0,33],'support_plane_z':13,'mount_xy':[[-20,33],[20,33]],
    'attachment':'Two M3 screws and washers into M3 OD5/L4 inserts; screw length selected after measuring ear+washer stack.',
    'screw_length_rule':'Length = actual ear thickness + washer thickness + desired insert engagement. Verify tip does not bottom or project below intended support.',
    'wire_colors_from_label':{'input_positive':'red','input_negative':'black','output_positive':'yellow','output_negative':'black'},
  },
  'panel':{
    'print_file':name+'.stl','size_xyz':[200,130,13],'base_thickness':5,'corner_radius':4,
    'M3_buck_bosses':{'xy':[[-20,33],[20,33]],'od':10,'top_z':13,'insert_entry_z':13,'pilot_diameter':4.4,'pilot_depth':5,'clearance_diameter':3.4},
    'M5_frame_bosses':{'xy':frame_xy,'od':16,'top_z':13,'pilot_diameter':6.4,'pilot_depth':10.5,'clearance_diameter':5.4,'frame_pattern_xy':[176,106],'entry_direction':[0,0,-1]},
    'PSU_future_adapter_slots':{'centers_xy':[[x,y] for x in (-55,55) for y in (-48,-2)],'overall_length':34,'width':4.4,'axis':'X','purpose':'M4 screws through new future brackets into matching insert backing pieces; NOT a PSU hole pattern'},
    'insert_counts':{'M3_OD5_L4':2,'M5_OD7_1_L9_5':4},
    'approx_body_gap_y':(33-12.5)-(-25+psu_size[1]/2),
    'reserved_service_area':'Keep both PSU ends clear beyond x=+/-71 approx; extra terminal/cord allowance and guard dimensions TBD. Converter wires leave along X at y33.',
    'placement':'Stationary electronics area, outside LEGO path and isolated from feeder vibration; full-machine transform TBD.',
  },
  'validation':{'valid_single_solid':True,'watertight_mesh':True,'dimensions_mm':[bb.xlen,bb.ylen,bb.zlen],'fits_256mm_with_5mm_brim':True,'triangles':n,'physical_fit_tested':False,'PSU_mount_complete':False,'full_machine_collision_checked':False},
  'print_guidance':'Flat underside down. Test insert fits first. Check PETG temperature suitability against actual component temperatures. Do not print final full panel until PSU adapter layout is confirmed if avoiding reprints is the priority.',
  'electrical_integration_pending':['Verify actual PSU ratings and output','12V and5V load budget including motor startup/stall','driver/MCU/servo mounting dimensions','branch protection and wire sizes','AC terminal guard and strain relief','protective-earth connection as required by actual supply; printed mount is not an earth path','cooling and physical access'],
}
(OUT/'electronics_dimensions.json').write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps(spec['validation'],indent=2))
