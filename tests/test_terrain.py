import math

import numpy as np
import pytest

from config.regions import REGIONS
from src.terrain import build as build_mod
from src.terrain.aggregate import FEATURE_NAMES, aggregate_to_grid
from src.terrain.dem import DemRaster, tile_name, tiles_for_region
from src.terrain.features import terrain_derivatives
from src.terrain.grid import Grid

M_PER_DEG = 111_320.0
PX = 30.0                                          # pixel size in metres for the pure-numpy tests


def plane(rows=40, cols=40, rise_east=0.0, rise_north=0.0):
    """Elevation where height grows by `rise_east` m per metre eastward and `rise_north` northward. Row 0 = north."""
    r, c = np.mgrid[0:rows, 0:cols]
    return rise_east * c * PX + rise_north * (rows - 1 - r) * PX


def test_slope_aspect_of_planes():
    inner = (slice(5, -5), slice(5, -5))
    slope, aspect, curv = terrain_derivatives(plane(rise_east=math.tan(math.radians(30))), PX, PX)
    assert np.allclose(slope[inner], 30, atol=0.01)
    assert np.allclose(aspect[inner], 270, atol=0.01)           # rises to the east, so it faces west
    assert np.allclose(curv[inner], 0, atol=1e-9)

    _, aspect_n, _ = terrain_derivatives(plane(rise_north=math.tan(math.radians(20))), PX, PX)
    assert np.allclose(aspect_n[inner], 180, atol=0.01)         # rises to the north, so it faces south
    _, aspect_w, _ = terrain_derivatives(plane(rise_east=-0.5), PX, PX)
    assert np.allclose(aspect_w[inner], 90, atol=0.01)          # falls to the east, so it faces east


def test_bowl_is_concave_and_ridge_is_convex():
    r, c = np.mgrid[-20:20, -20:20]
    bowl = 0.001 * ((r * PX) ** 2 + (c * PX) ** 2)
    _, _, curv = terrain_derivatives(bowl, PX, PX)
    assert np.allclose(curv[5:-5, 5:-5], 4 * 0.001, rtol=1e-6)  # laplacian of k(x^2+y^2) is 4k, positive
    _, _, ridge = terrain_derivatives(-bowl, PX, PX)
    assert (ridge[5:-5, 5:-5] < 0).all()


def test_tile_naming():
    assert tile_name(11.4, 76.7) == "Copernicus_DSM_COG_10_N11_00_E076_00_DEM"
    assert tile_name(-3.2, -60.5) == "Copernicus_DSM_COG_10_S04_00_W061_00_DEM"
    assert tiles_for_region(REGIONS["nilgiris"]) == [(11, 76)]
    assert sorted(tiles_for_region(REGIONS["wayanad"])) == [(11, 75), (11, 76)]


def synthetic_raster(region, grid, deg_slope=30.0):
    """A 30 m DEM covering the region plus margin, shaped as a plane rising eastward."""
    d = 1 / 3600
    pad = 0.003
    west, north = region.west - pad, region.north + pad
    W = int((region.east - region.west + 2 * pad) / d)
    H = int((region.north - region.south + 2 * pad) / d)
    mid_lat = north - d * H / 2
    cols = np.arange(W)
    east_m = cols * d * M_PER_DEG * math.cos(math.radians(mid_lat))
    elev = np.tile(math.tan(math.radians(deg_slope)) * east_m, (H, 1)) + 500
    return DemRaster(elev, west, north, d, d)


def test_aggregate_plane_to_grid():
    region = REGIONS["nilgiris"]
    grid = Grid.from_region(region, 250)
    raster = synthetic_raster(region, grid)
    H = raster.elevation.shape[0]
    mid_lat = raster.north - raster.dlat * H / 2
    slope, aspect, curv = terrain_derivatives(raster.elevation, raster.dlat * M_PER_DEG,
                                              raster.dlon * M_PER_DEG * math.cos(math.radians(mid_lat)))
    f = aggregate_to_grid(grid, raster, slope, aspect, curv)
    assert set(f) == set(FEATURE_NAMES) and all(v.shape == (grid.n_cells,) for v in f.values())
    assert np.allclose(f["slope_mean"], 30, atol=0.3) and np.allclose(f["slope_max"], 30, atol=0.3)
    assert np.allclose(f["aspect_sin"], -1, atol=0.01) and np.allclose(f["aspect_cos"], 0, atol=0.02)  # faces west
    elev = f["elevation"].reshape(grid.rows, grid.cols)
    assert (np.diff(elev, axis=1) > 0).all()                    # higher towards the east
    assert (f["relief"] > 0).all()


def test_aggregate_rejects_a_dem_that_misses_part_of_the_region():
    region = REGIONS["nilgiris"]
    grid = Grid.from_region(region, 250)
    raster = synthetic_raster(region, grid)
    cropped = DemRaster(raster.elevation[:, : raster.elevation.shape[1] // 2], raster.west, raster.north,
                        raster.dlon, raster.dlat)
    z = np.zeros_like(cropped.elevation)
    with pytest.raises(ValueError):
        aggregate_to_grid(grid, cropped, z, z, z)


def write_geotiff(path, raster):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin
    H, W = raster.elevation.shape
    with rasterio.open(path, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(raster.west, raster.north, raster.dlon, raster.dlat)) as dst:
        dst.write(raster.elevation.astype("float32"), 1)


def test_full_pipeline_from_a_geotiff_file(tmp_path, monkeypatch):
    pytest.importorskip("rasterio")
    region = REGIONS["nilgiris"]
    grid = Grid.from_region(region, 250)
    write_geotiff(tmp_path / "dem_nilgiris.tif", synthetic_raster(region, grid, 25.0))   # manual-file route, no network
    feats = build_mod.build_static_features(region, grid, raw_dir=tmp_path)
    assert np.allclose(feats["slope_mean"], 25, atol=0.4)

    monkeypatch.setattr(build_mod, "CACHE_DIR", tmp_path / "cache")
    assert build_mod.load_cached_features(region, grid) is None             # nothing cached yet
    build_mod.save_features(region, grid, feats)
    loaded = build_mod.load_cached_features(region, grid)
    assert loaded is not None and np.allclose(loaded["slope_mean"], feats["slope_mean"])
    assert build_mod.load_cached_features(region, Grid.from_region(region, 500)) is None    # different grid: rejected


def test_context_uses_cached_real_terrain_when_present(tmp_path, monkeypatch):
    from src import context
    region = REGIONS["nilgiris"]
    grid = Grid.from_region(region, 250)
    monkeypatch.setattr(build_mod, "CACHE_DIR", tmp_path)
    context.load_region_context.cache_clear()
    assert context.load_region_context("nilgiris").terrain_source == "mock"          # tests run in mock mode

    feats = {name: np.full(grid.n_cells, 10.0, dtype=np.float32) for name in FEATURE_NAMES}
    feats["slope_mean"] = np.linspace(0, 40, grid.n_cells).astype(np.float32)
    build_mod.save_features(region, grid, feats)
    monkeypatch.setattr(context, "TERRAIN_MODE", "auto")
    context.load_region_context.cache_clear()
    ctx = context.load_region_context("nilgiris")
    assert ctx.terrain_source == "real" and np.allclose(ctx.slope, feats["slope_mean"]) and len(ctx.villages) > 0
    context.load_region_context.cache_clear()
