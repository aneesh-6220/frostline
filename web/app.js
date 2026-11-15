/* Frostline client. All numbers come from the /api endpoints (approved engine); nothing is computed here except display formatting. */
(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const W = (y) => `${y}/${String(y + 1).slice(-2)}`;
  const C = { navy: "#0B1220", blue: "#2563EB", slate: "#334155", border: "#E2E8F0", amber: "#D97706", muted: "#64748B", teal: "#0F766E" };
  const S = { meta: null, location: null, variable: null, first: null, last: null, inv: null, cmp: { a: "dettah_bay", b: "aklavik_delta", v: "fdd_octdec", first: null, last: null }, road: "dettah_bay" };
  const charts = {};
  let map = null, markers = {};

  async function api(path) {
    const r = await fetch(path);
    let body; try { body = await r.json(); } catch { body = { error: `Unexpected response (${r.status}).` }; }
    if (!r.ok) throw new Error(body.error || `Request failed (${r.status}).`);
    return body;
  }
  function showError(msg) { const e = $("error"); if (!msg) { e.hidden = true; return; } e.textContent = msg; e.hidden = false; }
  function chart(id) {
    if (!charts[id]) { charts[id] = echarts.init($(id), null, { renderer: "svg" }); }
    return charts[id];
  }
  window.addEventListener("resize", () => Object.values(charts).forEach((c) => c.resize()));

  const fmtN = (v, d = 1) => (v === null || v === undefined ? "n/a" : Number(v).toFixed(d));
  const locName = (id) => (S.meta.locations.find((l) => l.id === id) || {}).name || id;
  const locShort = (id) => (S.meta.locations.find((l) => l.id === id) || {}).short || id;
  const varObj = (id) => S.meta.variables.find((v) => v.id === id);
  const avail = (vid, lid) => (varObj(vid).availability || []).find((a) => a.location_id === lid);
  function fillSelect(sel, items, value) {
    sel.innerHTML = items.map((i) => `<option value="${esc(i.value)}"${i.disabled ? " disabled" : ""}>${esc(i.label)}</option>`).join("");
    if (value !== undefined && value !== null) sel.value = String(value);
  }
  function years(lo, hi) { const a = []; for (let y = lo; y <= hi; y++) a.push({ value: y, label: W(y) }); return a; }

  // ------------------------------------------------------------- hash state
  function readHash() {
    const [view, q] = location.hash.replace(/^#/, "").split("?");
    const p = new URLSearchParams(q || "");
    return { view: view || "overview", p };
  }
  function writeHash(view) {
    const p = new URLSearchParams({ l: S.location, v: S.variable, f: S.first, t: S.last });
    history.replaceState(null, "", `#${view}?${p}`);
  }
  function currentView() { return readHash().view; }

  // ------------------------------------------------------------- context bar
  function renderCtx() {
    const v = varObj(S.variable);
    $("ctx").innerHTML = `<span><span class="k">Location</span> <b>${esc(locName(S.location))}</b></span><span><span class="k">Variable</span> <b>${esc(v.label)}</b> <span class="k">(${esc(v.unit)})</span></span><span><span class="k">Period</span> <b>${W(S.first)} to ${W(S.last)}</b></span>`;
  }

  // ------------------------------------------------------------- explore
  function populateExplore() {
    const locs = S.meta.locations.map((l) => ({ value: l.id, label: l.role === "supplementary" ? `${l.name} (exploratory, approximate location)` : `${l.name}${l.role === "comparison" ? " (comparison, different setting)" : ""}` }));
    fillSelect($("sel-location"), locs, S.location);
    const vars = S.meta.variables.filter((v) => avail(v.id, S.location)).map((v) => ({ value: v.id, label: `${v.kind === "road" ? "Road: " : ""}${v.label}${v.tier === "exploratory" ? " (exploratory)" : ""}` }));
    if (!vars.find((x) => x.value === S.variable)) S.variable = vars[0].value;
    fillSelect($("sel-variable"), vars, S.variable);
    const a = avail(S.variable, S.location);
    S.first = Math.max(a.first, Math.min(S.first ?? a.first, a.last));
    S.last = Math.min(a.last, Math.max(S.last ?? a.last, a.first));
    if (S.first > S.last) { S.first = a.first; S.last = a.last; }
    fillSelect($("sel-first"), years(a.first, a.last), S.first);
    fillSelect($("sel-last"), years(a.first, a.last), S.last);
  }

  let invSeq = 0;
  async function loadInvestigation() {
    populateExplore(); renderCtx(); writeHash(currentView());
    const seq = ++invSeq;
    document.querySelectorAll("#view-explore .panel").forEach((p) => p.classList.add("loading"));
    try {
      const inv = await api(`/api/investigation?location=${S.location}&variable=${S.variable}&first=${S.first}&last=${S.last}`);
      if (seq !== invSeq) return;
      S.inv = inv; showError(null);
      renderExplore(); renderEvidence(); renderReports(); syncMap();
    } catch (e) {
      if (seq !== invSeq) return;
      S.inv = null; showError(e.message);
      $("stats").innerHTML = ""; $("sentence").textContent = "No result is shown for this selection."; $("plain").textContent = "";
      chart("chart-main").clear();
    } finally { document.querySelectorAll("#view-explore .panel").forEach((p) => p.classList.remove("loading")); }
  }

  function seriesChart(id, opts) {
    const c = chart(id);
    c.setOption({
      animationDuration: matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 250,
      grid: { left: 56, right: 18, top: 32, bottom: 64 },
      tooltip: { trigger: "axis", backgroundColor: "#0B1220", borderWidth: 0, textStyle: { color: "#F8FAFC", fontSize: 12 },
        valueFormatter: (v) => (v === null || v === undefined || Number.isNaN(v) ? "no value" : `${Number(v).toFixed(opts.decimals ?? 1)} ${opts.unit}`) },
      legend: { type: "scroll", bottom: 0, left: 0, textStyle: { color: C.slate, fontSize: 12 }, icon: "roundRect", itemWidth: 12, itemHeight: 3 },
      xAxis: { type: "category", data: opts.x.map(W), axisLine: { lineStyle: { color: C.border } }, axisLabel: { color: C.muted, fontSize: 11 }, axisTick: { show: false } },
      yAxis: { type: "value", name: opts.unit, nameTextStyle: { color: C.muted, fontSize: 11, align: "left" }, scale: true, splitLine: { lineStyle: { color: "#F1F5F9" } }, axisLabel: { color: C.muted, fontSize: 11 } },
      series: opts.series,
    }, true);
  }

  function renderExplore() {
    const inv = S.inv, f = inv.finding, v = inv.variable;
    const x = inv.series.map((d) => d.year);
    const inWin = (y) => y >= inv.first && y <= inv.last;
    const fittedMap = Object.fromEntries(inv.fitted.map((d) => [d.year, d.value]));
    const series = [
      { name: "Observed (in period)", type: "line", data: inv.series.map((d) => (inWin(d.year) ? d.value : null)), connectNulls: false, symbol: "circle", symbolSize: 6, lineStyle: { color: C.blue, width: 1.6 }, itemStyle: { color: C.blue } },
      { name: "Outside period", type: "line", data: inv.series.map((d) => (inWin(d.year) ? null : d.value)), connectNulls: false, symbol: "circle", symbolSize: 5, lineStyle: { color: "#CBD5E1", width: 1 }, itemStyle: { color: "#CBD5E1" } },
    ];
    if (inv.fitted.length) series.push({ name: "Theil-Sen trend", type: "line", data: x.map((y) => fittedMap[y] ?? null), symbol: "none", lineStyle: { color: C.navy, width: 1.6, type: "dashed" }, itemStyle: { color: C.navy } });
    seriesChart("chart-main", { x, unit: v.unit, decimals: v.decimals, series });
    $("chart-title").textContent = `${v.label} at ${inv.location.short || inv.location.name}`;
    $("chart-sub").textContent = `${v.source.name || ""}`;
    const missing = inv.series.filter((d) => inWin(d.year) && d.value === null).length;
    $("chart-note").textContent = `${missing ? `${missing} winter(s) in the period have no usable value and are left as gaps, never filled. ` : ""}Hover a point to read the winter and value.`;
    const chip = $("state-chip"); chip.className = `state ${f.state}`; chip.textContent = f.state_label;
    $("sentence").textContent = f.sentence;
    $("stats").innerHTML = inv.stat_rows.map((r) => `<dt>${esc(r.label)}</dt><dd>${esc(r.value)}</dd>`).join("") +
      (f.window_kind === "exploratory" && (f.status === "ok") ? `<dt>Adjusted q</dt><dd>not shown: user-selected window, exploratory, not adjusted for multiple testing</dd>` : "");
    const cv = $("caveat"); cv.hidden = !inv.bias_caveat; cv.textContent = inv.bias_caveat ? `Bias caveat: ${inv.bias_caveat}` : "";
    $("provenance").textContent = `Source: ${v.source.name}${v.power_parameter ? ` (${v.power_parameter})` : ""}. ${v.temporal_resolution || ""}; ${v.spatial_resolution || ""}. File: ${inv.source_file}. ${inv.series_note || ""}`;
    $("plain").textContent = inv.plain_language;
    $("definition").textContent = `Definition: ${v.definition}${v.why ? ` Why it matters: ${v.why}` : ""}`;
  }

  // ------------------------------------------------------------- atlas
  function initMap() {
    if (map || typeof maplibregl === "undefined") { if (typeof maplibregl === "undefined") $("map").innerHTML = '<p class="muted" style="padding:16px">The map library could not be loaded (offline?). Locations remain selectable from Explore.</p>'; return; }
    map = new maplibregl.Map({
      container: "map",
      style: { version: 8, sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "&copy; OpenStreetMap contributors" } }, layers: [{ id: "osm", type: "raster", source: "osm" }] },
      center: [-124, 65.5], zoom: 3.6, attributionControl: { compact: false },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    S.meta.locations.filter((l) => l.mapped).forEach((l) => {
      const el = document.createElement("button");
      el.className = "marker"; el.type = "button"; el.setAttribute("aria-label", `Select ${l.name}`); el.title = l.name;
      el.addEventListener("click", (ev) => { ev.stopPropagation(); selectLocation(l.id); });
      markers[l.id] = new maplibregl.Marker({ element: el }).setLngLat([l.lon, l.lat]).addTo(map);
      el.dataset.id = l.id; el.setAttribute("aria-label", `Select ${l.name}`);
    });
    syncMap();
  }
  function selectLocation(id) {
    S.location = id; S.first = null; S.last = null;
    loadInvestigation();
  }
  function syncMap() {
    Object.entries(markers).forEach(([id, m]) => m.getElement().classList.toggle("active", id === S.location));
    const l = S.meta.locations.find((x) => x.id === S.location);
    const side = $("atlas-side");
    const facts = (l.facts || []).map((f) => `<div class="fact"><b>${esc(f.label)}</b>${esc(f.text)} <span class="tag">${esc(f.status)}</span></div>`).join("");
    const others = S.meta.locations.filter((x) => !x.mapped).map((x) => `<li>${esc(x.name)}</li>`).join("");
    side.innerHTML = `<span class="tag">${esc(l.role === "primary" ? "Primary study location" : l.role === "comparison" ? "Comparison, different setting" : "Exploratory, approximate location")}</span>
      <h2 style="margin:4px 0 8px">${esc(l.name)}</h2>
      ${l.mapped ? `<p class="small muted">Sampling point ${fmtN(l.lat, 2)} N, ${fmtN(Math.abs(l.lon), 2)} W. ${esc(l.sampling_point)}</p>` : `<p class="small muted">No verified coordinates; this location is not drawn on the map.</p>`}
      ${l.cell ? `<p class="small">NASA POWER / MERRA-2 grid cell: ${esc(l.cell.label || JSON.stringify(l.cell))}</p>` : ""}
      <p>${esc(l.setting)}</p><p><b>Access:</b> ${esc(l.access)}</p>${l.caution ? `<p class="caveat">${esc(l.caution)}</p>` : ""}
      <div class="actions"><a class="btn primary" href="#explore">Investigate this location</a><a class="btn" href="#road">Road history</a></div>
      ${facts}
      <div class="fact"><b>Not drawn on the map</b>No route geometry is shown: Frostline does not have verified road lines. Supplementary corridors without verified coordinates: <ul class="small">${others}</ul></div>`;
    if (map && l.mapped && currentView() === "atlas") map.easeTo({ center: [l.lon, l.lat], zoom: Math.max(map.getZoom(), 4.2), duration: matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 600 });
  }

  // ------------------------------------------------------------- compare
  function populateCompare() {
    const primary = S.meta.locations.filter((l) => l.is_primary_pair || l.role === "supplementary");
    fillSelect($("cmp-a"), primary.map((l) => ({ value: l.id, label: l.name })), S.cmp.a);
    fillSelect($("cmp-b"), primary.map((l) => ({ value: l.id, label: l.name, disabled: l.id === S.cmp.a })), S.cmp.b);
    fillSelect($("cmp-var"), S.meta.compare_variables.map((id) => ({ value: id, label: varObj(id).label })), S.cmp.v);
    const a = avail(S.cmp.v, S.cmp.a), b = avail(S.cmp.v, S.cmp.b);
    const lo = Math.max(a.first, b.first), hi = Math.min(a.last, b.last);
    S.cmp.first = Math.max(lo, S.cmp.first ?? lo); S.cmp.last = Math.min(hi, S.cmp.last ?? hi);
    if (S.cmp.first > S.cmp.last) { S.cmp.first = lo; S.cmp.last = hi; }
    fillSelect($("cmp-first"), years(lo, hi), S.cmp.first); fillSelect($("cmp-last"), years(lo, hi), S.cmp.last);
  }
  async function loadCompare() {
    if (S.cmp.a === S.cmp.b) { S.cmp.b = S.meta.locations.find((l) => l.id !== S.cmp.a).id; }
    populateCompare();
    try {
      const c = await api(`/api/compare?variable=${S.cmp.v}&a=${S.cmp.a}&b=${S.cmp.b}&first=${S.cmp.first}&last=${S.cmp.last}`);
      showError(null);
      const x = []; for (let y = c.first; y <= c.last; y++) x.push(y);
      const val = (arr, y) => { const d = arr.find((r) => r.year === y); return d ? d.value : null; };
      seriesChart("chart-cmp", { x, unit: c.variable.unit, decimals: c.variable.decimals, series: [
        { name: c.a.short || c.a.name, type: "line", data: x.map((y) => val(c.series_a, y)), symbol: "circle", symbolSize: 5, lineStyle: { color: C.blue, width: 1.6 }, itemStyle: { color: C.blue } },
        { name: c.b.short || c.b.name, type: "line", data: x.map((y) => val(c.series_b, y)), symbol: "diamond", symbolSize: 6, lineStyle: { color: C.teal, width: 1.6 }, itemStyle: { color: C.teal } }] });
      $("cmp-title").textContent = `${c.variable.label}: ${c.a.short || c.a.name} and ${c.b.short || c.b.name}`;
      $("cmp-sub").textContent = `${c.common_years.length} matched winters, ${W(c.first)} to ${W(c.last)}, ${c.variable.unit}`;
      const u = c.variable.unit_per_decade;
      const row = (label, f) => `<tr><td>${esc(label)}</td><td class="num">${f.n}</td><td class="num">${(f.status === "ok") ? `${fmtN(f.slope, 1)}` : "not estimated"}</td><td class="num">${(f.status === "ok") ? `${fmtN(f.ci_low, 1)} to ${fmtN(f.ci_high, 1)}` : "n/a"}</td><td class="num">${f.p === null ? "n/a" : fmtN(f.p, 3)}</td><td><span class="state ${f.state}">${esc(f.state_label)}</span></td></tr>`;
      $("cmp-table").innerHTML = `<thead><tr><th>Series</th><th>n</th><th>Slope (${esc(u)})</th><th>95% interval (Theil-Sen)</th><th>p (unadjusted)</th><th>Status</th></tr></thead><tbody>${row(c.a.name, c.finding_a)}${row(c.b.name, c.finding_b)}${row("Difference (A minus B), matched winters", c.diff)}</tbody>`;
      const chip = $("cmp-chip"); chip.className = `state ${c.formal ? "unresolved" : "exploratory"}`; chip.textContent = c.formal ? "Approved comparison window" : "Descriptive, exploratory window";
      $("cmp-sentence").textContent = c.sentence;
      const cv = $("cmp-caveat"); cv.hidden = !c.bias_caveat; cv.textContent = c.bias_caveat ? `Bias caveat: ${c.bias_caveat}` : "";
    } catch (e) { showError(e.message); chart("chart-cmp").clear(); $("cmp-table").innerHTML = ""; $("cmp-sentence").textContent = "No comparison is shown for this selection."; }
  }

  // ------------------------------------------------------------- road
  async function loadRoad() {
    const roads = S.meta.locations.filter((l) => avail("open_day", l.id));
    fillSelect($("road-loc"), roads.map((l) => ({ value: l.id, label: `${l.road_name || l.name}${l.role === "supplementary" ? " (exploratory)" : ""}` })), S.road);
    try {
      const r = await api(`/api/road?location=${S.road}`); showError(null);
      const l = r.location;
      $("road-context").innerHTML = `<div class="panel-h"><h2>${esc(l.road_name || l.name)}</h2><span class="tag">${esc(l.road_kind_label)}</span></div><p>${esc(l.setting)}</p><p><b>Access context:</b> ${esc(l.access)}</p><p class="small muted">Records: ${r.status_counts.total} winters, ${r.status_counts.verified} verified${Object.keys(r.status_counts.other || {}).length ? `; other: ${esc(Object.entries(r.status_counts.other).map(([k, v]) => `${k} ${v}`).join(", "))}` : ""}.</p>`;
      const rec = r.record, x = rec.map((d) => d.season_start_year);
      const ok = (d, k) => (d.record_status === "verified" ? d[k] : null);
      const c = chart("chart-road");
      seriesChart("chart-road", { x, unit: "days since Oct 1", decimals: 0, series: [
        { name: "Opening day", type: "line", data: rec.map((d) => ok(d, "open_day")), symbol: "circle", symbolSize: 5, lineStyle: { color: C.blue }, itemStyle: { color: C.blue } },
        { name: "Closing day", type: "line", data: rec.map((d) => ok(d, "close_day")), symbol: "diamond", symbolSize: 6, lineStyle: { color: C.navy }, itemStyle: { color: C.navy } }] });
      c.setOption({ tooltip: { formatter: (ps) => { const d = rec[ps[0].dataIndex]; return `${W(d.season_start_year)}<br>Opened ${esc(d.opening_date || "no record")}<br>Closed ${esc(d.closing_date || "no record")}<br>Status: ${esc(d.record_status)}`; } } });
      const rows = Object.entries(r.trends).map(([k, t]) => {
        if (t.error) return `<tr><td>${esc(k)}</td><td colspan="6">${esc(t.error)}</td></tr>`;
        const f = t.finding;
        return `<tr><td>${esc(t.variable.label)}</td><td class="num">${W(f.first)} to ${W(f.last)}</td><td class="num">${f.n}</td><td class="num">${(f.status === "ok") ? fmtN(f.slope, 1) : "not estimated"}</td><td class="num">${(f.status === "ok") ? `${fmtN(f.ci_low, 1)} to ${fmtN(f.ci_high, 1)}` : "n/a"}</td><td class="num">${f.p === null ? "n/a" : fmtN(f.p, 3)}${f.q !== null ? `<br>q ${fmtN(f.q, 3)}` : ""}</td><td>${esc(f.sentence)}</td></tr>`;
      }).join("");
      $("road-trends").innerHTML = `<thead><tr><th>Metric</th><th>Period</th><th>n</th><th>Slope (days per decade)</th><th>95% interval</th><th>p / q</th><th>Reading</th></tr></thead><tbody>${rows}</tbody>`;
      $("road-caveat").textContent = `${r.road_caveat} Temperature data alone cannot tell whether a road is safe; Frostline is a historical record, not a prediction or safety tool.`;
      const env = r.environment.fdd_octdec;
      if (env) {
        const ey = env.series.map((d) => d.year);
        seriesChart("chart-road-env", { x: ey, unit: env.variable.unit, decimals: 0, series: [{ name: env.variable.label, type: "bar", data: env.series.map((d) => d.value), itemStyle: { color: "#93C5FD" }, barMaxWidth: 14 }] });
      } else chart("chart-road-env").clear();
      const as = r.associations || [];
      $("road-assoc").innerHTML = as.length ? `<thead><tr><th>Climate metric</th><th>Road metric</th><th>Window</th><th>Spearman rho</th><th>95% interval</th><th>n</th><th>q</th><th>Note</th></tr></thead><tbody>${as.map((a) => `<tr><td>${esc(a.climate_metric)}</td><td>${esc(a.road_metric)}</td><td>${esc(a.predictor_window)}</td><td class="num">${fmtN(a.spearman_rho, 2)}</td><td class="num">${fmtN(a.ci95_low, 2)} to ${fmtN(a.ci95_high, 2)}</td><td class="num">${a.n}</td><td class="num">${fmtN(a.q_bh_family, 3)}</td><td class="small">${esc(a.note)}</td></tr>`).join("")}</tbody>` : `<tbody><tr><td>No approved association results exist for this road.</td></tr></tbody>`;
    } catch (e) { showError(e.message); }
  }

  // ------------------------------------------------------------- evidence
  let stationLoaded = false;
  function renderEvidence() {
    if (!S.inv) return;
    const e = S.inv.evidence;
    $("ev-headline").textContent = e.headline; $("ev-suit").textContent = e.suitability;
    $("ev-dims").innerHTML = e.dimensions.map((d) => `<div class="dim ${esc(d.tone)}"><div class="t">${esc(d.title)}</div><div class="s">${esc(d.state)}</div><p>${esc(d.summary)}</p>${d.reasons.length ? `<ul class="small">${d.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}</div>`).join("");
    $("ev-layers").innerHTML = e.layers.map((l) => `<div class="fact"><b>${esc(l.title)}</b><span class="muted small">${esc(l.question)}</span><ul class="small">${l.items.map((i) => `<li>${esc(typeof i === "string" ? i : JSON.stringify(i))}</li>`).join("")}</ul></div>`).join("") + `<p class="small muted">Files used: ${esc(e.files.join(", "))}</p>`;
    const m = S.meta;
    $("ev-sources").innerHTML = `<h2>Sources and citations</h2>${Object.values(m.sources).map((s) => `<div class="fact"><b>${esc(s.name)}</b>${esc(s.citation || s.description || "")} ${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>` : ""}</div>`).join("")}<p class="small">${esc(m.power_ack)}</p><p class="small muted">AI-use disclosure: this interface and its API layer were written with the help of an AI coding assistant; all values come from the team's committed data and tested scientific code.</p>`;
  }
  async function loadStation() {
    if (stationLoaded) return;
    try {
      const s = await api("/api/station"); stationLoaded = true;
      seriesChart("chart-station", { x: s.years, unit: "°C-days", decimals: 0, series: [
        { name: "NASA POWER (MERRA-2 cell)", type: "line", data: s.nasa, symbol: "circle", symbolSize: 5, lineStyle: { color: C.blue }, itemStyle: { color: C.blue } },
        { name: "ECCC Yellowknife station", type: "line", data: s.station, symbol: "diamond", symbolSize: 6, connectNulls: false, lineStyle: { color: C.amber }, itemStyle: { color: C.amber } }] });
      $("station-note").textContent = `On ${s.n_complete} winters with a complete station record, the NASA POWER cell averages ${fmtN(s.nasa_mean, 0)} °C-days against ${fmtN(s.station_mean, 0)} at the station (${fmtN(s.pct_over, 0)}% higher; Pearson r = ${fmtN(s.pearson_r, 2)}). Gaps are station winters with missing days, never filled. ${s.diff_finding.sentence}`;
    } catch (e) { $("station-note").textContent = `Station comparison unavailable: ${e.message}`; }
  }

  // ------------------------------------------------------------- reports
  function renderReports() {
    if (!S.inv) return;
    const q = `location=${S.location}&variable=${S.variable}&first=${S.first}&last=${S.last}`;
    $("dl-html").href = `/api/brief.html?${q}`; $("dl-csv").href = `/api/series.csv?${q}`; $("dl-json").href = `/api/brief.json?${q}`;
    const f = S.inv.finding;
    $("rep-summary").textContent = `${S.inv.variable.label} at ${S.inv.location.name}, ${W(f.first)} to ${W(f.last)}, n = ${f.n} winters. ${f.state_label}. The brief contains the series, statistics, interpretation, evidence assessment, limitations and citations for exactly this selection.`;
    if (currentView() === "reports") $("rep-preview").src = `/api/brief.html?${q}&inline=1`;
  }

  // ------------------------------------------------------------- overview
  async function renderOverview() {
    const ids = S.meta.locations.filter((l) => l.is_primary_pair).map((l) => l.id);
    const cards = await Promise.all(ids.map((id) => api(`/api/investigation?location=${id}&variable=fdd_octdec`).catch(() => null)));
    $("ov-grid").innerHTML = cards.filter(Boolean).map((c) => `<button class="ov-card" type="button" data-loc="${c.location.id}"><span class="tag">${c.location.role === "primary" ? "Primary" : "Comparison, different setting"}</span><h2 style="margin:4px 0">${esc(c.location.name)}</h2><div class="n">Oct-Dec FDD, ${W(c.first)} to ${W(c.last)}, n = ${c.finding.n}</div><p class="small">${esc(c.finding.state_label)}. ${esc(c.finding.sentence)}</p></button>`).join("");
    document.querySelectorAll(".ov-card").forEach((b) => b.addEventListener("click", () => { S.location = b.dataset.loc; S.variable = "fdd_octdec"; S.first = S.last = null; location.hash = "#explore"; loadInvestigation(); }));
  }

  // ------------------------------------------------------------- routing
  function route() {
    const { view } = readHash();
    const v = document.getElementById(`view-${view}`) ? view : "overview";
    document.querySelectorAll(".view").forEach((s) => s.classList.toggle("on", s.id === `view-${v}`));
    document.querySelectorAll("[data-view]").forEach((a) => { const on = a.dataset.view === v; a.classList.toggle("active", on); if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    $("ctx").hidden = !["explore", "atlas", "evidence", "reports"].includes(v);
    if (v === "atlas") { initMap(); setTimeout(() => { map && map.resize(); syncMap(); }, 30); }
    if (v === "compare") loadCompare();
    if (v === "road") loadRoad();
    if (v === "evidence") loadStation();
    if (v === "reports") renderReports();
    if (S.inv) writeHash(v);
    setTimeout(() => Object.values(charts).forEach((c) => c.resize()), 20);
  }

  async function boot() {
    try { S.meta = await api("/api/meta"); }
    catch (e) { showError(`Frostline could not load its data: ${e.message}`); return; }
    const { p } = readHash();
    S.location = S.meta.locations.find((l) => l.id === p.get("l")) ? p.get("l") : S.meta.default_location;
    S.variable = S.meta.variables.find((v) => v.id === p.get("v")) ? p.get("v") : S.meta.default_variable;
    S.first = p.get("f") ? +p.get("f") : null; S.last = p.get("t") ? +p.get("t") : null;
    $("sel-location").addEventListener("change", (e) => selectLocation(e.target.value));
    $("sel-variable").addEventListener("change", (e) => { S.variable = e.target.value; S.first = S.last = null; loadInvestigation(); });
    $("sel-first").addEventListener("change", (e) => { S.first = +e.target.value; if (S.first > S.last) S.last = S.first; loadInvestigation(); });
    $("sel-last").addEventListener("change", (e) => { S.last = +e.target.value; if (S.last < S.first) S.first = S.last; loadInvestigation(); });
    $("btn-reset").addEventListener("click", () => { S.first = S.last = null; loadInvestigation(); });
    $("cmp-a").addEventListener("change", (e) => { S.cmp.a = e.target.value; if (S.cmp.b === S.cmp.a) S.cmp.b = S.meta.locations.find((l) => l.id !== S.cmp.a).id; S.cmp.first = S.cmp.last = null; loadCompare(); });
    $("cmp-b").addEventListener("change", (e) => { S.cmp.b = e.target.value; S.cmp.first = S.cmp.last = null; loadCompare(); });
    $("cmp-var").addEventListener("change", (e) => { S.cmp.v = e.target.value; S.cmp.first = S.cmp.last = null; loadCompare(); });
    $("cmp-first").addEventListener("change", (e) => { S.cmp.first = +e.target.value; if (S.cmp.first > S.cmp.last) S.cmp.last = S.cmp.first; loadCompare(); });
    $("cmp-last").addEventListener("change", (e) => { S.cmp.last = +e.target.value; if (S.cmp.last < S.cmp.first) S.cmp.first = S.cmp.last; loadCompare(); });
    $("road-loc").addEventListener("change", (e) => { S.road = e.target.value; loadRoad(); });
    window.addEventListener("hashchange", route);
    await loadInvestigation();
    renderOverview();
    route();
  }
  boot();
})();
