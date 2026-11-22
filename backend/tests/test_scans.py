import io
from pathlib import Path

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
    fixture = Path(__file__).resolve().parents[1] / "vision_assets" / "demo-plastic.jpg"
    response = citizen.post("/api/scans", files={"image": ("photo.jpg", fixture.read_bytes(), "image/jpeg")})
    assert response.status_code == 201
    detection = response.json()["detections"][0]
    assert detection["material"] == "plastic"
    assert all(0 <= coordinate <= 1 for coordinate in detection["box"])


def test_wide_scene_recovers_two_separate_bottles(citizen):
    fixture = Path(__file__).resolve().parents[1] / "vision_assets" / "demo-plastic.jpg"
    scene = Image.new("RGB", (1100, 760), "white")
    with Image.open(fixture) as source:
        for size, location in ((310, (35, 40)), (128, (830, 520))):
            photo = source.convert("RGB")
            photo.thumbnail((size, size))
            scene.paste(photo, location)
    upload = io.BytesIO()
    scene.save(upload, format="PNG")
    response = citizen.post("/api/scans", files={"image": ("scene.png", upload.getvalue(), "image/png")})
    assert response.status_code == 201
    plastics = [item for item in response.json()["detections"] if item["material"] == "plastic"]
    assert len(plastics) == 2
    assert sorted(item["box"][0] > 0.5 for item in plastics) == [False, True]


def test_electronics_need_explicit_disposal_confirmation(citizen):
    scan = citizen.post("/api/scans", files=photo())
    path = f"/api/scans/{scan.json()['id']}/confirm"
    body = {"material": "e-waste", "weight": 1}
    assert citizen.post(path, json=body).status_code == 422
    assert citizen.post(path, json={**body, "discarded_electronics": True}).status_code == 200
