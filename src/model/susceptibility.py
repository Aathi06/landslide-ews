"""Static landslide susceptibility from terrain, learned from the landslide inventory.

Method: frequency ratio (FR), a standard bivariate statistical method that works with small inventories.
For each terrain factor the cells are split into 5 equal-area bins. FR of a bin = (share of landslides in
the bin) / (share of the area in the bin). FR > 1 means landslides are over-represented there. A cell's
score is the sum of log(FR) over the factors, converted to a 0..1 percentile rank across the region.
Fallback when there is no trained model: percentile rank of slope alone.
"""
import json
from pathlib import Path

import numpy as np

from config.settings import MODELS_DIR

FACTORS = ("slope_mean", "elevation", "curvature")
N_BINS = 5
ALPHA = 1.0          # pseudo-count so an empty bin does not give FR = 0
SLOPE_RANK = {"method": "slope_rank"}


def rank01(x) -> np.ndarray:
    """Percentile rank in (0, 1): 0.5/n for the lowest value up to 1 - 0.5/n for the highest."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    return (r + 0.5) / len(x)


def fit_fr(features: dict, pos_cells, factors=FACTORS, n_bins: int = N_BINS, alpha: float = ALPHA) -> dict:
    """Learn FR tables from the landslide cells. features: name -> per-cell array."""
    pos_cells = np.asarray(pos_cells, int)
    model = {"method": "frequency_ratio", "n_positives": int(len(pos_cells)), "factors": {}}
    for f in factors:
        x = np.asarray(features[f], float)
        edges = np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1])
        b = np.digitize(x, edges)
        area = np.maximum(np.bincount(b, minlength=n_bins), 1) / len(x)
        hits = np.bincount(b[pos_cells], minlength=n_bins)
        fr = ((hits + alpha) / (len(pos_cells) + alpha * n_bins)) / area
        model["factors"][f] = {"edges": edges.tolist(), "fr": fr.tolist()}
    return model


def raw_score(model: dict, features: dict) -> np.ndarray:
    if model["method"] == "slope_rank":
        return np.asarray(features["slope_mean"], float)
    total = 0.0
    for f, t in model["factors"].items():
        b = np.digitize(np.asarray(features[f], float), np.asarray(t["edges"]))
        total = total + np.log(np.asarray(t["fr"]))[b]
    return np.asarray(total, float)


def score(model: dict, features: dict) -> np.ndarray:
    """Susceptibility 0..1 per cell."""
    return rank01(raw_score(model, features))


def model_path(key: str, models_dir: Path | None = None) -> Path:
    return (models_dir or MODELS_DIR) / f"susceptibility_{key}.json"


def save_model(model: dict, key: str) -> Path:
    path = model_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2))
    return path


def load_model(key: str) -> dict | None:
    path = model_path(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def usable(model: dict | None, features: dict) -> bool:
    """A trained model can only be applied if every factor it was trained on is available."""
    return bool(model) and (model["method"] == "slope_rank" or all(f in features for f in model["factors"]))
