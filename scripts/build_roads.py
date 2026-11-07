"""Download the road network and hospitals from OpenStreetMap once and cache them for the dashboard.
    python -m scripts.build_roads --region nilgiris
Needs:  pip install -r requirements-roads.txt     (and internet the first time)
Restart the server afterwards: the road-impact panel then fills in."""
import argparse

from config.regions import REGIONS
from src.roads.assets import build_road_assets

ap = argparse.ArgumentParser()
ap.add_argument("--region", default="nilgiris", choices=list(REGIONS))
args = ap.parse_args()
region = REGIONS[args.region]
print(f"Downloading roads and hospitals for {region.name} (this can take a few minutes the first time) ...")
nodes, edges, hospitals = build_road_assets(region)
print(f"{nodes} junctions, {edges} road segments, {hospitals} hospitals cached.")
if hospitals == 0:
    print("No hospitals tagged in OpenStreetMap here: the region centre will be used as the reference point.")
print("Done. Restart the server.")
