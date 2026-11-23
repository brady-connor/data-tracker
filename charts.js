// Small SVG charts (no external libraries, so they work offline).
const PALETTE = ["#0f766e", "#b45309", "#1d4ed8", "#be123c", "#6d28d9", "#4d7c0f", "#0e7490", "#a16207", "#9d174d", "#475569"];

function niceStep(range, ticks) {
  const raw = range / ticks, p = Math.pow(10, Math.floor(Math.log10(raw)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= raw) return m * p;
  return 10 * p;
}
function axis(min, max, ticks = 4) {
  if (max === min) { max = min + 1; }
  const step = niceStep(max - min, ticks);
  const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
  const out = []; for (let v = lo; v <= hi + step / 2; v += step) out.push(+v.toFixed(6));
  return { lo, hi, ticks: out };
}

// Lines over the days. series = [{name, values (null = no value)}].
function lineChart(el, { labels, series, unit }) {
  const vals = series.flatMap(s => s.values).filter(v => v !== null);
  if (!labels.length || !vals.length) { el.innerHTML = '<p class="muted">Pick at least one item to see its line.</p>'; return; }
  const W = 720, H = 320, L = 52, R = 12, T = 12, B = 40, pw = W - L - R, ph = H - T - B;
  const a = axis(Math.min(...vals), Math.max(...vals));
  const n = labels.length, x = i => L + (n === 1 ? pw / 2 : pw * i / (n - 1)), y = v => T + ph - ph * (v - a.lo) / (a.hi - a.lo);
  let g = "";
  for (const t of a.ticks) g += `<line x1="${L}" x2="${W - R}" y1="${y(t)}" y2="${y(t)}" class="grid"/><text x="${L - 6}" y="${y(t) + 4}" class="ax" text-anchor="end">${t}</text>`;
  const step = Math.ceil(n / 10);
  labels.forEach((lb, i) => { if (i % step === 0) g += `<text x="${x(i)}" y="${H - B + 16}" class="ax" text-anchor="middle">${esc(lb.slice(5))}</text>`; });
  series.forEach((s, si) => {
    const color = PALETTE[si % PALETTE.length]; let d = "", pen = false;
    s.values.forEach((v, i) => { if (v === null) { pen = false; return; } d += (pen ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); pen = true; });
    g += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2"/>`;
    s.values.forEach((v, i) => { if (v !== null) g += `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${color}"><title>${esc(s.name)}, ${esc(labels[i])}: ${v}${unit ? " " + esc(unit) : ""}</title></circle>`; });
  });
  const legend = '<div class="legend">' + series.map((s, i) => `<span><i style="background:${PALETTE[i % PALETTE.length]}"></i>${esc(s.name)}</span>`).join("") + "</div>";
  el.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Line chart${unit ? " in " + esc(unit) : ""}">${g}</svg>${legend}`;
}

// Vertical bars. series = [{name, values}], dates: show MM-DD under the bars.
function barChart(el, { labels, series, dates }) {
  if (!labels.length) { el.innerHTML = '<p class="muted">No data yet.</p>'; return; }
  const W = 720, H = 300, L = 48, R = 10, T = 12, B = 40, pw = W - L - R, ph = H - T - B;
  const a = axis(0, Math.max(0.1, ...series.flatMap(s => s.values)));
  const n = labels.length, gw = pw / n, bw = Math.max(1, gw * 0.8 / series.length);
  let g = "";
  for (const t of a.ticks) { const yy = T + ph - ph * (t - a.lo) / (a.hi - a.lo); g += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" class="grid"/><text x="${L - 6}" y="${yy + 4}" class="ax" text-anchor="end">${t}</text>`; }
  series.forEach((s, si) => s.values.forEach((v, i) => {
    const h = ph * v / (a.hi - a.lo);
    g += `<rect x="${L + i * gw + gw * 0.1 + si * bw}" y="${T + ph - h}" width="${bw}" height="${h}" class="bar c${si + 1}"><title>${esc(labels[i])}: ${v}</title></rect>`;
  }));
  const step = Math.ceil(n / 12);
  labels.forEach((lb, i) => { if (i % step === 0) g += `<text x="${L + i * gw + gw / 2}" y="${H - B + 16}" class="ax" text-anchor="middle">${esc(dates ? String(lb).slice(5) : lb)}</text>`; });
  el.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart">${g}</svg>`;
}

// Horizontal bars for ranked lists; values may be negative.
function hBarChart(el, { labels, values, unit }) {
  if (!labels.length) { el.innerHTML = '<p class="muted">No data yet.</p>'; return; }
  const W = 720, rowH = 26, L = 170, R = 60, H = labels.length * rowH + 8, pw = W - L - R;
  const lo = Math.min(0, ...values), hi = Math.max(0, ...values), span = hi - lo || 1;
  const x0 = L + pw * (-lo) / span;
  let g = `<line x1="${x0}" x2="${x0}" y1="2" y2="${H - 2}" class="grid"/>`;
  labels.forEach((lb, i) => {
    const y = 4 + i * rowH, w = pw * Math.abs(values[i]) / span, x = values[i] >= 0 ? x0 : x0 - w;
    const text = lb.length > 26 ? lb.slice(0, 25) + "…" : lb;
    g += `<text x="${L - 8}" y="${y + 16}" class="lbl" text-anchor="end">${esc(text)}</text>` +
         `<rect x="${x}" y="${y + 3}" width="${w}" height="${rowH - 8}" class="bar ${values[i] < 0 ? "c2" : "c1"}"><title>${esc(lb)}: ${values[i]}${unit ? " " + esc(unit) : ""}</title></rect>` +
         `<text x="${values[i] >= 0 ? x0 + w + 6 : x0 + 6}" y="${y + 16}" class="ax">${values[i]}</text>`;
  });
  el.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart${unit ? " in " + esc(unit) : ""}">${g}</svg>`;
}
