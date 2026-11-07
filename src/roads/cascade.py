"""Cascading impact: risky road segments are cut, then we ask who is left stranded.

All functions take a networkx MultiDiGraph whose nodes have x (lon), y (lat) and whose edges have
'length' in metres, which is exactly what osmnx returns. No osmnx import is needed here.
"""
from dataclasses import dataclass
from typing import Callable, Sequence

import networkx as nx
import numpy as np

RiskAt = Callable[[float, float], float]          # (lon, lat) -> risk 0..1


def make_risk_sampler(grid, risk_frame: np.ndarray) -> RiskAt:
    """Look up the risk of whichever grid cell contains a point. risk_frame is uint8 0..100."""
    def at(lon: float, lat: float) -> float:
        r = min(max(int((lat - grid.region.south) / grid.dlat), 0), grid.rows - 1)
        c = min(max(int((lon - grid.region.west) / grid.dlon), 0), grid.cols - 1)
        return float(risk_frame[r * grid.cols + c]) / 100
    return at


def edge_risk(G: nx.MultiDiGraph, u, v, risk_at: RiskAt) -> float:
    """Risk of a road segment = the worst of its two ends and its midpoint."""
    x1, y1, x2, y2 = G.nodes[u]["x"], G.nodes[u]["y"], G.nodes[v]["x"], G.nodes[v]["y"]
    return max(risk_at(x1, y1), risk_at(x2, y2), risk_at((x1 + x2) / 2, (y1 + y2) / 2))


def cut_risky_edges(G: nx.MultiDiGraph, risk_at: RiskAt, threshold: float):
    """Returns (copy of G without risky edges, list of removed (u, v, key))."""
    cut = [(u, v, k) for u, v, k in G.edges(keys=True) if edge_risk(G, u, v, risk_at) >= threshold]
    H = G.copy()
    H.remove_edges_from(cut)
    return H, cut


def nearest_node(G: nx.MultiDiGraph, lon: float, lat: float):
    """Closest road junction to a point (plain Euclidean on lon/lat, fine at district scale)."""
    ids = list(G.nodes)
    xs = np.array([G.nodes[n]["x"] for n in ids])
    ys = np.array([G.nodes[n]["y"] for n in ids])
    return ids[int(np.argmin((xs - lon) ** 2 + (ys - lat) ** 2))]


@dataclass(frozen=True)
class VillageAccess:
    name: str
    isolated: bool
    baseline_km: float          # distance to the nearest anchor with every road open
    cut_km: float | None        # distance after cuts, None if isolated
    extra_km: float | None      # detour added by the cuts, None if isolated


def _dist_to_anchors(G: nx.MultiDiGraph, anchor_nodes: set) -> dict:
    """Shortest road distance (m) from the nearest anchor to every junction, treating roads as two-way."""
    return nx.multi_source_dijkstra_path_length(G.to_undirected(), anchor_nodes, weight="length")


def village_access(G, G_cut, villages: Sequence, anchors: Sequence[tuple[float, float]]) -> list[VillageAccess]:
    """For each village: can it still reach an anchor (hospital / main road) and how far is the detour?
    anchors: list of (lon, lat). Villages need .name .lon .lat."""
    if not anchors:
        raise ValueError("need at least one anchor (hospital or main road junction)")
    anchor_nodes = {nearest_node(G, lon, lat) for lon, lat in anchors}
    before, after = _dist_to_anchors(G, anchor_nodes), _dist_to_anchors(G_cut, anchor_nodes)
    rows = []
    for v in villages:
        n = nearest_node(G, v.lon, v.lat)
        base = before.get(n)
        if base is None:                                  # never connected, even before the storm
            rows.append(VillageAccess(v.name, True, float("inf"), None, None))
        elif n in after:
            rows.append(VillageAccess(v.name, False, float(base) / 1000, float(after[n]) / 1000, float(after[n] - base) / 1000))
        else:
            rows.append(VillageAccess(v.name, True, float(base) / 1000, None, None))
    return rows


def cascade_report(G, villages, anchors, risk_at: RiskAt, threshold: float = 0.70) -> dict:
    """One call for the dashboard: how many roads are cut and which villages are stranded."""
    G_cut, cut = cut_risky_edges(G, risk_at, threshold)
    rows = village_access(G, G_cut, villages, anchors)
    return dict(cut_edges=len(cut), total_edges=G.number_of_edges(),
                isolated=[r.name for r in rows if r.isolated], villages=rows)
