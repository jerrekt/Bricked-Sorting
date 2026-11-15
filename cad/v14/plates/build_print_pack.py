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
                nm = f'{k}_v{v}_{f.name.split("_", 1)[1]}'
                z.write(f, f'{NAME}/{nm}'); names.append(nm)
            rows.append(f'| {k} | v{v} | {"/".join(mats)} | {ver[k]["what"]} | {len(names)} |')
            log += [f'- **{k}** {line}' for line in ver[k]['log']]
        idx = [f'# Bricked Sorting prints', '',
               'One folder for every print. File names: `P<n>_v<version>_<material>_<what>.3mf`.',
               'If a plate number has a higher version than what you printed, check the change log below to see if you need to reprint.', '',
               '| Plate | Version | Material | What | Files |', '|---|---|---|---|---|'] + rows + ['', '## Change log', ''] + (log or ['- none yet'])
        parts = HERE / 'P14-P18_parts.md'
        if parts.exists():
            idx += ['', '---', '', parts.read_text()]
        z.writestr(f'{NAME}/INDEX.md', '\n'.join(idx) + '\n')
    print(out, len(files), 'files')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
