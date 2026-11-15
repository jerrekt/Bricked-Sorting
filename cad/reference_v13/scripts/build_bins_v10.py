"""Bricked Sorting V10: 600x350 bin tiers, integral-mouth bins, locators with
bin-presence switch pockets, and a compact scoop. CadQuery 2.8. Units mm.

Frame (tier-local): Z axis = scoop yaw axis, Z=0 = top of the LOWER carrier,
+Y = drawer pull-out direction (yaw 0). All numbers below are proposals.
Fit values come from BJ's 3D-printing runbook (P2S, PLA, 0.4/0.2):
  sliding/dovetail 0.07 per side, press pockets -0.02 per side.
Bins are a loose drop-in for children, so their pocket clearance is larger
(0.6 per side) on purpose. Switch body size is NOT measured: see SW_*.
"""
from pathlib import Path
import math, json, struct, collections, hashlib
import numpy as np
import cadquery as cq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'bins_v10'; OUT.mkdir(exist_ok=True)

# ---------------- layout parameters ----------------
PITCH = 22.5            # deg per bin, 8 bins fill 180 deg per tier
HALF = math.radians(PITCH / 2)
GAP_SIDE = 3.0          # bin side face offset from the radial boundary (6 mm between bins)
RI, RO = 152.0, 290.0   # bin inner / outer face radius
T, FLOOR = 2.4, 2.4     # wall and floor (same as test bins V1/V2)
CORNER = 4.0            # outer vertical corner radius
LIP_OUT, LIP_H = 8.0, 10.0   # outward grip lip at the outer wall top
BEVEL = 12.0            # 45 deg deflector inside the inner wall top
POCKET_CLR = 0.6        # loose drop-in clearance per side (kids lift bins out)
LOC_SEAT, LOC_RIM, LOC_GAP = 13.5, 3.0, 0.2
CARRIER, TIER_GAP = 3.0, 10.0
H_LOW, SILL_LOW = 140.0, 70.0          # lower bins: full walls 140, inner wall 70 (window above)
H_UPPER = 140.0  # upper bins: open top, inner wall full height
# BJ 2026-11-03 12:34 PT: each floor standardizes to its biggest size; the only
# difference is floor 1 vs floor 2. S/M/L classes are kept as labels only.
H_UP = {'S': H_UPPER, 'M': H_UPPER, 'L': H_UPPER}
# Switch pocket (generic KW11-3Z roller lever). MEASURE the real body and edit.
SW_L, SW_W, SW_H, SW_R = 20.0, 6.4, 10.3, 215.0
SW_CLR = 0.15           # starting clearance per side; body is also trapped by the carrier
WIN_W, WIN_L = 4.6, 24.0   # narrower than the 6.4 body so it cannot pass up through
# Compact scoop (reuses hub 06 and its four M3 screws)
SLOPE = 40.0; SN, CS = math.sin(math.radians(SLOPE)), math.cos(math.radians(SLOPE))
SC_FLOOR, SC_WALL, SC_FLARE = 3.2, 45.0, 6.0
SC_REAR, SC_CATCH_END, SC_NOSE = -55.0, 35.0, 133.0   # horizontal distances from yaw axis
SC_CATCH_HALF, SC_OUT_HALF = 55.0, 20.0                # 110 wide catch -> 40 wide outlet
SC_SWEEP = 137.0        # everything trimmed inside this yaw radius
NOSE_CLR_LOW, NOSE_CLR_UP = 35.0, 35.0   # scoop lowest point above sill / inner-wall top
MAX_PART_H = 30.0       # tallest accepted part as it slides (assumption)
BED = (248.0, 248.0, 256.0)

LOWER_SEAT = LOC_SEAT
UPPER_CARRIER_UNDERSIDE = LOWER_SEAT + H_LOW + TIER_GAP
UPPER_SEAT = UPPER_CARRIER_UNDERSIDE + CARRIER + LOC_SEAT

# Slot -> class from test_bin_v1/recalibrated_bin_allocation.json
GROUPS = {1: 'Red / Orange', 2: 'Yellow', 3: 'Green / Lime', 4: 'Blue / Azure',
          5: 'Pink / Purple', 6: 'Black / Dark Gray', 7: 'White / Light Gray', 8: 'Unknown color'}
UPPER_CLASS = {1: 'M', 2: 'S', 3: 'S', 4: 'M', 5: 'S', 6: 'L', 7: 'L', 8: 'M'}
def slot_yaw(k):  # proposed: slot 1 at the -X end, slot 8 at the +X end
    return 90.0 - PITCH * (k - 0.5)

# ---------------- geometry helpers ----------------
def side_point(r, g, sign):
    u = (sign * math.sin(HALF), math.cos(HALF)); n = (-sign * math.cos(HALF), math.sin(HALF))
    t = math.sqrt(r * r - g * g)
    return (t * u[0] + g * n[0], t * u[1] + g * n[1])

def wedge_wire(r1, r2, g):
    L1, L2 = side_point(r1, g, -1), side_point(r2, g, -1)
    R1, R2 = side_point(r1, g, 1), side_point(r2, g, 1)
    V = lambda p: cq.Vector(p[0], p[1], 0)
    edges = [cq.Edge.makeLine(V(L1), V(L2)),
             cq.Edge.makeThreePointArc(V(L2), cq.Vector(0, r2, 0), V(R2)),
             cq.Edge.makeLine(V(R2), V(R1)),
             cq.Edge.makeThreePointArc(V(R1), cq.Vector(0, r1, 0), V(L1))]
    return cq.Wire.assembleEdges(edges)

def rounded(w, r):
    return w.offset2D(-r, 'arc')[0].offset2D(r, 'arc')[0]

def prism(w, z0, h):
    return cq.Workplane(obj=cq.Solid.extrudeLinear(w, [], cq.Vector(0, 0, h)).translate(cq.Vector(0, 0, z0)))

def revolved(points):
    return cq.Workplane('XZ').polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0))

def box(x, y, z, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((x, y, z))

OUTER_W = rounded(wedge_wire(RI, RO, GAP_SIDE), CORNER)
INNER_W = OUTER_W.offset2D(-T, 'arc')[0]

def make_bin(h, sill):
    p = prism(OUTER_W, 0, h).cut(prism(INNER_W, FLOOR, h + 5))
    interior_sector = prism(wedge_wire(RI - 1, RO - 0.5, GAP_SIDE + T), 0, h + 20)
    if sill < h:   # lower tier: open window in the inner wall above the sill
        p = p.cut(prism(wedge_wire(60, RI + T + 0.2, GAP_SIDE + T), sill, h + 5 - sill))
    bev = revolved([(RI + T - 0.05, sill), (RI + T + BEVEL, sill - BEVEL), (RI + T - 0.05, sill - 2 * BEVEL)])
    p = p.union(bev.intersect(interior_sector))
    lip = revolved([(RO - 1, h), (RO + LIP_OUT, h), (RO + LIP_OUT, h - 2), (RO - 0.05, h - LIP_H), (RO - 1, h - LIP_H)])
    p = p.union(lip.intersect(prism(wedge_wire(100, RO + LIP_OUT + 2, GAP_SIDE + 2), 0, h + 1)))
    return p.clean()

def make_locator():
    base_w = rounded(wedge_wire(RI - POCKET_CLR - T, RO + POCKET_CLR + T, LOC_GAP), 1.0)
    pocket_w = OUTER_W.offset2D(POCKET_CLR, 'arc')[0]
    p = prism(base_w, 0, LOC_SEAT + LOC_RIM).cut(prism(pocket_w, LOC_SEAT, LOC_RIM + 1))
    # switch pocket open to the bottom, long axis radial, roller window to the seat
    p = p.cut(box(0, SW_R, -0.01, SW_W + 2 * SW_CLR, SW_L + 2 * SW_CLR, SW_H + 2 * SW_CLR))
    p = p.cut(box(0, SW_R, SW_H, WIN_W, WIN_L, LOC_SEAT + 5))
    # wire groove on the underside to the inner edge
    p = p.cut(box(0, (RI - 10 + SW_R - SW_L / 2) / 2, -0.01, 6, SW_R - SW_L / 2 - (RI - 10) + 1, 4))
    # three M3 countersunk screws down into the carrier (carrier holes pending)
    for x, y in [(0, 172.0), (-24.0, 262.0), (24.0, 262.0)]:
        p = p.cut(cq.Workplane(obj=cq.Solid.makeCylinder(1.7, LOC_SEAT + 2, cq.Vector(x, y, -1))))
        p = p.cut(cq.Workplane(obj=cq.Solid.makeCone(1.7, 3.3, 1.6, cq.Vector(x, y, LOC_SEAT - 1.6))))
    return p.clean()

def make_scoop_print():
    """Built flat (print orientation) like V3 part 05, then trimmed in the
    assembled pose so nothing sweeps outside SC_SWEEP, then returned flat."""
    Y = lambda h: h / CS
    outline = [(-SC_CATCH_HALF, Y(SC_REAR)), (SC_CATCH_HALF, Y(SC_REAR)), (SC_CATCH_HALF, Y(SC_CATCH_END)),
               (SC_OUT_HALF, Y(SC_NOSE)), (-SC_OUT_HALF, Y(SC_NOSE)), (-SC_CATCH_HALF, Y(SC_CATCH_END))]
    wire = cq.Workplane('XY').polyline(outline).close().val()
    def ow(a, z):
        w = wire if a == 0 else cq.Workplane('XY').add(wire).toPending().offset2D(a, kind='intersection').val()
        return w.translate(cq.Vector(0, 0, z))
    outer = cq.Solid.makeLoft([ow(0, 0), ow(SC_FLARE, SC_FLOOR + SC_WALL)], ruled=True)
    inner = cq.Solid.makeLoft([ow(-SC_FLOOR, SC_FLOOR), ow(SC_FLARE - SC_FLOOR, SC_FLOOR + SC_WALL + .05)], ruled=True)
    s = cq.Workplane(obj=outer.cut(inner))
    s = s.cut(box(0, Y(SC_NOSE) + 46, SC_FLOOR, 220, 100, 80))   # open discharge end
    for x in [-15, 15]:
        for y in [-12, 12]:   # same countersunk M3 pattern as V3 part 05 / hub 06
            s = s.cut(cq.Workplane(obj=cq.Solid.makeCylinder(1.7, 8, cq.Vector(x, y, -1))))
            s = s.cut(cq.Workplane(obj=cq.Solid.makeCone(1.7, 3.2, 1.5, cq.Vector(x, y, SC_FLOOR - 1.5))))
    asm = s.rotate((0, 0, 0), (1, 0, 0), -SLOPE)
    asm = asm.intersect(cq.Workplane(obj=cq.Solid.makeCylinder(SC_SWEEP, 600, cq.Vector(0, 0, -300))))
    return asm.rotate((0, 0, 0), (1, 0, 0), SLOPE).clean()

# ---------------- build parts ----------------
parts = {'40_bin_lower_PRINT_8': make_bin(H_LOW, SILL_LOW)}
parts['41_bin_upper_PRINT_8'] = make_bin(H_UPPER, H_UPPER)
parts['42_bin_locator_PRINT_16'] = make_locator()
scoop_flat = make_scoop_print()
parts['43_compact_scoop_PRINT_FLAT'] = scoop_flat

def stl_check(name, wp):
    path = OUT / (name + '.stl')
    bb0 = wp.val().BoundingBox()
    wp = wp.translate((-(bb0.xmin + bb0.xmax) / 2, -(bb0.ymin + bb0.ymax) / 2, -bb0.zmin))
    cq.exporters.export(wp, str(path), tolerance=.04, angularTolerance=.08)
    cq.exporters.export(wp, str(OUT / (name + '.step')))
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 80)[0]
    dt = np.dtype([('n', '<f4', (3,)), ('v', '<f4', (3, 3)), ('a', '<u2')])
    v = np.frombuffer(raw, dtype=dt, count=n, offset=84)['v'].astype(float)
    edges = collections.Counter()
    for tri in v:
        a = [tuple(round(t, 4) for t in q) for q in tri]
        for i, j in ((0, 1), (1, 2), (2, 0)): edges[tuple(sorted((a[i], a[j])))] += 1
    span = np.ptp(v.reshape(-1, 3), axis=0)
    # bed fit: allow any rotation about Z, test the best of 0..89 deg
    pts = v.reshape(-1, 3)[:, :2]; best = None
    for d in range(0, 90):
        t = math.radians(d); R = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        s = np.ptp(pts @ R.T, axis=0)
        if best is None or max(s) < max(best[1]): best = (d, s)
    solid = wp.val()
    return {'valid_single_solid': bool(solid.isValid()) and len(wp.solids().vals()) == 1,
            'watertight_mesh': all(k == 2 for k in edges.values()),
            'triangles': int(n), 'extent_xyz': [round(x, 2) for x in span],
            'best_bed_rotation_deg': best[0], 'bed_footprint_at_best': [round(x, 1) for x in best[1]],
            'fits_248x248x256': bool(max(best[1]) <= BED[0] and span[2] <= BED[2]),
            'solid_volume_cm3': round(solid.Volume() / 1000, 1),
            'sha256_stl': hashlib.sha256(raw).hexdigest()}

report = {'status': 'PROPOSED V10 GEOMETRY, not a print release', 'units': 'mm', 'parts': {}}
for name, wp in parts.items():
    report['parts'][name] = stl_check(name, wp)
    assert report['parts'][name]['valid_single_solid'], name
    assert report['parts'][name]['watertight_mesh'], name

# ---------------- assemble tiers and check ----------------
def place(wp, yaw, z):
    return wp.rotate((0, 0, 0), (0, 0, 1), yaw).translate((0, 0, z))

tiers = {'lower': [], 'upper': []}
for k in range(1, 9):
    y = slot_yaw(k)
    tiers['lower'].append(('lower', k, place(parts['40_bin_lower_PRINT_8'], y, LOWER_SEAT), place(parts['42_bin_locator_PRINT_16'], y, 0), H_LOW, SILL_LOW))
    c = UPPER_CLASS[k]; nm = '41_bin_upper_PRINT_8'
    zc = UPPER_CARRIER_UNDERSIDE + CARRIER
    tiers['upper'].append(('upper', k, place(parts[nm], y, UPPER_SEAT), place(parts['42_bin_locator_PRINT_16'], y, zc), H_UP[c], H_UP[c]))

all_solids = [(f'{t}-{k}-bin', b) for t in tiers for (_, k, b, l, h, s) in tiers[t]] + \
             [(f'{t}-{k}-loc', l) for t in tiers for (_, k, b, l, h, s) in tiers[t]]
clash = []
for i in range(len(all_solids)):
    for j in range(i + 1, len(all_solids)):
        a, b = all_solids[i][1].val(), all_solids[j][1].val()
        ba, bb = a.BoundingBox(), b.BoundingBox()
        if ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin:
            continue
        v = a.intersect(b).Volume()
        if v > 0.01: clash.append([all_solids[i][0], all_solids[j][0], round(v, 2)])
bbs = [s.val().BoundingBox() for _, s in all_solids]
footprint = {'x': [round(min(b.xmin for b in bbs), 1), round(max(b.xmax for b in bbs), 1)],
             'y': [round(min(b.ymin for b in bbs), 1), round(max(b.ymax for b in bbs), 1)],
             'z_top': round(max(b.zmax for b in bbs), 1)}
footprint['width'] = round(footprint['x'][1] - footprint['x'][0], 1)
footprint['depth_from_yaw_axis'] = round(footprint['y'][1], 1)
assert footprint['width'] <= 600, footprint

# scoop in assembly: rotate to the 40 deg pose, then yaw/height per bin
scoop_asm = scoop_flat.rotate((0, 0, 0), (1, 0, 0), -SLOPE)
sb = scoop_asm.val().BoundingBox()
verts = np.array([[v.X, v.Y, v.Z] for v in scoop_asm.val().Vertices()])
sweep_r = float(np.max(np.hypot(verts[:, 0], verts[:, 1])))
# nose floor end radius (floor corners at the outlet)
nose_r = math.hypot(SC_OUT_HALF, SC_NOSE)
poses = []; scoop_clash = []
for t in tiers:
    for (_, k, b, l, h, s) in tiers[t]:
        seat = LOWER_SEAT if t == 'lower' else UPPER_SEAT
        sill_abs = seat + s
        low = sill_abs + (NOSE_CLR_LOW if t == 'lower' else NOSE_CLR_UP)
        sc = scoop_asm.translate((0, 0, low - sb.zmin)).rotate((0, 0, 0), (0, 0, 1), slot_yaw(k))
        for name, other in all_solids:
            v = sc.val().intersect(other.val()).Volume()
            if v > 0.01: scoop_clash.append([f'{t}-{k}', name, round(v, 2)])
        floor_top = low + SC_FLOOR / CS
        poses.append({'tier': t, 'slot': k, 'yaw_deg': slot_yaw(k), 'scoop_lowest_z': round(low, 1),
                      'outlet_floor_top_z': round(floor_top, 1), 'sill_or_inner_wall_top_z': round(sill_abs, 1),
                      'drop_part_bottom_to_sill': round(floor_top - sill_abs, 1),
                      'part_top_if_30mm': round(floor_top + MAX_PART_H, 1)})
lower_nose = min(p['scoop_lowest_z'] for p in poses if p['tier'] == 'lower')
upper_nose = max(p['scoop_lowest_z'] for p in poses if p['tier'] == 'upper')
lift_travel_needed = upper_nose - lower_nose
window_margin = UPPER_CARRIER_UNDERSIDE - max(p['part_top_if_30mm'] for p in poses if p['tier'] == 'lower')

# mouth width: clear chord between side-wall inner faces at the inner wall
def chord_clear(r): return 2 * (r * math.tan(HALF) - (GAP_SIDE + T) / math.cos(HALF))
mouth = round(chord_clear(RI), 1); yaw_err = 1.0
mouth_margin = round(mouth - 2 * SC_OUT_HALF - 2 * RI * math.radians(yaw_err), 1)

# flight: horizontal distance travelled while the part bottom drops to the sill
def flight(v, drop):
    vh, vz = v * CS, v * SN; g = 9810.0
    t = (-vz + math.sqrt(vz * vz + 2 * g * drop)) / g
    return vh * t
gap = RI - nose_r
flight_rows = []
for t, d in [('lower', poses[0]['drop_part_bottom_to_sill']), ('upper', min(p['drop_part_bottom_to_sill'] for p in poses if p['tier'] == 'upper'))]:
    for v in (300, 500, 800, 1100):
        flight_rows.append({'tier': t, 'exit_speed_mm_s': v, 'drop_mm': d, 'horizontal_mm': round(flight(v, d), 1), 'gap_to_cross_mm': round(gap, 1)})
# exit speed estimate along the 40 deg floor from the axis to the outlet
slide = SC_NOSE / CS
v_est = {mu: round(1000 * math.sqrt(max(0, 2 * 9.81 * slide / 1000 * (SN - mu * CS))), 0) for mu in (0.3, 0.45, 0.6)}

# capacity (geometric, before packing voids)
inner_area = cq.Face.makeFromWires(INNER_W).Area()
cap = {}
for k in range(1, 9):
    lo = inner_area * (SILL_LOW - FLOOR) / 1e6
    c = UPPER_CLASS[k]; up = inner_area * (H_UP[c] - 10 - FLOOR) / 1e6
    cap[k] = {'group': GROUPS[k], 'lower_L_to_sill': round(lo, 3), 'upper_class': c, 'upper_L_to_10mm_below_rim': round(up, 3)}
low_tot = sum(v['lower_L_to_sill'] for v in cap.values()); up_tot = sum(v['upper_L_to_10mm_below_rim'] for v in cap.values())

# reference assembly STEP (not a print file)
asm = cq.Assembly(name='V10_TIERS_REFERENCE_ONLY')
for nm, s in all_solids: asm.add(s, name=nm)
asm.add(scoop_asm.translate((0, 0, lower_nose - sb.zmin)), name='scoop_lower_slot1_pose')
asm.save(str(OUT / 'V10_TIERS_REFERENCE_ONLY.step'))

report.update({
 'frame': 'Z = yaw axis; Z0 = top of lower carrier; +Y = pull-out direction',
 'radii': {'bin_inner_face': RI, 'bin_outer_face': RO, 'grip_lip_outer': RO + LIP_OUT, 'locator_inner_edge': RI - POCKET_CLR - T, 'locator_outer_edge': RO + POCKET_CLR + T, 'scoop_sweep_radius_measured': round(sweep_r, 2), 'scoop_outlet_floor_radius': round(nose_r, 1)},
 'radial_clearance_scoop_to_locator': round(RI - POCKET_CLR - T - sweep_r, 1),
 'heights': {'lower_seat': LOWER_SEAT, 'lower_bin_walls': H_LOW, 'lower_sill': SILL_LOW, 'upper_carrier_underside': UPPER_CARRIER_UNDERSIDE, 'upper_seat': UPPER_SEAT, 'upper_bins': H_UP, 'stack_top': footprint['z_top']},
 'footprint': footprint, 'fits_600x350': footprint['width'] <= 600 and footprint['depth_from_yaw_axis'] <= 350,
 'bin_and_locator_clashes': clash, 'scoop_clashes_at_16_delivery_poses': scoop_clash,
 'delivery_poses': poses, 'lift_travel_needed_mm': round(lift_travel_needed, 1),
 'lift_travel_in_existing_CAD_mm': 105, 'lower_window_margin_30mm_part_mm': round(window_margin, 1),
 'mouth_clear_width_at_inner_wall': mouth, 'outlet_width': 2 * SC_OUT_HALF, 'mouth_margin_after_1deg_yaw_error_each_side': mouth_margin,
 'flight_estimate': flight_rows, 'exit_speed_estimate_mm_s_by_friction': v_est,
 'capacity_geometric_liters': cap, 'tier_totals_L': {'lower': round(low_tot, 2), 'upper': round(up_tot, 2), 'upper_share': round(up_tot / (low_tot + up_tot), 3)},
 'not_verified': ['physical print fit', 'switch body size and roller height (SW_* parameters)', 'actuation by bin weight',
                  'loose-fill volume per color group', 'part flight and bounce', 'drawer carriers, runners, latches', 'lift travel extension',
                  'scanner/trapdoor drop onto the compact scoop'],
})
(OUT / 'dimensions_and_checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['footprint', 'fits_600x350', 'bin_and_locator_clashes', 'scoop_clashes_at_16_delivery_poses', 'lift_travel_needed_mm', 'lower_window_margin_30mm_part_mm', 'mouth_clear_width_at_inner_wall', 'mouth_margin_after_1deg_yaw_error_each_side', 'radial_clearance_scoop_to_locator', 'tier_totals_L', 'exit_speed_estimate_mm_s_by_friction']}, indent=1))
for n, r in report['parts'].items(): print(n, r['extent_xyz'], r['bed_footprint_at_best'], r['fits_248x248x256'], r['solid_volume_cm3'])
for f in flight_rows: print(f)
