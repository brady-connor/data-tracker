(async () => {
  renderNav();
  try {
    const { rows, status } = await loadData();
    const day = status.run_time.slice(0, 10);
    document.getElementById("runtime").textContent = status.run_time.replace("T", " ").replace("Z", " UTC");
    const counts = [["Days with a successful run", status.days_with_success], ["Items in the latest run", status.items],
                    ["Appeared", status.new_today], ["Disappeared", status.gone_today]];
    document.getElementById("counts").innerHTML = counts.map(([l, v]) => `<div class="count"><b>${v}</b>${l}</div>`).join("") +
      `<div class="count"><b>${esc(status.first_run_date)}</b>First run date</div>`;
    document.getElementById("sources").innerHTML = status.sources.map(s =>
      `<tr><td>${esc(s.name)}</td><td class="${s.ok ? "ok" : "fail"}">${s.ok ? "OK" : "Failed"}</td><td class="num">${s.count}</td></tr>`).join("");

    // biggest moves since the previous run (same rule as the daily issue)
    const change = compare(rows, day), top = change.moves.slice(0, 5);
    document.getElementById("moves").innerHTML = top.length
      ? top.map(m => `<li><b>${esc(m.item)}</b> ${m.change > 0 ? "+" : ""}${m.change} °C <span class="muted">(${m.old} → ${m.new} °C)</span></li>`).join("")
      : '<li class="muted">No moves yet. A move needs an earlier run to compare with.</li>';
    const names = rs => rs.map(r => esc(r.item)).join(", ");
    document.getElementById("changes").textContent =
      `Appeared: ${change.appeared.length ? names(change.appeared) : "none"}. Disappeared: ${change.gone.length ? names(change.gone) : "none"}.`;

    // latest values of every item with the change since its previous run
    const items = latestWithPrev(rows).sort((a, b) => byText(a.row.item, b.row.item));
    document.getElementById("headrow").innerHTML = "<th>Item</th><th>As of</th>" + NUM.map(([, l, u]) => `<th class="num">${l} (${u})</th>`).join("");
    document.getElementById("latest").innerHTML = items.map(({ row: r, prev: p }) =>
      `<tr><td>${esc(r.item)}<span class="delta">${esc(r.country)}</span></td><td>${r.date}</td>` +
      NUM.map(([k]) => {
        if (r[k] === null) return '<td class="num">–</td>';
        let d = "";
        if (p && p[k] !== null) { const c = round2(r[k] - p[k]); d = `<span class="delta ${c > 0 ? "up" : c < 0 ? "down" : ""}">${c > 0 ? "+" : ""}${c}</span>`; }
        return `<td class="num">${fmt(r[k], 1)}${d}</td>`;
      }).join("") + "</tr>").join("");
  } catch (e) { showError(e); }
})();
