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

  /* ---------- buy list: groups by stage with prices (option A, picked by BJ 2026-11-03) ---------- */
  // Totals only make sense for one build, so the page starts on the planned version (V1 since Nov 8).
  ver = 'v1'; document.querySelectorAll('.filters button[data-v]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-v') === 'v1' ? 'true' : 'false'); });
  var OPEN = {};
  function money(n, approx) { return n == null ? '' : (approx ? '~' : '') + '$' + (Math.round(n * 100) / 100).toFixed(n % 1 ? 2 : 0); }
  function costOf(list) {
    var t = 0, ap = false, un = 0;
    list.forEach(function (p) { if (p.cost == null) { un++; return; } t += p.cost; if (p.approx) ap = true; });
    return { total: t, approx: ap, unpriced: un, text: money(t, ap) + (un ? ' + ' + un + ' unpriced' : '') };
  }
  function shown(list) { return list.filter(function (p) { return filter === 'all' || (filter === 'need' ? !p.bought : p.bought); }); }
  function storeLink(p) {
    var link = safeLink(p.link);
    return p.where ? (link ? '<a href="' + esc(link) + '" target="_blank" rel="noopener noreferrer">' + esc(p.where) + '</a>' : esc(p.where)) : '';
  }
  function row(p, cols) {
    var c = '<li class="crow ' + (p.bought ? 'got' : 'need') + '" title="' + esc(p.what || '') + '">' +
      '<span class="cdot" aria-label="' + (p.bought ? 'Have it' : 'To buy') + '"></span>' +
      '<span class="cname">' + esc(p.part) + (p.note && !p.bought ? '<span class="cnote">' + esc(p.note) + '</span>' : '') +
        '<span class="cmeta">' + [p.qty ? 'Qty ' + esc(p.qty) : '', cols.store ? storeLink(p) : ''].filter(Boolean).join(' · ') + '</span></span>' +
      '<span class="cqty">' + esc(p.qty || '') + '</span>' +
      (cols.store ? '<span class="cstore">' + storeLink(p) + '</span>' : '') +
      '<span class="ccost">' + (p.cost == null ? '<span class="muted">n/a</span>' : money(p.cost, p.approx)) + '</span>' +
      buttons(p).replace('p-acts', 'cacts') + '</li>';
    return c;
  }
  function groupHtml(id, title, list, opts) {
    var all = list, got = all.filter(function (p) { return p.bought; }), need = all.filter(function (p) { return !p.bought; });
    var cAll = costOf(all), cGot = costOf(got), cNeed = costOf(need);
    var pct = cAll.total ? Math.round(cGot.total / cAll.total * 100) : (all.length ? Math.round(got.length / all.length * 100) : 0);
    var open = !!OPEN[id], items = shown(all);
    return '<section class="cgrp' + (open ? ' open' : '') + '"><button type="button" class="cgrp-btn" aria-expanded="' + open + '" data-cg="' + esc(id) + '">' +
      '<span class="cg-name">' + esc(title) + '</span>' +
      '<span class="cg-cost">' + (need.length ? money(cNeed.total, cNeed.approx) + ' to buy' : 'All on hand') + '</span><span class="grp-chev" aria-hidden="true"></span>' +
      '<span class="cg-bar"><i style="width:' + pct + '%"></i></span>' +
      '<span class="cg-sub">' + got.length + ' of ' + all.length + ' on hand · ' + money(cGot.total, cGot.approx) + ' on hand' + (cNeed.unpriced ? ' · ' + cNeed.unpriced + ' unpriced' : '') + '</span></button>' +
      '<ul class="clist"' + (open ? '' : ' hidden') + '>' + (items.length ? items.map(function (p) { return row(p, opts || {}); }).join('') : '<li class="muted small">Nothing here for this filter.</li>') + '</ul></section>';
  }
  function summary(parts) {
    var need = parts.filter(function (p) { return !p.bought; }), got = parts.filter(function (p) { return p.bought; });
    var cN = costOf(need), cG = costOf(got), cA = costOf(parts);
    return { need: need, got: got, cN: cN, cG: cG, cA: cA, pct: cA.total ? Math.round(cG.total / cA.total * 100) : 0 };
  }

  function renderBuyList() {
    // money totals count the machine only; the LEGO test set is listed but not added in
    var all = DATA.parts.filter(inVersion), parts = all.filter(function (p) { return p.stage !== 'test'; }), s = summary(parts), wrap = $('list');
    $('pct').textContent = s.pct + '%'; $('fill').style.width = s.pct + '%';
    $('count').innerHTML = '<b class="money">' + money(s.cN.total, s.cN.approx) + '</b> left to buy' + (s.cN.unpriced ? ' + PLA (slice first)' : '') +
      ' · ' + money(s.cG.total, s.cG.approx) + ' on hand · ' + s.got.length + ' of ' + parts.length + ' parts';
    var labels = DATA.stage_labels || STAGES;
    var html = Object.keys(labels).map(function (st) {
      var l = all.filter(function (p) { return p.stage === st; });
      return l.length ? groupHtml('s-' + st, labels[st], l, { store: true }) : '';
    }).join('');
    wrap.innerHTML = html;
  }

  function show(d, isLive) {
    // The bot keeps only versions and parts; fill the rest from the static file.
    if (STATIC) { d.stage_labels = d.stage_labels || STATIC.stage_labels; d.versions = d.versions || STATIC.versions; d.type_labels = d.type_labels || STATIC.type_labels; }
    DATA = d; live = isLive;
    $('mode').textContent = isLive ? 'Live' : 'Static';
    $('mode').className = 'mode-badge' + (isLive ? ' live' : '');
    renderVersions(d.versions || {});
    renderBuyList();
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
    var g = e.target.closest('button[data-cg]');
    if (g) {
      var open = g.getAttribute('aria-expanded') !== 'true'; OPEN[g.dataset.cg] = open;
      g.setAttribute('aria-expanded', String(open)); g.parentNode.classList.toggle('open', open);
      g.parentNode.querySelector('.clist').hidden = !open; return;
    }
    var b = e.target.closest('button[data-id]'); if (!b) return;
    openDialog(b.dataset.id, b.dataset.b === '1');
  });

  function group(attr, set) {
    document.querySelectorAll('.filters button[' + attr + ']').forEach(function (b) {
      b.addEventListener('click', function () {
        set(b.getAttribute(attr));
        document.querySelectorAll('.filters button[' + attr + ']').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        if (DATA) renderBuyList();
      });
    });
  }
  group('data-f', function (v) { filter = v; });
  group('data-v', function (v) { ver = v; });

  load();
  if (API) setInterval(function () { if (!document.hidden && !$('dlg').open) load(); }, 30000);
})();
