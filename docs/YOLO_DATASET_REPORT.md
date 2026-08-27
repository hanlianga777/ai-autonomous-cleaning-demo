# Custom YOLO Dataset Report

## Scope

This is a **Demo-specific Custom YOLO / scenario PoC**. It was trained only from the user's supplied `AI Cleaning demo 照片.zip` assets. It does not use a public waste dataset, downloaded training photos, or generated waste imagery. It is not production-ready and must not replace the Phase 8R perception path until separately accepted and verified.

## Source audit

- Raw images: 9 PNGs, across four native demo scenes; every image is 1448×1086.
- Scene counts: Demo 1 = 2, Demo 2 = 4, Demo 3 = 2, Demo 4 = 1.
- Before / after / multi-view-before: 6 / 3 / 3.
- Exact duplicates inside the supplied ZIP: none.

| Business class | Fixed id | Native positive images | Native instances | Data status |
| --- | ---: | ---: | ---: | --- |
| `liquid` | 0 | 3 | 3 | LOW DATA |
| `can` | 1 | 1 | 1 | LOW DATA |
| `leaf` | 2 | 0 | 0 | NO POSITIVE DATA |
| `large_object` | 3 | 1 | 2 | LOW DATA |
| `small_litter` | 4 | 1 | 1 | LOW DATA |

`leaf` is intentionally unlabelled: the outdoor image contains background foliage, not a ground-leaf cleaning target. Inventing a label would make the dataset less trustworthy.

## Annotation and review

- Vision-assisted bounding-box prelabels were checked against supplied native images. Reproducible boxes are in `datasets/ai_cleaning_yolo/annotations.json`.
- Format: standard Ultralytics YOLO detection labels (`class_id x_center y_center width height`, normalized to 0–1).
- Local Chinese-labelled review previews are in `datasets/ai_cleaning_review/`; user images and previews are not committed.
- Demo 4 has two independent `large_object` boxes.
- The three cleaned-after images are holdout negative samples, never positive labels.

## Split and augmentation

- Train: 5 native before images (Demo 1, two Demo 2 views, Demo 3, Demo 4).
- Validation: 1 native Demo 2 before image from another camera.
- Holdout: 3 cleaned-after images for negative verification only.
- Augmentation stays within the source split: HSV brightness/contrast ±10%, rotation up to 3°, scale 5%, translation 2%. Mosaic, mixup, flips and generative synthesis are disabled.

The different Demo 2 camera images depict one incident, so even this native-image split is correlated. The one-image validation metric is not a generalization claim.

## Training run

| Item | Result |
| --- | --- |
| Base model | Ultralytics `yolo11n.pt` (nano) |
| Requested epochs | 60 |
| Actual outcome | early stopped after 59 epochs; best epoch 39 |
| Device | CPU fallback on MacBook Air M1 |
| Time | 150.85 seconds (includes MPS attempt) |
| MPS result | attempted first; Ultralytics 8.4.120 / PyTorch 2.13 MPS failed with `zeros: Dimension size must be non-negative` |
| Best validation | liquid-only: mAP50 0.995, mAP50-95 0.398, precision 0.0143, recall 1.0 |

The fallback is built into `tools/custom_yolo_demo.py`; no CUDA or dependency upgrade was installed. The validation set contains only one liquid instance, so mAP is reported only for traceability.

Local, Git-ignored outputs:

```text
models/ai_cleaning_custom_yolo/best.pt
models/ai_cleaning_custom_yolo/last.pt
models/ai_cleaning_custom_yolo/data.yaml
models/ai_cleaning_custom_yolo/training_summary.json
```

## Per-image inference at confidence ≥ 0.25

| Native image | Ground truth | Prediction | Result |
| --- | --- | --- | --- |
| Demo 1 before | `small_litter` | none | miss |
| Demo 2 view 1 before | `liquid` | none | miss |
| Demo 2 view 2 before | `liquid` | none | miss |
| Demo 2 view 3 before | `liquid` | none | miss |
| Demo 3 before | `can` | none | miss |
| Demo 4 before | two `large_object` | two `large_object` (0.9395, 0.7867) | correct |
| `leaf` | no supplied positive image | not evaluable | no claim |

At very low thresholds the model produces more candidate boxes but also false positives, including on cleaned-after images. Lowering the operational threshold is not an acceptable workaround.

## Before / after negative test

| Pair | Expected after result | Actual at ≥ 0.25 | Result |
| --- | --- | --- | --- |
| Demo 1 paper / `small_litter` | no `small_litter` | no detection | pass, but before was missed |
| Demo 2 beverage / `liquid` | no `liquid` | no detection | pass, but all before views were missed |
| Demo 3 can / `can` | no `can` | no detection | pass, but before was missed |

These negative passes do not prove a usable verification model because the corresponding positive before detections failed.

## Failure cases and limits

1. Only `large_object` is detected reliably at the standard 0.25 threshold.
2. `liquid`, `can`, and `small_litter` are missed; `leaf` has no training or validation evidence.
3. There are only eight positive native instances and no independent scene-level validation set.
4. The images are fixed-camera generated demo scenes; geometry, lighting and target scale are too narrow for production generalization.
5. This run does **not** validate Phase 8R REAL YOLO + Qwen-VL end-to-end and is intentionally not wired into the running product.

## Reproducible commands

```bash
python3 tools/custom_yolo_demo.py audit
python3 tools/custom_yolo_demo.py prepare
python3 tools/custom_yolo_demo.py verify
python3 tools/custom_yolo_demo.py train
python3 tools/custom_yolo_demo.py infer
```
