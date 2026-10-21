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
| `src/terrain/` | Grid, elevation source, slope and other terrain features |
| `src/rainfall/` | Storm simulator (live rainfall source arrives day 4) |
| `src/model/` | `predict_risk()`, the single function the trained model replaces |
| `src/exposure/` | Settlements at risk |
| `src/roads/`, `src/alerts/` | Road-network cascade (day 5), Telegram alerts (day 6) |
| `src/context.py` | Static data for one region, built once and cached |
| `src/scenario.py` | Rainfall to features to risk frames for one storm |
| `api/` | HTTP routes only |
| `static/` | Browser front end |
| `data/` | Raw downloads and processed tables (git-ignored) |
| `tests/` | Basic checks |

Status: day 1. Terrain, villages and the risk curve are placeholders.
