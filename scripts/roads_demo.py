"""Download real roads + hospitals for the Nilgiris, run a heavy storm, print who gets cut off.
Needs:  pip install -r requirements-roads.txt     (and internet)
    python -m scripts.roads_demo
"""
from config.regions import REGIONS
from src.context import load_region_context
from src.roads.cascade import cascade_report, make_risk_sampler
from src.roads.graph import load_hospitals, load_road_graph
from src.scenario import run_storm

region = REGIONS["nilgiris"]
ctx = load_region_context("nilgiris")
G = load_road_graph(region)
anchors = load_hospitals(region) or [region.center]
print(f"{G.number_of_nodes()} junctions, {G.number_of_edges()} road segments, {len(anchors)} hospitals")

storm = run_storm(ctx.slope, total_mm=280, hours=48, pattern="burst")
frame = storm.risk_frames[int(len(storm.risk_frames) * 0.7)]
report = cascade_report(G, ctx.villages, anchors, make_risk_sampler(ctx.grid, frame))
print(f"cut {report['cut_edges']} of {report['total_edges']} segments; isolated: {report['isolated'] or 'none'}")
for r in report["villages"]:
    print(r)
