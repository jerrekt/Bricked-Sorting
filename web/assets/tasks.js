/* Static task board. Reads data/tasks.json and data/progress.json, no backend. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var STATUS_LABEL = { todo: 'To do', in_progress: 'In progress', blocked: 'Blocked', done: 'Done' };
  var filter = 'all';

  function dueLabel(due) {
    var days = Math.round((new Date(due + 'T00:00:00') - new Date(new Date().toDateString())) / 86400000);
    var when = days < 0 ? 'past due' : days === 0 ? 'today' : days === 1 ? 'tomorrow' : 'in ' + days + ' days';
    return { text: due + ' · ' + when, soon: days <= 7, past: days < 0 };
  }

  function renderDeadlines(d) {
    var box = $('deadlines'); if (!box) return;
    var items = d.tasks.filter(function (t) { return t.due && t.status !== 'done'; })
      .sort(function (a, b) { return a.due < b.due ? -1 : 1; });
    box.hidden = !items.length;
    var ul = $('dl-list'); if (!ul) return; ul.innerHTML = '';
    items.forEach(function (t) {
      var dl = dueLabel(t.due);
      var li = document.createElement('li'); li.className = 'dl-row' + (dl.past ? ' past' : dl.soon ? ' soon' : '');
      li.innerHTML = '<span class="dl-date">' + esc(dl.text) + '</span><span class="dl-title">' + esc(t.title) + '</span><span class="t-owner">' + esc(t.owner || '') + '</span>';
      ul.appendChild(li);
    });
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

  function renderTasks(d) {
    var wrap = $('board'); wrap.innerHTML = '';
    Object.keys(d.milestone_labels).forEach(function (mid) {
      var tasks = d.tasks.filter(function (t) { return t.milestone === mid && (filter === 'all' || t.status === filter); });
      if (!tasks.length) return;
      var sec = document.createElement('section'); sec.className = 'ms';
      sec.innerHTML = '<h3>' + esc(d.milestone_labels[mid]) + '</h3>';
      var ul = document.createElement('ul'); ul.className = 'tlist';
      tasks.forEach(function (t) {
        var li = document.createElement('li'); li.className = 'task st-' + t.status;
        li.innerHTML = '<span class="t-status">' + STATUS_LABEL[t.status] + '</span><span class="t-title">' + esc(t.title) + '</span>' +
          (t.owner ? '<span class="t-owner">' + esc(t.owner) + '</span>' : '') +
          (t.due ? '<span class="t-due">Due ' + esc(dueLabel(t.due).text) + '</span>' : '') +
          (t.detail ? '<span class="t-detail">' + esc(t.detail) + '</span>' : '');
        ul.appendChild(li);
      });
      sec.appendChild(ul); wrap.appendChild(sec);
    });
  }

  var TASKS;
  function setFilter(f) {
    filter = f;
    document.querySelectorAll('.filters button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.f === f ? 'true' : 'false'); });
    renderTasks(TASKS);
  }

  document.querySelectorAll('.filters button').forEach(function (b) { b.addEventListener('click', function () { setFilter(b.dataset.f); }); });

  fetch('data/progress.json').then(function (r) { return r.json(); }).then(renderProgress);
  fetch('data/tasks.json').then(function (r) { return r.json(); }).then(function (d) { TASKS = d; renderTasks(d); renderDeadlines(d); });
})();
