
import numpy as np
import pandas as pd

def live_bms_stream():
    row = {
        "Pack Vol": 48 + np.random.normal(0,0.05),
        "Curent": 5 + np.random.normal(0,0.3),
        "Soc": np.random.uniform(40,90),
        "Rem. Ah": np.random.uniform(30000,45000),
        "Full Cap": 54000,
        "Cycle": np.random.randint(1,300),
    }
    for i in range(1,25):
        row[f"Cell{i}"] = 3500 + np.random.normal(0,6)
    for i in range(1,5):
        row[f"Temp{i}"] = 30 + np.random.normal(0,1.2)
    return pd.DataFrame([row])
