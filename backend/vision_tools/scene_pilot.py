"""Fit a separate object-category candidate and audit current region coverage.

Run with the vision training environment:
    python -m backend.vision_tools.scene_pilot .tools/openimages
"""

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper
from PIL import Image
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from backend.vision import Box, crop_region, overlap, pixels, tile_regions, yolo_regions
from backend.vision_tools.train import RESOURCES

LABELS = ("Bottle", "Human hand", "Laptop", "Sunglasses", "Watch")
ANNOTATIONS = {
    "classes.csv": "https://storage.googleapis.com/openimages/v7/oidv7-class-descriptions-boxable.csv",
    "validation-boxes.csv": "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv",
    "test-boxes.csv": "https://storage.googleapis.com/openimages/v5/test-annotations-bbox.csv",
}
IMAGE_ROOT = "https://open-images-dataset.s3.amazonaws.com"
SEED = 417


@dataclass(frozen=True)
class Example:
    image_id: str
    category: str
    bounds: Box
    path: Path


def fetch(url: str, path: Path, *, timeout: int = 75) -> None:
    if path.exists() and path.stat().st_size:
        return
    import shutil

    staged = path.with_suffix(path.suffix + ".part")
    with urlopen(url, timeout=timeout) as response, staged.open("wb") as output:
        shutil.copyfileobj(response, output)
    staged.replace(path)


def select_examples(cache: Path, split: str, limit: int) -> list[Example]:
    with (cache / "classes.csv").open(encoding="utf-8", newline="") as source:
        categories = {code: label for code, label in csv.reader(source) if label in LABELS}
    pool: dict[str, dict[str, Box]] = {label: {} for label in LABELS}
    with (cache / f"{split}-boxes.csv").open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            category = categories.get(row["LabelName"])
            if not category or row["IsGroupOf"] == "1" or row["IsDepiction"] == "1":
                continue
            bounds = (float(row["XMin"]), float(row["YMin"]), float(row["XMax"]), float(row["YMax"]))
            width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
            if min(bounds) < 0 or max(bounds) > 1 or min(width, height) < 0.025:
                continue
            pool[category].setdefault(row["ImageID"], bounds)
    rng = random.Random(SEED)
    images = cache / split
    images.mkdir(exist_ok=True)
    examples = []
    for label, candidates in pool.items():
        if len(candidates) < limit:
            raise ValueError(f"{split}: {label} has only {len(candidates)} eligible images.")
        examples.extend(
            Example(key, label, candidates[key], images / f"{key}.jpg")
            for key in rng.sample(sorted(candidates), limit)
        )
    return examples


def download_images(examples: list[Example]) -> list[Path]:
    paths = {item.path for item in examples}

    def grab(path: Path) -> Path | None:
        for host in (IMAGE_ROOT, "https://open-images-dataset.s3.us-east-1.amazonaws.com"):
            try:
                fetch(f"{host}/{path.parent.name}/{path.name}", path, timeout=15)
                with Image.open(path) as image:
                    image.verify()
                return None
            except OSError:
                continue
        return path

    with ThreadPoolExecutor(max_workers=12) as pool:
        return [path for path in pool.map(grab, sorted(paths)) if path is not None]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoder(cache: Path) -> ort.InferenceSession:
    url, expected_hash = RESOURCES["mobile.onnx"]
    path = cache / "mobile.onnx"
    fetch(url, path)
    if digest(path) != expected_hash:
        raise ValueError("MobileNet source checksum did not match the training manifest.")
    graph = onnx.load(path)
    head = graph.graph.node[-1]
    features = head.input[0]
    unused = set(head.input[1:])
    graph.graph.node.remove(head)
    for initializer in list(graph.graph.initializer):
        if initializer.name in unused:
            graph.graph.initializer.remove(initializer)
    del graph.graph.output[:]
    graph.graph.output.append(helper.make_tensor_value_info(features, TensorProto.FLOAT, ["batch", 1280]))
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    return ort.InferenceSession(graph.SerializeToString(), options, providers=["CPUExecutionProvider"])


def features_for(network: ort.InferenceSession, examples: list[Example]) -> np.ndarray:
    batches = []
    for offset in range(0, len(examples), 12):
        patches = []
        for item in examples[offset : offset + 12]:
            with Image.open(item.path) as image:
                patches.append(pixels(crop_region(image.convert("RGB"), item.bounds)))
        batches.append(network.run(None, {"pixel_values": np.stack(patches)})[0])
    return np.concatenate(batches)


def proposal_audit(examples: list[Example]) -> dict[str, dict[str, int]]:
    stats = {label: Counter(total=0, full_box_matches=0, detailed_box_matches=0) for label in LABELS}
    for item in examples:
        with Image.open(item.path) as source:
            image = source.convert("RGB")
        image.thumbnail((1280, 1280))
        full = yolo_regions(image)
        detailed = full + tile_regions(image, detail=True)
        stats[item.category]["total"] += 1
        stats[item.category]["full_box_matches"] += any(overlap(box, item.bounds) >= 0.50 for box in full)
        stats[item.category]["detailed_box_matches"] += any(
            overlap(box, item.bounds) >= 0.50 for box in detailed
        )
    return {label: dict(counts) for label, counts in stats.items()}


def run(cache: Path, fit_limit: int, test_limit: int) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    for name, url in ANNOTATIONS.items():
        fetch(url, cache / name)
    fitting = select_examples(cache, "validation", fit_limit)
    held_out = select_examples(cache, "test", test_limit)
    missing = set(download_images(fitting + held_out))
    fitting = [row for row in fitting if row.path not in missing]
    held_out = [row for row in held_out if row.path not in missing]
    if {row.category for row in fitting} != set(LABELS):
        raise ValueError("A fitting object class is missing after downloads.")
    fit_ids = {row.image_id for row in fitting}
    fit_hashes = {digest(row.path) for row in fitting}
    test = [row for row in held_out if row.image_id not in fit_ids and digest(row.path) not in fit_hashes]
    if {row.category for row in test} != set(LABELS):
        raise ValueError("A held-out object class is missing after duplicate removal.")

    network = encoder(cache)
    train_vectors = features_for(network, fitting)
    test_vectors = features_for(network, test)
    with threadpool_limits(limits=2):
        candidate = LogisticRegression(C=0.35, class_weight="balanced", max_iter=600, random_state=SEED)
        candidate.fit(train_vectors, [row.category for row in fitting])
    predictions = candidate.predict(test_vectors)
    fit_counts = Counter(row.category for row in fitting)
    test_counts = Counter(row.category for row in test)
    correct = Counter(
        row.category for row, prediction in zip(test, predictions, strict=True) if row.category == prediction
    )
    np.savez(
        cache / "object-head-candidate.npz",
        classes=candidate.classes_.astype(str),
        weights=candidate.coef_,
        bias=candidate.intercept_,
    )
    metrics = {
        "seed": SEED,
        "fit_split": "Open Images validation",
        "test_split": "Open Images test",
        "fit_per_class": dict(fit_counts),
        "test_per_class": dict(test_counts),
        "crop_correct_per_class": {label: correct[label] for label in LABELS},
        "crop_accuracy": sum(correct.values()) / len(test),
        "proposal_iou50": proposal_audit(test),
        "dropped_cross_split_duplicates": len(held_out) - len(test),
        "unavailable_photo_paths": [path.relative_to(cache).as_posix() for path in sorted(missing)],
        "fit_ids": sorted(fit_ids),
        "test_ids": sorted({row.image_id for row in test}),
    }
    (cache / "scene-pilot-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--fit-per-label", type=int, default=24)
    parser.add_argument("--test-per-label", type=int, default=12)
    args = parser.parse_args()
    if min(args.fit_per_label, args.test_per_label) <= 0:
        parser.error("Sample counts must be positive.")
    metrics = run(args.cache, args.fit_per_label, args.test_per_label)
    print(json.dumps({name: value for name, value in metrics.items() if not name.endswith("_ids")}, indent=2))


if __name__ == "__main__":
    main()
