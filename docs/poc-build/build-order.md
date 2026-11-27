# Build order and first run

The order across all the guides, then how to bring the machine up for the Dec 2 demo.

## Build order

| # | Step | Guide |
|---|---|---|
| 0 | Read `fit-checks.md`. Buy what `buy-list.md` says is missing. | |
| 1 | **Wood:** front mid rail. Measure between the beam posts (needs 26 3/8 in). | Skin 0, Indicate 0 |
| 2 | **Deck:** centre lines, funnel hole (2 1/4 in). | Isolate 0, Identify 0 |
| 3 | **Under the deck** while the sides are open: scoop beam, carriage, drive, home switch, cup. | Indicate 1–4 |
| 4 | **Drum** unit and drive on the deck. Cut the two trays (4b), then mount them on their springs. | Isolate 1–4b |
| 5 | **Scanner:** funnel, plate with doors and linkage, servo, top parts. | Identify 1–4 |
| 6 | **Back:** bottom keeper bars, then the electronics trays (notched), boards, wiring. Wire the IEC inlet into tile B c1 r3 before that tile goes on. | Skin 2, Electronics 0–5 |
| 7 | **Power-up checks**, then the motion tests below (sides still open, easy to reach). | Electronics 6, below |
| 8 | **Skin:** walls (each wall top down, logo row last), corner caps, access panel, roof halves with the studs. | Skin 1–4 |
| 9 | **Hopper** in the stud, chute block trimmed with the hopper in, deflector. | Isolate 5 |
| 10 | **Containers** on the floor at the POC spacing. | Indicate 5 |
| 11 | First run, below. | |

## Motion tests (no pieces)

Do each on its own, with everything else unpowered.

1. **Drum:** turns smoothly, tire doesn't slip. Drop 5 pieces in the back: they must walk toward the outlet plate. If they walk back, reverse the motor direction in the code.
2. **Scoop:** home slowly toward the hopper end. The carriage stops on the switch with the cup over column 1. Then go to the receive spot (under the funnel) and to each column. Tilt front and back at each.
3. **Trapdoors:** open and close 20 times. They close flat every time.
4. **LEDs** on and off. **Camera** picture shows the whole window, in focus.
5. **Trays** (when the motors and the fix are in): each buzzes on its own without touching anything.

## First run, one piece at a time

1. Put a piece on the closed doors by hand.
2. Take a picture and send it to the server. The website shows the piece and its bin.
3. Scoop to the receive spot, doors open, the piece drops into the cup.
4. Scoop to the bin's column, tilt to the bin's side, back to level.
5. The piece is in the right container and the website count went up by one.

Repeat with 20 mixed pieces. Write down for each: identified right (yes/no), right container (yes/no), seconds from doors to container. These fill the Specification Sheet and Performance slides.

## Full run (after the feed works)

1. Drum on, pour 20 pieces into the hopper. They walk to the outlet and drop out one at a time.
2. Trays carry them to the landing ramp and onto the doors, one at a time.
3. Same loop as above.
4. Count: pieces sorted per minute, jams, wrong bins.

## Demo day

- Website up and reachable on the classroom Wi-Fi; phone or laptop logged in.
- Power cord, spare fuse, the test set of pieces, containers empty.
- Roof half with the hopper lifts off if something jams inside.

## Not ready yet

- Motion code (drum, scoop, doors, trays) is not written.
- The pin map in `electronics.md` is a proposal: confirm with Ethan, Vivek and Marshall.
- Tray fix (Isolate 4b) checked in CAD only; vibration motors not bought.
