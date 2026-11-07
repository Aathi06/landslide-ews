# AI-powered landslide early warning and monitoring system (Nilgiris, Western Ghats)

Source problem: Y-Hack'26 Challenge 24 (KPR Institute of Engineering and Technology).
Every number comes from the project's own scripts; their raw output is saved in `docs/results/` and `docs/MODEL_RESULTS.md`.

## 1. Introduction
- Landslides follow heavy rainfall on steep, weak slopes. They damage roads, cut villages off and cost lives.
- Warnings are slow when rainfall, terrain, past events and road networks sit in separate places.
- Study region: the Nilgiris district area of Tamil Nadu (11.25-11.55 N, 76.55-76.95 E), in the Western Ghats,
  which has a long history of monsoon landslides on its roads and railway.
- The system is a **decision-support prototype**, not a certified warning system.

## 2. Objectives and what was delivered
| Objective in the problem statement | Status |
|---|---|
| Integrate rainfall, terrain, satellite and historical data | Done for rainfall (live, forecast, simulated), terrain (30 m DEM) and the NASA landslide inventory. Satellite imagery and soil moisture were not used |
| AI/ML landslide risk prediction | Built and validated, but the learned model showed **no skill** (section 7), so the dashboard uses a slope-based susceptibility with a published rainfall trigger |
| Real-time GIS risk maps and heatmaps | Done: 3D risk map with storm playback, live and simulated rainfall |
| Vulnerable roads, villages, infrastructure | Done: road network and hospitals from OpenStreetMap; roads cut and settlements cut off at the storm's peak |
| Early warnings and emergency alerts | Done: three alert levels, no repeats, Telegram sending (off unless enabled) |
| Multilingual communication | Done: alert text in English, Tamil and Hindi |
| Prioritise emergency response | Partly: each settlement shows its alert level and population, and the hospital detour after road cuts (or "cut off"). There is no automatic ranking or dispatch plan |
| Geo-tagged field reports | Not built (future work) |
| Offline / low-network operation | Not built. Partly mitigated: the last rainfall download is cached and reused if the network drops |
| Dashboards | Done |
| Continuous update from new field and sensor data | Rainfall updates hourly; no field or sensor data |

## 3. System design
Two layers feed one risk function.
- **Static layer** (computed once): terrain features per 250 m grid cell, the susceptibility score, road graph, hospitals, settlements.
- **Dynamic layer** (refreshed hourly): rainfall totals over the previous 24 h and 72 h, from Open-Meteo, or from the storm simulator.
- **Risk = susceptibility x rainfall trigger**, a relative index between 0 and 1 (not a calibrated probability). This is the same structure as NASA's LHASA system.
- **Impact layer:** risk frames -> road segments above the alert threshold are removed from the road graph -> settlements that can no longer reach a hospital are "cut off" -> alert messages are generated.
- Stack: Python, FastAPI, NumPy, rasterio, networkx and osmnx; MapLibre GL and deck.gl in the browser; Telegram Bot API for alerts.
- Live and simulated rainfall go through the same pipeline, so the simulator tests the system, not a separate code path.

## 4. Data
| Data | Source | What we used |
|---|---|---|
| Elevation | Copernicus GLO-30 DEM (30 m) | Nilgiris tile; 133 x 174 = 23,142 grid cells of 250 m. Elevation 295-2,612 m (median 1,814 m); median cell slope 16.7 degrees, 95th percentile 33.3 degrees |
| Landslide records | NASA Global Landslide Catalog (11,033 events worldwide) | India 1,265; Western Ghats box 142; Nilgiris 22. Only events with location accuracy of exact, 1 km or 5 km were used: 13 events, falling in 13 distinct grid cells. Wayanad has one event, at 50 km accuracy, so it was not used |
| Rainfall | Open-Meteo (forecast + past 7 days; 5 x 5 sample points interpolated to the grid) | Hourly rainfall, modelled values rather than rain-gauge readings |
| Roads, hospitals, settlements | OpenStreetMap via osmnx | 8,457 road junctions, 20,878 road segments, 59 hospitals. 30 named OSM towns, villages and hamlets (the largest by population value). Where OSM has no population, the number is a guess by type: town 15,000, village 1,500, hamlet 300 |

## 5. Methodology
**Terrain features.** Slope, aspect and curvature are computed from the 30 m DEM first and then summarised per 250 m cell, so steep spots are not averaged away. Slope is the main driver: gravity pulls harder along steeper ground.

**Susceptibility.** A frequency-ratio model was trained on the 13 landslide cells using slope, elevation and curvature. Each factor is split into five equal-area bins; the ratio of landslide share to area share shows which bins are over-represented. Cell scores are summed in log form and converted to a 0-1 percentile rank. The training script only adopts the learned model if it beats a slope-only baseline in cross-validation by at least 0.02 AUC. It did not (section 7), so the dashboard uses **the percentile rank of mean slope** as the susceptibility.

**Rainfall trigger.** The Caine (1980) global threshold for shallow landslides: intensity I = 14.82 D^-0.39 mm/h, which means about 103 mm in 24 h and 201 mm in 72 h. The trigger score is 0 with no rain, 0.5 at the threshold, about 0.9 at 1.5 times it and about 1 at twice it. It uses whichever of the 24 h and 72 h totals is closer to its threshold.

**Impact.** A road segment is cut when the risk at either end or its midpoint reaches 70%. Each settlement is snapped to its nearest junction; the detour to the nearest hospital is computed on the remaining network.

**Alerts.** Watch at 50%, warning at 70%, emergency at 85%. A settlement is alerted again only if its level rises. Text exists in English, Tamil and Hindi. Sending to Telegram needs an explicit switch (EWS_ALERTS_SEND=1 plus the bot credentials); by default it is a dry run.

## 6. Implementation and testing
55 automated tests cover slope and aspect maths on known planes, monotonic risk (more rain never lowers risk), the live rainfall pipeline with a cached fallback, the training and cross-validation code on synthetic data, road cutting and isolation on a small road grid, alert levels and repeat suppression, and the API routes. The browser interface was checked by hand.

## 7. Evaluation (read this section carefully)
**Susceptibility model.** Leave-one-block-out spatial cross-validation (8 km blocks). The score is presence-versus-background AUC: how highly the held-out landslide cells rank among all cells (0.5 = chance).

| Model | AUC |
|---|---|
| Frequency ratio (slope, elevation, curvature) | **0.36 +/- 0.08** |
| Slope-only baseline | **0.48 +/- 0.09** |

Both are at or below chance. The learned model ranks the held-out landslide cells *lower* than average. With only 13 cells the uncertainty is large, but the result is consistent with likely causes:
1. **Very few events** (13), too few to learn from reliably.
2. **Inventory bias.** The catalogue is news-reported, so events cluster on roads and railways, which run along valleys and lower slopes, not on the steepest ground. Several of the Nilgiris entries are railway sectors.
3. **Location error.** Positions are only accurate to 1-5 km, but cells are 250 m, so the terrain at the recorded point is blurred.

**What follows.** The dashboard does not claim a validated landslide model. The map is a *physically motivated prior* (steeper ground is more susceptible) multiplied by a published rainfall trigger. Its numbers are a relative index, and no one should read them as the chance of a landslide.

**Rainfall trigger check.** Caine's threshold (103 mm in 24 h, 201 mm in 72 h) was compared with ERA5 rainfall at the region centre for the 22 dated Nilgiris events (20 distinct days; two days have two railway-sector entries).

| Result | Value |
|---|---|
| Events at or above the Caine threshold | **0 of 22** |
| Median event rainfall relative to the threshold | **0.11 times** |
| Closest event | 9 Nov 2009: 80 mm in 24 h and 177 mm in 72 h, 0.88 times the threshold |
| Every other event | at most 0.35 times the threshold |
| Scale suggested by the script (rain level 75% of events reached) | 0.30 |

We did **not** adopt 0.30. This sample is not safe to calibrate on:
1. ERA5 is a coarse model and under-estimates point rainfall in steep terrain and in heavy monsoon bursts.
2. Catalogue dates are report dates and the hour is unknown. Some events have almost no rain nearby in time (22 Dec 2016: 0 mm in 72 h), which points to date or cause errors.
3. Several events are not rain-triggered: the catalogue lists construction and a leaking pipe among the Nilgiris triggers.

A scale of 0.30 would put the threshold at about 31 mm in 24 h, so ordinary rain would trigger alerts, which means fitting noise. The trigger therefore stays the published global threshold and is **not validated locally**. Calibrating it with IMD rain-gauge data is the first piece of future work.


## 8. Results from the system
Storm sweep on the real road network: 48 h cloudburst, measured at the frame with the most cells at or above 70% risk, with the 30 OpenStreetMap settlements.

| Storm | Area at or above 70% risk | Roads cut | Settlements cut off |
|---|---|---|---|
| 100 mm | 0.0% | 0.0% | 0 of 30 |
| 150 mm | 14.4% | 0.7% | 0 of 30 |
| 200 mm | 29.1% | 3.8% | 3 of 30 |
| 250 mm | 30.5% | 4.1% | 3 of 30 |
| 300 mm | 30.5% | 4.1% | 3 of 30 |

Reading the table:
- Risk rises with rainfall, as it must. Below about 100 mm nothing is at or above 70%.
- **The area above 70% stops at about 30%.** By design a cell's risk can never exceed its susceptibility percentile, so only the top 30% most susceptible cells can pass 70%, however heavy the storm.
- **Few roads are cut (about 4%)** because most roads run along valleys, where slope-based susceptibility is low.

200 mm storm in detail: Burliar (3.9 km from a hospital), Mavanalla (20.2 km) and Katteri (3.6 km) are cut off. Edakadu's route to a hospital grows from 9.1 km to 11.8 km (+2.7 km). Kattabettu, Yellanalli and Kulisholai each gain 0.3 km. The other 23 settlements are unaffected.

Example alert (hour 28 of a 260 mm cloudburst, watch level, population is an estimate):
- English: "WATCH: Landslide risk is rising near Burliar (60%). About 1,500 people live there. Keep monitoring rainfall and be ready to move."
- Tamil: "கவனிக்கவும்: Burliar அருகே நிலச்சரிவு அபாயம் அதிகரித்து வருகிறது (60%). அங்கு சுமார் 1,500 பேர் வசிக்கின்றனர். மழை நிலவரத்தைக் கவனித்து, பாதுகாப்பான இடத்திற்குச் செல்லத் தயாராக இருங்கள்."

Screenshots to include: calm day in live mode; a 240 mm storm at the peak hour with cut roads and rings; the Alert messages dialog in Tamil.

## 9. Limitations
- The learned susceptibility has no demonstrated skill (section 7). The shown risk is an unvalidated prior times a published trigger.
- The risk is a relative index, not a calibrated probability, and has not been validated against dated events.
- The inventory is tiny, news-reported and biased towards roads.
- Rainfall: 25 interpolated sample points and modelled values smooth out local cloudbursts.
- Settlement populations are guesses by type (town 15,000, village 1,500, hamlet 300) when OSM has no value, so an alert saying "about 15,000 people" is an estimate. The list also holds two spellings of Mettupalayam from separate OSM entries.
- Risk cannot exceed a cell's susceptibility rank, so at most about 30% of the area can pass 70%, whatever the rainfall.
- Only about 4% of road segments are cut in the worst storm, because roads follow valleys where slope-based susceptibility is low.
- Landslide dates in the catalogue are report dates, so the local rainfall check is rough.
- Cut roads are drawn as straight lines between junctions, not along the real road shape.
- Roads are cut as soon as one point is at or above 70%; real roads often survive partial slope failures.
- No field validation, no sensor data, no offline mode.
- A prototype for decision support, not a certified warning system.

## 10. Future work
- Train on the 82 well-located Western Ghats events (and NASA's newer COOLR inventory) using terrain sampled at each point; sample negatives carefully to avoid road and railway bias.
- Validate at a coarser scale that matches the 1-5 km location error.
- Add soil moisture and vegetation (NDVI), and rain-gauge data (IMD) to calibrate the rainfall trigger.
- Geo-tagged field reports with photo verification; a region picker for Wayanad and other regions.
- Offline and SMS alerts; real sensors (low-cost soil-moisture and rain gauges).
- Ensemble rainfall forecasts to show an uncertainty range.

## 11. Conclusion
We built a working end-to-end prototype: live and simulated rainfall, 30 m terrain, a rainfall trigger, a 3D dashboard, real road and settlement data, road-cut and cut-off analysis, and multilingual alerts, tested with 55 automated checks. The learned landslide model could not be validated with the available inventory, and the report says so. The architecture lets a better model drop in without changing the rest.

## 12. References and tools
Caine (1980) rainfall intensity-duration thresholds; NASA Global Landslide Catalog and the LHASA model (Kirschbaum and Stanley); Copernicus DEM GLO-30; Open-Meteo (ERA5 and forecast); OpenStreetMap. Libraries: FastAPI, NumPy, rasterio, networkx, osmnx, httpx, pytest; MapLibre GL, deck.gl; CARTO basemap.

## 13. Reproducing the results
```bash
python -m scripts.train_susceptibility --region nilgiris          # writes docs/MODEL_RESULTS.md
python -m scripts.check_trigger --region nilgiris                 # docs/results/check_trigger.txt
python -m scripts.roads_demo                                      # docs/results/roads_demo.txt
python -m scripts.alerts_demo                                     # docs/results/alerts_demo.txt
pytest                                                            # 55 tests
```
