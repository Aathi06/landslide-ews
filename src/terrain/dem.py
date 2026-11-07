"""Elevation sources: synthetic (tests, offline) and real Copernicus GLO-30 at 30 m."""
import math
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np

from config.regions import Region
from config.settings import DEM_BASE_URL, DEM_PAD_DEG, RAW_DIR
from .grid import Grid


class TerrainUnavailable(Exception):
    """The real DEM could not be downloaded or read."""


# ------------------------------------------------------------------ synthetic
def make_mock_dem(grid: Grid, seed: int) -> np.ndarray:
    """Fake mountains from random sine ridges, rescaled so the steepest 5% of
    cells sit near 38 degrees. Returns elevation in metres, shape (rows, cols)."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:grid.rows, 0:grid.cols]
    dem = np.zeros((grid.rows, grid.cols))
    for wavelength, amp in [(160, 3.0), (80, 2.0), (40, 1.2), (18, 0.6)]:
        for _ in range(3):
            ang, phase = rng.uniform(0, np.pi), rng.uniform(0, 2 * np.pi)
            k = 2 * np.pi / wavelength
            dem += amp * np.sin(k * (x * np.cos(ang) + y * np.sin(ang)) + phase)
    gy, gx = np.gradient(dem, 1.0)
    steep = np.percentile(np.hypot(gx, gy), 95)
    return dem * math.tan(math.radians(38)) / steep * grid.cell_m


# ----------------------------------------------------------------------- real
@dataclass(frozen=True)
class DemRaster:
    """A DEM at its native resolution. elevation[0, 0] is the north-west pixel."""
    elevation: np.ndarray     # (H, W) metres
    west: float               # lon of the raster's west edge
    north: float              # lat of the raster's north edge
    dlon: float               # pixel width in degrees
    dlat: float               # pixel height in degrees


def tile_name(lat: float, lon: float) -> str:
    """Copernicus tiles are 1x1 degree and named after their SOUTH-WEST corner."""
    la, lo = math.floor(lat), math.floor(lon)
    return (f"Copernicus_DSM_COG_10_{'N' if la >= 0 else 'S'}{abs(la):02d}_00_"
            f"{'E' if lo >= 0 else 'W'}{abs(lo):03d}_00_DEM")


def tiles_for_region(region: Region, pad: float = DEM_PAD_DEG) -> list[tuple[int, int]]:
    lats = range(math.floor(region.south - pad), math.floor(region.north + pad) + 1)
    lons = range(math.floor(region.west - pad), math.floor(region.east + pad) + 1)
    return [(la, lo) for la in lats for lo in lons]


def ensure_tile(lat_i: int, lon_i: int, raw_dir: Path = RAW_DIR) -> Path:
    """Path to a tile on disk, downloading it on first use."""
    name = tile_name(lat_i, lon_i)
    path = raw_dir / f"{name}.tif"
    if path.exists():
        return path
    url = f"{DEM_BASE_URL}/{name}/{name}.tif"
    raw_dir.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".part")
    try:
        with httpx.stream("GET", url, timeout=60, follow_redirects=True) as r:
            r.raise_for_status()
            with open(part, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
    except httpx.HTTPError as err:
        part.unlink(missing_ok=True)
        raise TerrainUnavailable(
            f"Could not download {url} ({err}). As a fallback, download a DEM that covers the region "
            f"(EPSG:4326 GeoTIFF) and save it as {raw_dir}/dem_<region key>.tif") from err
    part.replace(path)
    return path


def load_real_dem(region: Region, raw_dir: Path = RAW_DIR) -> DemRaster:
    """Real elevation for the region (plus a small margin), merged from one or more tiles.
    A GeoTIFF placed by hand at data/raw/dem_<region key>.tif takes priority over downloading."""
    import rasterio
    from rasterio.merge import merge

    manual = raw_dir / f"dem_{region.key}.tif"
    paths = [manual] if manual.exists() else [ensure_tile(la, lo, raw_dir) for la, lo in tiles_for_region(region)]
    sources = [rasterio.open(p) for p in paths]
    try:
        for s in sources:
            if s.crs is None or not s.crs.is_geographic:
                raise TerrainUnavailable(f"{s.name} must use lat/lon coordinates (EPSG:4326)")
        bounds = (region.west - DEM_PAD_DEG, region.south - DEM_PAD_DEG,
                  region.east + DEM_PAD_DEG, region.north + DEM_PAD_DEG)
        data, transform = merge(sources, bounds=bounds)
        nodata = sources[0].nodata
    finally:
        for s in sources:
            s.close()
    elevation = data[0].astype("float64")
    if nodata is not None:
        elevation[elevation == nodata] = np.nan
    if np.isnan(elevation).any():                       # rare voids: fill so gradients stay finite
        elevation[np.isnan(elevation)] = np.nanmean(elevation)
    return DemRaster(elevation, transform.c, transform.f, transform.a, -transform.e)
