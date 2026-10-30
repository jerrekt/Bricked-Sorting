Task chart handoff (from Ain't No Waymo, for Bricked Sorting)

For the Claude chat working on Bricked Sorting. This explains how the team task chart on the Ain't No Waymo site works, so it can be copied or simplified. Source: repo jerrekt/Aint-No-WAYmo (public), files kratos/team_tasks.py, team_tasks.json, project_progress.json, and the task board script in Mini_Waymo_V12_Demo.html. Test: tests/test_team_board.py. Read from those files on 2026-10-30. The board has only been run in tests and by BJ's read-only deploy, never with real teammates. Also in Mnemosyne: projects/task-chart-handoff.md.

WHAT THE CHART IS
Two parts on one page:
1. Task board. Tasks grouped by milestone. Each has a status (todo, in_progress, blocked, done) and an owner. 34 seeded tasks across 8 milestones. Filter row, refresh button, re-polls every 15 seconds while open. Anyone can read it. A teammate clicks a task to claim it, mark it done / in progress / blocked, or release it.
2. Progress gauge. project_progress.json lists milestones, each complete or not, with an "evidence" sentence. Percent = completed milestones / total, equally weighted. Rule in its "basis" line: only verified completed milestones count, and a simulation is not proof of working hardware. It is edited by hand; it is not computed from the task board.

HOW THE BOARD WORKS
- Seed file team_tasks.json: schema, version, milestone_labels (id to display name), tasks. Each task: {id, milestone, title, status, owner, detail}. Ids look like scope-01.
- Storage: SQLite (path from WAYMO_TASKS_DB). Table team_tasks plus an audit table team_task_audit (task, actor, action, old status, new status, time). Tasks are inserted with INSERT OR IGNORE, so editing the seed file does NOT change tasks that already exist. New ids are added. To change an existing task, update the database or reset it.
- API (FastAPI): GET /api/tasks (public, no-store), POST /api/tasks/{id}/claim, /status, /release. Body: {name, password}, plus status for status changes.
- Server-side rules: claim only if nobody owns it and it is not done (409 otherwise). Only the owner can change or release it (403). Release resets to todo. A claim sets in_progress. Names are 2 to 70 characters.
- Password: one shared team password in the environment variable WAYMO_TASK_PASSWORD (8 characters minimum). If unset, write endpoints return 503, so the site stays read-only. Compared in constant time after hashing. After 8 wrong tries in 10 minutes from one address it returns 429.
- Front end: plain JavaScript in the page. Calls /api/tasks on the same hostname (no CORS). If the API is unreachable it shows a built-in fallback copy of the tasks and disables editing.

WEAK POINTS TO FIX, NOT COPY
- One shared password for everyone: anyone with it can act as anyone. The name check only stops accidents. Better: individual logins, or Cloudflare Access in front of the write routes.
- The password is sent on every change. Fine over HTTPS. Never put it in the HTML or the repo.
- The rate limit counts by client address. Behind a Cloudflare tunnel that may be the tunnel's address, so one person's wrong tries could lock everyone out. Not tested in the real deployment.
- setup() reads the seed file on every request. Harmless but wasteful.
- No way to add, rename or delete tasks from the page. Changing the list means editing the seed and the database.

THREE OPTIONS FOR BRICKED SORTING (recommendation first)
A. Static chart from a JSON file in the repo, edited by commit.
   Good: no server code, no password, history is git, works on the existing site.
   Bad: teammates edit JSON or ask Claude; no live claiming.
B. Copy the FastAPI and SQLite board.
   Good: live claim and update from the page, audit table included.
   Bad: needs a container, an environment file with a password, a restart policy, and the fixes above.
C. Keep tasks only in Mnemosyne (inbox/todo.md).
   Good: zero setup. Bad: not visible to teammates or the class.

Recommendation: A first, B only if the team really wants to claim tasks live. Confidence: medium. Not known: team size, where its site is hosted, whether teammates will edit anything. Ask BJ.

STEPS FOR OPTION A
1. Make tasks.json in the Bricked Sorting repo, same shape: milestones with labels, tasks with id, milestone, title, status, owner, detail. Owners as first names or roles. Full names stay in private notes, not on a public page.
2. Make progress.json like project_progress.json: milestones, status, and an evidence sentence for each complete one. Percent only from complete milestones.
3. Render both in the site's page with a small script: group by milestone, color by status, filter buttons (copy the filter and redraw functions from the Ain't No Waymo board script).
4. Seed tasks from the project's notes (projects/bricked-sorting.md, bricked-sorting-build.md) and course deadlines. Do not invent tasks, dates or percentages. Ask BJ for anything missing.
5. Branch, preview at desktop and 400 px, merge only when BJ says "push". Bump the version once per merge (decisions/project-standard.md).

STEPS FOR OPTION B (only if BJ picks it)
1. Copy kratos/team_tasks.py and the board script. Point TASKS_SEED at the new seed file and rename the environment variables for the project.
2. Run the tests/test_team_board.py pattern against the copy: wrong password gives 401, duplicate claim 409, a stranger 403, release resets the task.
3. Deploy read-only first (no password set, writes return 503). Confirm the page works. Then set a password in the service's environment file in the container. This is security work: add a note to runbooks/security-review.md and flag it to BJ before building. Use Opus at high effort.
4. Fix the weak points above before turning writes on.

RULES THAT STILL APPLY
Short replies. Never write passwords, tokens or keys. No other people's names on public pages. Mark claims confirmed or unconfirmed. Code goes on a branch and merges only on BJ's "push".
