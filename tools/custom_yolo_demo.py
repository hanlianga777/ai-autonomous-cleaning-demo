#!/usr/bin/env python3
"""Prepare, train, and inspect the local demo-specific Custom YOLO PoC.

This utility intentionally works only with the user's local demo photos.  It
does not download a public waste dataset, generate synthetic waste imagery, or
change the running CleanOps product.  Generated source photos, review images,
and model weights are ignored by Git; the reproducible annotation manifest and
dataset configuration remain in the repository.

Usage:
  python3 tools/custom_yolo_demo.py audit
  python3 tools/custom_yolo_demo.py prepare
  python3 tools/custom_yolo_demo.py verify
  python3 tools/custom_yolo_demo.py train
  python3 tools/custom_yolo_demo.py infer
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "datasets" / "ai_cleaning_raw" / "AI Cleaning demo 照片"
DATASET_ROOT = ROOT / "datasets" / "ai_cleaning_yolo"
REVIEW_ROOT = ROOT / "datasets" / "ai_cleaning_review"
MODEL_ROOT = ROOT / "models" / "ai_cleaning_custom_yolo"
MANIFEST_PATH = DATASET_ROOT / "annotations.json"
DATA_YAML_PATH = DATASET_ROOT / "data.yaml"
MODEL_DATA_YAML_PATH = MODEL_ROOT / "data.yaml"
TRAINING_SUMMARY_PATH = MODEL_ROOT / "training_summary.json"
INFERENCE_REPORT_PATH = MODEL_ROOT / "demo_inference.json"

# Fixed business taxonomy. Do not reorder or add labels without an architecture decision.
CLASS_NAMES = ["liquid", "can", "leaf", "large_object", "small_litter"]
CHINESE_NAMES = {
    "liquid": "液体污渍",
    "can": "易拉罐",
    "leaf": "树叶",
    "large_object": "大件物品",
    "small_litter": "其他小型垃圾",
}
CLASS_ID = {name: index for index, name in enumerate(CLASS_NAMES)}
COLORS = {
    "liquid": "#d97706",
    "can": "#2563eb",
    "leaf": "#16a34a",
    "large_object": "#7c3aed",
    "small_litter": "#dc2626",
}

# Every box below was vision-assisted from the supplied native image, then
# reviewed against the source image. Coordinates are xyxy pixels at 1448x1086.
# The after images intentionally have no boxes: they are holdout negative
# verification samples and must not teach the model that a cleaned scene
# contains the object. This also avoids an MPS loss bug for all-background
# batches in the installed PyTorch/Ultralytics combination.
SAMPLES: list[dict[str, Any]] = [
    {
        "id": "demo1_before",
        "source": "demo1 室外地面纸巾/清洁前.png",
        "split": "train",
        "scene": "demo1_outdoor_tissue",
        "phase": "before",
        "boxes": [{"class": "small_litter", "xyxy": [716, 675, 775, 716]}],
        "review_status": "VERIFIED_PRELABEL",
    },
    {
        "id": "demo1_after",
        "source": "demo1 室外地面纸巾/清洁后.png",
        "split": "holdout",
        "scene": "demo1_outdoor_tissue",
        "phase": "after",
        "boxes": [],
        "review_status": "NEGATIVE_SAMPLE",
    },
    {
        "id": "demo2_view1_before",
        "source": "demo2 室内地面奶茶污渍/清洁前视角1.png",
        "split": "train",
        "scene": "demo2_beverage_spill_cam_a1_02",
        "phase": "before",
        "boxes": [{"class": "liquid", "xyxy": [684, 529, 802, 617]}],
        "review_status": "VERIFIED_PRELABEL",
    },
    {
        "id": "demo2_view2_before",
        "source": "demo2 室内地面奶茶污渍/清洁前视角2.png",
        "split": "train",
        "scene": "demo2_beverage_spill_cam_a1_01",
        "phase": "before",
        "boxes": [{"class": "liquid", "xyxy": [643, 544, 827, 641]}],
        "review_status": "VERIFIED_PRELABEL",
    },
    {
        "id": "demo2_view3_before",
        "source": "demo2 室内地面奶茶污渍/清洁前视角3.png",
        "split": "val",
        "scene": "demo2_beverage_spill_cam_a1_04",
        "phase": "before",
        "boxes": [{"class": "liquid", "xyxy": [630, 539, 817, 614]}],
        "review_status": "VERIFIED_PRELABEL",
    },
    {
        "id": "demo2_after",
        "source": "demo2 室内地面奶茶污渍/清洁后视角.png",
        "split": "holdout",
        "scene": "demo2_beverage_spill_after_cam_a1_02",
        "phase": "after",
        "boxes": [],
        "review_status": "NEGATIVE_SAMPLE",
    },
    {
        "id": "demo3_before",
        "source": "demo3 室内2楼易拉罐/清洁前.png",
        "split": "train",
        "scene": "demo3_indoor_can",
        "phase": "before",
        "boxes": [{"class": "can", "xyxy": [699, 695, 735, 721]}],
        "review_status": "VERIFIED_PRELABEL",
    },
    {
        "id": "demo3_after",
        "source": "demo3 室内2楼易拉罐/清洁后.png",
        "split": "holdout",
        "scene": "demo3_indoor_can",
        "phase": "after",
        "boxes": [],
        "review_status": "NEGATIVE_SAMPLE",
    },
    {
        "id": "demo4_before",
        "source": "demo4 室内走廊垃圾桶旁的纸箱/清洁前.png",
        "split": "train",
        "scene": "demo4_oversized_boxes",
        "phase": "before",
        "boxes": [
            {"class": "large_object", "xyxy": [505, 570, 627, 706]},
            {"class": "large_object", "xyxy": [604, 610, 723, 729]},
        ],
        "review_status": "VERIFIED_PRELABEL",
    },
]


def source_path(sample: dict[str, Any]) -> Path:
    return RAW_ROOT / str(sample["source"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (Path("/System/Library/Fonts/PingFang.ttc"), Path("/System/Library/Fonts/STHeiti Medium.ttc")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def yolo_line(class_name: str, xyxy: list[int], width: int, height: int) -> str:
    left, top, right, bottom = xyxy
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(f"Invalid bbox {xyxy} for image size {width}x{height}")
    x_center = ((left + right) / 2) / width
    y_center = ((top + bottom) / 2) / height
    box_width = (right - left) / width
    box_height = (bottom - top) / height
    return f"{CLASS_ID[class_name]} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def sample_inventory() -> dict[str, Any]:
    raw_images = sorted(path for path in RAW_ROOT.rglob("*") if path.suffix.lower() in {".png", ".jpg", ".jpeg"})
    dimensions = Counter()
    hashes: dict[str, list[str]] = {}
    for image_path in raw_images:
        with Image.open(image_path) as image:
            dimensions[f"{image.width}x{image.height}"] += 1
        hashes.setdefault(sha256(image_path), []).append(str(image_path.relative_to(ROOT)))

    by_scene = Counter(sample["scene"].split("_")[0] for sample in SAMPLES)
    usable_images = Counter()
    instance_count = Counter()
    before_count = after_count = multi_view_count = 0
    for sample in SAMPLES:
        if sample["phase"] == "before":
            before_count += 1
            if sample["scene"].startswith("demo2_"):
                multi_view_count += 1
        else:
            after_count += 1
        for box in sample["boxes"]:
            usable_images[box["class"]] += 1
            instance_count[box["class"]] += 1

    return {
        "raw_image_total": len(raw_images),
        "scenes": dict(sorted(by_scene.items())),
        "resolution_counts": dict(dimensions),
        "exact_duplicates_inside_zip": [paths for paths in hashes.values() if len(paths) > 1],
        "before_images": before_count,
        "after_images": after_count,
        "multiview_before_images": multi_view_count,
        "positive_image_count_by_class": {name: usable_images[name] for name in CLASS_NAMES},
        "instance_count_by_class": {name: instance_count[name] for name in CLASS_NAMES},
        "low_data_classes": [name for name in CLASS_NAMES if instance_count[name] < 5],
        "note": "leaf has no valid target instance in the supplied images; background foliage is intentionally not annotated.",
    }


def write_yaml(path: Path, root_value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = "\n".join(f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES))
    path.write_text(
        f"path: {root_value}\ntrain: images/train\nval: images/val\nnames:\n{names}\n",
        encoding="utf-8",
    )


def draw_review(sample: dict[str, Any], image_path: Path, output_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    label_font = safe_font(28)
    small_font = safe_font(20)
    for box in sample["boxes"]:
        class_name = str(box["class"])
        color = COLORS[class_name]
        left, top, right, bottom = box["xyxy"]
        draw.rectangle((left, top, right, bottom), outline=color, width=5)
        label = CHINESE_NAMES[class_name]
        label_bounds = draw.textbbox((0, 0), label, font=label_font)
        label_height = label_bounds[3] - label_bounds[1] + 10
        draw.rectangle((left, max(0, top - label_height), left + label_bounds[2] + 16, top), fill=color)
        draw.text((left + 8, max(0, top - label_height) + 3), label, fill="white", font=label_font)

    status = "负样本：清洁后无目标" if not sample["boxes"] else f"预标注已复核：{sample['review_status']}"
    draw.rectangle((12, image.height - 48, 520, image.height - 12), fill="black")
    draw.text((24, image.height - 44), status, fill="white", font=small_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def prepare() -> None:
    missing = [str(source_path(sample)) for sample in SAMPLES if not source_path(sample).exists()]
    if missing:
        raise FileNotFoundError("Missing supplied source photos:\n" + "\n".join(missing))

    for split in ("train", "val"):
        (DATASET_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
        cache_file = DATASET_ROOT / "labels" / f"{split}.cache"
        if cache_file.exists():
            cache_file.unlink()
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_samples: list[dict[str, Any]] = []
    for sample in SAMPLES:
        source = source_path(sample)
        split = str(sample["split"])
        if split == "holdout":
            destination_image = DATASET_ROOT / "holdout" / f"{sample['id']}.png"
            destination_image.parent.mkdir(parents=True, exist_ok=True)
            # Remove only an obsolete generated staging copy from an earlier run.
            for old_split in ("train", "val"):
                for obsolete in (
                    DATASET_ROOT / "images" / old_split / f"{sample['id']}.png",
                    DATASET_ROOT / "labels" / old_split / f"{sample['id']}.txt",
                ):
                    if obsolete.exists():
                        obsolete.unlink()
            destination_label = None
        else:
            destination_image = DATASET_ROOT / "images" / split / f"{sample['id']}.png"
            destination_label = DATASET_ROOT / "labels" / split / f"{sample['id']}.txt"
        shutil.copy2(source, destination_image)
        with Image.open(source) as image:
            label_lines = [yolo_line(str(box["class"]), list(box["xyxy"]), image.width, image.height) for box in sample["boxes"]]
            dimensions = {"width": image.width, "height": image.height}
        if destination_label:
            destination_label.write_text("\n".join(label_lines) + ("\n" if label_lines else ""), encoding="utf-8")
        draw_review(sample, source, REVIEW_ROOT / f"{sample['id']}_review.png")
        manifest_samples.append({**sample, "dimensions": dimensions, "source_sha256": sha256(source)})

    # Ultralytics resolves a relative `path` from the process working directory,
    # not from data.yaml. Keep it explicitly project-relative because this tool
    # is intentionally invoked from the repository root.
    write_yaml(DATA_YAML_PATH, "datasets/ai_cleaning_yolo")
    write_yaml(MODEL_DATA_YAML_PATH, "datasets/ai_cleaning_yolo")
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "purpose": "Demo-specific Custom YOLO PoC; never production training data.",
                "classes": [{"id": CLASS_ID[name], "name": name, "display_name_zh": CHINESE_NAMES[name]} for name in CLASS_NAMES],
                "annotation_method": "Vision-assisted bbox prelabels, manually checked against the supplied original image; after images are explicit negative samples.",
                "split_policy": "Native source-image split. Any Ultralytics augmentation stays within its source image split; no generated image is copied between train and val.",
                "samples": manifest_samples,
                "inventory": sample_inventory(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(sample_inventory(), ensure_ascii=False, indent=2))
    print(f"Prepared YOLO dataset at {DATASET_ROOT}")
    print(f"Wrote Chinese review previews to {REVIEW_ROOT}")


def verify() -> None:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError("Run prepare before verify.")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    split_scenes: dict[str, set[str]] = {"train": set(), "val": set()}
    label_total = Counter()
    for sample in manifest["samples"]:
        split = sample["split"]
        image_path = (DATASET_ROOT / "holdout" / f"{sample['id']}.png") if split == "holdout" else (DATASET_ROOT / "images" / split / f"{sample['id']}.png")
        label_path = DATASET_ROOT / "labels" / split / f"{sample['id']}.txt"
        review_path = REVIEW_ROOT / f"{sample['id']}_review.png"
        if not image_path.exists() or not review_path.exists() or (split != "holdout" and not label_path.exists()):
            failures.append(f"Missing generated asset for {sample['id']}")
            continue
        if split == "holdout":
            continue
        lines = [line for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != len(sample["boxes"]):
            failures.append(f"Label count mismatch for {sample['id']}")
        for line in lines:
            values = line.split()
            if len(values) != 5:
                failures.append(f"Invalid YOLO line in {label_path}: {line}")
                continue
            class_number, *coordinates = values
            if int(class_number) not in range(len(CLASS_NAMES)) or any(not 0 < float(value) <= 1 for value in coordinates):
                failures.append(f"Out-of-range YOLO line in {label_path}: {line}")
            label_total[CLASS_NAMES[int(class_number)]] += 1
        # The split unit is the individual native source photo, not an augmentation.
        # Keep this explicit so future generated variants cannot cross the boundary.
        split_scenes[split].add(sample["id"])

    if split_scenes["train"] & split_scenes["val"]:
        failures.append("An original source image appears in both train and val.")
    if failures:
        raise RuntimeError("Dataset verification failed:\n- " + "\n- ".join(failures))
    print("Dataset verification passed.")
    print("Instances:", json.dumps({name: label_total[name] for name in CLASS_NAMES}, ensure_ascii=False))
    print("LOW DATA:", ", ".join(name for name in CLASS_NAMES if label_total[name] < 5))


def preferred_device() -> str:
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


def train() -> None:
    verify()
    from ultralytics import YOLO

    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    def run_training(device: str):
        # The standard lightweight base weight may be fetched by Ultralytics if
        # not cached. It is model initialization only, never an extra training
        # image or waste dataset.
        model = YOLO("yolo11n.pt")
        return model.train(
            data=str(DATA_YAML_PATH),
            epochs=60,
            imgsz=640,
            batch=2,
            device=device,
            workers=0,
            seed=42,
            deterministic=True,
            patience=20,
            project=str(MODEL_ROOT / "runs"),
            name="custom_yolo",
            exist_ok=True,
            degrees=3.0,
            translate=0.02,
            scale=0.05,
            shear=0.0,
            perspective=0.0,
            flipud=0.0,
            fliplr=0.0,
            hsv_h=0.01,
            hsv_s=0.10,
            hsv_v=0.10,
            mosaic=0.0,
            mixup=0.0,
            erasing=0.0,
            plots=True,
            verbose=True,
        )

    device = preferred_device()
    attempted_devices = [device]
    fallback_reason: str | None = None
    # The standard lightweight base weight may be fetched by Ultralytics if not
    # cached. It is a model initialization weight, never an extra training image
    # or waste dataset.
    try:
        results = run_training(device)
    except RuntimeError as error:
        # The locally installed Ultralytics 8.4.120 / PyTorch 2.13 MPS pair
        # fails on the custom detection loss with an invalid `zeros` shape.
        # The requested behaviour is MPS first, then a safe CPU fallback.
        if device != "mps" or "Dimension size must be non-negative" not in str(error):
            raise
        fallback_reason = str(error)
        print("MPS training is incompatible with this local stack; retrying on CPU.")
        device = "cpu"
        attempted_devices.append(device)
        results = run_training(device)
    duration = round(time.monotonic() - started, 2)
    run_dir = Path(results.save_dir)
    weights_dir = run_dir / "weights"
    for name in ("best.pt", "last.pt"):
        source = weights_dir / name
        if source.exists():
            shutil.copy2(source, MODEL_ROOT / name)
    summary = {
        "schema_version": "1.0",
        "purpose": "Demo-specific / PoC only; no production-readiness claim.",
        "base_model": "yolo11n.pt",
        "device": device,
        "attempted_devices": attempted_devices,
        "fallback_reason": fallback_reason,
        "epochs_requested": 60,
        "training_time_seconds": duration,
        "dataset_yaml": str(DATA_YAML_PATH.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "best_weights": str((MODEL_ROOT / "best.pt").relative_to(ROOT)),
        "last_weights": str((MODEL_ROOT / "last.pt").relative_to(ROOT)),
        "augmentation": {"brightness_hsv_v": 0.10, "contrast_hsv_s": 0.10, "rotation_degrees": 3.0, "scale": 0.05, "translation": 0.02, "mosaic": 0.0, "mixup": 0.0},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    TRAINING_SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def infer() -> None:
    if not (MODEL_ROOT / "best.pt").exists():
        raise FileNotFoundError("No best.pt found. Run train first.")
    from ultralytics import YOLO

    model = YOLO(str(MODEL_ROOT / "best.pt"))
    report_samples: list[dict[str, Any]] = []
    for sample in SAMPLES:
        source = source_path(sample)
        result = model.predict(source=str(source), imgsz=640, conf=0.25, device=preferred_device(), verbose=False)[0]
        predictions: list[dict[str, Any]] = []
        for box in result.boxes:
            class_name = CLASS_NAMES[int(box.cls.item())]
            predictions.append(
                {
                    "class": class_name,
                    "confidence": round(float(box.conf.item()), 4),
                    "xyxy": [round(float(value), 1) for value in box.xyxy[0].tolist()],
                }
            )
        expected = [str(box["class"]) for box in sample["boxes"]]
        predicted_classes = [prediction["class"] for prediction in predictions]
        forbidden_by_after_sample = {
            "demo1_after": "small_litter",
            "demo2_after": "liquid",
            "demo3_after": "can",
        }
        forbidden = {forbidden_by_after_sample[sample["id"]]} if sample["id"] in forbidden_by_after_sample else set()
        after_pass = not (set(predicted_classes) & forbidden)
        report_samples.append(
            {
                "image": str(source.relative_to(ROOT)),
                "sample_id": sample["id"],
                "phase": sample["phase"],
                "ground_truth": expected,
                "predictions": predictions,
                "after_negative_test_pass": after_pass if forbidden else None,
            }
        )
    report = {
        "schema_version": "1.0",
        "model": str((MODEL_ROOT / "best.pt").relative_to(ROOT)),
        "confidence_threshold": 0.25,
        "samples": report_samples,
    }
    INFERENCE_REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "prepare", "verify", "train", "infer"))
    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(sample_inventory(), ensure_ascii=False, indent=2))
    elif args.command == "prepare":
        prepare()
    elif args.command == "verify":
        verify()
    elif args.command == "train":
        train()
    else:
        infer()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # Keep a concise, actionable CLI failure.
        print(f"ERROR: {error}", file=sys.stderr)
        raise
