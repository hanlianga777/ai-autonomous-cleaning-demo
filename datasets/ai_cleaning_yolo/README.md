# AI Cleaning Demo YOLO Dataset

This directory holds the reproducible configuration and annotation manifest for
the local **Demo-specific Custom YOLO** proof of concept. The original user
photos, staged image copies, review previews, labels and trained model weights
are intentionally Git-ignored. Cleaned-after photographs remain in local
`holdout/` for the required negative verification test; they never enter the
training or validation folders.

Prepare the local dataset from the supplied ZIP, then run:

```bash
python3 tools/custom_yolo_demo.py prepare
python3 tools/custom_yolo_demo.py verify
python3 tools/custom_yolo_demo.py train
python3 tools/custom_yolo_demo.py infer
```

The fixed label order is `liquid`, `can`, `leaf`, `large_object`,
`small_litter`. Do not reorder it. `leaf` currently has no valid supplied
positive image and is intentionally recorded as LOW DATA rather than being
invented from background foliage.
