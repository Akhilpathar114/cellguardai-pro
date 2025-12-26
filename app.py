
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from bms_features import sanitize_bms_csv, engineer_features
from live_simulator import live_bms_stream

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="CellGuardAI | Battery Intelligence Report",
    layout="wide"
)

# ---------------- THEME ----------------
st.markdown("""
<style>
body { background-color:#0f1117; color:#e6e6e6; }
h1,h2,h3 { color:#f1f3f4; }
.section {
    padding:22px;
    border-radius:12px;
    background-color:#161a23;
    margin-bottom:22px;
}
.muted { color:#9aa0a6; font-size:14px; }
.sidebar-title { font-size:18px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("<div class='sidebar-title'>🔍 Analysis Navigator</div>", unsafe_allow_html=True)
nav = st.sidebar.radio(
    "Go to section",
    [
        "Overview",
        "How Analysis Works",
        "Key Findings",
        "Time-Based Analysis",
        "Prediction",
        "Recommendations",
        "Assumptions"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Report Context**")

# ---------------- DATA LOAD ----------------
source = st.sidebar.radio("Data Source", ["Live BMS (Demo)", "Upload CSV"])

if source == "Upload CSV":
    f = st.sidebar.file_uploader("Upload BMS CSV", type=["csv"])
    if not f:
        st.stop()
    raw = pd.read_csv(f)
else:
    raw = live_bms_stream()

df_full = engineer_features(sanitize_bms_csv(raw))

# ---------------- TIME WINDOW ----------------
window = st.sidebar.selectbox("Time Window", ["Full Data", "Last 7 Days", "Last 24 Hours"])

if window == "Last 24 Hours":
    df = df_full.tail(1440)
elif window == "Last 7 Days":
    df = df_full.tail(10080)
else:
    df = df_full.copy()

latest = df.iloc[-1]
analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------------- HEADER ----------------
st.markdown("""
<h1>🔋 CellGuardAI</h1>
<p class='muted'>
Narrative battery analysis with predictive intelligence
</p>
""", unsafe_allow_html=True)

# ---------------- OVERVIEW ----------------
if nav == "Overview":
    st.markdown(f"""
    <div class='section'>
    <h2>1. Analysis Overview</h2>
    <ul>
        <li><b>Samples analyzed:</b> {len(df)}</li>
        <li><b>Analysis time:</b> {analysis_time}</li>
        <li><b>Data source:</b> {source}</li>
        <li><b>Time window:</b> {window}</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# ---------------- HOW ANALYSIS WORKS ----------------
elif nav == "How Analysis Works":
    st.markdown("""
    <div class='section'>
    <h2>2. How CellGuardAI Analyzes Batteries</h2>
    <p>
    Instead of checking instant threshold violations, CellGuardAI examines how
    stress accumulates inside the battery over time.
    </p>
    <ul>
        <li>Tracks <b>cell imbalance growth rate</b></li>
        <li>Measures <b>thermal stress accumulation</b></li>
        <li>Estimates <b>health degradation slope</b></li>
    </ul>
    <details>
    <summary><b>Why this matters</b></summary>
    Early degradation often forms long before alarms trigger. Trend analysis
    reveals hidden risk.
    </details>
    </div>
    """, unsafe_allow_html=True)

# ---------------- KEY FINDINGS ----------------
elif nav == "Key Findings":
    cell_growth = df["cell_diff"].diff().mean()
    temp_avg = df["temp_max"].mean()
    health_drop = df["health_score"].iloc[0] - df["health_score"].iloc[-1]

    st.markdown(f"""
    <div class='section'>
    <h2>3. Key Findings</h2>
    <ul>
        <li>Cell imbalance is increasing at <b>{cell_growth:.3f} units/sample</b></li>
        <li>Average peak temperature observed: <b>{temp_avg:.1f} °C</b></li>
        <li>Total health degradation: <b>{health_drop:.2f} points</b></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# ---------------- TIME BASED ANALYSIS ----------------
elif nav == "Time-Based Analysis":
    st.markdown("""
    <div class='section'>
    <h2>4. Time-Based Evidence</h2>
    <p class='muted'>
    These plots show how internal stress builds gradually over time.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(px.line(df, y="health_score", title="Battery Health vs Time"), use_container_width=True)
    with st.expander("Why this matters"):
        st.write("A steeper downward slope indicates accelerated aging.")

    st.plotly_chart(px.line(df, y="cell_diff", title="Cell Imbalance vs Time"), use_container_width=True)
    with st.expander("Why this matters"):
        st.write("Growing imbalance increases internal stress and risk.")

    st.plotly_chart(px.line(df, y="temp_max", title="Maximum Temperature vs Time"), use_container_width=True)
    with st.expander("Why this matters"):
        st.write("Sustained thermal stress accelerates degradation.")

# ---------------- PREDICTION ----------------
elif nav == "Prediction":
    deg_rate = (100 - df["health_score"]).diff().rolling(10).mean().iloc[-1]
    if pd.isna(deg_rate) or deg_rate <= 0:
        deg_rate = 0.15

    health = latest["health_score"]
    fw = max((health - 55) / deg_rate, 0)
    low, high = fw * 0.8, fw * 1.3

    st.markdown(f"""
    <div class='section'>
    <h2>5. Future Risk Prediction</h2>
    <p>
    If current usage patterns continue, CellGuardAI estimates elevated risk within:
    </p>
    <h3>{int(low)} – {int(high)} cycles</h3>
    <p class='muted'>
    Prediction based on historical trend extrapolation (medium confidence)
    </p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- RECOMMENDATIONS ----------------
elif nav == "Recommendations":
    actions = []
    if fw < 50:
        actions.append("Inspect weakest cell and reduce load stress immediately")
    if latest["temp_max"] > 55:
        actions.append("Improve thermal dissipation during peak operation")
    if latest["cell_diff"] > 100:
        actions.append("Perform cell balancing procedure")
    if not actions:
        actions.append("Continue normal operation and periodic monitoring")

    st.markdown("""
    <div class='section'>
    <h2>6. Recommended Actions</h2>
    <ol>
    """, unsafe_allow_html=True)

    for a in actions:
        st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)

    st.markdown("""
    </ol>
    <details>
    <summary><b>How recommendations are generated</b></summary>
    Recommendations are derived from predicted risk horizon and observed stress patterns.
    </details>
    </div>
    """, unsafe_allow_html=True)

# ---------------- ASSUMPTIONS ----------------
elif nav == "Assumptions":
    st.markdown("""
    <div class='section'>
    <h2>7. Assumptions & Limitations</h2>
    <ul>
        <li>Trend-based model (not electrochemical simulation)</li>
        <li>Assumes similar future operating conditions</li>
        <li>Advisory decision-support system</li>
        <li>Conservative alignment with IEC / SAE safety philosophy (illustrative)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.caption(
    "CellGuardAI explains how batteries degrade over time and predicts future risk to guide proactive decisions."
)
