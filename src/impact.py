"""What a storm does beyond the risk map: roads cut, settlements stranded, alerts that would go out.

Everything here is derived from the risk frames the dashboard already shows, so numbers always agree with it.
"""
import os
from functools import lru_cache

import numpy as np

from config.settings import ALERT_THRESHOLD
from src.alerts.dispatch import AlertTracker, dispatch_alerts
from src.alerts.messages import SUPPORTED_LANGS
from src.alerts.telegram import send_telegram
from src.context import RegionContext, load_region_context
from src.rainfall.live import get_live_rain
from src.roads.assets import RoadsUnavailable, load_road_assets
from src.scenario import run_live, run_storm

MAX_CUT_SEGMENTS = 4000          # cap on road segments sent to the browser for drawing


# ------------------------------------------------------------------ frames
@lru_cache(maxsize=16)
def _storm(key: str, total_mm: float, hours: int, pattern: str):
    return run_storm(load_region_context(key).susceptibility, total_mm, hours, pattern)


def scenario_frames(key: str, mode: str, total_mm: float = 240, hours: int = 48, pattern: str = "burst",
                    refresh: bool = False) -> tuple[list[np.ndarray], int]:
    """(risk frames, index of 'now'). Simulated storms start at frame 0. Live mode may raise LiveUnavailable."""
    if mode == "live":
        ctx = load_region_context(key)
        res = run_live(ctx.susceptibility, ctx.grid, get_live_rain(ctx.grid.region, refresh=refresh))
        return res.risk_frames, res.now_frame
    return _storm(key, float(total_mm), int(hours), pattern).risk_frames, 0


def peak_frame_index(frames: list[np.ndarray], start: int = 0, threshold: float = ALERT_THRESHOLD) -> int:
    """The frame (at or after `start`) with the most cells at or above the alert threshold."""
    thr = int(threshold * 100)
    return max(range(start, len(frames)), key=lambda i: int((frames[i] >= thr).sum()))


# ------------------------------------------------------------------ roads
def _km(x: float | None) -> float | None:
    return None if x is None or x == float("inf") else round(float(x), 2)


def road_impact(ctx: RegionContext, assets, frame: np.ndarray, threshold: float = ALERT_THRESHOLD) -> dict:
    """Cut every road segment whose risk is at or above the threshold, then see who is stranded."""
    try:
        from src.roads.cascade import cut_risky_edges, make_risk_sampler, village_access
    except ImportError:                       # networkx is only in requirements-roads.txt, so the server must start without it
        raise RoadsUnavailable("networkx is not installed. Run: pip install -r requirements-roads.txt")
    G = assets.graph
    G_cut, cut = cut_risky_edges(G, make_risk_sampler(ctx.grid, frame), threshold)
    rows = village_access(G, G_cut, ctx.villages, assets.anchors)
    segments, seen = [], set()
    for u, v, _ in cut:
        pair = frozenset((u, v))
        if pair in seen or len(segments) >= MAX_CUT_SEGMENTS:
            continue
        seen.add(pair)
        segments.append([round(G.nodes[u]["x"], 4), round(G.nodes[u]["y"], 4),
                         round(G.nodes[v]["x"], 4), round(G.nodes[v]["y"], 4)])
    total = G.number_of_edges()
    return dict(available=True, cut_edges=len(cut), total_edges=total,
                cut_pct=round(100 * len(cut) / total, 1) if total else 0.0,
                isolated=[r.name for r in rows if r.isolated], segments=segments,
                villages=[dict(name=r.name, isolated=r.isolated, baseline_km=_km(r.baseline_km),
                               cut_km=_km(r.cut_km), extra_km=_km(r.extra_km)) for r in rows])


# ------------------------------------------------------------------ alerts
def alert_timeline(villages, frames: list[np.ndarray], start: int = 0, end: int | None = None,
                   langs=SUPPORTED_LANGS, tracker: AlertTracker | None = None, send=None) -> list[dict]:
    """Walk the frames in order and list every alert that would be announced, with the frame it fires on.
    Default `send` does nothing and returns False (dry run)."""
    tracker = tracker or AlertTracker()
    send = send or (lambda text: False)
    out = []
    for i in range(start, len(frames) if end is None else end + 1):
        for a in dispatch_alerts(villages, frames[i], tracker, langs=tuple(langs), send=send):
            out.append(dict(frame=i, village=a.village, level=a.level, lang=a.lang, text=a.text, delivered=a.delivered))
    return out


def sending_enabled() -> bool:
    """Real Telegram sending needs an explicit opt-in AND the bot credentials."""
    return (os.environ.get("EWS_ALERTS_SEND") == "1"
            and bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_CHAT_ID")))


_TRACKERS: dict[str, AlertTracker] = {}


def send_alerts(key: str, frames: list[np.ndarray], now_frame: int, mode: str, langs, reset: bool = False) -> dict:
    """Announce alerts. Dry run (nothing leaves the machine) unless sending_enabled().
    Live mode only announces current conditions; simulations walk the whole storm."""
    ctx = load_region_context(key)
    enabled = sending_enabled()
    if enabled:
        if reset or key not in _TRACKERS:
            _TRACKERS[key] = AlertTracker()
        tracker = _TRACKERS[key]
    else:
        tracker = AlertTracker()                    # dry runs never use up the repeat suppression
    start, end = (now_frame, now_frame) if mode == "live" else (0, None)
    alerts = alert_timeline(ctx.villages, frames, start, end, langs, tracker, send_telegram if enabled else None)
    return dict(enabled=enabled, count=len(alerts), delivered=sum(a["delivered"] for a in alerts), alerts=alerts)


# ------------------------------------------------------------------ one call for the dashboard
def compute_impact(key: str, frames: list[np.ndarray], now_frame: int = 0) -> dict:
    ctx = load_region_context(key)
    peak = peak_frame_index(frames, now_frame)
    try:
        roads = road_impact(ctx, load_road_assets(ctx.grid.region), frames[peak])
    except RoadsUnavailable as err:
        roads = dict(available=False, reason=str(err))
    return dict(peak_frame=peak, villages_source=ctx.villages_source, roads=roads,
                alerts=alert_timeline(ctx.villages, frames))
