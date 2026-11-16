"""Every print STL must be ONE solid (BJ 2026-11-16: the scoop beam plug, cup stub, carriage flag and idler arms were
loose bodies that would have printed as separate pieces). Drawer-face ink inlays (*_ink) are many letters by design.
Usage: python3 check_bodies.py [files...]   (default: every print STL in all modules). Exit 1 if any part is in pieces."""
import glob, os, sys
import trimesh
ROOTS = ['/home/claude/wt_frame5/cad/v14/frame/print', '/home/claude/wt_deck5/cad/v14/deck/print',
         '/home/claude/wt_all/cad/v14/drawer/print', '/home/claude/wt_all/cad/v14/scoop/print', '/home/claude/wt_all/cad/v14/plates/v13_reuse']
files = sys.argv[1:] or sorted(f for r in ROOTS for f in glob.glob(r + '/*.stl'))
bad = []
for f in files:
    if '_ink' in os.path.basename(f):
        continue
    n = len([p for p in trimesh.load(f).split(only_watertight=False) if p.volume > 1.0])
    if n != 1:
        bad.append((n, f))
for n, f in bad:
    print(f'{n} pieces: {f}')
print(f'{len(files)} files, {len(bad)} in pieces')
sys.exit(1 if bad else 0)
