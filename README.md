# Landslide early-warning system

AI-based landslide risk prediction and storm-scenario dashboard for the Western Ghats.

## Run
```
pip install -r requirements.txt
uvicorn api.main:app --reload       # then open http://localhost:8000
pytest                              # sanity checks
```

## Layout
| Folder | Job |
|---|---|
| `config/` | Region boxes (`regions.py`) and global settings (`settings.py`) |
| `src/terrain/` | Grid, elevation sources (synthetic and real Copernicus 30 m DEM), slope/aspect/curvature, caching |
| `src/rainfall/` | Storm simulator, live Open-Meteo source (`live.py`), rolling totals, interpolation |
| `src/model/` | Susceptibility (frequency ratio from the NASA inventory), rainfall trigger (Caine 1980), `predict_risk()`, evaluation |
| `src/exposure/` | Settlements at risk (placeholders, or real ones cached from OpenStreetMap) |
| `src/roads/`, `src/alerts/` | Road-network cascade, Telegram alerts; `src/roads/assets.py` loads the cached road graph |
| `src/impact.py` | Joins risk frames to roads cut, stranded settlements and the alert timeline (used by `/api/impact`) |
| `src/context.py` | Static data for one region, built once and cached |
| `src/scenario.py` | Rainfall to features to risk frames for one storm |
| `api/` | HTTP routes only |
| `static/` | Browser front end |
| `data/` | Raw downloads and processed tables (git-ignored) |
| `tests/` | Basic checks |

Status: day 2 block C plus wiring. Risk = learned susceptibility x rainfall trigger. The dashboard also shows roads cut and settlements stranded at the storm's peak, and previews the alert messages in English, Tamil and Hindi.

One-time data steps (each needs internet; the dashboard works without them, using fallbacks):
```
python -m scripts.build_terrain --region nilgiris       # real 30 m terrain
python -m scripts.train_susceptibility --region nilgiris  # learned susceptibility (needs data/raw/landslides.csv)
python -m scripts.check_trigger --region nilgiris       # optional: suggests EWS_TRIGGER_SCALE
python -m scripts.build_roads --region nilgiris         # road network + hospitals -> road impact panel
python -m scripts.build_villages --region nilgiris      # real settlements (used with real terrain)
```
Telegram: sending is a dry run unless `EWS_ALERTS_SEND=1`, `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are all set. See `docs/MODEL_RESULTS.md` (created by training) for validation numbers.
