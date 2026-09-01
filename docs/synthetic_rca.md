# FabSight v0.9 — Synthetic Named Telemetry and Explainable RCA

> The relationships in this named telemetry simulator are synthetic educational relationships created to demonstrate AI process-intelligence architecture. They are not claims about real semiconductor process physics, production recipes, or control limits.

## Why a separate telemetry system?

SECOM is real public semiconductor-origin data with anonymous variables. `feature_103` must remain anonymous and cannot become temperature, pressure, or another named measurement. It supports statistical FAIL-risk prediction, not physical interpretation.

FabSight v0.9 separately generates a controlled simulation with named variables. Because its rules are authored by this project, the synthetic ground truth can evaluate an RCA classifier. Simulation conclusions apply only inside this experiment.

```text
SECOM → ProcessPredictor → anonymous statistical risk
Synthetic telemetry → RCAPredictor → simulated named scenario
```

## Schema and arbitrary baselines

`telemetry_runs.csv` contains one row per run: IDs, scenario, severity, evaluation-only ground truth and provenance, process duration, tool age, and alarm rate. `telemetry_readings.csv` contains multiple timestamped readings per run: elapsed seconds, chamber temperature, chamber pressure, RF power, gas flow, and vibration.

All values use arbitrary educational simulation scales:

| Signal | Configured baseline |
|---|---:|
| chamber temperature | 60 |
| chamber pressure | 40 |
| RF power | 800 |
| gas flow | 50 |
| vibration | 0.10 |
| process duration | 60 |

These are not production specifications or operating limits.

## Scenario rules

| Scenario | Primary synthetic signals | Secondary signals | Purpose |
|---|---|---|---|
| NORMAL_OPERATION | Near-baseline noisy signals | — | Reference behavior |
| THERMAL_DRIFT | Temperature slope and maximum | Vibration, alarm rate | Gradual drift |
| PRESSURE_INSTABILITY | Pressure standard deviation and range | Alarm rate | Unstable pressure |
| RF_POWER_INSTABILITY | RF standard deviation and slope | — | Oscillation and drift |
| GAS_FLOW_DEVIATION | Gas-flow mean and slope | — | Offset flow |
| TOOL_DEGRADATION | Vibration slope, tool age, alarm rate | Vibration maximum | Cross-run degradation |
| MULTI_FACTOR_ANOMALY | Temperature slope and pressure variation | Vibration, alarm rate | Overlapping faults |

LOW, MODERATE, and HIGH severity scale the synthetic signal strength. Noise and overlapping ranges make classification non-trivial. Generation uses seed 42.

## Temporal features and model

Each run is summarized into 33 readable features: mean, standard deviation, minimum, maximum, range, and slope for five signals, plus process duration, tool age, and alarm rate. Slope measures whether a signal tends to rise or fall during an event; `60 → 61 → 63 → 66` has a positive slope.

Splitting is performed at the run level (70% train, 15% validation, 15% test), so readings from one run never cross partitions. `ground_truth_cause`, scenario, severity, provenance, and notices are excluded from model inputs.

The classifier is a class-balanced `RandomForestClassifier` with 220 trees. Global feature importance provides understandable contributors. Model probability is called model confidence, not scientific certainty. SHAP is not required.

## Ground-truth boundary

`ground_truth_cause` exists only in generation and evaluation data. Normal inference receives engineered telemetry, an RCA prediction, trend summaries, and provenance. Ground truth is rejected if it appears in agent telemetry evidence and is absent from agent state updates, prompts, RAG context, and reports.

The agent may say that `THERMAL_DRIFT` is the strongest scenario within the FabSight simulation. It must never generalize that conclusion into a real production-process diagnosis.

## Commands

```powershell
python scripts/generate_telemetry.py --runs 2000
python scripts/train_rca_model.py
python scripts/evaluate_rca_model.py
python scripts/inspect_telemetry_run.py --run RUN-00042
python scripts/diagnose_telemetry_run.py --run RUN-00042
```

Inspection writes separate trend plots for temperature, pressure, RF power, gas flow, and vibration under `reports/rca/trends/`. Generated data, models, and reports are ignored by Git.

## Agent integration

`ManufacturingCase.telemetry_evidence` is optional, preserving old cases. When present, the planner can route to `ANALYZE_TELEMETRY`. The evidence review and final report add synthetic telemetry findings and a simulated RCA result, while retaining process, vision, equipment, knowledge, and provenance evidence.

v0.9 remains automatic and single-run. It adds no checkpoint database, long-term memory, human interrupt, web application, deployment configuration, or real causal process model.
