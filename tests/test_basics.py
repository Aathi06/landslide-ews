import numpy as np
from fastapi.testclient import TestClient

from api.main import app
from src.context import load_region_context
from src.model.predict import predict_risk
from src.scenario import run_storm
from src.terrain.features import slope_degrees


def test_slope_of_a_45_degree_plane():
    cell = 250
    dem = np.tile(np.arange(20) * cell, (20, 1)).astype(float)   # rises one cell-width per cell
    assert np.allclose(slope_degrees(dem, cell)[5:-5, 5:-5], 45, atol=0.01)


def test_more_rain_never_lowers_risk():
    slope = np.linspace(0, 45, 200)
    low = predict_risk(slope, 20, 60)
    high = predict_risk(slope, 80, 200)
    assert (high >= low).all()


def test_steeper_is_riskier_at_equal_rain():
    r = predict_risk(np.array([10.0, 30.0, 40.0]), 50, 150)
    assert r[0] < r[1] < r[2]


def test_storm_peak_grows_with_total_rain():
    slope = load_region_context("nilgiris").slope
    peaks = [max(f.mean() for f in run_storm(slope, mm, 48, "burst").risk_frames) for mm in (0, 100, 200, 300)]
    assert peaks == sorted(peaks)


def test_api_routes():
    c = TestClient(app)
    assert {r["key"] for r in c.get("/api/regions").json()} == {"nilgiris", "wayanad"}
    for key in ("nilgiris", "wayanad"):
        s = c.get("/api/static", params={"region": key}).json()
        assert s["rows"] * s["cols"] > 10_000 and len(s["villages"]) > 0
        assert c.get("/api/simulate", params={"region": key}).status_code == 200
    assert c.get("/api/static", params={"region": "nowhere"}).status_code == 404
