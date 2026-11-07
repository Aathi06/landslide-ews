"""Landslide risk = how susceptible the ground is x how much the rain has triggered it.

This mirrors the structure of NASA's LHASA system: a static susceptibility map combined with a rainfall
trigger. The result is a RELATIVE RISK INDEX in 0..1, not a calibrated probability."""
import numpy as np

from .trigger import trigger_score


def predict_risk(susceptibility: np.ndarray, rain24, rain72) -> np.ndarray:
    """susceptibility: per-cell score 0..1 (see src.model.susceptibility). rain24 / rain72: mm over the
    previous 24 / 72 hours, either one number for the whole region or one per cell."""
    return np.asarray(susceptibility, float) * trigger_score(rain24, rain72)
