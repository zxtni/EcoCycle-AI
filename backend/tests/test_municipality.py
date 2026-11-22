from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import User, engine


def test_municipal_role_and_exports(citizen):
    assert citizen.get("/api/municipality/summary").status_code == 403
    with Session(engine) as db:
        account = db.scalar(select(User))
        assert account is not None
        account.role = "admin"
        db.commit()
    assert citizen.get("/api/municipality/summary").json()["totals"]["records"] == 0
    result = citizen.get("/api/municipality/forecast?weeks=2").json()
    assert result["synthetic"] and len(result["weeks"]) == 2
    assert citizen.get("/api/municipality/report/pdf").content.startswith(b"%PDF")
    assert "Section,Label,Value" in citizen.get("/api/municipality/report/csv").text
