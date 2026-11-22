"""Fit the waste classification head and export it into a portable ONNX graph.

Run from the repository root: python -m backend.vision_tools.train PATH_TO_CACHE
"""

import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper, numpy_helper
from PIL import Image
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from backend.vision import ASSETS, MATERIALS, crop_region, detect, foreground_region, pixels

TRASHNET = "https://raw.githubusercontent.com/garythung/trashnet/6fa2b878c6c1b4304b91109070ce0edf9279bb31/data"
MOBILE = "https://huggingface.co/onnx-community/mobilenet_v2_1.0_224/resolve/c5903ea5f5bb219f02c85a778af0fedf14f502d8/onnx/model.onnx"
ELECTRONICS = "https://www.kaggle.com/api/v1/datasets/download/akshat103/e-waste-image-dataset?datasetVersionNumber=1"
RESOURCES = {
    "mobile.onnx": (MOBILE, "a86af476bbfa58ec86cae5f17d3d17d88c3c2b489e8ae2bd7e02421257f14dc2"),
    "trashnet.zip": (f"{TRASHNET}/dataset-resized.zip", "0bf472790f8b20e5c950d5b5012a9d38af0d3392efd65f8ce171334fc16b07c2"),
    "ewaste.zip": (ELECTRONICS, "1b0ab4530da8f2317ad6b435dadd1eeedf97f3d9ecc8e93942d270ea59c6db30"),
    "train.txt": (f"{TRASHNET}/one-indexed-files-notrash_train.txt", "420971a4248b42b07a741ef277059d92ded0c559cae8960c6a488e9c316ff789"),
    "val.txt": (f"{TRASHNET}/one-indexed-files-notrash_val.txt", "a6c01936e4a4adce41e8da776db39b366d1db46acf07f63215bbe24709081340"),
    "test.txt": (f"{TRASHNET}/one-indexed-files-notrash_test.txt", "a8cc4e520e4676c6e1bd6346d51a101f80e468763a36f2818ed4e32abb05bb79"),
}


def download(cache: Path) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    for filename, (url, digest) in RESOURCES.items():
        path = cache / filename
        if not path.exists():
            with urlopen(url, timeout=120) as response:
                path.write_bytes(response.read())
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Unexpected checksum for {filename}. Remove the cached copy and retry.")


def records(cache: Path) -> dict:
    splits = defaultdict(list)
    names = {}
    for group in ("train", "val", "test"):
        for row in (cache / f"{group}.txt").read_text().splitlines():
            names[row.split()[0]] = group
    seen: dict[str, set[str]] = defaultdict(set)
    for source in ["trashnet.zip", "ewaste.zip"]:
        with zipfile.ZipFile(cache / source) as archive:
            for key in sorted(archive.namelist()):
                path = Path(key)
                if path.suffix.lower() != ".jpg" or key.startswith("__MACOSX"):
                    continue
                if source == "trashnet.zip":
                    group = names.get(path.name)
                    label = path.parent.name if path.parent.name in MATERIALS else "other"
                else:
                    group = path.parts[1]
                    label = "e-waste"
                if group not in ("train", "val", "test"):
                    continue
                raw = archive.read(key)
                digest = hashlib.sha256(raw).hexdigest()
                seen[digest].add(group)
                splits[group].append((key, label, raw, digest))
    for group in splits:
        # A repeated byte-identical image may only belong to one published split.
        splits[group] = [(k, lbl, data) for k, lbl, data, d in splits[group] if len(seen[d]) == 1]
    return splits


def rgb_image(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as image:
        return image.convert("RGB")


def embed(graph: onnx.ModelProto, samples: list) -> tuple[np.ndarray, list]:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    network = ort.InferenceSession(graph.SerializeToString(), options, providers=["CPUExecutionProvider"])
    vectors, labels, batch = [], [], []
    for _, label, raw in samples:
        image = rgb_image(raw)
        batch.append(pixels(image))
        labels.append(label)
        region = foreground_region(image)
        if region is not None:
            batch.append(pixels(crop_region(image, region)))
            labels.append(label)
        if len(batch) >= 24:
            vectors.append(network.run(None, {"pixel_values": np.stack(batch)})[0])
            batch = []
    if batch:
        vectors.append(network.run(None, {"pixel_values": np.stack(batch)})[0])
    return np.concatenate(vectors), labels


def train(cache: Path, training: list) -> None:
    graph = onnx.load(cache / "mobile.onnx")
    final = graph.graph.node[-1]
    features = final.input[0]
    head_parameters = set(final.input[1:])
    graph.graph.node.remove(final)
    for weight in list(graph.graph.initializer):
        if weight.name in head_parameters:
            graph.graph.initializer.remove(weight)
    del graph.graph.output[:]
    graph.graph.output.append(helper.make_tensor_value_info(features, TensorProto.FLOAT, ["batch", 1280]))
    vectors, labels = embed(graph, training)
    with threadpool_limits(limits=2):
        classifier = LogisticRegression(C=0.35, max_iter=600, class_weight="balanced", random_state=417)
        classifier.fit(vectors, labels)
    assert list(classifier.classes_) == list(MATERIALS)
    for name, matrix in (("waste_weights", classifier.coef_.T), ("waste_bias", classifier.intercept_)):
        graph.graph.initializer.append(numpy_helper.from_array(matrix.astype(np.float32), name))
    graph.graph.node.extend([
        helper.make_node("Gemm", [features, "waste_weights", "waste_bias"], ["waste_logits"]),
        helper.make_node("Softmax", ["waste_logits"], ["probabilities"], axis=1),
    ])
    del graph.graph.output[:]
    graph.graph.output.append(helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, ["batch", len(MATERIALS)]))
    onnx.checker.check_model(graph)
    onnx.save(graph, ASSETS / "materials.onnx")
    print(f"Saved material head trained on {len(training)} images and {len(vectors)} views.", flush=True)


def evaluate(test: list) -> dict:
    confusion: dict = defaultdict(Counter)
    accepted = correct = 0
    for key, label, raw in test:
        result = detect(rgb_image(raw))
        top = result["detections"][0]["material"] if result["detections"] else "unassigned"
        confusion[label][top] += 1
        if label != "other":
            accepted += int(top != "unassigned")
            correct += int(label == top)
        if label == top == "plastic" and not (ASSETS / "demo-plastic.jpg").exists():
            (ASSETS / "demo-plastic.jpg").write_bytes(raw)
            (ASSETS / "demo-source.txt").write_text(key + "\n", encoding="utf-8")
    total = sum(sum(c.values()) for key, c in confusion.items() if key != "other")
    return {
        "test_images": len(test), "target_images": total, "correct_target": correct,
        "detected_target": accepted, "target_top1_accuracy": correct / total,
        "target_coverage": accepted / total, "confusion": confusion,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--evaluate-only", action="store_true")
    args = parser.parse_args()
    download(args.cache)
    splits = records(args.cache)
    if not args.evaluate_only:
        train(args.cache, splits["train"])
    metrics = evaluate(splits["test"])
    metrics["splits"] = {split: dict(Counter(r[1] for r in rows)) for split, rows in splits.items()}
    metrics["materials_sha256"] = hashlib.sha256((ASSETS / "materials.onnx").read_bytes()).hexdigest()
    (ASSETS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
