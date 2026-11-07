import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from config.regions import REGIONS
from src.context import load_region_context
from src.rainfall import live as live_mod
from src.rainfall.features import rolling_total
from src.rainfall.interpolate import bilinear
from src.rainfall.live import LiveRain, LiveUnavailable, get_live_rain, lattice_axes, parse_open_meteo
from src.scenario import run_live

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
NOW = T0 + timedelta(hours=168)             # 7 days of history, 3 days of forecast
HOURS = 240
TIMES = [(T0 + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(HOURS)]


def fake_payload(n_points=25, storm=(150, 165), mm=10.0):
    rain = [0.0] * HOURS
    for h in range(*storm):
        rain[h] = mm
    rain[5] = None                          # the API can return nulls
    return [{"hourly": {"time": TIMES, "precipitation": list(rain)}} for _ in range(n_points)]


def fake_live(**kw):
    times, rain = parse_open_meteo(fake_payload(**kw), 25)
    lat, lon = lattice_axes(REGIONS["nilgiris"])
    return LiveRain(times, rain, lat, lon, NOW, stale=False)


def test_rolling_total_matches_hand_calc():
    r = np.array([[1, 2, 3, 4, 5.0]])
    assert rolling_total(r, 2).tolist() == [[1, 3, 5, 7, 9]]


def test_bilinear_reproduces_a_plane():
    lat, lon = np.linspace(0, 4, 5), np.linspace(10, 14, 5)
    v = 2 * lat[:, None] + 3 * lon[None, :]
    glat, glon = np.array([0.5, 1.7, 3.9]), np.array([10.2, 12.6, 13.9])
    assert np.allclose(bilinear(v, lat, lon, glat, glon), 2 * glat[:, None] + 3 * glon[None, :])


def test_parse_handles_nulls_and_single_location():
    times, rain = parse_open_meteo(fake_payload(), 25)
    assert rain.shape == (25, HOURS) and rain[0, 5] == 0.0
    _, single = parse_open_meteo(fake_payload(n_points=1)[0], 1)   # single location comes back as a dict
    assert single.shape == (1, HOURS)
    with pytest.raises(ValueError):
        parse_open_meteo(fake_payload(n_points=3), 25)


def test_live_risk_rises_after_a_storm():
    ctx = load_region_context("nilgiris")
    res = run_live(ctx.susceptibility, ctx.grid, fake_live(), now=NOW)
    assert res.offsets[res.now_frame] == 0 and min(res.offsets) >= -72 and max(res.offsets) <= 48
    assert res.risk_frames[res.now_frame].mean() > res.risk_frames[0].mean()


def test_dry_week_stays_calm():
    ctx = load_region_context("nilgiris")
    res = run_live(ctx.susceptibility, ctx.grid, fake_live(mm=0.0), now=NOW)
    assert max(f.max() for f in res.risk_frames) < 50


def test_cache_fallback_marks_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(live_mod, "CACHE_DIR", tmp_path)
    region = REGIONS["nilgiris"]
    (tmp_path / "live_nilgiris.json").write_text(
        json.dumps({"fetched_at": (NOW - timedelta(hours=3)).isoformat(), "payload": fake_payload()}))

    def boom(*a, **k):
        raise RuntimeError("offline")
    monkeypatch.setattr(live_mod, "fetch_raw", boom)
    got = get_live_rain(region, now=NOW)
    assert got.stale is True and got.rain.shape == (25, HOURS)

    (tmp_path / "live_nilgiris.json").unlink()
    with pytest.raises(LiveUnavailable):
        get_live_rain(region, now=NOW)


def test_fresh_fetch_writes_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(live_mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(live_mod, "fetch_raw", lambda lats, lons: fake_payload(len(lats)))
    got = get_live_rain(REGIONS["nilgiris"], now=NOW)
    assert got.stale is False and (tmp_path / "live_nilgiris.json").exists()


def test_live_endpoint(monkeypatch):
    c = TestClient(api_main.app)
    monkeypatch.setattr(api_main, "get_live_rain", lambda region, refresh=False: fake_live())
    body = c.get("/api/live").json()
    assert body["stale"] is False and 0 <= body["now_frame"] < len(body["frames"])

    def down(region, refresh=False):
        raise LiveUnavailable("no network")
    monkeypatch.setattr(api_main, "get_live_rain", down)
    assert c.get("/api/live").status_code == 503
