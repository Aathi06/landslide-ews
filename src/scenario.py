"""Run one storm over one region: rainfall -> features -> risk frames."""
from dataclasses import dataclass

import numpy as np

from config.settings import MAX_FRAMES, TAIL_HOURS
from src.model.predict import predict_risk
from src.rainfall.simulator import hyetograph, window_total


@dataclass
class StormResult:
    risk_frames: list[np.ndarray]   # uint8 0..100, one array per frame
    hours: list[int]
    cum: list[float]                # cumulative mm at each frame
    rate: list[float]               # mm/h at each frame
    total_hours: int


def run_storm(slope: np.ndarray, total_mm: float, hours: int, pattern: str) -> StormResult:
    rain = np.concatenate([hyetograph(total_mm, hours, pattern), np.zeros(TAIL_HOURS)])
    cum = np.cumsum(rain)
    n = len(rain)
    picks = np.unique(np.linspace(0, n - 1, min(n, MAX_FRAMES)).round().astype(int))
    frames = [np.round(predict_risk(slope, window_total(cum, h, 24), window_total(cum, h, 72)) * 100).astype(np.uint8)
              for h in picks]
    return StormResult(frames, [int(h) + 1 for h in picks],
                       [round(float(cum[h]), 1) for h in picks],
                       [round(float(rain[h]), 1) for h in picks], n)
