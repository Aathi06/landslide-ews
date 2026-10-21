"""Synthetic storms. Day 4 adds a live Open-Meteo source with the same output shape."""
import numpy as np


def hyetograph(total_mm: float, hours: int, pattern: str) -> np.ndarray:
    """Hourly rain (mm/h) that sums to total_mm. pattern: steady | burst | building."""
    t = np.arange(hours) + 0.5
    if pattern == "burst":
        w = np.exp(-0.5 * ((t - hours * 0.55) / (hours / 7)) ** 2)
    elif pattern == "building":
        w = (t / hours) ** 2
    else:
        w = np.ones(hours)
    return total_mm * w / w.sum()


def window_total(cum: np.ndarray, hour: int, window: int) -> float:
    """Rain that fell in the `window` hours ending at `hour` (inclusive)."""
    return float(cum[hour] - (cum[hour - window] if hour >= window else 0.0))
