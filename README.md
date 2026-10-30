# Bricked Sorting

SJSU senior project (Tech 190A). An automated system that feeds, identifies, sorts, and tracks LEGO pieces.

**Workflow:** Isolate → Identify → Indicate

## Folders

| Folder | Owner | What goes here |
|---|---|---|
| `isolate/` | Vivek | Feeder stage: circular vibrator, V1/V2 vibrators, one piece at a time to the inspection spot |
| `identify/` | Ethan | Camera capture and Pi code for identifying pieces |
| `indicate/` | Marshall | Rotating chute, servo, homing, limit switches, bins |
| `web/` | Branden | Web dashboard |
| `kratos/` | Branden | Kratos server: classification service and its API |
| `docs/` | Marshall | Slides, reports, Gantt, diagrams |

Work only in your own folder so changes don't collide. Branden (lead) helps across every folder and owns the Kratos server and the website.

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

## Website
- `web/` is the public site (bricked-01.adsuaracloud.com): landing page plus a simulated demo dashboard.
- It deploys itself: CT 150 pulls `main` every 60 seconds. Anything merged to `main` goes live within a minute.
- Bin codes and color groups: `docs/bin-system.md` and `web/data/bins.json`.
- Team task chart (not built yet): `docs/task-chart-handoff.md` covers how to add one, based on the Ain't No Waymo project's board.
- `deploy/` holds the server setup. Changes there do not auto-deploy; they are installed by hand.

## Notes
- Add a short `README.md` in your folder: what it does, how to run it, wiring/pins.
- Don't commit passwords, Wi-Fi credentials, or API keys.
