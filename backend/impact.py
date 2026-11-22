import json
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from backend.auth import DB, Citizen
from backend.db import Scan
from backend.scans import Material

router = APIRouter(prefix="/api", tags=["impact"])
TABLE = json.loads(Path(__file__).with_name("materials.json").read_text(encoding="utf-8"))
WARDS = ("Indiranagar", "Koramangala", "Jayanagar", "Malleshwaram", "HSR Layout", "Whitefield")


class Estimate(BaseModel):
    material: Material
    weight: float = Field(gt=0, le=10_000, allow_inf_nan=False)


class Confirmation(Estimate):
    weight_source: Literal["user", "estimated"] = "user"
    ward: str = Field(default="Central", min_length=1, max_length=80)


def calculate(material: Material, weight: float) -> dict:
    factor = TABLE["materials"][material]
    return {
        "material": material,
        "weight": weight,
        "value_inr": round(weight * factor["inr_per_kg"], 4),
        "carbon_kg": round(weight * factor["carbon_kg_per_kg"], 6),
        "energy_kwh": round(weight * factor["energy_kwh_per_kg"], 6),
        "landfill_kg": weight,
        "factor": factor,
        "version": TABLE["version"],
    }


@router.get("/materials")
def materials():
    return {**TABLE, "wards": WARDS}


@router.post("/materials/estimate")
def estimate(body: Estimate):
    return calculate(body.material, body.weight)


@router.post("/scans/{scan_id}/confirm")
def confirm(scan_id: int, body: Confirmation, db: DB, user: Citizen):
    breakdown = calculate(body.material, body.weight)
    breakdown["weight_source"] = body.weight_source
    if body.ward not in (*WARDS, "Central"):
        raise HTTPException(422, "Choose a supported ward.")
    updated = db.execute(
        update(Scan)
        .where(
            Scan.id == scan_id,
            Scan.user_id == user.id,
            Scan.material.is_(None),
        )
        .values(material=body.material, weight=body.weight, breakdown=json.dumps(breakdown), ward=body.ward)
        .returning(Scan.id)
    )
    if updated.scalar_one_or_none() is None:
        if db.scalar(select(Scan.id).where(Scan.id == scan_id, Scan.user_id == user.id)) is None:
            raise HTTPException(404, "Scan not found.")
        raise HTTPException(409, "This scan is already in your history.")
    db.commit()
    return breakdown


@router.get("/impact")
def impact(db: DB, user: Citizen):
    rows = db.scalars(
        select(Scan)
        .where(
            Scan.user_id == user.id,
            Scan.breakdown.is_not(None),
        )
        .order_by(Scan.created.desc())
    ).all()
    history = [
        {
            "id": row.id,
            "created": row.created.isoformat() + "Z",
            "ward": row.ward,
            **json.loads(row.breakdown or "{}"),
        }
        for row in rows
    ]
    keys = ("value_inr", "carbon_kg", "energy_kwh", "landfill_kg")
    totals = {key: round(sum(entry[key] for entry in history), 6) for key in keys}
    dates = {row.created.date() for row in rows}
    day = date.today()
    if day not in dates:
        day -= timedelta(days=1)
    streak = 0
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    badges = []
    if history:
        badges.append("First sort")
    if totals["landfill_kg"] >= 5:
        badges.append("Five kilos diverted")
    if streak >= 7:
        badges.append("Week of action")
    return {"totals": totals, "history": history, "streak": streak, "badges": badges}
