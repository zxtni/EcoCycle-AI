import csv
import io
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from fpdf import FPDF
from sqlalchemy import select

from backend.auth import DB, Admin
from backend.db import Scan, User
from backend.forecast import forecast
from backend.locator import BENGALURU, distance

router = APIRouter(prefix="/api/municipality", tags=["municipality"])


def summary(db: DB, start: date | None, end: date | None, demo: bool):
    if start and end and start > end:
        raise HTTPException(422, "The start date must precede the end date.")
    query = select(Scan).join(User).where(Scan.breakdown.is_not(None), User.synthetic == demo)
    if start:
        query = query.where(Scan.created >= datetime.combine(start, time.min))
    if end:
        query = query.where(Scan.created <= datetime.combine(end, time.max))
    mix: dict[str, float] = defaultdict(float)
    trend: dict[str, float] = defaultdict(float)
    wards: dict[str, float] = defaultdict(float)
    totals = {"records": 0, "landfill_kg": 0.0, "carbon_kg": 0.0, "energy_kwh": 0.0}
    for scan in db.scalars(query):
        values = json.loads(scan.breakdown or "{}")
        for key in ("landfill_kg", "carbon_kg", "energy_kwh"):
            totals[key] += values[key]
        totals["records"] += 1
        weight = values["landfill_kg"]
        mix[values["material"]] += weight
        monday = scan.created.date() - timedelta(days=scan.created.weekday())
        trend[monday.isoformat()] += weight
        wards[scan.ward] += weight
    return {
        "totals": totals,
        "mix": dict(mix),
        "trend": dict(sorted(trend.items())),
        "wards": dict(wards),
        "synthetic": demo,
    }


@router.get("/summary")
def municipal_summary(
    db: DB, _admin: Admin, start: date | None = None, end: date | None = None, demo: bool = False
):
    return summary(db, start, end, demo)


@router.get("/forecast")
def municipal_forecast(_admin: Admin, weeks: int = Query(4, ge=1, le=12)):
    data = forecast(weeks=weeks)
    stops = data["weeks"][0]["wards"][:4]
    route = []
    position = BENGALURU
    while stops:
        stop = min(stops, key=lambda ward: distance(*position, ward["lat"], ward["lon"]))
        stops.remove(stop)
        route.append(stop)
        position = (stop["lat"], stop["lon"])
    return {**data, "route": route}


@router.get("/report/{kind}")
def export_report(
    kind: Literal["csv", "pdf"],
    db: DB,
    _admin: Admin,
    start: date | None = None,
    end: date | None = None,
    demo: bool = False,
):
    data = summary(db, start, end, demo)
    records = [
        ("Dataset", "Source", "Synthetic demo" if demo else "Citizen records"),
        ("Range", "Start", start.isoformat() if start else "All dates"),
        ("Range", "End", end.isoformat() if end else "All dates"),
    ]
    for section in ("totals", "mix", "trend", "wards"):
        records.extend((section, key, str(round(value, 3))) for key, value in data[section].items())
    headers = {"Content-Disposition": f'attachment; filename="ecocycle-report.{kind}"'}
    if kind == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(("Section", "Label", "Value"))
        writer.writerows(records)
        return Response(buffer.getvalue(), media_type="text/csv", headers=headers)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 14, "EcoCycle AI - Municipality report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for section, label, value in records:
        pdf.cell(0, 8, f"{section.title()} | {label} | {value}", new_x="LMARGIN", new_y="NEXT")
    return Response(bytes(pdf.output()), media_type="application/pdf", headers=headers)

