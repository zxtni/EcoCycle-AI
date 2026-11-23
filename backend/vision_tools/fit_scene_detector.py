"""Fine-tune Open Images YOLO on EcoCycle's targeted annotated photo subset."""

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

import torch
from ultralytics import YOLO

from backend.vision import overlap
from backend.vision_tools.scene_pilot import LABELS, Example, select_examples

WEIGHTS_SHA256 = "3851dfbf39ed2a076b1f39215cc22dba64eb5646f282bf964703785b0bed6a41"
SCORE = 0.20


def val_ids(examples: list[Example]) -> set[str]:
    return {
        item.image_id
        for label in LABELS
        for item in [item for item in examples if item.category == label][:5]
    }


def stage_dataset(
    root: Path, cache: Path, items: list[Example], validation: set[str], names: dict[int, str]
) -> Path:
    dataset = root / "data"
    split_for = {item.image_id: "val" if item.image_id in validation else "train" for item in items}
    for section in ("images", "labels"):
        for split in ("train", "val"):
            (dataset / section / split).mkdir(parents=True, exist_ok=True)
    for image_id, split in split_for.items():
        shutil.copyfile(
            cache / "validation" / f"{image_id}.jpg", dataset / "images" / split / f"{image_id}.jpg"
        )
    category_map = {label: index for index, label in names.items() if label in LABELS}
    rows: dict[str, list[str]] = {image_id: [] for image_id in split_for}
    with (cache / "classes.csv").open(newline="", encoding="utf-8") as source:
        codes = {code: category_map[label] for code, label in csv.reader(source) if label in category_map}
    with (cache / "validation-boxes.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            image_id, label = row["ImageID"], row["LabelName"]
            if (
                image_id not in rows
                or label not in codes
                or row["IsGroupOf"] == "1"
                or row["IsDepiction"] == "1"
            ):
                continue
            left, right, top, bottom = (float(row[key]) for key in ("XMin", "XMax", "YMin", "YMax"))
            if min(left, top) < 0 or max(right, bottom) > 1 or left >= right or top >= bottom:
                continue
            rows[image_id].append(
                f"{codes[label]} {(left + right) / 2} {(top + bottom) / 2} {right - left} {bottom - top}"
            )
    for image_id, labels in rows.items():
        (dataset / "labels" / split_for[image_id] / f"{image_id}.txt").write_text(
            "\n".join(labels), encoding="utf-8"
        )
    settings = {
        "path": dataset.as_posix(),
        "train": "images/train",
        "val": "images/val",
        "names": names,
    }
    path = dataset / "scene.yaml"
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return path


def audit(model: YOLO, examples: list[Example], device: str) -> dict[str, dict[str, int]]:
    names = dict(model.names)
    selected = [index for index, label in names.items() if label in LABELS]
    by_id = {}
    for prediction in model.predict(
        source=[str(path) for path in sorted({row.path for row in examples})],
        imgsz=640,
        conf=SCORE,
        classes=selected,
        iou=0.45,
        device=device,
        stream=True,
        verbose=False,
    ):
        by_id[Path(prediction.path).stem] = [
            (names[int(label)], tuple(box))
            for label, box in zip(prediction.boxes.cls.tolist(), prediction.boxes.xyxyn.tolist(), strict=True)
        ]
    counts = {label: Counter(total=0, matched=0) for label in LABELS}
    for row in examples:
        counts[row.category]["total"] += 1
        counts[row.category]["matched"] += any(
            label == row.category and overlap(box, row.bounds) >= 0.50 for label, box in by_id[row.image_id]
        )
    return {label: dict(counter) for label, counter in counts.items()}


def matched(stats: dict[str, dict[str, int]]) -> int:
    return sum(row["matched"] for row in stats.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("weights", type=Path)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if hashlib.sha256(args.weights.read_bytes()).hexdigest() != WEIGHTS_SHA256:
        raise ValueError("Expected the pinned Ultralytics YOLOv8n Open Images checkpoint.")
    torch.set_num_threads(6)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fitting = select_examples(args.cache, "validation", 24)
    held_out = select_examples(args.cache, "test", 12)
    fit_ids = {item.image_id for item in fitting}
    fit_hashes = {hashlib.sha256(item.path.read_bytes()).digest() for item in fitting}
    held_out = [
        item
        for item in held_out
        if item.image_id not in fit_ids and hashlib.sha256(item.path.read_bytes()).digest() not in fit_hashes
    ]
    validation = val_ids(fitting)
    internal = [row for row in fitting if row.image_id in validation]
    base = YOLO(str(args.weights))
    stage = stage_dataset(output, args.cache, fitting, validation, dict(base.names))
    base_val = audit(base, internal, args.device)
    print("Pretrained internal validation:", base_val, flush=True)

    trainable = YOLO(str(args.weights))
    trainable.train(
        data=str(stage),
        project=str(output),
        name="targeted",
        exist_ok=True,
        device=args.device,
        imgsz=384,
        batch=8,
        epochs=args.epochs,
        workers=0,
        freeze=10,
        optimizer="AdamW",
        lr0=0.00015,
        seed=417,
        deterministic=True,
        mosaic=0.45,
        close_mosaic=0,
        plots=False,
        verbose=False,
        amp=False,
    )
    fine_tuned = YOLO(str(output / "targeted" / "weights" / "best.pt"))
    tuned_val = audit(fine_tuned, internal, args.device)
    selected = "fine-tuned" if matched(tuned_val) >= matched(base_val) else "pretrained"
    model = fine_tuned if selected == "fine-tuned" else base
    result = {
        "checkpoint_sha256": WEIGHTS_SHA256,
        "score_threshold": SCORE,
        "iou_threshold": 0.50,
        "fit_images": len(fit_ids - validation),
        "internal_validation_images": len(validation),
        "held_out_images": len({item.image_id for item in held_out}),
        "epochs": args.epochs,
        "pretrained_internal_validation": base_val,
        "fine_tuned_internal_validation": tuned_val,
        "selected": selected,
        "pretrained_holdout": audit(base, held_out, args.device),
        "fine_tuned_holdout": audit(fine_tuned, held_out, args.device),
    }
    (output / "scene-detector-metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    exported = Path(model.export(format="onnx", imgsz=640, opset=17, simplify=False, device="cpu"))
    destination = output / "objects.onnx"
    if exported.resolve() != destination.resolve():
        shutil.copyfile(exported, destination)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
