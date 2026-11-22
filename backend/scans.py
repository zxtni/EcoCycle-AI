import io
import json
from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.auth import DB, Citizen
from backend.db import Feedback, Scan
from backend.vision import detect

router = APIRouter(prefix="/api/scans", tags=["scans"])
Material = Literal["plastic", "glass", "metal", "e-waste"]
MAX_BYTES = 8 * 1024 * 1024


class Correction(BaseModel):
    material: Material
    note: str = Field(default="", max_length=400)


def owned_scan(scan_id: int, db: DB, user: Citizen) -> Scan:
    scan = db.scalar(select(Scan).where(Scan.id == scan_id, Scan.user_id == user.id))
    if scan is None:
        raise HTTPException(404, "Scan not found.")
    return scan


@router.post("", status_code=201)
def scan_photo(db: DB, user: Citizen, image: Annotated[UploadFile, File()]):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Choose a JPEG, PNG or WebP photo.")
    data = image.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Choose a photo under 8 MB.")
    try:
        with Image.open(io.BytesIO(data), formats=["JPEG", "PNG", "WEBP"]) as original:
            if original.width * original.height > 24_000_000:
                raise HTTPException(413, "Choose a photo under 24 megapixels.")
            oriented = ImageOps.exif_transpose(original).convert("RGB")
            oriented.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, "The photo could not be decoded.") from exc
    try:
        result = detect(oriented)
    except (OSError, RuntimeError) as exc:
        raise HTTPException(503, "The detection model is unavailable.") from exc
    entry = Scan(user_id=user.id, predictions=json.dumps(result))
    db.add(entry)
    db.commit()
    return {"id": entry.id, **result}


@router.put("/{scan_id}/correction")
def correct(scan_id: int, body: Correction, db: DB, user: Citizen):
    entry = owned_scan(scan_id, db, user)
    feedback = db.scalar(select(Feedback).where(Feedback.scan_id == entry.id))
    if feedback is None:
        feedback = Feedback(scan_id=entry.id)
        db.add(feedback)
    feedback.material = body.material
    feedback.note = body.note.strip()
    feedback.status = "pending"
    db.commit()
    return {"status": feedback.status}

