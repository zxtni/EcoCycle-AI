import io

from PIL import Image


def photo(color="white"):
    data = io.BytesIO()
    Image.new("RGB", (160, 160), color).save(data, format="PNG")
    return {"image": ("photo.png", data.getvalue(), "image/png")}


def test_scan_requires_session(client):
    assert client.post("/api/scans", files=photo()).status_code == 401


def test_upload_and_correction(citizen):
    image = citizen.post("/api/scans", files=photo())
    assert image.status_code == 201
    assert image.json()["status"] == "blurry"
    scan_id = image.json()["id"]
    endpoint = f"/api/scans/{scan_id}/correction"
    assert citizen.put(endpoint, json={"material": "metal"}).json()["status"] == "pending"
    assert citizen.put(endpoint, json={"material": "rubber"}).status_code == 422

    citizen.post("/api/auth/logout")
    citizen.post(
        "/api/auth/register",
        json={
            "email": "second@example.org",
            "password": "Another long passphrase",
            "name": "Second",
        },
    )
    assert citizen.put(endpoint, json={"material": "metal"}).status_code == 404


def test_invalid_upload(citizen):
    assert citizen.post("/api/scans", files={"image": ("bad.png", b"bad", "image/png")}).status_code == 422

def test_real_model_detects_held_out_plastic(citizen):
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[1] / "vision_assets" / "demo-plastic.jpg"
    response = citizen.post("/api/scans", files={"image": ("photo.jpg", fixture.read_bytes(), "image/jpeg")})
    assert response.status_code == 201
    detection = response.json()["detections"][0]
    assert detection["material"] == "plastic"
    assert all(0 <= coordinate <= 1 for coordinate in detection["box"])
