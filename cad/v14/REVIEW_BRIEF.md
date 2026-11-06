# Bricked Sorting V14: design brief for an outside review

You are reviewing a mechanical design with another AI (Claude). BJ, the team lead, will pass your replies back and forth. Be concrete: numbers, failure modes, what you would change and why. Disagree where you think we are wrong.

## The project
SJSU Tech 190A senior project, team of 4 (one person does all CAD and printing). A desktop machine that sorts **one box of medium LEGO bricks (LEGO Classic 10696, 484 pieces, about 1 L loose), maybe a bit more**, into 16 bins by color and by brick vs non-brick. Bricks are fed **a handful at a time**, not the whole box at once. Semester 1 (due Dec 2) is a rough cardboard proof of concept; semester 2 is this printed machine.

Hard constraints:
- **Max 30 in tall** (a couple of inches over is OK). Footprint 1040 x 520 mm (41 x 20.5 in), shaped like a giant 2x1 LEGO brick with two 312 mm studs on the roof.
- **Fully 3D printed** structure (no aluminum extrusion, no metal drawer slides). Printer bed 256 mm (design to 248). Bought parts only: electronics, motors, servos, switches, LEDs, 625ZZ bearings, a GT2 belt and pulleys, screws and heat-set inserts.
- Cheap, uses parts already owned: two salvaged NEMA17s, 3x TMC2209, MG996R servos, XIAO ESP32-S3 Sense (camera), XIAO ESP32-C3, MCP23017, KW11-3Z switches, APDS-9960 color sensor, DRV8833 for vibration motors. Image classification runs on a home server.

## Current V14 layout (coordinates in mm; origin floor center, +X right, +Y front, +Z up)
- **Lower brick (z 0..390):** one drawer with 16 open bins (108 x 150 footprint, 150 tall) in two rows of 8 (bin centers x = -406 + 116 i, rows y = ±150). The drawer pulls out 490 mm on 2-stage telescoping printed runners so the back row clears the front. Above the bins (z 186..366), a printed beam at y = 0 spans the width; a carriage on 625 bearings rides it, driven by a NEMA17 + GT2 belt, homed on an endstop. A servo on the carriage tilts the scoop toward the back or front row.
- **Deck brick (z 390..720):** drum, vibration trays, scanner, electronics. The scanner drops each brick through a hole in the deck at (330, 0) into the scoop.
- **Drum, as built now (V13):** 160 OD x 180 long barrel on 4 roller wheels (625 bearings), friction-driven by a NEMA17 with a TPU tire. Inside: one triangular helical flight, pitch 90 mm, 1.75 turns, pushes bricks to the outlet. The outlet end plate is **static** (bolted to the frame) with an outlet window at the bottom and a lip so pieces only leave when the spiral delivers them. Axis runs front-to-back; a hopper in the left roof stud feeds the drum's rear end.
- **Trays:** V1 (long, slower) and V2 (short, faster) vibration trays with coin vibration motors carry pieces from the drum outlet to the scanner. The speed step between them pulls clumps apart. **Decided: keep two trays.**
- **Scanner:** landing ramp, two servo trapdoors, camera above, LED bar, color sensor. One piece at a time.

## The open question
Since pieces are fed a handful at a time, the drum does not need to hold the whole box. Two options:

**A. Short drum 140 OD x 150.** One print (~4.5 h), holds ~0.6 L at ~30 % fill. Layout stays as above, drop point stays at (330, 0).

**B. Long drum ~120-130 OD x ~550 along X**, spanning under both roof studs. Hopper at the left stud feeds the left end; the outlet is at the right end; V1 then V2 run back toward -X along the front to the scanner. Holds ~1.5 L, sits lower, gives a longer spiral path and gentler feed. Costs: prints in 3 bolted sections (spiral must line up at the joints), needs 3 roller stations, moves the scanner and drop point, and the scoop and deck designs change mid-build.

Claude's current lean: A, because the capacity B adds is not needed. BJ is considering B.

## What we want from you
1. A or B (or something else), and why. Address jamming of long pieces (2x8 plates are 64 mm), fill level vs tumbling, singulation quality at the scanner, print and assembly risk.
2. Anything in the layout you think will fail first: the 490 mm printed telescoping drawer with ~10 kg of bins, the printed beam and carriage, the scoop dumping into bins 116 mm apart while staying above z 186, frame racking, vibration-tray tuning.
3. Simpler ways to hit the same goals with the parts listed.
Keep the answer under about 600 words; we will go a few rounds.

## Follow-up sent to ChatGPT: the old scoop (Z lift + yaw) vs the new slide
Until V13 the bins were reached differently. **Old design (V3 carriage, V10-V13):** 16 bins in **two stacked tiers of 8**, each tier a ring of wedge-shaped bins around a central lift. A NEMA17 with a T8 lead screw raised a carriage on two 12 mm rods (236 mm of travel between the tiers); on top, a second NEMA17 yawed a hub carrying an open scoop that tipped the brick into one of 8 bins (45 deg apart). Two drawers, one per tier. That made the lower half 624 mm tall and the whole machine 1248 mm plus studs (about 54 in).
**New design (V14):** one tier of 16 bins in two straight rows, scoop on a belt-driven X slide plus a servo tilt, one drawer. Chosen to get under 30 in while keeping 16 bins in the 1040 x 520 footprint. A single ring of 16 around a yaw would need a ~700 mm circle (a 1040 x 1040 footprint) or ~39 mm bin mouths if squeezed into 520.
Question: is there a way to keep the Z + yaw approach (already designed and partly understood) within 30 in and 16 bins, e.g. two shallow tiers, a smaller-radius ring with taller narrow bins, or yaw + short radial reach? Compare it with the slide on accuracy, speed, part count, print risk and what can go wrong.
