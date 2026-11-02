# Indicate (Marshall)

The chute that moves to the right floor and slot and drops the piece into its bin.

## Test the bins with the Live page
1. On the laptop: `pip install pyserial`
2. Upload `arduino/bin_receiver/bin_receiver.ino` to the Arduino. Serial Monitor at 115200, type `1-3`, it should answer `OK 1-3`. Close the Serial Monitor after.
3. Dry run first: `python bridge/bin_bridge.py --dry-run`, then on the Live page press **Start simulator**. Codes print in the terminal.
4. Real run: `python bridge/bin_bridge.py --port COM5` (your port). Each simulated piece now moves the chute.
5. Real camera instead of the simulator: add `--source live`.

## Bin codes
`floor-slot`, like `1-3`. Floor 1 = bottom row (bricks), floor 2 = top row. Slots 1-7 colors, slot 8 unknown color.
Full table: `bin-lookup.csv` / `bin-lookup.json` (generated from `web/data/bins.json`, don't edit by hand).
Send Branden the measured heights (per floor) and angles (per slot) when the hardware exists.
