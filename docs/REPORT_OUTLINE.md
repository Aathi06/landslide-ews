# Report outline: AI-powered landslide early warning and monitoring system

Source problem: Y-Hack'26 Challenge 24 (KPR Institute of Engineering and Technology). Replace TODO items with the team's real results.

## 1. Introduction
- Landslides follow heavy rainfall on steep, weak slopes. They damage roads, isolate villages and cost lives.
- Warnings are slow when rainfall, terrain and past-event data sit in separate places.
- Study region: the Nilgiris (Tamil Nadu) in the Western Ghats. TODO: add Wayanad if it gets finished.

## 2. Objectives
Map each objective from the problem statement to what was built, and say honestly what was not built.

| Objective | Status |
|---|---|
| Integrate rainfall, terrain and historical data | Rainfall (live and simulated) and terrain built. TODO: confirm real DEM |
| AI/ML landslide risk prediction | TODO: trained model, or a labelled heuristic if time ran out |
| Real-time GIS risk maps and heatmaps | Built: 3D risk map with storm playback |
| Vulnerable roads, villages, infrastructure | Villages built (placeholders until OSM). Road cascade: TODO |
| Early warnings and alerts | Telegram alerts in English, Tamil, Hindi: TODO status |
| Multilingual communication | Alert templates in 3 languages |
| Offline / low-network operation | Not built. Partly mitigated: cached live data when the network drops. Future work |
| Geo-tagged field reports | Not built. Future work |
| Dashboards | Built |

## 3. System design
Describe the architecture: static layer (terrain features, computed once) plus dynamic layer (rainfall, refreshed
hourly) feed one risk function; results go to the dashboard and alerts. Include a diagram.
- Backend: Python, FastAPI. Front end: MapLibre GL and deck.gl. Alerts: Telegram Bot API.
- Rainfall source: Open-Meteo (past 7 days and 3-day forecast, 25 sample points, interpolated to a 250 m grid).
- Swappable rainfall source: live and simulated rain go through the same pipeline.

## 4. Data
| Data | Source | Notes |
|---|---|---|
| Elevation | Copernicus DEM (30 m) | TODO: confirm used |
| Landslide records | NASA Global Landslide Catalog | News-reported, biased toward accessible places, positional errors. TODO: number of usable points |
| Rainfall | Open-Meteo | Model-based values, not rain-gauge readings |
| Roads, villages | OpenStreetMap | TODO |

## 5. Methodology
- Terrain features: slope (arctan of the elevation gradient), aspect, curvature. Why each matters physically.
- Rainfall features: cumulative 24 h and 72 h totals, because soil saturates over time.
- Model: TODO (XGBoost susceptibility + rainfall trigger, or the heuristic).
- Risk to alert levels: watch 50%, warning 70%, emergency 85%.

## 6. Evaluation
TODO: precision, recall and ROC-AUC (not accuracy: landslides are rare). Say whether the train/test split was spatial.
Sanity checks done in code: more rainfall never lowers risk; steeper slope is riskier at equal rainfall.

## 7. Results
Screenshots: calm day in live mode, 150 mm storm, 300 mm storm, alert feed, alert message on a phone.

## 8. Limitations (write these plainly)
- Landslide records are sparse and biased; the model learns that bias.
- Rainfall from 25 interpolated points smooths local variation; Open-Meteo values are modelled.
- Prototype for decision support, not a certified warning system; no field validation.
- TODO: anything still placeholder at submission (terrain, villages, risk formula).

## 9. Future work
Multi-region validation (leave-one-region-out), soil moisture and vegetation (NDVI), satellite change detection,
real sensors (ESP32), offline/SMS mode, field-report form with photo verification, flash-flood hazard.

## 10. Conclusion

## References
NASA Global Landslide Catalog; Copernicus DEM; Open-Meteo; OpenStreetMap; Caine (1980) rainfall intensity-duration
thresholds for landslides. Add libraries used: FastAPI, NumPy, scikit-learn, XGBoost, MapLibre GL, deck.gl, osmnx.
