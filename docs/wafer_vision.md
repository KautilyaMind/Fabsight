# FabSight v0.4 wafer vision

FabSight v0.4 is a standalone educational computer-vision demonstration using the
public [WM-811K Wafer Map dataset](https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map).
It contains no proprietary manufacturing data and is not suitable for production
quality-control decisions.

## What is a wafer?

A wafer is a thin circular silicon substrate on which many semiconductor devices are
manufactured. The wafer surface is divided into many small device locations called
dies.

## What is a wafer map?

A wafer map is not an ordinary photograph. It is a grid representing spatial
die-level inspection or test states across a wafer.

```text
       wafer

      O O O
    O O X O O
   O X X X O O
   O O X O O O
    O O O O
      O O

X = defective or abnormal die location
```

A defect pattern is a recurring spatial arrangement of abnormal dies. Recognizing a
pattern can provide useful evidence for a later engineering investigation, but the
pattern does not prove any particular physical cause.

## Dataset labels

FabSight uses only actual labeled, structurally valid maps for supervised learning.
Unlabeled and malformed records are counted and excluded. Source labels are
normalized as follows:

| Source label | FabSight label |
|---|---|
| Center | `CENTER` |
| Donut | `DONUT` |
| Edge-Loc | `EDGE_LOCAL` |
| Edge-Ring | `EDGE_RING` |
| Loc | `LOCAL` |
| Random | `RANDOM` |
| Scratch | `SCRATCH` |
| Near-full | `NEAR_FULL` |
| None | `NONE` |

Classes are included only when they actually occur in the loaded dataset. The common
WM-811K release is extremely imbalanced and mostly unlabeled. FabSight reports the
complete source distribution, then caps the default educational subset at 2,000
maps per class so `NONE` cannot dominate a small CPU training run. Rare classes are
not oversampled.

## Preprocessing

Native maps have varying dimensions and discrete values: background, normal die, and
defective die. Maps are resized to 32×32 using nearest-neighbor interpolation so no
new fractional die states are invented. Values are divided by 2 during tensor
loading, producing a numerical range from 0 to 1.

The split is reproducible and stratified: 70% training, 15% validation, and 15% final
test. Validation macro F1 chooses the best training epoch. The test split is reserved
for final evaluation. Training uses class-weighted cross-entropy. No rotations,
flips, or other augmentation are used because spatial orientation may carry meaning.

## How the CNN works

```text
Wafer map
    ↓
small visual patterns detected
    ↓
larger spatial structures detected
    ↓
defect-class probabilities
```

A convolution is a small learned filter moving across the wafer map looking for
useful local patterns. FabSight uses two convolution blocks followed by a small dense
classifier and softmax probabilities. This is intentionally compact rather than a
large production architecture.

## Confidence

The predictor reports its highest softmax probability and demonstration bands:

- below 0.60: `LOW`
- 0.60 through 0.80: `MODERATE`
- above 0.80: `HIGH`

Confidence is not a calibrated production guarantee or a process-control limit.

## Architectural boundary and limitations

v0.3 produces a FAIL probability from anonymous SECOM variables. v0.4 independently
produces a spatial defect class from a wafer map. No wafer map is linked to a SECOM
row or synthetic wafer. Visual classification does not identify a physical root
cause. Dataset labels and distributions may not represent every production fab.
