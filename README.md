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

## How to add files (no terminal needed)

`main` is protected: nobody, Branden included, can change it directly. Every change is a **pull request (PR)** that Branden merges. Once merged, it's live within a minute.

**Browser (easiest)**
1. Get added as a collaborator: send Branden your GitHub username, then accept the invite email.
2. Open the repo, go into **your folder**.
3. **Add file → Upload files**, or open a file and click the **pencil** to edit.
4. Write a short note (like `Isolate: feeder sketch v1`). Keep **"Create a new branch and start a pull request"** selected, then **Propose changes → Create pull request**.
5. Tell Branden in Discord.

**GitHub Desktop**
1. File → Clone repository → `jerrekt/Bricked-Sorting`.
2. **Current branch → New branch** (name it after what you're doing).
3. Edit files in your folder, write a summary, **Commit**, then **Publish branch**.
4. Click **Create Pull Request** and tell Branden.

Never upload passwords, keys, tokens, Wi-Fi logins or IP addresses: this repo is public.

## Tasks
The task board is at bricked-01.adsuaracloud.com/tasks.html. Update your tasks from the team Discord: `/mytasks`, `/claim`, `/start`, `/blocked`, `/done`, `/release` (or the buttons on the Tasks page with the team password). Every change posts in #tasks. Code: `kratos/claim-bot`.

## Website
- `web/` is the public site (bricked-01.adsuaracloud.com): landing page plus a simulated demo dashboard.
- It deploys itself: CT 150 pulls `main` every 60 seconds. Anything merged to `main` goes live within a minute.
- Bin codes and color groups: `docs/bin-system.md` and `web/data/bins.json`.
- Team task chart: `web/tasks.html`. Titles, details and due dates live in `web/data/tasks.json` (change by PR); owners and statuses change live through the claim bot.
- `deploy/` holds the server setup. Changes there do not auto-deploy; they are installed by hand.

## Notes
- Add a short `README.md` in your folder: what it does, how to run it, wiring/pins.
- Don't commit passwords, Wi-Fi credentials, or API keys.
