# Chat C: Bricked Sorting claim system + Discord bot

**Model:** Opus 5.5 high. This adds a server, a secret and a public write path to a box teammates can log into. Switch to Sonnet medium only for the page layout. Stop BJ and tell him when to switch.

## First message to paste in the new chat
> Read this handoff. Attach jerrekt/Bricked-Sorting (with push) and jerrekt/mnemosyne. The task chart is already built and static. I want teammates to claim tasks and a Discord bot. Before building anything, give me the plan and wait for my yes. Put the reply header (Mnemosyne version, time, commit) on every reply. Short replies.

## Who / rules
- BJ = Branden Adsuara, lead and integrator of Bricked Sorting (SJSU Tech 190A, Team 5). GitHub: jerrekt. Teammates: Ethan (Identify), Vivek (Isolate), Marshall (Indicate). **They do not use GitHub.** They use Discord.
- Short direct replies. Ask before expensive builds. Code goes on a branch with a preview (desktop and 400px); merge only when BJ says "push". Notes can go straight to Mnemosyne main.
- On Mnemosyne / Bricked Sorting work, start each reply with `Mnemosyne vX.XXX · date time PT · commit <hash>`. Read the current version from the vault (it was v1.020 on Oct 24) and bump it per reply.
- Never write passwords, tokens, bot tokens, webhook URLs, public keys' private halves, real IPs or real hostnames in the repo, PRs, the vault's public notes, or chat. If BJ pastes a secret, tell him to rotate it.
- The repo is **public**. Teammates appear by first name only on the site. Real IPs and hostnames go only in Mnemosyne `private/`.
- Log changes in Mnemosyne `inbox/changes.yaml` (read `# next id` first; single-quoted values, double any apostrophe). Questions for BJ go in `inbox/questions.yaml`. Security work gets a note in `runbooks/security-review.md` BEFORE building. Validate with `python3 tests/check_vault.py`. Don't pipe checks into `tail` before a `&&` push.
- Claude can't reach BJ's servers. Give commands, ask for pasted output, don't claim success first.

## What already exists (Bricked-Sorting repo, main, last commit `1e559fe`)
- **Static task chart**: `web/tasks.html`, `web/assets/tasks.js` (74 lines), `web/data/tasks.json`, `web/data/progress.json`. No backend. Edited by pull request. Handoff reasoning: `docs/task-chart-handoff.md`.
- **41 tasks** in 8 milestones (repo, bins, isolate, identify, indicate, dashboard, hardware, course). Status now: 10 done, 6 in progress, 6 blocked, 19 todo. Owners: Branden 22, Marshall 10, Ethan 6, Vivek 2, All 1. Some tasks have a `due` date (Deadlines panel shows non-done ones). Task shape: `{id, milestone, title, status, owner, detail, due?}`; status is `todo | in_progress | blocked | done`.
- Progress gauge: completed milestones / 8 (only `repo` is complete), edited by hand, not computed from tasks.
- The tasks.json note says: when a feature is added, add a task, and update the BOM sheet and slide deck (hw-04, course-04).
- **Hosting**: public site at bricked-01.adsuaracloud.com, nginx on **CT 150** (Kratos), Cloudflare tunnel. A root-owned `/usr/local/sbin` script pulls `main` every 60 s as user `bricksite` and **only serves static files in `web/`**; pushes can't change the script or nginx config. So backend code is NOT deployed by that pull. See `deploy/` and Mnemosyne `runbooks/bricked-sorting-site.md`.
- **CT 150 is shared**: it also runs the inference server/dashboard (`/opt/brickbase-dashboard`, Ethan's). Ethan has a password SSH login over Tailscale and scoped Proxmox access; whether he gets sudo is an open question (q24). **Assume Ethan can read anything on CT 150 that isn't locked down**, so don't put a bot token or password in a file he could read. Consider a separate container instead.
- A teammate once "nuked the website with Cloudflare"; the tunnel ran on a different machine. Avoid depending on that tunnel for anything that must survive.

## What BJ wants now
1. **Claim system**: teammates claim a task, mark in progress / blocked / done, release it, without GitHub.
2. **Discord bot**: they do it from Discord; the team sees activity in a channel.
(Not decided: whether the website also gets claim buttons. Ask BJ.)

## Recommended design (ask BJ to confirm; confidence: medium)
**Discord-first.** The weak point of the Ain't No Waymo board is one shared password that lets anyone act as anyone. Discord solves it: a slash command arrives signed and carries the user's Discord ID.
- Map Discord user ID -> teammate name once (BJ provides). `/claim task:identify-02`, `/done`, `/blocked reason:...`, `/release`, `/mytasks`, `/tasks`. Only the owner can change or release their task; BJ can override.
- Prefer **HTTP interactions** (Discord POSTs to an endpoint, you verify the Ed25519 signature) over a bot with a gateway connection: no bot token to store, no long-lived process, works through a tunnel. A bot token is only needed if the bot must read messages or post on its own; a webhook URL covers one-way posts to a channel.
- Backend: small FastAPI + SQLite service (adapt Ain't No Waymo's `kratos/team_tasks.py` and `kratos/team_updates.py`, public repo jerrekt/Aint-No-WAYmo). The page reads `GET /api/tasks`.
- **Source of truth rule (learned today):** keep `tasks.json` as the seed for titles, details, due dates, milestones, and new tasks; store only `owner` and `status` as an overlay in SQLite keyed by task id, and merge on read. Do NOT copy the Waymo `INSERT OR IGNORE` approach: edits to the seed never reached existing rows, so the live site showed stale data until we served the file directly.
- Decide how the overlay gets back into `tasks.json` (periodic PR by BJ, or a `/export` command). Without that, git and the live board drift apart.
- Static fallback: if the API is down, `tasks.js` should show `tasks.json` read-only, as it does now.

## Security items to settle before building (Opus high; write to `runbooks/security-review.md` first)
- Where it runs (separate unprivileged container preferred over CT 150) and as which user; secrets in a root-only env file read by systemd (`EnvironmentFile`), never in the repo.
- Verify Discord's Ed25519 signature on every request and reject stale timestamps; ignore the request otherwise.
- Allow-list of Discord user IDs; per-user and global rate limits; clean/length-limit all text; Discord messages with `allowed_mentions: {"parse": []}` so task text can't ping @everyone.
- If the website gets write buttons too, key rate limits on `CF-Connecting-IP` (not the tunnel's address) and use an opt-in env flag so a password alone can't turn writes on.
- An audit table (task, discord id, action, old and new status, time).
- Backend deploys are by hand (the 60 s pull doesn't touch them). If BJ wants auto-pull for the backend, copy the Waymo design: root-owned script in `/usr/local/sbin`, ff-only, syntax check, rollback. That's a separate decision.

## Lessons from Ain't No Waymo (same pattern, already live there)
- GitHub: REST only through the proxy (`gh api`); GraphQL and settings writes are blocked. Create PRs with a JSON file and `--input`. Shallow clones need `git remote set-branches --add origin <branch>` before pushing a new branch.
- Branch protection: BJ must enable `main` protection on this repo himself (task `repo-05`, still todo; the repo is public and auto-deploys). Ruleset worked there: PR required, 0 approvals, no force push.
- Rate limit by `CF-Connecting-IP`. Run the board test in a venv with fastapi, pydantic, httpx.
- Test live with one real Discord message before calling it working; ask BJ to paste the output.
- Add a task to `tasks.json` for each piece built (claim API, bot, security review) and update the BOM sheet and slide deck per hw-04 and course-04 if the feature touches them. Keep the word "password" out of public task text.

## First steps for the new chat
1. Read Mnemosyne `README.md`, `CONVENTIONS.md`, `projects/bricked-sorting-build.md`, `runbooks/bricked-sorting-site.md`, `inbox/todo.md`, `projects/task-chart-handoff.md`. Read the repo's `docs/task-chart-handoff.md`.
2. Ask BJ: (a) Discord-only, or also buttons on the site? (b) separate container or CT 150? (c) one-way channel feed only, or full slash commands? (d) Discord IDs of Ethan, Marshall, Vivek, himself (names only in the vault's private notes).
3. Write the plan and the security-review entry. Wait for his yes. Then build on a branch, test with a fake Discord client, preview, and merge on "push".
