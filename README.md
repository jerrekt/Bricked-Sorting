# Bricked Sorting

SJSU senior project (Tech 190A). An automated system that feeds, identifies, sorts, and tracks LEGO pieces.

**Workflow:** Isolate → Identify → Indicate

## Folders

| Folder | Owner | What goes here |
|---|---|---|
| `isolate/` | Vivek | Feeder stage: circular vibrator, V1/V2 vibrators, one piece at a time to the inspection spot |
| `identify/` | Ethan | Camera capture, Pi code, Kratos API integration |
| `indicate/` | Marshall | Rotating chute, servo, homing, limit switches, bins |
| `web/` | Branden | Web dashboard |
| `kratos/` | Branden | Classification service, deploy scripts |
| `docs/` | Branden | Slides, BOM, Gantt, diagrams |

Work only in your own folder so changes don't collide.

## How data flows

Camera → Raspberry Pi / controller → Kratos (classification + UI) → Web dashboard
Kratos result → controller → motors and chute

## How to push (no terminal needed)

**Option A: GitHub Desktop**
1. Install GitHub Desktop, sign in, then File → Clone repository → `Jerrekt/bricked-sorting`.
2. Put or edit files in your folder.
3. In GitHub Desktop: write a short summary, click Commit, then Push origin.

**Option B: Browser**
1. Open the repo on github.com and go into your folder.
2. Add file → Upload files (or click a file and use the pencil icon to edit).
3. Write a short commit message and commit.

## Notes
- Add a short `README.md` in your folder: what it does, how to run it, wiring/pins.
- Don't commit passwords, Wi-Fi credentials, or API keys.
