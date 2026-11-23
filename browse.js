(async () => {
  renderNav();
  const KEY = "dt-shortlist";
  const getShort = () => { try { return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) { return new Set(); } };
  const saveShort = s => { try { localStorage.setItem(KEY, JSON.stringify([...s])); } catch (e) {} };
  const st = { region: "", country: "", q: "", short: false, key: "item", dir: 1 };
  let items = [];
  const $ = id => document.getElementById(id);

  function draw() {
    const shortlist = getShort(), q = st.q.toLowerCase();
    const list = items.filter(r => (!st.region || r.region === st.region) && (!st.country || r.country === st.country) &&
      (!q || r.item.toLowerCase().includes(q)) && (!st.short || shortlist.has(r.item_id)));
    list.sort((a, b) => {
      const x = a[st.key], y = b[st.key];
      if (x === null && y === null) return 0;
      if (x === null) return 1; if (y === null) return -1;     // empty values last
      return (typeof x === "string" ? byText(x, y) : x - y) * st.dir || byText(a.item_id, b.item_id);
    });
    $("count").textContent = `${list.length} of ${items.length} items`;
    $("shortcount").textContent = shortlist.size;
    const arrow = k => (st.key === k ? (st.dir === 1 ? " ▲" : " ▼") : "");
    $("headrow").innerHTML = '<th>Star</th><th><button class="sort" data-k="item">Item' + arrow("item") + "</button></th><th>Country</th><th>Region</th>" +
      NUM.map(([k, l, u]) => `<th class="num"><button class="sort" data-k="${k}">${l} (${u})${arrow(k)}</button></th>`).join("") + "<th>As of</th>";
    $("rows").innerHTML = list.map(r => `<tr>
      <td><button class="star${shortlist.has(r.item_id) ? " on" : ""}" data-id="${esc(r.item_id)}" aria-label="Save to shortlist" aria-pressed="${shortlist.has(r.item_id)}">${shortlist.has(r.item_id) ? "★" : "☆"}</button></td>
      <td>${esc(r.item)}</td><td>${esc(r.country)}</td><td>${esc(r.region)}</td>` +
      NUM.map(([k]) => `<td class="num">${fmt(r[k], 1)}</td>`).join("") + `<td>${r.date}</td></tr>`).join("");
  }

  try {
    const { rows } = await loadData();
    items = latestWithPrev(rows).map(x => x.row);
    const opts = (id, label, key) => { $(id).innerHTML = `<option value="">${label}</option>` + [...new Set(items.map(r => r[key]))].sort().map(v => `<option>${esc(v)}</option>`).join(""); };
    opts("region", "All regions", "region"); opts("country", "All countries", "country");
    $("region").addEventListener("change", e => { st.region = e.target.value; draw(); });
    $("country").addEventListener("change", e => { st.country = e.target.value; draw(); });
    $("q").addEventListener("input", e => { st.q = e.target.value; draw(); });
    $("short").addEventListener("change", e => { st.short = e.target.checked; draw(); });
    $("headrow").addEventListener("click", e => {
      const b = e.target.closest(".sort"); if (!b) return;
      if (st.key === b.dataset.k) st.dir = -st.dir; else { st.key = b.dataset.k; st.dir = b.dataset.k === "item" ? 1 : -1; }
      draw();
    });
    $("rows").addEventListener("click", e => {
      const b = e.target.closest(".star"); if (!b) return;
      const s = getShort(); s.has(b.dataset.id) ? s.delete(b.dataset.id) : s.add(b.dataset.id);
      saveShort(s); draw();
    });
    draw();
  } catch (e) { showError(e); }
})();
