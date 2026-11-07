"""Build, cache and load the static terrain feature table for a region."""
import math
from pathlib import Path

import numpy as np

from config.regions import Region
from config.settings import CACHE_DIR, RAW_DIR
from src.terrain.aggregate import FEATURE_NAMES, aggregate_to_grid
from src.terrain.dem import load_real_dem
from src.terrain.features import terrain_derivatives
from src.terrain.grid import Grid

M_PER_DEG = 111_320.0


def cache_path(region: Region) -> Path:
    return CACHE_DIR / f"static_{region.key}.npz"


def build_static_features(region: Region, grid: Grid, raw_dir: Path = RAW_DIR) -> dict[str, np.ndarray]:
    """Real DEM -> slope, aspect, curvature at native resolution -> one row per grid cell."""
    raster = load_real_dem(region, raw_dir)
    H = raster.elevation.shape[0]
    mid_lat = raster.north - raster.dlat * H / 2
    dy_m = raster.dlat * M_PER_DEG
    dx_m = raster.dlon * M_PER_DEG * math.cos(math.radians(mid_lat))
    slope, aspect, curvature = terrain_derivatives(raster.elevation, dy_m, dx_m)
    return aggregate_to_grid(grid, raster, slope, aspect, curvature)


def save_features(region: Region, grid: Grid, features: dict[str, np.ndarray]) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(region)
    np.savez_compressed(path, rows=grid.rows, cols=grid.cols, cell_m=grid.cell_m, **features)
    return path


def load_cached_features(region: Region, grid: Grid) -> dict[str, np.ndarray] | None:
    """The cached table, or None if missing or built for a different grid."""
    path = cache_path(region)
    if not path.exists():
        return None
    try:
        with np.load(path) as z:
            if (int(z["rows"]), int(z["cols"]), int(z["cell_m"])) != (grid.rows, grid.cols, grid.cell_m):
                return None
            return {name: z[name] for name in FEATURE_NAMES}
    except (OSError, KeyError, ValueError):
        return None


def build_and_cache(region: Region, grid: Grid, raw_dir: Path = RAW_DIR) -> dict[str, np.ndarray]:
    features = build_static_features(region, grid, raw_dir)
    save_features(region, grid, features)
    return features
