"""Check the rainfall trigger against the real events: how much rain fell on the days landslides were recorded?
Uses the Open-Meteo historical archive (ERA5, free, no key). Needs internet.
    python -m scripts.check_trigger --region nilgiris
Prints each event's rain and a suggested EWS_TRIGGER_SCALE."""
import argparse
import json
import time
from datetime import timedelta

import httpx
import numpy as np

from config.regions import REGIONS
from config.settings import RAW_DIR
from src.model.inventory import CSV_PATH, read_events
from src.model.trigger import caine_total_mm, event_rain_ratio

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
ap = argparse.ArgumentParser()
ap.add_argument("--region", default="nilgiris", choices=list(REGIONS))
args = ap.parse_args()
region = REGIONS[args.region]
lon0, lat0 = region.center
cache_file = RAW_DIR / f"era5_events_{region.key}.json"
cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}


def hourly_rain(day):
    """Hourly mm for the 4 days before `day` and `day` itself (120 values; event day = hours 96..119)."""
    key = day.isoformat()
    if key not in cache:
        r = None
        for attempt in range(4):
            r = httpx.get(ARCHIVE, timeout=30, params=dict(
                latitude=round(lat0, 3), longitude=round(lon0, 3), hourly="precipitation", timezone="UTC",
                start_date=(day - timedelta(days=4)).isoformat(), end_date=key))
            if r.status_code != 429:
                break
            time.sleep(5 * (attempt + 1))
        r.raise_for_status()
        cache[key] = [0.0 if v is None else float(v) for v in r.json()["hourly"]["precipitation"]]
        time.sleep(0.4)
    return np.array(cache[key])


events = [e for e in read_events(CSV_PATH, (region.south, region.north, region.west, region.east)) if e.day]
print(f"{len(events)} dated events. Caine threshold: {caine_total_mm(24):.0f} mm/24 h, {caine_total_mm(72):.0f} mm/72 h")
print(f"Rain sampled at the region centre ({lat0:.2f}, {lon0:.2f}); ERA5 is a coarse model and can under-estimate extremes.\n")
print(f"{'date':12s} {'24h mm':>7} {'72h mm':>7} {'x threshold':>12}")
ratios = []
for e in sorted(events, key=lambda e: e.day):
    r24, r72, ratio = event_rain_ratio(hourly_rain(e.day), 96)
    ratios.append(ratio)
    print(f"{e.day.isoformat():12s} {r24:7.0f} {r72:7.0f} {ratio:12.2f}")
RAW_DIR.mkdir(parents=True, exist_ok=True)
cache_file.write_text(json.dumps(cache))

ratios = np.array(ratios)
print(f"\nEvents at or above the Caine threshold: {(ratios >= 1).sum()} of {len(ratios)}; median {np.median(ratios):.2f}x")
suggest = float(np.clip(np.quantile(ratios, 0.25), 0.3, 1.0))
print(f"Suggested EWS_TRIGGER_SCALE = {suggest:.2f}  (rain level that 75% of these events reached or exceeded)")
print("Use it:  EWS_TRIGGER_SCALE=%.2f uvicorn api.main:app --reload" % suggest)
