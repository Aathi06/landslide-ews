"""Real settlements from OpenStreetMap, cached as JSON so the server never needs the network.

Build once (needs internet and `pip install -r requirements-roads.txt`):
    python -m scripts.build_villages --region nilgiris
Population comes from the OSM `population` tag when someone entered it; otherwise it is a rough guess by
settlement type (see GUESS_POP). Treat those numbers as estimates.
"""
import json
import re

from config.regions import Region
from config.settings import CACHE_DIR
from src.exposure.villages import Village
from src.terrain.grid import Grid

PLACE_TAGS = ["town", "village", "hamlet"]
GUESS_POP = {"town": 15000, "village": 1500, "hamlet": 300}
MAX_VILLAGES = 30


def villages_path(region: Region):
    return CACHE_DIR / f"villages_{region.key}.json"


def cell_of(grid: Grid, lon: float, lat: float) -> int | None:
    """Flat grid index of the cell containing a point, or None if it is outside the grid."""
    r = int((lat - grid.region.south) / grid.dlat)
    c = int((lon - grid.region.west) / grid.dlon)
    if not (0 <= r < grid.rows and 0 <= c < grid.cols):
        return None
    return r * grid.cols + c


def _population(raw, place: str) -> int:
    m = re.search(r"\d[\d,]*", str(raw or ""))
    if m:
        n = int(m.group().replace(",", ""))
        if n > 0:
            return n
    return GUESS_POP.get(place, 300)


def build_osm_villages(region: Region) -> int:
    """Download named towns / villages / hamlets inside the region and cache them. Returns how many were kept."""
    import osmnx as ox
    gdf = ox.features_from_bbox((region.west, region.south, region.east, region.north), tags={"place": PLACE_TAGS})
    rows, seen = [], set()
    for _, f in gdf.iterrows():
        name = f.get("name")
        if not isinstance(name, str) or not name.strip() or name in seen:
            continue
        seen.add(name)
        pt = f.geometry.representative_point()
        place = f.get("place") if f.get("place") in PLACE_TAGS else "village"
        rows.append(dict(name=name.strip(), pop=_population(f.get("population"), place),
                         lon=float(pt.x), lat=float(pt.y), place=place))
    rows.sort(key=lambda r: -r["pop"])
    rows = rows[:MAX_VILLAGES]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    villages_path(region).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return len(rows)


def load_cached_villages(region: Region, grid: Grid) -> list[Village] | None:
    """Villages from the cache, or None if there is no usable cache (the caller falls back to placeholders)."""
    path = villages_path(region)
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text())
        out = []
        for r in rows:
            cell = cell_of(grid, float(r["lon"]), float(r["lat"]))
            if cell is not None:
                out.append(Village(str(r["name"]), int(r["pop"]), cell, float(r["lon"]), float(r["lat"])))
        return out or None
    except (OSError, ValueError, KeyError, TypeError):
        return None
