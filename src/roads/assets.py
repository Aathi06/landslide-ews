"""Road network + hospitals for the API: loaded from the cache only, never downloaded while serving requests.

Build the cache once (needs internet and `pip install -r requirements-roads.txt`):
    python -m scripts.build_roads --region nilgiris
"""
import json
from dataclasses import dataclass

from config.regions import Region
from config.settings import CACHE_DIR


class RoadsUnavailable(Exception):
    """Raised with a human-readable reason when road impact cannot be computed."""


@dataclass(frozen=True)
class RoadAssets:
    graph: object                              # networkx MultiDiGraph (from osmnx)
    anchors: list[tuple[float, float]]         # (lon, lat) of hospitals, or the region centre as a fallback


_LOADED: dict[str, RoadAssets] = {}


def graph_path(region: Region):
    return CACHE_DIR / f"roads_{region.key}.graphml"


def hospitals_path(region: Region):
    return CACHE_DIR / f"hospitals_{region.key}.json"


def roads_cached(region: Region) -> bool:
    return graph_path(region).exists()


def build_road_assets(region: Region) -> tuple[int, int, int]:
    """Download (once) and cache the road graph and hospital list. Returns (junctions, segments, hospitals)."""
    from src.roads.graph import load_hospitals, load_road_graph
    G = load_road_graph(region)
    hospitals = load_hospitals(region)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    hospitals_path(region).write_text(json.dumps([[float(x), float(y)] for x, y in hospitals]))
    _LOADED.pop(region.key, None)
    return G.number_of_nodes(), G.number_of_edges(), len(hospitals)


def load_road_assets(region: Region) -> RoadAssets:
    """Cached graph + anchors. Raises RoadsUnavailable (with the reason) instead of downloading."""
    if region.key in _LOADED:
        return _LOADED[region.key]
    if not roads_cached(region):
        raise RoadsUnavailable(f"No road network cached. Run: python -m scripts.build_roads --region {region.key}")
    try:
        import osmnx as ox
    except ImportError:
        raise RoadsUnavailable("osmnx is not installed. Run: pip install -r requirements-roads.txt")
    G = ox.load_graphml(graph_path(region))
    anchors: list[tuple[float, float]] = []
    hp = hospitals_path(region)
    if hp.exists():
        try:
            anchors = [(float(x), float(y)) for x, y in json.loads(hp.read_text())]
        except (OSError, ValueError):
            anchors = []
    assets = RoadAssets(G, anchors or [region.center])
    _LOADED[region.key] = assets
    return assets
