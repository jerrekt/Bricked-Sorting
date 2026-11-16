"""Whole-machine print status: every printed part (qty, est grams, est hours) from the module parts.json files plus the
V13 reuse parts, minus what BJ has printed (DONE below, kept in step with print_log.json). Writes print_status.json
(also copied to the site as web/data/prints.json).
Estimates are the modules' day-profile numbers (V13 reuse parts: geometry at 2 walls / 15 %, deck g/h ratio).
Usage: python3 print_status.py [OUT.json]
"""
import json, sys
from pathlib import Path
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = Path('/home/claude')
MODS = [('Frame and skin', ROOT / 'wt_frame5/cad/v14/frame/parts.json', 'printed'),
        ('Deck', ROOT / 'wt_deck5/cad/v14/deck/parts.json', 'printed_new'),
        ('Drawers', ROOT / 'wt_all/cad/v14/drawer/parts.json', 'printed'),
        ('Scoop', ROOT / 'wt_all/cad/v14/scoop/parts.json', 'printed')]
V13 = [('47b_tumbler_barrel_helical_flight', 1, 'PETG', 3), ('48_drum_rear_feed_guard', 1, 'PETG', 2), ('49b_drum_static_outlet_plate', 1, 'PETG', 2),
       ('54_drum_drive_core_5mm', 1, 'PETG', 2), ('55_drum_friction_tire_TPU', 1, 'TPU', 2), ('56_drum_NEMA17_adjustable_bracket', 1, 'PETG', 2),
       ('57d_door_slider', 1, 'PETG', 2), ('59_door_link', 2, 'PETG', 2), ('59b_servo_link', 1, 'PETG', 2), ('60_servo_horn_arm', 1, 'PETG', 2),
       ('62_vib_motor_saddle', 2, 'PETG', 2), ('63_vib_motor_cap', 2, 'PETG', 2)]
DEN = {'PETG': 1.27, 'PLA': 1.24, 'TPU': 1.21}
# label -> qty printed (BJ's Bambu history, 2026-11-15). 'printing' counts separately.
DONE = {'130_stud_ring_left_hopper': 1, '131_stud_cap_right': 1, '120_clip_C1_single': 1,
        '201_hopper': 1, '202_feed_chute': 1, '203_V1_tray': 1, '204_V2_tray': 1, '207_leaf_spring_V1_1': 1, '207_leaf_spring_V1_2': 1,
        '207_leaf_spring_V2_1': 1, '207_leaf_spring_V2_2': 1, '210_scanner_plate': 1, '211_landing_ramp_low': 1, '213_servo_saddle': 1,
        '214_trapdoor_A': 1, '214_trapdoor_B': 1, '215_camera_bridge': 1, '50b_drum_625_roller': 4,
        '160_rail_R': 1, '161_rail_L': 1, '162_station_R': 1, '162_station_L': 1, '164_guide_R': 1, '168_face_B1': 1, '168_face_B1_ink': 1,
        '172_reed_coupon_tray': 1, '172_reed_coupon_floor': 1,
        '49b_drum_static_outlet_plate': 1, '55_drum_friction_tire_TPU': 1, '56_drum_NEMA17_adjustable_bracket': 1, '57d_door_slider': 1,
        '59b_servo_link': 1, '63_vib_motor_cap': 2, '47b_tumbler_barrel_helical_flight': 1,
        '48_drum_rear_feed_guard': 1, '54_drum_drive_core_5mm': 1, '59_door_link': 2, '60_servo_horn_arm': 1, '62_vib_motor_saddle': 2,
        '205_drum_cradle_A_ypos': 1, '205_drum_cradle_B_yneg': 1, '206_motor_wall': 1, '212_slider_post': 1, '216_led_bar_holder_A': 1,
            '216_led_bar_holder_B': 1, '217_webcam_mount_generic': 1, '218_apds9960_mount': 1, '228_webcam_cable_spool': 1, '226_usb_cable_clip_1': 1, '226_usb_cable_clip_2': 1}
PRINTING = {'180_beam_seg_1': 1, '180_beam_seg_2': 1, '180_beam_seg_3': 1}
SKIP = {'217_xiao_sense_camera_mount'}   # BJ 2026-11-16: POC uses the Pi + Logitech USB webcam, no XIAO camera

# POC scope (BJ 2026-11-16): semester-1 proof of concept = open wood frame + the very top (roof tiles, studs, hopper)
# + deck (isolate / identify) + scoop (indicate). Walls, corner caps, panels, drawers and faces wait for semester 2.
def scope_of(module, part):
    if module == 'Drawers':
        return 'sem2'
    if module == 'Frame and skin':
        return 'poc' if part.startswith(('114_roof', '123_clip_C3', '122_clip_H', '130_', '131_')) else 'sem2'
    return 'poc'


def est_v13(name, mat, walls, gph):
    m = trimesh.load(HERE / 'v13_reuse' / f'{name}_PRINT_1.stl')
    V = abs(m.volume); sh = min(V, m.area * 0.42 * walls)
    g = DEN[mat] * (sh + 0.15 * (V - sh)) / 1000
    return g, g / gph


def main(out):
    rows = []
    deck = json.loads(MODS[1][1].read_text())
    gph = deck['est_total_grams_new_parts'] / deck['est_total_hours_new_parts']
    for mod, f, key in MODS:
        for p in json.loads(f.read_text())[key]:
            if p['label'] in SKIP: continue
            g = p.get('est_grams_each', p.get('est_grams', 0)); h = p.get('est_hours_each', p.get('est_hours', 0))
            rows.append({'module': mod, 'part': p['label'], 'material': p['material'], 'qty': p['qty'], 'g_each': round(g, 1), 'h_each': round(h, 2)})
    for name, q, mat, walls in V13:
        g, h = est_v13(name, mat, walls, gph)
        rows.append({'module': 'Drum (V13 parts)', 'part': name, 'material': mat, 'qty': q, 'g_each': round(g, 1), 'h_each': round(h, 2)})
    T = {'total': [0, 0], 'done': [0, 0], 'printing': [0, 0], 'left': [0, 0]}
    mods = {}
    for r in rows:
        d = min(DONE.get(r['part'], 0), r['qty']); pr = min(PRINTING.get(r['part'], 0), r['qty'] - d); left = r['qty'] - d - pr
        r.update(done=d, printing=pr, left=left, scope=scope_of(r['module'], r['part']))
        for k, n in (('total', r['qty']), ('done', d), ('printing', pr), ('left', left)):
            T[k][0] += n * r['g_each']; T[k][1] += n * r['h_each']
        m = mods.setdefault(r['module'], {'total_g': 0, 'left_g': 0, 'left_h': 0, 'parts': 0, 'parts_left': 0})
        m['total_g'] += r['qty'] * r['g_each']; m['left_g'] += left * r['g_each']; m['left_h'] += left * r['h_each']
        m['parts'] += r['qty']; m['parts_left'] += left
    POC = {'total': [0, 0], 'done': [0, 0], 'printing': [0, 0], 'left': [0, 0]}
    for r in rows:
        if r['scope'] != 'poc': continue
        for k, n in (('total', r['qty']), ('done', r['done']), ('printing', r['printing']), ('left', r['left'])):
            POC[k][0] += n * r['g_each']; POC[k][1] += n * r['h_each']
    log = json.loads((HERE / 'print_log.json').read_text())
    used = sum(e['grams'] for e in log['prints']); used_h = sum(e.get('hours', 0) for e in log['prints'] if e.get('status') != 'printing')
    mach = [e for e in log['prints'] if e.get('status', 'done') == 'done' and not e['plate'].startswith(('(', 'P1', 'P5', 'P4 (old'))
            or e['plate'] in ('P14+P4', 'P13/P16/P18', 'P16', 'P17', 'P18', 'P12', 'P11') and e.get('status', 'done') == 'done']
    pace = round(sum(e.get('hours', 0) for e in mach) / T['done'][1], 2) if T['done'][1] else 1.0   # Bambu actual h / CAD est h on the same parts
    res = {'_note': 'Estimates. Total/left from the CAD day-profile numbers (no supports, brim or purge); used = BJ\'s Bambu jobs incl. tests and '
                     'cancels (print_log.json). Generated by cad/v14/plates/print_status.py on branch cad-v14-all.',
           'updated': log.get('updated', ''),
           'summary': {k: {'grams': round(v[0]), 'hours': round(v[1], 1)} for k, v in T.items()},
           'poc': {k: {'grams': round(v[0]), 'hours': round(v[1], 1)} for k, v in POC.items()},
           'pace_factor': pace,
           'left_at_pace_hours': round(T['left'][1] * pace),
           'used_so_far': {'grams': round(used), 'hours': round(used_h, 1), 'jobs': len(log['prints'])},
           'printing_now': [r['part'] for r in rows if r['printing']],
           'modules': {k: {kk: round(vv, 1) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in mods.items()},
           'parts': rows}
    Path(out).write_text(json.dumps(res, indent=1))
    print('POC', json.dumps(res['poc']), 'left at pace', round(res['poc']['left']['hours'] * pace))
    print(json.dumps(res['summary']), res['used_so_far'], 'pace', pace, 'left at pace', res['left_at_pace_hours'])
    for k, v in res['modules'].items(): print(k, v)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / 'print_status.json')
