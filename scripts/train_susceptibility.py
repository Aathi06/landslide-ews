"""Train the landslide susceptibility model for a region from the NASA inventory and report honest numbers.
Needs: data/raw/landslides.csv  and  the terrain cache (python -m scripts.build_terrain --region nilgiris)
    python -m scripts.train_susceptibility --region nilgiris
Writes models/susceptibility_<region>.json and docs/MODEL_RESULTS.md."""
import argparse
from datetime import date

import numpy as np

from config.regions import REGIONS
from config.settings import CELL_M, ROOT
from src.model.evaluate import spatial_block_cv
from src.model.inventory import CSV_PATH, PRECISE, positive_cells, read_events
from src.model.susceptibility import FACTORS, fit_fr, save_model
from src.terrain.build import load_cached_features
from src.terrain.grid import Grid

ap = argparse.ArgumentParser()
ap.add_argument("--region", default="nilgiris", choices=list(REGIONS))
ap.add_argument("--margin", type=float, default=0.02, help="FR must beat slope-only AUC by this much to be used")
args = ap.parse_args()

region = REGIONS[args.region]
grid = Grid.from_region(region, CELL_M)
features = load_cached_features(region, grid)
if features is None:
    raise SystemExit(f"No terrain cache. Run: python -m scripts.build_terrain --region {args.region}")
events = read_events(CSV_PATH, (region.south, region.north, region.west, region.east))
cells = positive_cells(events, grid, PRECISE)
print(f"{len(events)} catalogue events in the region; {len(cells)} distinct 250 m cells with location accuracy {PRECISE}")
if len(cells) < 8:
    raise SystemExit("Too few landslide cells to train anything meaningful (need at least 8).")

cv = spatial_block_cv(features, cells, grid)
print(f"\nSpatial block cross-validation ({cv['folds']} folds, {cv['n_tested']} held-out landslides)")
print(f"  frequency-ratio model : AUC {cv['fr_auc']:.2f} +/- {cv['fr_se']:.2f}")
print(f"  slope-only baseline   : AUC {cv['slope_auc']:.2f} +/- {cv['slope_se']:.2f}")
print("  (0.5 = no better than chance, 1.0 = landslides always in the top-ranked cells)")

model = fit_fr(features, cells)
use_fr = cv["fr_auc"] >= cv["slope_auc"] + args.margin
if use_fr:
    model.update(cv_auc=round(cv["fr_auc"], 3), baseline_auc=round(cv["slope_auc"], 3), accuracy_used=list(PRECISE))
    save_model(model, args.region)
    print(f"\nFR beats slope-only by at least {args.margin}: saved models/susceptibility_{args.region}.json")
else:
    print(f"\nFR does NOT beat slope-only by {args.margin}. Not saving a model: the dashboard keeps the slope-rank fallback.")

print("\nFrequency ratio per factor (bins low to high; > 1 means landslides are over-represented):")
lines = []
for f in FACTORS:
    t = model["factors"][f]
    edges = [round(e, 4 if f == "curvature" else 1) for e in t["edges"]]
    fr = [round(v, 2) for v in t["fr"]]
    print(f"  {f:11s} edges {edges}\n              FR    {fr}")
    lines.append(f"| {f} | {edges} | {fr} |")

docs = ROOT / "docs"
docs.mkdir(exist_ok=True)
(docs / "MODEL_RESULTS.md").write_text(f"""# Susceptibility model results ({region.name}, generated {date.today()})

- Landslide cells used: {len(cells)} (from {len(events)} catalogue events; location accuracy {', '.join(PRECISE)})
- Method: frequency ratio over {', '.join(FACTORS)}; score is the percentile rank of the summed log(FR)
- Validation: leave-one-block-out (8 km blocks), {cv['folds']} folds, {cv['n_tested']} held-out landslides
  - frequency ratio: AUC {cv['fr_auc']:.2f} +/- {cv['fr_se']:.2f}
  - slope-only baseline: AUC {cv['slope_auc']:.2f} +/- {cv['slope_se']:.2f}
- Model used by the dashboard: {'frequency ratio' if use_fr else 'slope-rank fallback (FR did not beat it)'}

| factor | bin edges (equal-area bins) | frequency ratio per bin |
|---|---|---|
""" + "\n".join(lines) + """

AUC here is presence versus background: how highly the held-out landslide cells rank among all cells (0.5 = chance).

Caveats: the inventory is news-reported, biased towards roads and railways, and positions are only accurate to
1-5 km, so the model sees blurred terrain at landslide sites. With so few events the standard error is large.
""")
print("\nWrote docs/MODEL_RESULTS.md")
