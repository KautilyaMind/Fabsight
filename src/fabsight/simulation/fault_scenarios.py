"""Human-readable simulation rule catalog."""
SCENARIO_RULES={
 "NORMAL_OPERATION":{"primary":[],"secondary":[],"purpose":"near-baseline reference"},
 "THERMAL_DRIFT":{"primary":["temperature slope","temperature maximum"],"secondary":["vibration","alarm rate"],"purpose":"gradual simulated drift"},
 "PRESSURE_INSTABILITY":{"primary":["pressure standard deviation","pressure range"],"secondary":["alarm rate"],"purpose":"unstable simulated pressure"},
 "RF_POWER_INSTABILITY":{"primary":["RF power standard deviation","RF slope"],"secondary":[],"purpose":"oscillation and drift"},
 "GAS_FLOW_DEVIATION":{"primary":["gas-flow mean","gas-flow slope"],"secondary":[],"purpose":"offset simulated flow"},
 "TOOL_DEGRADATION":{"primary":["vibration slope","tool age cycles","alarm rate"],"secondary":["vibration maximum"],"purpose":"gradual cross-run degradation"},
 "MULTI_FACTOR_ANOMALY":{"primary":["temperature slope","pressure variation"],"secondary":["vibration","alarm rate"],"purpose":"overlapping simulated faults"},
}
