/* Intro: a LEGO brick drops into the scanner, gets identified, and the chute sends it to its bin.
   Shown once per browser session on whichever page the visitor opens first. Tap, click or Esc skips it.
   Load this right after <body> so it covers the page before anything paints. */
(function () {
  if (/[?&]nointro\b/.test(location.search)) return;
  try { if (sessionStorage.getItem('brickedIntroSeen') === '1') return; sessionStorage.setItem('brickedIntroSeen', '1'); } catch (e) {}

  var css =
    '#brickIntro{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;' +
    'background:radial-gradient(ellipse at 50% 38%,#1b2540,#0b0f1a 70%);color:#eef1fa;cursor:pointer;animation:biOut .5s ease 2.75s forwards;font:600 14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}' +
    '#brickIntro::after{content:"";position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#d01012 0 33.3%,#f5c518 33.3% 66.6%,#0057c2 66.6% 100%)}' +
    '#brickIntro .biLogo{height:clamp(36px,9vw,56px);width:auto;opacity:0;transform:translateY(8px);animation:biRise .6s ease .15s forwards}' +
    '#brickIntro svg{width:min(86vw,420px);height:auto;overflow:hidden}' +
    '#brickIntro .biTag{color:#9aa4c0;font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:0;animation:biRise .6s ease 2.05s forwards}' +
    '#brickIntro .biSkip{position:absolute;bottom:18px;right:18px;font-size:11px;color:#6f7896;letter-spacing:.06em}' +
    '#brickIntro .biBrick{animation:biPath 1.8s cubic-bezier(.45,0,.4,1) .4s both}' +
    '#brickIntro .biChute{transform-origin:150px 80px;transform:rotate(125deg);animation:biAim .4s ease-out 1.0s forwards}' +
    '#brickIntro .biFlash{opacity:0;animation:biFlash .3s ease .85s}' +
    '#brickIntro .biBeam{opacity:0;animation:biFlash .3s ease .85s}' +
    '#brickIntro .biLabel{opacity:0;animation:biLabel 1.3s ease .95s forwards}' +
    '#brickIntro .biGlow{opacity:0;animation:biGlow .8s ease 2.0s forwards}' +
    '@keyframes biPath{' +
      '0%{transform:translate(150px,-14px) rotate(0)}' +
      '25%{transform:translate(150px,42px) rotate(0)}' +
      '50%{transform:translate(150px,42px) rotate(0)}' +
      '58%{transform:translate(161px,74px) rotate(26deg)}' +
      '80%{transform:translate(219px,102px) rotate(26deg)}' +
      '92%{transform:translate(238px,124px) rotate(10deg)}' +
      '100%{transform:translate(240px,136px) rotate(0)}}' +
    '@keyframes biAim{to{transform:rotate(26deg)}}' +
    '@keyframes biFlash{0%,100%{opacity:0}40%{opacity:.9}}' +
    '@keyframes biLabel{0%{opacity:0}20%,75%{opacity:1}100%{opacity:.0}}' +
    '@keyframes biGlow{0%{opacity:0}30%{opacity:1}100%{opacity:0}}' +
    '@keyframes biRise{to{opacity:1;transform:none}}' +
    '@keyframes biOut{to{opacity:0;visibility:hidden}}' +
    '@media (prefers-reduced-motion:reduce){#brickIntro{animation:biOut .3s ease .7s forwards}#brickIntro *{animation:none!important;opacity:1!important}' +
      '#brickIntro .biBrick{transform:translate(240px,136px)!important}#brickIntro .biChute{transform:rotate(26deg)!important}#brickIntro .biFlash,#brickIntro .biBeam,#brickIntro .biLabel,#brickIntro .biGlow{opacity:0!important}}';

  // Bin colors are the site's color groups (web/data/bins.json): red, yellow, green, blue.
  var bins = [['#D6372B', 60], ['#F2C21B', 120], ['#3E9B45', 180], ['#2F74C8', 240]].map(function (b) {
    return '<rect x="' + (b[1] - 24) + '" y="118" width="48" height="34" rx="3" fill="' + b[0] + '"/>' +
      '<rect x="' + (b[1] - 24) + '" y="118" width="48" height="5" fill="#000" opacity=".22"/>';
  }).join('');

  var glow = '<rect class="biGlow" x="213" y="115" width="54" height="40" rx="5" fill="none" stroke="#9cc6ff" stroke-width="2.5"/>';

  var svg =
    '<svg viewBox="0 0 300 160" aria-hidden="true">' +
      // scanner: hood, camera, light beam
      '<rect x="120" y="18" width="60" height="44" rx="6" fill="#1d2538" stroke="#2b3552" stroke-width="2"/>' +
      '<circle cx="150" cy="25" r="4" fill="#4f9bff"/>' +
      '<path class="biBeam" d="M150 28 L130 58 H170 Z" fill="#eaf2ff"/>' +
      '<rect class="biFlash" x="122" y="20" width="56" height="40" rx="5" fill="#ffffff"/>' +
      '<text class="biLabel" x="196" y="38" fill="#eef1fa" font-size="10" font-weight="700">BLUE · 2x2</text>' +
      '<text class="biLabel" x="196" y="50" fill="#9aa4c0" font-size="8">bin 4</text>' +
      // chute: pivots under the scanner, swings from straight down to the blue bin
      '<g class="biChute"><rect x="150" y="76" width="80" height="8" rx="4" fill="#9aa4c0"/></g>' +
      '<circle cx="150" cy="80" r="5" fill="#eef1fa"/>' +
      // the brick: over the chute, under the bins, so it drops into the bin
      '<g class="biBrick"><rect x="-11" y="-6" width="22" height="12" rx="1.5" fill="#2F74C8"/>' +
        '<rect x="-8" y="-9" width="6" height="3.5" rx="1" fill="#2F74C8"/><rect x="2" y="-9" width="6" height="3.5" rx="1" fill="#2F74C8"/>' +
        '<rect x="-11" y="-6" width="22" height="3" rx="1.5" fill="#fff" opacity=".18"/></g>' +
            bins + glow +
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
  setTimeout(done, 4500); // safety net if animations never fire
})();
