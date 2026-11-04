/* Intro: our real sorter from above. A brick lands on the trapdoors under the camera, gets
   identified, the lift picks the floor and the scoop turns to the bin's 22.5 deg slot, the doors
   open and the brick slides down the scoop into its wedge bin (8 bins in a half ring, like the
   V10/V11 CAD). Shown once per browser session on whichever page is opened first.
   Tap, click or Esc skips. ?nointro turns it off. Load right after <body>. */
(function () {
  if (/[?&]nointro\b/.test(location.search)) return;
  try { if (sessionStorage.getItem('brickedIntroSeen') === '1') return; sessionStorage.setItem('brickedIntroSeen', '1'); } catch (e) {}

  var CX = 150, CY = 58, R0 = 68, R1 = 124, TARGET = 4;           // yaw axis, bin ring, blue bin slot
  var aim = function (k) { return 180 - 22.5 * (k - 0.5); };       // slot k center, degrees (screen, y down)
  var A = aim(TARGET), START = aim(2) + 4;                         // scoop starts near slot 2
  function pt(r, deg) { var t = deg * Math.PI / 180; return (CX + r * Math.cos(t)).toFixed(1) + ' ' + (CY + r * Math.sin(t)).toFixed(1); }
  var rad = A * Math.PI / 180, along = function (r) { return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)]; };
  var p60 = along(30), p97 = along(98), p103 = along(104);
  var tr = function (p, s, rot) { return 'transform:translate(' + p[0].toFixed(1) + 'px,' + p[1].toFixed(1) + 'px) rotate(' + rot + 'deg) scale(' + s + ')'; };
  var rot = (A - 90).toFixed(2);

  var css =
    '#brickIntro{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;' +
    'background:radial-gradient(ellipse at 50% 38%,#1b2540,#0b0f1a 70%);color:#eef1fa;cursor:pointer;animation:biOut .5s ease 2.9s forwards;font:600 14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}' +
    '#brickIntro::after{content:"";position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#d01012 0 33.3%,#f5c518 33.3% 66.6%,#0057c2 66.6% 100%)}' +
    '#brickIntro .biLogo{height:clamp(40px,9vw,104px);width:auto;opacity:0;transform:translateY(8px);animation:biRise .6s ease .1s forwards}' +
    '#brickIntro svg{width:min(90vw,460px);height:auto;overflow:hidden}' +
    '#brickIntro .biTag{color:#9aa4c0;font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:0;animation:biRise .6s ease 2.2s forwards}' +
    '#brickIntro .biSkip{position:absolute;bottom:18px;right:18px;font-size:11px;color:#6f7896;letter-spacing:.06em}' +
    '#brickIntro .biBrick{animation:biPath 1.9s linear .4s both}' +
    '#brickIntro .biScoop{transform-origin:' + CX + 'px ' + CY + 'px;transform:rotate(' + (START - 90) + 'deg);animation:biAim .45s cubic-bezier(.4,0,.2,1) 1.0s forwards}' +
    '#brickIntro .biDoorL{transform-origin:' + (CX - 17) + 'px ' + CY + 'px;animation:biOpen .18s ease-in 1.55s forwards}' +
    '#brickIntro .biDoorR{transform-origin:' + (CX + 17) + 'px ' + CY + 'px;animation:biOpen .18s ease-in 1.55s forwards}' +
    '#brickIntro .biFlash{opacity:0;animation:biFlash .3s ease .9s}' +
    '#brickIntro .biLabel{opacity:0;animation:biLabel 1.5s ease .95s forwards}' +
    '#brickIntro .biLift{transform:translateY(0);animation:biLift .45s cubic-bezier(.4,0,.2,1) 1.0s forwards}' +
    '#brickIntro .biGlow{opacity:0;animation:biGlow .8s ease 2.2s forwards}' +
    '@keyframes biPath{' +
      '0%{' + tr([CX, CY], 1.9, 0) + ';opacity:0}' +
      '22%{' + tr([CX, CY], 1, 0) + ';opacity:1}' +
      '62%{' + tr([CX, CY], 1, 0) + ';opacity:1}' +
      '70%{' + tr(p60, .82, rot) + ';opacity:1}' +
      '90%{' + tr(p97, .82, rot) + ';opacity:1}' +
      '100%{' + tr(p103, .5, rot) + ';opacity:0}}' +
    '@keyframes biAim{to{transform:rotate(' + (A - 90) + 'deg)}}' +
    '@keyframes biOpen{to{transform:scaleX(.12)}}' +
    '@keyframes biLift{to{transform:translateY(26px)}}' +
    '@keyframes biFlash{0%,100%{opacity:0}40%{opacity:.9}}' +
    '@keyframes biLabel{0%{opacity:0}15%,80%{opacity:1}100%{opacity:.25}}' +
    '@keyframes biGlow{0%{opacity:0}30%{opacity:1}100%{opacity:0}}' +
    '@keyframes biRise{to{opacity:1;transform:none}}' +
    '@keyframes biOut{to{opacity:0;visibility:hidden}}' +
    '@media (prefers-reduced-motion:reduce){#brickIntro{animation:biOut .3s ease .8s forwards}#brickIntro *{animation:none!important;opacity:1!important}' +
      '#brickIntro .biScoop{transform:rotate(' + (A - 90) + 'deg)!important}#brickIntro .biBrick,#brickIntro .biFlash,#brickIntro .biGlow{opacity:0!important}}';

  // Wedge bins in a half ring, one 22.5 deg slot each. Colors are the site's 8 slots (web/data/bins.json).
  var COLORS = ['#D6372B', '#F2C21B', '#3E9B45', '#2F74C8', '#B65FA8', '#2A2B2E', '#E9E7E1', '#8A8F98'];
  var wedges = COLORS.map(function (c, i) {
    var k = i + 1, a0 = aim(k) - 10.35, a1 = aim(k) + 10.35;
    var d = 'M' + pt(R0, a0) + ' L' + pt(R1, a0) + ' A' + R1 + ' ' + R1 + ' 0 0 1 ' + pt(R1, a1) + ' L' + pt(R0, a1) + ' A' + R0 + ' ' + R0 + ' 0 0 0 ' + pt(R0, a0) + 'Z';
    return '<path d="' + d + '" fill="' + c + '"' + (c === '#2A2B2E' ? ' stroke="#4a5372" stroke-width="1"' : '') + '/>' +
      (k === TARGET ? '<path class="biGlow" d="' + d + '" fill="none" stroke="#bcd8ff" stroke-width="2.5"/>' : '');
  }).join('');

  var svg =
    '<svg viewBox="0 0 300 188" aria-hidden="true">' +
      wedges +
      // scoop: wide catch under the scanner, tapering to the outlet; turns about the yaw axis
      '<g class="biScoop"><path d="M' + (CX - 15) + ' ' + CY + ' L' + (CX + 15) + ' ' + CY + ' L' + (CX + 6) + ' ' + (CY + 64) + ' L' + (CX - 6) + ' ' + (CY + 64) + 'Z" fill="#9aa4c0"/>' +
        '<path d="M' + (CX - 9) + ' ' + (CY + 6) + ' L' + (CX + 9) + ' ' + (CY + 6) + ' L' + (CX + 3) + ' ' + (CY + 60) + ' L' + (CX - 3) + ' ' + (CY + 60) + 'Z" fill="#7d87a3"/></g>' +
      // scanner plate with two trapdoors (seen from above)
      '<rect x="' + (CX - 21) + '" y="' + (CY - 21) + '" width="42" height="42" rx="4" fill="none" stroke="#4a5372" stroke-width="2"/>' +
      '<rect class="biDoorL" x="' + (CX - 17) + '" y="' + (CY - 17) + '" width="17" height="34" fill="#2b3552"/>' +
      '<rect class="biDoorR" x="' + CX + '" y="' + (CY - 17) + '" width="17" height="34" fill="#2b3552"/>' +
      '<rect class="biFlash" x="' + (CX - 21) + '" y="' + (CY - 21) + '" width="42" height="42" rx="4" fill="#ffffff"/>' +
      // the brick (2x2, top view)
      '<g class="biBrick"><rect x="-10" y="-10" width="20" height="20" rx="2" fill="#2F74C8"/>' +
        '<circle cx="-4.5" cy="-4.5" r="3" fill="#4d8be0"/><circle cx="4.5" cy="-4.5" r="3" fill="#4d8be0"/>' +
        '<circle cx="-4.5" cy="4.5" r="3" fill="#4d8be0"/><circle cx="4.5" cy="4.5" r="3" fill="#4d8be0"/></g>' +
      // what Identify decided
      '<text class="biLabel" x="' + (CX + 30) + '" y="' + (CY - 26) + '" fill="#eef1fa" font-size="10" font-weight="700">BLUE · 2x2 BRICK</text>' +
      '<text class="biLabel" x="' + (CX + 30) + '" y="' + (CY - 14) + '" fill="#9aa4c0" font-size="8">floor 1 · bin 4</text>' +
      // lift: which floor the scoop is on (floor 1 = bricks, floor 2 = other parts)
      '<g transform="translate(40 8)"><rect x="-2" y="0" width="4" height="36" rx="2" fill="#2b3552"/>' +
        '<text x="8" y="7" fill="#6f7896" font-size="7">floor 2</text><text x="8" y="34" fill="#6f7896" font-size="7">floor 1</text>' +
        '<circle class="biLift" cx="0" cy="4" r="4" fill="#eef1fa"/></g>' +
    '</svg>';

  var st = document.createElement('style'); st.id = 'brickIntroStyle'; st.textContent = css;
  var el = document.createElement('div');
  el.id = 'brickIntro'; el.setAttribute('role', 'presentation'); el.setAttribute('aria-hidden', 'true');
  el.innerHTML = '<img class="biLogo" src="assets/logo-720.png" alt="">' + svg + '<div class="biTag">LEGO sorter · SJSU Tech 190A</div><div class="biSkip">tap to skip</div>';

  function done() {
    if (el.parentNode) el.parentNode.removeChild(el);
    if (st.parentNode) st.parentNode.removeChild(st);
    document.removeEventListener('keydown', key);
  }
  function key(e) { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') done(); }
  document.head.appendChild(st);
  (document.body || document.documentElement).appendChild(el);
  el.addEventListener('click', done);
  document.addEventListener('keydown', key);
  el.addEventListener('animationend', function (ev) { if (ev.target === el) done(); });
  setTimeout(done, 4600); // safety net if animations never fire
})();
