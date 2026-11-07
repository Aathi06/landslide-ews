"""Count NASA landslide records inside our study regions.
Put the CSV at data/raw/landslides.csv, then:
    python -m scripts.count_landslides
"""
import csv
from collections import Counter

from config.regions import REGIONS
from config.settings import RAW_DIR

PATH = RAW_DIR / "landslides.csv"
PRECISE = {"exact", "1km", "5km"}                    # good enough for 250 m cells

BOXES = {r.name: (r.south, r.north, r.west, r.east) for r in REGIONS.values()}
BOXES["Western Ghats (8-15N, 74-78.5E)"] = (8.0, 15.0, 74.0, 78.5)

with open(PATH, encoding="utf-8-sig", newline="") as f:
    rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
cols = list(rows[0])
def pick(exact, prefix):
    """Exact column name first; a loose match only as a fallback (loose matching once picked 'population' for 'lat')."""
    return exact if exact in cols else next((c for c in cols if c.startswith(prefix)), None)


find = lambda key: next((c for c in cols if key in c), None)
lat_c, lon_c = pick("latitude", "lat"), pick("longitude", "lon")
acc_c, trig_c, ctry_c = find("accuracy"), find("trigger"), find("country")
print(f"{len(rows)} rows. Columns: {cols}\n")
if not (lat_c and lon_c):
    raise SystemExit("Could not find latitude/longitude columns. Send me the column list above.")


def num(v):
    try:
        return float(v)
    except ValueError:
        return None


def report(label, subset):
    acc = Counter((r.get(acc_c, "") or "unknown").lower() for r in subset) if acc_c else {}
    usable = sum(n for a, n in acc.items() if a in PRECISE) if acc_c else "n/a"
    print(f"{label}: {len(subset)} points, {usable} with location accuracy {sorted(PRECISE)}")
    if acc:
        print("   accuracy:", dict(acc.most_common()))
    if trig_c and subset:
        print("   triggers:", dict(Counter(r.get(trig_c, "") or "unknown" for r in subset).most_common(5)))


for label, (s, n, w, e) in BOXES.items():
    inside = [r for r in rows if (num(r[lat_c]) is not None and num(r[lon_c]) is not None
                                  and s <= num(r[lat_c]) <= n and w <= num(r[lon_c]) <= e)]
    report(label, inside)
    for r in inside[:8]:
        print(f"   - {r.get('event_date', '')[:10]}  {r.get('event_title', '')[:70]}  [{r.get(acc_c, '') if acc_c else ''}]")
if ctry_c:
    report("India (whole country)", [r for r in rows if r[ctry_c].lower() == "india"])
