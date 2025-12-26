
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from bms_features import sanitize_bms_csv, engineer_features
from live_simulator import live_bms_stream

# ================= CONFIG =================
st.set_page_config(
    page_title="CellGuardAI | Predictive Battery Safety Platform",
    layout="wide"
)

# ================= THEME =================
st.markdown("""
<style>
body { background-color:#0e1117; color:#e6e6e6; }
h1,h2,h3 { color:#eaeaea; }
.block-container { padding-top:1.5rem; }
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<h1>🛡 CellGuardAI</h1>
<p style='color:#9aa0a6;font-size:15px'>
Predictive battery safety intelligence — detects how failure is forming before protection systems react
</p>
""", unsafe_allow_html=True)

# ================= NAV =================
view = st.radio("Mode", ["Fleet Command Center", "Single Battery Analysis"], horizontal=True)

# ================= SCENARIOS =================
SCENARIOS = {
    "Industry Baseline (Conservative)": {"charge":1.0,"thermal":1.0},
    "Aggressive Fast Charging": {"charge":1.4,"thermal":1.1},
    "High Ambient Temperature": {"charge":1.1,"thermal":1.5},
    "Conservative Operation": {"charge":0.8,"thermal":0.8},
}
scenario = st.selectbox("Operating Scenario", list(SCENARIOS.keys()))

# ================= HELPERS =================
def maintenance_action(fw,temp,imb):
    if fw < 50:
        return "IMMEDIATE INSPECTION REQUIRED"
    if temp > 55 or imb > 100:
        return "SCHEDULE MAINTENANCE"
    if fw < 150:
        return "PREVENTIVE ACTION ADVISED"
    return "NO ACTION REQUIRED"

def confidence_level(df):
    slope = df["health_score"].diff().rolling(5).std().iloc[-1]
    if slope < 0.05: return "HIGH"
    if slope < 0.15: return "MEDIUM"
    return "LOW"

def alert_log(df):
    events=[]
    for i in range(len(df)):
        if df.iloc[i]["health_score"]<60:
            events.append(("Health below safe margin",i))
        if df.iloc[i]["temp_max"]>60:
            events.append(("Thermal stress event",i))
        if df.iloc[i]["cell_diff"]>120:
            events.append(("Severe cell imbalance",i))
    return events

# ================= FLEET SIM =================
def simulate_fleet(n=8):
    rows=[]
    for i in range(n):
        df = engineer_features(sanitize_bms_csv(live_bms_stream()))
        latest=df.iloc[-1]
        health=latest["health_score"]
        deg=max((100-df["health_score"]).diff().rolling(5).mean().iloc[-1],0.2)
        m=SCENARIOS[scenario]
        deg*=m["charge"]*m["thermal"]
        fw=max((health-55)/deg,0)
        rows.append({
            "Battery ID":f"BAT-{i+1:02d}",
            "Health":round(health,1),
            "Failure Window (cycles)":int(fw),
            "Risk":"HIGH" if fw<50 else "MEDIUM" if fw<150 else "LOW",
            "Recommended Action":maintenance_action(fw,latest["temp_max"],latest["cell_diff"])
        })
    return pd.DataFrame(rows)

# ================= FLEET VIEW =================
if view=="Fleet Command Center":
    st.markdown("## Fleet Risk Ranking & Maintenance Priority")
    fleet=simulate_fleet().sort_values("Failure Window (cycles)")
    st.dataframe(fleet,use_container_width=True)

    st.plotly_chart(
        px.histogram(fleet,x="Failure Window (cycles)",color="Risk",
                     title="Fleet Failure Risk Distribution"),
        use_container_width=True
    )

    st.download_button(
        "⬇ Export Fleet Report",
        fleet.to_csv(index=False),
        file_name="fleet_report.csv"
    )

# ================= SINGLE BATTERY =================
else:
    df = engineer_features(sanitize_bms_csv(live_bms_stream()))
    latest=df.iloc[-1]

    health=latest["health_score"]
    deg=max((100-df["health_score"]).diff().rolling(10).mean().iloc[-1],0.15)
    m=SCENARIOS[scenario]
    deg*=m["charge"]*m["thermal"]
    fw=max((health-55)/deg,0)
    low,high=fw*0.75,fw*1.3

    st.markdown("## SYSTEM STATUS")
    if fw<50: st.error("DEGRADATION FORMING — HIGH RISK")
    elif fw<150: st.warning("DEGRADATION DETECTED — MONITOR")
    else: st.success("SYSTEM STABLE")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Health",f"{health:.1f}/100")
    c2.metric("Failure Window",f"{fw:.0f} cycles")
    c3.metric("Confidence",confidence_level(df))
    c4.metric("Confidence Range",f"{low:.0f}–{high:.0f}")

    st.markdown("### Maintenance Recommendation")
    st.info(maintenance_action(fw,latest["temp_max"],latest["cell_diff"]))

    st.markdown("### Alert Timeline")
    alerts=alert_log(df)
    if alerts:
        st.dataframe(pd.DataFrame(alerts,columns=["Event","Index"]))
    else:
        st.success("No critical alerts detected")

    st.markdown("### Failure Formation Trends")
    st.plotly_chart(px.line(df,y="health_score",title="Health Trajectory"),use_container_width=True)
    st.plotly_chart(px.line(df,y="cell_diff",title="Cell Imbalance Growth"),use_container_width=True)
    st.plotly_chart(px.line(df,y="temp_max",title="Thermal Stress Trend"),use_container_width=True)

    with st.expander("Standards & Assumptions"):
        st.write("""
        • Conservative risk modeling aligned with IEC/SAE safety philosophy (illustrative)  
        • Trend-based prediction, not electrochemical simulation  
        • Advisory system — final decisions remain with human engineers
        """)

    st.download_button(
        "⬇ Export Battery Report",
        pd.DataFrame({
            "Metric":["Health","Failure Window","Confidence"],
            "Value":[health,fw,confidence_level(df)]
        }).to_csv(index=False),
        file_name="battery_report.csv"
    )

st.caption(
    "CellGuardAI is a predictive safety-intelligence layer that augments traditional BMS. "
    "Designed for fleet-scale decision making."
)
