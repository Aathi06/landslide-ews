"""Live and forecast rainfall from Open-Meteo (free, no key).

Flow: lattice of sample points -> one HTTP request -> hourly rain per point.
The last good response is cached on disk so the dashboard survives a network drop.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import numpy as np

from config.regions import Region
from config.settings import (CACHE_DIR, LIVE_CACHE_MIN, LIVE_FORECAST_DAYS, LIVE_LATTICE,
                             LIVE_PAST_DAYS, OPEN_METEO_URL)


class LiveUnavailable(Exception):
    """No fresh data and no cache to fall back on."""


@dataclass
class LiveRain:
    times: list[datetime]        # hourly, UTC
    rain: np.ndarray             # (n_points, T) mm per hour, point order = lat-major lattice
    lat_axis: np.ndarray
    lon_axis: np.ndarray
    fetched_at: datetime
    stale: bool                  # True when served from cache after a failed fetch


def lattice_axes(region: Region, n: int = LIVE_LATTICE) -> tuple[np.ndarray, np.ndarray]:
    return np.linspace(region.south, region.north, n), np.linspace(region.west, region.east, n)


def fetch_raw(lats: list[float], lons: list[float]):
    """One request for all points. Returns Open-Meteo's JSON (list of locations)."""
    params = {
        "latitude": ",".join(f"{v:.4f}" for v in lats),
        "longitude": ",".join(f"{v:.4f}" for v in lons),
        "hourly": "precipitation",
        "past_days": LIVE_PAST_DAYS,
        "forecast_days": LIVE_FORECAST_DAYS,
        "timezone": "UTC",
    }
    r = httpx.get(OPEN_METEO_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def parse_open_meteo(payload, n_points: int) -> tuple[list[datetime], np.ndarray]:
    """Turn the API JSON into (times, rain[n_points, T]). Missing values become 0 mm."""
    locations = payload if isinstance(payload, list) else [payload]
    if len(locations) != n_points:
        raise ValueError(f"expected {n_points} locations, got {len(locations)}")
    times = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
             for t in locations[0]["hourly"]["time"]]
    rain = np.zeros((n_points, len(times)))
    for p, loc in enumerate(locations):
        series = loc["hourly"]["precipitation"]
        if len(series) != len(times):
            raise ValueError("locations have different lengths")
        rain[p] = [0.0 if v is None else float(v) for v in series]
    return times, rain


def _cache_path(region: Region):
    return CACHE_DIR / f"live_{region.key}.json"


def _read_cache(region: Region):
    path = _cache_path(region)
    if not path.exists():
        return None
    try:
        blob = json.loads(path.read_text())
        return datetime.fromisoformat(blob["fetched_at"]), blob["payload"]
    except (ValueError, KeyError, OSError):
        return None


def get_live_rain(region: Region, refresh: bool = False, now: datetime | None = None) -> LiveRain:
    """Fresh data if possible, otherwise the cached copy (marked stale), otherwise LiveUnavailable."""
    now = now or datetime.now(timezone.utc)
    lat_axis, lon_axis = lattice_axes(region)
    lats = [float(a) for a in lat_axis for _ in lon_axis]     # lat-major: matches reshape(n, n)
    lons = [float(o) for _ in lat_axis for o in lon_axis]
    n_points = len(lats)

    cached = _read_cache(region)
    if cached and not refresh and (now - cached[0]).total_seconds() < LIVE_CACHE_MIN * 60:
        times, rain = parse_open_meteo(cached[1], n_points)
        return LiveRain(times, rain, lat_axis, lon_axis, cached[0], stale=False)

    try:
        payload = fetch_raw(lats, lons)
        times, rain = parse_open_meteo(payload, n_points)
    except Exception as err:                                  # network down, rate limit, bad JSON
        if cached:
            times, rain = parse_open_meteo(cached[1], n_points)
            return LiveRain(times, rain, lat_axis, lon_axis, cached[0], stale=True)
        raise LiveUnavailable(f"Could not reach Open-Meteo and no cached data exists ({err})") from err

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(region).write_text(json.dumps({"fetched_at": now.isoformat(), "payload": payload}))
    return LiveRain(times, rain, lat_axis, lon_axis, now, stale=False)
