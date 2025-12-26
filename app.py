
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="CellGuardAI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
body { background-color:#0e1117; color:#f1f3f4; }
h1 { font-size:48px; }
.hero { padding:60px 20px; text-align:center; }
.hero-risk { font-size:22px; color:#ffb74d; }
.hero-cycles { font-size:36px; font-weight:600; margin:20px 0; }
.hero-cause { font-size:18px; color:#9aa0a6; }
.section { max-width:1100px; margin:auto; padding:60px 20px; }
.caption { color:#9aa0a6; font-size:14px; }
.check { font-size:20px; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ---- Mock Data ----
np.random.seed(42)
time = pd.date_range(end=datetime.now(), periods=200)
health = np.linspace(95, 78, 200) + np.random.normal(0, 0.3, 200)
imbalance = np.linspace(20, 110, 200) + np.random.normal(0, 5, 200)

df = pd.DataFrame({
    "time": time,
    "health": health,
    "imbalance": imbalance
})

deg_rate = abs(np.gradient(df["health"]).mean())
failure_cycles = int((df["health"].iloc[-1] - 60) / deg_rate)

# ---- HERO ----
st.markdown(f"""
<div class="hero">
    <div class="hero-risk">⚠️ Battery degradation is forming</div>
    <div class="hero-cycles">Critical risk in ~{failure_cycles} cycles</div>
    <div class="hero-cause">Primary cause: Internal cell imbalance under thermal stress</div>
</div>
""", unsafe_allow_html=True)

# ---- STORY ----
st.markdown("""
<div class="section">
<h2>What’s happening</h2>
<p>
Over recent operation, this battery has begun aging faster than expected.
Although no safety limits have been crossed yet, internal imbalance and repeated
heat exposure are quietly accelerating degradation.
</p>
</div>
""", unsafe_allow_html=True)

# ---- EVIDENCE ----
st.markdown("""
<div class="section">
<h2>Evidence from data</h2>
<p class="caption">These trends reveal degradation before alarms trigger.</p>
</div>
""", unsafe_allow_html=True)

st.plotly_chart(px.line(df, x="time", y="health", title="Battery health declining over time"), use_container_width=True)
st.plotly_chart(px.line(df, x="time", y="imbalance", title="Cell imbalance increasing internally"), use_container_width=True)

# ---- FUTURE ----
st.markdown(f"""
<div class="section">
<h2>What happens next</h2>
<p><b>If nothing changes:</b> high-risk degradation within ~{failure_cycles} cycles</p>
<p><b>If recommended actions are applied:</b> risk delayed by ~40–60%</p>
</div>
""", unsafe_allow_html=True)

# ---- ACTIONS ----
st.markdown("""
<div class="section">
<h2>What to do next</h2>
<div class="check">✓ Reduce high-current charging</div>
<div class="check">✓ Inspect weakest cell</div>
<div class="check">✓ Improve cooling during peak load</div>
</div>
""", unsafe_allow_html=True)

with st.expander("How this analysis works"):
    st.write("""
    CellGuardAI analyzes time-based trends in battery health and internal imbalance
    instead of relying on fixed thresholds. Predictions are trend-based and intended
    for early warning and decision support.
    """)

st.caption(
    "CellGuardAI makes invisible battery degradation visible early, understandable instantly, and actionable immediately."
)
