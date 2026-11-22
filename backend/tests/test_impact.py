from backend.impact import calculate


def test_values_scale_with_weight():
    first = calculate("glass", 1)
    double = calculate("glass", 2)
    assert first["value_inr"] == 1
    assert double["energy_kwh"] == 2 * first["energy_kwh"]
    assert double["carbon_kg"] == 2 * first["carbon_kg"]
    assert double["landfill_kg"] == 2


def test_estimate_rejects_negative_weight(client):
    assert client.post("/api/materials/estimate", json={"material": "glass", "weight": -1}).status_code == 422
