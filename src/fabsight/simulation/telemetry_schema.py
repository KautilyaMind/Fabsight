"""Schema constants for arbitrary-scale educational telemetry."""
from dataclasses import dataclass,asdict

SCENARIOS=("NORMAL_OPERATION","THERMAL_DRIFT","PRESSURE_INSTABILITY","RF_POWER_INSTABILITY","GAS_FLOW_DEVIATION","TOOL_DEGRADATION","MULTI_FACTOR_ANOMALY")
SEVERITIES=("LOW","MODERATE","HIGH")
SIGNALS=("chamber_temperature","chamber_pressure","rf_power","gas_flow","vibration")
FEATURE_INPUT_COLUMNS=SIGNALS+("process_duration","tool_age_cycles","alarm_rate")

@dataclass(frozen=True)
class TelemetryBaseline:
    chamber_temperature:float=60.0
    chamber_pressure:float=40.0
    rf_power:float=800.0
    gas_flow:float=50.0
    vibration:float=.10
    process_duration:float=60.0

BASELINE=TelemetryBaseline()
BASELINE_NOISE={"chamber_temperature":.6,"chamber_pressure":.35,"rf_power":4.0,"gas_flow":.5,"vibration":.008}
SIMULATION_NOTICE="Synthetic educational relationships on arbitrary simulation scales; not production process specifications or control limits."
