"""CPU waste detection with YOLO region proposals and a trained material head."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps

ASSETS = Path(__file__).with_name("vision_assets")
MODEL_VERSION = "ecocycle-regions-v2"
MATERIALS = ("e-waste", "glass", "metal", "other", "plastic")
Box = tuple[float, float, float, float]


class Detection(TypedDict):
    material: str
    confidence: float
    box: Box


class ScanResult(TypedDict):
    status: Literal["detected", "no_detection", "blurry"]
    model: str
    detections: list[Detection]


@lru_cache(maxsize=2)
def session(filename: str) -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    return ort.InferenceSession(
        str(ASSETS / filename), sess_options=options, providers=["CPUExecutionProvider"]
    )


def pixels(image: Image.Image) -> np.ndarray:
    square = image.resize((224, 224), Image.Resampling.BILINEAR)
    return np.asarray(square, dtype=np.float32).transpose(2, 0, 1) / 127.5 - 1.0


def overlap(a: Box, b: Box) -> float:
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return intersection / max(area_a + area_b - intersection, 1e-9)


def yolo_regions(image: Image.Image) -> list[Box]:
    w, h = image.size
    scale = 640 / max(w, h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    left, top = (640 - nw) // 2, (640 - nh) // 2
    padded = Image.new("RGB", (640, 640), (114, 114, 114))
    padded.paste(image.resize((nw, nh), Image.Resampling.BILINEAR), (left, top))
    inputs = np.asarray(padded, dtype=np.float32).transpose(2, 0, 1)[None] / 255
    network = session("regions.onnx")
    rows = network.run(None, {"images": inputs})[0][0].T
    classes = rows[:, 4:].argmax(axis=1)
    scores = rows[:, 4:].max(axis=1)
    # Prior classes include containers, tableware and common electronics.
    objects = np.isin(classes, [*range(39, 46), *range(62, 71), 72, 74, 75, 76, 78])
    indices = np.flatnonzero((scores >= 0.18) & objects)
    selected: list[Box] = []
    for index in indices[np.argsort(-scores[indices])[:100]]:
        x, y, width, height = rows[index, :4]
        bounds = np.clip(
            [
                (x - width / 2 - left) / nw,
                (y - height / 2 - top) / nh,
                (x + width / 2 - left) / nw,
                (y + height / 2 - top) / nh,
            ],
            0,
            1,
        )
        box = (float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))
        if (box[2] - box[0]) * (box[3] - box[1]) < 0.004:
            continue
        if all(overlap(box, old) < 0.45 for old in selected):
            selected.append(box)
        if len(selected) == 8:
            break
    return selected


def foreground_region(image: Image.Image) -> Box | None:
    """An isolated object's contrast with the border can supply a missing box."""
    small = np.asarray(image.resize((112, 112)), dtype=float)
    border = np.concatenate(
        (
            small[:3].reshape(-1, 3),
            small[-3:].reshape(-1, 3),
            small[:, :3].reshape(-1, 3),
            small[:, -3:].reshape(-1, 3),
        )
    )
    background = np.median(border, axis=0)
    border_distance = np.max(np.abs(border - background), axis=1)
    if np.median(border_distance) > 32:
        return None
    threshold = max(26.0, float(np.percentile(border_distance, 65)) + 17)
    mask = np.max(np.abs(small - background), axis=2) > threshold
    if not 0.018 <= mask.mean() <= 0.80:
        return None
    # Ignore thin border artifacts and outlying compression noise.
    y, x = np.where(mask)
    x1, x2 = np.quantile(x, [0.012, 0.988]) / 112
    y1, y2 = np.quantile(y, [0.012, 0.988]) / 112
    return max(0, x1 - 0.025), max(0, y1 - 0.025), min(1, x2 + 0.025), min(1, y2 + 0.025)


def crop_region(image: Image.Image, box: Box) -> Image.Image:
    w, h = image.size
    pad_x, pad_y = (box[2] - box[0]) * 0.1, (box[3] - box[1]) * 0.1
    return image.crop(
        (
            max(0, int((box[0] - pad_x) * w)),
            max(0, int((box[1] - pad_y) * h)),
            min(w, int(np.ceil((box[2] + pad_x) * w))),
            min(h, int(np.ceil((box[3] + pad_y) * h))),
        )
    )


def tile_regions(image: Image.Image) -> list[Box]:
    """Give small objects a second pass in overlapping, enlarged views."""
    width, height = image.size
    tile_width, tile_height = round(width * 0.62), round(height * 0.62)
    regions: list[Box] = []
    for left in (0, width - tile_width):
        for top in (0, height - tile_height):
            tile = image.crop((left, top, left + tile_width, top + tile_height))
            for x1, y1, x2, y2 in yolo_regions(tile):
                # Skip proposals clipped at a tile seam. Adjacent tiles overlap.
                if (
                    (left and x1 < 0.02)
                    or (top and y1 < 0.02)
                    or (left + tile_width < width and x2 > 0.98)
                    or (top + tile_height < height and y2 > 0.98)
                ):
                    continue
                regions.append(
                    (
                        (left + x1 * tile_width) / width,
                        (top + y1 * tile_height) / height,
                        (left + x2 * tile_width) / width,
                        (top + y2 * tile_height) / height,
                    )
                )
    return regions


def classify(image: Image.Image, boxes: list[Box]) -> list[Detection]:
    if not boxes:
        return []
    patches = np.stack([pixels(crop_region(image, box)) for box in boxes])
    probabilities = session("materials.onnx").run(None, {"pixel_values": patches})[0]
    detections: list[Detection] = []
    for box, scores in zip(boxes, probabilities, strict=True):
        label = int(np.argmax(scores))
        score = float(scores[label])
        if MATERIALS[label] != "other" and score >= 0.62:
            detections.append(
                {
                    "material": MATERIALS[label],
                    "confidence": round(score, 5),
                    "box": (round(box[0], 5), round(box[1], 5), round(box[2], 5), round(box[3], 5)),
                }
            )
    return detections


def detect(image: Image.Image) -> ScanResult:
    rgb = ImageOps.exif_transpose(image).convert("RGB")
    rgb.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    result: ScanResult = {"model": MODEL_VERSION, "status": "no_detection", "detections": []}
    gray = np.asarray(rgb.convert("L").resize((150, 150)), dtype=float)
    edges = 4 * gray[1:-1, 1:-1] - gray[2:, 1:-1] - gray[:-2, 1:-1]
    edges -= gray[1:-1, 2:] + gray[1:-1, :-2]
    if min(rgb.size) < 48 or edges.var() < 10:
        result["status"] = "blurry"
        return result
    detections = classify(rgb, yolo_regions(rgb))
    if len(detections) < 2 and max(rgb.size) >= 500:
        tiles = sorted(classify(rgb, tile_regions(rgb)), key=lambda item: item["confidence"], reverse=True)
        for candidate in tiles:
            if all(overlap(candidate["box"], item["box"]) < 0.40 for item in detections):
                detections.append(candidate)
            if len(detections) >= 8:
                break
    if not detections:
        foreground = foreground_region(rgb)
        if foreground:
            detections = classify(rgb, [foreground])
    result["detections"] = sorted(detections, key=lambda item: item["confidence"], reverse=True)
    if detections:
        result["status"] = "detected"
    return result
