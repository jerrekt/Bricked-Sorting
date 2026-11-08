# Changelog

Site and repo version. One bump per merged pull request (see `tools/bump_version.py`).
It counts updates to this repo, not how finished the machine is; the Tasks page shows that.
V1.001 to V1.014 were numbered afterwards, in merge order.

## V1.030 · 2026-11-07
- Camera tab: team password to watch (checked on CT 150, 12-hour cookie)

## V1.029 · 2026-11-07
- Camera tab: live feed from the Pi camera (via CT 150 /camera-stream, 640 px, 5 fps)

## V1.028 · 2026-11-07
- Live page: click a Recount bin to clear it after pouring it back

## V1.027 · 2026-11-07
- Live page bins fill up like the Demo: piles and fill bars, sized for 3 boxes

## V1.026 · 2026-11-07
- Live page keeps reconnecting until the server answers (it gave up after two tries before)

## V1.025 · 2026-11-07
- Live page centered on Identify and the bins: big camera photo, piece and color match, Identify stats, simulator moved to Testing tools

## V1.024 · 2026-11-07
- Live page: bins show Open and Recount from the bin switches (Pi posts /live/bins)

## V1.023 · 2026-11-07
- Camera in the nav on every page; phone nav in two rows of three

## V1.022 · 2026-11-07
- Camera page (Ethan): status of the Pi camera service, matches the site

## V1.021 · 2026-11-05
- V13 drum: static outlet plate and helical flight, one bearing fewer

## V1.020 · 2026-11-03
- V12 CAD: eight CAD tasks done, extrusion and T-nuts on the buy list

## V1.019 · 2026-11-03
- Team: Vivek is Isolate, code and testing
- Home: compact bin animation (2 rows of 8), wording matches the lift-and-scoop design, social preview tags
- Demo: speed slider reads 16x instead of pcs/s; the first visit runs one box on its own
- Live: says "Machine off" with a plain explanation instead of a connection error
- Footer on every page: GitHub, bja.adsuaracloud.com, changelog, course and instructor

## V1.018 · 2026-11-03
- Buy list: parts grouped by stage with prices, $ to buy per group and totals for the V3 build

## V1.017 · 2026-11-03
- Task board: each bar is now two rows, Sem 1 cardboard POC ending at the checkpoint flag, and Sem 2 final

## V1.016 · 2026-11-03
- Bigger Bricked Sorting logo on the intro on desktop

## V1.015 · 2026-11-03
- Site version in the header of every page, with this changelog (#15)
- Intro animation of our sorter from above: the brick lands on the trapdoors, is identified, the lift goes to floor 1 and the scoop turns to bin 4, the doors open and it slides into the wedge bin (once per visit, tap to skip) (#15)

## V1.014 · 2026-11-03
- Task board: cardboard POC vs final version, checkpoint on every bar, progress card computed from tasks (#14)

## V1.013 · 2026-11-03
- Task board: task sizes and work-weighted progress bars (#13)

## V1.012 · 2026-11-03
- Color groups: move 5 colors a normal color sensor would confuse (#10)

## V1.011 · 2026-11-03
- Task board: 5 groups with progress bars, CAD tasks, finished work marked done (#12)

## V1.010 · 2026-11-03
- Parts page and buy list; /parts and /bought in the claim bot (#11)

## V1.009 · 2026-11-03
- Claim bot: optional Build page parts (bought flags) (#9)

## V1.008 · 2026-11-02
- Live page: camera pieces and simulator drop into bins; Marshall's bin bridge (#8)

## V1.007 · 2026-11-01
- New logo and site icon (#7)

## V1.006 · 2026-11-01
- Claim bot: team and admin names from the env, for a second team (#3)

## V1.005 · 2026-11-01
- register_commands.py: send the DiscordBot user agent (#4)

## V1.004 · 2026-11-01
- README upload steps for a protected main; clean up stale tasks (#6)

## V1.003 · 2026-11-01
- Claim bot: PowerShell version of register_commands (#2)

## V1.002 · 2026-11-01
- Mark repo-05 (branch protection) done (#5)

## V1.001 · 2026-11-01
- Task claim system: live Tasks page, Discord commands, bots container (#1)
