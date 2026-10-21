"""Terrain features computed from a DEM array. Day 2 adds aspect and curvature."""
import numpy as np


def slope_degrees(dem: np.ndarray, cell_m: float) -> np.ndarray:
    """Slope in degrees for every cell: arctan of the height gradient.
    dem: (rows, cols) metres. Returns the same shape."""
    dz_dy, dz_dx = np.gradient(dem, cell_m)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
