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

# ---- real terrain (Copernicus GLO-30, 30 m) ----
import os

RAW_DIR = ROOT / "data" / "raw"
DEM_BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"
DEM_PAD_DEG = 0.002        # read a little beyond the region so edge cells have neighbours for gradients
# auto  = use the cached real-terrain file if it exists, else synthetic terrain (no network at startup)
# real  = build it now (downloads the DEM), fail loudly if impossible
# mock  = always synthetic (used by the tests)
TERRAIN_MODE = os.environ.get("EWS_TERRAIN", "auto")

# ---- risk model ----
MODELS_DIR = ROOT / "models"
# Multiplies the Caine rainfall thresholds. 1.0 = the published global threshold.
# scripts/check_trigger.py suggests a local value; override without editing: EWS_TRIGGER_SCALE=0.7
TRIGGER_SCALE = float(os.environ.get("EWS_TRIGGER_SCALE", "1.0"))
