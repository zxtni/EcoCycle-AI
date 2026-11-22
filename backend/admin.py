import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from backend.auth import DB, Admin
from backend.db import Audit, Center, Feedback, Scan
from backend.forecast import refresh_model
from backend.locator import center_payload
from backend.scans import Material

router = APIRouter(prefix="/api/admin", tags=["administration"])


class CenterInput(BaseModel):
    name: str = Field(min_length=2, max_length=120, pattern=r"\S")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    materials: list[Material] = Field(min_length=1, max_length=4)


class Review(BaseModel):
    status: Literal["accepted", "dismissed"]


def audit(db: DB, user: Admin, action: str):
    db.add(Audit(actor=user.id, action=action))
    db.commit()


@router.get("/centers")
def list_centers(db: DB, _user: Admin):
    return [
        {"key": row.id, **center_payload(row)} for row in db.scalars(select(Center).order_by(Center.name))
    ]


def write_center(row: Center, data: CenterInput):
    row.name = data.name.strip()
    row.lat, row.lon = data.lat, data.lon
    row.materials = json.dumps(list(dict.fromkeys(data.materials)))
    if not row.source:
        row.source = "Municipality managed"


@router.post("/centers", status_code=201)
def add_center(data: CenterInput, db: DB, user: Admin):
    row = Center()
    write_center(row, data)
    db.add(row)
    db.flush()
    audit(db, user, f"Created center #{row.id}")
    return center_payload(row)


@router.put("/centers/{key}")
def edit_center(key: int, data: CenterInput, db: DB, user: Admin):
    row = db.get(Center, key)
    if row is None:
        raise HTTPException(404, "Center not found.")
    write_center(row, data)
    audit(db, user, f"Edited center #{key}")
    return center_payload(row)


@router.delete("/centers/{key}")
def delete_center(key: int, db: DB, user: Admin):
    row = db.get(Center, key)
    if row is None:
        raise HTTPException(404, "Center not found.")
    db.delete(row)
    audit(db, user, f"Removed center #{key}")
    return {"ok": True}


@router.get("/feedback")
def list_feedback(db: DB, _user: Admin):
    records = db.execute(select(Feedback, Scan).join(Scan).order_by(Feedback.id.desc()).limit(100))
    return [
        {
            "id": item.id,
            "scan_id": item.scan_id,
            "material": item.material,
            "note": item.note,
            "status": item.status,
            "prediction": json.loads(scan.predictions),
        }
        for item, scan in records
    ]


@router.put("/feedback/{key}")
def review_feedback(key: int, body: Review, db: DB, user: Admin):
    result = db.execute(
        update(Feedback)
        .where(Feedback.id == key, Feedback.status == "pending")
        .values(status=body.status)
        .returning(Feedback.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(409, "This correction is unavailable for review.")
    audit(db, user, f"Marked correction #{key} as {body.status}")
    return {"status": body.status}


@router.get("/audit")
def list_audit(db: DB, _user: Admin):
    records = db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))
    return [
        {"id": row.id, "actor": row.actor, "action": row.action, "created": row.created.isoformat() + "Z"}
        for row in records
    ]


@router.post("/forecast/refresh")
def retrain(db: DB, user: Admin):
    result = refresh_model()
    audit(db, user, "Refit weekly forecast")
    return result
