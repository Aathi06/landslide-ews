"""HTTP routes only. All logic lives in src/."""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from api.encoding import b64_uint8
from config.regions import DEFAULT_REGION, REGIONS
from config.settings import ALERT_THRESHOLD
from src.context import load_region_context
from src.rainfall.live import LiveUnavailable, get_live_rain
from src.scenario import run_live, run_storm

app = FastAPI(title="Landslide EWS")


def _ctx(region: str):
    if region not in REGIONS:
        raise HTTPException(404, f"unknown region '{region}'")
    return load_region_context(region)


@app.get("/api/regions")
def regions():
    return [dict(key=r.key, name=r.name, center=r.center) for r in REGIONS.values()]


@app.get("/api/static")
def static_info(region: str = DEFAULT_REGION):
    ctx = _ctx(region)
    g, r = ctx.grid, ctx.grid.region
    return dict(region=r.name, rows=g.rows, cols=g.cols, cell_m=g.cell_m,
                south=r.south, west=r.west, dlat=g.dlat, dlon=g.dlon,
                center=list(r.center), threshold=ALERT_THRESHOLD, terrain=ctx.terrain_source,
                villages=[asdict(v) for v in ctx.villages])


@app.get("/api/simulate")
def simulate(region: str = DEFAULT_REGION,
             total_mm: float = Query(200, ge=0, le=500),
             hours: int = Query(48, ge=3, le=72),
             pattern: str = "burst"):
    storm = run_storm(_ctx(region).slope, total_mm, hours, pattern)
    return dict(frames=[b64_uint8(f) for f in storm.risk_frames], hours=storm.hours,
                cum=storm.cum, rate=storm.rate, total_hours=storm.total_hours)


@app.get("/api/live")
def live(region: str = DEFAULT_REGION, refresh: bool = False):
    ctx = _ctx(region)
    try:
        rain = get_live_rain(ctx.grid.region, refresh=refresh)
    except LiveUnavailable as err:
        raise HTTPException(503, str(err))
    res = run_live(ctx.slope, ctx.grid, rain)
    return dict(frames=[b64_uint8(f) for f in res.risk_frames], offsets=res.offsets, rate=res.rate,
                r72=res.r72, now_frame=res.now_frame, fetched_at=res.fetched_at.isoformat(), stale=res.stale)


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
