# What changed compared with the pushed project (main before block C)

## New files
| File | Purpose |
|---|---|
| `src/model/susceptibility.py`, `trigger.py`, `evaluate.py`, `inventory.py` | Block C: learned susceptibility (frequency ratio), Caine rainfall trigger, spatial cross-validation, NASA inventory reader |
| `scripts/train_susceptibility.py`, `scripts/check_trigger.py` | Block C: train + validate the model, calibrate the trigger |
| `tests/test_model.py` | Block C tests |
| `models/.gitkeep` | Folder for the trained model JSON |
| `src/impact.py` | Wiring: roads cut, settlements stranded, alert timeline, opt-in Telegram sending |
| `src/roads/assets.py` | Wiring: loads the cached road graph + hospitals (never downloads while serving) |
| `src/exposure/osm_villages.py` | Wiring: real settlements from OpenStreetMap, cached as JSON |
| `scripts/build_roads.py`, `scripts/build_villages.py` | One-time downloads for the two caches above |
| `tests/test_impact.py` | Tests for all of the wiring |

## Changed files
| File | Change |
|---|---|
| `src/model/predict.py` | Risk = susceptibility x rainfall trigger (same signature shape) |
| `src/scenario.py`, `scripts/roads_demo.py`, `scripts/alerts_demo.py`, `tests/test_live.py`, `tests/test_basics.py` | Take `susceptibility` instead of raw slope |
| `config/settings.py` | `MODELS_DIR`, `TRIGGER_SCALE` |
| `src/context.py` | Susceptibility per cell, `model_method`; uses cached OSM villages on real terrain (`villages_source`) |
| `api/main.py` | New: `GET /api/impact`, `POST /api/alerts/send`; `/api/static` gains `villages_source`, `roads_ready`, `alerts_send_enabled` |
| `static/index.html` | Roads-cut and cut-off stats, cut roads and stranded villages on the map, alert-messages dialog (EN/TA/HI), settlement names now HTML-escaped |
| `README.md` | Status and data-step instructions |

Nothing was deleted. `requirements*.txt` are unchanged: the server still starts without osmnx/networkx
(the road panel then says why it is empty).

## Safety defaults
- Telegram sends nothing unless `EWS_ALERTS_SEND=1` AND `TELEGRAM_BOT_TOKEN` AND `TELEGRAM_CHAT_ID` are set.
  `GET /api/impact` never sends. `POST /api/alerts/send` is a dry run otherwise.
- The server never downloads anything at request time; every download is a script you run on purpose.
