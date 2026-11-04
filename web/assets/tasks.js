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

  /* ---------- weighted progress ----------
     Every task has a size (S/M/L -> size_points) and a phase: "poc" (cardboard proof of
     concept, semester 1) or "final" (semester 2). Bars count points, not tasks. */
  var PHASES = ['poc', 'final'];
  function phaseOf(t) { return t.phase === 'final' ? 'final' : 'poc'; }
  function phaseInfo(ph) {
    var p = (DATA.phases || {})[ph] || {};
    return { label: p.label || (ph === 'poc' ? 'Cardboard POC' : 'Final version'), when: p.when || (ph === 'poc' ? 'Semester 1' : 'Semester 2'), checkpoint: p.checkpoint };
  }
  function stats(list) {
    var by = function (st) { return list.filter(function (t) { return t.status === st; }); };
    var total = sum(list), done = sum(by('done')), run = sum(by('in_progress'));
    return { n: list.length, nDone: by('done').length, total: total, done: done, run: run,
             pct: total ? Math.round(done / total * 100) : 0 };
  }
  /* Two rows per bar: semester 1 (cardboard POC) and semester 2 (final). Each fills from the left,
     so finished final work never floats ahead of an empty POC. The POC row ends in the checkpoint
     flag with its date; it turns green when every POC task is done. */
  var FLAG = '<svg class="flag-ic" viewBox="0 0 12 14" aria-hidden="true"><path d="M2 1v12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M2.6 1.6h7.4l-2 2.6 2 2.6H2.6z" fill="currentColor"/></svg>';
  function shortDate(iso) {
    var m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], p = String(iso || '').split('-');
    return p.length === 3 ? m[+p[1] - 1] + ' ' + (+p[2]) : '';
  }
  function phaseBars(list, label) {
    var rows = PHASES.map(function (ph) {
      var inPh = list.filter(function (t) { return phaseOf(t) === ph; }), s = stats(inPh);
      if (!s.total) return '';
      var info = phaseInfo(ph), full = s.done === s.total;
      var dw = s.done / s.total * 100, rw = Math.min(100 - dw, s.run / s.total * 100);
      var end = ph === 'poc'
        ? '<span class="pend flag' + (full ? ' hit' : '') + '" title="Cardboard POC checkpoint">' + FLAG + (full ? 'POC done' : 'POC ' + esc(shortDate(info.checkpoint) || '')) + '</span>'
        : '<span class="pend fin' + (full ? ' hit' : '') + '">' + (full ? 'Done' : 'Final') + '</span>';
      return '<span class="prow ph-' + ph + '"><span class="plab">' + (ph === 'poc' ? 'Sem 1' : 'Sem 2') + '</span>' +
        '<span class="ptrack"><i class="b-done" style="width:' + dw.toFixed(1) + '%"></i><i class="b-run" style="width:' + rw.toFixed(1) + '%"></i></span>' +
        end + '<span class="ppct">' + s.pct + '%</span></span>';
    }).join('');
    var aria = label + ': ' + PHASES.map(function (ph) {
      var s = stats(list.filter(function (t) { return phaseOf(t) === ph; }));
      return s.total ? phaseInfo(ph).label + ' ' + s.pct + '% done' : '';
    }).filter(Boolean).join(', ');
    return '<span class="pbars" role="img" aria-label="' + esc(aria) + '">' + rows + '</span>';
  }

  function renderProgress(d) {
    var all = d.tasks, s = stats(all);
    $('pg-pct').textContent = s.pct + '%';
    $('pg-bar').innerHTML = phaseBars(all, 'Whole project');
    var poc = stats(all.filter(function (t) { return phaseOf(t) === 'poc'; }));
    var fin = stats(all.filter(function (t) { return phaseOf(t) === 'final'; }));
    var ck = phaseInfo('poc').checkpoint, ckText = '';
    if (ck) { var dl = dueLabel(ck); ckText = ' · checkpoint ' + dl.text; }
    $('pg-note').innerHTML = s.nDone + ' of ' + s.n + ' tasks done · ' + s.done + ' of ' + s.total + ' points. Counted from the task board, weighted by size.';
    var rows = [
      ['poc', poc, poc.done === poc.total ? 'Checkpoint reached. On to the final version.' :
        (poc.total - poc.done) + ' points left to the cardboard POC' + ckText + '.'],
      ['final', fin, fin.done === fin.total ? 'Final version done.' : (fin.total - fin.done) + ' points left. Mostly CAD, printing and assembly.']
    ];
    var list = $('pg-list'); list.innerHTML = '';
    rows.forEach(function (r) {
      var info = phaseInfo(r[0]), li = document.createElement('li'); li.className = 'pg-row ph-' + r[0];
      li.innerHTML = '<span class="pg-label">' + esc(info.when) + ' · ' + esc(info.label) + '</span><span class="pg-ev">' + esc(r[2]) + '</span>';
      list.appendChild(li);
    });
    // Encouragement: what got finished lately (live board only; the server stamps updated_at).
    var recent = all.filter(function (t) { return t.status === 'done' && t.updated_at && (Date.now() / 1000 - t.updated_at) < 14 * 86400; })
      .sort(function (a, b) { return b.updated_at - a.updated_at; }).slice(0, 4);
    var box = $('pg-recent');
    box.hidden = !recent.length;
    box.innerHTML = recent.length ? '<h3>Finished in the last two weeks</h3><ul>' + recent.map(function (t) {
      return '<li><span class="t-size sz-' + sizeOf(t) + '">' + sizeOf(t) + '</span>' + esc(t.title) + ' <span class="muted">· ' + esc(t.owner || 'Team') + ' · +' + points(t) + ' pt' + (points(t) > 1 ? 's' : '') + '</span></li>';
    }).join('') + '</ul>' : '';
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
    if (!live || !DATA.writes || t.status === 'done') return '';
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

  /* Groups: 3-5 collapsible buttons, each with its own progress bar. tasks.json "groups" lists
     which milestones each one holds; without it, every milestone is its own group. */
  var OPEN = {};
  try { OPEN = JSON.parse(localStorage.getItem('bricked-open-groups') || '{}') || {}; } catch (e) { OPEN = {}; }
  function saveOpen() { try { localStorage.setItem('bricked-open-groups', JSON.stringify(OPEN)); } catch (e) {} }

  function groupsOf(d) {
    var labels = d.milestone_labels || {}, seen = {}, out = [];
    (d.groups || []).forEach(function (g) {
      var ms = (g.milestones || []).filter(function (m) { return labels[m] && !seen[m]; });
      ms.forEach(function (m) { seen[m] = 1; });
      if (ms.length) out.push({ id: g.id, label: g.label, milestones: ms });
    });
    Object.keys(labels).forEach(function (m) { if (!seen[m]) out.push({ id: m, label: labels[m], milestones: [m] }); });
    return out;
  }

  /* Size: S, M or L. The group bars count work (points per size from tasks.json size_points),
     so one big task moves the bar more than a small one. Tasks without a size count as M. */
  var SIZE_WORD = { S: 'small', M: 'medium', L: 'large' };
  function sizeOf(t) { return SIZE_WORD[t.size] ? t.size : 'M'; }
  function points(t) {
    var p = (DATA.size_points || { S: 1, M: 2, L: 4 })[sizeOf(t)];
    return typeof p === 'number' && p > 0 ? p : 2;
  }
  function sum(list) { return list.reduce(function (a, t) { return a + points(t); }, 0); }

  function taskItem(t) {
    var li = document.createElement('li'); li.className = 'task st-' + t.status;
    var s = sizeOf(t);
    li.innerHTML = '<span class="t-status">' + (STATUS_LABEL[t.status] || esc(t.status)) + '</span>' +
      '<span class="t-title"><span class="t-size sz-' + s + '" title="Size: ' + SIZE_WORD[s] + ' (' + points(t) + ' pt)">' + s + '</span>' + esc(t.title) + '</span>' +
      '<span class="t-owner">' + esc(t.owner || 'Open') + '</span>' +
      (t.due && t.status !== 'done' ? '<span class="t-due">Due ' + esc(dueLabel(t.due).text) + '</span>' : '') +
      (t.note && t.status === 'blocked' ? '<span class="t-note">Blocked: ' + esc(t.note) + '</span>' : '') +
      (t.detail ? '<span class="t-detail">' + esc(t.detail) + '</span>' : '') + buttons(t);
    return li;
  }

  function renderTasks() {
    var d = DATA, wrap = $('board'); wrap.innerHTML = '';
    groupsOf(d).forEach(function (g) {
      var all = d.tasks.filter(function (t) { return g.milestones.indexOf(t.milestone) >= 0; });
      if (!all.length) return;
      var n = function (st) { return all.filter(function (t) { return t.status === st; }).length; };
      var s = stats(all), open = !!OPEN[g.id];
      var extra = [n('in_progress') && n('in_progress') + ' in progress', n('blocked') && n('blocked') + ' blocked'].filter(Boolean).join(' · ');
      var sec = document.createElement('section'); sec.className = 'grp' + (open ? ' open' : '');
      var pid = 'grp-' + esc(g.id);
      sec.innerHTML = '<button type="button" class="grp-btn" aria-expanded="' + open + '" aria-controls="' + pid + '" data-g="' + esc(g.id) + '">' +
        '<span class="grp-name">' + esc(g.label) + '</span><span class="grp-count">' + s.pct + '%</span><span class="grp-chev" aria-hidden="true"></span>' +
        phaseBars(all, g.label) +
        '<span class="grp-sub">' + s.nDone + ' of ' + s.n + ' tasks done' + (extra ? '<span class="sep"> · </span>' + extra : '') + '</span></button>';
      var panel = document.createElement('div'); panel.className = 'grp-panel'; panel.id = pid; panel.hidden = !open;
      PHASES.forEach(function (ph) {
        var inPh = all.filter(function (t) { return phaseOf(t) === ph; });
        var shown = inPh.filter(function (t) { return filter === 'all' || t.status === filter; });
        if (!shown.length) return;
        var info = phaseInfo(ph), ps = stats(inPh);
        var head = document.createElement('div'); head.className = 'ph-head ph-' + ph;
        head.innerHTML = '<h3>' + esc(info.label) + ' <span class="muted">· ' + esc(info.when) + '</span></h3><span class="ph-pct">' + ps.pct + '%</span>';
        panel.appendChild(head);
        var mids = g.milestones.filter(function (m) { return shown.some(function (t) { return t.milestone === m; }); });
        mids.forEach(function (mid) {
          var tasks = shown.filter(function (t) { return t.milestone === mid; });
          var ms = document.createElement('div'); ms.className = 'ms';
          if (mids.length > 1) ms.innerHTML = '<h4>' + esc(d.milestone_labels[mid]) + '</h4>';
          var ul = document.createElement('ul'); ul.className = 'tlist';
          tasks.forEach(function (t) { ul.appendChild(taskItem(t)); });
          ms.appendChild(ul); panel.appendChild(ms);
        });
      });
      if (!panel.children.length) panel.innerHTML = '<p class="muted small grp-empty">No ' + (filter === 'all' ? '' : STATUS_LABEL[filter].toLowerCase() + ' ') + 'tasks here.</p>';
      sec.appendChild(panel); wrap.appendChild(sec);
    });
  }

  function show(d, isLive) {
    DATA = d; live = isLive;
    $('mode').textContent = isLive ? 'Live' : 'Static';
    $('mode').className = 'mode-badge' + (isLive ? ' live' : '');
    renderProgress(d); renderTasks(); renderDeadlines(d);
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
    var g = e.target.closest('button[data-g]');
    if (g) {
      var open = g.getAttribute('aria-expanded') !== 'true';
      OPEN[g.dataset.g] = open; saveOpen();
      g.setAttribute('aria-expanded', String(open));
      g.parentNode.classList.toggle('open', open);
      $(g.getAttribute('aria-controls')).hidden = !open;
      return;
    }
    var b = e.target.closest('button[data-act]'); if (!b) return;
    openDialog(b.dataset.id, b.dataset.act, b.dataset.st);
  });

  function setFilter(f) {
    filter = f;
    document.querySelectorAll('.filters button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.f === f ? 'true' : 'false'); });
    if (DATA) renderTasks();
  }
  document.querySelectorAll('.filters button').forEach(function (b) { b.addEventListener('click', function () { setFilter(b.dataset.f); }); });

  load();
  if (API) setInterval(function () { if (!document.hidden && !$('dlg').open) load(); }, 30000);
})();
