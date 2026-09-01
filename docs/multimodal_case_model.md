# FabSight v0.5 multimodal case model

FabSight v0.5 adds a structured representation layer. It does not add a new model,
an agent, autonomous reasoning, or physical root-cause analysis.

## What changed?

Previously, process intelligence and wafer-map vision were separate. Now one
synthetic educational case can hold both outputs alongside synthetic fab and
equipment context:

```text
Synthetic fab context
        +
ProcessPredictor output
        +
WaferPredictor output
        +
synthetic maintenance and alarms
        ↓
ManufacturingCase
```

## Are the public datasets truly linked?

No. The SECOM process observations and WM-811K wafer maps originate independently.
FabSight creates a synthetic integration relationship solely to demonstrate
multimodal software architecture. A case must never be interpreted as evidence that
one original public record belongs to another or that one evidence stream caused the
other.

## Why integrate them?

Industrial AI software often needs a common object for process measurements,
inspection results, equipment history, maintenance, and alarms. A strongly structured
case provides that common interface while preserving origin labels and scientific
limitations.

## Case schema

`ManufacturingCase` contains:

- `fab_context`: synthetic wafer, lot, tool, process step, event, and timestamp;
- `process_evidence`: public sample identifier plus ProcessPredictor output;
- `vision_evidence`: public sample identifier plus WaferPredictor output;
- `equipment_context`: synthetic tool status and recent maintenance/alarms;
- `evidence_status`: descriptive `CONSISTENT` or `MIXED` agreement;
- `provenance`: mandatory source labels for every evidence section;
- `integration_metadata`: strategy, version, seed, timestamp, and linkage notice.

Provenance values use `PUBLIC_DATASET`, `SYNTHETIC`, `MODEL_OUTPUT`, and `DERIVED`.
`dataset_linkage` is always `SYNTHETIC`.

## Pairing strategy

`risk_pattern_consistency_v1` targets 70% coherent cases and 30% mixed cases. The
rate is configurable and selection uses a seeded random generator.

- LOW process risk plus `NONE`: `CONSISTENT`
- MODERATE/HIGH risk plus a visible pattern: `CONSISTENT`
- LOW risk plus a visible pattern: `MIXED`
- MODERATE/HIGH risk plus `NONE`: `MIXED`

This pairing is not a measured correlation. Mixed cases are deliberately retained so
future software can represent disagreement and uncertainty. v0.5 does not resolve
that disagreement.

## Equipment context

Maintenance and alarms are retrieved from the v0.1 synthetic tool history relative
to the selected synthetic process-event timestamp. They are context only. The case
does not assign blame, confirm a cause, or infer a physical mechanism.

## Architectural progression

```text
v0.1  synthetic factory structure
v0.2  public process-data preparation
v0.3  process-quality prediction
v0.4  wafer-map vision
v0.5  structured multimodal case integration
```

All public data, model outputs, and synthetic records retain their separate origins.
