import { useCallback, useEffect, useMemo, useState } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowUpRight, BarChart3, Check,
  ChevronDown, ChevronLeft, ChevronRight, CircleHelp, CloudRain, Database,
  FileSpreadsheet, Filter, Gauge, Layers3, LoaderCircle, MapPin, RefreshCw,
  Search, ShieldCheck, Upload, Wind, X
} from "lucide-react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

const Plot = createPlotlyComponent(Plotly);
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const BANDS = ["Low", "Guarded", "Elevated", "High"];
const BAND_COLORS = { Low: "#49c3a7", Guarded: "#e8bd64", Elevated: "#ed8c55", High: "#f06b68" };
const LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, ui-sans-serif, system-ui", color: "#9baec1", size: 11 },
  margin: { l: 42, r: 14, t: 24, b: 42 },
  xaxis: { gridcolor: "rgba(142,164,184,.10)", zerolinecolor: "rgba(142,164,184,.10)", automargin: true },
  yaxis: { gridcolor: "rgba(142,164,184,.10)", zerolinecolor: "rgba(142,164,184,.10)", automargin: true },
  showlegend: false
};
const CONFIG = { responsive: true, displayModeBar: false, displaylogo: false };

async function api(path, options = {}) {
  const response = await fetch(API_BASE + path, options);
  const type = response.headers.get("content-type") || "";
  const body = type.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = body && typeof body === "object" ? body.detail || body.message : body;
    throw new Error(message || "Request failed (" + response.status + ")");
  }
  return body;
}
const number = (value) => Number(value || 0).toLocaleString("en-US", { maximumFractionDigits: 1 });
function dateLabel(value) {
  if (!value) return "—";
  const valueDate = new Date(value);
  return Number.isNaN(valueDate.getTime()) ? "—" : valueDate.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
function BandBadge({ band }) {
  return <span className={"band-badge band-" + String(band || "low").toLowerCase()}><i />{band || "Low"}</span>;
}
function MetricCard({ label, value, note, icon: Icon, accent }) {
  return <div className="metric-card"><div className="metric-card-top"><span className={"metric-icon " + accent}><Icon size={17} /></span><span className="metric-note">{note}</span></div><div className="metric-value">{value}</div><div className="metric-label">{label}</div></div>;
}
function PanelHeading({ eyebrow, title, action }) {
  return <div className="panel-heading"><div><div className="panel-eyebrow">{eyebrow}</div><h2>{title}</h2></div>{action}</div>;
}
function Empty({ title, detail }) {
  return <div className="empty-state"><Database size={23} /><strong>{title}</strong><span>{detail}</span></div>;
}
function RiskMap({ points }) {
  const center = useMemo(() => {
    if (!points?.length) return [39.5, -98.35];
    return [points.reduce((sum, p) => sum + p.lat, 0) / points.length, points.reduce((sum, p) => sum + p.lng, 0) / points.length];
  }, [points]);
  if (!points?.length) return <Empty title="No mapped records" detail="Try broadening the current filters." />;
  return <MapContainer center={center} zoom={4} scrollWheelZoom className="risk-map">
    <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
    {points.slice(0, 900).map((p, i) => <CircleMarker key={p.id || (String(p.lat) + "-" + String(p.lng) + "-" + i)} center={[p.lat, p.lng]} radius={p.risk_band === "High" ? 6 : 4} pathOptions={{ color: BAND_COLORS[p.risk_band] || BAND_COLORS.Low, fillColor: BAND_COLORS[p.risk_band] || BAND_COLORS.Low, fillOpacity: .8, weight: 1 }}>
      <Popup><div className="map-popup"><strong>{p.city}, {p.state}</strong><span>Indicator: {p.risk_score}/100</span><span>Band: {p.risk_band}</span>{p.severity && <span>Recorded severity: {p.severity}/4</span>}</div></Popup>
    </CircleMarker>)}
  </MapContainer>;
}

export default function App() {
  const [filters, setFilters] = useState({ state: "", severity: "", band: "", search: "" });
  const [searchDraft, setSearchDraft] = useState("");
  const [options, setOptions] = useState({ states: [], severities: [], bands: BANDS });
  const [dashboard, setDashboard] = useState(null);
  const [records, setRecords] = useState({ total: 0, items: [] });
  const [quality, setQuality] = useState(null);
  const [meta, setMeta] = useState(null);
  const [page, setPage] = useState(0);
  const [view, setView] = useState("Overview");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [updated, setUpdated] = useState(new Date());

  const query = useMemo(() => {
    const p = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => { if (value !== "") p.set(key, value); });
    return p.toString();
  }, [filters]);
  const loadDashboard = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError("");
    try {
      const [data, opts, metadata] = await Promise.all([api("/api/dashboard" + (query ? "?" + query : "")), api("/api/options"), api("/api/meta")]);
      setDashboard(data); setOptions(opts); setMeta(metadata); setUpdated(new Date());
    } catch (err) { setError(err.message || "Could not connect to the API."); }
    finally { setLoading(false); }
  }, [query]);
  const loadRecords = useCallback(async () => {
    if (view !== "Incidents") return;
    try {
      const params = new URLSearchParams(query); params.set("offset", String(page * 25)); params.set("limit", "25");
      setRecords(await api("/api/records?" + params.toString()));
    } catch (err) { setError(err.message || "Could not load records."); }
  }, [view, page, query]);
  const loadQuality = useCallback(async () => {
    if (view !== "Data quality") return;
    try { setQuality(await api("/api/quality" + (query ? "?" + query : ""))); }
    catch (err) { setError(err.message || "Could not load quality report."); }
  }, [view, query]);
  useEffect(() => { loadDashboard(); }, [loadDashboard]);
  useEffect(() => { loadRecords(); }, [loadRecords]);
  useEffect(() => { loadQuality(); }, [loadQuality]);

  function changeFilter(key, value) {
    setPage(0);
    setFilters((old) => ({ ...old, [key]: value }));
    if (key === "search") setSearchDraft(value);
  }
  function resetFilters() {
    setFilters({ state: "", severity: "", band: "", search: "" }); setSearchDraft(""); setPage(0);
  }
  async function uploadCsv(event) {
    const file = event.target.files?.[0]; event.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) { setError("Choose a CSV file."); return; }
    setUploading(true); setError(""); setNotice("");
    try {
      const body = new FormData(); body.append("file", file);
      const result = await api("/api/upload", { method: "POST", body });
      resetFilters(); setNotice(number(result.metadata.row_count) + " records imported from " + file.name + ".");
      setView("Overview"); await loadDashboard(true);
    } catch (err) { setError(err.message || "Import failed."); }
    finally { setUploading(false); }
  }
  async function resetDemo() {
    setResetting(true); setError(""); setNotice("");
    try {
      const result = await api("/api/demo/reset", { method: "POST" });
      resetFilters(); setNotice(number(result.metadata.row_count) + " synthetic demo records restored.");
      setView("Overview"); await loadDashboard(true);
    } catch (err) { setError(err.message || "Could not restore the demo sample."); }
    finally { setResetting(false); }
  }
  const summary = dashboard?.summary;
  const exportHref = API_BASE + "/api/export.csv" + (query ? "?" + query : "");

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#overview" onClick={(e) => { e.preventDefault(); setView("Overview"); }}>
        <span className="brand-mark"><Activity size={23} /></span><span className="brand-copy"><strong>ROADSAFE<span>AI</span></strong><small>RISK INTELLIGENCE</small></span>
      </a>
      <div className="workspace-switch"><span className="workspace-avatar">US</span><span><strong>National overview</strong><small>Historical dataset</small></span><ChevronDown size={15} /></div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Dashboard views">
        <button className={view === "Overview" ? "active" : ""} onClick={() => setView("Overview")}><Layers3 size={17} />Overview</button>
        <button className={view === "Incidents" ? "active" : ""} onClick={() => setView("Incidents")}><MapPin size={17} />Incident explorer<span className="nav-count">{summary ? number(summary.records) : "—"}</span></button>
        <button className={view === "Data quality" ? "active" : ""} onClick={() => setView("Data quality")}><Database size={17} />Data quality</button>
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-source"><div className="source-icon"><ShieldCheck size={18} /></div><div><strong>Explainable by design</strong><p>Every indicator includes the factors contributing to its score.</p></div></div>
      <div className="sidebar-foot"><span className="live-dot" />API connection <strong>{error && !dashboard ? "Offline" : "Ready"}</strong><small>BUILD 2.0.0</small></div>
    </aside>

    <main className="main-content">
      <header className="topbar">
        <div className="breadcrumbs"><span>Road safety</span><ChevronRight size={14} /><strong>{view}</strong></div>
        <div className="topbar-actions"><span className="updated-time"><span className="live-dot" />Updated {updated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span><button className="icon-button" title="Refresh dashboard" onClick={() => loadDashboard()}><RefreshCw size={16} /></button><span className="user-avatar">K</span></div>
      </header>

      <div className="page-wrap">
        <div className="page-title-row">
          <div><div className="eyebrow">ROAD SAFETY ANALYTICS <span>•</span> V2.0</div><h1>{view === "Overview" ? "Risk intelligence overview" : view === "Incidents" ? "Incident explorer" : "Data quality centre"}</h1><p className="page-subtitle">{view === "Overview" ? "Turn historical accident records into a clearer picture of risk patterns." : view === "Incidents" ? "Search, filter and inspect historical accident records." : "Inspect missing values and validation results before analysis."}</p></div>
          <div className="page-actions">
            <label className={"button button-secondary " + (uploading ? "disabled" : "")}>{uploading ? <LoaderCircle className="spin" size={16} /> : <Upload size={16} />}{uploading ? "Importing…" : "Import CSV"}<input type="file" accept=".csv,text/csv" onChange={uploadCsv} disabled={uploading} hidden /></label>
            <a className="button button-primary" href={exportHref}><ArrowDownToLine size={16} />Export CSV</a>
          </div>
        </div>

        <div className="prototype-notice"><span className="notice-symbol"><AlertTriangle size={17} /></span><div><strong>Historical analysis prototype</strong><span>The risk indicator is a transparent heuristic on recorded accident data — not a trained model, future-crash probability or live road warning.</span></div><a href="https://github.com/KamaleshTech/Proactive_Road_Risk_Dashboard" target="_blank" rel="noreferrer">Project notes <ArrowUpRight size={13} /></a></div>
        {error && <div className="toast toast-error"><AlertTriangle size={16} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss"><X size={16} /></button></div>}
        {notice && <div className="toast toast-success"><Check size={16} /><span>{notice}</span><button onClick={() => setNotice("")} aria-label="Dismiss"><X size={16} /></button></div>}

        <section className="filter-bar">
          <div className="filter-title"><Filter size={15} /><span>FILTERS</span></div>
          <label className="filter-field"><span>State / region</span><select value={filters.state} onChange={(e) => changeFilter("state", e.target.value)}><option value="">All regions</option>{options.states.map((s) => <option key={s} value={s}>{s}</option>)}</select></label>
          <label className="filter-field"><span>Recorded severity</span><select value={filters.severity} onChange={(e) => changeFilter("severity", e.target.value)}><option value="">All severities</option>{options.severities.map((s) => <option key={s} value={s}>Level {s}</option>)}</select></label>
          <label className="filter-field"><span>Indicator band</span><select value={filters.band} onChange={(e) => changeFilter("band", e.target.value)}><option value="">All bands</option>{BANDS.map((b) => <option key={b} value={b}>{b}</option>)}</select></label>
          <form className="search-form" onSubmit={(e) => { e.preventDefault(); changeFilter("search", searchDraft.trim()); }}><Search size={16} /><input aria-label="Search city state weather" placeholder="Search city, state, weather…" value={searchDraft} onChange={(e) => setSearchDraft(e.target.value)} />{searchDraft && <button type="button" onClick={() => { setSearchDraft(""); changeFilter("search", ""); }} aria-label="Clear search"><X size={14} /></button>}<button type="submit" className="search-submit">Search</button></form>
          <button className="clear-filters" onClick={resetFilters}>Reset</button>
        </section>

        {loading && !dashboard ? <div className="loading-state"><LoaderCircle className="spin" size={28} /><strong>Loading road-risk intelligence</strong><span>Connecting to the analytics API…</span></div>
          : !dashboard ? <div className="offline-state"><Database size={30} /><h2>Dashboard data unavailable</h2><p>Start the FastAPI backend and reload. A local setup normally uses port 8000.</p><button className="button button-primary" onClick={() => loadDashboard()}>Retry connection</button></div>
          : view === "Overview" ? <Overview dashboard={dashboard} onIncidents={() => setView("Incidents")} onReset={resetDemo} resetting={resetting} />
          : view === "Incidents" ? <Incidents data={records} page={page} pages={Math.max(1, Math.ceil((records.total || 0) / 25))} onPage={setPage} exportHref={exportHref} />
          : <DataQuality quality={quality || { dataset: meta, report: dashboard.quality }} onReset={resetDemo} resetting={resetting} />}

        <footer className="page-footer"><span>ROADSAFE AI <b className="footer-separator">/</b> HISTORICAL ROAD SAFETY ANALYTICS</span><span><CircleHelp size={14} />Prototype only · Not for emergency response</span></footer>
      </div>
    </main>
  </div>;
}

function Overview({ dashboard, onIncidents, onReset, resetting }) {
  const { summary, risk_bands, monthly, hourly, by_state, by_weather, map_points, top_records, meta } = dashboard;
  const donut = { type: "pie", labels: risk_bands.map((x) => x.band), values: risk_bands.map((x) => x.records), hole: .72, sort: false, marker: { colors: risk_bands.map((x) => BAND_COLORS[x.band]) }, textinfo: "none", hovertemplate: "%{label}<br>%{value:,} records<extra></extra>" };
  const trend = { type: "scatter", mode: "lines+markers", x: monthly.map((x) => x.month), y: monthly.map((x) => x.records), line: { color: "#5aaddd", width: 2.4, shape: "spline" }, marker: { color: "#82d5ef", size: 5 }, fill: "tozeroy", fillcolor: "rgba(90,173,221,.10)", hovertemplate: "%{x}<br>%{y:,} records<extra></extra>" };
  const hours = { type: "bar", x: hourly.map((x) => String(x.hour).padStart(2, "0") + ":00"), y: hourly.map((x) => x.records), marker: { color: "#45b8a0" }, hovertemplate: "%{x}<br>%{y:,} records<extra></extra>" };
  const states = { type: "bar", orientation: "h", x: by_state.map((x) => x.records), y: by_state.map((x) => x.state), marker: { color: "#4ba5d0" }, hovertemplate: "%{y}<br>%{x:,} records<extra></extra>" };
  const weather = { type: "bar", orientation: "h", x: by_weather.map((x) => x.records), y: by_weather.map((x) => x.weather), marker: { color: "#b2a0ee" }, hovertemplate: "%{y}<br>%{x:,} records<extra></extra>" };
  return <div className="dashboard-stack">
    <div className="dataset-ribbon"><span className="dataset-ribbon-icon"><Database size={15} /></span><div><strong>{meta?.is_demo ? "Synthetic demo sample" : (meta?.name || "Uploaded dataset")}</strong><span>{number(meta?.row_count)} validated records · {meta?.is_demo ? "Synthetic example data" : "User-provided historical data"}</span></div><button className="text-button" onClick={onReset} disabled={resetting}>{resetting ? <LoaderCircle size={14} className="spin" /> : <RefreshCw size={14} />}{resetting ? "Restoring…" : "Reset demo"}</button></div>
    <div className="metrics-grid">
      <MetricCard label="Records in view" value={number(summary.records)} note="Current filters" icon={Database} accent="blue" />
      <MetricCard label="Average indicator" value={summary.mean_indicator} note="/ 100" icon={Gauge} accent="teal" />
      <MetricCard label="Elevated / high" value={number(summary.elevated_high)} note={(summary.records ? Math.round(summary.elevated_high / summary.records * 100) : 0) + "% of view"} icon={AlertTriangle} accent="amber" />
      <MetricCard label="High indicator" value={number(summary.high_records)} note="Heuristic band" icon={Activity} accent="rose" />
    </div>
    <div className="chart-grid chart-grid-main">
      <section className="panel"><PanelHeading eyebrow="TEMPORAL PATTERNS" title="Recorded incidents over time" action={<span className="chart-tag"><Activity size={13} />Monthly</span>} />
        {monthly.length ? <Plot data={[trend]} layout={{ ...LAYOUT, height: 285, margin: { l: 44, r: 12, t: 20, b: 48 }, xaxis: { ...LAYOUT.xaxis, tickangle: -25, nticks: 8 }, yaxis: { ...LAYOUT.yaxis, rangemode: "tozero" } }} config={CONFIG} useResizeHandler className="plot" /> : <Empty title="No usable timestamps" detail="Records need a valid start-time field for temporal charts." />}
        <div className="chart-footnote"><span className="footnote-dot" />Historical event counts, not the probability of an accident.</div>
      </section>
      <section className="panel"><PanelHeading eyebrow="INDICATOR DISTRIBUTION" title="Historical risk bands" />
        {summary.records ? <><div className="donut-wrap"><Plot data={[donut]} layout={{ ...LAYOUT, height: 215, margin: { l: 2, r: 2, t: 0, b: 0 }, annotations: [{ text: "<b>" + number(summary.records) + "</b><br><span style='font-size:10px'>records</span>", showarrow: false, font: { size: 21, color: "#edf6ff" } }] }} config={CONFIG} useResizeHandler className="plot donut-plot" /></div><div className="band-legend">{risk_bands.map((row) => <div key={row.band}><span style={{ background: BAND_COLORS[row.band] }} /><span>{row.band}</span><strong>{number(row.records)}</strong></div>)}</div></> : <Empty title="No matching records" detail="Reset or broaden the filters." />}
      </section>
    </div>
    <div className="chart-grid chart-grid-three">
      <section className="panel"><PanelHeading eyebrow="DAILY RHYTHM" title="Records by hour" />{hourly.length ? <Plot data={[hours]} layout={{ ...LAYOUT, height: 250, margin: { l: 38, r: 8, t: 15, b: 38 }, xaxis: { ...LAYOUT.xaxis, tickangle: -40, dtick: 3 }, yaxis: { ...LAYOUT.yaxis, rangemode: "tozero" }, bargap: .25 }} config={CONFIG} useResizeHandler className="plot" /> : <Empty title="Time data unavailable" detail="Upload records with Start_Time." />}</section>
      <section className="panel"><PanelHeading eyebrow="REGIONAL VIEW" title="Top states / regions" />{by_state.length ? <Plot data={[states]} layout={{ ...LAYOUT, height: 250, margin: { l: 42, r: 10, t: 15, b: 25 }, yaxis: { ...LAYOUT.yaxis, autorange: "reversed" }, xaxis: { ...LAYOUT.xaxis, rangemode: "tozero" }, bargap: .35 }} config={CONFIG} useResizeHandler className="plot" /> : <Empty title="Region data unavailable" detail="No state names in the filtered records." />}</section>
      <section className="panel"><PanelHeading eyebrow="CONTEXT" title="Common weather labels" />{by_weather.length ? <Plot data={[weather]} layout={{ ...LAYOUT, height: 250, margin: { l: 95, r: 10, t: 15, b: 25 }, yaxis: { ...LAYOUT.yaxis, autorange: "reversed" }, xaxis: { ...LAYOUT.xaxis, rangemode: "tozero" }, bargap: .35 }} config={CONFIG} useResizeHandler className="plot" /> : <Empty title="Weather unavailable" detail="No weather labels found." />}</section>
    </div>
    <section className="panel map-panel"><PanelHeading eyebrow="GEOSPATIAL CONTEXT" title="Accident record distribution" action={<span className="chart-tag"><MapPin size={13} />{number(map_points.length)} points</span>} /><div className="map-legend">{BANDS.map((band) => <span key={band}><i style={{ background: BAND_COLORS[band] }} />{band}</span>)}</div><RiskMap points={map_points} /><div className="map-footnote"><MapPin size={13} />Historical record locations. Colour shows configured heuristic, not an official danger classification.</div></section>
    <section className="panel top-records-panel"><PanelHeading eyebrow="PRIORITY REVIEW" title="Highest indicator records" action={<button className="text-button" onClick={onIncidents}>Open incident explorer <ArrowUpRight size={14} /></button>} />
      {top_records.length ? <div className="table-wrap"><table className="records-table"><thead><tr><th>LOCATION / TIME</th><th>WEATHER</th><th>RECORDED SEVERITY</th><th>INDICATOR</th><th>WHY IT SCORED</th></tr></thead><tbody>{top_records.slice(0, 6).map((row, i) => <tr key={row.id || (row.city + "-" + row.start_time + "-" + i)}><td><strong>{row.city}, {row.state}</strong><span>{dateLabel(row.start_time)}</span></td><td>{row.weather_condition || "Unknown"}</td><td>{row.severity ? <span className="severity-level">L{row.severity}</span> : "—"}</td><td><div className="score-cell"><strong>{row.risk_score}</strong><span className="score-track"><i style={{ width: row.risk_score + "%", background: BAND_COLORS[row.risk_band] }} /></span><BandBadge band={row.risk_band} /></div></td><td className="explanation-cell">{row.explanation}</td></tr>)}</tbody></table></div> : <Empty title="No records to show" detail="Broaden the active filters." />}
    </section>
    <div className="below-fold-actions"><div><Wind size={17} /><span>Weather and road-context signals are explicit, reviewable rules.</span></div><button className="button button-secondary" onClick={onIncidents}>Explore records <ArrowUpRight size={15} /></button></div>
  </div>;
}

function Incidents({ data, page, pages, onPage, exportHref }) {
  return <div className="dashboard-stack">
    <div className="dataset-ribbon"><span className="dataset-ribbon-icon"><FileSpreadsheet size={16} /></span><div><strong>Filtered incident records</strong><span>{number(data.total)} records match. Showing up to 25 per page.</span></div><a className="text-button" href={exportHref}><ArrowDownToLine size={14} />Export current view</a></div>
    <section className="panel incident-list-panel"><PanelHeading eyebrow="HISTORICAL RECORDS" title="Incident explorer" action={<span className="chart-tag"><Database size={13} />{number(data.total)} results</span>} />
      {data.items?.length ? <><div className="table-wrap"><table className="records-table incidents-table"><thead><tr><th>LOCATION / TIME</th><th>WEATHER</th><th>SEVERITY</th><th>INDICATOR</th><th>EXPLANATION</th><th>COORDINATES</th></tr></thead><tbody>{data.items.map((row) => <tr key={row.id}><td><strong>{row.city}, {row.state}</strong><span>{dateLabel(row.start_time)}</span></td><td>{row.weather_condition || "Unknown"}</td><td>{row.severity ? <span className="severity-level">L{row.severity}</span> : "—"}</td><td><div className="score-cell"><strong>{row.risk_score}</strong><BandBadge band={row.risk_band} /></div></td><td className="explanation-cell">{row.explanation}</td><td className="coordinates">{Number(row.start_lat).toFixed(4)}, {Number(row.start_lng).toFixed(4)}</td></tr>)}</tbody></table></div><div className="pagination"><span>Showing {data.total ? page * 25 + 1 : 0}–{Math.min((page + 1) * 25, data.total)} of {number(data.total)}</span><div><button disabled={page === 0} onClick={() => onPage(Math.max(0, page - 1))}><ChevronLeft size={15} />Previous</button><span>Page {page + 1} / {pages}</span><button disabled={page + 1 >= pages} onClick={() => onPage(Math.min(pages - 1, page + 1))}>Next<ChevronRight size={15} /></button></div></div></> : <Empty title="No records match" detail="Change the filters or reset them to see more records." />}
    </section>
    <div className="notice-inline"><AlertTriangle size={15} /><span>Recorded severity is an event label. It is kept separate from the heuristic indicator and is not used to calculate the score.</span></div>
  </div>;
}

function DataQuality({ quality, onReset, resetting }) {
  if (!quality) return <div className="loading-state"><LoaderCircle className="spin" size={25} /><strong>Loading quality report</strong></div>;
  const report = quality.report || {};
  const fields = report.fields || [];
  return <div className="dashboard-stack">
    <div className="dataset-ribbon"><span className="dataset-ribbon-icon"><Database size={16} /></span><div><strong>{quality.dataset?.name || "Active dataset"}</strong><span>{number(report.rows)} records in the current view</span></div><button className="text-button" onClick={onReset} disabled={resetting}>{resetting ? <LoaderCircle size={14} className="spin" /> : <RefreshCw size={14} />}{resetting ? "Restoring…" : "Reset demo"}</button></div>
    <div className="metrics-grid"><MetricCard label="Records checked" value={number(report.rows)} note="Current filters" icon={Database} accent="blue" /><MetricCard label="Invalid coordinate rows removed" value={number(quality.dataset?.dropped_rows || 0)} note="Last import" icon={MapPin} accent="amber" /><MetricCard label="Fields inspected" value={number(fields.length)} note="Normalized schema" icon={Check} accent="teal" /><MetricCard label="Active dataset" value={quality.dataset?.is_demo ? "Demo" : "Upload"} note="Dataset source" icon={FileSpreadsheet} accent="rose" /></div>
    <section className="panel quality-panel"><PanelHeading eyebrow="DATA HEALTH" title="Missing-value overview" action={<span className="chart-tag"><Check size={13} />Validation active</span>} /><p className="panel-description">Optional sensor and context fields may be missing. Invalid coordinates are removed; unusual environmental values are treated as missing rather than silently influencing the indicator.</p>
      {fields.length ? <div className="quality-list">{fields.map((field) => <div className="quality-row" key={field.field}><div className="quality-name"><strong>{field.field.replaceAll("_", " ")}</strong><span>{number(field.missing)} missing</span></div><div className="quality-track"><i style={{ width: Math.min(100, field.missing_percent) + "%" }} /></div><strong className={field.missing_percent > 25 ? "quality-high" : ""}>{field.missing_percent.toFixed(1)}%</strong></div>)}</div> : <Empty title="No missing values to report" detail="No recognized fields in this view." />}
    </section>
    <section className="panel note-panel"><div className="note-icon"><CircleHelp size={18} /></div><div><strong>What these checks do — and do not — tell you</strong><p>The report flags missing values and validates coordinates. It does not certify that source values are true or that data represents times when no accident occurred. Predictive modelling needs an explicitly constructed target, background samples, temporal/geographic validation and leakage review.</p></div></section>
  </div>;
}
