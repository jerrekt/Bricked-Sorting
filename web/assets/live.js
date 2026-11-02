/* Live page: reads /live/state once, then long-polls /live/events for new pieces.
   The team password is kept only in this page's memory, never saved. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var API = ((document.querySelector('meta[name="bricked-api"]') || {}).content || '').replace(/\/+$/, '');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var BINS = null, NAMES = ['Branden', 'Ethan', 'Marshall', 'Vivek'];
  var lastId = 0, mode = 'idle', counts = { live: {}, sim: {} }, recent = [], queue = [], busy = false, pass = '', lastName = '';

  function slotInfo(slot) { return BINS.slots.filter(function (s) { return s.slot === slot; })[0] || {}; }
  function shown() { return mode === 'sim' ? counts.sim : counts.live; }

  function buildBins() {
    [2, 1].forEach(function (f) {
      var el = $('floor' + f); el.innerHTML = '';
      BINS.slots.forEach(function (s) {
        var code = f + '-' + s.slot, d = document.createElement('div');
        d.className = 'bin'; d.id = 'bin-' + code;
        d.innerHTML = '<div class="bin-code">' + code + '</div>' +
          (s.swatch ? '<span class="bin-sw" style="background:' + esc(s.swatch) + '"></span>' : '<span class="bin-sw unk"></span>') +
          '<div class="bin-label">' + esc(s.label) + '</div><div class="bin-count" id="cnt-' + code + '">0</div>';
        el.appendChild(d);
      });
    });
  }

  function drawCounts() {
    var c = shown(), sums = { 1: 0, 2: 0 };
    [1, 2].forEach(function (f) { BINS.slots.forEach(function (s) {
      var code = f + '-' + s.slot, n = c[code] || 0; sums[f] += n;
      var el = $('cnt-' + code); if (el) el.textContent = n;
    }); });
    $('f1sum').textContent = sums[1] + (sums[1] === 1 ? ' piece' : ' pieces'); $('f2sum').textContent = sums[2] + (sums[2] === 1 ? ' piece' : ' pieces');
  }

  var MODE_TEXT = { live: ['Live camera', 'live', 'Pieces from the camera, identified on our server.'],
                    sim: ['Simulator', 'sim', 'Fake pieces from the real 10696 parts list. Marshall\'s bins can follow along.'],
                    idle: ['Idle', 'off', 'No pieces in the last minute. Start the simulator, or run the camera.'],
                    off: ['Not connected', 'off', 'Can\'t reach the server right now. Retrying.'] };
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

  function showPiece(e) {
    $('p-code').textContent = e.code;
    $('p-name').textContent = e.name || 'Piece';
    $('p-meta').innerHTML = esc(e.color || '') + (e.confidence != null ? ' · ' + Math.round(e.confidence * 100) + '% sure' : '') +
      ' · <span class="tag' + (e.source === 'sim' ? ' sim' : '') + '">' + (e.source === 'sim' ? 'simulated' : 'camera') + '</span>';
    var th = $('thumb');
    if (e.has_image) th.innerHTML = '<img alt="Camera photo of the piece" src="' + API + '/live/img/' + e.id + '.jpg">';
    else th.innerHTML = '<span class="blk" style="background:' + esc(colorFor(e)) + '"></span>';
  }

  function addRecent(e) {
    recent.unshift(e); recent = recent.slice(0, 12);
    $('recent').innerHTML = recent.map(function (r) {
      var t = new Date(r.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return '<li><span class="r-time">' + t + '</span><span class="r-code">' + esc(r.code) + '</span><span class="r-name">' + esc(r.name) +
        '</span><span class="tag' + (r.source === 'sim' ? ' sim' : '') + '">' + (r.source === 'sim' ? 'sim' : 'cam') + '</span></li>';
    }).join('');
    $('recent-empty').hidden = recent.length > 0;
  }

  function play(e) {
    var c = counts[e.source]; c[e.code] = (c[e.code] || 0) + 1;
    showPiece(e); addRecent(e);
    var bin = $('bin-' + e.code);
    if (bin && !reduce && e.source === (mode === 'sim' ? 'sim' : 'live')) {
      var d = document.createElement('span'); d.className = 'drop'; d.style.background = colorFor(e);
      bin.appendChild(d); setTimeout(function () { d.remove(); }, 650);
      bin.classList.remove('pulse'); void bin.offsetWidth; bin.classList.add('pulse');
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
      recent = []; evs.slice(-12).forEach(addRecent);
      if (evs.length) showPiece(evs[evs.length - 1]);
      drawCounts(); $('ctl').hidden = false;
    });
  }

  function poll() {
    getJSON(API + '/live/events?after=' + lastId + '&wait=25').then(function (r) {
      if (r.mode !== mode) loadState().catch(function () {});
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

  fetch('data/bins.json').then(function (r) { return r.json(); }).then(function (b) {
    BINS = b; buildBins(); drawCounts();
    if (!API) { setMode('off'); return; }
    loadState().then(poll, function () { setMode('off'); setTimeout(function () { loadState().then(poll, function () {}); }, 5000); });
  });
})();
