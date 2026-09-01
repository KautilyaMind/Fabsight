"""Transparent noisy signal rules for each simulated fault scenario."""
from __future__ import annotations
import numpy as np
from fabsight.simulation.telemetry_schema import BASELINE,BASELINE_NOISE

STRENGTH={"LOW":.65,"MODERATE":1.0,"HIGH":1.4}
def simulate_signals(scenario:str,severity:str,n:int,rng:np.random.Generator,tool_age:int)->dict[str,np.ndarray]:
    t=np.linspace(0,1,n); s=STRENGTH[severity]
    values={name:getattr(BASELINE,name)+rng.normal(0,BASELINE_NOISE[name],n) for name in BASELINE_NOISE}
    if scenario in {"THERMAL_DRIFT","MULTI_FACTOR_ANOMALY"}:
        values["chamber_temperature"] += s*5.0*t; values["vibration"] += s*.015*t
    if scenario in {"PRESSURE_INSTABILITY","MULTI_FACTOR_ANOMALY"}:
        values["chamber_pressure"] += rng.normal(0,s*2.0,n)+s*1.2*np.sin(t*np.pi*5)
    if scenario=="RF_POWER_INSTABILITY": values["rf_power"] += s*25*np.sin(t*np.pi*6)+s*10*t
    if scenario=="GAS_FLOW_DEVIATION": values["gas_flow"] += s*(3.5+2.0*t)
    if scenario=="TOOL_DEGRADATION":
        age_factor=max(0,(tool_age-500)/1000); values["vibration"] += s*(.025+.05*age_factor)*t
    return values
