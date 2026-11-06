"""Global tunables. Region boxes live in regions.py."""

CELL_M = 250            # grid cell size in metres
MAX_FRAMES = 36         # frames sent to the browser per storm
TAIL_HOURS = 12         # dry hours simulated after the rain stops
ALERT_THRESHOLD = 0.70  # risk at which a settlement counts as "on alert"

# ---- live rainfall (Open-Meteo) ----
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "processed"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LIVE_LATTICE = 5          # 5 x 5 = 25 sample points over the region
LIVE_PAST_DAYS = 7        # history fetched (needs > 72 h before the first frame)
LIVE_FORECAST_DAYS = 3
LIVE_FRAMES_BACK = 72     # timeline starts this many hours before "now"
LIVE_FRAMES_AHEAD = 48    # ...and ends this many hours after
LIVE_CACHE_MIN = 30       # reuse a cached response younger than this (minutes)
