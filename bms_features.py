
import pandas as pd
import numpy as np

def sanitize_bms_csv(df):
    df = df.copy()

    # Robust timestamp handling
    if "Date" in df.columns and "Time" in df.columns:
        ts = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            errors="coerce"
        )
        if ts.notna().sum() > 0:
            df["timestamp"] = ts
        else:
            df["timestamp"] = pd.date_range("2025-01-01", periods=len(df), freq="S")
    else:
        df["timestamp"] = pd.date_range("2025-01-01", periods=len(df), freq="S")

    # SOC cleanup
    if "Soc" in df.columns:
        df["Soc"] = (
            df["Soc"]
            .astype(str)
            .str.replace("%", "", regex=False)
        )
        df["Soc"] = pd.to_numeric(df["Soc"], errors="coerce")

    # Force numeric for others
    for c in df.columns:
        if c not in ["Date", "Time", "timestamp"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.ffill().bfill()
    return df


def engineer_features(df):
    df = df.copy()

    # Safe dt computation (works even if timestamp is not datetime)
    if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        dt = df["timestamp"].diff().dt.total_seconds()
    else:
        dt = pd.Series(1.0, index=df.index)

    df["dt"] = dt.fillna(1).clip(lower=1)

    # Power & Energy
    df["power"] = df["Pack Vol"] * df["Curent"]
    df["energy_Wh"] = (df["power"] * df["dt"]) / 3600
    df["energy_throughput"] = df["energy_Wh"].abs().cumsum()

    # Cell features
    cell_cols = [c for c in df.columns if c.startswith("Cell")]
    df["cell_min"] = df[cell_cols].min(axis=1)
    df["cell_max"] = df[cell_cols].max(axis=1)
    df["cell_diff"] = df["cell_max"] - df["cell_min"]
    df["cell_std"] = df[cell_cols].std(axis=1)
    df["weakest_cell"] = df[cell_cols].idxmin(axis=1)

    # Thermal
    temp_cols = [c for c in df.columns if c.startswith("Temp")]
    df["temp_mean"] = df[temp_cols].mean(axis=1)
    df["temp_max"] = df[temp_cols].max(axis=1)
    df["temp_diff"] = df["temp_max"] - df[temp_cols].min(axis=1)

    # Capacity proxy
    if "Rem. Ah" in df.columns and "Full Cap" in df.columns:
        df["capacity_ratio"] = df["Rem. Ah"] / df["Full Cap"]
    else:
        df["capacity_ratio"] = 1.0

    # Health score
    df["health_score"] = (
        100
        - 35 * (df["cell_diff"] / df["cell_diff"].max())
        - 35 * (df["temp_diff"] / df["temp_diff"].max())
        - 30 * (1 - df["capacity_ratio"])
    ).clip(0, 100)

    # RUL proxy
    degradation = (100 - df["health_score"]).rolling(10).mean().diff()
    rate = degradation.replace(0, np.nan).mean()
    if pd.notna(rate) and rate > 0:
        df["rul_estimate"] = (df["health_score"] - 60) / rate
    else:
        df["rul_estimate"] = np.nan

    return df
