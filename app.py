from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from road_risk.analytics import (
    add_historical_indicator,
    demo_data,
    filtered_records,
    normalize_dataframe,
    quality_summary,
)

st.set_page_config(
    page_title="Proactive Road Risk Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1440px; }
      .hero { padding: 1.55rem 1.7rem; border-radius: 18px; color: #f8fafc;
              background: linear-gradient(125deg, #101c35 0%, #123f56 58%, #087e8b 100%);
              margin-bottom: 1.25rem; }
      .hero h1 { color: #fff; letter-spacing: -.035em; margin: .15rem 0 .55rem 0; }
      .hero p { color: #d8eaf0; font-size: 1.02rem; margin: 0; max-width: 850px; }
      .eyebrow { text-transform: uppercase; letter-spacing: .16em; font-weight: 700;
                 font-size: .73rem; color: #9ee7dd; }
      .notice { padding: .9rem 1rem; border: 1px solid #e9c46a; background: #fff8e4;
                border-radius: 10px; color: #594515; margin: .8rem 0 1rem 0; }
      [data-testid="stMetric"] { border: 1px solid #e5eaf0; border-radius: 13px; padding: 1rem; background: #fff; }
      [data-testid="stDataFrame"] { border: 1px solid #e5eaf0; border-radius: 10px; overflow: hidden; }
      footer { visibility: hidden; }
    </style>
    <div class="hero">
      <div class="eyebrow">Road safety intelligence · Research prototype</div>
      <h1>Proactive Road Risk Dashboard</h1>
      <p>Explore historical accident patterns, inspect weather and road-context factors, and prioritize records with an explainable historical indicator.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="notice"><strong>Scope:</strong> this prototype uses a transparent heuristic on historical accident records. It is not a trained AI model, calibrated crash probability, live traffic feed, or operational safety warning.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Data source")
    upload = st.file_uploader("Upload accident records (CSV)", type=["csv"])
    st.caption("The sample is synthetic and only intended to verify the interface. Upload a compatible historical CSV to analyse it.")
    st.divider()
    st.header("Filters")

try:
    if upload is not None:
        raw = pd.read_csv(upload, low_memory=False)
        source_label = f"Uploaded file: {upload.name}"
        is_demo = False
    else:
        raw = demo_data()
        source_label = "Built-in synthetic demo sample"
        is_demo = True
    data, report = normalize_dataframe(raw)
    data = add_historical_indicator(data)
except Exception as exc:
    st.error(f"Could not load this dataset: {exc}")
    st.info("Expected columns include Start_Lat and Start_Lng. Check the CSV's headers, encoding, and contents.")
    st.stop()

with st.sidebar:
    st.success(source_label)
    state_options = sorted(data["State"].dropna().astype(str).unique().tolist()) if "State" in data else []
    selected_states = st.multiselect("State / region", state_options, default=state_options)
    severity_options = (
        sorted(pd.to_numeric(data["Severity"], errors="coerce").dropna().astype(int).unique().tolist())
        if "Severity" in data else []
    )
    selected_severity = st.multiselect("Recorded severity", severity_options, default=severity_options)
    band_order = ["Low", "Guarded", "Elevated", "High"]
    selected_bands = st.multiselect("Indicator band", band_order, default=band_order)

filtered = filtered_records(data, selected_states, selected_severity, selected_bands)
if filtered.empty:
    st.warning("No records match the current filters. Expand the filters to continue.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Records analysed", f"{len(filtered):,}")
m2.metric("Mean historical indicator", f"{filtered['Historical_Risk_Indicator'].mean():.1f}/100")
m3.metric("Elevated / high records", f"{filtered['Indicator_Band'].isin(['Elevated', 'High']).sum():,}")
m4.metric("Rows removed for coordinates", f"{report.dropped_bad_coordinates:,}")
if is_demo:
    st.caption("Demo mode: metrics below describe 12 synthetic examples, not official accident statistics.")

overview, patterns, quality_tab, records_tab = st.tabs(
    ["Overview", "Explore patterns", "Data quality", "Records & export"]
)

with overview:
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Historical indicator distribution")
        band_counts = filtered["Indicator_Band"].value_counts().reindex(band_order, fill_value=0).rename_axis("Band").reset_index(name="Records")
        chart = px.bar(
            band_counts, x="Band", y="Records", color="Band",
            category_orders={"Band": band_order},
            color_discrete_map={"Low":"#2a9d8f","Guarded":"#e9c46a","Elevated":"#f4a261","High":"#e76f51"},
        )
        chart.update_layout(showlegend=False, margin=dict(l=5,r=5,t=20,b=5), height=330)
        st.plotly_chart(chart, use_container_width=True)
    with right:
        st.subheader("Configured signal checks")
        checks = []
        if "Visibility(mi)" in filtered:
            checks.append({"Signal":"Reduced visibility (≤5 mi)", "Records":int((pd.to_numeric(filtered["Visibility(mi)"], errors="coerce") <= 5).sum())})
        if "Weather_Condition" in filtered:
            checks.append({"Signal":"Severe weather label", "Records":int(filtered["Weather_Condition"].astype("string").str.lower().str.contains(r"heavy rain|thunder|snow|sleet|ice|freezing|fog", na=False).sum())})
        if "Sunrise_Sunset" in filtered:
            checks.append({"Signal":"Night-time record", "Records":int(filtered["Sunrise_Sunset"].astype("string").str.lower().eq("night").sum())})
        if checks:
            plot = px.bar(pd.DataFrame(checks), x="Records", y="Signal", orientation="h", color="Records", color_continuous_scale="Teal")
            plot.update_layout(coloraxis_showscale=False, margin=dict(l=5,r=5,t=20,b=5), height=330)
            st.plotly_chart(plot, use_container_width=True)
        else:
            st.info("Optional weather/time columns are not present in this dataset.")
    st.subheader("Highest indicator records")
    top_cols = [c for c in ["Start_Time","State","City","Severity","Weather_Condition","Historical_Risk_Indicator","Indicator_Band","Indicator_Explanation"] if c in filtered]
    st.dataframe(filtered.sort_values("Historical_Risk_Indicator", ascending=False)[top_cols].head(10), use_container_width=True, hide_index=True)
    if {"Start_Lat","Start_Lng"}.issubset(filtered.columns):
        st.subheader("Geographic distribution")
        map_data = filtered
        if len(map_data) > 3000:
            map_data = map_data.sample(3000, random_state=42)
            st.caption("Map samples 3,000 records for responsiveness; counts above use all filtered records.")
        hover_cols = [c for c in ["City","State","Historical_Risk_Indicator","Indicator_Band","Weather_Condition"] if c in map_data]
        map_fig = px.scatter_map(
            map_data, lat="Start_Lat", lon="Start_Lng", color="Indicator_Band",
            hover_data=hover_cols, zoom=2, height=450,
            color_discrete_map={"Low":"#2a9d8f","Guarded":"#e9c46a","Elevated":"#f4a261","High":"#e76f51"},
        )
        map_fig.update_layout(map_style="open-street-map", margin=dict(l=0,r=0,t=10,b=0), legend_title_text="Indicator")
        st.plotly_chart(map_fig, use_container_width=True)

with patterns:
    st.subheader("When do accident records occur?")
    if "Start_Time" in filtered and filtered["Start_Time"].notna().any():
        dated = filtered.dropna(subset=["Start_Time"]).copy()
        dated["Month"] = dated["Start_Time"].dt.to_period("M").astype(str)
        monthly = dated.groupby("Month", as_index=False).size().rename(columns={"size":"Records"})
        line = px.line(monthly, x="Month", y="Records", markers=True, title="Recorded events by month")
        line.update_layout(xaxis_title="Month", yaxis_title="Records", margin=dict(l=5,r=5,t=45,b=5))
        st.plotly_chart(line, use_container_width=True)
        dated["Hour"] = dated["Start_Time"].dt.hour
        hourly = dated.groupby("Hour", as_index=False).size().rename(columns={"size":"Records"})
        bars = px.bar(hourly, x="Hour", y="Records", title="Recorded events by hour")
        bars.update_layout(xaxis=dict(dtick=2), margin=dict(l=5,r=5,t=45,b=5))
        st.plotly_chart(bars, use_container_width=True)
    else:
        st.info("No usable Start_Time values are available for time-based charts.")
    if "State" in filtered:
        by_state = filtered.groupby("State", dropna=False).size().reset_index(name="Records").sort_values("Records", ascending=False).head(15)
        st.subheader("Top regions in filtered records")
        state_fig = px.bar(by_state, x="State", y="Records", color="Records", color_continuous_scale="Teal")
        state_fig.update_layout(coloraxis_showscale=False, margin=dict(l=5,r=5,t=20,b=5))
        st.plotly_chart(state_fig, use_container_width=True)
    if "Weather_Condition" in filtered:
        by_weather = filtered["Weather_Condition"].fillna("Unknown").astype(str).value_counts().head(12).rename_axis("Weather").reset_index(name="Records")
        st.subheader("Common weather labels")
        weather_fig = px.bar(by_weather, x="Records", y="Weather", orientation="h")
        weather_fig.update_layout(yaxis={"categoryorder":"total ascending"}, margin=dict(l=5,r=5,t=20,b=5))
        st.plotly_chart(weather_fig, use_container_width=True)

with quality_tab:
    st.subheader("Dataset quality")
    q1, q2, q3 = st.columns(3)
    q1.metric("Input rows", f"{report.rows_in:,}")
    q2.metric("Valid-coordinate rows", f"{report.rows_out:,}")
    q3.metric("Rows removed", f"{report.dropped_bad_coordinates:,}")
    for warning in report.warnings:
        st.warning(warning)
    if not report.warnings:
        st.success("No missing-field or coordinate warning was raised by the current checks.")
    st.dataframe(quality_summary(data), use_container_width=True, hide_index=True)
    st.caption("Quality checks cannot verify source truth. Extreme values should be checked against domain-specific rules.")

with records_tab:
    st.subheader("Filtered records and CSV export")
    st.caption("The original row fields are retained for valid-coordinate rows; indicator fields are additional heuristic results.")
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=480)
    csv_bytes = BytesIO()
    filtered.to_csv(csv_bytes, index=False)
    st.download_button(
        "Download filtered records (CSV)", data=csv_bytes.getvalue(),
        file_name="road_risk_filtered_records.csv", mime="text/csv",
    )

st.divider()
st.caption("Proactive Road Risk Dashboard · Historical analytics prototype · Not for emergency response or operational safety decisions.")
