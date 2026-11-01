/* Task board. Reads the claim server when <meta name="bricked-api"> is set and reachable;
   otherwise shows data/tasks.json read-only. The team password is kept only in this
   page's memory, never saved. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var STATUS_LABEL = { todo: 'To do', in_progress: 'In progress', blocked: 'Blocked', done: 'Done' };
  var API = ((document.querySelector('meta[name="bricked-api"]') || {}).content || '').replace(/\/+$/, '');
  var filter = 'all', DATA = null, live = false, pass = '', lastName = '';

  function dueLabel(due) {
    var days = Math.round((new Date(due + 'T00:00:00') - new Date(new Date().toDateString())) / 86400000);
    var when = days < 0 ? 'past due' : days === 0 ? 'today' : days === 1 ? 'tomorrow' : 'in ' + days + ' days';
    return { text: due + ' · ' + when, soon: days <= 7, past: days < 0 };
  }

  function renderProgress(p) {
    var done = p.milestones.filter(function (m) { return m.complete; }).length;
    var pct = Math.round((done / p.milestones.length) * 100);
    $('pg-pct').textContent = pct + '%';
    $('pg-fill').style.width = pct + '%';
    $('pg-note').textContent = done + ' of ' + p.milestones.length + ' milestones complete · ' + p.note;
    var list = $('pg-list'); list.innerHTML = '';
    p.milestones.forEach(function (m) {
      var li = document.createElement('li');
      li.className = 'pg-row' + (m.complete ? ' done' : '');
      li.innerHTML = '<span class="pg-dot"></span><span class="pg-label">' + esc(m.label) + '</span><span class="pg-ev">' + esc(m.evidence) + '</span>';
      list.appendChild(li);
    });
  }

  function renderDeadlines(d) {
    var box = $('deadlines'); if (!box) return;
    var items = d.tasks.filter(function (t) { return t.due && t.status !== 'done'; })
      .sort(function (a, b) { return a.due < b.due ? -1 : 1; });
    box.hidden = !items.length;
    var ul = $('dl-list'); ul.innerHTML = '';
    items.forEach(function (t) {
      var dl = dueLabel(t.due);
      var li = document.createElement('li'); li.className = 'dl-row' + (dl.past ? ' past' : dl.soon ? ' soon' : '');
      li.innerHTML = '<span class="dl-date">' + esc(dl.text) + '</span><span class="dl-title">' + esc(t.title) + '</span><span class="t-owner">' + esc(t.owner || 'Open') + '</span>';
      ul.appendChild(li);
    });
  }

  function unowned(o) { return !o || o === 'All'; }

  function buttons(t) {
    if (!live || !DATA.writes) return '';
    var b = [];
    if (unowned(t.owner) && t.status !== 'done') b.push(['claim', null, 'Claim', 1]);
    if (!unowned(t.owner)) {
      if (t.status !== 'in_progress') b.push(['status', 'in_progress', 'Start']);
      if (t.status !== 'blocked') b.push(['status', 'blocked', 'Blocked']);
      if (t.status !== 'done') b.push(['status', 'done', 'Done', 1]);
      b.push(['release', null, 'Release']);
    }
    return '<span class="t-acts">' + b.map(function (x) {
      return '<button type="button"' + (x[3] ? ' class="pri"' : '') + ' data-id="' + esc(t.id) + '" data-act="' + x[0] + '" data-st="' + (x[1] || '') + '">' + x[2] + '</button>';
    }).join('') + '</span>';
  }

  function renderTasks() {
    var d = DATA, wrap = $('board'); wrap.innerHTML = '';
    Object.keys(d.milestone_labels).forEach(function (mid) {
      var tasks = d.tasks.filter(function (t) { return t.milestone === mid && (filter === 'all' || t.status === filter); });
      if (!tasks.length) return;
      var sec = document.createElement('section'); sec.className = 'ms';
      sec.innerHTML = '<h3>' + esc(d.milestone_labels[mid]) + '</h3>';
      var ul = document.createElement('ul'); ul.className = 'tlist';
      tasks.forEach(function (t) {
        var li = document.createElement('li'); li.className = 'task st-' + t.status;
        li.innerHTML = '<span class="t-status">' + (STATUS_LABEL[t.status] || esc(t.status)) + '</span><span class="t-title">' + esc(t.title) + '</span>' +
          '<span class="t-owner">' + esc(t.owner || 'Open') + '</span>' +
          (t.due ? '<span class="t-due">Due ' + esc(dueLabel(t.due).text) + '</span>' : '') +
          (t.note ? '<span class="t-note">Blocked: ' + esc(t.note) + '</span>' : '') +
          (t.detail ? '<span class="t-detail">' + esc(t.detail) + '</span>' : '') + buttons(t);
        ul.appendChild(li);
      });
      sec.appendChild(ul); wrap.appendChild(sec);
    });
  }

  function show(d, isLive) {
    DATA = d; live = isLive;
    $('mode').textContent = isLive ? 'Live' : 'Static';
    $('mode').className = 'mode-badge' + (isLive ? ' live' : '');
    renderTasks(); renderDeadlines(d);
  }

  function getJSON(url, ms) {
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = ctl && setTimeout(function () { ctl.abort(); }, ms);
    return fetch(url, { cache: 'no-store', signal: ctl && ctl.signal }).then(function (r) {
      clearTimeout(timer); if (!r.ok) throw new Error(r.status); return r.json();
    });
  }

  function load() {
    var staticLoad = function () { return getJSON('data/tasks.json', 8000).then(function (d) { show(d, false); }); };
    if (!API) return staticLoad();
    return getJSON(API + '/api/tasks', 4000).then(function (d) { show(d, true); }, staticLoad);
  }

  /* ----- claim / status / release dialog ----- */
  var pending = null;
  function openDialog(id, act, st) {
    var t = DATA.tasks.filter(function (x) { return x.id === id; })[0]; if (!t) return;
    pending = { id: id, act: act, st: st };
    var verb = act === 'claim' ? 'Claim' : act === 'release' ? 'Release' : 'Mark ' + STATUS_LABEL[st].toLowerCase();
    $('dlg-title').textContent = verb + ': ' + t.title;
    var sel = $('dlg-name'); sel.innerHTML = '<option value="">Pick your name</option>' +
      (DATA.names || []).map(function (n) { return '<option>' + esc(n) + '</option>'; }).join('');
    sel.value = lastName || (act !== 'claim' && (DATA.names || []).indexOf(t.owner) >= 0 ? t.owner : '');
    $('dlg-pass').value = pass;
    $('dlg-note-wrap').hidden = st !== 'blocked'; $('dlg-note').value = ''; $('dlg-note').required = st === 'blocked';
    $('dlg-err').textContent = '';
    $('dlg').showModal();
    (sel.value ? (pass ? $('dlg-ok') : $('dlg-pass')) : sel).focus();
  }

  $('dlg-cancel').addEventListener('click', function () { $('dlg').close(); });
  $('dlg-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var name = $('dlg-name').value, pw = $('dlg-pass').value;
    if (!name) { $('dlg-err').textContent = 'Pick your name.'; return; }
    var body = { name: name, password: pw };
    if (pending.act === 'status') { body.status = pending.st; body.note = $('dlg-note').value; }
    $('dlg-ok').disabled = true; $('dlg-err').textContent = '';
    fetch(API + '/api/tasks/' + encodeURIComponent(pending.id) + '/' + pending.act, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      $('dlg-ok').disabled = false;
      if (!res.ok) { $('dlg-err').textContent = res.j.detail || 'That did not save. Try again.'; return; }
      pass = pw; lastName = name;
      $('dlg').close(); load();
    }, function () {
      $('dlg-ok').disabled = false; $('dlg-err').textContent = 'Could not reach the task server. Try again in a minute.';
    });
  });

  $('board').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-act]'); if (!b) return;
    openDialog(b.dataset.id, b.dataset.act, b.dataset.st);
  });

  function setFilter(f) {
    filter = f;
    document.querySelectorAll('.filters button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.f === f ? 'true' : 'false'); });
    if (DATA) renderTasks();
  }
  document.querySelectorAll('.filters button').forEach(function (b) { b.addEventListener('click', function () { setFilter(b.dataset.f); }); });

  getJSON('data/progress.json', 8000).then(renderProgress, function () {});
  load();
  if (API) setInterval(function () { if (!document.hidden && !$('dlg').open) load(); }, 30000);
})();
