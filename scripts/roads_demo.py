"""Real Nilgiris roads + hospitals from OpenStreetMap: how much of the network is cut as the storm grows?
Needs:  pip install -r requirements-roads.txt     (and internet the first time)
    python -m scripts.roads_demo                      # sweep 100..300 mm, details for the 200 mm storm
    python -m scripts.roads_demo --mm 150 250 --detail 250
"""
import argparse

import numpy as np

from config.regions import REGIONS
from config.settings import ALERT_THRESHOLD
from src.context import load_region_context
from src.roads.cascade import cascade_report, make_risk_sampler
from src.roads.graph import load_hospitals, load_road_graph
from src.scenario import run_storm


def peak_frame(frames):
    """The frame in which the most cells are above the alert threshold."""
    thr = int(ALERT_THRESHOLD * 100)
    return max(frames, key=lambda f: int((f >= thr).sum()))


def main(region_key="nilgiris", mm_values=(100, 150, 200, 250, 300), detail_mm=200, hours=48):
    region = REGIONS[region_key]
    ctx = load_region_context(region_key)
    G = load_road_graph(region)
    anchors = load_hospitals(region) or [region.center]
    print(f"terrain: {ctx.terrain_source}; {G.number_of_nodes()} junctions, "
          f"{G.number_of_edges()} road segments, {len(anchors)} hospitals\n")

    print(f"{'storm':>8} {'area >=70%':>11} {'roads cut':>10} {'villages isolated':>18}")
    detail = None
    for mm in sorted(set(mm_values) | {detail_mm}):
        frame = peak_frame(run_storm(ctx.susceptibility, mm, hours, "burst").risk_frames)
        rep = cascade_report(G, ctx.villages, anchors, make_risk_sampler(ctx.grid, frame), ALERT_THRESHOLD)
        area = 100 * float((frame >= int(ALERT_THRESHOLD * 100)).mean())
        cut = 100 * rep["cut_edges"] / rep["total_edges"]
        print(f"{mm:>5} mm {area:>10.1f}% {cut:>9.1f}% {len(rep['isolated']):>10} of {len(ctx.villages)}")
        if mm == detail_mm:
            detail = rep

    print(f"\nDetail for the {detail_mm} mm storm:")
    for r in detail["villages"]:
        if r.isolated:
            print(f"  {r.name}: ISOLATED (was {r.baseline_km:.1f} km from a hospital)")
        else:
            print(f"  {r.name}: {r.baseline_km:.1f} km -> {r.cut_km:.1f} km (+{r.extra_km:.1f} km detour)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mm", type=int, nargs="+", default=[100, 150, 200, 250, 300])
    ap.add_argument("--detail", type=int, default=200)
    a = ap.parse_args()
    main(mm_values=a.mm, detail_mm=a.detail)
