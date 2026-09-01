"""Reproducible normalized telemetry-run and reading generation."""
from __future__ import annotations
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from fabsight.config import DEFAULT_TELEMETRY_RUNS,RANDOM_SEED,TELEMETRY_DATA_DIR,TELEMETRY_READINGS_PER_RUN
from fabsight.simulation.signal_models import simulate_signals
from fabsight.simulation.telemetry_schema import BASELINE,SCENARIOS,SEVERITIES,SIMULATION_NOTICE

def generate_telemetry(run_count:int=DEFAULT_TELEMETRY_RUNS,readings_per_run:int=TELEMETRY_READINGS_PER_RUN,seed:int=RANDOM_SEED)->tuple[pd.DataFrame,pd.DataFrame]:
    if run_count<7 or readings_per_run<3: raise ValueError("Generate at least 7 runs and 3 readings per run.")
    rng=np.random.default_rng(seed); runs=[]; readings=[]
    scenario_values=np.resize(np.array(SCENARIOS,dtype=object),run_count); rng.shuffle(scenario_values)
    for i,scenario in enumerate(scenario_values,1):
        severity="LOW" if scenario=="NORMAL_OPERATION" else str(rng.choice(SEVERITIES,p=[.3,.45,.25]))
        run_id=f"RUN-{i:05d}"; tool_index=(i-1)%12+1; tool_age=int(rng.integers(30,500) if scenario!="TOOL_DEGRADATION" else rng.integers(900,2200))
        alarm=float(np.clip(rng.normal(.03,.015),0,1))
        strength={"LOW":.65,"MODERATE":1,"HIGH":1.4}[severity]
        if scenario in {"THERMAL_DRIFT","PRESSURE_INSTABILITY","RF_POWER_INSTABILITY","GAS_FLOW_DEVIATION"}: alarm+=.05*strength
        if scenario=="TOOL_DEGRADATION": alarm+=.15*strength
        if scenario=="MULTI_FACTOR_ANOMALY": alarm+=.22*strength
        duration=float(BASELINE.process_duration+rng.normal(0,3)+(.04*tool_age if scenario=="TOOL_DEGRADATION" else 0))
        signals=simulate_signals(str(scenario),severity,readings_per_run,rng,tool_age)
        runs.append({"run_id":run_id,"event_id":f"EVT-TEL-{i:05d}","wafer_id":f"WAF-TEL-{i:05d}","lot_id":f"LOT-TEL-{(i-1)//25+1:04d}","tool_id":f"TOOL-{tool_index:02d}","process_step":"SIMULATED_PROCESS","scenario":scenario,"severity":severity,"ground_truth_cause":scenario,"ground_truth_provenance":"SYNTHETIC_GROUND_TRUTH","source_type":"SYNTHETIC_TELEMETRY","process_duration":duration,"tool_age_cycles":tool_age,"alarm_rate":alarm,"simulation_notice":SIMULATION_NOTICE})
        start=datetime(2025,1,1)+timedelta(minutes=i*2)
        for j in range(readings_per_run):
            readings.append({"telemetry_id":f"TEL-{i:05d}-{j:03d}","run_id":run_id,"timestamp":(start+timedelta(seconds=j*5)).isoformat(),"elapsed_seconds":j*5,**{k:float(v[j]) for k,v in signals.items()}})
    return pd.DataFrame(runs),pd.DataFrame(readings)

def save_telemetry(runs:pd.DataFrame,readings:pd.DataFrame,output_dir:Path=TELEMETRY_DATA_DIR)->None:
    output_dir.mkdir(parents=True,exist_ok=True); runs.to_csv(output_dir/"telemetry_runs.csv",index=False); readings.to_csv(output_dir/"telemetry_readings.csv",index=False)
