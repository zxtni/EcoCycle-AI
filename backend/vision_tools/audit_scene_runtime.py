"""Score the shipped ONNX object detector on the untouched phone-scene pilot subset."""

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

from backend.vision import MODEL_VERSION, identify_objects, overlap
from backend.vision_tools.scene_pilot import LABELS, select_examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    labels = [label for label in LABELS if label != "Human hand"]
    rows = [row for row in select_examples(args.cache, "test", 12) if row.category in labels]
    results = {}
    for mode in ("standard", "detailed"):
        stats = {label: Counter(total=0, matched=0, emitted=0) for label in labels}
        for row in rows:
            with Image.open(row.path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1280, 1280))
            found = identify_objects(image, detail=mode == "detailed")
            stats[row.category]["total"] += 1
            stats[row.category]["matched"] += any(
                item["name"] == row.category and overlap(item["box"], row.bounds) >= 0.50 for item in found
            )
            stats[row.category]["emitted"] += len(found)
        results[mode] = {name: dict(counts) for name, counts in stats.items()}
    report = {
        "model": MODEL_VERSION,
        "object_score_threshold": 0.2,
        "iou_threshold": 0.5,
        "test_images": len(rows),
        "results": results,
    }
    formatted = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(formatted + "\n", encoding="utf-8")
    print(formatted)


if __name__ == "__main__":
    main()
