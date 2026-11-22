import json
import math
from functools import lru_cache
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
PROVIDERS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)


def distance(lat: float, lon: float, dest_lat: float, dest_lon: float) -> float:
    a, b = math.radians(lat), math.radians(dest_lat)
    dlon = math.radians(dest_lon - lon)
    scale = math.sin((b - a) / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(dlon / 2) ** 2
    return 12742 * math.asin(math.sqrt(min(1, max(0, scale))))


@lru_cache(maxsize=96)
def overpass(lat: float, lon: float, bucket: int) -> list[dict] | None:
    query = f"[out:json][timeout:7];nwr[amenity=recycling](around:18000,{lat},{lon});out center 150;"
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
            break
        except (requests.RequestException, ValueError):
            continue
    else:
        return None
    listings = []
    for element in doc.get("elements", []):
        tags = element.get("tags", {})
        center = element.get("center", element)
        if "lat" not in center or "lon" not in center:
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


@router.get("/centers")
def centers(
    db: DB,
    _user: Citizen,
    lat: float = Query(BENGALURU[0], ge=-90, le=90),
    lon: float = Query(BENGALURU[1], ge=-180, le=180),
    material: Material | None = None,
):
    live = overpass(round(lat, 2), round(lon, 2), int(monotonic() // 900))
    local = [center_payload(row) for row in db.scalars(select(Center)).all()]
    combined = (live or []) + local
    results = []
    for center in combined:
        km = distance(lat, lon, center["lat"], center["lon"])
        if km <= 20 and (material is None or material in center["materials"]):
            results.append({**center, "distance": round(km, 2)})
    results.sort(key=lambda item: item["distance"])
    return {"centers": results, "live_available": live is not None}
