/* Live status page. Reads data/live.json every 5 s. Shows an empty state when nothing is connected. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var BINS = null, last = null;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function fmtAge(sec) { return sec < 90 ? Math.round(sec) + ' s ago' : Math.round(sec / 60) + ' min ago'; }

  function renderBins(counts) {
    ['2', '1'].forEach(function (f) {
      var el = $('floor' + f); el.innerHTML = '';
      BINS.slots.forEach(function (s) {
        var c = f + '-' + s.slot, n = (counts && counts[c]) || 0;
        var d = document.createElement('div'); d.className = 'bin';
        d.innerHTML = '<div class="bin-code">' + c + '</div><div class="bin-label">' + esc(s.label) + '</div><div class="bin-count">' + n + '</div>';
        el.appendChild(d);
      });
    });
  }

  function render(d) {
    var live = d && d.updated;
    var age = live ? (Date.now() - Date.parse(d.updated)) / 1000 : null;
    var stale = live && age > 30;
    $('state').textContent = !live ? 'Not connected' : stale ? 'No recent data' : 'Live';
    $('state').className = 'badge ' + (!live ? 'off' : stale ? 'warn' : 'on');
    $('age').textContent = live ? 'Updated ' + fmtAge(age) : '';
    $('empty').hidden = !!live;
    $('stages').hidden = !live;
    if (live) {
      var st = d.stages || {};
      ['isolate', 'identify', 'indicate'].forEach(function (k) {
        var v = st[k] || {};
        $('st-' + k).textContent = v.status || 'unknown';
        $('st-' + k).className = 'st-val ' + (v.status === 'ok' ? 'ok' : v.status === 'error' ? 'bad' : '');
        $('st-' + k + '-note').textContent = v.note || '';
      });
      var p = d.lastPiece;
      $('last').textContent = p ? (p.code + ' · ' + (p.name || 'piece') + (p.confidence != null ? ' · ' + Math.round(p.confidence * 100) + '%' : '')) : 'None yet';
    }
    renderBins(d && d.counts);
  }

  function poll() {
    fetch('data/live.json?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(render, function () { render(null); });
  }

  fetch('data/bins.json').then(function (r) { return r.json(); }).then(function (b) {
    BINS = b; render(null); poll(); setInterval(poll, 5000);
  });
})();
