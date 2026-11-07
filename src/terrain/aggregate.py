"""Collapse 30 m pixels onto the 250 m dashboard grid."""
import numpy as np

from .dem import DemRaster
from .grid import Grid

FEATURE_NAMES = ("elevation", "relief", "slope_mean", "slope_max", "aspect_sin", "aspect_cos", "curvature")


def aggregate_to_grid(grid: Grid, raster: DemRaster, slope: np.ndarray, aspect: np.ndarray,
                      curvature: np.ndarray) -> dict[str, np.ndarray]:
    """One value per grid cell (flat, row-major, south to north) for every feature in FEATURE_NAMES.
    Slope is computed on the fine pixels FIRST and only then summarised, so steep spots are not smoothed away.
      elevation: mean height   relief: highest minus lowest pixel in the cell
      slope_mean / slope_max : mean and steepest pixel slope
      aspect_sin / aspect_cos: average facing direction (flat pixels, slope < 1 degree, count as no direction)
      curvature: mean curvature"""
    H, W = raster.elevation.shape
    lat = raster.north - (np.arange(H) + 0.5) * raster.dlat
    lon = raster.west + (np.arange(W) + 0.5) * raster.dlon
    row = np.floor((lat - grid.region.south) / grid.dlat).astype(int)
    col = np.floor((lon - grid.region.west) / grid.dlon).astype(int)
    mask = ((row >= 0) & (row < grid.rows))[:, None] & ((col >= 0) & (col < grid.cols))[None, :]
    cell = (row[:, None] * grid.cols + col[None, :])[mask]
    n = grid.n_cells

    count = np.bincount(cell, minlength=n)
    if count.min() == 0:
        raise ValueError("the DEM does not cover the whole region")

    def mean(a: np.ndarray) -> np.ndarray:
        return np.bincount(cell, weights=a[mask], minlength=n) / count

    elev = raster.elevation
    hi = np.full(n, -np.inf)
    lo = np.full(n, np.inf)
    smax = np.zeros(n)
    np.maximum.at(hi, cell, elev[mask])
    np.minimum.at(lo, cell, elev[mask])
    np.maximum.at(smax, cell, slope[mask])

    facing = slope >= 1.0
    rad = np.radians(aspect)
    out = dict(
        elevation=mean(elev), relief=hi - lo,
        slope_mean=mean(slope), slope_max=smax,
        aspect_sin=mean(np.where(facing, np.sin(rad), 0.0)),
        aspect_cos=mean(np.where(facing, np.cos(rad), 0.0)),
        curvature=mean(curvature),
    )
    return {k: v.astype(np.float32) for k, v in out.items()}
