"""Read the NASA Global Landslide Catalog CSV and turn events into grid cells."""
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np

from config.settings import RAW_DIR
from src.terrain.grid import Grid

CSV_PATH = RAW_DIR / "landslides.csv"
PRECISE = ("exact", "1km", "5km")          # location accuracy good enough for 250 m cells


@dataclass(frozen=True)
class Event:
    lat: float
    lon: float
    day: date | None
    accuracy: str
    title: str


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_day(s: str) -> date | None:
    token = (s or "").strip().split(" ")[0]
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def read_events(path: Path = CSV_PATH, box: tuple[float, float, float, float] | None = None) -> list[Event]:
    """All events, or those inside box = (south, north, west, east)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    events = []
    for r in rows:
        lat, lon = _num(r.get("latitude")), _num(r.get("longitude"))
        if lat is None or lon is None:
            continue
        if box and not (box[0] <= lat <= box[1] and box[2] <= lon <= box[3]):
            continue
        events.append(Event(lat, lon, _parse_day(r.get("event_date", "")),
                            (r.get("location_accuracy") or "unknown").lower(), r.get("event_title", "")))
    return events


def positive_cells(events: list[Event], grid: Grid, accuracies=PRECISE) -> np.ndarray:
    """Unique grid cells containing at least one event with an acceptable location accuracy."""
    cells = set()
    for e in events:
        if e.accuracy not in accuracies:
            continue
        r = int((e.lat - grid.region.south) / grid.dlat)
        c = int((e.lon - grid.region.west) / grid.dlon)
        if 0 <= r < grid.rows and 0 <= c < grid.cols:
            cells.add(r * grid.cols + c)
    return np.array(sorted(cells), dtype=int)
