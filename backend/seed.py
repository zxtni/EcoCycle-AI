import json
import os
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import password_hash
from backend.db import Center, Scan, User, engine, now
from backend.impact import calculate
from backend.scans import Material


def seed():
    if os.getenv("APP_ENV") == "production" or os.getenv("ECO_DEMO") == "0":
        return
    examples = (
        ("Indiranagar sample collection point", 12.9784, 77.6408, ["plastic", "glass"]),
        ("Jayanagar sample collection point", 12.9250, 77.5938, ["metal", "plastic"]),
        ("Koramangala sample collection point", 12.9352, 77.6245, ["e-waste", "metal"]),
    )
    with Session(engine) as session:
        for name, lat, lon, materials in examples:
            if session.scalar(select(Center.id).where(Center.name == name)) is None:
                session.add(
                    Center(
                        name=name, lat=lat, lon=lon, materials=json.dumps(materials), source="Synthetic demo"
                    )
                )
        for role in ("citizen", "admin"):
            email = role + "@example.org"
            if session.scalar(select(User.id).where(User.email == email)):
                continue
            user = User(
                email=email,
                name="Demo " + role.capitalize(),
                role=role,
                synthetic=True,
                password=password_hash("EcoCycle local demo 2026!"),
            )
            session.add(user)
            session.flush()
            if role == "citizen":
                demo_materials: tuple[Material, ...] = ("plastic", "glass", "metal", "e-waste")
                wards = ("Indiranagar", "Koramangala", "Jayanagar", "Whitefield")
                for index in range(16):
                    material = demo_materials[index % len(demo_materials)]
                    weight = round(0.15 + index * 0.08, 2)
                    session.add(
                        Scan(
                            user_id=user.id,
                            material=material,
                            weight=weight,
                            created=now() - timedelta(days=index * 2),
                            predictions=json.dumps({"status": "synthetic", "detections": []}),
                            breakdown=json.dumps(calculate(material, weight)),
                            ward=wards[index % len(wards)],
                        )
                    )
        session.commit()


if __name__ == "__main__":
    seed()

