// Shared helpers for all three pages.
const NAV = [["index.html", "Today"], ["browse.html", "Browse"], ["trends.html", "Trends"]];
// numeric columns of data/history.csv: [column, label, unit]
const NUM = [["temp_c", "Temperature", "°C"], ["feels_like_c", "Feels like", "°C"],
             ["humidity_pct", "Humidity", "%"], ["wind_kmh", "Wind", "km/h"],
             ["pressure_hpa", "Pressure", "hPa"]];

function renderNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.getElementById("nav").innerHTML =
    '<a class="brand" href="index.html">Data Tracker</a>' +
    NAV.map(([h, t]) => `<a href="${h}"${h === here ? ' class="active"' : ""}>${t}</a>`).join("");
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function parseCSV(text) {
  const rows = []; let row = [], f = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; }
      else f += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f !== "" || row.length) { row.push(f); rows.push(row); }
  const head = rows.shift() || [];
  return rows.filter(r => r.length === head.length).map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

function num(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}
const round2 = x => Math.round(x * 100) / 100;
function fmt(n, d = 1) { return n === null || n === undefined ? "–" : String(Math.round(n * 10 ** d) / 10 ** d); }
const byText = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function toRows(csvText) {
  return parseCSV(csvText).map(r => { for (const [k] of NUM) r[k] = num(r[k]); return r; });
}

async function loadData() {
  const get = u => fetch(u, { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(u + " returned " + r.status); return r; });
  const [csv, status] = await Promise.all([
    get("data/history.csv").then(r => r.text()),
    get("data/status.json").then(r => r.json()),
  ]);
  return { rows: toRows(csv), status };
}

// The move rule. Same rule as watcher/moves.py (see README):
// per source, compare the day with that source's previous run; a move is the
// change in temp_c, rounded to 2 decimals; ranked by size, then item_id.
function compare(rows, date) {
  const by = new Map();
  for (const r of rows) {
    if (!by.has(r.source)) by.set(r.source, new Map());
    const days = by.get(r.source);
    if (!days.has(r.date)) days.set(r.date, new Map());
    days.get(r.date).set(r.item_id, r);
  }
  const moves = [], appeared = [], gone = [];
  for (const source of [...by.keys()].sort()) {
    const days = by.get(source);
    if (!days.has(date)) continue;
    const earlier = [...days.keys()].filter(d => d < date).sort();
    if (!earlier.length) continue;
    const cur = days.get(date), prev = days.get(earlier[earlier.length - 1]);
    for (const id of [...cur.keys()].sort()) if (!prev.has(id)) appeared.push(cur.get(id));
    for (const id of [...prev.keys()].sort()) if (!cur.has(id)) gone.push(prev.get(id));
    for (const id of [...cur.keys()].sort()) {
      if (!prev.has(id)) continue;
      const n = cur.get(id).temp_c, o = prev.get(id).temp_c;
      if (n !== null && o !== null) moves.push({ item_id: id, item: cur.get(id).item, source, old: o, new: n, change: round2(n - o) });
    }
  }
  moves.sort((a, b) => Math.abs(b.change) - Math.abs(a.change) || byText(a.item_id, b.item_id));
  appeared.sort((a, b) => byText(a.item_id, b.item_id));
  gone.sort((a, b) => byText(a.item_id, b.item_id));
  return { moves, appeared, gone };
}

// One entry per item: its latest row and the row before it (or null).
function latestWithPrev(rows) {
  const m = new Map();
  for (const r of rows) { if (!m.has(r.item_id)) m.set(r.item_id, []); m.get(r.item_id).push(r); }
  return [...m.values()].map(a => {
    a.sort((x, y) => byText(x.date, y.date));
    return { row: a[a.length - 1], prev: a.length > 1 ? a[a.length - 2] : null };
  });
}

function showError(e) {
  const el = document.getElementById("msg");
  el.hidden = false;
  el.textContent = "Could not load the data files (" + e.message + "). Open the site once while online.";
}

if (typeof navigator !== "undefined" && "serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
if (typeof module !== "undefined") module.exports = { parseCSV, toRows, compare, latestWithPrev, round2, NUM, byText };
