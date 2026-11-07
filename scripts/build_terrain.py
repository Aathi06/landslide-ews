"""Download the real DEM for a region, compute terrain features, cache them, print a sanity report.
    python -m scripts.build_terrain --region nilgiris
Needs:  pip install -r requirements-terrain.txt     (and internet the first time)
Afterwards the server picks the cached file up automatically (restart it)."""
import argparse

import numpy as np

from config.regions import REGIONS
from config.settings import CELL_M
from src.terrain.build import build_and_cache
from src.terrain.grid import Grid

ap = argparse.ArgumentParser()
ap.add_argument("--region", default="nilgiris", choices=list(REGIONS))
args = ap.parse_args()

region = REGIONS[args.region]
grid = Grid.from_region(region, CELL_M)
print(f"Building terrain for {region.name}: {grid.rows} x {grid.cols} = {grid.n_cells} cells ...")
f = build_and_cache(region, grid)

pct = lambda a: np.percentile(a, [5, 50, 95]).round(1).tolist()
print("elevation m  [p5, median, p95]:", pct(f["elevation"]), " range:", round(float(f["elevation"].min())), "-", round(float(f["elevation"].max())))
print("slope_mean deg [p5, median, p95]:", pct(f["slope_mean"]))
print("slope_max  deg [p5, median, p95]:", pct(f["slope_max"]))
print("curvature [p5, median, p95]:", np.percentile(f["curvature"], [5, 50, 95]).round(5).tolist())
if f["elevation"].max() - f["elevation"].min() < 100:
    print("WARNING: elevation range is under 100 m. This does not look like mountains; check the DEM.")
print("Saved. Restart the server to use real terrain.")
