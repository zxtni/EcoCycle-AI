from backend import locator


def test_saved_directory_uses_requested_coordinates_and_material(citizen, monkeypatch):
    snapshot = {
        "date": "2026-11-25",
        "centers": [
            {"id": "far", "lat": 19.2, "lon": 72.8, "materials": ["glass"]},
            {"id": "near", "lat": 19.1, "lon": 72.8, "materials": ["glass"]},
            {"id": "other-material", "lat": 19.1, "lon": 72.8, "materials": ["metal"]},
            {"id": "outside", "lat": 28.61, "lon": 77.21, "materials": ["glass"]},
        ],
    }
    monkeypatch.setattr(locator, "directory_snapshot", lambda: snapshot)

    def unexpected_live_request(*args):
        raise AssertionError("Saved results should work without a live request")

    monkeypatch.setattr(locator, "overpass", unexpected_live_request)
    result = citizen.get("/api/centers", params={"lat": 19.1, "lon": 72.8, "material": "glass"})
    assert result.status_code == 200
    data = result.json()
    assert data["snapshot_date"] == snapshot["date"]
    assert [center["id"] for center in data["centers"]] == ["near", "far"]
    assert data["centers"][0]["distance"] == 0


def test_live_fallback_when_saved_directory_has_no_match(citizen, monkeypatch):
    monkeypatch.setattr(locator, "directory_snapshot", lambda: {"date": "2026-11-25", "centers": []})
    monkeypatch.setattr(locator, "overpass", lambda *_: [])
    data = citizen.get("/api/centers", params={"lat": 19.1, "lon": 72.8}).json()
    assert data == {"centers": [], "live_available": True, "snapshot_date": None}
