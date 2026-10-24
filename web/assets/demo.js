/* Bricked Sorting demo dashboard.
   Everything here is simulated in the browser. The bin table (data/bins.json) and the
   bin codes ("floor-slot", e.g. 1-3) are the same ones Kratos and the Indicate controller
   will use, so a live data source can replace SimSource later without changing the UI. */
(function () {
  'use strict';

  var BINS, SET, BOX = [], EXPECT = {}, CAP = {};
  var S, run = null;
  var KEY = 'bricked-demo-v1';
  var BOXES_CAPACITY = 3;
  var $ = function (s) { return document.querySelector(s); };

  function esc(t) { return String(t).replace(/[&<>"']/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function code(f, s) { return f + '-' + s; }
  function codes() { var a = []; [2, 1].forEach(function (f) { for (var s = 1; s <= 8; s++) a.push(code(f, s)); }); return a; }
  function slotOf(key) { for (var i = 0; i < BINS.slots.length; i++) if (BINS.slots[i].key === key) return BINS.slots[i].slot; return 8; }
  function trueCode(p) { return code(p.brick ? 1 : 2, slotOf(BINS.colorMap[p.color] || 'unknown')); }
  function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function now() { var d = new Date(); return d.toTimeString().slice(0, 5); }
  function sum(o) { var n = 0; for (var k in o) n += o[k]; return n; }
  function plural(n, w) { return n + ' ' + w + (n === 1 ? '' : 's'); }

  /* ---------- state ---------- */
  function fresh() {
    var bins = {};
    codes().forEach(function (c) { bins[c] = []; });
    return { bins: bins, total: null, out: [], flags: {}, log: [], view: 'simple', misread: 3, speed: 16, boxes: 0 };
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function load() {
    try { var t = JSON.parse(localStorage.getItem(KEY)); if (t && t.bins && t.bins['1-1']) return t; } catch (e) {}
    return fresh();
  }
  function count(c) { return S.bins[c].length; }
  function inBins() { var n = 0; codes().forEach(function (c) { n += count(c); }); return n; }
  function counts() { var o = {}; codes().forEach(function (c) { o[c] = count(c); }); return o; }
  function log(msg) { S.log.unshift(now() + '  ' + msg); S.log = S.log.slice(0, 60); }
  function flagged() { return codes().filter(function (c) { return S.flags[c]; }); }

  /* ---------- simulated source: one piece at a time ---------- */
  function identify(p) {
    var c = trueCode(p), slot = +c.split('-')[1];
    if (slot !== 8 && Math.random() * 100 < S.misread) c = c.split('-')[0] + '-8';
    return c;
  }

  /* ---------- rendering ---------- */
  function binCard(c) {
    var f = +c[0], slot = +c.split('-')[1], info = BINS.slots[slot - 1];
    var b = document.createElement('button');
    b.className = 'bin'; b.type = 'button'; b.dataset.code = c;
    b.setAttribute('aria-label', 'Bin ' + c + ', ' + info.label);
    b.innerHTML = '<span class="bin-code">' + c + '</span>' +
      (info.swatch ? '<span class="bin-sw" style="background:' + info.swatch + '"></span>' : '<span class="bin-sw unk"></span>') +
      '<span class="bin-label">' + esc(slot === 8 ? (f === 1 ? 'Unknown brick' : 'Unknown other') : info.label) + '</span>' +
      '<span class="bin-count">0</span><span class="bin-total"></span><span class="fill"><i></i></span>';
    b.addEventListener('click', function () { if (!run) openBin(c); });
    return b;
  }
  function buildBins() {
    [2, 1].forEach(function (f) {
      var el = $('#floor' + f); el.innerHTML = '';
      for (var s = 1; s <= 8; s++) el.appendChild(binCard(code(f, s)));
    });
  }
  function renderBins(pulse) {
    codes().forEach(function (c) {
      var el = document.querySelector('.bin[data-code="' + c + '"]'), n = count(c);
      el.querySelector('.bin-count').textContent = n;
      el.querySelector('.bin-total').textContent = S.total ? 'total ' + S.total[c] : '';
      var pct = Math.min(100, Math.round(n / CAP[c] * 100));
      el.querySelector('.fill i').style.width = pct + '%';
      el.classList.toggle('full', pct >= 80);
      el.classList.toggle('flagged', !!S.flags[c]);
      var fl = el.querySelector('.flag');
      if (S.flags[c] && !fl) { fl = document.createElement('span'); fl.className = 'flag'; fl.textContent = 'Opened'; el.appendChild(fl); }
      if (!S.flags[c] && fl) fl.remove();
      if (pulse && pulse === c) { el.classList.remove('pulse'); void el.offsetWidth; el.classList.add('pulse'); }
    });
    [1, 2].forEach(function (f) {
      var n = 0; for (var s = 1; s <= 8; s++) n += count(code(f, s));
      $('#f' + f + 'sum').textContent = plural(n, 'piece');
    });
  }
  function renderSide() {
    $('#totalOut').textContent = S.total ? sum(S.total) : 'Not set';
    $('#inBinsOut').textContent = inBins();
    $('#outOut').textContent = S.out.length;
    var fl = flagged();
    $('#flagOut').textContent = fl.length ? fl.join(', ') : 'None';
    $('#outTray').hidden = !S.out.length;
    $('#outCount').textContent = S.out.length;
    document.querySelectorAll('[data-action]').forEach(function (b) { b.disabled = !!run || !canDo(b.dataset.action); });
    $('#startBtn').disabled = !!run;
    $('#log').innerHTML = S.log.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('');
    $('#hint').textContent = hint();
  }
  function hint() {
    if (run) return '';
    if (!S.total) return 'Start here: press Start sort to count your first box. That count becomes your collection total.';
    var fl = flagged();
    if (fl.length) return 'Bins ' + fl.join(', ') + ' were opened. Find What\'s Missing re-sorts only those bins plus whatever you found.';
    if (S.out.length) return S.out.length + ' pieces are out. Put them back, or run Find What\'s Missing to check for losses.';
    return 'Tap a bin to pull it out and take some pieces, like a kid would.';
  }
  function render(pulse) { renderBins(pulse); renderSide(); }
  function stage(id, html, on) { var el = $(id); el.querySelector('.st-val').innerHTML = html; el.classList.toggle('on', !!on); }
  function idleStages() { stage('#stIsolate', 'Idle'); stage('#stIdentify', '–'); stage('#stIndicate', '–'); }

  /* ---------- actions ---------- */
  function totalPieces() { return S.total ? sum(S.total) : 0; }
  function canDo(a) {
    if (a === 'count') return true;
    if (a === 'add') return !!S.total && S.boxes < BOXES_CAPACITY;
    if (a === 'audit') return !!S.total && (flagged().length > 0 || S.out.length > 0);
    if (a === 'return') return S.out.length > 0;
    return false;
  }
  var ACTIONS = {
    count: { title: 'Count Everything', start: 'Start sort',
      text: function () { return S.total ? 'Every piece in the bins and every piece that is out goes back through the machine. The result replaces your collection total. Use this once at setup or to start over.'
        : 'Pour one LEGO Classic 10696 box (484 pieces) into the hopper. This first count becomes your collection total.'; } },
    add: { title: 'Add New LEGO', start: 'Start sort',
      text: function () { return 'You bought a new set. One more 10696 box goes through the machine and is added straight to your collection total. Bins are sized for ' + BOXES_CAPACITY + ' boxes; you have ' + S.boxes + '.'; } },
    audit: { title: 'Find What\'s Missing', start: 'Start sort' },
    'return': { title: 'Put pieces back', start: 'Start sort',
      text: function () { return 'Normal sorting. The ' + S.out.length + ' pieces that are out go back into their bins. Your collection total does not change.'; } }
  };

  function chooser() {
    if (!S.total) return confirmAction('count');
    var opts = ['add', 'return', 'audit', 'count'].filter(canDo);
    var body = '<p class="muted">What are you putting in the hopper?</p>' + opts.map(function (a, i) {
      return '<label class="result" style="display:flex;gap:10px;align-items:flex-start;cursor:pointer"><input type="radio" name="act" value="' + a + '"' + (i === 0 ? ' checked' : '') + '><span><strong>' + ACTIONS[a].title + '</strong><br><span class="muted small">' + short(a) + '</span></span></label>';
    }).join('');
    sheet('Start sort', body, [btn('Next', 'primary', function () { var v = document.querySelector('input[name=act]:checked'); if (v) confirmAction(v.value); })]);
  }
  function short(a) {
    return { add: 'A new box. Adds to your total.', 'return': 'Pieces that were out. Total stays the same.',
      audit: 'Recount opened bins and compare to your total.', count: 'Recount everything and reset the total.' }[a];
  }

  function confirmAction(a) {
    if (a === 'audit') return auditSheet();
    sheet(ACTIONS[a].title, '<p>' + ACTIONS[a].text() + '</p>', [btn('Cancel', '', close), btn(ACTIONS[a].start, 'primary', function () { close(); begin(a); })]);
  }

  function auditSheet() {
    var fl = flagged(), n = S.out.length, found = Math.max(0, n - Math.min(2, n));
    var body = '<p>' + (fl.length ? 'Dump bins <strong>' + fl.join(', ') + '</strong> into the hopper.' : 'No bins were opened.') + ' Gather everything that was out and add it too.</p>' +
      (n ? '<p class="muted small">' + plural(n, 'piece') + ' left the machine. How many did you find?</p><div class="stepper"><button type="button" class="btn" id="fMinus">−</button><output id="fOut">' + found + '</output><button type="button" class="btn" id="fPlus">+</button><span class="muted">of ' + n + '</span></div>' : '') +
      '<p class="muted small">Bins that were not opened are not re-sorted.</p>';
    sheet('Find What\'s Missing', body, [btn('Cancel', '', close), btn('Start sort', 'primary', function () { close(); begin('audit', { found: found }); })]);
    if (n) {
      var upd = function () { $('#fOut').textContent = found; };
      $('#fMinus').onclick = function () { found = Math.max(0, found - 1); upd(); };
      $('#fPlus').onclick = function () { found = Math.min(n, found + 1); upd(); };
    }
  }

  function newBox() {
    var a = []; SET.parts.forEach(function (p) { for (var i = 0; i < p.qty; i++) a.push({ color: p.color, hex: p.hex, part: p.part, brick: p.brick }); });
    return a;
  }

  function begin(a, opt) {
    var snap = JSON.stringify(S), q = [];
    if (a === 'count') {
      if (!S.total && inBins() === 0 && !S.out.length) { q = newBox(); S.boxes = 1; }
      else { codes().forEach(function (c) { q = q.concat(S.bins[c]); S.bins[c] = []; }); q = q.concat(S.out); S.out = []; }
      S.flags = {};
    } else if (a === 'add') { q = newBox(); S.boxes++; }
    else if (a === 'return') { q = S.out; S.out = []; }
    else if (a === 'audit') {
      flagged().forEach(function (c) { q = q.concat(S.bins[c]); S.bins[c] = []; });
      shuffle(S.out);
      q = q.concat(S.out.slice(0, opt.found)); S.out = S.out.slice(opt.found);
      S.flags = {};
    }
    run = { mode: a, q: shuffle(q), i: 0, acc: 0, last: 0, snap: snap, before: counts(), added: {} };
    codes().forEach(function (c) { run.added[c] = 0; });
    $('#stopBtn').hidden = false; $('.progress').hidden = false;
    log(ACTIONS[a].title + ': sorting ' + plural(q.length, 'piece'));
    render(); requestAnimationFrame(tick);
  }

  function tick(t) {
    if (!run) return;
    if (!run.last) run.last = t;
    var dt = Math.min(0.25, (t - run.last) / 1000); run.last = t;
    run.acc += dt * S.speed;
    var lastCode = null, p;
    while (run.acc >= 1 && run.i < run.q.length) {
      run.acc -= 1; p = run.q[run.i++];
      var c = identify(p); S.bins[c].push(p); run.added[c]++; lastCode = c;
      stage('#stIsolate', 'Piece #' + run.i, true);
      stage('#stIdentify', '<span class="dot" style="background:' + p.hex + '"></span>' + esc(p.color + ' ' + p.part), true);
      stage('#stIndicate', '→ bin <strong>' + c + '</strong>', true);
    }
    var pct = run.q.length ? run.i / run.q.length * 100 : 100;
    $('#progFill').style.width = pct + '%';
    $('#progText').textContent = run.i + ' / ' + run.q.length;
    if (lastCode) renderBins(lastCode);
    if (run.i >= run.q.length) return finish();
    requestAnimationFrame(tick);
  }

  function finish() {
    var r = run; run = null;
    $('#stopBtn').hidden = true; $('.progress').hidden = true; idleStages();
    if (r.mode === 'count') { S.total = counts(); log('Collection total set: ' + plural(sum(S.total), 'piece')); }
    if (r.mode === 'add') { codes().forEach(function (c) { S.total[c] += r.added[c]; }); log('Added ' + plural(sum(r.added), 'piece') + ' to the total'); }
    if (r.mode === 'return') log('Put back ' + plural(sum(r.added), 'piece') + '. Total unchanged');
    save(); render();
    if (r.mode === 'audit') results();
  }

  function stop() {
    if (!run) return;
    S = JSON.parse(run.snap); run = null;
    $('#stopBtn').hidden = true; $('.progress').hidden = true; idleStages();
    log('Stopped. Nothing changed'); save(); render();
  }

  /* ---------- compare to the collection total ---------- */
  function results() {
    var items = [];
    [2, 1].forEach(function (f) {
      var d = {}; for (var s = 1; s <= 8; s++) { var c = code(f, s); d[c] = count(c) - S.total[c]; }
      var unk = code(f, 8), spare = Math.max(0, d[unk]);
      for (var s2 = 1; s2 <= 7; s2++) {
        var c2 = code(f, s2);
        if (d[c2] < 0) {
          var lack = -d[c2], m = Math.min(lack, spare); spare -= m;
          if (m) items.push({ kind: 'misread', code: c2, n: m, unk: unk });
          if (lack - m) items.push({ kind: 'missing', code: c2, n: lack - m });
        } else if (d[c2] > 0) items.push({ kind: 'extra', code: c2, n: d[c2] });
      }
      if (d[unk] < 0) items.push({ kind: 'missing', code: unk, n: -d[unk] });
      if (spare > 0) items.push({ kind: 'extra', code: unk, n: spare });
    });
    var lost = items.filter(function (i) { return i.kind === 'missing'; }).reduce(function (a, i) { return a + i.n; }, 0);
    log('Find What\'s Missing: ' + (items.length ? plural(lost, 'piece') + ' possibly missing' : 'everything matches'));
    save(); render();
    if (!items.length) return sheet('Everything matches', '<p class="ok">Every bin matches your collection total.</p>', [btn('Done', 'primary', close)]);
    var body = items.map(function (it, i) {
      var lab = labelOf(it.code);
      if (it.kind === 'misread') return '<div class="result misread" id="r' + i + '"><strong>' + it.code + ' ' + lab + ': ' + it.n + ' short</strong><br><span class="muted small">' + it.unk + ' (unknown) has ' + it.n + ' extra. Likely misread by the camera, not lost.</span><div class="acts"><button type="button" class="btn small" data-r="' + i + '" data-do="ok">OK</button></div></div>';
      if (it.kind === 'missing') return '<div class="result" id="r' + i + '"><strong>' + it.code + ' ' + lab + ': ' + plural(it.n, 'piece') + ' possibly missing</strong><div class="acts"><button type="button" class="btn small" data-r="' + i + '" data-do="gone">Yes, really gone</button><button type="button" class="btn small" data-r="' + i + '" data-do="keep">No, still have it</button></div></div>';
      return '<div class="result" id="r' + i + '"><strong>' + it.code + ' ' + lab + ': ' + it.n + ' more than your total</strong><div class="acts"><button type="button" class="btn small" data-r="' + i + '" data-do="addt">Add to total</button><button type="button" class="btn small" data-r="' + i + '" data-do="ok">Ignore</button></div></div>';
    }).join('');
    sheet('Find What\'s Missing', body, [btn('Done', 'primary', close)]);
    document.querySelectorAll('[data-do]').forEach(function (b) {
      b.addEventListener('click', function () {
        var it = items[+b.dataset.r], d = b.dataset.do, box = $('#r' + b.dataset.r);
        if (d === 'gone') {
          S.total[it.code] -= it.n; dropLost(it.code, it.n);
          log(it.code + ': ' + plural(it.n, 'piece') + ' confirmed gone, total lowered');
        } else if (d === 'keep') log(it.code + ': kept in total (still somewhere)');
        else if (d === 'addt') { S.total[it.code] += it.n; log(it.code + ': ' + it.n + ' added to total'); }
        box.classList.add('done'); box.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
        save(); render();
      });
    });
  }
  function dropLost(c, n) {
    for (var i = S.out.length - 1; i >= 0 && n > 0; i--) if (trueCode(S.out[i]) === c) { S.out.splice(i, 1); n--; }
  }
  function labelOf(c) {
    var f = +c[0], s = +c.split('-')[1];
    return s === 8 ? (f === 1 ? 'Unknown brick' : 'Unknown other') : BINS.slots[s - 1].label + (f === 1 ? ' bricks' : ' other');
  }

  /* ---------- bin sheet: pull out a bin, take pieces ---------- */
  function openBin(c) {
    var n = count(c), take = Math.min(3, n);
    var groups = {};
    S.bins[c].forEach(function (p) { var k = p.color + '|' + p.part; (groups[k] = groups[k] || { p: p, n: 0 }).n++; });
    var list = Object.keys(groups).sort(function (a, b) { return groups[b].n - groups[a].n; }).map(function (k) {
      var g = groups[k]; return '<li><span class="dot" style="background:' + g.p.hex + '"></span><span>' + esc(g.p.color + ' ' + g.p.part) + '</span><span>' + g.n + '</span></li>';
    }).join('');
    var body = '<p><strong>' + plural(n, 'piece') + '</strong>' + (S.total ? ' · collection total ' + S.total[c] : '') + ' · capacity about ' + CAP[c] + (S.flags[c] ? ' · <strong>opened</strong>' : '') + '</p>' +
      '<p class="muted small">Pulling the bin out trips its limit switch, so it gets flagged for the next recount.</p>' +
      (n ? '<p>How many pieces do you take out to play?</p><div class="stepper"><button type="button" class="btn" id="tMinus">−</button><output id="tOut">' + take + '</output><button type="button" class="btn" id="tPlus">+</button></div>' : '') +
      (list ? '<div data-adv><h3>In this bin</h3><ul class="parts">' + list + '</ul></div>' : '');
    sheet('Bin ' + c + ' · ' + labelOf(c), body, [btn('Close', '', close), btn(n ? 'Pull out and take' : 'Pull out bin', 'primary', function () {
      shuffle(S.bins[c]);
      var taken = S.bins[c].splice(0, take);
      S.out = S.out.concat(taken); S.flags[c] = true;
      log('Bin ' + c + ' opened, ' + plural(taken.length, 'piece') + ' taken out');
      save(); close(); render();
    })]);
    if (n) {
      var upd = function () { $('#tOut').textContent = take; };
      $('#tMinus').onclick = function () { take = Math.max(0, take - 1); upd(); };
      $('#tPlus').onclick = function () { take = Math.min(n, take + 1); upd(); };
    }
  }

  /* ---------- dialog helpers ---------- */
  function btn(label, cls, fn) { var b = document.createElement('button'); b.type = 'button'; b.className = 'btn ' + (cls || ''); b.textContent = label; b.onclick = fn; return b; }
  function sheet(title, body, buttons) {
    var d = $('#sheet');
    $('#sheetTitle').textContent = title; $('#sheetBody').innerHTML = body;
    var f = $('#sheetFoot'); f.innerHTML = ''; buttons.forEach(function (b) { f.appendChild(b); });
    if (!d.open) { if (d.showModal) d.showModal(); else d.setAttribute('open', ''); }
  }
  function close() { var d = $('#sheet'); if (d.close) d.close(); else d.removeAttribute('open'); }

  /* ---------- controls ---------- */
  function setView(v) {
    S.view = v; document.body.classList.toggle('advanced', v === 'advanced');
    document.querySelectorAll('.seg').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.mode === v)); });
    save();
  }
  function wire() {
    $('#startBtn').onclick = chooser;
    $('#stopBtn').onclick = stop;
    document.querySelectorAll('[data-action]').forEach(function (b) { b.onclick = function () { confirmAction(b.dataset.action); }; });
    document.querySelectorAll('.seg').forEach(function (b) { b.onclick = function () { setView(b.dataset.mode); }; });
    var sp = $('#speed'); sp.value = S.speed; $('#speedOut').textContent = S.speed + ' pcs/s';
    sp.oninput = function () { S.speed = +sp.value; $('#speedOut').textContent = S.speed + ' pcs/s'; save(); };
    var mr = $('#misread'); mr.value = S.misread; $('#misreadOut').textContent = S.misread + '%';
    mr.oninput = function () { S.misread = +mr.value; $('#misreadOut').textContent = S.misread + '%'; save(); };
    $('#resetBtn').onclick = function () {
      sheet('Reset demo', '<p>Empty every bin and clear the collection total?</p>', [btn('Cancel', '', close), btn('Reset', 'primary', function () { var v = S.view; S = fresh(); S.view = v; save(); close(); render(); })]);
    };
  }

  function init(bins, set) {
    BINS = bins; SET = set;
    codes().forEach(function (c) { EXPECT[c] = 0; });
    SET.parts.forEach(function (p) { EXPECT[trueCode(p)] += p.qty; });
    codes().forEach(function (c) { CAP[c] = Math.max(10, EXPECT[c] * BOXES_CAPACITY); });
    S = load();
    buildBins(); wire(); setView(S.view || 'simple'); idleStages(); render();
  }

  Promise.all([fetch('data/bins.json').then(function (r) { return r.json(); }), fetch('data/set-10696.json').then(function (r) { return r.json(); })])
    .then(function (a) { init(a[0], a[1]); })
    .catch(function () { $('#hint').textContent = 'Could not load the bin table. Reload the page.'; });
})();
