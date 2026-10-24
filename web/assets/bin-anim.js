/* Bin-fill animation for the landing page.
   Based on the 2026-10-24 handoff, reordered to the machine: floor 2 (other pieces) on top,
   floor 1 (bricks) below, slots 1-8 left to right, slot 8 = unknown color.
   Pieces and colors come from the real 10696 parts list (data/set-10696.json).
   Set window.FREEZE = true before load to render a single frame via render(t). */
(function () {
  'use strict';
  var cv = document.getElementById('binAnim'); if (!cv) return;
  var x = cv.getContext('2d');
  var HT = { brick: 15, plate: 8, tile: 8, slope: 15, round: 15, technic: 13, wheel: 24, arch: 15 };
  var HW = { brick: 25, plate: 25, tile: 25, slope: 18, round: 10, technic: 27, wheel: 12, arch: 18 };
  var BW = 72, GAP = 8, X0 = 14, CAPH = 112, PITCH = 185, FULLH = 92;
  var SL = 180, DR = 260, STT = 450, T = 420, HOLD = 2200, N = 64;
  function rail(r) { return 34 + r * PITCH + (r >= 2 ? 24 : 0); }
  function floorY(r) { return rail(r) + 150; }
  function binX(b) { return X0 + (b % 4) * (BW + GAP); }
  function binRow(b) { return Math.floor(b / 4); }
  function kindOf(part) {
    if (/^Brick \d+ x \d+/.test(part)) return 'brick';
    if (/Tire|Wheel/.test(part)) return 'wheel';
    if (/Plate, Round|Brick, Round|Cone/.test(part)) return 'round';
    if (/^Plate/.test(part)) return 'plate';
    if (/^Tile/.test(part)) return 'tile';
    if (/Slope/.test(part)) return 'slope';
    if (/Window|Arch|Shutter/.test(part)) return 'arch';
    return 'technic';
  }
  var s = 17; function rnd() { s = (s * 9301 + 49297) % 233280; return s / 233280; }
  var seq = [], binFull = [], swatch = [], STROKE = 'rgba(0,0,0,0.5)';

  function build(bins, set) {
    var slotOf = {}; bins.slots.forEach(function (sl) { slotOf[sl.key] = sl.slot; swatch[sl.slot - 1] = sl.swatch; });
    var pool = []; set.parts.forEach(function (p) { for (var i = 0; i < p.qty; i++) pool.push(p); });
    var hm = []; for (var i = 0; i < 16; i++) { var a = []; for (var j = 0; j < BW; j++) a.push(0); hm.push(a); }
    var lastIn = []; for (i = 0; i < 16; i++) lastIn.push([]);
    function support(a, xc, hw) { var m = 0, lo = Math.max(0, Math.floor(xc - hw)), hi = Math.min(BW - 1, Math.ceil(xc + hw)); for (var i = lo; i <= hi; i++) if (a[i] > m) m = a[i]; return m; }
    var tries = 0;
    while (seq.length < N && tries < 4000) {
      tries++;
      var pc = pool[Math.floor(rnd() * pool.length)], kind = kindOf(pc.part);
      var slot = slotOf[bins.colorMap[pc.color] || 'unknown'] || 8;
      var bin = (pc.brick ? 8 : 0) + slot - 1, a2 = hm[bin], hw = HW[kind], h = HT[kind] + 1;
      var lo = hw + 3, hi = BW - hw - 3, x1 = lo + rnd() * (hi - lo), s1 = support(a2, x1, hw);
      var best = 1e9, c = [];
      for (var xc = Math.ceil(lo); xc <= hi; xc += 2) { var sv = support(a2, xc, hw); c.push([xc, sv]); if (sv < best) best = sv; }
      var near = c.filter(function (q) { return q[1] <= best + 3; }), pk = near[Math.floor(rnd() * near.length)];
      var x2 = pk[0], s2 = pk[1];
      if (s2 + h > CAPH) continue;
      if (s1 + h > CAPH + 20) s1 = s2;
      var i0 = seq.length;
      var p = { kind: kind, hex: pc.hex, bin: bin, x1: x1, s1: Math.max(s1, s2), x2: x2, s2: s2, h: h, rot1: (rnd() - 0.5) * 0.5, rotF: (rnd() - 0.5) * 0.14, st: i0 * T, jolts: [] };
      p.tl = p.st + SL + DR;
      lastIn[bin].slice(-3).forEach(function (k) { seq[k].jolts.push({ t: p.tl, a: (rnd() - 0.5) * 6 }); });
      for (i = Math.max(0, Math.floor(x2 - hw)); i <= Math.min(BW - 1, Math.ceil(x2 + hw)); i++) a2[i] = s2 + h;
      if (s2 + h >= FULLH && binFull[bin] == null) binFull[bin] = p.tl + STT;
      lastIn[bin].push(i0); seq.push(p);
    }
  }

  function stud(cx, top, hex) { x.fillStyle = hex; x.fillRect(cx - 5, top - 4, 10, 4); x.strokeRect(cx - 4.5, top - 4.5, 9, 4); }
  function shade(w, h) { x.fillStyle = 'rgba(255,255,255,0.28)'; x.fillRect(-w / 2 + 3, -h / 2 + 2, w - 6, 2); x.fillStyle = 'rgba(0,0,0,0.12)'; x.fillRect(-w / 2 + 1, h / 2 - 3, w - 2, 2); }
  function piece(kind, hex) {
    var h = HT[kind]; x.fillStyle = hex; x.strokeStyle = STROKE; x.lineWidth = 1;
    if (kind === 'brick' || kind === 'plate' || kind === 'tile' || kind === 'technic') {
      var w = kind === 'technic' ? 54 : 50;
      if (kind === 'brick' || kind === 'plate') { stud(-12, -h / 2, hex); stud(12, -h / 2, hex); }
      x.fillStyle = hex; x.fillRect(-w / 2, -h / 2, w, h); x.strokeRect(-w / 2 + 0.5, -h / 2 + 0.5, w - 1, h - 1);
      if (kind === 'technic') { x.fillStyle = 'rgba(0,0,0,0.55)'; [-17, 0, 17].forEach(function (px) { x.beginPath(); x.arc(px, 0, 3.5, 0, 7); x.fill(); }); }
      else shade(w, h);
    } else if (kind === 'slope') { stud(10, -h / 2, hex); x.fillStyle = hex; x.beginPath(); x.moveTo(-18, h / 2); x.lineTo(18, h / 2); x.lineTo(18, -h / 2); x.lineTo(2, -h / 2); x.closePath(); x.fill(); x.stroke(); }
    else if (kind === 'round') { stud(0, -h / 2, hex); x.fillStyle = hex; x.fillRect(-9, -h / 2, 18, h); x.strokeRect(-8.5, -h / 2 + 0.5, 17, h - 1); x.fillStyle = 'rgba(255,255,255,0.3)'; x.fillRect(-6, -h / 2 + 2, 3, h - 4); }
    else if (kind === 'wheel') { x.fillStyle = '#2b2b2b'; x.beginPath(); x.arc(0, 0, 12, 0, 7); x.fill(); x.stroke(); x.fillStyle = hex; x.beginPath(); x.arc(0, 0, 6, 0, 7); x.fill(); x.stroke(); }
    else if (kind === 'arch') { stud(-9, -h / 2, hex); stud(9, -h / 2, hex); x.fillStyle = hex; x.beginPath(); x.rect(-18, -h / 2, 36, h); x.moveTo(8, h / 2); x.arc(0, h / 2, 8, 0, Math.PI, true); x.closePath(); x.fill('evenodd'); x.stroke(); }
  }
  function place(cx, cy, rot, q) { x.save(); x.translate(cx, cy); x.rotate(rot); piece(q.kind, q.hex); x.restore(); }
  function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || '#888780'; }

  function render(t) {
    var line = css('--muted'), warn = css('--warn');
    x.clearRect(0, 0, 340, 804);
    x.fillStyle = line; x.font = '600 12px system-ui,sans-serif'; x.textAlign = 'left';
    x.fillText('Floor 2 · other pieces', 14, rail(0) - 20); x.fillText('Floor 1 · bricks', 14, rail(2) - 20);
    for (var r = 0; r < 4; r++) {
      var ry = rail(r), fl = floorY(r);
      x.strokeStyle = line; x.lineWidth = 1; x.setLineDash([4, 4]); x.beginPath(); x.moveTo(10, ry + 16); x.lineTo(330, ry + 16); x.stroke(); x.setLineDash([]);
      for (var c = 0; c < 4; c++) {
        var i = r * 4 + c, bx = X0 + c * (BW + GAP), k = i % 8;
        var full = binFull[i] != null && t >= binFull[i];
        x.strokeStyle = full ? warn : line; x.lineWidth = 3;
        x.beginPath(); x.moveTo(bx + 6, fl - 125); x.lineTo(bx, fl - 119); x.lineTo(bx, fl - 3); x.quadraticCurveTo(bx, fl + 3, bx + 6, fl + 3);
        x.lineTo(bx + BW - 6, fl + 3); x.quadraticCurveTo(bx + BW, fl + 3, bx + BW, fl - 3); x.lineTo(bx + BW, fl - 119); x.lineTo(bx + BW - 6, fl - 125); x.stroke();
        if (full) {
          var pu = 1 + 0.12 * Math.sin((t - binFull[i]) / 160), pr = Math.min(1, (t - binFull[i]) / 150);
          x.save(); x.translate(bx + BW / 2, fl - 123); x.scale(pu * pr, pu * pr);
          x.fillStyle = warn; x.beginPath(); x.arc(0, 0, 10, 0, 7); x.fill();
          x.fillStyle = '#fff'; x.font = '700 15px system-ui,sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('!', 0, 1); x.restore(); x.textBaseline = 'alphabetic';
        }
        var codeTxt = (r < 2 ? '2-' : '1-') + (k + 1);
        x.fillStyle = line; x.font = '600 11px system-ui,sans-serif'; x.textAlign = 'left'; x.fillText(codeTxt, bx + 2, fl + 22);
        if (k === 7) { x.font = '600 15px system-ui,sans-serif'; x.textAlign = 'center'; x.fillText('?', bx + BW - 12, fl + 23); }
        else { x.fillStyle = swatch[k]; x.beginPath(); x.arc(bx + BW - 12, fl + 18, 6, 0, 7); x.fill(); x.strokeStyle = line; x.lineWidth = 1; x.stroke(); }
      }
    }
    for (var n = 0; n < seq.length; n++) {
      var q = seq[n]; if (t < q.st) break;
      var row = binRow(q.bin), bx2 = binX(q.bin), fl2 = floorY(row), y0 = rail(row), u = t - q.st;
      var yA = fl2 - q.s1 - q.h / 2 - 1, yB = fl2 - q.s2 - q.h / 2 - 1, cx, cy, rot, pp;
      if (u < SL) { pp = u / SL; cx = 170 + (bx2 + q.x1 - 170) * pp; cy = y0; rot = 0; }
      else if (u < SL + DR) { pp = (u - SL) / DR; cx = bx2 + q.x1; cy = y0 + (yA - y0) * pp * pp; rot = q.rot1 * pp; }
      else if (u < SL + DR + STT) { pp = (u - SL - DR) / STT; var e = 1 - Math.pow(1 - pp, 3); cx = bx2 + q.x1 + (q.x2 - q.x1) * e; cy = yA + (yB - yA) * e; rot = q.rot1 + (q.rotF - q.rot1) * e; }
      else { cx = bx2 + q.x2; cy = yB; rot = q.rotF; }
      if (u >= SL + DR) q.jolts.forEach(function (j) { var d = t - j.t; if (d > 0) { var o = j.a * Math.exp(-d / 260) * Math.sin(d / 38); cx += o; rot += o * 0.012; } });
      place(cx, cy, rot, q);
    }
  }
  window.render = render;

  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  Promise.all([fetch('data/bins.json').then(function (r) { return r.json(); }), fetch('data/set-10696.json').then(function (r) { return r.json(); })]).then(function (a) {
    build(a[0], a[1]);
    var TOTAL = seq.length * T + HOLD, t0 = null;
    function loop(now) { if (!t0) t0 = now; var t = now - t0; render(t); if (t > TOTAL) t0 = now; if (!window.FREEZE) requestAnimationFrame(loop); }
    var rb = document.getElementById('replay'); if (rb) rb.onclick = function () { t0 = null; if (reduce) render(TOTAL); };
    if (window.FREEZE) render(0); else if (reduce) render(TOTAL); else requestAnimationFrame(loop);
  });
})();
