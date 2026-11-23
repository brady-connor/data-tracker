// Trends: every number is computed here from data/history.csv.
function trendsCompute(rows) {
  const out = { empty: rows.length === 0 };
  if (out.empty) return out;
  const dates = [...new Set(rows.map(r => r.date))].sort();
  out.dates = dates; out.first = dates[0]; out.last = dates[dates.length - 1];
  const byItem = new Map();
  for (const r of rows) { if (!byItem.has(r.item_id)) byItem.set(r.item_id, []); byItem.get(r.item_id).push(r); }
  for (const a of byItem.values()) a.sort((x, y) => byText(x.date, y.date));
  out.byItem = byItem;

  // 1. change in temp_c from each item's first row to its latest row
  out.sinceFirst = [];
  for (const [id, a] of byItem) {
    const f = a[0], l = a[a.length - 1];
    if (a.length >= 2 && f.temp_c !== null && l.temp_c !== null)
      out.sinceFirst.push({ item_id: id, item: f.item, from: f.date, to: l.date, first: f.temp_c, last: l.temp_c, change: round2(l.temp_c - f.temp_c) });
  }
  out.sinceFirst.sort((a, b) => b.change - a.change || byText(a.item_id, b.item_id));

  // 2. for each day, the biggest single move (move rule), and the biggest overall
  out.dayMoves = dates.map(d => { const m = compare(rows, d).moves; return { date: d, move: m.length ? m[0] : null }; });
  out.bestDay = null;
  for (const dm of out.dayMoves) if (dm.move && (!out.bestDay || Math.abs(dm.move.change) > Math.abs(out.bestDay.move.change))) out.bestDay = dm;

  // 3. spread of temp_c across the items on the last date
  out.latestTemps = rows.filter(r => r.date === out.last && r.temp_c !== null)
    .map(r => ({ item_id: r.item_id, item: r.item, temp: r.temp_c })).sort((a, b) => b.temp - a.temp || byText(a.item_id, b.item_id));
  out.range = out.latestTemps.length ? round2(out.latestTemps[0].temp - out.latestTemps[out.latestTemps.length - 1].temp) : null;

  // 4. average absolute day-to-day change in temp_c per item
  out.volatility = [];
  for (const [id, a] of byItem) {
    const diffs = [];
    for (let i = 1; i < a.length; i++) if (a[i].temp_c !== null && a[i - 1].temp_c !== null) diffs.push(Math.abs(a[i].temp_c - a[i - 1].temp_c));
    if (diffs.length) out.volatility.push({ item_id: id, item: a[0].item, avg: round2(diffs.reduce((x, y) => x + y, 0) / diffs.length), n: diffs.length });
  }
  out.volatility.sort((a, b) => b.avg - a.avg || byText(a.item_id, b.item_id));

  // 5. average wind_kmh per item over all its rows
  out.wind = [];
  for (const [id, a] of byItem) {
    const v = a.map(r => r.wind_kmh).filter(x => x !== null);
    if (v.length) out.wind.push({ item_id: id, item: a[0].item, avg: round2(v.reduce((x, y) => x + y, 0) / v.length), n: v.length });
  }
  out.wind.sort((a, b) => b.avg - a.avg || byText(a.item_id, b.item_id));
  return out;
}

function renderSections(m) {
  const html = [];
  const add = (title, text, id) => html.push(`<section class="report"><h2>${title}</h2><p>${text}</p><div id="${id}"></div></section>`);
  const sg = n => (n > 0 ? "+" : "") + n;
  const sf = m.sinceFirst, nd = m.dates.length;

  if (sf.length) {
    const up = sf[0], down = sf[sf.length - 1];
    add(`${esc(up.item)} warmed the most since the first run (${sg(up.change)} °C)`,
      `Across ${sf.length} items, ${esc(up.item)} rose ${sg(up.change)} °C (${up.first} to ${up.last} °C, ${up.from} to ${up.to}). ${esc(down.item)} ${down.change < 0 ? "fell the most" : "rose the least"} at ${sg(down.change)} °C (${down.first} to ${down.last} °C). ` +
      `Computed from history.csv: for each item, the temp_c of its latest row minus the temp_c of its first row, rounded to 2 decimals.`, "t1");
  } else add("Not enough data yet to compare with the first run", "This needs an item with at least two days of temperature values. It fills in as the history grows.", "t1");

  if (m.bestDay) {
    const b = m.bestDay.move;
    add(`The biggest single move was ${sg(b.change)} °C, ${esc(b.item)} on ${m.bestDay.date}`,
      `On ${m.bestDay.date}, ${esc(b.item)} went from ${b.old} to ${b.new} °C since its source's previous run, the largest absolute move on any of the ${nd} days. ` +
      `Computed from history.csv: for each day, every item's temp_c minus its temp_c in the same source's previous run (the move rule in the README); the chart shows the largest absolute move of each day.`, "t2");
  } else add("Not enough data yet for the biggest move", "A move needs two runs of the same source. It fills in after the second day.", "t2");

  if (m.range !== null) {
    const hot = m.latestTemps[0], cold = m.latestTemps[m.latestTemps.length - 1];
    add(`Temperatures span ${m.range} °C across ${m.latestTemps.length} items on ${m.last}`,
      `The warmest item is ${esc(hot.item)} at ${hot.temp} °C and the coolest is ${esc(cold.item)} at ${cold.temp} °C, a gap of ${m.range} °C. ` +
      `Computed from history.csv: the temp_c of every row dated ${m.last} (the last date), with the gap being the maximum minus the minimum.`, "t3");
  } else add("No temperatures on the last date", "Nothing to compare yet.", "t3");

  if (m.volatility.length) {
    const v = m.volatility[0];
    add(`${esc(v.item)} swings the most from run to run (${v.avg} °C on average)`,
      `${esc(v.item)} changed by ${v.avg} °C on average between consecutive runs (${v.n} comparison${v.n === 1 ? "" : "s"}). The steadiest item is ${esc(m.volatility[m.volatility.length - 1].item)} at ${m.volatility[m.volatility.length - 1].avg} °C. ` +
      `Computed from history.csv: for each item, the absolute difference in temp_c between each row and the one before it, averaged.`, "t4");
  } else add("Not enough data yet for run-to-run swings", "This needs at least two days of values.", "t4");

  if (m.wind.length) {
    const w = m.wind[0];
    add(`${esc(w.item)} is the windiest item (${w.avg} km/h on average)`,
      `${esc(w.item)} averages ${w.avg} km/h over ${w.n} row${w.n === 1 ? "" : "s"}; the calmest is ${esc(m.wind[m.wind.length - 1].item)} at ${m.wind[m.wind.length - 1].avg} km/h. ` +
      `Computed from history.csv: for each item, the mean of wind_kmh over all of its rows, skipping empty values.`, "t5");
  } else add("No wind values yet", "Nothing to average yet.", "t5");
  document.getElementById("sections").innerHTML = html.join("");

  const $ = id => document.getElementById(id);
  hBarChart($("t1"), { labels: sf.map(x => x.item), values: sf.map(x => x.change), unit: "°C" });
  barChart($("t2"), { labels: m.dayMoves.map(d => d.date), dates: true, series: [{ name: "Biggest move", values: m.dayMoves.map(d => d.move ? Math.abs(d.move.change) : 0) }] });
  hBarChart($("t3"), { labels: m.latestTemps.map(x => x.item), values: m.latestTemps.map(x => x.temp), unit: "°C" });
  hBarChart($("t4"), { labels: m.volatility.slice(0, 10).map(x => x.item), values: m.volatility.slice(0, 10).map(x => x.avg), unit: "°C" });
  hBarChart($("t5"), { labels: m.wind.slice(0, 10).map(x => x.item), values: m.wind.slice(0, 10).map(x => x.avg), unit: "km/h" });
}

function setupExplorer(m) {
  const ids = [...m.byItem.keys()].sort((a, b) => byText(m.byItem.get(a)[0].item, m.byItem.get(b)[0].item));
  const chosen = new Set(ids.slice(0, 5));
  const sel = document.getElementById("value");
  sel.innerHTML = NUM.map(([k, l, u]) => `<option value="${k}">${l} (${u})</option>`).join("");
  document.getElementById("itemlist").innerHTML = ids.map(id =>
    `<label><input type="checkbox" value="${esc(id)}"${chosen.has(id) ? " checked" : ""}> ${esc(m.byItem.get(id)[0].item)}</label>`).join("");
  const boxes = () => [...document.querySelectorAll("#itemlist input")];
  function draw() {
    const [k, , unit] = NUM.find(n => n[0] === sel.value);
    const picked = boxes().filter(b => b.checked).map(b => b.value);
    const series = picked.map(id => {
      const a = m.byItem.get(id), byDate = new Map(a.map(r => [r.date, r[k]]));
      return { name: a[0].item, values: m.dates.map(d => (byDate.has(d) ? byDate.get(d) : null)) };
    });
    lineChart(document.getElementById("lines"), { labels: m.dates, series, unit });
  }
  sel.addEventListener("change", draw);
  document.getElementById("itemlist").addEventListener("change", draw);
  document.getElementById("all").addEventListener("click", () => { boxes().forEach(b => b.checked = true); draw(); });
  document.getElementById("none").addEventListener("click", () => { boxes().forEach(b => b.checked = false); draw(); });
  draw();
}

if (typeof document !== "undefined") {
  (async () => {
    renderNav();
    try {
      const { rows } = await loadData();
      const m = trendsCompute(rows);
      if (m.empty) { document.getElementById("sections").innerHTML = '<p class="muted">The history file has no rows yet.</p>'; return; }
      setupExplorer(m); renderSections(m);
    } catch (e) { showError(e); }
  })();
}
if (typeof module !== "undefined") module.exports = { trendsCompute };
