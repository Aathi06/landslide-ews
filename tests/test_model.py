import json

import numpy as np
import pytest

from config.regions import REGIONS
from src.model import susceptibility as sus
from src.model.evaluate import percentile_of, presence_background_auc, spatial_block_cv
from src.model.inventory import positive_cells, read_events
from src.model.predict import predict_risk
from src.model.trigger import caine_total_mm, event_rain_ratio, trigger_score
from src.terrain.grid import Grid

GRID = Grid.from_region(REGIONS["nilgiris"], 250)


def test_caine_thresholds():
    assert round(caine_total_mm(24)) == 103 and round(caine_total_mm(72)) == 201


def test_trigger_shape():
    assert trigger_score(0, 0) == 0
    assert np.isclose(trigger_score(caine_total_mm(24), 0), 0.5)             # exactly at the threshold
    rain = np.linspace(0, 400, 50)
    t = trigger_score(rain * 0.4, rain)
    assert (np.diff(t) >= 0).all() and t[-1] > 0.99                          # always rises with rain
    assert trigger_score(60, 100, scale=0.5) > trigger_score(60, 100, scale=1.0)   # lower scale = more sensitive


def test_risk_needs_both_ground_and_rain():
    s = np.array([0.1, 0.9])
    assert (predict_risk(s, 0, 0) == 0).all()                                # steep ground, no rain: no risk
    heavy = predict_risk(s, 200, 400)
    assert heavy[1] > heavy[0] and heavy[1] <= 0.9                           # never above susceptibility


def test_rank01_is_uniform():
    r = sus.rank01(np.random.default_rng(0).normal(size=1000))
    assert 0 < r.min() < 0.001 and 0.999 < r.max() < 1 and np.isclose(r.mean(), 0.5, atol=1e-6)


def test_auc_by_hand():
    assert presence_background_auc(np.arange(100.0), np.array([50.0])) == pytest.approx(0.5, abs=0.01)
    assert presence_background_auc(np.arange(100.0), np.array([200.0])) == 1.0
    assert percentile_of(np.sort(np.array([1.0, 1.0, 1.0])), np.array([1.0]))[0] == 0.5     # ties count half


def synthetic(n_pos=40, informative=True, seed=0):
    rng = np.random.default_rng(seed)
    n = GRID.n_cells
    r, c = np.divmod(np.arange(n), GRID.cols)
    slope = 20 + 10 * np.sin(r / 9) * np.cos(c / 11) + rng.normal(0, 2, n)
    feats = {"slope_mean": slope, "elevation": 1500 + 300 * np.cos(r / 20) + rng.normal(0, 30, n),
             "curvature": rng.normal(0, 0.002, n)}
    if informative:
        p = np.exp((slope - slope.mean()) / 2.5)
        pos = rng.choice(n, n_pos, replace=False, p=p / p.sum())      # landslides favour steep ground
    else:
        pos = rng.choice(n, n_pos, replace=False)
    return feats, np.unique(pos)


def test_model_learns_a_real_signal_and_not_a_fake_one():
    feats, pos = synthetic(informative=True)
    cv = spatial_block_cv(feats, pos, GRID)
    assert cv["fr_auc"] > 0.75 and cv["slope_auc"] > 0.75
    feats, pos = synthetic(informative=False, seed=3)
    assert spatial_block_cv(feats, pos, GRID)["fr_auc"] < 0.65               # no signal: stays near chance


def test_fit_and_score_roundtrip(tmp_path, monkeypatch):
    feats, pos = synthetic()
    model = sus.fit_fr(feats, pos)
    s = sus.score(model, feats)
    assert s.shape == (GRID.n_cells,) and 0 < s.min() and s.max() < 1
    assert s[pos].mean() > 0.6                                                # landslide cells rank above average
    monkeypatch.setattr(sus, "MODELS_DIR", tmp_path)
    sus.save_model(model, "demo")
    assert sus.load_model("demo")["method"] == "frequency_ratio" and sus.load_model("nothing") is None
    assert not sus.usable(model, {"slope_mean": feats["slope_mean"]})         # missing factors: cannot be applied


def test_inventory_reading(tmp_path):
    p = tmp_path / "l.csv"
    p.write_text("event_date,event_title,location_accuracy,admin_division_population,longitude,latitude\n"
                 "06/01/2017,a,5km,100,76.70,11.40\n"
                 "2009-11-10 00:00:00,b,25km,100,76.71,11.41\n"
                 "07/25/2013,c,exact,100,76.70,11.40\n"          # same 250 m cell as the first
                 "01/01/2010,d,exact,100,70.0,30.0\n")           # far outside the box
    r = REGIONS["nilgiris"]
    events = read_events(p, (r.south, r.north, r.west, r.east))
    assert len(events) == 3 and events[0].day.year == 2017 and events[1].day.year == 2009
    assert len(positive_cells(events, GRID)) == 1                             # 25 km event excluded, duplicates merged


def test_event_rain_ratio():
    rain = np.zeros(120)
    rain[100:108] = 15.0                                                      # 120 mm in 8 h on the event day
    r24, r72, ratio = event_rain_ratio(rain, 96)
    assert r24 == 120 and r72 == 120 and ratio == pytest.approx(120 / caine_total_mm(24))
    assert event_rain_ratio(np.zeros(120), 96)[2] == 0


def test_context_uses_trained_model_only_on_real_terrain(tmp_path, monkeypatch):
    from src import context
    from src.terrain import build as build_mod
    feats, pos = synthetic()
    full = {k: v.astype(np.float32) for k, v in feats.items()}
    for name in ("relief", "slope_max", "aspect_sin", "aspect_cos"):
        full[name] = np.zeros(GRID.n_cells, dtype=np.float32)
    monkeypatch.setattr(build_mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(sus, "MODELS_DIR", tmp_path)
    build_mod.save_features(REGIONS["nilgiris"], GRID, full)
    sus.save_model(sus.fit_fr(full, pos), "nilgiris")

    context.load_region_context.cache_clear()
    assert context.load_region_context("nilgiris").model_method == "slope_rank"        # tests run on mock terrain
    monkeypatch.setattr(context, "TERRAIN_MODE", "auto")
    context.load_region_context.cache_clear()
    ctx = context.load_region_context("nilgiris")
    assert ctx.terrain_source == "real" and ctx.model_method == "frequency_ratio"
    assert ctx.susceptibility.shape == (GRID.n_cells,)
    context.load_region_context.cache_clear()
