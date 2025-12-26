
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from bms_features import sanitize_bms_csv, engineer_features
from live_simulator import live_bms_stream

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="CellGuardAI | Battery Analysis Report",
    layout="wide"
)

# ---------------- THEME ----------------
st.markdown("""
<style>
body { background-color:#0f1117; color:#e6e6e6; }
h1,h2,h3 { color:#f1f3f4; }
.section { padding:20px; border-radius:10px; background-color:#161a23; margin-bottom:18px; }
.muted { color:#9aa0a6; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<h1>🔋 CellGuardAI – Battery Analysis Report</h1>
<p class='muted'>
AI-driven diagnostic and predictive analysis of battery behavior over time
</p>
""", unsafe_allow_html=True)

# ---------------- DATA LOAD ----------------
source = st.radio("Data Source", ["Live BMS (Demo)", "Upload CSV"], horizontal=True)

if source == "Upload CSV":
    f = st.file_uploader("Upload BMS CSV file", type=["csv"])
    if not f:
        st.stop()
    raw = pd.read_csv(f)
else:
    raw = live_bms_stream()

df = engineer_features(sanitize_bms_csv(raw))
latest = df.iloc[-1]

duration = len(df)
analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------------- SECTION 1: OVERVIEW ----------------
st.markdown(f"""
<div class='section'>
<h2>1. Analysis Overview</h2>
<ul>
<li><b>Samples analyzed:</b> {duration}</li>
<li><b>Analysis timestamp:</b> {analysis_time}</li>
<li><b>Data source:</b> {source}</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------- SECTION 2: HOW ANALYSIS WORKS ----------------
st.markdown("""
<div class='section'>
<h2>2. How CellGuardAI Analyzed the Battery</h2>
<p>
CellGuardAI examined battery behavior over time instead of relying on instant thresholds.
It focused on how internal stresses accumulate and interact.
</p>
<ul>
<li>Tracked <b>cell voltage imbalance growth</b> rather than absolute values</li>
<li>Observed <b>thermal stress accumulation</b> across operating cycles</li>
<li>Estimated <b>health degradation rate</b> from historical trends</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------- SECTION 3: KEY FINDINGS ----------------
cell_growth = df["cell_diff"].diff().mean()
temp_avg = df["temp_max"].mean()
health_drop = df["health_score"].iloc[0] - df["health_score"].iloc[-1]

st.markdown(f"""
<div class='section'>
<h2>3. Key Findings from Data</h2>
<ul>
<li>Average cell imbalance growth rate: <b>{cell_growth:.3f} mV/sample</b></li>
<li>Average maximum temperature observed: <b>{temp_avg:.1f} °C</b></li>
<li>Total health degradation over dataset: <b>{health_drop:.2f} points</b></li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------- SECTION 4: TIME-BASED ANALYSIS ----------------
st.markdown("""
<div class='section'>
<h2>4. Time-Based Behavioral Analysis</h2>
<p class='muted'>The following plots show how degradation forms gradually over time.</p>
</div>
""", unsafe_allow_html=True)

st.plotly_chart(
    px.line(df, y="health_score", title="Battery Health vs Time"),
    use_container_width=True
)

st.plotly_chart(
    px.line(df, y="cell_diff", title="Cell Voltage Imbalance vs Time"),
    use_container_width=True
)

st.plotly_chart(
    px.line(df, y="temp_max", title="Maximum Temperature vs Time"),
    use_container_width=True
)

# ---------------- SECTION 5: FUTURE PREDICTION ----------------
deg_rate = (100 - df["health_score"]).diff().rolling(10).mean().iloc[-1]
if pd.isna(deg_rate) or deg_rate <= 0:
    deg_rate = 0.15

health = latest["health_score"]
failure_window = max((health - 55) / deg_rate, 0)
low, high = failure_window * 0.8, failure_window * 1.3

st.markdown(f"""
<div class='section'>
<h2>5. Future Risk Prediction</h2>
<p>
If current operating behavior continues, CellGuardAI estimates that failure risk will
increase significantly within:
</p>
<h3>{int(low)} – {int(high)} cycles</h3>
<p class='muted'>
Prediction based on trend extrapolation (medium confidence)
</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SECTION 6: RECOMMENDED ACTIONS ----------------
actions = []
if failure_window < 50:
    actions.append("Immediately inspect the weakest cell and reduce load stress")
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
</div>
""", unsafe_allow_html=True)

# ---------------- SECTION 7: ASSUMPTIONS ----------------
st.markdown("""
<div class='section'>
<h2>7. Assumptions & Limitations</h2>
<ul>
<li>Trend-based predictive model (not electrochemical simulation)</li>
<li>Assumes future operating conditions remain similar</li>
<li>Intended for early warning and decision support</li>
<li>Conservative modeling aligned with IEC / SAE safety philosophy (illustrative)</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.caption(
    "CellGuardAI provides interpretable, future-oriented battery analysis to support proactive maintenance decisions."
)
