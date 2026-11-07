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


def run_storm(susceptibility: np.ndarray, total_mm: float, hours: int, pattern: str) -> StormResult:
    rain = np.concatenate([hyetograph(total_mm, hours, pattern), np.zeros(TAIL_HOURS)])
    cum = np.cumsum(rain)
    n = len(rain)
    picks = np.unique(np.linspace(0, n - 1, min(n, MAX_FRAMES)).round().astype(int))
    frames = [np.round(predict_risk(susceptibility, window_total(cum, h, 24), window_total(cum, h, 72)) * 100).astype(np.uint8)
              for h in picks]
    return StormResult(frames, [int(h) + 1 for h in picks],
                       [round(float(cum[h]), 1) for h in picks],
                       [round(float(rain[h]), 1) for h in picks], n)


# ------------------------------------------------------------------ live mode
from datetime import datetime, timezone

from config.settings import LIVE_FRAMES_AHEAD, LIVE_FRAMES_BACK
from src.rainfall.features import rolling_total
from src.rainfall.interpolate import bilinear
from src.rainfall.live import LiveRain
from src.terrain.grid import Grid


@dataclass
class LiveResult:
    risk_frames: list[np.ndarray]
    offsets: list[int]       # hours relative to now (negative = past, positive = forecast)
    rate: list[float]        # region-average mm/h at each frame
    r72: list[float]         # region-average rain over the previous 72 h
    now_frame: int           # which frame is "now"
    fetched_at: datetime
    stale: bool


def run_live(susceptibility: np.ndarray, grid: Grid, live: LiveRain, now: datetime | None = None) -> LiveResult:
    """Same pipeline as a simulated storm, but the rain comes from the live source.
    Rolling totals are computed at the 25 sample points, then spread over the grid."""
    now = now or datetime.now(timezone.utc)
    n = len(live.lat_axis)
    T = len(live.times)
    now_idx = max(i for i, t in enumerate(live.times) if t <= now)
    start = max(0, now_idx - LIVE_FRAMES_BACK)
    end = min(T - 1, now_idx + LIVE_FRAMES_AHEAD)
    picks = np.linspace(start, end, min(end - start + 1, MAX_FRAMES)).round().astype(int)
    picks = sorted(set(picks.tolist()) | {now_idx})

    r24 = rolling_total(live.rain, 24)
    r72 = rolling_total(live.rain, 72)
    glat = grid.region.south + (np.arange(grid.rows) + 0.5) * grid.dlat
    glon = grid.region.west + (np.arange(grid.cols) + 0.5) * grid.dlon

    def spread(field_at_hour: np.ndarray) -> np.ndarray:
        return bilinear(field_at_hour.reshape(n, n), live.lat_axis, live.lon_axis, glat, glon).ravel()

    frames = [np.round(predict_risk(susceptibility, spread(r24[:, h]), spread(r72[:, h])) * 100).astype(np.uint8)
              for h in picks]
    return LiveResult(frames, [h - now_idx for h in picks],
                      [round(float(live.rain[:, h].mean()), 2) for h in picks],
                      [round(float(r72[:, h].mean()), 1) for h in picks],
                      picks.index(now_idx), live.fetched_at, live.stale)
