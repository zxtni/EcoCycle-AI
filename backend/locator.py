import json
import math
from functools import lru_cache
from pathlib import Path
from time import monotonic

import requests
from fastapi import APIRouter, Query
from sqlalchemy import select

from backend.auth import DB, Citizen
from backend.db import Center
from backend.scans import Material

router = APIRouter(prefix="/api", tags=["locator"])
MATERIAL_TAGS = {
    "plastic": ("plastic", "plastic_bottles", "plastic_packaging"),
    "metal": ("metal", "cans", "scrap_metal", "aluminium"),
    "glass": ("glass", "glass_bottles"),
    "e-waste": ("electrical_items", "small_appliances", "electronics", "computers"),
}
BENGALURU = (12.9716, 77.5946)
SEARCH_RADIUS_KM = 1000
PROVIDERS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)


def distance(lat: float, lon: float, dest_lat: float, dest_lon: float) -> float:
    a, b = math.radians(lat), math.radians(dest_lat)
    dlon = math.radians(dest_lon - lon)
    scale = math.sin((b - a) / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(dlon / 2) ** 2
    return 12742 * math.asin(math.sqrt(min(1, max(0, scale))))


@lru_cache(maxsize=96)
def overpass(lat: float, lon: float, bucket: int) -> list[dict] | None:
    # Include a margin for rounding the cache coordinates. Filter exact distances below.
    scope = f"(around:{(SEARCH_RADIUS_KM + 1) * 1000},{lat},{lon})"
    query = (
        f"[out:json][timeout:7];(nwr[amenity=recycling]{scope};"
        f"nwr[recycling_type=centre]{scope};);out center;"
    )
    for url in PROVIDERS:
        try:
            response = requests.get(
                url,
                params={"data": query},
                timeout=(3, 8),
                headers={
                    "User-Agent": "EcoCycleAI/1.0 (academic recycling locator)",
                },
            )
            response.raise_for_status()
            doc = response.json()
            if "remark" in doc or not isinstance(doc.get("elements"), list):
                continue
            break
        except (requests.RequestException, ValueError):
            continue
    else:
        return None
    listings = []
    for element in doc.get("elements", []):
        tags = element.get("tags", {})
        center = element.get("center", element)
        if tags.get("access") in {"private", "no"} or "lat" not in center or "lon" not in center:
            continue
        matches = [
            material
            for material, variants in MATERIAL_TAGS.items()
            if any(tags.get("recycling:" + key) == "yes" for key in variants)
        ]
        kind = tags.get("recycling_type")
        listings.append(
            {
                "id": f"osm-{element['type']}-{element['id']}",
                "name": tags.get("name")
                or ("Recycling center" if kind == "centre" else "Recycling drop-off"),
                "lat": center["lat"],
                "lon": center["lon"],
                "materials": matches,
                "source": "OpenStreetMap",
                "url": f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
            }
        )
    return listings


def center_payload(row: Center) -> dict:
    return {
        "id": f"local-{row.id}",
        "name": row.name,
        "lat": row.lat,
        "lon": row.lon,
        "materials": json.loads(row.materials),
        "source": row.source,
        "url": None,
    }


@lru_cache(maxsize=1)
def directory_snapshot() -> dict:
    return json.loads(Path(__file__).with_name("recycling_india.json").read_text(encoding="utf-8"))


@router.get("/centers")
def centers(
    db: DB,
    _user: Citizen,
    lat: float = Query(BENGALURU[0], ge=-90, le=90),
    lon: float = Query(BENGALURU[1], ge=-180, le=180),
    material: Material | None = None,
):
    snapshot = directory_snapshot()
    local = [center_payload(row) for row in db.scalars(select(Center)).all()]

    def nearby(listings: list[dict]) -> list[dict]:
        matches = []
        for center in listings:
            km = distance(lat, lon, center["lat"], center["lon"])
            if km <= SEARCH_RADIUS_KM and (material is None or material in center["materials"]):
                matches.append({**center, "distance": round(km, 2)})
        return matches

    saved = nearby(snapshot["centers"])
    live = None if saved else overpass(round(lat, 2), round(lon, 2), int(monotonic() // 900))
    results = saved + nearby((live or []) + local)
    results.sort(key=lambda item: item["distance"])
    return {
        "centers": results[:150],
        "live_available": live is not None,
        "snapshot_date": snapshot["date"] if saved else None,
    }
