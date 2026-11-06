"""Download road network and hospitals from OpenStreetMap (needs osmnx>=2.0 and internet)."""
from config.regions import Region
from config.settings import CACHE_DIR


def _bbox(region: Region):
    return (region.west, region.south, region.east, region.north)      # osmnx 2.x order: left, bottom, right, top


def load_road_graph(region: Region, cache_dir=CACHE_DIR):
    """Drivable road graph (networkx MultiDiGraph) with a 'length' in metres on every edge.
    Cached as GraphML so the download happens once."""
    import osmnx as ox
    path = cache_dir / f"roads_{region.key}.graphml"
    if path.exists():
        return ox.load_graphml(path)
    G = ox.graph_from_bbox(_bbox(region), network_type="drive")
    cache_dir.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, path)
    return G


def load_hospitals(region: Region) -> list[tuple[float, float]]:
    """(lon, lat) of every OSM feature tagged amenity=hospital inside the region."""
    import osmnx as ox
    gdf = ox.features_from_bbox(_bbox(region), tags={"amenity": "hospital"})
    return [(p.x, p.y) for p in gdf.geometry.representative_point()]
