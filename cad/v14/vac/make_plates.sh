#!/bin/sh
# Plate P24: one .3mf per print job for the vacuum canister. Run after build_vac.py, from anywhere.
# Bump P24 in ../plates/versions.json (and add a log line) whenever a part on a plate changes.
# Material in the name is what to load: PLAyellow = shell, lid, hose port; PETG = black parts; PLA = coupons, any colour.
set -e
cd "$(dirname "$0")/../plates"
V=../vac/print
rm -f P24_*.3mf
python3 make_plate.py P24_PLA_vac_1_coupons_PRINT_FIRST "$V/265_vac_coupon_socket_ring_PRINT_1.stl+$V/266_vac_coupon_hose_socket_PRINT_1.stl"
python3 make_plate.py P24_PLAyellow_vac_2_shell_lower $V/250_vac_shell_lower_PRINT_1.stl
python3 make_plate.py P24_PLAyellow_vac_3_lid $V/255_vac_lid_PRINT_1.stl
python3 make_plate.py P24_PLAyellow_vac_4_hose_port_and_pivot_cap $V/256_vac_hose_port_PRINT_1.stl $V/253_vac_pivot_cap_PRINT_1.stl
python3 make_plate.py P24_PETG_vac_5_black_funnel $V/251_vac_funnel_PRINT_1.stl
python3 make_plate.py P24_PETG_vac_6_black_gate_disc_and_eyes $V/252_vac_gate_disc_PRINT_1.stl $V/261_vac_eye_PRINT_1.stl:2
python3 make_plate.py P24_PETG_vac_7_black_screen $V/254_vac_screen_PRINT_1.stl
python3 make_plate.py P24_PETG_vac_8_black_mouthpiece_handle_elbows $V/260_vac_handle_PRINT_1.stl $V/257_vac_mouthpiece_PRINT_1.stl $V/258_vac_wand_elbow_PRINT_1.stl:3
