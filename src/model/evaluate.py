"""Honest evaluation for a presence-only inventory.

There are no verified 'no landslide here' cells, so we ask a different question: how high does the model
rank the cells where landslides really happened, compared with ALL cells in the region? 1.0 = always at
the top, 0.5 = no better than chance. This equals AUC for presence versus background.
Spatial block cross-validation: landslides are grouped into 8 km blocks, and each block is held out in
turn while the model is fitted on the others, so a model cannot score well by memorising neighbours.
"""
import numpy as np

from .susceptibility import fit_fr, raw_score


def percentile_of(background_sorted: np.ndarray, values: np.ndarray) -> np.ndarray:
    """For each value: share of background cells scoring lower (ties count half)."""
    lo = np.searchsorted(background_sorted, values, side="left")
    hi = np.searchsorted(background_sorted, values, side="right")
    return (lo + 0.5 * (hi - lo)) / len(background_sorted)


def presence_background_auc(background: np.ndarray, positives: np.ndarray) -> float:
    return float(percentile_of(np.sort(background), positives).mean())


def spatial_block_cv(features: dict, pos_cells, grid, block_cells: int = 32) -> dict:
    """Leave-one-block-out CV of the FR model, against the slope-only baseline on the same landslides."""
    pos_cells = np.asarray(pos_cells, int)
    rows, cols = np.divmod(pos_cells, grid.cols)
    block = (rows // block_cells) * 1000 + cols // block_cells
    slope = np.asarray(features["slope_mean"], float)
    fr_pct, base_pct, folds = [], [], 0
    for b in np.unique(block):
        test, train = pos_cells[block == b], pos_cells[block != b]
        if len(train) < 3:
            continue
        folds += 1
        keep = np.ones(grid.n_cells, bool)
        keep[train] = False                                   # background excludes the cells it trained on
        raw = raw_score(fit_fr(features, train), features)
        fr_pct += percentile_of(np.sort(raw[keep]), raw[test]).tolist()
        base_pct += percentile_of(np.sort(slope[keep]), slope[test]).tolist()
    fr_pct, base_pct = np.array(fr_pct), np.array(base_pct)
    n = max(len(fr_pct), 1)
    return dict(folds=folds, n_tested=len(fr_pct),
                fr_auc=float(fr_pct.mean()) if len(fr_pct) else float("nan"),
                fr_se=float(fr_pct.std() / np.sqrt(n)),
                slope_auc=float(base_pct.mean()) if len(base_pct) else float("nan"),
                slope_se=float(base_pct.std() / np.sqrt(n)))
