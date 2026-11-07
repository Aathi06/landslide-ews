"""Download real town / village / hamlet locations from OpenStreetMap once and cache them.
    python -m scripts.build_villages --region nilgiris
Needs:  pip install -r requirements-roads.txt     (and internet the first time)
Used only with real terrain (python -m scripts.build_terrain). Restart the server afterwards."""
import argparse
import json

from config.regions import REGIONS
from src.exposure.osm_villages import build_osm_villages, villages_path

ap = argparse.ArgumentParser()
ap.add_argument("--region", default="nilgiris", choices=list(REGIONS))
args = ap.parse_args()
region = REGIONS[args.region]
print(f"Downloading settlements for {region.name} ...")
n = build_osm_villages(region)
print(f"{n} settlements cached in {villages_path(region)}")
for r in json.loads(villages_path(region).read_text())[:10]:
    print(f"  {r['name']:28s} {r['place']:8s} pop ~{r['pop']:,}")
print("Population is the OSM tag where present, otherwise a rough guess by settlement type.")
print("Restart the server.")
