"""CPU-only inference from a versioned JSON artifact fitted with scikit-learn."""

from __future__ import annotations

import json
import math
import os
from datetime import date, timedelta
from pathlib import Path
from typing import TypedDict


class Ward(TypedDict):
    ward: str
    lat: float
    lon: float
    share: float


class WardForecast(TypedDict):
    ward: str
    lat: float
    lon: float
    kg: float


class ForecastWeek(TypedDict):
    week_start: str
    wards: list[WardForecast]


class Metrics(TypedDict):
    mae_kg: float
    rmse_kg: float
    training_mean_mae_kg: float
    training_weeks: int
    test_weeks: int
    test_rows: int
    test_from: str
    test_through: str


class Artifact(TypedDict):
    coefficients: list[float]
    metrics: Metrics
    source_through: str
    source_weeks: int
    sklearn_version: str
    input_sha256: str


class Forecast(TypedDict):
    week_start: str
    synthetic: bool
    method: str
    source: str
    source_through: str
    metrics: Metrics
    weeks: list[ForecastWeek]


ASSETS = Path(__file__).resolve().parent / "forecast_assets"
DEFAULT_ARTIFACT = ASSETS / "model.json"
SOURCE = "https://data.austintexas.gov/d/mbnu-4wq9"
METHOD = (
    "Seasonal ridge regression on synthetic ward shares of Austin recycling weights"
)
WARDS: tuple[Ward, ...] = (
    {"ward": "Indiranagar", "lat": 12.9784, "lon": 77.6408, "share": 0.17},
    {"ward": "Koramangala", "lat": 12.9352, "lon": 77.6245, "share": 0.22},
    {"ward": "Jayanagar", "lat": 12.9250, "lon": 77.5938, "share": 0.15},
    {"ward": "Malleshwaram", "lat": 13.0031, "lon": 77.5643, "share": 0.13},
    {"ward": "HSR Layout", "lat": 12.9116, "lon": 77.6389, "share": 0.14},
    {"ward": "Whitefield", "lat": 12.9698, "lon": 77.7500, "share": 0.19},
)


def artifact_path() -> Path:
    return Path(os.environ.get("FORECAST_MODEL_PATH", str(DEFAULT_ARTIFACT)))


def features(week: date, index: int) -> list[float]:
    """Separate intercept and two annual Fourier harmonics for each ward."""
    phase = 2 * math.pi * (week.timetuple().tm_yday - 1) / 365.2425
    terms = [
        1.0,
        math.sin(phase),
        math.cos(phase),
        math.sin(2 * phase),
        math.cos(2 * phase),
    ]
    encoded = [0.0] * (len(WARDS) * len(terms))
    offset = len(terms) * index
    encoded[offset : offset + len(terms)] = terms
    return encoded


def refresh_model() -> Metrics:
    from .forecast_tools.train import train

    return train(artifact_path())["metrics"]


def forecast(week: date | None = None, weeks: int = 1) -> Forecast:
    if not 1 <= weeks <= 12:
        raise ValueError("Select one to twelve forecast weeks.")
    if week is None:
        today = date.today()
        week = today + timedelta(days=7 - today.weekday())
    else:
        week -= timedelta(days=week.weekday())
    path = artifact_path()
    artifact: Artifact = json.loads(
        (path if path.exists() else DEFAULT_ARTIFACT).read_text("utf-8")
    )
    predictions: list[ForecastWeek] = []
    for i in range(weeks):
        monday = week + timedelta(weeks=i)
        wards: list[WardForecast] = []
        for j, ward in enumerate(WARDS):
            kilograms = sum(
                a * b
                for a, b in zip(
                    features(monday, j), artifact["coefficients"], strict=True
                )
            )
            wards.append(
                {
                    "ward": ward["ward"],
                    "lat": ward["lat"],
                    "lon": ward["lon"],
                    "kg": round(max(0, kilograms), 1),
                }
            )
        predictions.append(
            {
                "week_start": monday.isoformat(),
                "wards": sorted(wards, key=lambda x: -x["kg"]),
            }
        )
    return {
        "week_start": week.isoformat(),
        "synthetic": True,
        "method": METHOD,
        "source": SOURCE,
        "source_through": artifact["source_through"],
        "metrics": artifact["metrics"],
        "weeks": predictions,
    }
