"""Download an independent, deterministic TACO street-photo sample and score boxes."""

import argparse
import json
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

from PIL import Image

from backend.vision import ASSETS, detect, overlap

TACO = "https://raw.githubusercontent.com/pedropro/TACO/70479ad9adc3da971a8ae75ac97eb1026910eec7/data/annotations.json"
MIRROR = "https://huggingface.co/datasets/RandyHuynh5815/TACO-Waste-Recognition/resolve/c23700b465af288488bd7b4544c4166b9a970edf"
MAPPING = {
    "glass": {6, 9, 23, 26},
    "metal": {0, 8, 10, 11, 12, 28, 50, 52},
    "plastic": {4, 5, 7, 21, 24, 27, 29, 36, 39, 40, 41, 44, 45, 47, 48, 49, 55},
}


def retrieve(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size:
        return
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(url, timeout=50) as response:
                data = response.read()
            path.write_bytes(data)
            return
        except OSError as error:
            last_error = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"Could not fetch {url}") from last_error


def prepare(cache: Path) -> list[dict]:
    cache.mkdir(exist_ok=True, parents=True)
    retrieve(TACO, cache / "taco.json")
    annotations = json.loads((cache / "taco.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    images = {item["id"]: item for item in annotations["images"]}
    for annotation in annotations["annotations"]:
        grouped[annotation["image_id"]].append(annotation)
    candidates = defaultdict(list)
    for key, items in grouped.items():
        if len(items) != 1:
            continue
        item = items[0]
        material = next((name for name, ids in MAPPING.items() if item["category_id"] in ids), None)
        if material is None:
            continue
        image = images[key]
        x, y, w, h = item["bbox"]
        width, height = image["width"], image["height"]
        candidates[material].append({
            "file": image["file_name"], "material": material,
            "box": [x / width, y / height, (x + w) / width, (y + h) / height],
        })
    rng = random.Random(417)
    subset = [r for material in sorted(candidates)
              for r in rng.sample(sorted(candidates[material], key=lambda i: i["file"]), 12)]

    def get(row: dict) -> None:
        path = cache / row["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        retrieve(f"{MIRROR}/{row['file']}", path)

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(get, subset))
    return subset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--download-only", action="store_true")
    args = parser.parse_args()
    rows = prepare(args.cache)
    if args.download_only:
        return
    correct = localized = emitted = 0
    for row in rows:
        with Image.open(args.cache / row["file"]) as image:
            result = detect(image)
        detections = result["detections"]
        emitted += len(detections)
        correct += int(bool(detections and detections[0]["material"] == row["material"]))
        localized += int(any(
            detection["material"] == row["material"] and
            overlap(tuple(detection["box"]), tuple(row["box"])) >= 0.5
            for detection in detections
        ))
        row["predictions"] = detections
    metrics = {
        "images": len(rows), "top_label_correct": correct, "true_positive_iou50": localized,
        "detections": emitted, "precision_at_iou50": localized / emitted if emitted else 0,
        "recall_at_iou50": localized / len(rows), "rows": rows,
    }
    (ASSETS / "street_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print({k: v for k, v in metrics.items() if k != "rows"})


if __name__ == "__main__":
    main()
