// Bricked Sorting: Tech 190A written report (due 2026-12-01). Run: node build_report.js
const fs = require('fs'), path = require('path');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType,
  ImageRun, PageBreak, TableOfContents, LevelFormat, BorderStyle, Footer, PageNumber, Header } = require('docx');
const HERE = __dirname, META = JSON.parse(fs.readFileSync(path.join(HERE, 'img/meta.json')));
const FONT = 'Arial';
let figN = 0, tabN = 0; const figs = [], tabs = [];

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 22, ...o });
// inline: **bold** and [[placeholder]] markup
function runs(text, o = {}) {
  const out = []; const re = /(\*\*[^*]+\*\*|\[\[[^\]]+\]\])/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(run(text.slice(last, m.index), o));
    const tok = m[0];
    if (tok.startsWith('**')) out.push(run(tok.slice(2, -2), { ...o, bold: true }));
    else out.push(run('[' + tok.slice(2, -2) + ']', { ...o, bold: true, highlight: 'yellow' }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(run(text.slice(last), o));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 140, line: 288 }, ...o });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })], pageBreakBefore: true });
const H1n = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const H3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: FONT })] });
const B = t => new Paragraph({ numbering: { reference: 'bul', level: 0 }, children: runs(t), spacing: { after: 70, line: 276 } });
const N = t => new Paragraph({ numbering: { reference: 'num', level: 0 }, children: runs(t), spacing: { after: 70, line: 276 } });
const TODO = t => new Paragraph({ children: [run('[' + t + ']', { bold: true, highlight: 'yellow' })], spacing: { after: 140 } });

function fig(name, caption, maxW = 624, maxH = 700) {
  const [w, h] = META[name]; let W = maxW, Hh = Math.round(h * W / w);
  if (Hh > maxH) { Hh = maxH; W = Math.round(w * Hh / h); }
  figN++; figs.push(`Figure ${figN}. ${caption}`);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: 'jpg', data: fs.readFileSync(path.join(HERE, 'img', name + '.jpg')), transformation: { width: W, height: Hh },
        altText: { title: caption, description: caption, name } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [run(`Figure ${figN}. `, { bold: true, size: 20 }), run(caption, { size: 20 })] }),
  ];
}
// placeholder for a real photo
function photo(caption, what) {
  figN++; figs.push(`Figure ${figN}. ${caption}`);
  const b = { style: BorderStyle.DASHED, size: 8, color: '999999' };
  return [
    new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows: [new TableRow({ height: { value: 2200, rule: 'atLeast' }, children: [
      new TableCell({ width: { size: 9360, type: WidthType.DXA }, borders: { top: b, bottom: b, left: b, right: b }, verticalAlign: 'center',
        shading: { type: ShadingType.CLEAR, fill: 'FFF9D6' }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run('[INSERT PHOTO: ' + what + ']', { bold: true, highlight: 'yellow' })] })] })] })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: [run(`Figure ${figN}. `, { bold: true, size: 20 }), run(caption, { size: 20 })] }),
  ];
}
function table(caption, widths, rows, o = {}) {
  tabN++; tabs.push(`Table ${tabN}. ${caption}`);
  const total = widths.reduce((a, b) => a + b, 0); const sz = o.size || 19;
  const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' }; const borders = { top: bd, bottom: bd, left: bd, right: bd };
  const trs = rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((c, j) => new TableCell({
    width: { size: widths[j], type: WidthType.DXA }, borders, margins: { top: 50, bottom: 50, left: 90, right: 90 },
    shading: i === 0 ? { type: ShadingType.CLEAR, fill: 'B71C1C' } : (i % 2 === 0 ? { type: ShadingType.CLEAR, fill: 'F6F6F6' } : undefined),
    children: [new Paragraph({ children: runs(String(c), { size: sz, ...(i === 0 ? { bold: true, color: 'FFFFFF' } : {}) }) })] })) }));
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 }, children: [run(`Table ${tabN}. `, { bold: true, size: 20 }), run(caption, { size: 20 })] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: trs }),
    new Paragraph({ spacing: { after: 160 }, children: [] }),
  ];
}
function code(caption, lines) {
  figN++; figs.push(`Figure ${figN}. ${caption}`);
  const bd = { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' };
  return [
    new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows: [new TableRow({ children: [new TableCell({
      width: { size: 9360, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd }, shading: { type: ShadingType.CLEAR, fill: 'F4F4F4' },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: lines.split('\n').map(l => new Paragraph({ spacing: { after: 0, line: 228 }, children: [new TextRun({ text: l.replace(/ /g, ' ') || ' ', font: 'Consolas', size: 15 })] })) })] })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: [run(`Figure ${figN}. `, { bold: true, size: 20 }), run(caption, { size: 20 })] }),
  ];
}

const body = [];
const add = (...x) => x.flat().forEach(e => body.push(e));

// ------------------------------------------------------------------ front matter
const title = [
  new Paragraph({ spacing: { before: 2400 }, alignment: AlignmentType.CENTER, children: [run('Bricked Sorting', { size: 64, bold: true, color: 'B71C1C' })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [run('An Artificial-Intelligence LEGO Sorter That Keeps Count', { size: 32 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 900 }, children: [run('Senior Project I: Written Technical Report', { size: 26, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('Branden Jerrick Adsuara', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('Vivek Goorla', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('Ethan Roche', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 900 }, children: [run('Marshall Wong', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('San José State University', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('Department of Aviation and Technology', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('TECH 190A, Section 01: Senior Project I, Fall 2026', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run('Instructor: Vlad Ionescu', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [run('December 1, 2026', { size: 24 })] }),
];

add(H1('Abstract'));
add(P('Loose LEGO pieces are slow to collect, sort and recount by hand. Bricked Sorting is a tabletop machine that sorts a mixed pile of LEGO pieces into 16 bins by type and color group and keeps a running count of every bin on a website. The machine works in three stages. Isolate uses a rotating drum and two vibrating trays to feed one piece at a time. Identify photographs each piece with a camera on a Raspberry Pi and sends the picture to a server that names the piece and its color. Indicate drops the piece into a scoop that slides to the correct bin. The final design is a 720 mm by 360 mm by 664 mm machine shaped like a red LEGO brick, built from a wood frame with 3D-printed mechanisms and a printed skin. During the first semester the team designed the complete machine in computer-aided design (CAD), printed 3.6 kg of parts in 95 hours of printing, and built the website and the identification service. As of November 22, 2026, identification runs from the camera to the live website and the bin-open detection works. The estimated value of the parts in one machine is about $330, against a target of $250 to $300. [[TEAM: add the measured sorting accuracy and speed from the proof-of-concept test once it is run.]]'));
add(P('**Keywords:** LEGO sorting, computer vision, image classification, Raspberry Pi, vibratory feeder, 3D printing, inventory tracking.'));

add(H1('Acknowledgements'));
add(P('The team thanks Vlad Ionescu, instructor of TECH 190A, for the guidance that turned the first proposals into a project that solves a real problem, and the Department of Aviation and Technology at San José State University for the course and facilities.'));
add(P('The piece identification in this project relies on Brickognize, a free image-recognition service for LEGO parts. The identification server, the website and the camera relay run on a home server owned by Branden Adsuara, who also supplied the 3D printer and many of the electronic parts that were already on hand. The Industrial Design students who joined the October 7 design sprint contributed early sketches of the enclosure.'));
add(TODO('TEAM: add anyone else who helped, for example people who lent tools, parts or LEGO.'));

add(H1('Table of Contents'));
add(new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-2' }));
add(P('Note for the editor: in Microsoft Word, right-click the table of contents and choose Update Field so the page numbers appear.', { }));

const LIST_SLOT = body.length;   // lists of figures and tables go here later

add(H1('Nomenclature'));
add(...table('Terms used in this report', [2400, 6960], [
  ['Term', 'Meaning'],
  ['Isolate', 'The first stage. It separates a pile of pieces so that one piece at a time reaches the camera.'],
  ['Identify', 'The second stage. A camera and a server decide what the piece is and which color group it belongs to.'],
  ['Indicate', 'The third stage. It moves the piece to the bin that matches the result from Identify.'],
  ['Bin code', 'The name of a bin, written floor-slot. Bin 1-3 is floor 1 (bricks), slot 3 (green).'],
  ['Brick / other', 'The two type groups. "Brick" means a plain rectangular brick or plate. "Other" means every other piece.'],
  ['CAD', 'Computer-aided design: the 3D computer model of every part of the machine.'],
  ['Deck', 'The plywood shelf in the middle of the machine. The Isolate and Identify stages sit on it.'],
  ['Scoop', 'The tilting cup that carries one piece from under the scanner to its bin.'],
  ['Stud', 'One of the two round bumps on top of the machine. Pieces are poured into the left stud.'],
  ['PLA / PETG / TPU', 'Three 3D-printing plastics: polylactic acid (stiff, easy to print), polyethylene terephthalate glycol (tougher), and thermoplastic polyurethane (rubber-like).'],
  ['Raspberry Pi', 'A small, low-cost computer. A Raspberry Pi 4B is the controller inside the machine.'],
  ['Kratos', 'The team name for the home server that runs the identification service and the website.'],
  ['Brickognize', 'An online service that names a LEGO piece from a photograph.'],
  ['POC', 'Proof of concept: the simplified first-semester build that shows the three stages working together.'],
  ['BOM', 'Bill of materials: the list of every part needed to build the machine.'],
  ['NEMA17', 'A standard size of stepper motor, a motor that turns in small exact steps.'],
  ['Servo', 'A small motor that turns to a commanded angle and holds it.'],
]));

// ------------------------------------------------------------------ executive summary
add(H1('Executive Summary'));
add(H2('The problem'));
add(P('A family or hobbyist with a large LEGO collection usually keeps it as one mixed pile. Finding a specific piece in a mixed pile is slow, sorting the pile by hand is slower, and nobody knows whether pieces have gone missing. Existing phone applications can recognize pieces in a photograph but cannot move them. The one commercial sorting service found during benchmarking is an industrial process run at the company\'s own site, not a product that sits in a home.'));
add(H2('The solution'));
add(P('Bricked Sorting is a tabletop machine shaped like a large red LEGO brick. The user pours pieces into the stud on top. Inside, three stages handle each piece:'));
add(N('**Isolate.** A rotating drum and two vibrating trays spread the pile out and release one piece at a time.'));
add(N('**Identify.** A camera photographs the piece. A server names the piece and its color and returns a bin code.'));
add(N('**Indicate.** Two trapdoors open and the piece drops into a scoop. The scoop slides along a beam to the correct position and tips the piece into one of 16 bins.'));
add(P('A website shows each piece as it is identified, the count in every bin, and which bins have been opened. Because the machine counts every piece, it can tell the user what is in the collection and, later, what is missing.'));
add(...fig('still_1_machine', 'The final machine in CAD: a 2x1 LEGO brick at large scale, with the hopper in the left stud and one drawer of eight bins on each long side.', 500));
add(H2('What has been done'));
add(B('The complete final machine was designed in CAD as four modules and checked by software for collisions between parts.'));
add(B('Every 3D-printed part needed for the proof of concept was printed: 3.6 kg of plastic in 39 print jobs and about 95 hours of printing between November 8 and November 22, 2026.'));
add(B('The identification chain works from the camera to the website, including over the wireless network used at the class presentation.'));
add(B('The website has seven pages: an overview, an animated demonstration, a live view, the camera, a team task board, a parts list and a print tracker.'));
add(B('The parts in one machine have an estimated value of about $330.'));
add(H2('What remains'));
add(B('Build the wood frame and assemble the stages on it (scheduled for the week of November 23).'));
add(B('Write the motion control that turns each bin code into a trapdoor, slide and tilt movement.'));
add(B('Measure identification accuracy, sorting accuracy and speed against the specification. [[TEAM: update this list on November 30.]]'));
add(B('Second semester: the red skin walls, the two drawers with a switch under each bin, and the inventory functions of the website.'));

// ------------------------------------------------------------------ introduction
add(H1('1. Introduction'));
add(H2('1.1 Background'));
add(P('LEGO is one of the most widely owned toys in the world, and the amount of it in homes keeps growing. The LEGO Group reported that consumer sales grew 16 percent in 2025 and that revenue rose 12 percent to DKK 83.5 billion [1]. Sets are sold sorted, in numbered bags, but after the first build most households store all of their sets together. The LEGO Classic 10696 box used as the test set in this project contains 484 pieces in more than 30 colors [8]; a typical collection holds many such boxes.'));
add(P('Three problems follow from the mixed pile, and they are the problems named in the project pitch of October 6, 2026:'));
add(B('**Collecting.** Pieces end up on the floor and are tedious to pick up.'));
add(B('**Sorting.** Storage boxes with compartments only help if somebody sorts the pieces first, and manual sorting is slow and repetitive.'));
add(B('**Recounting.** Nobody knows how many pieces of each kind there are, or whether a set is still complete.'));
add(P('The intended users are parents, children and adult builders: people who want to find a piece quickly, not people who run a resale business. That choice drives the design. The machine has to be affordable, small enough for a desk, safe to leave in a living room, and simple enough that a new user can operate it with minimal instructions.'));
add(H2('1.2 History of the project'));
add(P('The team is four students: one from manufacturing (Branden Adsuara) and three from computer science (Vivek Goorla, Ethan Roche and Marshall Wong). The course requires that the project solve a real problem and include artificial intelligence.'));
add(P('Two earlier proposals were rejected before the LEGO sorter was chosen. An automated garden irrigation system was rejected because it did not solve a clear enough problem. A measuring station that scanned an object and generated a custom packaging insert was rejected as too costly. The second proposal on the team\'s list, originally a quality-inspection idea built around a camera, was reworked into the LEGO sorter and approved. The name Bricked Sorting and the three-stage structure were set in the pitch.'));
add(...fig('pitch-03', 'The first sketch of the system from the October 6 pitch: a hopper and bowl for Isolate, a camera for Identify, and a chute over stacked bins for Indicate.', 520));
add(...fig('pitch-02', 'The form factor proposed in the pitch: a half-round enclosure with 16 wedge-shaped bins on two floors, fed by a lead-screw lift and a turning chute.', 520));
add(H2('1.3 Functional specification'));
add(P('The pitch set measurable targets for the finished product. They are repeated in Table 2 with the current status of each. The targets have not been changed during the semester. Section 5 reports results against them.'));
add(...table('Functional specification from the pitch, with status on November 22, 2026', [1500, 2700, 2300, 2860], [
  ['Category', 'Planned specification', 'Measure of success', 'Status'],
  ['Identification', 'Camera and AI identify the color and type of each piece', 'At least 85% identification accuracy', 'Working from camera to website. Accuracy not yet measured. [[TEAM: add result]]'],
  ['Sorting', 'A mechanism sends each piece to the correct bin', 'At least 90% correct sorting', 'Mechanism printed. Not yet assembled or measured. [[TEAM: add result]]'],
  ['Processing speed', 'One piece at a time', '5 to 10 pieces per minute', 'Not yet measured. [[TEAM: add result]]'],
  ['Connectivity', 'Raspberry Pi communicates over Wi-Fi or Ethernet', 'Stable connection for at least 30 minutes', 'Worked over Wi-Fi at the class presentation. Timed run not yet done.'],
  ['Dashboard', 'Website shows color, piece type, confidence and bin', 'Information updates within 3 seconds', 'Live page built and receiving pieces. Delay not yet timed.'],
  ['Color recognition', 'Detects major LEGO color groups', 'At least 8 color categories', '7 color groups plus an "unknown" bin per floor (Table 4).'],
  ['Categories', '16 bins: 8 brick and 8 non-brick', 'Pieces placed in the assigned category', 'Bin table defined and shared by the server, website and controller.'],
  ['Security', 'Password-protected controls', 'Unauthorized users cannot use the controls', 'Done: controls and the camera page require the team password.'],
  ['Usability', 'Simple loading area and labeled bins', 'A new user can operate it with minimal instructions', 'Pieces are poured into one stud; every bin has a code. User test not yet done.'],
  ['Size', 'Compact tabletop design', 'Fits on a standard desk or workbench', '720 x 360 mm footprint, 664 mm tall.'],
  ['Weight', 'Light enough to move', 'Below 30 lb (13.6 kg)', 'Printed parts are about 3.6 kg so far. Whole machine not yet weighed.'],
  ['Reliability', 'Operates without overheating', 'Runs for at least 30 minutes without failure', 'Not yet tested.'],
  ['Cost', 'Affordable unit', '$250 to $300 per unit', 'About $330 value of parts (Section 3.6): about 10% over the target.'],
], { size: 17 }));
add(H2('1.4 State-of-the-art review (benchmarking)'));
add(P('The benchmarking from the pitch compared Bricked Sorting with phone applications and with one sorting service. It has been updated with published figures and two well-documented hobby machines.'));
add(B('**Brickit** is a phone application. The user spreads pieces out, the camera recognizes them, and the application suggests models that can be built and shows where each piece is in the pile. It does not move or store pieces [5].'));
add(B('**Brickognize** is a recognition service for single LEGO parts, described in a 2023 paper that trains on photo-realistic rendered images because real labeled photographs are scarce [6]. It names a piece from one photograph. Bricked Sorting uses it as the recognition engine [7].'));
add(B('**Sort A Brick** is a company in Lithuania that sorts customers\' used bricks back into complete sets. Its conveyor separates pieces, identifies each one in a recognition chamber and is reported to process about 1,000 parts per hour with more than 99 percent precision across more than 25,000 distinct bricks [2]. It is an industrial service performed at the company\'s site.'));
add(B('**The Universal LEGO Sorting Machine** by Daniel West (2019) is a hobby machine built from about 10,000 LEGO elements. A Raspberry Pi runs a neural network trained on rendered 3D images, and the machine sorts about one brick every two seconds [3].'));
add(B('**Jacques Mattheij\'s sorter** (2017) used a hopper, two conveyor belts, a camera and timed puffs of air to sort two metric tons of LEGO for resale. The author reported that feeding pieces one at a time from a hopper was the hard part because pieces jam across the opening, and that the classifier needed about 20,000 labeled images [4].'));
add(...table('Benchmarking, updated from the pitch', [1700, 1500, 1700, 1800, 2660], [
  ['Feature', 'Phone apps (Brickit, Brickognize)', 'Sort A Brick', 'Hobby machines (West, Mattheij)', 'Bricked Sorting'],
  ['Identifies pieces', 'Yes', 'Yes', 'Yes', 'Yes, through Brickognize'],
  ['Physically sorts', 'No', 'Yes', 'Yes', 'Yes, into 16 bins'],
  ['Keeps a count of the collection', 'Partly (a scan of one pile)', 'For one order', 'No', 'Yes: a count per bin on the website'],
  ['Speed', 'Scanning only', 'About 1,000 pieces per hour [2]', 'About 1,800 per hour (one every 2 s) [3]', 'Target 300 to 600 per hour (5 to 10 per minute)'],
  ['Cost to the user', 'Free', 'Paid service', 'Not for sale', 'Target $250 to $300'],
  ['Where it is used', 'At home', 'At the company', 'The builder\'s workshop', 'At home, on a desk'],
  ['Intended user', 'Hobbyists', 'People returning old LEGO to sets', 'The builder', 'Families and builders'],
], { size: 17 }));
add(P('The review shows a gap. Recognition is solved well enough to use as a service, and industrial sorting exists, but there is no home product that both sorts and keeps count. The two hobby machines also gave two warnings that shaped the design: feeding one piece at a time is the hardest mechanical problem, and training a recognition model from nothing takes more labeled data than a four-person team can produce in a semester.'));

// ------------------------------------------------------------------ solution
add(H1('2. The Solution'));
add(H2('2.1 Overview'));
add(P('The final machine is 720 mm long, 360 mm deep and 664 mm tall including the two 50 mm studs on top. The proportions are those of a real 2x1 LEGO brick. Inside, a plywood deck divides the machine into two levels. Isolate and Identify sit on the deck. Indicate hangs under the deck, above two drawers that each hold eight bins. Figure 4 shows each stage on its own.'));
add(...fig('stages', 'The wood frame with one stage highlighted at a time, seen from the front: (1) frame, (2) Isolate, (3) Identify, (4) Indicate, (5) electronics, (6) everything with the roof and studs.'));
add(...fig('still_2_inside', 'The complete machine in CAD with the skin and roof removed.', 520));
add(H2('2.2 How a piece moves through the machine'));
add(N('The user pours pieces into the **hopper**, a funnel that sits inside the left stud. A chute carries them into the back of the drum.'));
add(N('The **drum** is a barrel that turns slowly on four bearing rollers, driven by a stepper motor through a rubber tire. A spiral rib inside the drum moves pieces toward the open front, where a fixed plate lets only a few pieces out at a time.'));
add(N('Pieces fall onto the first **vibrating tray** and then the second. Each tray sits on flat printed springs and is shaken by a small vibration motor. The trays are tilted about 4.5 degrees, so pieces walk forward and spread into a single line.'));
add(N('One piece lands on the **scanner plate**, on top of two closed trapdoors, under a camera and two strips of white lights.'));
add(N('The **Raspberry Pi** takes a picture and sends it to the server. The server asks Brickognize what the piece is, decides brick or other and the color group, and returns a bin code such as 1-3.'));
add(N('A servo opens the **trapdoors**. The piece drops through a funnel in the deck into the **scoop**, which is waiting underneath.'));
add(N('A stepper motor and belt slide the scoop along a beam to one of eight positions. A servo tips the scoop toward the front or the back, and the piece slides into its **bin**.'));
add(N('The website adds one to the count for that bin and shows the piece on the Live page.'));
add(H2('2.3 The bins'));
add(P('There are 16 bins in two groups of eight. One group holds plain rectangular bricks and plates. The other holds every other kind of piece: tiles, slopes, round pieces, wheels and so on. Within each group, slots 1 to 7 are color groups and slot 8 catches any color the system cannot place. The color groups were chosen from the inventory of one LEGO Classic 10696 box, so that the largest groups in a real box each get a bin; one box puts 149 pieces in the brick group and 335 in the other group.'));
add(...table('Bin slots and color groups (the same for both floors)', [900, 2200, 6260], [
  ['Slot', 'Color group', 'Shades merged into the group (set 10696)'],
  ['1', 'Red / Orange', 'Red, Dark Red, Orange, Dark Orange'],
  ['2', 'Yellow', 'Yellow, Bright Light Yellow, Bright Light Orange'],
  ['3', 'Green / Lime', 'Green, Bright Green, Dark Green, Lime, Yellowish Green'],
  ['4', 'Blue / Azure', 'Blue, Dark Blue, Dark Azure, Medium Azure, Dark Purple'],
  ['5', 'Pink / Purple', 'Bright Pink, Dark Pink, Magenta, Medium Lavender'],
  ['6', 'Black / Dark Gray', 'Black, Dark Bluish Gray, Dark Brown'],
  ['7', 'White / Light Gray', 'White, Light Bluish Gray, Light Aqua, Lavender'],
  ['8', 'Unknown', 'Tan, Reddish Brown, all transparent colors, anything the camera cannot place'],
]));
add(P('Sorting is coarse on purpose. A machine that tried to give every one of the thousands of LEGO part shapes its own bin would be far larger and more expensive, and a camera confuses similar shades. Sixteen bins answer the question a builder actually asks: "where are the blue bricks?"'));
add(H2('2.4 Isolate'));
add(...fig('deck_drum', 'Isolate in CAD: the hopper and chute (red), the drum on its cradles, and the outlet plate over the first vibrating tray.', 500));
add(P('Isolate is owned by Vivek Goorla. The hopper holds about 0.9 liters. The drum, its rollers, the drive hub and the friction tire were designed in an earlier version of the project and carried into the final design unchanged because they had already been drawn and checked. New cradles hold the drum on the deck.'));
add(H2('2.5 Identify'));
add(...fig('deck_scanner', 'Identify in CAD: the scanner plate on legs over the deck hole, the two trapdoors and their servo, and the camera bridge above.', 500));
add(P('Identify is owned by Ethan Roche. The camera is a Logitech USB webcam connected to the Raspberry Pi 4B. The Pi does not run the recognition itself. It sends each picture over a private network (Tailscale) to a container on the home server, and the server calls the Brickognize service. This keeps the computer inside the machine cheap and lets the team improve the rules on the server without touching the machine. An APDS-9960 color sensor has a mount on the scanner as a second way to read color; whether it is needed is still an open question, because the color name returned by Brickognize may be enough.'));
add(H2('2.6 Indicate'));
add(...fig('scoop_receive', 'Indicate in CAD: the scoop waiting under the deck funnel. The beam runs the length of the machine above the two rows of bins.', 500));
add(...fig('scoop_dump', 'The scoop tipped 40 degrees to drop a piece into a front bin.', 500));
add(P('Indicate is owned by Marshall Wong. The scoop is a shallow cup, open at both ends, on a carriage that rolls on eight small bearings along a hollow printed beam. A stepper motor and a toothed belt move the carriage. A servo tips the cup 40 degrees forward or backward through a pushrod. The cup floor has a soft rubber-like pad so that pieces land quietly and do not bounce out. A limit switch at one end tells the controller where the carriage is when the machine starts.'));
add(H2('2.7 Electronics'));
add(...fig('deck_elec', 'The electronics trays in CAD: the 12 V power supply with a cover over its mains terminals, and the Raspberry Pi. Every tray has a 10 mm grid of holes so that boards can be moved.', 500));
add(P('A 12 V, 10 A power supply feeds two stepper drivers (TMC2209), the lights and a converter that makes 5 V for the Raspberry Pi and the servos. A small motor driver (DRV8833) runs the two vibration motors. The trays sit on the deck at the back of the machine, behind a removable panel.'));
add(H2('2.8 User interface and experience'));
add(P('The user needs to do three things: pour pieces in, watch the website, and pull out a bin. There are no buttons on the machine for sorting choices. The website is the control panel (Section 2.9).'));
add(P('One design decision is worth recording. A teammate proposed a "take out" button with which the user scans each piece removed from a bin, so the inventory stays exact. The team lead argued that this is too slow for parents and children. The compromise is two modes: a simple mode in which opening a bin just marks it for a recount, and an advanced mode for users who want to scan every piece they take.'));
add(P('The recount idea works like this. A switch under each bin notices when the bin is lifted out. An opened bin means somebody took pieces, so its count can no longer be trusted. The website marks that bin "Recount". The user pours only that bin back through the machine, and the count is correct again without re-sorting the whole collection.'));
add(H2('2.9 The website: which functions are completed through the application'));
add(P('The application is a website, https://bricked-01.adsuaracloud.com, so it works on a phone, tablet or computer with nothing to install. The pages are plain files served from the project\'s code repository; a change approved in the repository appears on the site about one minute later. A small server program behind the site holds the live state.'));
add(...table('Website pages and the functions each one performs', [1500, 4660, 3200], [
  ['Page', 'Functions', 'Status on November 22'],
  ['About', 'Explains the product and the three stages, shows the team and the bin codes, and shows how the machine goes together.', 'Live'],
  ['Demo', 'An animated simulation of a full sort of the 484-piece test set, with speed control and simple and advanced views. Lets anyone try the product without the machine.', 'Live'],
  ['Live', 'Shows the piece being identified, the match confidence, the bin it is going to and the count and fill level of all 16 bins. Shows which bins are open and which need a recount. Password-protected buttons start and stop the simulator, reset all counts, and mark one bin as emptied.', 'Live; receives pieces from the camera'],
  ['Camera', 'Shows the picture from the machine\'s camera at about five frames per second, behind the team password.', 'Live'],
  ['Tasks', 'The team task board: every task, its owner and status, progress toward each semester, and course deadlines. Team members claim tasks from the team chat (Discord).', 'Live'],
  ['Parts', 'The list of parts to buy, three build options with their cost, and what is already on hand.', 'Live'],
  ['Prints', 'Every 3D-printed part with a picture, its printed size, material, and whether it has been printed; filament used and its cost.', 'Live'],
  ['Inventory (planned)', '"Count Everything" to set the collection total, "Add New LEGO" to add a box, and "Find What\'s Missing" to re-sort only the opened bins and compare every bin with the total.', 'Rules written; not built'],
], { size: 17 }));
add(...fig('web_about', 'The About page: what the product does and the three stages.'));
add(...fig('web_live', 'The Live page: the current piece, the 16 bins with their counts, and the state of the bin switches.'));
add(...fig('web_demo', 'The Demo page: a simulated sort that anyone can run.'));
add(...fig('web_prints', 'The Prints page: filament used, cost, and print progress. The total shown includes the lid of the vacuum canister.'));
add(...fig('web_tasks', 'The Tasks page: progress, deadlines and the team task board.'));
add(TODO('TEAM (Ethan / Marshall): add any hand sketches or wireframes of the dashboard made before the site was built.'));

add(H2('2.10 Code and how it affects the product'));
add(P('The project code is in one repository, github.com/jerrekt/Bricked-Sorting. Five short pieces are shown here because each one decides something the user can see.'));
add(H3('Deciding brick or other'));
add(...code('From classify.py on the identification server: the rule that decides the floor.',
`MIN_CONF = 50.0   # shape: below this, don't trust a "Brick" ID; treat as OTHER

_PLAIN_BRICK = re.compile(r"^(brick|plate) \\d+ x \\d+( x \\d+)?$")

def choose_shape(name, confidence=None):
    """BRICK only for a plain rectangular brick or plate. Curved, special, modified,
    round, sloped, tiles, technic, printed and anything unknown are OTHER."""
    if not name:
        return "OTHER"
    if confidence is not None:
        c = confidence * 100 if confidence <= 1.0 else confidence
        if c < MIN_CONF:
            return "OTHER"
    n = re.sub(r"\\s+", " ", name.lower().replace(",", " ")).strip()
    return "BRICK" if _PLAIN_BRICK.match(n) else "OTHER"`));
add(P('Brickognize returns a name such as "Brick 2 x 4" and a confidence. This function reduces that to one of two groups. A piece goes to the brick floor only when the name is exactly a plain brick or plate with its size and the service is at least 50 percent confident. Everything else, including anything the service is unsure about, goes to the other floor. The effect for the user is that the brick bins stay clean: a doubtful piece is never put among the bricks. Plates were added to the rule on November 18 after the team decided that plain plates belong with bricks. [[TEAM (Ethan): confirm this matches the version running on the server, and that the color groups in the server code match Table 4.]]'));
add(H3('Sending the camera picture'));
add(...code('From camera_push.py on the Raspberry Pi: the loop that sends pictures to the server.',
`while True:
    started = time.time()
    try:
        jpg = session.get(SNAP, timeout=3)
        jpg.raise_for_status()
        r = session.post(PUSH_URL, data=jpg.content,
                         headers={"Content-Type": "image/jpeg"}, timeout=5)
        r.raise_for_status()
        watchers = int(r.json().get("watchers", 0))
        failing_since = None
    except (requests.RequestException, ValueError) as e:
        watchers = 0
        failing_since = failing_since or started
    wait = (1.0 / FPS) if watchers else IDLE_EVERY
    time.sleep(max(0.05, wait - (time.time() - started)))`));
add(P('The server cannot open a connection to the machine, so the machine pushes pictures to the server. The loop sends five pictures per second while somebody has the Camera page open and one every five seconds otherwise. This keeps network use low and lets the page show correctly whether the machine is online. If the network drops, the loop keeps trying and recovers by itself, which is what the 30-minute connectivity target requires.'));
add(H3('Recounting one bin'));
add(...code('From live.py on the website server: what happens when a user marks a bin as emptied.',
`elif act == "recounted":
    # One bin was poured back into the hopper: clear its Recount flag and zero its
    # count, so the pieces are counted again. Other bins keep their counts.
    code = body.code.strip().upper()
    if not BIN_CODE.match(code):
        raise HTTPException(400, "bin codes look like 1-3 (or F3 / B3)")
    with HUB.lock:
        if code in HUB.open:
            raise HTTPException(409, f"Bin {code} is still open. Put it back first.")
        HUB.recount.discard(code)
        HUB.counts["live"].pop(code, None)
        HUB.counts["sim"].pop(code, None)
        HUB.bins_rev += 1`));
add(P('This is the recount function described in Section 2.8. It refuses a bin that is still out of the machine, then sets only that bin\'s count to zero. The counts of the other 15 bins are untouched, which is what makes a partial recount possible.'));
add(H3('Checking the CAD before printing'));
add(...code('From build_integration.py: every part is tested against every other part for overlap.',
`def clash(A, B, thr=0.5):
    hits = []
    bb = [(n, s, bbox(s)) for n, s in B]
    for n, s in A:
        b = bbox(s)
        for m, t, bt in bb:
            if _ov(b, bt):
                v = s.intersect(t); vol = v.val().Volume() if v.vals() else 0
                if vol > thr: hits.append([n, m, round(vol, 1)])
    return hits`));
add(...code('From check_bodies.py: every print file must be one solid piece.',
`for f in files:
    n = len([p for p in trimesh.load(f).split(only_watertight=False) if p.volume > 1.0])
    if n != 1:
        bad.append((n, f))
print(f'{len(files)} files, {len(bad)} in pieces')`));
add(P('These two checks affect the product indirectly: they are why the printed parts fit. The first reports any two parts that occupy the same space by more than 0.5 cubic millimeters, with the scoop tested at every one of its positions. The second catches a part that would print as two loose pieces. Section 5.4 describes the defect that led to the second check.'));
add(TODO('TEAM (Marshall): when the motion control is written, add a snapshot of the code that turns a bin code into the slide position and tilt direction.'));

// ------------------------------------------------------------------ methodology
add(H1('3. Design and Manufacturing Methodology'));
add(H2('3.1 Three stages, three owners'));
add(P('The work was split so that each stage has one owner and a fixed interface to the next stage: Isolate hands over one piece, Identify hands over one bin code, Indicate delivers the piece. The reason is practical. Three of the four team members are programmers who had not built a machine before. A stage with a clear input and output can be developed and tested alone, so nobody has to understand the whole system to make progress. The team lead owns the interfaces, the CAD, the printing, the wiring and the website, and helps wherever a stage is stuck.'));
add(H2('3.2 Why these methods were chosen and others were not'));
add(...table('Main design decisions and the alternatives considered', [1700, 2500, 2500, 2660], [
  ['Decision', 'Chosen', 'Alternatives not chosen', 'Reason'],
  ['Recognition', 'Brickognize service called from a server', 'Training a neural network; a classifier on the Raspberry Pi', 'Published sorters needed tens of thousands of labeled images [4] or millions of renders [3]. The service already knows the parts, and the server rules can change without touching the machine.'],
  ['Number of bins', '16: brick or other, by 8 color groups', 'One bin per part shape', 'Matches how builders look for pieces, keeps the machine desk-sized, and tolerates camera confusion between similar shades.'],
  ['Feeding', 'Rotating drum, then two vibrating trays', 'Circular vibrating bowl (pitch); conveyor belt from a hopper', 'A hopper feeding a belt jams [4]. The drum meters the flow and the trays spread it. A bowl feeder needs a tuned track for each part shape.'],
  ['Moving the piece to a bin', 'Scoop sliding on a belt-driven beam, tilting to two rows', 'Lead-screw lift with a turning chute over wedge bins on two floors (pitch); air jets beside a belt [4]', 'One straight axis and one tilt replace a lift and a rotation. The bins become simple boxes in two drawers. Air jets need a compressor, which is too loud and costly for a home.'],
  ['Structure', 'Wood frame with a thin printed skin', 'Fully 3D-printed body', 'The fully printed design came to about 25 kg of plastic and 550 hours of printing. Wood needs only straight cuts and cut the printed mass to about 8.5 kg.'],
  ['Size', '720 x 360 x 664 mm, one 2x1 brick', '1040 x 520 mm body, two stacked bricks (earlier version)', 'Fits a desk, and every part fits the 256 mm bed of the printer.'],
  ['Controller and camera', 'Raspberry Pi 4B with a USB webcam', 'ESP32 camera board (XIAO ESP32-S3 Sense) with a second ESP32 for the motors', 'The ESP32 boards would cut cost, but the Raspberry Pi and webcam were on hand and the identification code already ran on the Pi. The cheaper boards are set aside until the machine works.'],
  ['Counting opened bins', 'A switch under each bin; recount only the opened bin', 'Scanning every piece taken out', 'Scanning each piece is too slow for families. Kept as an optional advanced mode.'],
  ['Fasteners', 'Three wood-screw sizes and M3 machine screws into heat-set inserts', 'A different fastener for each joint', 'An early count reached more than eight fastener types. Fewer types mean fewer purchases and fewer assembly mistakes.'],
], { size: 16 }));
add(H2('3.3 Design method: CAD as code, one interface file'));
add(P('Every part was modeled with CadQuery, a tool in which a part is written as a short program instead of drawn by hand. All four modules (frame, deck, drawers and scoop) read their shared dimensions from a single interface file. When a shared dimension changes, each module is rebuilt from the same numbers, so the modules cannot drift apart. The interface went through five major versions during the semester; version 5.1, dated November 6, is the one built.'));
add(P('Each module delivers the same set of outputs: the parts in machine position for the collision check, the parts laid flat for printing, a list of parts with estimated plastic and print time, and still pictures. The integration check then loads all modules together.'));
add(H2('3.4 Manufacturing method'));
add(H3('Wood frame'));
add(P('The frame is four 2x2 posts, 1x2 rails and two pieces of half-inch plywood. Every cut is a straight crosscut, and the hardware store cuts the plywood. The frame carries all the loads; the printed skin only covers it. Figure 21 is the build sheet used for the frame.'));
add(...fig('wood_plan', 'The wood-frame build sheet: views, cut list, the roof cross rails and the deck plywood.', 624, 760));
add(H3('3D printing'));
add(P('All printed parts were made on one Bambu Lab P2S printer with a 0.4 mm nozzle and 0.2 mm layers. Three rules were applied to every part, because the printer usually runs unattended overnight or during work hours:'));
add(B('**No supports.** Every part has a flat face on the bed, overhangs no steeper than 45 degrees and short bridges. Sideways holes have a teardrop-shaped top so they print cleanly.'));
add(B('**One solid body.** Each file is checked by software to be a single piece.'));
add(B('**Fits come from test prints, not from guesses.** Small test pieces were printed first and the clearances that worked were written down and reused (Table 8).'));
add(...table('Material selection', [1900, 2600, 4860], [
  ['Material', 'Used for', 'Reason'],
  ['PETG (black)', 'Mechanisms: drum cradles, trays and springs, scanner, scoop beam, carriage, brackets, electronics trays', 'Tougher and less brittle than PLA, tolerates the warmth near motors, and flexes without cracking in the leaf springs.'],
  ['PLA (red)', 'Visible parts: studs, hopper, chute, roof tiles; later the wall skin and corner caps', 'Lowest cost ($9.99 per kg), prints flat and accurately in large thin tiles, and gives the LEGO color.'],
  ['PLA (other colors)', 'Roof clips, calibration pieces, drum parts printed earlier', 'The clip slots were sized from PLA test prints.'],
  ['TPU 95A', 'Drum friction tire, scoop cup pad', 'Rubber-like: grips the drum and quiets the landing of a piece.'],
  ['Wood (pine 2x2, 1x2; half-inch plywood)', 'Frame, floor and deck', 'Cheap, stiff, and needs only straight cuts.'],
]));
add(...table('Print settings and measured fits', [3600, 5760], [
  ['Item', 'Value used'],
  ['Layer height, nozzle', '0.2 mm, 0.4 mm'],
  ['Walls', '4 wall loops'],
  ['Nozzle temperature', 'PLA 205 °C; PETG 237 °C'],
  ['Hole for an M3 heat-set insert', '4.3 mm in PLA; 4.4 mm in PETG'],
  ['Hole for a 5 mm axle (push fit) in PETG', '5.1 mm'],
  ['Sliding fit in PETG', '0.20 mm clearance per side'],
  ['Dovetail and clip fit in PLA', '0.065 to 0.07 mm clearance per side'],
  ['Pocket for a 625 bearing (16 mm outside diameter)', '16.1 mm'],
]));
add(H2('3.5 Components'));
add(P('Figures 22 to 25 show every printed part of the proof of concept as modeled, with its material and printed size. Photographs of the real parts follow.'));
add(...fig('parts_frame', 'Printed parts of the frame module: studs, roof tiles and clips.'));
add(...fig('parts_drum', 'Printed parts of the drum.'));
add(...fig('parts_deck', 'Printed parts of the deck module: hopper, chute, trays, scanner and electronics trays.', 624, 780));
add(...fig('parts_scoop', 'Printed parts of the scoop module.'));
add(...photo('The printed parts of the proof of concept laid out.', 'all printed parts on a table, grouped by stage'));
add(...photo('The roof tiles and both studs assembled, with the hopper in the left stud.', 'roof with studs and hopper'));
add(...photo('The wood frame.', 'finished wood frame, front view'));
add(...photo('Isolate on the deck: drum and vibrating trays.', 'drum, cradles and trays mounted'));
add(...photo('Identify: scanner plate, trapdoors and camera.', 'scanner with the webcam and lights'));
add(...photo('Indicate: the scoop on its beam.', 'scoop beam, carriage and cup under the deck'));
add(...photo('Electronics: power supply, Raspberry Pi and motor drivers.', 'wired electronics trays'));
add(...photo('The assembled proof of concept.', 'whole machine, the picture used for the presentation'));
add(H2('3.6 Bill of materials and cost analysis'));
add(P('The pitch budget priced one unit at $300.63 at retail prices and $179.69 at bulk prices. The budget has been replaced by a bill of materials generated from the CAD, which counts what the design actually uses. Cost is reported as "value used": the quantity in the machine multiplied by a typical price for one, not the price of whole packs. Parts the team already owned are included at their value, because a unit built by someone else would have to buy them.'));
add(...table('Value of the parts in one finished machine, by section', [3000, 1800, 4560], [
  ['Section', 'Value used', 'Main items'],
  ['Wood', '$46.66', 'One 2x2, three 1x2, one plywood panel, wood screws'],
  ['Filament', '$80.72', 'About 8.5 kg of printed parts in the finished machine, by CAD estimate'],
  ['Motion', '$56.60', '2 stepper motors, 2 servos, 32 bearings, belt and pulley, 2 vibration motors'],
  ['Electronics', '$93.00', 'Raspberry Pi 4B, 3 stepper drivers, motor driver, switches, lights'],
  ['Power and wiring', '$38.00', '12 V supply, 5 V converter, mains cord, cable and connectors'],
  ['Fasteners', '$15.49', 'Heat-set inserts and machine screws'],
  ['**Total, finished machine**', '**$330.47**', 'Before sales tax. Excludes the USB webcam [[TEAM: add its value]]'],
  ['Proof of concept only', 'About $280', 'Without the wall skin, drawers, bins and their switches'],
  ['Vacuum attachment (optional)', '$22.28', 'About 2 kg of filament and its screws (Section 6)'],
]));
add(...table('Itemized bill of materials: bought and reused components', [2900, 700, 1100, 1100, 3560], [
  ['Item', 'Qty', 'Unit value', 'Value', 'Used in'],
  ['Raspberry Pi 4B', '1', '$55.00', '$55.00', 'Controller'],
  ['Logitech USB webcam', '1', '[[add]]', '[[add]]', 'Identify: camera'],
  ['NEMA17 stepper motor (reused)', '2', '$12.00', '$24.00', 'Drum drive; scoop slide'],
  ['TMC2209 stepper driver', '3', '$6.00', '$18.00', 'Two motors and one spare'],
  ['MG996R servo', '2', '$5.00', '$10.00', 'Trapdoors; scoop tilt'],
  ['625ZZ bearing', '32', '$0.50', '$16.00', 'Drum rollers, scoop carriage, drawers'],
  ['GT2 belt and 20-tooth pulley', '1', '$4.00', '$4.00', 'Scoop slide'],
  ['Coin vibration motor, 24 mm', '2', '$0.80', '$1.60', 'Vibrating trays'],
  ['PTFE (low-friction) tape', '1', '$1.00', '$1.00', 'Scoop carriage'],
  ['DRV8833 motor driver', '1', '$2.00', '$2.00', 'Vibration motors'],
  ['Reed switch and 6 mm magnet', '18 + 18', '$0.50', '$9.00', 'One pair under each bin (second semester)'],
  ['Roller limit switch', '3', '$0.50', '$1.50', 'Scoop home; drawer closed'],
  ['White LED strip, 12 V', '1 m', '$6.00', '$6.00', 'Scanner lights'],
  ['MOSFET switch module', '1', '$1.50', '$1.50', 'Switches the lights'],
  ['12 V 10 A power supply', '1', '$15.00', '$15.00', 'Power'],
  ['12 V to 5 V converter', '1', '$8.00', '$8.00', 'Raspberry Pi and servos'],
  ['Mains cord, cable, connectors, wire', '-', '-', '$15.00', 'Wiring'],
  ['2x2 x 8 ft lumber', '1', '$5.50', '$5.50', 'Corner posts'],
  ['1x2 x 8 ft lumber', '3', '$3.00', '$9.00', 'Rails and cleats'],
  ['Half-inch plywood, 2 x 4 ft', '1', '$16.00', '$16.00', 'Floor and deck'],
  ['Wood screws (#8 x 2.5 in, #6 x 1.25 in, #6 x 0.75 in)', '324', '$0.04 to $0.10', '$16.16', 'Frame; printed parts to wood'],
  ['M3 heat-set inserts and M2 to M5 screws', 'about 250', '-', '$15.49', 'Printed-to-printed joints'],
  ['Filament: red PLA, PETG, other PLA', 'about 8.5 kg', 'about $10 per kg', '$80.72', 'All printed parts'],
], { size: 17 }));
add(P('The total is about 10 percent above the $300 upper target. Three things explain the difference from the pitch budget. The pitch priced the Raspberry Pi at $35; a realistic price is $55. The pitch allowed $40 for filament; the finished machine uses about $81. Against that, the lead screw, linear rail and port expander in the pitch budget are no longer in the design. The clearest ways to bring the cost back under the target are the cheaper ESP32 controller and camera that were set aside (Table 6) and thinner skin panels; the wall tiles were already reduced from 2.0 mm to 1.2 mm, which saved about 0.9 kg of plastic.'));
add(H3('Actual printing cost to date'));
add(...table('Filament printed for the machine, November 8 to November 22, 2026', [2600, 1700, 1700, 3360], [
  ['Material', 'Mass printed', 'Price', 'Cost'],
  ['PETG', '2.21 kg', '$39.99 per 4 kg', '$22.12'],
  ['Red PLA', '0.76 kg', '$9.99 per kg', '$7.63'],
  ['Other PLA', '0.65 kg', '$9.99 per kg', '$6.46'],
  ['TPU', '0.004 kg', '-', '$0.04'],
  ['**Total**', '**3.63 kg**', '39 print jobs, about 95 hours', '**$36.25, or about $40 with 9.375% sales tax**'],
]));
add(P('The masses are the slicer figures where they were recorded and estimates otherwise. One finding is useful for planning: real prints came in 25 to 35 percent lighter than the CAD estimate, and took about 0.88 times the estimated time.'));

// ------------------------------------------------------------------ analysis
add(H1('4. Analysis and Modeling'));
add(H2('4.1 Geometric model of the whole machine'));
add(P('The main model in this project is geometric. The assumption is simple: if every part is in its correct place in one shared coordinate system and no two parts overlap, the machine can be assembled. The integration check loads the parts of all four modules and intersects each pair whose bounding boxes touch. The scoop is not a fixed part, so it is tested at 18 positions: waiting under the funnel, at its home switch, and tipped into each of the 16 bins.'));
add(P('The check found real problems before anything was printed. Two examples: the drawer body was 4 mm wider than the opening in the skin, and the tensioner for the scoop belt ran into one of the wood posts. Both were corrected in CAD. The current result is zero overlaps in all pairs and all 18 scoop positions.'));
add(H2('4.2 Will the piece land in the bin?'));
add(P('The scoop tips to 40 degrees. A piece on the pad slides off the lip and falls into the bin row beside the beam. The landing point was estimated for a brick sliding from the center of the cup with a friction coefficient between 0.3 and 0.45, which covers plastic on the rubber-like pad. The piece leaves the lip 75 mm from the centerline and lands 110 to 120 mm from it. The bin opening runs from 56 to 147 mm, so the piece lands inside with about 26 mm of fall from the lip to the top of the bin. With no friction at all the piece would land at 146 mm, on the edge; the pad is there to prevent that.'));
add(H2('4.3 Structural estimate for the scoop beam'));
add(P('The beam is a hollow printed box, 30 mm by 50 mm, spanning about 670 mm between its two supports and carrying about 0.4 kg of carriage, cup and servo. The estimated sag at mid-span is under 1 mm, which is small compared with the 26 mm of clearance above the bins. If the real beam bounces when the carriage stops, the fallback is thicker beam walls.'));
add(H2('4.4 Print budget'));
add(P('The first complete design was fully printed and came to about 25 kg and 550 printing hours, which one printer cannot deliver in a semester. A budget was therefore written into the interface: at most about 9.5 kg and 200 hours for the whole machine. The wood frame brought the design inside it, at about 8.5 kg. The proof of concept needed 3.6 kg.'));
add(H2('4.5 Capacity'));
add(P('Each bin holds 0.57 liters. The hopper holds about 0.9 liters, so a full box of pieces is poured in several loads. [[TEAM: measure how many pieces of the test set fill the hopper and the fullest bin.]]'));

// ------------------------------------------------------------------ experimentation
add(H1('5. Experimentation and Results'));
add(H2('5.1 Test plan'));
add(P('The testing sheet from the pitch listed six tests. Table 12 restates each with a method that another person could repeat, and gives its status. The test set for every test is one LEGO Classic 10696 box.'));
add(...table('Test plan and status on November 22, 2026', [1700, 4200, 1600, 1860], [
  ['Test', 'Method', 'Pass level', 'Status'],
  ['Classification', 'Place 100 pieces from the test set on the scanner one at a time. Record the name, color group and bin code returned, and compare with the correct bin.', 'At least 85% correct bin', 'Chain works; count not yet run'],
  ['Sorting', 'Feed 100 identified pieces. Record the bin each piece lands in against the bin code sent.', 'At least 90% in the correct bin', 'Waiting for assembly'],
  ['Speed', 'Time the machine sorting 50 pieces from pour to last drop.', '5 to 10 pieces per minute', 'Waiting for assembly'],
  ['Reliability', 'Run for 30 minutes. Record jams, missed detections and stops.', '30 minutes with no failure', 'Waiting for assembly'],
  ['Count (database)', 'After a sort, count each bin by hand and compare with the website.', 'Counts agree', 'Waiting for assembly'],
  ['Integration', 'Pour pieces in and confirm camera, server, website and motion all respond for each piece.', 'Every piece handled end to end', 'Camera, server and website confirmed; motion not yet'],
  ['Connectivity', 'Leave the Camera and Live pages open for 30 minutes on Wi-Fi and record dropouts.', 'No loss longer than 10 s', 'Worked at the class presentation; timed run not yet done'],
  ['Dashboard delay', 'Time from a piece on the scanner to its appearance on the Live page, 20 pieces.', 'Under 3 seconds', 'Not yet timed'],
], { size: 17 }));
add(H2('5.2 Tests completed'));
add(H3('Fit tests on the printer'));
add(P('Before any machine part was printed, small test pieces were printed to find the clearances in Table 8: a row of dovetail joints at 0.00 to 0.20 mm, pockets at four sizes, holes for heat-set inserts at three sizes in each plastic, and pockets for the 16 mm bearing. Each was assembled by hand and the tightest size that still went together was chosen. The values were then used for every part, and the printed parts of the proof of concept went together with those values.'));
add(H3('Software checks on the design'));
add(...table('Results of the automated checks', [4200, 5160], [
  ['Check', 'Result'],
  ['Overlap between parts, all four modules', '0 overlaps'],
  ['Scoop tested at 18 positions against the frame, deck and closed drawers', '0 overlaps; lowest point 136 mm, above the 134 mm limit over the bins'],
  ['Every print file is one solid piece', '164 files checked, 0 in pieces'],
  ['Every part fits the printer and prints without supports', 'All parts 248 mm or smaller on a flat face'],
  ['Automated tests of the website server', '63 tests, all passing'],
]));
add(H3('Identification and the website'));
add(P('The team confirmed three things on the working hardware by November 22: a piece placed under the camera is identified and appears on the Live page of the website; the connection works over the wireless network in the classroom used for the presentation; and the website shows a bin as open or closed when its switch changes.'));
add(TODO('TEAM (Ethan): add the number of pieces tried so far, how many were named correctly, and a screenshot of the Live page with a real piece on it.'));
add(H2('5.3 Results against the specification'));
add(...table('Measured results (to be completed after the proof-of-concept test)', [2600, 2200, 2200, 2360], [
  ['Measure', 'Target', 'Measured', 'Number of pieces or runs'],
  ['Identification accuracy', 'At least 85%', '[[add]]', '[[add]]'],
  ['Sorting accuracy', 'At least 90%', '[[add]]', '[[add]]'],
  ['Speed', '5 to 10 pieces per minute', '[[add]]', '[[add]]'],
  ['Continuous run without failure', '30 minutes', '[[add]]', '[[add]]'],
  ['Website delay', 'Under 3 seconds', '[[add]]', '[[add]]'],
  ['Weight', 'Below 30 lb', '[[add]]', '-'],
]));
add(TODO('TEAM: fill in Table 14 after the test on November 27 to 29. Report the count behind every percentage, for example "88 of 100".'));

add(H2('5.4 Discussion'));
add(P('The semester produced a complete design, the printed parts and a working software chain, but not yet a measured sort. The reasons are worth stating plainly, because they are the main lessons of the project.'));
add(H3('What went as planned'));
add(B('Splitting the work into three stages let the software for Identify and the website progress in parallel with the CAD.'));
add(B('Using an existing recognition service removed the largest risk found in the benchmarking, the need for a labeled data set.'));
add(B('The rule that every part prints without supports, as one piece, with measured fits, meant that 39 print jobs produced usable parts with few reprints.'));
add(H3('Failures and what they changed'));
add(B('**The first full design was too large to print.** At 25 kg and 550 hours it could not be built in the time available. The response was the wood frame, a smaller body and a written print budget. In hindsight the mass and time should have been estimated before the detailed design, not after.'));
add(B('**A part printed in two pieces.** A plug that joins two segments of the scoop beam was drawn 1 mm away from the segment, so the printer reported an empty layer. The team added the one-solid-body check, which then found five more parts with the same kind of defect before they were printed.'));
add(B('**A component size was assumed instead of measured.** The tray for the power supply was first drawn for a larger supply than the one the team owns. The rule since then is to design only around parts that have been measured.'));
add(B('**A print plate was too ambitious.** One plate of scoop parts was sliced at 23 hours with supports trapped inside the beam. It was split into two plates and the beam was turned so it needs no supports.'));
add(B('**The same roof tile was printed eight times.** The eight roof tiles are eight different files that look alike. Seven had to be reprinted correctly. The file notes now state that each file is a different position.'));
add(B('**Assembly started late.** Printing finished on November 22, which leaves about one week for the frame, wiring and motion control. The proof of concept was therefore reduced to the open frame, the top, the deck and the scoop; the skin walls and drawers moved to the second semester.'));
add(H3('Remaining risks'));
add(B('**Feeding one piece at a time.** Both published hobby machines found this to be the hardest part [3], [4], and the drum and trays have not yet run with real pieces. If two pieces reach the scanner together, the fallback for the proof of concept is to place pieces on the scanner by hand.'));
add(B('**Color.** Some shades can only be told apart by brightness, for example dark gray from light gray. The scanner needs fixed lighting, and the unknown bin exists so that a doubtful color is not forced into a wrong bin.'));
add(B('**Dependence on an outside service.** If Brickognize is unavailable, the machine cannot identify pieces. A local model is a second-semester option.'));
add(B('**Motion control is not yet written.** It is small in scope (one slide position and one tilt direction per bin code) but it is on the critical path.'));

// ------------------------------------------------------------------ conclusions
add(H1('6. Conclusions and Recommended Future Work'));
add(H2('6.1 Conclusions'));
add(P('The project set out to show that a desk-sized machine can sort mixed LEGO pieces into 16 bins and keep count of them for about $250 to $300. At the end of the first semester the following is known:'));
add(B('A complete design exists and passes its geometric checks: zero overlaps across four modules and 18 scoop positions, and 164 print files that are each one solid piece.'));
add(B('The proof-of-concept parts were made with 3.63 kg of filament in about 95 printing hours, for about $40 of filament.'));
add(B('The parts in a finished machine are worth about $330, which is 10 percent above the upper cost target. The target is reachable with the cheaper controller and camera that were set aside.'));
add(B('Identification works from the camera to the website, and the bin-open detection works.'));
add(B('Sorting accuracy, speed and reliability have not yet been measured. [[TEAM: replace this line with the measured results and state whether each target was met.]]'));
add(H2('6.2 Recommended future work'));
add(P('**Before the proof-of-concept presentation:** build the frame, mount the scoop and deck, wire the motors, write the motion control and run the tests in Table 12.'));
add(P('**Second semester, the finished product:**'));
add(B('Print and fit the red wall skin, the corner caps and the two drawers with their 16 bins.'));
add(B('Fit a switch under each bin and complete the recount function on the real machine.'));
add(B('Build the inventory functions of the website: Count Everything, Add New LEGO and Find What\'s Missing.'));
add(B('Tune Isolate with real pieces until one piece at a time reaches the scanner reliably.'));
add(B('Test the lower-cost ESP32 controller and camera to bring the unit cost under $300.'));
add(B('Run a user test with someone who has not seen the machine, to check the "minimal instructions" target.'));
add(P('**Collecting pieces from the floor.** The pitch included a floor collector, and the first concept was a push-along paddle wheel. The current proposal is a vacuum attachment: a yellow canister that fits a household shop vacuum, traps the pieces behind a screen, then lifts off the hose and sits on the hopper stud, where a gate in its base opens and drops the pieces into the machine. It is designed in CAD and its lid has been printed.'));
add(...fig('full_vac', 'The finished machine with the wall panels and drawers fitted, and the proposed vacuum canister on the hopper stud.', 420, 520));
add(...fig('pitch-13', 'The original schedule from the pitch.', 560));
add(...table('Schedule: planned and actual', [3200, 2400, 3760], [
  ['Task', 'Planned', 'Actual'],
  ['Project pitch', 'Oct 6', 'Oct 6'],
  ['Camera system and identification server', 'Sep 28 to Oct 30', 'Working by late October; connected to the website in November'],
  ['Budget and bill of materials', 'Oct 12 to 16', 'First budget Oct; CAD-based BOM Nov 18'],
  ['Design of the product in CAD', 'Oct 26 to Nov 6', 'Final interface Nov 6; corrections through Nov 16'],
  ['Printing', 'Not listed separately', 'Nov 8 to Nov 22'],
  ['Build proof of concept', 'Nov 16 to 20', 'Nov 23 to 29 (one week late)'],
  ['Final report', 'Nov 16 to 27', 'Dec 1'],
  ['Proof-of-concept presentation', 'Dec 2', 'Dec 2'],
]));
add(...table('Team roles', [2400, 6960], [
  ['Member', 'Responsibilities'],
  ['Branden Jerrick Adsuara', 'Project lead and integration. All CAD, 3D printing and assembly; wiring and power; the home server, website and bill of materials.'],
  ['Vivek Goorla', 'Isolate: code and testing of the feeding stage.'],
  ['Ethan Roche', 'Identify: camera capture, the Raspberry Pi code and piece identification.'],
  ['Marshall Wong', 'Indicate: the sorting mechanism and its control; project documents and presentations.'],
]));

// ------------------------------------------------------------------ references
add(H1('References'));
[
  '[1] The LEGO Group, "The LEGO Group delivers record results in 2025 driven by strong brand and innovative portfolio," news release, March 10, 2026. https://www.lego.com/en-us/aboutus/news/2026/march/the-lego-group-delivers-record-results-in-2025-driven-by-strong-brand-and-innovative-portfolio',
  '[2] C. Lawrence, "Sort A Brick launches world\'s first AI-powered LEGO sorting system," Tech.eu, October 17, 2025. https://tech.eu/2025/10/17/sort-a-brick-launches-worlds-first-ai-powered-lego-sorting-system/',
  '[3] The Brothers Brick, "World\'s first AI-powered LEGO sorting machine built with 10,000 LEGO bricks," December 6, 2019. https://www.brothers-brick.com/2019/12/06/this-fan-created-the-ultimate-lego-brick-sorting-machine-powered-by-ai-exclusive-feature',
  '[4] J. Mattheij, "How I Built an AI to Sort 2 Tons of Lego Pieces," IEEE Spectrum, June 23, 2017. https://spectrum.ieee.org/how-i-built-an-ai-to-sort-2-tons-of-lego-pieces',
  '[5] PetaPixel, "Brickit\'s AI Camera Scans Your LEGO to Suggest Things You Can Build," July 1, 2021. https://petapixel.com/2021/07/01/brickits-ai-camera-scans-your-lego-to-suggest-things-you-can-build/',
  '[6] J. Vidal et al., "Brickognize: Applying Photo-Realistic Image Synthesis for Lego Bricks Recognition with Limited Data," Sensors, vol. 23, no. 4, article 1898, 2023. https://www.mdpi.com/1424-8220/23/4/1898',
  '[7] Brickognize, LEGO part recognition service. https://brickognize.com',
  '[8] BrickLink, inventory of LEGO set 10696-1, Medium Creative Brick Box. https://www.bricklink.com/v2/catalog/catalogitem.page?S=10696-1',
  '[9] San José State University, Senior Project Handbook, Section 9: Writing the Technical Report.',
  '[10] Bricked Sorting project repository and website. https://github.com/jerrekt/Bricked-Sorting and https://bricked-01.adsuaracloud.com',
].forEach(r => add(new Paragraph({ children: [run(r, { size: 20 })], spacing: { after: 110 }, indent: { left: 420, hanging: 420 } })));
add(TODO('TEAM: check reference [6] authors and reference [8] against the sources before submitting.'));

// ------------------------------------------------------------------ appendices
add(H1('Appendix A. Wood cut list'));
add(...table('Wood cut list for the frame', [2700, 1500, 2300, 800, 2060], [
  ['Piece', 'Stock', 'Length', 'Qty', 'Use'],
  ['Corner post', '2x2', '600 mm (23 5/8 in)', '4', 'Corners'],
  ['Long top rail', '1x2', '632 mm (24 7/8 in)', '2', 'Under the roof'],
  ['Long deck cleat', '1x2', '632 mm (24 7/8 in)', '2', 'Carries the deck'],
  ['Short top rail', '1x2', '272 mm (10 11/16 in)', '2', 'Under the roof'],
  ['Short deck cleat', '1x2', '272 mm (10 11/16 in)', '2', 'Carries the deck'],
  ['Short bottom rail', '1x2', '272 mm (10 11/16 in)', '2', 'Ties the posts at the floor'],
  ['Beam post', '1x2', '212 mm (8 3/8 in)', '2', 'Holds the scoop beam'],
  ['Roof cross rail', '1x2, flat', '310 mm (12 3/16 in)', '2', 'Under the hopper stud'],
  ['Floor', '1/2 in plywood', '720 x 360 mm', '1', 'Base'],
  ['Deck', '1/2 in plywood', '708 x 348 mm', '1', 'Shelf; 38 mm corner notches and a 56 mm hole'],
]));
add(H1('Appendix B. Print log summary'));
add(P('The complete log of every print job (date, plate, material, mass, time and parts) is kept in the repository at cad/v14/plates/print_log.json and is shown on the Prints page of the website. Mass by material is in Table 11.'));
add(H1('Appendix C. Alternative concepts'));
add(P('**Floor collector, concept 1 (pitch).** A compact push-along collector with a ground-driven paddle wheel sweeping pieces into a removable hopper. Main concern: thin plates may be pushed forward instead of picked up. Replaced by the vacuum canister in Section 6.2.'));
add(P('**Three build options for the controller and camera.** (1) Raspberry Pi with a USB webcam: uses hardware on hand; chosen for the proof of concept. (2) Raspberry Pi with a generic camera module. (3) ESP32 camera board and ESP32 controller: lowest cost, set aside until the machine works.'));
add(TODO('TEAM (Marshall): add photographs and a short description of the cardboard prototype, and what was learned from it.'));

// lists of figures and tables (inserted after the table of contents)
const lists = [H1('List of Figures'), ...figs.map(f => new Paragraph({ children: [run(f, { size: 19 })], spacing: { after: 50 } })),
  H1('List of Tables'), ...tabs.map(f => new Paragraph({ children: [run(f, { size: 19 })], spacing: { after: 50 } }))];
body.splice(LIST_SLOT, 0, ...lists);

const doc = new Document({
  creator: 'Bricked Sorting team', title: 'Bricked Sorting: Senior Project I Written Report',
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: FONT, size: 22 } },
      heading1: { run: { font: FONT, size: 32, bold: true, color: 'B71C1C' }, paragraph: { spacing: { before: 240, after: 160 }, keepNext: true } },
      heading2: { run: { font: FONT, size: 26, bold: true, color: '222222' }, paragraph: { spacing: { before: 240, after: 110 }, keepNext: true } },
      heading3: { run: { font: FONT, size: 23, bold: true, color: '444444' }, paragraph: { spacing: { before: 180, after: 90 }, keepNext: true } },
    },
  },
  numbering: { config: [
    { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: title },
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }, pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run('Bricked Sorting · TECH 190A Written Report', { size: 16, color: '888888' })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: '666666' })] })] }) },
      children: body },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(HERE,'lists.txt'), figs.concat(tabs).map(s=>s.slice(0,90)).join('\n')); fs.writeFileSync(path.join(HERE, 'Bricked_Sorting_Written_Report.docx'), b); console.log('figures', figN, 'tables', tabN); });
