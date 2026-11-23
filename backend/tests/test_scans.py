import io
from pathlib import Path

from PIL import Image

from backend.vision import same_region


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


def test_upload_rejects_mismatched_type_and_animation(citizen):
    png = photo()["image"][1]
    assert citizen.post("/api/scans", files={"image": ("photo.jpg", png, "image/jpeg")}).status_code == 415
    frames = [Image.new("RGB", (160, 160), color) for color in ("white", "black")]
    animated = io.BytesIO()
    frames[0].save(animated, format="PNG", save_all=True, append_images=frames[1:], duration=100)
    assert (
        citizen.post(
            "/api/scans", files={"image": ("animated.png", animated.getvalue(), "image/png")}
        ).status_code
        == 422
    )


def test_scale_duplicates_are_distinct_from_neighboring_objects():
    bottle = (0.10, 0.10, 0.50, 0.80)
    assert same_region(bottle, (0.21, 0.27, 0.39, 0.63))
    assert not same_region(bottle, (0.42, 0.28, 0.65, 0.64))


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


def test_detail_scan_recovers_small_bottle_when_standard_already_detects_two(citizen):
    fixture = Path(__file__).resolve().parents[1] / "vision_assets" / "demo-plastic.jpg"
    scene = Image.new("RGB", (980, 700), "white")
    with Image.open(fixture) as source:
        for size, location in ((340, (10, 20)), (320, (645, 24)), (160, (480, 530))):
            sample = source.convert("RGB")
            sample.thumbnail((size, size))
            scene.paste(sample, location)
    upload = io.BytesIO()
    scene.save(upload, format="PNG")
    files = {"image": ("scene.png", upload.getvalue(), "image/png")}
    standard = citizen.post("/api/scans", files=files)
    detail = citizen.post("/api/scans", files=files, data={"detail": "true"})
    assert standard.status_code == detail.status_code == 201
    assert len(standard.json()["detections"]) == 2
    detections = detail.json()["detections"]
    assert [item["material"] for item in detections] == ["plastic"] * 3
    assert sum(item["box"][1] > 0.55 for item in detections) == 1


def test_electronics_need_explicit_disposal_confirmation(citizen):
    scan = citizen.post("/api/scans", files=photo())
    path = f"/api/scans/{scan.json()['id']}/confirm"
    body = {"material": "e-waste", "weight": 1}
    assert citizen.post(path, json=body).status_code == 422
    assert citizen.post(path, json={**body, "discarded_electronics": True}).status_code == 200
