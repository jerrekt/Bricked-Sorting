"""Bricked Sorting open-scoop lift, V3 heat-set hardware. CadQuery 2.7."""
from pathlib import Path
import collections
import json
import math
import struct
import io
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

OUT = Path(__file__).resolve().parent / 'lego_carriage_v3_heatset'
OUT.mkdir(exist_ok=True)
SLOPE = 40.0
SN, CS = math.sin(math.radians(SLOPE)), math.cos(math.radians(SLOPE))
FLOOR, WALL_HEIGHT, FLARE = 3.2, 45.0, 6.0
MOTOR_Y, HUB_Z, ROD_SPACING = 90.0, 48.0, 90.0
REAR, NOSE = -55.0 / CS, 110.0 / CS
PLATE_LIMIT, BRIM = 256.0, 5.0
INSERTS = {
    'M2': {'outside_diameter':3.0, 'length':3.0, 'pilot':2.6, 'depth':4.0},
    'M3': {'outside_diameter':5.0, 'length':4.0, 'pilot':4.4, 'depth':5.0},
    'M4': {'outside_diameter':6.3, 'length':8.1, 'pilot':5.6, 'depth':9.1},
    'M5': {'outside_diameter':7.1, 'length':9.5, 'pilot':6.4, 'depth':10.5},
}

def box(x, y, z, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((x, y, z))

def cyl(x, y, z, r, h):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x, y, z))

def yhole(x, y, z, r, length):
    return cq.Workplane('XZ').center(x, z).circle(r).extrude(length, both=True).translate((0, y, 0))

def directed_cylinder(origin, direction, radius, length):
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius,length,cq.Vector(*origin),cq.Vector(*direction)))

def heat_hole(part, size, origin, direction, screw_run):
    profile=INSERTS[size]
    part=part.cut(directed_cylinder(origin,direction,profile['pilot']/2,profile['depth']))
    return part.cut(directed_cylinder(origin,direction,{'M2':1.1,'M3':1.7,'M4':2.2,'M5':2.7}[size],screw_run))

def rod_insert_boss(part, x, z):
    # Full 8.1 mm M4 insert plus 1 mm melt relief; the old collar alone
    # was too thin to contain this insert without reaching the steel rod.
    part=part.union(directed_cylinder((x,-25,z),(0,1,0),6,18))
    return heat_hole(part,'M4',(x,-25,z),(0,1,0),26)

def nema_holes(s, x, y, z, h):
    s = s.cut(cyl(x, y, z, 11.3, h))
    for a in [-15.5, 15.5]:
        for b in [-15.5, 15.5]:
            s = s.cut(cyl(x+a, y+b, z, 1.7, h))
    return s

base = box(0, 25, 0, 210, 210, 8)
for x in [-45, 45]:
    base = base.union(cyl(x, 0, 8, 13, 30)).cut(cyl(x, 0, 10, 6.15, 30))
    base = rod_insert_boss(base,x,25)
for x in [-29, 29]:
    for y in [-22, 22]:
        base = base.union(box(x, y, 8, 10, 12, 50))
base = nema_holes(base.union(box(0, 0, 58, 68, 58, 6)), 0, 0, 57, 9)
for x in [-8, 8]:
    base = heat_hole(base,'M3',(x,-40,0),(0,0,1),9)
for x in [-85, 85]:
    for y in [-60, 110]:
        base = base.union(cyl(x,y,8,7.5,5))
        base = heat_hole(base,'M5',(x,y,13),(0,0,-1),14)

shelf = box(0, 66, 40, 60, 108, 6).edges('|Z').fillet(12)
car = box(0, 0, 0, 118, 28, 40).union(shelf)
for x in [-27, 27]:
    rib = cq.Workplane('YZ').polyline([(8, 8), (8, 40), (119, 40)]).close().extrude(3, both=True).translate((x, 0, 0))
    car = car.union(rib)
for x in [-45, 45]:
    car = car.cut(cyl(x, 0, -1, 6.2, 43))
car = car.cut(cyl(0, 0, -1, 5.3, 43))
for x, y in [(8, 0), (-8, 0), (0, 8), (0, -8)]:
    car = car.cut(cyl(x, y, -1, 1.7, 43)).cut(cyl(x, y, 6, 3.2, 36))
car = nema_holes(car, 0, MOTOR_Y, 39, 10)
car = car.union(box(13.5, -26, 0, 10, 28, 6))
car = car.union(box(13.5, -20, 6, 8, 14, 34))
car = car.union(box(13.5, -26, 40, 10, 28, 6))

cap = box(0, 0, 0, 118, 28, 14)
for x in [-45, 45]:
    cap = cap.cut(cyl(x, 0, -1, 6.15, 17))
    cap = rod_insert_boss(cap,x,7)
cap = cap.cut(cyl(0, 0, -1, 5.5, 17))

lower_switch = box(0, -40, 0, 32, 22, 5).union(box(-3.75, -32, 5, 22.5, 4, 85))
for x in [-8, 8]:
    lower_switch = lower_switch.cut(cyl(x, -40, -1, 1.7, 8))
for x in [-4.75, 4.75]:
    slot = cq.Workplane('XZ').center(x, 75).slot2D(20, 2.6, 90).extrude(8, both=True).translate((0, -32, 0))
    lower_switch = lower_switch.cut(slot)

# A separately adjustable upper switch rides on the right rod. Its mounting
# plate ends at X=7.5, clear of the X=8.5..18.5 upper carriage trigger.
upper_switch = cyl(45, 0, 0, 13, 18).cut(cyl(45, 0, -1, 6.15, 21))
arm = cq.Workplane('XY').polyline([(35,-8),(52,-8),(52,-35),(-15,-35),(-15,-29),(35,-29)]).close().extrude(6)
upper_switch = upper_switch.union(arm).union(box(-3.75, -32, -40, 22.5, 4, 40))
upper_switch = rod_insert_boss(upper_switch,45,9)
for x in [-4.75, 4.75]:
    slot = cq.Workplane('XZ').center(x, -23).slot2D(20, 2.6, 90).extrude(8, both=True).translate((0, -32, 0))
    upper_switch = upper_switch.cut(slot)

# The scoop is exported in its PRINT orientation: a flat floor on the bed.
# Assembly rotates it -40 degrees about X; its four floor screws line up
# with the tilted face of a separate hub.
outline = [(-55,REAR),(55,REAR),(55,35/CS),(48,NOSE),(-48,NOSE),(-55,35/CS)]
wire = cq.Workplane('XY').polyline(outline).close().val()
def offset_wire(amount, z):
    w = wire if amount == 0 else cq.Workplane('XY').add(wire).toPending().offset2D(amount, kind='intersection').val()
    return w.translate(cq.Vector(0, 0, z))

outer = cq.Solid.makeLoft([offset_wire(0,0), offset_wire(FLARE,FLOOR+WALL_HEIGHT)], ruled=True)
inner = cq.Solid.makeLoft([offset_wire(-FLOOR,FLOOR), offset_wire(FLARE-FLOOR,FLOOR+WALL_HEIGHT+0.05)], ruled=True)
scoop = cq.Workplane(obj=outer.cut(inner))
# Fully open discharge: remove the last 4 mm of front wall above the floor.
scoop = scoop.cut(box(0, NOSE+48, FLOOR, 220, 104, 80))
for x in [-15, 15]:
    for y in [-12, 12]:
        scoop = scoop.cut(cyl(x, y, -1, 1.7, 8))
        csink = cq.Solid.makeCone(1.7, 3.2, 1.5, cq.Vector(x,y,FLOOR-1.5), cq.Vector(0,0,1))
        scoop = scoop.cut(cq.Workplane(obj=csink))

hub = cq.Workplane('YZ').polyline([(-23,0),(23,0),(23,32-math.tan(math.radians(SLOPE))*23),(-23,32+math.tan(math.radians(SLOPE))*23)]).close().extrude(23, both=True)
hub = hub.cut(cyl(0, 0, -1, 2.6, 22))
hub = heat_hole(hub,'M3',(0,-23,10),(0,1,0),25)
plane = cq.Plane(origin=(0,0,32), xDir=(1,0,0), normal=(0,SN,CS))
for x in [-15, 15]:
    for y in [-12, 12]:
        bore = cq.Workplane(plane).center(x,y).circle(1.7).extrude(-9)
        pocket = cq.Workplane(plane).center(x,y).circle(INSERTS['M3']['pilot']/2).extrude(-INSERTS['M3']['depth'])
        hub = hub.cut(bore).cut(pocket)

# M2 screws pass through switch, bracket slots and a sliding backing bar.
# The bar's heat-set inserts enter from the accessible front face, opposite
# the switch. This retains vertical adjustment without loose nuts.
switch_backer=box(0,-27,-3.5,17,6,7)
for x in [-4.75,4.75]:
    switch_backer=heat_hole(switch_backer,'M2',(x,-24,0),(0,-1,0),7)
switch_backer_print=switch_backer.rotate((0,0,0),(1,0,0),90)

# Optional feet attach from below to the four M5 inserts in the base.
foot=cyl(0,0,0,12,10).cut(cyl(0,0,-1,2.7,12)).cut(cyl(0,0,-1,4.75,6.5))
foot_print=foot.rotate((0,0,0),(1,0,0),180)

def insert_test(size):
    spec=INSERTS[size];result=None
    for i,delta in enumerate([-.2,-.1,0,.1,.2]):
        diameter=round(spec['pilot']+delta,2);x=i*25;h=spec['depth']+3
        vertical=box(x,0,0,22,22,h)
        vertical=vertical.cut(cyl(x,0,h-spec['depth'],diameter/2,spec['depth']+1))
        vertical=vertical.cut(cyl(x,0,-1,{'M2':1.1,'M3':1.7,'M4':2.2,'M5':2.7}[size],h+2))
        horizontal=box(x,32,0,22,22,14)
        horizontal=horizontal.cut(directed_cylinder((x,21,7),(0,1,0),diameter/2,spec['depth']))
        horizontal=horizontal.cut(directed_cylinder((x,20,7),(0,1,0),{'M2':1.1,'M3':1.7,'M4':2.2,'M5':2.7}[size],24))
        for k in range(i+1):
            vertical=vertical.union(box(x-8+k*3.5,-8,h,1.5,2,.6))
            horizontal=horizontal.union(box(x-8+k*3.5,39,14,1.5,2,.6))
        p=vertical.union(horizontal)
        result=p if result is None else result.union(p)
    return result

rod_test = None
for i, d in enumerate([12.2,12.3,12.4,12.5,12.6]):
    p = box(i*23,0,0,21,24,12).cut(cyl(i*23,0,-1,d/2,15))
    for k in range(i+1):
        p = p.union(box(i*23-8+k*3.5,-9,12,1.5,2,0.6))
    rod_test = p if rod_test is None else rod_test.union(p)
shaft_test = None
for i,d in enumerate([5.1,5.2,5.3]):
    p = box(i*19,0,0,17,20,8).cut(cyl(i*19,0,-1,d/2,11))
    for k in range(i+1):
        p = p.union(box(i*19-5+k*4,-7,8,1.5,2,0.6))
    shaft_test = p if shaft_test is None else shaft_test.union(p)

design = {
 '01_ground_base':base, '02_moving_carriage_v3':car, '03_top_rod_brace':cap,
 '04_lower_switch_mount':lower_switch, '05_open_scoop_PRINT_FLAT':scoop,
 '06_angled_shaft_hub':hub, '07_upper_switch_rod_mount':upper_switch,
 '08_rod_fit_test':rod_test, '09_shaft_fit_test':shaft_test,
 '10_M2_switch_backer_PRINT_TWICE':switch_backer_print,
 '11_M2_insert_fit_test':insert_test('M2'), '12_M3_insert_fit_test':insert_test('M3'),
 '13_M4_insert_fit_test':insert_test('M4'), '14_M5_insert_fit_test':insert_test('M5'),
 '15_optional_foot_PRINT_FOUR':foot_print,
}
checks = {}
for name, p in design.items():
    p = p.clean(); design[name] = p
    bb = p.val().BoundingBox()
    # Normalize each printable file onto the bed without changing X/Y axes.
    printable = p.translate((0,0,-bb.zmin))
    expected = 5 if name.startswith('08') else 3 if name.startswith('09') else 10 if name.startswith(('11','12','13','14')) else 1
    assert p.val().isValid() and len(p.solids().vals()) == expected, name
    dims = [bb.xlen,bb.ylen,bb.zlen]
    assert max(dims) < PLATE_LIMIT and bb.xlen+2*BRIM < PLATE_LIMIT and bb.ylen+2*BRIM < PLATE_LIMIT, (name,dims)
    cq.exporters.export(printable, str(OUT/(name+'.stl')), tolerance=.05, angularTolerance=.12)
    cq.exporters.export(printable, str(OUT/(name+'.step')))
    checks[name] = {'dimensions_mm':[round(d,2) for d in dims], 'valid_solid':True, 'solid_count':expected,
                    'fits_256mm_bed_with_5mm_brim':True, 'material_volume_cm3':round(p.val().Volume()/1000,2)}

def assembled_scoop(z, yaw=0):
    return scoop.rotate((0,0,0),(1,0,0),-SLOPE).translate((0,0,32)).rotate((0,0,0),(0,0,1),yaw).translate((0,MOTOR_Y,z+HUB_Z))
def assembled_hub(z, yaw=0):
    return hub.rotate((0,0,0),(0,0,1),yaw).translate((0,MOTOR_Y,z+HUB_Z))

rods = [cyl(x,0,10,6,350) for x in [-45,45]]
lead = cyl(0,0,60,4,310)
lift_motor = box(0,0,10.7,42.3,42.3,47.3)
upper_mount_z = 281.0
fixed = {'base':base, 'top_brace':cap.translate((0,0,342)), 'lower_switch_mount':lower_switch.translate((0,0,8)),
         'upper_switch_mount':upper_switch.translate((0,0,upper_mount_z)),
         'lower_switch_backer':switch_backer.translate((0,0,83)),
         'upper_switch_backer':switch_backer.translate((0,0,upper_mount_z-23)),
         'left_rod':rods[0], 'right_rod':rods[1], 'lead_screw':lead, 'lift_motor':lift_motor}
def common_volume(a,b):
    ab,bb=a.val().BoundingBox(),b.val().BoundingBox()
    if ab.xmax<bb.xmin or ab.xmin>bb.xmax or ab.ymax<bb.ymin or ab.ymin>bb.ymax or ab.zmax<bb.zmin or ab.zmin>bb.zmax:
        return 0.0
    return a.val().intersect(b.val()).Volume()

collisions = []
sampled = 0
for z in [95,145,195,200]:
    moving_motor = box(0,MOTOR_Y,z-8,42,42,48)
    moving_car = car.translate((0,0,z))
    for yaw in range(-90,91,15):
        sampled += 1
        for mn,moving in [('scoop',assembled_scoop(z,yaw)),('hub',assembled_hub(z,yaw))]:
            for fn,stationary in {**fixed,'carriage':moving_car,'rotating_motor':moving_motor}.items():
                v=common_volume(moving,stationary)
                if v>0.01: collisions.append({'z':z,'yaw':yaw,'moving':mn,'fixed':fn,'volume_mm3':round(v,3)})
    for fn,stationary in fixed.items():
        v=common_volume(moving_car,stationary)
        if v>0.01: collisions.append({'z':z,'moving':'carriage','fixed':fn,'volume_mm3':round(v,3)})

relative_clearances=[]
for yaw in range(-90,91,5):
    moving=assembled_scoop(95,yaw).val()
    stationary=car.translate((0,0,95)).val()
    distance=moving.distance(stationary)
    relative_clearances.append(distance)
    if distance<1.0:
        collisions.append({'yaw':yaw,'moving':'scoop','fixed':'carriage','clearance_mm':round(distance,3)})

# Binary STL edge incidence catches holes/nonmanifold seams in the exports.
for name in design:
    raw=(OUT/(name+'.stl')).read_bytes(); count=struct.unpack_from('<I',raw,80)[0]; edges=collections.Counter()
    for i in range(count):
        values=struct.unpack_from('<9f',raw,84+i*50+12)
        v=[tuple(round(t,4) for t in values[j:j+3]) for j in (0,3,6)]
        for a,b in [(0,1),(1,2),(2,0)]: edges[tuple(sorted((v[a],v[b])))]+=1
    assert all(n==2 for n in edges.values()),name
    checks[name]['watertight_mesh']=True
checks['motion_check']={'sampled_poses':sampled,'heights_mm':[95,145,195,200],'yaw_degrees':[-90,90],
                        'collisions':collisions,'scoop_carriage_clearance_37_angles_mm':round(min(relative_clearances),3),
                        'note':'Sampled solid intersections only; not continuous clearance or physical testing. Switch levers, fasteners and cables not included.'}
(OUT/'geometry_checks.json').write_text(json.dumps(checks,indent=2))
(OUT/'insert_profiles.json').write_text(json.dumps(INSERTS,indent=2))
print(json.dumps(checks,indent=2),flush=True)

def render_scene(ax, scene, bounds, elev, azim):
    faces, colors = [], []
    light=np.array([-.4,-.5,.85]); light/=np.linalg.norm(light)
    for p,color in scene:
        verts,tris=p.val().tessellate(.3,.15)
        verts=np.array([v.toTuple() for v in verts]); rgb=np.array(to_rgb(color))
        for f in tris:
            tri=verts[list(f)]; n=np.cross(tri[1]-tri[0],tri[2]-tri[0]); n/=max(np.linalg.norm(n),1e-12)
            shade=.67+.33*max(0,np.dot(n,light))
            faces.append(tri);colors.append(rgb*shade)
    ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,edgecolors='none',zsort='average'))
    ax.set(xlim=bounds[0],ylim=bounds[1],zlim=bounds[2]);ax.set_box_aspect([b[1]-b[0] for b in bounds]);ax.view_init(elev,azim)
    ax.set_proj_type('ortho');ax.set_axis_off()
    ax.set_facecolor('#f6f7f8')

fig=plt.figure(figsize=(14,8),facecolor='#f6f7f8')
ax=fig.add_axes([0,.07,.65,.82],projection='3d')
motor_preview=box(0,0,-56,42,42,48).union(cyl(0,0,-8,2.5,24))
sc=scoop.rotate((0,0,0),(1,0,0),-SLOPE).translate((0,0,32))
render_scene(ax,[(sc,'#20a3aa'),(hub,'#e89a39'),(motor_preview,'#353b44')],[(-85,85),(-85,165),(-85,155)],35,55)
fig.text(.05,.93,'OPEN SCOOP · V3',size=23,weight='bold',color='#202b38')
fig.text(.05,.885,'40° ramp  /  flared catch area  /  flush floor screws',size=12,color='#4e5d6c')
fig.text(.05,.06,'Separate shaft hub bolts to the scoop. LEGO follows the open ramp above the motor.',size=11,color='#4e5d6c')
bedax=fig.add_axes([.68,.27,.29,.54]);bedax.set_aspect('equal')
bedax.add_patch(plt.Rectangle((-128,-128),256,256,facecolor='#e5e9ed',edgecolor='#647383'))
bb=scoop.val().BoundingBox();cx=(bb.xmin+bb.xmax)/2;cy=(bb.ymin+bb.ymax)/2
bedax.add_patch(plt.Rectangle((bb.xmin-cx-5,bb.ymin-cy-5),bb.xlen+10,bb.ylen+10,facecolor='#b9dfde',edgecolor='none'))
pts=np.array(outline);pts[:,1]-=cy
bedax.fill(pts[:,0],pts[:,1],facecolor='#20a3aa',alpha=.65)
bedax.add_patch(plt.Rectangle((bb.xmin-cx,bb.ymin-cy),bb.xlen,bb.ylen,fill=False,edgecolor='#126b73',linewidth=1))
bedax.set(xlim=(-141,141),ylim=(-141,141));bedax.set_axis_off()
bedax.set_title('P2S · 256 × 256 mm',fontsize=13,color='#202b38',pad=12)
fig.text(.69,.22,f'Print footprint: {bb.xlen:.1f} × {bb.ylen:.1f} mm',size=12,color='#202b38')
fig.text(.69,.18,f'Height: {bb.zlen:.1f} mm · 5 mm brim shown',size=11,color='#4e5d6c')
image_bytes=io.BytesIO()
fig.savefig(image_bytes,format='png',dpi=170,facecolor=fig.get_facecolor())
(OUT/'open_scoop_preview.png').write_bytes(image_bytes.getvalue());plt.close(fig)

fig=plt.figure(figsize=(10,11),facecolor='#f6f7f8');ax=fig.add_axes([0,0,1,.9],projection='3d')
scene=[(p,'#85929e') for p in fixed.values()]
scene += [(car.translate((0,0,110)),'#e89a39'),(box(0,MOTOR_Y,102,42,42,48),'#353b44'),
          (assembled_hub(110),'#e89a39'),(assembled_scoop(110),'#20a3aa')]
render_scene(ax,scene,[(-115,115),(-85,235),(0,385)],22,-60)
fig.text(.06,.95,'BRICKED SORTING · OPEN-SCOOP LIFT',size=18,weight='bold',color='#202b38')
fig.text(.06,.91,'90 mm rod spacing · motor axis moved forward to Y=90 mm',size=11,color='#4e5d6c')
image_bytes=io.BytesIO()
fig.savefig(image_bytes,format='png',dpi=150,facecolor=fig.get_facecolor())
(OUT/'assembly_preview.png').write_bytes(image_bytes.getvalue());plt.close(fig)

# Exchange assembly: STEP includes reference rods and motor bodies; do not print it.
assembly=cq.Assembly(name='BrickedSorting_OpenScoop_V3_HeatSet')
for name,p in fixed.items():assembly.add(p,name=name)
assembly.add(car.translate((0,0,110)),name='moving_carriage')
assembly.add(assembled_hub(110),name='shaft_hub')
assembly.add(assembled_scoop(110),name='open_scoop')
cq.exporters.export(assembly.toCompound(),str(OUT/'ASSEMBLY_REFERENCE_ONLY.step'))
if collisions:
    raise RuntimeError(f'{len(collisions)} sampled collisions; inspect geometry_checks.json')
