"""Terrain features computed from a DEM array."""
import numpy as np


def slope_degrees(dem: np.ndarray, cell_m: float) -> np.ndarray:
    """Slope in degrees for every cell: arctan of the height gradient.
    dem: (rows, cols) metres. Returns the same shape."""
    dz_dy, dz_dx = np.gradient(dem, cell_m)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def terrain_derivatives(dem: np.ndarray, dy_m: float, dx_m: float):
    """Slope, aspect and curvature of a DEM whose row 0 is the NORTH edge.

    dem: (H, W) metres. dy_m / dx_m: pixel height / width in metres.
    Returns three arrays shaped like dem:
      slope_deg  : steepness, 0 flat to 90 vertical
      aspect_deg : compass direction the slope faces (downhill), 0 = north, 90 = east, clockwise
      curvature  : sum of second derivatives (1/m). Positive = concave (a bowl that collects water),
                   negative = convex (a ridge that sheds it)
    """
    dz_drow, dz_dx = np.gradient(dem, dy_m, dx_m)       # rows run north to south, columns west to east
    dz_dnorth = -dz_drow
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dnorth)))
    aspect = np.degrees(np.arctan2(-dz_dx, -dz_dnorth)) % 360     # direction of steepest DESCENT
    curvature = np.gradient(dz_dx, dx_m, axis=1) + np.gradient(dz_drow, dy_m, axis=0)
    return slope, aspect, curvature
