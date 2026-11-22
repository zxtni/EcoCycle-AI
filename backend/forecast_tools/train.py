"""Rebuild with python -m backend.forecast_tools.train from the repository root."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ..forecast import ASSETS, WARDS, Artifact, Metrics, artifact_path, features

SEED = 43109
TEST_WEEKS = 52
POUNDS_TO_KG = 0.45359237
SCENARIO_SHARE = 0.075


def train(output: Path) -> Artifact:
    rng = random.Random(SEED)
    source = ASSETS / "austin_weekly.csv"
    with source.open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream))
    records.sort(key=lambda record: record["week_start"])
    if len(records) < TEST_WEEKS * 3:
        raise ValueError("Training needs at least three years of weekly collections.")

    rows: list[list[float]] = []
    targets: list[float] = []
    for record in records:
        week = date.fromisoformat(record["week_start"])
        total = float(record["pounds"]) * POUNDS_TO_KG * SCENARIO_SHARE
        phase = 2 * math.pi * (week.timetuple().tm_yday - 1) / 365.2425
        # Six synthetic local allocations always sum to the scaled city measurement.
        shares = [
            ward["share"] * (1 + 0.15 * math.sin(phase + i) + rng.uniform(-0.09, 0.09))
            for i, ward in enumerate(WARDS)
        ]
        for index, share in enumerate(shares):
            rows.append(features(week, index))
            targets.append(total * share / sum(shares))

    x = np.asarray(rows)
    y = np.asarray(targets)
    cutoff = (len(records) - TEST_WEEKS) * len(WARDS)
    regressor = Ridge(alpha=1.0, fit_intercept=False, solver="svd")
    regressor.fit(x[:cutoff], y[:cutoff])
    predicted = regressor.predict(x[cutoff:])
    means = y[:cutoff].reshape(-1, len(WARDS)).mean(axis=0)
    metrics: Metrics = {
        "mae_kg": round(float(mean_absolute_error(y[cutoff:], predicted)), 2),
        "rmse_kg": round(float(mean_squared_error(y[cutoff:], predicted) ** 0.5), 2),
        "training_mean_mae_kg": round(
            float(mean_absolute_error(y[cutoff:], np.tile(means, TEST_WEEKS))), 2
        ),
        "training_weeks": cutoff // len(WARDS),
        "test_weeks": TEST_WEEKS,
        "test_rows": len(y) - cutoff,
        "test_from": records[-TEST_WEEKS]["week_start"],
        "test_through": records[-1]["week_start"],
    }
    # Metrics describe only the held-out predictions. Refit all data for deployment.
    regressor.fit(x, y)
    artifact: Artifact = {
        "coefficients": regressor.coef_.tolist(),
        "metrics": metrics,
        "source_through": records[-1]["week_start"],
        "source_weeks": len(records),
        "sklearn_version": sklearn.__version__,
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=output.parent, delete=False
    ) as handle:
        staged = Path(handle.name)
        try:
            json.dump(artifact, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            handle.close()
            staged.unlink(missing_ok=True)
            raise
    try:
        os.replace(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    return artifact


if __name__ == "__main__":
    print(json.dumps(train(artifact_path())["metrics"], indent=2))
