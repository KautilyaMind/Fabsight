# SECOM process data in FabSight v0.2

## What SECOM is

SECOM is a public dataset from the UCI Machine Learning Repository. It contains
anonymized measurements collected from a semiconductor manufacturing process and a
pass/fail outcome for each observation. FabSight uses it under its CC BY 4.0 license
for educational data preparation. The dataset was contributed by Michael McCann and
Adrian Johnston in 2008 (DOI: `10.24432/C54305`).

## What one row represents

```text
one manufacturing observation
        ↓
hundreds of anonymous process measurements
        ↓
PASS / FAIL result
```

The original target uses `-1` for pass and `1` for fail. FabSight converts these to
the readable labels `PASS` and `FAIL` while preserving each supplied timestamp.

## What the features represent

The columns contain numerical process measurements, but their physical identities
are anonymous. Names such as `feature_000` describe only column position. They must
not be interpreted as temperature, pressure, a particular sensor, or a particular
process step.

## Why FabSight uses SECOM

SECOM provides practice with high-dimensional manufacturing data, missing values,
class imbalance, and leakage-safe preparation. Later, separately scoped versions
may use the prepared data to study process patterns, failure prediction, or anomaly
analysis. Version v0.2 trains no predictive model.

## What SECOM cannot tell us

SECOM cannot directly identify:

- which variable measures temperature or pressure;
- which physical sensor or tool produced a measurement;
- which wafer image belongs to an observation;
- which exact mechanism caused a failure.

These limitations prevent physical root-cause claims from the anonymous columns.

## Preprocessing decisions

FabSight makes an 80/20 stratified split with random seed 42. It then uses only the
training partition to identify all-missing and constant columns, learn median values,
and learn scaling parameters. Those fitted transformations are applied unchanged to
the test partition, preventing test information from leaking into preprocessing.

## Relationship to v0.1

v0.1 models fictional tools, lots, wafers, steps, events, maintenance, and alarms.
v0.2 prepares a separate real public table of anonymous process measurements. There
is no fabricated mapping between a SECOM observation and a synthetic v0.1 wafer.
