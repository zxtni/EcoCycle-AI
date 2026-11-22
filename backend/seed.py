import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import Center, engine


def seed():
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
        session.commit()


if __name__ == "__main__":
    seed()
