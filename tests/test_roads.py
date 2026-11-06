import pytest

nx = pytest.importorskip("networkx")

from src.exposure.villages import Village
from src.roads.cascade import cascade_report, cut_risky_edges, nearest_node, village_access

X0, Y0, STEP = 76.0, 11.0, 0.01


def lattice():
    """3x3 grid of junctions, every road 1000 m, two-way."""
    G = nx.MultiDiGraph()
    for i in range(3):
        for j in range(3):
            G.add_node((i, j), x=X0 + STEP * i, y=Y0 + STEP * j)
    for i in range(3):
        for j in range(3):
            for di, dj in ((1, 0), (0, 1)):
                if i + di < 3 and j + dj < 3:
                    G.add_edge((i, j), (i + di, j + dj), length=1000.0)
                    G.add_edge((i + di, j + dj), (i, j), length=1000.0)
    return G


def near(a, b):
    return abs(a - b) < 1e-9


ANCHORS = [(X0, Y0)]                                            # junction (0, 0)
V_FAR = Village("Far", 100, 0, X0 + 2 * STEP, Y0 + 2 * STEP)    # junction (2, 2)
V_NEAR = Village("Near", 100, 0, X0 + STEP, Y0)                 # junction (1, 0)


def test_nearest_node():
    assert nearest_node(lattice(), X0 + 0.0102, Y0 - 0.0003) == (1, 0)


def test_no_risk_means_no_cuts_and_no_detours():
    rep = cascade_report(lattice(), [V_FAR, V_NEAR], ANCHORS, lambda lon, lat: 0.1)
    assert rep["cut_edges"] == 0 and rep["isolated"] == []
    assert all(r.extra_km == 0 for r in rep["villages"])


def test_cutting_one_road_forces_a_detour():
    risk_at = lambda lon, lat: 0.9 if near(lon, X0 + STEP / 2) and near(lat, Y0) else 0.0   # only that midpoint
    G = lattice()
    G_cut, cut = cut_risky_edges(G, risk_at, 0.7)
    assert len(cut) == 2                                 # the road is two-way: two directed edges
    rows = {r.name: r for r in village_access(G, G_cut, [V_NEAR], ANCHORS)}
    assert not rows["Near"].isolated
    assert rows["Near"].baseline_km == 1.0 and rows["Near"].cut_km == 3.0 and rows["Near"].extra_km == 2.0


def test_high_risk_zone_isolates_a_village():
    risk_at = lambda lon, lat: 0.95 if lon > X0 + 1.5 * STEP else 0.0       # the whole east column
    rep = cascade_report(lattice(), [V_FAR, V_NEAR], ANCHORS, risk_at)
    assert rep["isolated"] == ["Far"]
    near_row = next(r for r in rep["villages"] if r.name == "Near")
    assert not near_row.isolated


def test_needs_an_anchor():
    G = lattice()
    with pytest.raises(ValueError):
        village_access(G, G, [V_NEAR], [])
