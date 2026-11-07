"""HTTP routes only. All logic lives in src/."""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from api.encoding import b64_uint8
from config.regions import DEFAULT_REGION, REGIONS
from config.settings import ALERT_THRESHOLD
from src.alerts.messages import SUPPORTED_LANGS
from src.context import load_region_context
from src.impact import compute_impact, scenario_frames, send_alerts, sending_enabled
from src.roads.assets import roads_cached
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
                center=list(r.center), threshold=ALERT_THRESHOLD, terrain=ctx.terrain_source, model=ctx.model_method,
                villages_source=ctx.villages_source, roads_ready=roads_cached(r), alerts_send_enabled=sending_enabled(),
                villages=[asdict(v) for v in ctx.villages])


@app.get("/api/simulate")
def simulate(region: str = DEFAULT_REGION,
             total_mm: float = Query(200, ge=0, le=500),
             hours: int = Query(48, ge=3, le=72),
             pattern: str = "burst"):
    storm = run_storm(_ctx(region).susceptibility, total_mm, hours, pattern)
    return dict(frames=[b64_uint8(f) for f in storm.risk_frames], hours=storm.hours,
                cum=storm.cum, rate=storm.rate, total_hours=storm.total_hours)


@app.get("/api/live")
def live(region: str = DEFAULT_REGION, refresh: bool = False):
    ctx = _ctx(region)
    try:
        rain = get_live_rain(ctx.grid.region, refresh=refresh)
    except LiveUnavailable as err:
        raise HTTPException(503, str(err))
    res = run_live(ctx.susceptibility, ctx.grid, rain)
    return dict(frames=[b64_uint8(f) for f in res.risk_frames], offsets=res.offsets, rate=res.rate,
                r72=res.r72, now_frame=res.now_frame, fetched_at=res.fetched_at.isoformat(), stale=res.stale)


def _frames(region: str, mode: str, total_mm: float, hours: int, pattern: str, refresh: bool = False):
    _ctx(region)
    if mode not in ("sim", "live"):
        raise HTTPException(400, "mode must be 'sim' or 'live'")
    try:
        return scenario_frames(region, mode, total_mm, hours, pattern, refresh)
    except LiveUnavailable as err:
        raise HTTPException(503, str(err))


@app.get("/api/impact")
def impact(region: str = DEFAULT_REGION, mode: str = "sim",
           total_mm: float = Query(240, ge=0, le=500), hours: int = Query(48, ge=3, le=72), pattern: str = "burst"):
    """Roads cut and settlements stranded at the storm's peak, plus every alert the storm would trigger (dry run)."""
    frames, now = _frames(region, mode, total_mm, hours, pattern)
    return compute_impact(region, frames, now)


@app.post("/api/alerts/send")
def alerts_send(region: str = DEFAULT_REGION, mode: str = "sim",
                total_mm: float = Query(240, ge=0, le=500), hours: int = Query(48, ge=3, le=72), pattern: str = "burst",
                langs: str = "en,ta", reset: bool = False):
    """Announce the alerts. A dry run unless EWS_ALERTS_SEND=1 and the Telegram variables are set."""
    wanted = tuple(x for x in langs.split(",") if x)
    if not wanted or any(x not in SUPPORTED_LANGS for x in wanted):
        raise HTTPException(400, f"langs must be a comma list from {SUPPORTED_LANGS}")
    frames, now = _frames(region, mode, total_mm, hours, pattern)
    return send_alerts(region, frames, now, mode, wanted, reset)


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
