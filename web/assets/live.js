/* Live page: reads /live/state once, then long-polls /live/events for new pieces.
   The team password is kept only in this page's memory, never saved. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var API = ((document.querySelector('meta[name="bricked-api"]') || {}).content || '').replace(/\/+$/, '');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var BINS = null, NAMES = ['Branden', 'Ethan', 'Marshall', 'Vivek'];
  var TEST = /[?&]test=bins\b/.test(location.search);
  var binState = { sensors: false, open: {}, recount: [], drawers_open: [] };
  var lastId = 0, mode = 'idle', counts = { live: {}, sim: {} }, recent = [], queue = [], busy = false, pass = '', lastName = '';
  var seen = { live: [], sim: [] }, seenIds = {};  /* pieces since this page opened, for the Identify stats */

  function slotInfo(slot) { return BINS.slots.filter(function (s) { return s.slot === slot; })[0] || {}; }
  function shown() { return mode === 'sim' ? counts.sim : counts.live; }

  /* ---------- bin piles and fill bars, same look as the Demo page ----------
     Capacity matches the Demo: what 3 LEGO 10696 boxes put in each bin (placeholder bin sizes).
     Counts come from the server, so a pile is rebuilt from its count with that bin's color;
     pieces that arrive while the page is open drop in with their real shape and color. */
  var BOXES_CAPACITY = 3, CAP = {}, PW = 80, PH = 64, piles = {}, animating = false, DROP = 280;
  function codesAll() { var a = []; [2, 1].forEach(function (f) { for (var s = 1; s <= 8; s++) a.push(f + '-' + s); }); return a; }
  function setCaps(set) {
    var exp = {}; codesAll().forEach(function (c) { exp[c] = 0; });
    var slotOfKey = {}; BINS.slots.forEach(function (s) { slotOfKey[s.key] = s.slot; });
    (set && set.parts || []).forEach(function (p) {
      var c = (p.brick ? 1 : 2) + '-' + (slotOfKey[BINS.colorMap[p.color] || 'unknown'] || 8); exp[c] += p.qty;
    });
    codesAll().forEach(function (c) { CAP[c] = Math.max(10, exp[c] * BOXES_CAPACITY); });
    [1, 2].forEach(function (f) { var n = 0; for (var s = 1; s <= 7; s++) n += exp[f + '-' + s]; CAP[f + '-8'] += Math.ceil(n * 0.05 * BOXES_CAPACITY); });
  }
  function shapeOf(name) {
    name = name || '';
    if (/^Brick \d+ x \d+/.test(name)) return [20, 9];
    if (/Tire|Wheel/.test(name)) return [10, 10];
    if (/Round|Cone/.test(name)) return [8, 9];
    if (/^Plate|^Tile/.test(name)) return [20, 4];
    if (/Slope/.test(name)) return [14, 8];
    return [16, 7];
  }
  function pileFor(c) {
    if (piles[c]) return piles[c];
    var cv = document.querySelector('#bin-' + c + ' .pile'); if (!cv) return null;
    var sc = Math.min(1, Math.sqrt((PW * PH * 0.5) / (CAP[c] || 60) / 120));
    return (piles[c] = { cv: cv, x: cv.getContext('2d'), hm: new Array(PW).fill(0), items: [], sc: sc });
  }
  function place(pl, name, hex, brickFloor) {
    var d = shapeOf(name || (brickFloor ? 'Brick 2 x 2' : '')), w = Math.max(3, d[0] * pl.sc), h = Math.max(2, d[1] * pl.sc), best = 1e9, xs = [];
    for (var x0 = 0; x0 <= PW - w; x0 += 1) {
      var m = 0; for (var i = Math.floor(x0); i < Math.ceil(x0 + w); i++) if (pl.hm[i] > m) m = pl.hm[i];
      xs.push([x0, m]); if (m < best) best = m;
    }
    var near = xs.filter(function (q) { return q[1] <= best + h * 0.3; }), pk = near[Math.floor(Math.random() * near.length)];
    var top = Math.min(pk[1] + h, PH + 40);
    for (var j = Math.floor(pk[0]); j < Math.ceil(pk[0] + w); j++) pl.hm[j] = top;
    return { x: pk[0], y: pk[1], w: w, h: h, hex: hex, rot: (Math.random() - 0.5) * 0.12, t0: 0,
      studs: (brickFloor || /^(Brick|Plate) \d/.test(name || '')) && w > 8 };
  }
  function pileRebuild(c, n) {
    var pl = pileFor(c); if (!pl) return;
    var slot = +c.split('-')[1], hex = slotInfo(slot).swatch || '#9aa0a6', brickFloor = c.charAt(0) === '1';
    pl.hm.fill(0); pl.items = [];
    for (var i = 0; i < n; i++) pl.items.push(place(pl, '', hex, brickFloor));
    drawPile(c);
  }
  function pileAdd(e) {
    var pl = pileFor(e.code); if (!pl) return;
    var it = place(pl, e.name, colorFor(e), e.code.charAt(0) === '1');
    it.t0 = reduce ? 0 : performance.now(); pl.items.push(it); pl.dirty = true;
    if (it.t0) kick(); else drawPile(e.code);
  }
  function kick() { if (!animating) { animating = true; requestAnimationFrame(frame); } }
  function frame(t) {
    var any = false;
    Object.keys(piles).forEach(function (c) { var pl = piles[c]; if (pl.dirty) { if (drawPile(c, t)) any = true; else pl.dirty = false; } });
    if (any) requestAnimationFrame(frame); else animating = false;
  }
  function drawPile(c, t) {
    var pl = piles[c], x = pl.x, k = pl.cv.width / PW, moving = false;
    t = t || performance.now();
    x.setTransform(k, 0, 0, k, 0, 0); x.clearRect(0, 0, PW, PH);
    for (var i = Math.max(0, pl.items.length - 400); i < pl.items.length; i++) {
      var it = pl.items[i], yb = PH - it.y, rot = it.rot;
      if (it.t0) {
        var u = (t - it.t0) / DROP;
        if (u < 1) { moving = true; yb = -2 + (yb + 2) * u * u; rot = it.rot * u; } else it.t0 = 0;
      }
      if (yb - it.h > PH) continue;
      x.save(); x.translate(it.x + it.w / 2, yb - it.h / 2); x.rotate(rot);
      x.fillStyle = it.hex; x.fillRect(-it.w / 2, -it.h / 2, it.w, it.h);
      x.strokeStyle = 'rgba(0,0,0,.35)'; x.lineWidth = 0.6; x.strokeRect(-it.w / 2 + 0.3, -it.h / 2 + 0.3, it.w - 0.6, it.h - 0.6);
      if (it.h > 3) { x.fillStyle = 'rgba(255,255,255,.28)'; x.fillRect(-it.w / 2 + 1, -it.h / 2 + 0.8, it.w - 2, Math.max(0.6, it.h * 0.15)); }
      if (it.studs) { x.fillStyle = it.hex; var sw = Math.max(1.5, it.w * 0.18), sh = Math.max(1, it.h * 0.3); x.fillRect(-it.w * 0.3 - sw / 2, -it.h / 2 - sh, sw, sh); x.fillRect(it.w * 0.3 - sw / 2, -it.h / 2 - sh, sw, sh); }
      x.restore();
    }
    return moving;
  }

  function buildBins() {
    [2, 1].forEach(function (f) {
      var el = $('floor' + f); el.innerHTML = '';
      BINS.slots.forEach(function (s) {
        var code = f + '-' + s.slot, d = document.createElement('div');
        d.className = 'bin'; d.id = 'bin-' + code;
        d.innerHTML = '<div class="bin-code">' + code + '</div>' +
          (s.swatch ? '<span class="bin-sw" style="background:' + esc(s.swatch) + '"></span>' : '<span class="bin-sw unk"></span>') +
          '<div class="bin-label">' + esc(s.label) + '</div><span class="bin-flag" id="flag-' + code + '" hidden></span>' +
          '<div class="bin-count" id="cnt-' + code + '">0</div>' +
          '<canvas class="pile" width="160" height="128" aria-hidden="true"></canvas><span class="fill" title="How full, sized for 3 boxes"><i></i></span>';
        el.appendChild(d);
      });
    });
  }

  function drawCounts() {
    var c = shown(), sums = { 1: 0, 2: 0 };
    [1, 2].forEach(function (f) { BINS.slots.forEach(function (s) {
      var code = f + '-' + s.slot, n = c[code] || 0; sums[f] += n;
      var el = $('cnt-' + code); if (el) el.textContent = n;
      var bin = $('bin-' + code); if (!bin) return;
      var pct = Math.min(100, Math.round(n / (CAP[code] || 60) * 100));
      bin.querySelector('.fill i').style.width = pct + '%';
      bin.classList.toggle('full', pct >= 80);
      var pl = pileFor(code); if (pl && pl.items.length !== n) pileRebuild(code, n);
    }); });
    $('f1sum').textContent = sums[1] + (sums[1] === 1 ? ' piece' : ' pieces'); $('f2sum').textContent = sums[2] + (sums[2] === 1 ? ' piece' : ' pieces');
  }

  /* bin switches: a lifted bin is open; once it goes back its count needs a recount */
  function binName(code) {
    var m = /^([12])-([1-8])$/.exec(code);
    if (m) {
      var fl = BINS.floors.filter(function (f) { return f.floor === +m[1]; })[0] || {};
      return (fl.label || 'Floor ' + m[1]) + ' · ' + (slotInfo(+m[2]).label || 'slot ' + m[2]) + ' (' + code + ')';
    }
    return (code.charAt(0) === 'F' ? 'Front drawer' : 'Back drawer') + ' · bin ' + code;
  }

  function drawBins(b) {
    if (!b || !BINS) return;
    binState = b;
    var open = b.open || {}, rec = b.recount || [];
    [1, 2].forEach(function (f) { BINS.slots.forEach(function (s) {
      var code = f + '-' + s.slot, el = $('bin-' + code), flag = $('flag-' + code);
      if (!el) return;
      var isOpen = code in open, isRec = !isOpen && rec.indexOf(code) >= 0;
      el.classList.toggle('is-open', isOpen); el.classList.toggle('is-recount', isRec);
      flag.hidden = !(isOpen || isRec); flag.textContent = isOpen ? 'Open' : 'Recount';
    }); });
    var lines = [];
    (b.drawers_open || []).forEach(function (d) {
      lines.push('<li><b>' + (d === 'front' ? 'Front' : 'Back') + ' drawer is out.</b> The machine waits until it is closed.</li>');
    });
    Object.keys(open).sort().forEach(function (code) {
      lines.push('<li><b>' + esc(binName(code)) + ' is open.</b> Its count stops being trusted.</li>');
    });
    if (rec.length) {
      lines.push('<li><b>Recount:</b> ' + rec.map(function (c) { return esc(binName(c)); }).join(', ') +
        '. Pour only ' + (rec.length === 1 ? 'that bin' : 'those bins') + ' back into the hopper, then Reset counts.</li>');
    }
    $('bin-alert-list').innerHTML = lines.join('');
    $('bin-alert').hidden = !lines.length;
    $('sensors').textContent = TEST ? 'Bin switches: test mode (fake, this page only)' :
      b.sensors ? 'Bin switches: reporting' : 'Bin switches: not reporting';
    $('sensors').className = 'sensors' + (b.sensors || TEST ? ' on' : '');
  }

  /* ?test=bins: fake switch changes in this page only, so the look can be checked without the Pi */
  function testBins() {
    var steps = [
      { sensors: true, open: {}, recount: [], drawers_open: [] },
      { sensors: true, open: { '1-1': 1 }, recount: [], drawers_open: [] },
      { sensors: true, open: {}, recount: ['1-1'], drawers_open: [] },
      { sensors: true, open: { '2-4': 1 }, recount: ['1-1'], drawers_open: ['front'] },
      { sensors: true, open: {}, recount: ['1-1', '2-4'], drawers_open: [] }
    ], i = 0;
    (function next() { drawBins(steps[i]); i = (i + 1) % steps.length; setTimeout(next, 3000); })();
  }

  var MODE_TEXT = { live: ['Live camera', 'live', 'Pieces from the camera, identified on our server.'],
                    sim: ['Simulator', 'sim', 'Fake pieces from the real 10696 parts list. Marshall\'s bins can follow along.'],
                    idle: ['Idle', 'off', 'No pieces in the last minute. Put a piece under the camera, or open Testing tools below.'],
                    off: ['Machine off', 'off', 'The machine is not running right now. This page updates on its own when it comes back; try the Demo meanwhile.'] };
  function setMode(m, sim) {
    mode = m; var t = MODE_TEXT[m] || MODE_TEXT.idle;
    $('mode').textContent = t[0]; $('mode').className = 'mode ' + t[1];
    var sub = t[2];
    if (m === 'sim' && sim && sim.until) {
      var left = Math.max(0, Math.round((sim.until * 1000 - Date.now()) / 60000));
      sub += ' Started by ' + (sim.by || 'someone') + ', stops in about ' + left + ' min.';
    }
    $('sub').textContent = sub;
  }

  function colorFor(e) { return e.hex || slotInfo(e.slot).swatch || '#9aa0a6'; }

  function pct(v) { return v == null ? null : Math.round(v * 100); }
  function level(v) { return v == null ? '' : v >= 0.8 ? 'hi' : v >= 0.6 ? 'mid' : 'lo'; }
  function meter(bar, val, v) {
    var p = pct(v);
    $(bar).style.width = (p == null ? 0 : p) + '%'; $(bar).className = level(v);
    $(val).textContent = p == null ? '–' : p + '%';
  }
  function binLabel(e) {
    if (!BINS || e.floor == null) return '';
    var fl = BINS.floors.filter(function (f) { return f.floor === e.floor; })[0] || {};
    return (slotInfo(e.slot).label || '') + (fl.label ? ' · ' + fl.label : '');
  }
  function srcTag(e) {
    return '<span class="tag' + (e.source === 'sim' ? ' sim' : '') + '">' + (e.source === 'sim' ? 'simulated' : 'camera') + '</span>';
  }

  function showPiece(e) {
    $('p-code').textContent = e.code;
    $('p-binlabel').textContent = binLabel(e);
    $('p-name').textContent = e.name || 'Piece';
    var sub = [];
    if (e.part_id) sub.push('Part ' + e.part_id);
    if (e.category) sub.push(e.category);
    if (e.shape) sub.push(e.shape);
    $('p-sub').textContent = sub.join(' · ');
    meter('m-piece', 'v-piece', e.confidence);
    $('p-color').textContent = e.color || 'Color';
    $('p-sw').style.background = colorFor(e);
    meter('m-color', 'v-color', e.color_confidence);
    var t = new Date(e.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    $('p-tags').innerHTML = srcTag(e) + '<span>' + t + '</span>' + (e.confidence != null && e.confidence < 0.6 ? '<span class="tag">low match</span>' : '');
    var sh = $('shot');
    if (e.has_image) sh.innerHTML = '<img alt="Camera photo of the piece" src="' + API + '/live/img/' + e.id + '.jpg">';
    else sh.innerHTML = '<span class="blk" style="background:' + esc(colorFor(e)) + '"></span>';
  }

  function addRecent(e) {
    recent.unshift(e); recent = recent.slice(0, 12);
    $('recent').innerHTML = recent.map(function (r) {
      var t = new Date(r.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      var th = r.has_image ? '<img alt="" loading="lazy" src="' + API + '/live/img/' + r.id + '.jpg">' :
        '<span class="sw" style="background:' + esc(colorFor(r)) + '"></span>';
      var c = pct(r.confidence);
      return '<li><span class="r-th">' + th + '</span><span class="r-time">' + t + '</span><span class="r-code">' + esc(r.code) +
        '</span><span class="r-name">' + esc(r.name) + '</span><span class="r-conf">' + (c == null ? '' : c + '%') +
        '</span><span class="tag' + (r.source === 'sim' ? ' sim' : '') + '">' + (r.source === 'sim' ? 'sim' : 'cam') + '</span></li>';
    }).join('');
    $('recent-empty').hidden = recent.length > 0;
  }

  /* Identify stats for the source on screen (camera, or the simulator while it runs) */
  function note(e) {
    if (seenIds[e.id]) return; seenIds[e.id] = 1;
    (seen[e.source] || (seen[e.source] = [])).push(e);
  }
  function ago(ts) {
    if (!ts) return '–';
    var s = Math.max(0, Math.round(Date.now() / 1000 - ts));
    return s < 60 ? s + ' s ago' : s < 3600 ? Math.round(s / 60) + ' min ago' : Math.round(s / 3600) + ' h ago';
  }
  function drawStats() {
    var list = seen[mode === 'sim' ? 'sim' : 'live'] || [];
    var conf = list.filter(function (e) { return e.confidence != null; });
    var avg = conf.length ? conf.reduce(function (a, e) { return a + e.confidence; }, 0) / conf.length : null;
    $('st-n').textContent = list.length;
    $('st-avg').textContent = avg == null ? '–' : Math.round(avg * 100) + '%';
    $('st-low').textContent = conf.filter(function (e) { return e.confidence < 0.6; }).length;
    $('st-unk').textContent = list.filter(function (e) { return e.slot === 8; }).length;
    $('st-last').textContent = list.length ? ago(list[list.length - 1].ts) : '–';
  }
  setInterval(drawStats, 1000);

  function play(e) {
    var c = counts[e.source]; c[e.code] = (c[e.code] || 0) + 1;
    note(e); showPiece(e); addRecent(e); drawStats();
    var bin = $('bin-' + e.code);
    if (bin && e.source === (mode === 'sim' ? 'sim' : 'live')) {
      var pl = pileFor(e.code);
      if (pl && pl.items.length === (c[e.code] || 0) - 1) pileAdd(e);
      if (!reduce) { bin.classList.remove('pulse'); void bin.offsetWidth; bin.classList.add('pulse'); }
    }
    drawCounts();
  }

  function pump() {
    if (busy || !queue.length) return;
    busy = true;
    while (queue.length > 8) { var skip = queue.shift(); counts[skip.source][skip.code] = (counts[skip.source][skip.code] || 0) + 1; addRecent(skip); }
    play(queue.shift());
    setTimeout(function () { busy = false; pump(); }, reduce ? 50 : 350);
  }

  function getJSON(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }

  function loadState() {
    return getJSON(API + '/live/state').then(function (s) {
      lastId = s.last_id; counts = s.counts; setMode(s.mode, s.sim);
      var evs = s.events || [];
      recent = []; evs.slice(-12).forEach(addRecent); evs.forEach(note); drawStats();
      if (evs.length) showPiece(evs[evs.length - 1]);
      drawCounts(); $('ctl').hidden = false; $('b-reset').hidden = false;
      if (!TEST) drawBins(s.bins);
    });
  }

  function poll() {
    getJSON(API + '/live/events?after=' + lastId + '&wait=25').then(function (r) {
      if (r.mode !== mode) loadState().catch(function () {});
      if (r.bins && !TEST) drawBins(r.bins);
      (r.events || []).forEach(function (e) { if (e.id > lastId) { lastId = e.id; queue.push(e); } });
      pump(); setTimeout(poll, r.busy ? 3000 : 100);
    }, function () { setMode('off'); setTimeout(function () { loadState().then(poll, function () { setTimeout(poll, 5000); }); }, 3000); });
  }

  /* controls */
  var pending = null;
  function ask(action, title) {
    pending = action; $('dlg-title').textContent = title;
    $('dlg-name').innerHTML = '<option value="">Pick your name</option>' + NAMES.map(function (n) { return '<option>' + esc(n) + '</option>'; }).join('');
    $('dlg-name').value = lastName; $('dlg-pass').value = pass; $('dlg-err').textContent = '';
    $('dlg').showModal(); ($('dlg-name').value ? $('dlg-pass') : $('dlg-name')).focus();
  }
  $('b-start').addEventListener('click', function () { ask('start', 'Start simulator'); });
  $('b-stop').addEventListener('click', function () { ask('stop', 'Stop simulator'); });
  $('b-reset').addEventListener('click', function () { ask('reset', 'Reset bin counts'); });
  $('dlg-cancel').addEventListener('click', function () { $('dlg').close(); });
  $('dlg-form').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var name = $('dlg-name').value, pw = $('dlg-pass').value;
    if (!name) { $('dlg-err').textContent = 'Pick your name.'; return; }
    $('dlg-ok').disabled = true;
    fetch(API + '/live/control', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, password: pw, action: pending, rate: +$('rate').value, minutes: 5 }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        $('dlg-ok').disabled = false;
        if (!res.ok) { $('dlg-err').textContent = res.j.detail || 'That did not work. Try again.'; return; }
        pass = pw; lastName = name; $('dlg').close(); loadState().catch(function () {});
      }, function () { $('dlg-ok').disabled = false; $('dlg-err').textContent = 'Could not reach the server.'; });
  });

  Promise.all([fetch('data/bins.json').then(function (r) { return r.json(); }),
               fetch('data/set-10696.json').then(function (r) { return r.json(); }).catch(function () { return null; })]).then(function (a) {
    BINS = a[0]; setCaps(a[1]); buildBins(); drawCounts();
    if (TEST) testBins();
    if (!API) { setMode('off'); return; }
    (function start(delay) {  /* keep trying until the server answers (it may be off or restarting) */
      loadState().then(poll, function () { setMode('off'); setTimeout(function () { start(Math.min(delay * 2, 30000)); }, delay); });
    })(5000);
  });
})();
