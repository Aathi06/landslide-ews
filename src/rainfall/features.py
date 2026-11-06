"""Rainfall features shared by the live source and the simulator."""
import numpy as np


def rolling_total(rain: np.ndarray, window: int) -> np.ndarray:
    """Rain that fell in the `window` hours ending at each hour (inclusive).
    rain: (..., T) mm per hour. Returns the same shape.
    Early hours with less than `window` hours of history just sum what exists."""
    cum = np.cumsum(rain, axis=-1)
    out = cum.copy()
    out[..., window:] = cum[..., window:] - cum[..., :-window]
    return out
