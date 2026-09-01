# FabSight v0.3 process-quality model

FabSight v0.3 is an educational demonstration. It uses the public SECOM dataset and
contains no proprietary manufacturing data. Its results are not suitable for
production process control.

## What problem are we solving?

```text
anonymous SECOM measurements
            ↓
v0.2 train-only preprocessing
            ↓
process-quality model
            ↓
PASS / FAIL and FAIL probability
```

The goal is to estimate how likely one manufacturing observation is to carry the
SECOM `FAIL` label. Hundreds of variables make manual inspection of every statistical
relationship difficult, so two deliberately simple machine-learning baselines are
used.

## Why Logistic Regression?

Logistic Regression is fast and provides a clear linear baseline. Positive
coefficients are associated within the model with increased predicted FAIL
probability; negative coefficients are associated with decreased probability. A
coefficient does not prove that a variable physically caused an outcome.

## Why Random Forest?

Random Forest combines decision trees and can represent nonlinear relationships. Its
feature importance indicates which anonymous variables the fitted model relied on
more heavily. Importance neither reveals a variable's sensor identity nor proves a
physical root cause.

## Class imbalance and evaluation

FAIL examples are rare, so both models use `class_weight="balanced"`. Accuracy is
not the primary selection metric: predicting almost everything as PASS could look
accurate while missing failures. FabSight reports accuracy for context, but focuses
on FAIL precision, recall, F1, ROC-AUC, and the confusion matrix.

- True positive: an actual FAIL correctly predicted as FAIL.
- False negative: an actual FAIL predicted as PASS. This misses a potential issue.
- False positive: an actual PASS predicted as FAIL. This creates an unnecessary
  investigation in the conceptual example.

The preferred model is selected using a validation subset taken only from v0.2's
training partition. Selection prioritizes FAIL recall, then FAIL F1 and ROC-AUC.
After selection, both model designs are refitted on all training rows. The v0.2 test
partition remains untouched until the separate evaluation command.

## Threshold and risk interpretation

The default classification threshold is 0.50. Reports also show FAIL precision and
recall at thresholds 0.30 through 0.70. Lower thresholds usually catch more failures
but create more false alarms; higher thresholds may reduce false alarms but miss more
failures. No production threshold is optimized in v0.3.

Risk labels are a configurable application demonstration:

- below 0.30: `LOW`
- 0.30 through 0.70: `MODERATE`
- above 0.70: `HIGH`

They are not semiconductor process-control limits.

## Scientific limitations

SECOM features are anonymous. Names such as `feature_103` describe column positions,
not known sensors or physical quantities. Predictions identify statistical patterns,
not physical mechanisms or root causes. v0.3 does not connect SECOM observations to
the synthetic lots, wafers, or tools from v0.1.
