"""Landslide risk. Day 1: hand-tuned placeholder. Day 3: trained model behind the same signature."""
import numpy as np


def predict_risk(slope: np.ndarray, rain24: float, rain72: float) -> np.ndarray:
    """Probability (0..1) per cell. Steeper slope and more accumulated rain push it up.
    slope: degrees per cell. rain24/rain72: mm over the last 24 / 72 hours."""
    z = 0.16 * (slope - 30) + 0.020 * (rain72 - 175) + 0.010 * (rain24 - 60)
    return 1.0 / (1.0 + np.exp(-z))
