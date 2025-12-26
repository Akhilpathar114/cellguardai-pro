
import streamlit as st
import pandas as pd
import plotly.express as px
from bms_features import sanitize_bms_csv, engineer_features
from live_simulator import live_bms_stream

st.set_page_config(page_title="CellGuardAI – Predictive Battery Guardian", layout="wide")

# ---------- HEADER ----------
st.markdown("""
<h1>🛡 CellGuardAI</h1>
<p style='font-size:16px;color:gray'>
AI system that predicts how battery failure is forming — before alarms trigger.
</p>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.header("Input")
mode = st.sidebar.radio("Data Source", ["Live BMS", "Upload CSV"])

st.sidebar.subheader("What-if Simulation")
charge_reduction = st.sidebar.slider("Reduce Charging Stress (%)", 0, 50, 0)
cooling_gain = st.sidebar.slider("Improve Cooling (%)", 0, 50, 0)

# ---------- DATA ----------
if mode == "Upload CSV":
    f = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if not f:
        st.stop()
    raw = pd.read_csv(f)
else:
    raw = live_bms_stream()

df = engineer_features(sanitize_bms_csv(raw))
latest = df.iloc[-1]

# ---------- FUTURE PREDICTION LOGIC ----------
health = latest["health_score"]

# Degradation rate proxy
deg_rate = max((100 - df["health_score"]).diff().rolling(10).mean().iloc[-1], 0.1)

# Apply what-if improvements
deg_rate *= (1 - charge_reduction/100)
deg_rate *= (1 - cooling_gain/100)

failure_window = max((health - 55) / deg_rate, 0)

# Cause attribution
cell_factor = min(latest["cell_diff"] / df["cell_diff"].max(), 1)
temp_factor = min(latest["temp_max"] / df["temp_max"].max(), 1)
cap_factor = 1 - latest.get("capacity_ratio", 1)

total = cell_factor + temp_factor + cap_factor + 1e-6
cell_pct = cell_factor / total * 100
temp_pct = temp_factor / total * 100
cap_pct = cap_factor / total * 100

# ---------- EXECUTIVE STATUS ----------
st.markdown("## System Status")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Health", f"{health:.1f}/100")
c2.metric("Risk Level", "HIGH" if health < 60 else "MEDIUM" if health < 80 else "LOW")
c3.metric("Failure Window", f"{failure_window:.0f} cycles")
c4.metric("Likely Failing Cell", latest["weakest_cell"])

# ---------- AI VERDICT ----------
st.markdown("## 🧠 CellGuardAI Prediction")

if failure_window < 50:
    st.error("Failure forming rapidly. Action required soon.")
elif failure_window < 150:
    st.warning("Failure forming gradually. Preventive action recommended.")
else:
    st.success("No immediate failure pattern detected.")

st.markdown(f"""
**Predicted behavior if usage continues unchanged:**  
• High-risk window in **~{failure_window:.0f} cycles**  
• Failure likely initiated by **{latest['weakest_cell']}**
""")

# ---------- CAUSE ATTRIBUTION ----------
st.markdown("## Why this future is predicted")

st.write("Relative contribution to future risk:")

st.plotly_chart(
    px.bar(
        x=["Cell Imbalance", "Thermal Stress", "Capacity Fade"],
        y=[cell_pct, temp_pct, cap_pct],
        labels={"x": "Cause", "y": "Contribution (%)"},
        title="Failure Cause Attribution"
    ),
    use_container_width=True
)

# ---------- KEY TRENDS ----------
st.markdown("## How failure is forming")

st.plotly_chart(px.line(df, y="health_score", title="Health Trajectory"), use_container_width=True)
st.plotly_chart(px.line(df, y="cell_diff", title="Cell Imbalance Growth"), use_container_width=True)
st.plotly_chart(px.line(df, y="temp_max", title="Thermal Stress Accumulation"), use_container_width=True)

# ---------- FOOTER ----------
st.caption(
    "CellGuardAI predicts battery futures using trend intelligence, not thresholds. "
    "It augments traditional BMS by revealing how risk evolves over time."
)
