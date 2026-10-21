"""Elevation source. Day 1: synthetic. Day 2: replaced by a real DEM loader."""
import math

import numpy as np

from .grid import Grid


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
