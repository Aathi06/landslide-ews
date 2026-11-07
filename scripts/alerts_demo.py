"""Run a simulated storm and print the alerts it would send (real send if Telegram env vars are set).
    python -m scripts.alerts_demo
"""
import sys

from src.alerts.dispatch import AlertTracker, dispatch_alerts
from src.context import load_region_context
from src.scenario import run_storm

sys.stdout.reconfigure(encoding="utf-8")      # Windows consoles cannot print Tamil/Hindi otherwise
ctx = load_region_context("nilgiris")
storm = run_storm(ctx.susceptibility, total_mm=260, hours=48, pattern="burst")
tracker = AlertTracker()
for hour, frame in zip(storm.hours, storm.risk_frames):
    for a in dispatch_alerts(ctx.villages, frame, tracker, langs=("en", "ta")):
        print(f"[hour {hour:>2}] {a.village} {a.level} ({a.lang}) delivered={a.delivered}\n    {a.text}")
