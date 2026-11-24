"""Build the one print folder BJ keeps: Bricked_Sorting_Prints.zip -> Bricked_Sorting_Prints/
Every plate file is renamed P<n>_v<version>_<rest>.3mf from versions.json, plus INDEX.md (plate, version, material,
what it is, change log). When a plate changes: rebuild its .3mf, bump its "v" in versions.json, add a log line, re-run.
Usage: python3 build_print_pack.py OUT_DIR
"""
import json, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = 'Bricked_Sorting_Prints'


def key(f):
    return f.name.split('_', 1)[0]


def main(out_dir):
    ver = json.loads((HERE / 'versions.json').read_text())
    files = sorted(HERE.glob('P*.3mf'))
    groups = {}
    for f in files:
        groups.setdefault(key(f), []).append(f)
    order = sorted(groups, key=lambda k: (int(re.match(r'P(\d+)', k).group(1)), k))
    rows, log = [], []
    out = Path(out_dir) / f'{NAME}.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for k in order:
            v = ver[k]['v']
            mats = sorted({f.name.split('_')[1] for f in groups[k]})
            names = []
            for f in groups[k]:
                nm = f'{k}_v{ver[k].get("file_v", {}).get(f.name, v)}_{f.name.split("_", 1)[1]}'   # done files keep the version printed
                fold = 'done' if f.name in ver[k].get('done_files', []) else ver[k].get('folder', '1_now')
                z.write(f, f'{NAME}/{fold}/{nm}'); names.append(nm)
            rows.append(f'| {k} | v{v} | {ver[k].get("folder", "")} | {"/".join(mats)} | {ver[k]["what"]} | {len(names)} |')
            log += [f'- **{k}** {line}' for line in ver[k]['log']]
        idx = [f'# Bricked Sorting prints', '',
               'One folder for every print. File names: `P<n>_v<version>_<material>_<what>.3mf`.',
               'If a plate number has a higher version than what you printed, check the change log below to see if you need to reprint.', '',
               ver.get('_folders', ''), '', ver.get('_naming', ''), '', '| Plate | Version | Folder | Material | What | Files |', '|---|---|---|---|---|---|'] + rows + ['', '## Change log', ''] + (log or ['- none yet'])
        pl = json.loads((HERE / 'print_log.json').read_text())
        tot = {}
        for e in pl['prints']: tot[e['material']] = tot.get(e['material'], 0) + e['grams']
        idx += ['', '## Filament used', '', f'**Total: {sum(tot.values())} g** (' + ', '.join(f'{m} {g} g' for m, g in sorted(tot.items())) + f") over {sum(e.get('hours', 0) for e in pl['prints']):.0f} h of printing", '',
                pl['_note'], '', '| When | Bambu job | h | Plate | Ver | Material | g | Status | Parts / note |', '|---|---|---|---|---|---|---|---|---|']
        idx += [f"| {e['date']} | {e.get('bambu_job', '')} | {e.get('hours', '')} | {e['plate']} | v{e['version']} | {e['material']} | {e['grams']} ({e['source']}) | {e.get('status', 'done')} | {', '.join(e['parts'])}{' (' + e['note'] + ')' if e['note'] else ''} |" for e in pl['prints']]
        parts = HERE / 'P14-P18_parts.md'
        if parts.exists():
            idx += ['', '---', '', parts.read_text()]
        z.writestr(f'{NAME}/INDEX.md', '\n'.join(idx) + '\n')
        import os
        pv = os.environ.get('PREVIEWS_DIR')          # rendered by make_previews.py (PNGs are not kept on cad-v14-all)
        if pv:
            for png in sorted(Path(pv).glob('*.png')):
                z.write(png, f'{NAME}/previews/{png.name}')
        if (HERE / 'print_status.json').exists():   # the website Prints page reads this from the prints branch
            z.write(HERE / 'print_status.json', f'{NAME}/status.json')
    print(out, len(files), 'files')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
