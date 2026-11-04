/* Parts / buy list. Reads the claim server when <meta name="bricked-api"> is set and reachable;
   otherwise shows data/build_parts.json read-only. The team password is kept only in this
   page's memory, never saved. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var API = ((document.querySelector('meta[name="bricked-api"]') || {}).content || '').replace(/\/+$/, '');
  var STAGES = { identify: 'Identify', isolate: 'Isolate', indicate: 'Indicate', power: 'Power and wiring', structure: 'Structure', test: 'Test material' };
  var VLABEL = { all: 'Every version', v1: 'V1 only', v2: 'V2 only', v3: 'V3 only', 'v1+v2': 'V1 + V2 (Pi)' };
  var filter = 'all', ver = 'all', DATA = null, STATIC = null, live = false, pass = '', lastName = '';

  function inVersion(p) { return ver === 'all' || p.versions === 'all' || String(p.versions || 'all').split('+').indexOf(ver) >= 0; }
  function safeLink(u) { return /^https:\/\//.test(u || '') ? u : ''; }

  function renderVersions(v) {
    var g = $('vgrid'); g.innerHTML = '';
    ['v1', 'v2', 'v3'].forEach(function (k) {
      var x = v[k]; if (!x) return;
      var d = document.createElement('div'); d.className = 'vcard';
      d.innerHTML = '<span class="vtag' + (x.tag === 'Planned' ? ' planned' : '') + '">' + esc(x.tag || '') + '</span>' +
        '<div class="vtop"><h3>' + esc(x.name) + '</h3><span class="vcost">' + esc(x.cost || '') + '</span></div>' +
        '<p>' + esc(x.how) + '</p>' + (x.pro ? '<p><b>Good:</b> ' + esc(x.pro) + '</p>' : '') + (x.con ? '<p><b>Catch:</b> ' + esc(x.con) + '</p>' : '');
      g.appendChild(d);
    });
  }

  function buttons(p) {
    if (!live || !DATA.writes) return '';
    return '<span class="p-acts"><button type="button"' + (p.bought ? '' : ' class="pri"') + ' data-id="' + esc(p.id) + '" data-b="' + (p.bought ? '0' : '1') + '">' +
      (p.bought ? 'Mark not bought' : 'Mark bought') + '</button></span>';
  }

  function renderList() {
    var parts = DATA.parts.filter(inVersion);
    var got = parts.filter(function (p) { return p.bought; }).length;
    var pct = parts.length ? Math.round(got / parts.length * 100) : 0;
    $('pct').textContent = pct + '%'; $('fill').style.width = pct + '%';
    $('count').textContent = got + ' of ' + parts.length + ' on hand · ' + (parts.length - got) + ' to buy';
    var wrap = $('list'); wrap.innerHTML = '';
    var labels = DATA.stage_labels || STAGES;
    Object.keys(labels).forEach(function (st) {
      var items = parts.filter(function (p) { return p.stage === st && (filter === 'all' || (filter === 'need' ? !p.bought : p.bought)); });
      if (!items.length) return;
      var sec = document.createElement('section'); sec.className = 'stage';
      sec.innerHTML = '<h3>' + esc(labels[st]) + '</h3>';
      var ul = document.createElement('ul'); ul.className = 'plist';
      items.forEach(function (p) {
        var link = safeLink(p.link);
        var where = p.where ? (link ? '<a href="' + esc(link) + '" target="_blank" rel="noopener noreferrer">' + esc(p.where) + '</a>' : esc(p.where)) : '';
        var li = document.createElement('li'); li.className = 'part ' + (p.bought ? 'got' : 'need');
        li.innerHTML = '<span class="p-st">' + (p.bought ? 'Have it' : 'To buy') + '</span><span class="p-name">' + esc(p.part) + '</span>' +
          '<span class="p-price">' + esc(p.price || '') + '</span>' +
          '<span class="p-meta">' + (p.qty ? '<span>Qty ' + esc(p.qty) + '</span>' : '') + (where ? '<span>' + where + '</span>' : '') +
          '<span>' + esc(VLABEL[p.versions] || p.versions || '') + '</span><code>' + esc(p.id) + '</code>' +
          (p.bought && p.bought_by ? '<span>by ' + esc(p.bought_by) + '</span>' : '') + '</span>' +
          (p.what ? '<span class="p-what">' + esc(p.what) + '</span>' : '') +
          (p.note ? '<span class="p-note">' + esc(p.note) + '</span>' : '') + buttons(p);
        ul.appendChild(li);
      });
      sec.appendChild(ul); wrap.appendChild(sec);
    });
    if (!wrap.children.length) wrap.innerHTML = '<p class="muted">Nothing here.</p>';
  }

  function show(d, isLive) {
    // The bot keeps only versions and parts; fill the rest from the static file.
    if (STATIC) { d.stage_labels = d.stage_labels || STATIC.stage_labels; d.versions = d.versions || STATIC.versions; }
    DATA = d; live = isLive;
    $('mode').textContent = isLive ? 'Live' : 'Static';
    $('mode').className = 'mode-badge' + (isLive ? ' live' : '');
    renderVersions(d.versions || {}); renderList();
  }

  function getJSON(url, ms) {
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = ctl && setTimeout(function () { ctl.abort(); }, ms);
    return fetch(url, { cache: 'no-store', signal: ctl && ctl.signal }).then(function (r) {
      clearTimeout(timer); if (!r.ok) throw new Error(r.status); return r.json();
    });
  }

  function load() {
    var staticLoad = function () { return getJSON('data/build_parts.json', 8000).then(function (d) { STATIC = d; show(d, false); }); };
    var first = STATIC ? Promise.resolve() : getJSON('data/build_parts.json', 8000).then(function (d) { STATIC = d; }, function () {});
    if (!API) return staticLoad();
    return first.then(function () { return getJSON(API + '/api/parts', 4000); }).then(function (d) { show(d, true); }, staticLoad);
  }

  /* ----- mark bought dialog ----- */
  var pending = null;
  function openDialog(id, bought) {
    var p = DATA.parts.filter(function (x) { return x.id === id; })[0]; if (!p) return;
    pending = { id: id, bought: bought };
    $('dlg-title').textContent = (bought ? 'Mark bought: ' : 'Mark not bought: ') + p.part;
    var sel = $('dlg-name'); sel.innerHTML = '<option value="">Pick your name</option>' +
      (DATA.names || []).map(function (n) { return '<option>' + esc(n) + '</option>'; }).join('');
    sel.value = lastName; $('dlg-pass').value = pass; $('dlg-err').textContent = '';
    $('dlg').showModal();
    (sel.value ? (pass ? $('dlg-ok') : $('dlg-pass')) : sel).focus();
  }

  $('dlg-cancel').addEventListener('click', function () { $('dlg').close(); });
  $('dlg-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var name = $('dlg-name').value, pw = $('dlg-pass').value;
    if (!name) { $('dlg-err').textContent = 'Pick your name.'; return; }
    $('dlg-ok').disabled = true; $('dlg-err').textContent = '';
    fetch(API + '/api/parts/' + encodeURIComponent(pending.id), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, password: pw, bought: pending.bought })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      $('dlg-ok').disabled = false;
      if (!res.ok) { $('dlg-err').textContent = res.j.detail || 'That did not save. Try again.'; return; }
      pass = pw; lastName = name;
      $('dlg').close(); load();
    }, function () {
      $('dlg-ok').disabled = false; $('dlg-err').textContent = 'Could not reach the server. Try again in a minute.';
    });
  });

  $('list').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-id]'); if (!b) return;
    openDialog(b.dataset.id, b.dataset.b === '1');
  });

  function group(attr, set) {
    document.querySelectorAll('.filters button[' + attr + ']').forEach(function (b) {
      b.addEventListener('click', function () {
        set(b.getAttribute(attr));
        document.querySelectorAll('.filters button[' + attr + ']').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        if (DATA) renderList();
      });
    });
  }
  group('data-f', function (v) { filter = v; });
  group('data-v', function (v) { ver = v; });

  load();
  if (API) setInterval(function () { if (!document.hidden && !$('dlg').open) load(); }, 30000);
})();
