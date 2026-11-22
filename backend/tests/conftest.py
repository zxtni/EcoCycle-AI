import os
import tempfile
from pathlib import Path

_directory = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(_directory.name) / "test.db").as_posix()

import pytest
from fastapi.testclient import TestClient

from backend.db import Base, engine
from backend.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def citizen(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "student@example.org", "password": "A long passphrase", "name": "Student"},
    )
    assert res.status_code == 201
    return client
