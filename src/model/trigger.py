"""Rainfall trigger: how close is the recent rain to what normally sets off landslides?

Caine (1980), a global intensity-duration threshold for shallow landslides and debris flows:
    I = 14.82 * D^-0.39        (I in mm/h, D = duration in hours)
so the rain TOTAL needed over D hours is  I * D = 14.82 * D^0.61:   ~103 mm in 24 h, ~201 mm in 72 h.
"""
import numpy as np

from config.settings import TRIGGER_SCALE


def caine_total_mm(hours: float) -> float:
    return 14.82 * hours ** 0.61


def rain_ratio(r24, r72, scale: float = TRIGGER_SCALE):
    """1.0 means 'right at the threshold' in whichever window is closer to its threshold."""
    return np.maximum(np.asarray(r24, float) / (caine_total_mm(24) * scale),
                      np.asarray(r72, float) / (caine_total_mm(72) * scale))


def trigger_score(r24, r72, scale: float = TRIGGER_SCALE):
    """0 with no rain, 0.5 exactly at the threshold, about 0.9 at 1.5x, about 1 at 2x. Always rises with rain."""
    return 1.0 - 2.0 ** (-rain_ratio(r24, r72, scale) ** 3)


def event_rain_ratio(rain: np.ndarray, day_start: int) -> tuple[float, float, float]:
    """For a landslide on a known DAY but unknown hour: the heaviest 24 h and 72 h totals ending
    at any hour of that day. rain: hourly mm; rain[day_start:day_start+24] is the event day and the
    series must hold at least 71 hours before day_start. Returns (max_r24, max_r72, ratio)."""
    best24 = best72 = 0.0
    for h in range(day_start, day_start + 24):
        best24 = max(best24, float(rain[h - 23:h + 1].sum()))
        best72 = max(best72, float(rain[h - 71:h + 1].sum()))
    return best24, best72, float(rain_ratio(best24, best72))
