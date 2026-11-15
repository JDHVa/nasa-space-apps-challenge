import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import service
from app.api import app
from app.data import site as site_module
from app.data.site import load_demo_site
from app.schemas import AnalyzeResponse
from app.twin.ensemble import SiteParams, build_samples, run_strategy
from app.twin.rotations import generate_alternatives, parse_rotation


@pytest.fixture(scope="module")
def demo_site():
    return load_demo_site()


def test_water_balance_closes(demo_site):
    samples = build_samples(demo_site.weather, 20.52, 3, 12)
    params = SiteParams(20.52, 2.1, 0.24)
    for crops in (["maize"], ["beans", "oats"], ["fallow"]):
        run = run_strategy(crops, samples, params, 3, irrigation_mm=100)
        assert run.balance_residual < 1e-6


def test_alternatives_distinct():
    current = parse_rotation(["maize", "beans"]).crops
    alternatives = generate_alternatives(current)
    assert len(alternatives) >= 2
    assert all(tuple(current) != alt.crops for alt in alternatives)


def test_demo_offline(monkeypatch, tmp_path):
    from app.data import gee, power

    def blocked(*args, **kwargs):
        raise OSError("network disabled")

    monkeypatch.setattr(power, "fetch_power_daily", blocked)
    monkeypatch.setattr(gee, "fetch_gee_summary", blocked)
    monkeypatch.setattr(site_module, "fetch_power_daily", blocked)
    monkeypatch.setattr(site_module, "fetch_gee_summary", blocked)
    monkeypatch.setattr(service, "demo_path", lambda farm: tmp_path / f"demo_{farm}.json")
    client = TestClient(app)
    response = client.get("/demo")
    assert response.status_code == 200
    parsed = AnalyzeResponse(**response.json())
    assert len(parsed.strategies) >= 3
    assert parsed.strategies[0].is_current
    assert parsed.site.data_mode == "demo"
    assert parsed.site.soil is not None
    assert parsed.validation.soil_moisture_observed and len(parsed.validation.soil_moisture_twin) == 12
    assert len(parsed.strategies[0].bare_soil_calendar) == 12
    assert parsed.strategies[0].daily_sample


def test_analyze_and_explain(monkeypatch):
    from app.ai import emulator, narrator

    def broken(messages):
        raise ConnectionError("ollama down")
        yield ""

    monkeypatch.setattr(narrator, "ollama_chunks", broken)
    monkeypatch.setattr(emulator, "MODEL_PATH", emulator.MODEL_PATH.with_name("missing.pt"))
    emulator.reset_emulator()
    monkeypatch.setattr(service, "load_site", lambda lat, lon: load_demo_site())
    client = TestClient(app)
    body = {"lat": 20.52, "lon": -100.81, "current_rotation": ["maize"], "priorities": {"water": 1, "nitrogen": 0.5, "erosion": 0.5, "organic_matter": 0.5, "income": 0.2}, "years": 4, "lang": "es"}
    analysis = client.post("/analyze", json=body).json()
    scores = [s["score"] for s in analysis["strategies"][1:]]
    assert scores == sorted(scores, reverse=True)
    streamed = client.post("/explain", json={"strategy_id": "current", "analysis": analysis, "lang": "es"})
    assert "Evidencia" in streamed.text
    whatif = client.post("/whatif", json={"strategy_id": "cover_crop", "sowing_shift_days": 10, "irrigation_mm": 50, "crop_swap": None, "site": analysis["site"]})
    assert whatif.json()["method"] == "twin"
    assert set(whatif.json()["metrics"]) == set(analysis["strategies"][0]["metrics"])


def test_whatif_falls_back_to_twin_without_model(monkeypatch):
    from app.ai import emulator

    monkeypatch.setattr(emulator, "MODEL_PATH", emulator.MODEL_PATH.with_name("missing.pt"))
    emulator.reset_emulator()
    client = TestClient(app)
    analysis = client.get("/demo").json()
    body = {"strategy_id": "current", "sowing_shift_days": 5, "irrigation_mm": 50, "crop_swap": None, "site": analysis["site"]}
    response = client.post("/whatif", json=body)
    emulator.reset_emulator()
    assert response.status_code == 200
    assert response.json()["method"] == "twin"


def test_explain_falls_back_to_template_when_ollama_down(monkeypatch):
    from app.ai import narrator

    def broken(messages):
        raise ConnectionError("ollama down")
        yield ""

    monkeypatch.setattr(narrator, "ollama_chunks", broken)
    client = TestClient(app)
    analysis = client.get("/demo").json()
    response = client.post("/explain", json={"strategy_id": "current", "analysis": analysis, "lang": "en"})
    assert response.status_code == 200
    assert "Data gaps" in response.text


def test_unknown_crop_is_reported_not_swapped():
    parsed = parse_rotation(["maize", "quinoa"])
    assert parsed.crops == ["maize"]
    assert "Unrecognized crop: quinoa" in parsed.gaps
    empty = parse_rotation(["quinoa"])
    assert empty.crops == ["fallow"] and empty.gaps


def test_double_crop_uses_rye_in_cold_climate():
    cold = {plan.strategy_id: plan.crops for plan in generate_alternatives(["maize", "soybean"], 120.0)}
    warm = {plan.strategy_id: plan.crops for plan in generate_alternatives(["maize", "beans"], 5.0)}
    assert cold["double_crop"] == ("soybean", "rye")
    assert warm["double_crop"] == ("beans", "oats")


def test_farm_demos_use_bundled_data(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "demo_path", lambda farm: tmp_path / f"demo_{farm}.json")
    client = TestClient(app)
    for farm, soil_hint in (("iowa", "SSURGO"), ("bajio", "SoilGrids")):
        parsed = AnalyzeResponse(**client.get("/demo", params={"farm": farm}).json())
        assert soil_hint in parsed.site.soil.source
        assert parsed.validation.fit and "soil_moisture_r" in parsed.validation.fit
        assert any("Soil" in line for line in parsed.strategies[0].evidence)
        assert any("Input costs" in gap for gap in parsed.strategies[0].gaps)
        assert any(src.name.startswith(("USDA", "ISRIC")) for src in parsed.sources)
    assert parsed.strategies[0].metrics["erosion_t_ha"].p50 < 8


def test_analyze_failure_keeps_request_point(monkeypatch):
    def broken(lat, lon):
        raise OSError("offline")

    monkeypatch.setattr(service, "load_site", broken)
    client = TestClient(app)
    body = {"lat": 35.0, "lon": -100.0, "current_rotation": ["maize", "quinoa"], "years": 3}
    analysis = client.post("/analyze", json=body).json()
    assert analysis["site"]["lat"] == 35.0 and analysis["site"]["lon"] == -100.0
    assert analysis["site"]["data_mode"] == "demo"
    gaps = analysis["strategies"][0]["gaps"]
    assert "Live NASA data unavailable for this point; demo farm climate used" in gaps
    assert "Unrecognized crop: quinoa" in gaps


def test_whatif_uses_request_rotation(monkeypatch):
    from app.ai import emulator

    monkeypatch.setattr(emulator, "MODEL_PATH", emulator.MODEL_PATH.with_name("missing.pt"))
    emulator.reset_emulator()
    client = TestClient(app)
    analysis = client.get("/demo", params={"farm": "bajio"}).json()
    seasons = [{"crop": "sorghum", "year_index": i, "start_month": 6, "end_month": 10} for i in range(3)]
    body = {"strategy_id": "current", "sowing_shift_days": 0, "irrigation_mm": 0, "crop_swap": None, "site": analysis["site"], "rotation": seasons}
    sorghum = client.post("/whatif", json=body).json()["metrics"]
    body.pop("rotation")
    default = client.post("/whatif", json=body).json()["metrics"]
    emulator.reset_emulator()
    assert sorghum["water_use_mm"] != default["water_use_mm"]


def test_n_balance_counts_fertilizer_and_income_is_net(demo_site):
    samples = build_samples(demo_site.weather, 20.52, 3, 8)
    params = SiteParams(20.52, 2.1, 0.24)
    maize = run_strategy(["maize"], samples, params, 3)
    assert np.median(maize.metrics["n_balance_kg_ha"]) > 0
    assert np.median(maize.metrics["income_index"]) < 100
