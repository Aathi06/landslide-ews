"""Everything static about one region, built once and cached."""
import zlib
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from config.regions import REGIONS
from config.settings import CELL_M, TERRAIN_MODE
from src.exposure.villages import Village, pick_placeholder_villages
from src.terrain.build import build_and_cache, load_cached_features
from src.terrain.dem import make_mock_dem
from src.terrain.features import slope_degrees
from src.terrain.grid import Grid


@dataclass(frozen=True)
class RegionContext:
    grid: Grid
    slope: np.ndarray            # flat, one value per cell (degrees): the slope the risk model uses
    villages: list[Village]
    features: dict               # name -> flat array, one value per cell
    terrain_source: str          # "real" (Copernicus DEM) or "mock" (synthetic)


@lru_cache(maxsize=8)
def load_region_context(key: str) -> RegionContext:
    region = REGIONS[key]
    grid = Grid.from_region(region, CELL_M)
    seed = zlib.crc32(key.encode())                  # stable per region

    features = None
    if TERRAIN_MODE in ("auto", "real"):
        features = load_cached_features(region, grid)
        if features is None and TERRAIN_MODE == "real":
            features = build_and_cache(region, grid)         # downloads the DEM; raises if impossible
    if features is not None:
        slope, source = features["slope_mean"].astype(float), "real"
    else:
        dem = make_mock_dem(grid, seed)
        slope = slope_degrees(dem, grid.cell_m).ravel()
        features = {"elevation": dem.ravel(), "slope_mean": slope, "slope_max": slope}
        source = "mock"
    return RegionContext(grid, slope, pick_placeholder_villages(grid, slope, seed), features, source)
