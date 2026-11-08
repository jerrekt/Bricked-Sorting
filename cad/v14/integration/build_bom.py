"""V14 (interface 5.1) bill of materials: BOM_V14.xlsx + BOM_V14.md.
Quantities come from each module's parts.json / the frame cut list; prices are BJ's paid prices from
web/data/build_parts.json where we have them, otherwise typical listings (marked approx). Owned = on hand per the
vault inventory / Parts page. Run: python3 build_bom.py
"""
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
WT_FRAME = Path('/home/claude/wt_frame5/cad/v14/frame'); WT_DECK = Path('/home/claude/wt_deck5/cad/v14/deck')
DRAWER = HERE.parent / 'drawer'; SCOOP = HERE.parent / 'scoop'

pf = json.loads((WT_FRAME / 'parts.json').read_text()); pk = json.loads((WT_DECK / 'parts.json').read_text())
pd = json.loads((DRAWER / 'parts.json').read_text()); ps = json.loads((SCOOP / 'parts.json').read_text())
G = {'F': pf['totals']['printed_grams'], 'K': pk['est_total_grams_new_parts'], 'D': pd['est_total_grams'], 'S': ps['est_total_grams']}
H = {'F': pf['totals']['printed_hours'], 'K': pk['est_total_hours_new_parts'], 'D': pd['est_total_hours'], 'S': ps['est_total_hours']}
petg = sum(p['est_grams_each'] * p['qty'] for p in pd['printed'] if 'PETG' in p['material'])
red_kg = round(G['F'] / 1000, 2)
other_kg = round((G['K'] + G['D'] + G['S'] - petg) / 1000, 2)
petg_kg = round(petg / 1000 + 0.15, 2)          # + deck trays/springs (PETG) ~0.15

# section, item, spec, qty (number), unit, where used, owned (Y/N/part), unit price, price per, approx, source, note
ROWS = [
 # ---------------- wood ----------------
 ('Wood', '2x2 x 8 ft', 'select pine/fir, straight', 1, 'board', 'F: 4 corner posts 600', 'N', 5.50, 1, True, 'Home Depot / Lowe\'s', 'cut list: cad-v14-frame5 frame/cut_list.md'),
 ('Wood', '1x2 x 8 ft', '19 x 38 actual', 3, 'board', 'F: top rails, deck cleats, bottom rails, beam posts, roof cross rails', 'N', 3.00, 1, True, 'Home Depot / Lowe\'s', ''),
 ('Wood', '1/2 in plywood 2 x 4 ft', 'handy panel; store cuts 720x360 + 708x348', 1, 'panel', 'F: floor + deck', 'N', 16.00, 1, True, 'Home Depot / Lowe\'s', 'deck needs corner notches + 56 mm funnel hole'),
 ('Wood', '#8 x 2.5 in wood screw', '', 44, 'pc', 'F: rails/cleats/beam posts/cross rails to posts', 'N', 8.00, 100, True, 'Home Depot', ''),
 ('Wood', '#8 x 2 in wood screw', '', 8, 'pc', 'F: posts to floor ply', 'N', 0, 1, True, '', 'in the #8 box if mixed; else buy 1 small pack'),
 ('Wood', '#6 x 1.25 in wood screw', '', 12, 'pc', 'F: deck ply to cleats', 'N', 5.00, 100, True, 'Home Depot', ''),
 ('Wood', '#6 x 3/4 in wood screw', 'pan head', 252, 'pc', 'F clips 176, K 48, D 22, S 6', 'N', 9.00, 300, True, 'Home Depot', 'buy a 300-pc box'),
 # ---------------- filament ----------------
 ('Filament', 'PLA red', 'skin, studs, corner caps, hopper', red_kg, 'kg', 'F skin (+ K hopper)', 'part', 15.68, 1, False, 'eBay (Parts page price)', 'day-profile estimate; slice before buying'),
 ('Filament', 'PLA (any colour)', 'trays, bins, faces, deck and scoop parts', other_kg, 'kg', 'D, K, S', 'part', 10.00, 1, True, 'Micro Center / Amazon', 'faces in 2 colours + white inlay on the AMS'),
 ('Filament', 'PETG', 'rails, stations, guides, V trays, springs', petg_kg, 'kg', 'D runners, K trays', 'Y', 0, 1, False, '', 'on hand'),
 # ---------------- motion ----------------
 ('Motion', '625ZZ bearing', '5 x 16 x 5', 32, 'pc', 'D 16, K 8, S 8', 'N', 10.00, 50, True, 'AliExpress / Amazon', 'test the 625 pocket coupon first'),
 ('Motion', 'NEMA17 stepper', 'salvaged, 5 mm shaft', 2, 'pc', 'K drum drive, S slide', 'Y', 0, 1, False, '', '2 salvaged from a printer'),
 ('Motion', 'GT2 20T pulley 5 mm bore + 6 mm belt', 'belt 1.3 m', 1, 'kit', 'S slide drive', 'N', 9.00, 1, True, 'Amazon', 'kits come with belt + idler'),
 ('Motion', 'MG996R servo', '', 2, 'pc', 'K scanner doors, S cup tilt', 'Y', 0, 1, False, '', '3 on hand'),
 ('Motion', '24 mm coin vibration motor', '3-5 V', 2, 'pc', 'K V1/V2 trays', 'N', 6.00, 10, True, 'AliExpress / Amazon', 'test one tray first'),
 ('Motion', 'PTFE tape / film', '', 1, 'roll', 'S anti-lift hooks, K thrust ring', 'N', 6.00, 1, True, 'Amazon', 'optional'),
 # ---------------- electronics ----------------
 ('Electronics', 'Raspberry Pi 4B', 'brain', 1, 'pc', 'system', 'Y', 0, 1, False, '', 'V14 plan 2026-11-07: Pi stays the brain'),
 ('Electronics', 'XIAO ESP32-S3 Sense', 'camera', 1, 'pc', 'K scanner 217', 'Y', 0, 1, False, 'Seeed', '2 ordered Nov 5'),
 ('Electronics', 'OV5640 AF camera for XIAO', '', 1, 'pc', 'K scanner', 'Y', 0, 1, False, 'Seeed', 'ordered Nov 5'),
 ('Electronics', 'XIAO ESP32-C3', 'motion/IO board', 1, 'pc', 'K electronics tray', 'Y', 0, 1, False, '', 'on hand'),
 ('Electronics', 'APDS-9960 colour sensor (GY-9960-3.3)', '3.3 V board', 1, 'pc', 'K scanner 218', 'N', 2.00, 1, True, 'AliExpress', 'q28: colour source still open'),
 ('Electronics', 'MCP23017 I2C expander module', '~40 x 25', 3, 'pc', 'D: 1 per drawer (16 reeds); K: 1 on the deck', 'N', 6.19, 3, False, 'AliExpress (Parts page price)', 'set A0-A2 to different addresses: 0x20, 0x21, 0x22'),
 ('Electronics', 'TMC2209 stepper driver', 'BTT V1.3', 3, 'pc', 'K drum, S slide (+1 spare)', 'Y', 0, 1, False, 'Amazon', 'bought Nov 3'),
 ('Electronics', 'DRV8833 motor driver', '', 1, 'pc', 'K vibration motors', 'Y', 0, 1, False, '', 'on hand'),
 ('Electronics', 'Reed switch N/O, glass 2 x 14 mm', '', 18, 'pc', 'D: 1 under each bin + 2 spares', 'N', 4.00, 20, True, 'AliExpress / Amazon', 'glass breaks; bend leads 2 mm from the glass'),
 ('Electronics', 'Neodymium magnet 6 x 2 mm disc', 'N35-N52', 18, 'pc', 'D: 1 in each bin floor + coupon', 'N', 5.00, 50, True, 'Amazon', 'press fit 5.96 hole; CA glue if loose'),
 ('Electronics', 'KW11-3Z roller limit switch', '', 3, 'pc', 'D: 2 drawer-closed interlocks; S: 1 endstop', 'Y', 0, 1, False, 'Temu', '40 on hand'),
 ('Electronics', 'White COB LED strip 12 V, 1 m', 'CRI 90+, 5000-6500 K', 1, 'm', 'K scanner 216: two 70 mm bars cut from it', 'N', 5.00, 1, True, 'AliExpress', 'switched by the MOSFET module'),
 ('Electronics', 'MOSFET trigger module', '', 1, 'pc', 'K LED switch', 'Y', 0, 1, False, '', '2 on hand'),
 # ---------------- power + wiring ----------------
 ('Power + wiring', '12 V PSU', '10 A (or the 20 A ALITOVE)', 1, 'pc', 'K electronics tray 1', 'Y', 0, 1, False, 'Amazon', 'on hand'),
 ('Power + wiring', '12 V to 5 V buck', 'DROK', 1, 'pc', 'K', 'Y', 0, 1, False, '', 'on hand'),
 ('Power + wiring', 'AC cord 16/3', '', 1, 'pc', 'PSU', 'Y', 0, 1, False, '', 'on hand'),
 ('Power + wiring', '4-core flexible cable', '3V3, GND, SDA, SCL', 2, 'm', 'D: drawer to deck, service loop for 150 travel', 'N', 8.00, 5, True, 'Amazon', 'or 4 silicone 22 AWG wires twisted'),
 ('Power + wiring', 'Servo extension lead 3-wire', '', 1, 'm', 'S rolling loop', 'N', 5.00, 1, True, 'Amazon', ''),
 ('Power + wiring', 'Silicone wire 22 AWG kit', '', 1, 'kit', 'reeds to MCP, general', 'Y', 0, 1, False, 'Amazon', 'on hand'),
 ('Power + wiring', 'XT30 connectors', '', 2, 'pair', 'power', 'Y', 0, 1, False, '', 'on hand'),
 # ---------------- fasteners ----------------
 ('Fasteners', 'M3 heat-set insert', '4.1 hole, 5.7 deep', 75, 'pc', 'F 24, K 30, D 20, S 1', 'Y', 0, 1, False, '', 'assortment on hand; count before starting'),
 ('Fasteners', 'M3 x 8 countersunk', '', 20, 'pc', 'F 16, K 4', 'part', 3.00, 60, True, 'AliExpress', 'check the M2-M5 kit first'),
 ('Fasteners', 'M3 x 10 / x 12 socket', '', 60, 'pc', 'K 40, D 20', 'Y', 0, 1, False, 'Amazon', '720-pc M3 kit on hand'),
 ('Fasteners', 'M3 x 12 + nut', '', 24, 'pc', 'K 4, D 12, S 8', 'Y', 0, 1, False, '', 'M3 kit'),
 ('Fasteners', 'M3 x 16 / x 30', '', 5, 'pc', 'D preload jacks 4, S tensioner 1', 'Y', 0, 1, False, '', 'M3 kit'),
 ('Fasteners', 'M5 x 25 + nut/nyloc', '', 17, 'pc', 'D station axles 12, S 5', 'part', 8.00, 50, True, 'Amazon', 'M2-M5 kit may cover some'),
 ('Fasteners', 'M5 x 30 + nyloc', '', 4, 'pc', 'K drum roller axles', 'part', 0, 1, True, '', 'in the M5 pack'),
 ('Fasteners', 'M5 x 50 + nyloc', '', 2, 'pc', 'S top roller axles', 'N', 3.00, 10, True, 'Amazon', ''),
 ('Fasteners', 'M5 x 16 + nut', '', 8, 'pc', 'D guide axles 4, K bracket 4', 'part', 0, 1, True, '', 'in the M5 pack / kit'),
 ('Fasteners', 'M2 x 8 / x 12 + nut', '', 10, 'pc', 'D switch 4, S servo/endstop 6', 'Y', 0, 1, False, '', 'M2-M5 kit'),
]


def main():
    wb = Workbook(); ws = wb.active; ws.title = 'BOM'
    F = 'Arial'; hdr = Font(name=F, bold=True, color='FFFFFF'); fill = PatternFill('solid', fgColor='B71C1C')
    inp = Font(name=F, color='0000FF'); base = Font(name=F); bold = Font(name=F, bold=True)
    thin = Side(style='thin', color='DDDDDD')
    ws['A1'] = 'Bricked Sorting V14 (interface 5.1) bill of materials'; ws['A1'].font = Font(name=F, bold=True, size=14)
    ws['A2'] = ('Blue = editable inputs (qty, owned, prices). "To buy" = what is not on hand. Prices marked approx are typical listings, '
                'not checked; others are what BJ paid (Parts page). Quantities from each module\'s parts.json and the frame cut list.')
    ws['A2'].font = Font(name=F, italic=True, size=9); ws.merge_cells('A2:N2'); ws.row_dimensions[2].height = 28
    ws['A2'].alignment = Alignment(wrap_text=True, vertical='top')
    cols = ['Section', 'Item', 'Spec', 'Qty', 'Unit', 'Where used', 'Owned (Y/N/part)', 'Pack price ($)', 'Pack size', 'Approx', 'Packs to buy', 'Cost to buy ($)', 'Source', 'Note']
    for c, h in enumerate(cols, 1):
        cell = ws.cell(row=4, column=c, value=h); cell.font = hdr; cell.fill = fill; cell.alignment = Alignment(wrap_text=True, vertical='center')
    r = 5
    for sec, item, spec, qty, unit, where, own, price, per, approx, src, note in ROWS:
        vals = [sec, item, spec, qty, unit, where, own, price, per, 'approx' if approx else '', None, None, src, note]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v); cell.font = inp if c in (4, 7, 8, 9) else base
            cell.border = Border(bottom=thin)
        # packs to buy: ceil(qty / pack size) unless owned; continuous units (kg, m) round up too
        ws.cell(row=r, column=11, value=f'=IF(G{r}="Y",0,IF(I{r}>0,ROUNDUP(D{r}/I{r},0),0))').font = base
        ws.cell(row=r, column=12, value=f'=K{r}*H{r}').font = base
        ws.cell(row=r, column=8).number_format = '$#,##0.00;($#,##0.00);-'; ws.cell(row=r, column=12).number_format = '$#,##0.00;($#,##0.00);-'
        r += 1
    last = r - 1
    ws.cell(row=r + 1, column=11, value='Total to buy').font = bold
    ws.cell(row=r + 1, column=12, value=f'=SUM(L5:L{last})').font = bold; ws.cell(row=r + 1, column=12).number_format = '$#,##0.00'
    ws.cell(row=r + 2, column=11, value='by section:').font = base
    secs = []
    for row in ROWS:
        if row[0] not in secs: secs.append(row[0])
    for k, s in enumerate(secs):
        ws.cell(row=r + 3 + k, column=11, value=s).font = base
        c = ws.cell(row=r + 3 + k, column=12, value=f'=SUMIFS(L5:L{last},A5:A{last},K{r + 3 + k})'); c.font = base; c.number_format = '$#,##0.00'
    ws.cell(row=r + 4 + len(secs), column=1, value='Note: "part" owned = partly on hand (count first); the formula still prices one pack. PLA "part": red on hand, buy what the slicer says is missing.').font = Font(name=F, italic=True, size=9)
    widths = [13, 34, 28, 7, 7, 40, 10, 11, 8, 8, 9, 11, 22, 46]
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'C5'; ws.auto_filter.ref = f'A4:N{last}'
    # print summary sheet
    p = wb.create_sheet('Printed')
    p['A1'] = 'Printed parts (day-profile estimate, 45 g/h)'; p['A1'].font = Font(name=F, bold=True, size=14)
    for c, h in enumerate(['Module', 'Branch', 'Grams', 'Hours'], 1):
        cell = p.cell(row=3, column=c, value=h); cell.font = hdr; cell.fill = fill
    mods = [('F frame + skin', 'cad-v14-frame5', G['F'], H['F']), ('K deck', 'cad-v14-deck5', G['K'], H['K']),
            ('D drawers + bins', 'cad-v14-all', G['D'], H['D']), ('S scoop', 'cad-v14-all', G['S'], H['S'])]
    for k, (m, b, g, h) in enumerate(mods):
        for c, v in enumerate([m, b, g, h], 1): p.cell(row=4 + k, column=c, value=v).font = inp if c > 2 else base
    p['A9'] = 'Total'; p['A9'].font = bold; p['C9'] = '=SUM(C4:C7)'; p['D9'] = '=SUM(D4:D7)'
    for c in ('C9', 'D9'): p[c].font = bold
    for rr in range(4, 10): p[f'C{rr}'].number_format = '#,##0'; p[f'D{rr}'].number_format = '0.0'
    p['A10'] = 'Budget (interface 5.1)'; p['C10'] = 9500; p['D10'] = 200; p['C10'].font = inp; p['D10'].font = inp
    p['A11'] = 'Headroom'; p['C11'] = '=C10-C9'; p['D11'] = '=D10-D9'; p['C11'].number_format = '#,##0'; p['D11'].number_format = '0.0'
    for col, w in zip('ABCD', (22, 18, 10, 10)): p.column_dimensions[col].width = w
    out = HERE / 'BOM_V14.xlsx'; wb.save(out)
    # markdown copy for the repo
    md = ['# V14 bill of materials (interface 5.1)', '', 'Generated by `build_bom.py`; the spreadsheet `BOM_V14.xlsx` has the formulas. Owned: Y on hand, N buy, part = check.', '',
          '| Section | Item | Qty | Unit | Where used | Owned | Pack price | Source |', '|---|---|---|---|---|---|---|---|']
    for sec, item, spec, qty, unit, where, own, price, per, approx, src, note in ROWS:
        pr = '' if not price else f'${price:.2f}/{per}' + (' ~' if approx else '')
        md.append(f'| {sec} | {item}{" (" + spec + ")" if spec else ""} | {qty} | {unit} | {where} | {own} | {pr} | {src} |')
    md += ['', f'Printed: {sum(G.values())/1000:.2f} kg, ~{sum(H.values()):.0f} h (F {G["F"]/1000:.2f}, K {G["K"]/1000:.2f}, D {G["D"]/1000:.2f}, S {G["S"]/1000:.2f} kg).']
    (HERE / 'BOM_V14.md').write_text('\n'.join(md) + '\n')
    print(out)


if __name__ == '__main__':
    main()
