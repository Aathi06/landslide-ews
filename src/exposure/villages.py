"""Settlements at risk. Day 1: placeholders. Day 5: real villages from OpenStreetMap."""
import math
import string
from dataclasses import dataclass

import numpy as np

from src.terrain.grid import Grid


@dataclass(frozen=True)
class Village:
    name: str
    pop: int
    cell: int       # flat index into the grid
    lon: float
    lat: float


def pick_placeholder_villages(grid: Grid, slope: np.ndarray, seed: int, n: int = 14) -> list[Village]:
    """Scatter n fake settlements on mid-slope cells, at least 14 cells apart."""
    rng = np.random.default_rng(seed)
    candidates = np.flatnonzero((slope.ravel() > 17) & (slope.ravel() < 32))
    picked: list[tuple[int, int]] = []
    for idx in rng.permutation(candidates):
        r, c = divmod(int(idx), grid.cols)
        if not (6 < r < grid.rows - 6 and 6 < c < grid.cols - 6):
            continue
        if all(math.hypot(r - r2, c - c2) > 14 for r2, c2 in picked):
            picked.append((r, c))
        if len(picked) == n:
            break
    villages = []
    for i, (r, c) in enumerate(picked):
        lon, lat = grid.cell_lonlat(r, c)
        villages.append(Village(f"Settlement {string.ascii_uppercase[i]}",
                                int(rng.integers(300, 6000)), r * grid.cols + c, lon, lat))
    return villages
