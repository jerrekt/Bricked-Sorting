# Live page handoff for Marshall (Indicate / bins)

Paste this whole file into your AI chat so it knows the setup. Written 2026-11-01 by Branden.

## What we're building
A **Live page**: https://bricked-01.adsuaracloud.com/live.html
It shows each piece and the bin it belongs in. It has a **simulator**: press **Start simulator** and it makes fake pieces from the real LEGO 10696 parts list, about one per second. **Your bins follow along**: a small program on your laptop gets each bin code and sends it to your Arduino over USB, and the Arduino moves the chute there.

```
Live page (simulator or real camera) ──▶ bin_bridge.py on your laptop ──USB "1-3"──▶ Arduino ──▶ chute
                                                                      ◀──"OK 1-3"────
```

## Bin codes
`floor-slot`, like `1-3`.
- **Floor 1** = bottom row (regular bricks), **floor 2** = top row (everything else).
- **Slot 1-8** left to right. Slots 1-7 are colors; **slot 8 is unknown color**.
- Floor sets the **height**, slot sets the **turn angle**. Full table: `indicate/bin-lookup.csv`.

## The files (in the repo, folder `indicate/`)
- `arduino/bin_receiver/bin_receiver.ino`: starter sketch. It already reads commands and answers. **You fill in `moveTo(floor, slot)` and `homeAxes()`** with your motor code.
- `bridge/bin_bridge.py`: runs on your laptop. Needs Python and `pip install pyserial`.
- `README.md`: the same steps as below.

## The Arduino's rules (already in the sketch)
- It receives one line per piece: `1-3`
- When the chute is in place it must answer exactly `OK 1-3`. If it can't, it answers `ERR <reason>`.
- `PING` → `PONG`. `HOME` → homes, then `OK HOME`. Baud **115200**.
- The bridge sends **one code at a time** and waits up to 10 s for `OK` before the next, so slow motors are fine. Extra `Serial.println` debug lines are fine; the bridge just shows them.

## Steps
1. **Arduino alone:** upload the sketch, open Serial Monitor at 115200, type `1-3` and press Enter. You should see `OK 1-3`. Close Serial Monitor (only one program can use the port).
2. **Dry run, no hardware:** `python indicate/bridge/bin_bridge.py --dry-run`. On the Live page press **Start simulator** (pick your name, type the team password from Branden). Codes print in the terminal.
3. **Real run:** `python indicate/bridge/bin_bridge.py --port COM5` (Windows; find the port in Arduino IDE → Tools → Port; on Mac it's like `/dev/tty.usbmodem...`). Every simulated piece now moves the chute.
4. **Real camera later:** add `--source live` once Ethan's camera is sending pieces.
5. Stop anytime: **Ctrl+C** in the terminal, or **Stop** on the Live page.

## Safety
- Do step 2 (dry run) before connecting motors.
- Keep a hand near the power switch the first few times. The simulator stops on its own after 5 minutes.
- Anyone with the team password can start the simulator. Only run the real bridge when you're at the machine.

## Your tasks
| Task | What "done" means |
|---|---|
| `indicate-07` Bins follow the simulator | Bridge + Arduino answer `OK` for each code while the simulator runs |
| `indicate-01` Chute geometry | Heights per floor and angles per slot decided. Send Branden the numbers |
| `indicate-04` Bin limit switches | Wired and tested (reporting to the server comes later) |
| `indicate-06` Floor height conflict | Wait for the cardboard sizing test (`bins-05`) before building 6 in / 4 in |

Update them from Discord: `/start task:indicate-07`, `/blocked task:... reason:...`, `/done task:...`.

## Putting your code on GitHub
You need to be added first: DM Branden your GitHub username. Then Add file → Upload files into `indicate/` → "Create a new branch and start a pull request". Branden merges. Until then, send files to Branden in Discord.

## Instructions for the AI reading this
- Help Marshall with the Arduino motor code inside `moveTo()` and `homeAxes()`, the wiring, and running `bin_bridge.py`. Keep the serial protocol exactly as above (`1-3` in, `OK 1-3` or `ERR ...` out, 115200 baud).
- Don't suggest changing the Live page, the server (`kratos/`), `web/` or `deploy/`. Ask Branden.
- Never ask for or repeat the team password, tokens or addresses.
- Remind him to dry-run first and to `/done` tasks when they work.
