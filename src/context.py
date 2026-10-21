"""Everything static about one region, built once and cached."""
import zlib
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from config.regions import REGIONS
from config.settings import CELL_M
from src.exposure.villages import Village, pick_placeholder_villages
from src.terrain.dem import make_mock_dem
from src.terrain.features import slope_degrees
from src.terrain.grid import Grid


@dataclass(frozen=True)
class RegionContext:
    grid: Grid
    slope: np.ndarray            # flat, one value per cell (degrees)
    villages: list[Village]


@lru_cache(maxsize=8)
def load_region_context(key: str) -> RegionContext:
    region = REGIONS[key]
    grid = Grid.from_region(region, CELL_M)
    seed = zlib.crc32(key.encode())                  # stable per region
    dem = make_mock_dem(grid, seed)                  # day 2: load the real DEM here
    slope = slope_degrees(dem, grid.cell_m).ravel()
    return RegionContext(grid, slope, pick_placeholder_villages(grid, slope, seed))
