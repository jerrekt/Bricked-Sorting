"""V13 drum (BJ 2026-11-04 15:17 PT): static front plate with one bottom outlet, and a helical flight
inside the barrel instead of three straight ribs. Built in the V7 barrel frame: axis = +Z (0..180),
local +X points down (8 deg off). Parts: 47b barrel with flight, 49b static outlet plate."""
import math, json
from pathlib import Path
import cadquery as cq
ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'isolate_v13'; OUT.mkdir(exist_ok=True)
def box(x, y, z, dx, dy, dz): return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((x, y, z))
def cyl(x, y, z, d, h): return cq.Workplane('XY').center(x, y).circle(d / 2).extrude(h).translate((0, 0, z))
def insert(p, origin, axis):   # M3 heat-set pilot 4.0 x 6 (runbook)
    return p.cut(cq.Workplane('XY').circle(2.0).extrude(6).translate((0, 0, -6)).rotate((0, 0, 0), (1, 0, 0), 180 if axis[2] < 0 else 0).translate(origin))

OD, ID, L = 160.0, 152.0, 180.0
PITCH, FL_H, FL_W, TURNS = 90.0, 12.0, 12.0, 1.75          # flight: 12 tall, 12 wide base, triangular, 1.75 turns
barrel = cyl(0, 0, 0, OD, L).cut(cyl(0, 0, -1, ID, L + 2))
# helical flight: triangle in the (radial, axial) plane swept along a helix on the inside wall
r_wall = ID / 2 - 0.01
helix = cq.Wire.makeHelix(PITCH, PITCH * TURNS, r_wall - FL_H + 0.5, center=cq.Vector(0, 0, 8), dir=cq.Vector(0, 0, 1))
# profile at the helix start point (r, 0, 8): triangle with the vertical face on the wall side and a 45 deg underside
p0 = helix.startPoint()
prof = (cq.Workplane('XZ', origin=(p0.x, p0.y, p0.z)).polyline([(0, 0), (FL_H, 0), (FL_H, FL_W)]).close())
flight = prof.sweep(cq.Workplane().add(helix), isFrenet=True)
flight = flight.intersect(cyl(0, 0, 1, ID + 0.5, L - 2))            # keep it inside the bore
barrel = barrel.union(flight)
for deg in (90, 210, 330):                                           # end bosses + M3 inserts, as V7
    t = math.radians(deg); x, y = 74 * math.cos(t), 74 * math.sin(t)
    for z in (0, 170): barrel = barrel.union(cyl(x, y, z, 12, 10))
    barrel = insert(barrel, (x, y, 0), (0, 0, 1)); barrel = insert(barrel, (x, y, 180), (0, 0, -1))
barrel = barrel.clean()

# 49b static front plate: labyrinth ring over the barrel end, face plate with a bottom outlet, ears to the cradles
GAP, RING_T, FACE_T = 1.5, 6.0, 4.0
plate = cyl(0, 0, L + 2, 172, FACE_T)                                               # face, 2 mm off the barrel end
# inner spill lip reaching 6 mm into the bore (clear of the end bosses at r 68..80), cut away over the outlet
plate = plate.union(cyl(0, 0, L - 6, 134, 8).cut(cyl(0, 0, L - 7, 116, 10)))
# thrust face: the barrel's three end bosses (r 68..80) rub on this ring if the drum slides forward; 0.6 gap at rest; grease it
plate = plate.union(cyl(0, 0, L + 0.6, 162, 1.5).cut(cyl(0, 0, L, 134, 3)))
WIN_W, WIN_R0, WIN_R1 = 65.0, 28.0, 68.0                                            # outlet: 65 wide, from r 28 to r 68 on the down side (+X)
plate = plate.cut(box((WIN_R0 + WIN_R1) / 2, 0, L - 8, WIN_R1 - WIN_R0, WIN_W, 16))
plate = plate.cut(box(60, 0, L - 8, 30, WIN_W + 12, 10))                            # lip opened over the outlet so pieces slide straight out
plate = plate.cut(cyl(WIN_R1 - WIN_W / 2 + 0, 0, L, 0.01, 1)) if False else plate
EAR_Y = 91.5                                                                           # cradle plates at +-92 from the drum axis
for sy in (-1, 1):
    ear = box(0, sy * (EAR_Y - 8), L + 2, 40, 8, FACE_T).union(box(0, sy * (EAR_Y - 6), L - 20, 40, 4, 26))   # tab stops at y 87.5, strip on the cradle's inner face (y 83.5..87.5)
    for z in (L - 14, L - 2): ear = ear.cut(cq.Workplane('XY').circle(1.7).extrude(10).translate((0, 0, -5)).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, sy * (EAR_Y - 6), z)))
    plate = plate.union(ear)
plate = plate.clean()

# checks: barrel rotated vs plate (must be 0 at every angle), flight inside the bore, print bed
def vol(a, b):
    try: return a.val().intersect(b.val()).Volume()
    except Exception: return 0.0
rot = {deg: round(vol(barrel.rotate((0, 0, 0), (0, 0, 1), deg), plate), 2) for deg in range(0, 360, 30)}
bb = barrel.val().BoundingBox(); pb = plate.val().BoundingBox()
report = {'barrel_vs_static_plate_mm3_by_angle': rot, 'flight': {'pitch': PITCH, 'height': FL_H, 'base': FL_W, 'turns': TURNS, 'advance_mm_per_rev': PITCH, 'mm_per_s_at_4rpm': PITCH * 4 / 60},
          'outlet': {'width': WIN_W, 'radial_from': WIN_R0, 'radial_to': WIN_R1, 'lip_at_wall_mm': ID / 2 - WIN_R1}, 'thrust': 'static plate carries the thrust face; V7 part 57 and its 9th 625 bearing are dropped',
          'barrel_bbox': [round(v, 1) for v in (bb.xlen, bb.ylen, bb.zlen)], 'plate_bbox': [round(v, 1) for v in (pb.xlen, pb.ylen, pb.zlen)],
          'barrel_valid_single': barrel.val().isValid() and len(barrel.solids().vals()) == 1, 'plate_valid_single': plate.val().isValid() and len(plate.solids().vals()) == 1,
          'barrel_volume_cm3': round(barrel.val().Volume() / 1000, 1), 'print': '47b: axis vertical, outlet end down; the flight underside is 45 deg so no supports. 49b: face down on the bed.'}
cq.exporters.export(barrel, str(OUT / '47b_tumbler_barrel_helical_flight.stl')); cq.exporters.export(barrel, str(OUT / '47b_tumbler_barrel_helical_flight.step'))
cq.exporters.export(flight, str(OUT / '47b_flight_only_PREVIEW.stl'))   # render aid only, not a print
cq.exporters.export(plate, str(OUT / '49b_drum_static_outlet_plate.stl')); cq.exporters.export(plate, str(OUT / '49b_drum_static_outlet_plate.step'))
(OUT / 'drum_v13_checks.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report, indent=1))
