"""Spread values from a coarse lattice of sample points onto the fine grid."""
import numpy as np


def _weights(axis: np.ndarray, x: np.ndarray):
    """For each x: index of the lattice cell it falls in, and how far across it (0..1)."""
    i = np.clip(np.searchsorted(axis, x) - 1, 0, len(axis) - 2)
    t = np.clip((x - axis[i]) / (axis[i + 1] - axis[i]), 0.0, 1.0)
    return i, t


def bilinear(values: np.ndarray, lat_axis: np.ndarray, lon_axis: np.ndarray,
             grid_lat: np.ndarray, grid_lon: np.ndarray) -> np.ndarray:
    """values: (len(lat_axis), len(lon_axis)). Returns (len(grid_lat), len(grid_lon))."""
    ri, rt = _weights(lat_axis, grid_lat)
    ci, ct = _weights(lon_axis, grid_lon)
    ri, rt = ri[:, None], rt[:, None]
    ci, ct = ci[None, :], ct[None, :]
    top = values[ri, ci] * (1 - ct) + values[ri, ci + 1] * ct
    bottom = values[ri + 1, ci] * (1 - ct) + values[ri + 1, ci + 1] * ct
    return top * (1 - rt) + bottom * rt
