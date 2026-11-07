"""Roads cut, stranded settlements, alert timeline, cached villages, and the new API routes."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

nx = pytest.importorskip("networkx")

from config.regions import Region
from src.exposure.osm_villages import cell_of, load_cached_villages
from src.exposure.villages import Village
from src.impact import alert_timeline, peak_frame_index, road_impact, send_alerts, sending_enabled
from src.roads import assets as road_assets
from src.roads.assets import RoadAssets, RoadsUnavailable
from src.terrain.grid import Grid

X0, Y0, STEP = 76.0, 11.0, 0.01
REGION = Region("t", "Test", 10.95, 11.10, 75.95, 76.10)
GRID = Grid.from_region(REGION, 2000)


def lattice():
    """3x3 junctions, every road 1000 m, two-way (same shape as tests/test_roads.py)."""
    G = nx.MultiDiGraph()
    for i in range(3):
        for j in range(3):
            G.add_node((i, j), x=X0 + STEP * i, y=Y0 + STEP * j)
    for i in range(3):
        for j in range(3):
            for di, dj in ((1, 0), (0, 1)):
                if i + di < 3 and j + dj < 3:
                    G.add_edge((i, j), (i + di, j + dj), length=1000.0)
                    G.add_edge((i + di, j + dj), (i, j), length=1000.0)
    return G


def ctx_with(villages):
    return SimpleNamespace(grid=GRID, villages=villages)


FAR = Village("Far", 400, 0, X0 + 2 * STEP, Y0 + 2 * STEP)
NEAR = Village("Near", 900, 0, X0 + STEP, Y0)
ASSETS = RoadAssets(lattice(), [(X0, Y0)])


def frame_of(value):
    return np.full(GRID.n_cells, value, dtype=np.uint8)


def test_peak_frame_is_the_one_with_most_alerted_cells():
    frames = [frame_of(10), frame_of(80), frame_of(95), frame_of(40)]
    assert peak_frame_index(frames) == 1                         # ties go to the earliest frame
    assert peak_frame_index(frames, start=2) == 2


def test_calm_storm_cuts_nothing_and_strands_nobody():
    r = road_impact(ctx_with([FAR, NEAR]), ASSETS, frame_of(10))
    assert r["available"] and r["cut_edges"] == 0 and r["cut_pct"] == 0.0
    assert r["isolated"] == [] and r["segments"] == []
    assert all(v["extra_km"] == 0 for v in r["villages"])


def test_severe_storm_cuts_every_road_once_per_pair_and_strands_both():
    r = road_impact(ctx_with([FAR, NEAR]), ASSETS, frame_of(100))
    assert r["cut_edges"] == r["total_edges"] == 24               # 12 roads, two directions each
    assert len(r["segments"]) == 12                               # drawn once per road, not twice
    assert sorted(r["isolated"]) == ["Far", "Near"]
    json.dumps(r, allow_nan=False)                                # no inf/nan may reach the browser


def test_impact_is_json_safe_even_for_a_village_never_connected():
    G = lattice()
    G.add_node("island", x=X0 + 0.5, y=Y0 + 0.5)
    lone = Village("Lone", 50, 0, X0 + 0.5, Y0 + 0.5)
    r = road_impact(ctx_with([lone]), RoadAssets(G, [(X0, Y0)]), frame_of(10))
    assert r["isolated"] == ["Lone"] and r["villages"][0]["baseline_km"] is None
    json.dumps(r, allow_nan=False)


def test_alert_timeline_fires_each_level_once_per_language_and_never_sends():
    v = Village("V", 1000, 5, X0, Y0)
    frames = [frame_of(10), frame_of(60), frame_of(60), frame_of(80), frame_of(95)]
    out = alert_timeline([v], frames, langs=("en", "ta"))
    assert [(a["frame"], a["level"], a["lang"]) for a in out] == [
        (1, "watch", "en"), (1, "watch", "ta"), (3, "warning", "en"), (3, "warning", "ta"),
        (4, "emergency", "en"), (4, "emergency", "ta")]
    assert not any(a["delivered"] for a in out)
    assert all(a["text"] for a in out)


def test_alert_timeline_window():
    v = Village("V", 1000, 5, X0, Y0)
    frames = [frame_of(90), frame_of(90), frame_of(90)]
    assert alert_timeline([v], frames, start=1, end=1, langs=("en",))[0]["frame"] == 1


def test_sending_needs_explicit_opt_in_and_credentials(monkeypatch):
    for k in ("EWS_ALERTS_SEND", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(k, raising=False)
    assert not sending_enabled()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x"); monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    assert not sending_enabled()                                  # credentials alone are not consent
    monkeypatch.setenv("EWS_ALERTS_SEND", "1")
    assert sending_enabled()


def test_send_alerts_is_a_dry_run_by_default(monkeypatch):
    for k in ("EWS_ALERTS_SEND", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(k, raising=False)
    from src.context import load_region_context
    ctx = load_region_context("nilgiris")
    frames = [np.full(ctx.grid.n_cells, 90, dtype=np.uint8)]
    for _ in range(2):                                            # a dry run can be repeated: nothing is "used up"
        res = send_alerts("nilgiris", frames, 0, "sim", ("en", "ta"))
        assert res["enabled"] is False and res["delivered"] == 0
        assert res["count"] == 2 * len(ctx.villages)


# ------------------------------------------------------------------ cached villages and road assets
def test_cell_of_inside_and_outside():
    assert cell_of(GRID, REGION.west + GRID.dlon * 2.5, REGION.south + GRID.dlat * 1.5) == 1 * GRID.cols + 2
    assert cell_of(GRID, REGION.west - 1, REGION.south) is None


def test_cached_villages_round_trip_and_bad_files(tmp_path, monkeypatch):
    path = tmp_path / "v.json"
    monkeypatch.setattr("src.exposure.osm_villages.villages_path", lambda region: path)
    assert load_cached_villages(REGION, GRID) is None             # no file
    path.write_text(json.dumps([
        dict(name="Kotagiri", pop=28000, lon=76.0, lat=11.0, place="town"),
        dict(name="Elsewhere", pop=10, lon=10.0, lat=10.0, place="hamlet")]))
    vs = load_cached_villages(REGION, GRID)
    assert [v.name for v in vs] == ["Kotagiri"]                   # the one outside the grid is dropped
    assert vs[0].cell == cell_of(GRID, 76.0, 11.0)
    path.write_text("{not json")
    assert load_cached_villages(REGION, GRID) is None             # corrupt cache falls back, never crashes


def test_context_keeps_placeholders_on_synthetic_terrain():
    from src.context import load_region_context
    assert load_region_context("nilgiris").villages_source == "placeholder"


def test_roads_unavailable_without_a_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(road_assets, "CACHE_DIR", tmp_path)
    road_assets._LOADED.pop("t", None)
    with pytest.raises(RoadsUnavailable, match="build_roads"):
        road_assets.load_road_assets(REGION)


# ------------------------------------------------------------------ API routes
@pytest.fixture
def client(monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    for k in ("EWS_ALERTS_SEND", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(k, raising=False)

    def no_roads(region):
        raise RoadsUnavailable("test: no roads")
    monkeypatch.setattr("src.impact.load_road_assets", no_roads)
    from api.main import app
    return fastapi_testclient.TestClient(app)


def test_static_reports_new_flags(client):
    s = client.get("/api/static").json()
    assert s["villages_source"] == "placeholder" and s["alerts_send_enabled"] is False
    assert isinstance(s["roads_ready"], bool)


def test_impact_endpoint_without_roads_still_returns_alerts(client):
    d = client.get("/api/impact", params=dict(total_mm=400, hours=12, pattern="burst")).json()
    assert d["roads"] == dict(available=False, reason="test: no roads")
    assert isinstance(d["peak_frame"], int) and isinstance(d["alerts"], list)
    assert {"frame", "village", "level", "lang", "text", "delivered"} <= set(d["alerts"][0]) if d["alerts"] else True


def test_alerts_send_endpoint_is_a_dry_run_and_validates_input(client):
    ok = client.post("/api/alerts/send", params=dict(total_mm=400, hours=12, langs="en,hi")).json()
    assert ok["enabled"] is False and ok["delivered"] == 0
    assert client.post("/api/alerts/send", params=dict(langs="xx")).status_code == 400
    assert client.get("/api/impact", params=dict(mode="bogus")).status_code == 400
    assert client.get("/api/impact", params=dict(region="nowhere")).status_code == 404
