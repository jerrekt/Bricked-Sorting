"""Regenerate the offline engineering register without modifying lift geometry."""
from pathlib import Path
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parent
def read_json(name):
    return json.loads((ROOT / name).read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks = read_json('geometry_checks.json')
bins = read_json('handoff_references/bins_repo_snapshot.json')
inventory = read_json('handoff_references/set_10696_repo_snapshot.json')
assert sum(p['qty'] for p in inventory['parts']) == 484
counts = {f'{f}-{s}': 0 for f in (1, 2) for s in range(1, 9)}
slots = {s['key']: s['slot'] for s in bins['slots']}
for p in inventory['parts']:
    floor = 1 if p['brick'] else 2
    key = bins['colorMap'].get(p['color'], 'unknown')
    counts[f'{floor}-{slots[key]}'] += p['qty']

poses = {
    '01_ground_base': ['identity'],
    '02_moving_carriage_v3': ['translate(0,0,H)'],
    '03_top_rod_brace': ['translate(0,0,342)'],
    '04_lower_switch_mount': ['translate(0,0,8)'],
    '05_open_scoop_PRINT_FLAT': ['rotate_X(-40)', 'translate(0,0,32)', 'rotate_Z(yaw)', 'translate(0,90,H+48)'],
    '06_angled_shaft_hub': ['rotate_Z(yaw)', 'translate(0,90,H+48)'],
    '07_upper_switch_rod_mount': ['translate(0,0,241)'],
    '10_M2_switch_backer_PRINT_TWICE': ['rotate_X(-90)', 'translate(0,-30,83) OR translate(0,-30,258)'],
    '15_optional_foot_PRINT_FOUR': ['rotate_X(180)', 'translate(x_corner,y_corner,0)'],
}
parts = {}
for name, check in checks.items():
    if name == 'motion_check':
        continue
    raw = (ROOT / (name + '.stl')).read_bytes()
    n = struct.unpack_from('<I', raw, 80)[0]
    assert len(raw) == 84 + 50 * n
    mins = [float('inf')] * 3
    maxs = [-float('inf')] * 3
    for i in range(n):
        v = struct.unpack_from('<9f', raw, 84 + i * 50 + 12)
        for j in range(9):
            axis = j % 3
            mins[axis] = min(mins[axis], v[j])
            maxs[axis] = max(maxs[axis], v[j])
    dims = [maxs[i] - mins[i] for i in range(3)]
    assert all(abs(dims[i] - check['dimensions_mm'][i]) < .02 for i in range(3))
    parts[name] = {
        'print_envelope_mm_xyz_rounded': check['dimensions_mm'],
        'stl_print_bounds_mm': {'min_xyz': mins, 'max_xyz': maxs},
        'solid_count': check['solid_count'],
        'print_count': 2 if name.startswith('10_') else 4 if name.startswith('15_') else None if name.startswith(('08_', '09_', '11_', '12_', '13_', '14_')) else 1,
        'role': 'fit_test' if name.startswith(('08_', '09_', '11_', '12_', '13_', '14_')) else 'optional_foot' if name.startswith('15_') else 'assembly_part',
        'print_to_assembly_operations_in_order': poses.get(name),
        'sha256_stl': sha(ROOT / (name + '.stl')),
        'sha256_step': sha(ROOT / (name + '.step')),
    }

data = {
    'project': 'Bricked Sorting',
    'document_revision': 'V3 engineering handoff 2026-10-29',
    'geometry_revision': 'V3 heat-set; no geometry changed by this documentation update',
    'units': {'length': 'mm', 'angle': 'deg'},
    'status_vocabulary': ['user_requirement', 'cad_baseline', 'proposal', 'unknown', 'physically_verified'],
    'physical_verification': 'No fit, load, capacity or sorting test results supplied.',
    'user_requirements': {
        'minimize_replacement_prints': True,
        'large_assembled_machine_acceptable': True,
        'assembled_max_dimensions_mm_xyz': None,
        'printer': 'Bambu P2S', 'individual_bed_mm_xyz': [256, 256, 256],
        'nozzle_diameter_mm': .4, 'material_for_initial_fit': 'PLA',
        'direct_printed_rod_bores': True,
        'new_printed_joints': 'M2/M3/M4/M5 screws with matching user heat-set inserts',
        'add_modules': ['16 bins and holders', 'two vibratory V stages', 'scanner/release platform if feasible'],
        'funnel_selection': 'open scoop',
        'target_sets': {'set': '10696-1', 'quantity_range': [1, 2], 'listed_piece_counts': [484, 968]},
    },
    'coordinates': {
        'origin': 'lead-screw axis at base underside',
        'axes': {'X': 'across rods', 'Y': 'forward', 'Z': 'up'},
        'yaw_axis_xy': [0, 90],
        'yaw_positive': 'right hand about +Z; +Y turns toward -X',
        'radial_xy_formula': 'x=-r*sin(yaw), y=90+r*cos(yaw)',
        'H': 'global height of lowest printed carriage surface/local z=0',
        'ground_offset_mm': '10 with original feet, 0 without; add new pedestal height if used',
        'transforms': 'Operations use print STL/STEP coordinates and apply in listed order. Geometry source has different local normalization for upper collar and backers.',
    },
    'interfaces_cad_baseline': {
        'base_M5': {'xy_centers': [[-85,-60],[85,-60],[-85,110],[85,110]], 'pattern_xy': [170,170], 'entry_z':13, 'insert_axis':[0,0,-1], 'boss_od':15, 'boss_z_range':[8,13], 'clearance_diameter':5.4, 'usage':'feet or adapter; define shared fastener stack'},
        'base_lower_bracket_M3': {'xy_centers':[[-8,-40],[8,-40]], 'entry_z':0, 'insert_axis':[0,0,1]},
        'rods': {'diameter':12,'length':350,'xy_centers':[[-45,0],[45,0]],'center_spacing':90,'z_range':[10,360],'fixed_bore_diameter':12.3,'moving_bore_diameter':12.4},
        'top_brace': {'assembly_z_range':[342,356],'lead_clearance_diameter':11,'M4_entry_centers':[[-45,-25,349],[45,-25,349]],'insert_axis':[0,1,0]},
        'base_rod_M4': {'entry_centers':[[-45,-25,25],[45,-25,25]],'insert_axis':[0,1,0]},
        'motor_mounts': {'bolt_pattern_xy':[31,31],'M3_clearance_diameter':3.4,'pilot_clearance_diameter':22.6,'fixed_axis_xy':[0,0],'fixed_face_z':58,'rotating_axis_xy':[0,90],'rotating_face_z_formula':'H+40','rotating_shaft_diameter':5,'rotating_shaft_length':24,'rotating_case_xyz':[42,42,48],'rotating_case_z_formula':['H-8','H+40']},
        'lead_nut': {'M3_hole_xy':[[8,0],[-8,0],[0,8],[0,-8]],'pitch_circle_diameter':16,'adjacent_hole_distance':math.sqrt(128),'body_clearance_diameter':10.6,'flange_nominal_diameter_approx':22,'threaded_purchased_part':True},
        'scoop_hub': {'scoop_plane_M3_xy':[[-15,-12],[-15,12],[15,-12],[15,12]],'pattern_xy':[30,24],'clearance_diameter':3.4,'countersink_diameter':6.4,'countersink_depth':1.5,'ramp_slope_deg':40,'floor_thickness':3.2,'wall_height_above_floor':45,'flare':6,'hub_shaft_bore_diameter':5.2,'hub_shaft_bore_depth':21,'shaft_insertion_nominal':16,'hub_bottom_formula':'H+48','side_M3_entry_hub_local':[0,-23,10],'side_M3_axis':[0,1,0],'outlet_clear_width_approx':90,'outlet_floor_lip_radius_approx':110,'outlet_floor_z_formula_approx':'H-12.3'},
        'switches': {'purchased_body_xyz':[20,6.4,10.2],'purchased_hole_diameter':2.4,'hole_spacing':9.5,'bracket_slot_width':2.6,'bracket_slot_overall_length':20,'screw_center_travel_each_direction':8.7,'bracket_plate_thickness':4,'hole_x':[-4.75,4.75],'lower_reference_hole_z':83,'upper_reference_hole_z':258,'upper_collar_reference_bottom_z':281,'backer_physical_xyz':[17,6,7],'backer_M2_entry_direction_physical':[0,-1,0],'lever_geometry':'unknown/not modeled'},
        'optional_feet': {'od':24,'height':10,'clearance_diameter':5.4,'head_recess_diameter':9.5,'head_recess_depth':5.5},
    },
    'insert_profiles_cad_starting_points': read_json('insert_profiles.json'),
    'hardware': read_json('hardware_manifest.json'),
    'baseline_parts': parts,
    'baseline_sources_sha256': {name:sha(ROOT/name) for name in ('build_carriage_v3.py','ASSEMBLY_REFERENCE_ONLY.step','geometry_checks.json','insert_profiles.json','hardware_manifest.json')},
    'motion_cad_only': {'H_range':[95,200],'travel':105,'yaw_range':[-90,90],'full_rotation_validated':False,'reference_assembly_H':110,'existing_sample_results':checks['motion_check']},
    'sorting': {
        'code_format': bins['codeFormat'], 'floors': bins['floors'], 'slots': bins['slots'], 'rules': bins['rules'], 'colorMap': bins['colorMap'],
        'physical_calibration': bins['physical'],
        'per_bin_inventory_counts': {code:{'one_set':n,'two_sets':2*n} for code,n in counts.items()},
        'counts_do_not_establish_volume':True,
        'process_order':['drum tumbler','V1','V2','inspection/held part','chute positioning','release','chute transit','bin'],
        'manual_exclusions_proposed':['large 8x16 plate','brick separator','out-of-tested-envelope pieces'],
    },
    'integration_proposals': {
        'modular_independent_frame': {'recommendation_rating_out_of_10':9,'status':'proposal'},
        'bin_layout': {'tiers':2,'bins_per_tier':8,'forward_semicircle_recommended':True,'status':'proposal; user circle/semicircle requirement remains flexible','radius':None,'mouth_dimensions':None,'floor_heights':None,'storage_volume_per_bin':None},
        'vibration_stages': {'quantity':2,'status':'proposal','isolated_from_scanner':True,'motor_model':None,'mount_dimensions':None,'tray_dimensions':None},
        'scanner': {'recommendation_rating_out_of_10':8,'status':'proposal','drop_xy':[0,90],'tray_dimensions':None,'camera_model':None,'camera_working_distance':None,'gate_type':None,'gate_actuator':None},
        'reach_constraint': {'illustrative_sector_pitch_deg':22.5,'adjacent_center_chord_at_r110':2*110*math.sin(math.radians(11.25)),'warning':'90-wide outlet exceeds ~42.9 pitch. Larger rack needs reachable receiving necks or a removable outlet adapter; footprint permission alone does not solve reach.','straight_extension_extra_drop_per_extra_horizontal_reach':math.tan(math.radians(40))},
    },
    'unknowns': ['actually printed revision and parts','actual fit corrections','assembled footprint upper bound','lead screw actual length/lead and exact nut','maximum automatic LEGO envelope','loose-fill storage volume','bin receiving paths and rack radius','tier mouth heights','drum interface','vibration motors and mounts','feeder tray geometry','camera/lens/lighting','scanner gate and actuator','angular home sensor','cable routing','complete assembly collisions and loads'],
    'references': {'repository':'https://github.com/jerrekt/Bricked-Sorting','website':'https://bricked-01.adsuaracloud.com/','repo_snapshot_commit_short':'c11a4c3','remote_unchanged_by_this_task':True},
}
assert sum(counts.values()) == 484
assert len(parts) == 15
assert data['sorting']['physical_calibration']['zByFloorMm'] == {'1': None, '2': None}
if (ROOT/'electronics_addon/electronics_dimensions.json').exists():
    data['document_revision']='V3 engineering handoff plus additive power layout 2026-10-29'
    data['geometry_revision']='Original V3 lift unchanged; separate electronics panel added'
    data['workflow_file']='WORKFLOW_AND_CAD_STATUS.txt'
    data['electronics_addon']=read_json('electronics_addon/electronics_dimensions.json')
    data['additive_parts']={
      '16_electronics_layout_panel':{
        'directory':'electronics_addon',
        'sha256_stl':sha(ROOT/'electronics_addon/16_electronics_layout_panel.stl'),
        'sha256_step':sha(ROOT/'electronics_addon/16_electronics_layout_panel.step'),
        'full_machine_pose':None,
        'PSU_retention_status':'pending measured mounting geometry',
      }
    }
if (ROOT/'brick_layout_v4/layout_dimensions_and_parts.json').exists():
    layout=read_json('brick_layout_v4/layout_dimensions_and_parts.json')
    data['document_revision']='V4 brick-style base/layout engineering handoff 2026-10-29'
    data['geometry_revision']='V3 lift retained; additive electronics and V4 housing layout'
    data['housing_layout_v4']={
      'dimensions_file':'brick_layout_v4/layout_dimensions_and_parts.json',
      'instructions':'brick_layout_v4/READ_THIS_FIRST_V4.txt',
      'body_xyz':layout['outer_body_xyz'],
      'shell':layout['shell_details'],
      'floor':layout['floor'],
      'lift_transform_and_interfaces':layout['lift'],
      'bin_layout_proposal':layout['bins'],
      'electronics_pose_proposal':layout['electronics'],
      'part_checks_and_quantities':layout['print_checks'],
      'pending':layout['not_yet_designed'],
      'controller_calibration_unchanged':True,
    }
if (ROOT/'external_access_v5/outside_access_dimensions.json').exists():
    access=read_json('external_access_v5/outside_access_dimensions.json')
    data['document_revision']='V5 outside bin access 2026-10-29'
    data['latest_access_revision']={
      'instructions':'external_access_v5/READ_THIS_FIRST_V5.txt',
      'dimensions_file':'external_access_v5/outside_access_dimensions.json',
      'user_requirement':access['user_requirement'],
      'concept':access['concept'],
      'access_dimensions':access['drawer_access'],
      'carrier_reference':access['carriers_reference_only'],
      'hardware':access['hardware'],
      'control_requirements':access['control_requirements'],
      'part_checks':access['new_part_checks'],
      'superseded_front_skin':access['replaced_parts_in_layout'],
      'remaining':access['not_yet_released'],
      'validation':access['validation'],
      'calibration_unchanged':True,
    }
if (ROOT/'intake_stud_v6/intake_and_access_dimensions.json').exists():
    intake=read_json('intake_stud_v6/intake_and_access_dimensions.json')
    data['document_revision']='V6 open loading stud 2026-10-29'
    data['latest_intake_revision']={
      'instructions':'intake_stud_v6/READ_THIS_FIRST_V6.txt',
      'dimensions_file':'intake_stud_v6/intake_and_access_dimensions.json',
      'intake':intake['latest_intake'],
      'effective_modeled_print_counts':intake.get('effective_modeled_print_counts',{}),
      'outside_bin_access_retained':True,
    }
if (ROOT/'isolate_v7/isolate_and_machine_dimensions.json').exists():
    isolation=read_json('isolate_v7/isolate_and_machine_dimensions.json')
    data['document_revision']='V7 proposed Isolate and scanner integration 2026-10-29'
    data['latest_isolate_revision']={
      'instructions':'isolate_v7/READ_THIS_FIRST_V7.txt',
      'dimensions_file':'isolate_v7/isolate_and_machine_dimensions.json',
      'proposed_module':isolation['proposed_isolate'],
      'effective_modeled_print_counts':isolation['effective_modeled_print_counts'],
      'baseline_geometry_unchanged':True,
      'additional_clearance_report':'isolate_v7/additional_clearance_checks.json',
      'world_pose_note':'V7 raises body roof andstud poses300. Lower lift/drawer coordinates remain asV5. Older section heights are historical.',
    }
    data['unknowns']=[x for x in data['unknowns'] if x not in ('drum interface','feeder tray geometry','camera/lens/lighting')]
    data['unknowns']+=['V7 motor/actuator procurement and verified camera adapter','V7 directional feeder suspension and measured material flow','V7 chassis/guards and full structural verification']
(ROOT/'ENGINEERING_REGISTER.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'parts':len(parts),'total_per_set':sum(counts.values()),'per_bin_counts':counts,'register':'ENGINEERING_REGISTER.json'},indent=2))
