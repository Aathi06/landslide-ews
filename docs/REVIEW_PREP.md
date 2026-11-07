# Review preparation: what to say and what you will be asked

## The 30-second version
"Landslides in the Nilgiris happen when heavy rain falls on steep ground, and they cut roads to villages.
Our system combines terrain, live rainfall and road data. It scores every 250 m cell for risk, shows it on a 3D map,
works out which roads would be cut and which settlements would be stranded, and drafts alerts in English, Tamil and Hindi.
It is a decision-support prototype. We were honest about one thing: the learned model did not beat chance with the
small landslide inventory, so the map uses a slope prior with a published rainfall threshold."

## How one storm flows through the system (two minutes)
1. **Terrain** (once): a 30 m elevation model is turned into slope, aspect and curvature, then summarised per 250 m cell.
2. **Susceptibility** (once): each cell gets a 0-1 score. Steeper ground scores higher.
3. **Rainfall** (every hour): Open-Meteo gives rain for 25 points; we compute the last 24 h and 72 h totals and spread them over the grid.
   The simulator makes the same totals from the sliders.
4. **Rainfall trigger**: compares those totals with Caine's global threshold (103 mm in 24 h, 201 mm in 72 h). 0 = no rain, 0.5 = at threshold, about 1 = twice it.
5. **Risk = susceptibility x trigger.** No rain means no risk anywhere; heavy rain lights up the most susceptible ground first.
6. **Impact:** road segments at or above 70% risk are removed from the road graph; settlements that can no longer reach a hospital are "cut off".
7. **Alerts:** watch 50%, warning 70%, emergency 85%; one alert per level per settlement; text in three languages.

## Who should be able to explain what
| Person | Module | Be ready to explain |
|---|---|---|
| Aathi | `src/terrain`, `src/model`, `src/rainfall`, `src/impact.py`, `api/`, `static/` | The whole flow above; the validation result; why the fallback is used |
| Alerts teammate | `src/alerts/` | The three levels and thresholds; why alerts are not repeated (tracker remembers the highest level sent); why Telegram is a dry run by default; the three languages (templates with village, risk % and population filled in); how a message is sent (Telegram Bot API, token from environment variables, never in git) |
| Roads teammate | `src/roads/` | A road network is a graph: junctions are nodes, road segments are edges. Cut a segment by removing the edge. Then shortest-path distance from each village to the nearest hospital before and after; no path means isolated. 8,457 junctions, 20,878 segments, 59 hospitals from OpenStreetMap |
| Docs teammate | `docs/` | The report structure, what is real and what is placeholder, and the limitations section |

Everyone: say truthfully who built and who debugged each part, and be able to name the tools and libraries used.

## The numbers you may be asked for
- Grid: 133 x 174 = 23,142 cells of 250 m. Terrain: Copernicus DEM, 30 m.
- Landslide inventory: NASA Global Landslide Catalog, 11,033 events worldwide; 22 in the Nilgiris; 13 with good location accuracy (exact, 1 km, 5 km).
- Validation (spatial cross-validation): learned model AUC 0.36 +/- 0.08; slope-only 0.48 +/- 0.09; 0.5 is chance.
- Rainfall trigger: 103 mm / 24 h, 201 mm / 72 h (Caine 1980). Check against the 22 dated events: 0 of 22 reached it in ERA5 rain (median 0.11x; closest was 9 Nov 2009 at 0.88x). We kept the published value.
- Roads: 8,457 junctions, 20,878 segments, 59 hospitals. 30 OpenStreetMap settlements. Tests: 55.
- Storm sweep: 100 mm nothing; 150 mm 14% of area, 0 settlements cut off; 200 mm 29% of area, 3.8% of roads cut, 3 settlements cut off (Burliar, Mavanalla, Katteri); 250 to 300 mm about 30% and 4%, 3 settlements.

## The honest-limits answer (practise saying this calmly)
"We trained a frequency-ratio model on the 13 landslide locations we could use. In spatial cross-validation it scored
0.36, and a plain slope baseline scored 0.48, so neither beat chance. We think this is because there are very few
events, the catalogue is news-reported and clusters on roads and railways along valleys, and locations are only
accurate to 1-5 km while our cells are 250 m. We did not lower our acceptance rule to force the learned model in.
The dashboard therefore uses slope as susceptibility, and the risk number is a relative index, not a probability."

## Likely questions
**Why not deep learning or XGBoost?** 13 usable events is far too few. A complex model would memorise them. Frequency ratio is the standard method for small inventories, and it still failed validation.

**How accurate is it?** We cannot claim accuracy. The inventory is too small and biased to measure it. What we can show: the maths on test cases, the pipeline end to end, and that more rain always means more risk.

**What is AUC?** Out of all the cells, how highly the model ranks the cells where a landslide really happened. 1 = always top, 0.5 = chance, below 0.5 = worse than chance.

**Why is the learned model worse than chance?** Probably inventory bias: news reports of landslides come from roads and railways, which sit on valley floors, not the steepest slopes. With 13 points the uncertainty is large.

**What is spatial cross-validation?** Landslides are grouped into 8 km blocks; each block is hidden in turn while the model trains on the rest. Without it, nearby landslides leak between training and test and the score looks better than it is.

**Where does the rainfall threshold come from?** Caine (1980), a global study of rainfall that triggered shallow landslides. It is a global threshold; local ones in the Western Ghats are likely lower, which is why we check it against real events (check_trigger).

**Is the rainfall real-time?** Near real-time: Open-Meteo updates hourly and includes a forecast. The values are modelled, not from rain gauges, and 25 sample points smooth out local cloudbursts.

**What if the internet fails?** Live mode uses the last cached download and says so. The simulator works without internet (except map tiles).

**Why did none of the 22 recorded landslide days reach the rainfall threshold?** ERA5 is coarse and under-estimates point rain in steep terrain; catalogue dates are report dates with unknown hours; and some events were not rain-triggered (construction, a leaking pipe). Only the November 2009 event came close (0.88x). We did not lower the threshold to fit this noisy sample (the script suggested 0.30, which would alarm on about 30 mm of rain). It stays the published value and is listed as unvalidated.

**Why does the area above 70% stop at about 30%?** Risk is susceptibility multiplied by the trigger, and the trigger is at most 1, so a cell's risk can never exceed its susceptibility rank. Only the top 30% of cells by rank can pass 70%. It is a simplification of the model, and we say so.

**Why are only about 4% of roads cut and 3 settlements cut off?** Most roads run along valleys, where slope-based susceptibility is low, so the steep ground that turns red is mostly off the road network. The cut-off settlements are the ones whose only route crosses a high-risk segment.

**Why are some populations guesses?** OpenStreetMap often has no population tag. We use rough values by settlement type and say so on the dashboard.

**Does it really send alerts?** Only if started with EWS_ALERTS_SEND=1 and a Telegram bot token and chat id. Otherwise it is a dry run and nothing leaves the machine.

**Why are cut roads straight lines?** We draw them between junctions. The cut/not-cut decision uses the whole graph; only the drawing is simplified.

**What would you do with more time?** Train on the 82 Western Ghats events with better negative sampling, calibrate the rainfall trigger with local rain-gauge data, add soil moisture and field reports, and validate on past monsoon events.

**What is real and what is placeholder?** Real: the DEM, rainfall, the NASA inventory, the road network, hospitals and settlement positions. Estimated: some populations. Not validated: the risk index itself.

## If something breaks during the demo
- Map is blank: no internet, or tiles blocked. Use the screen recording.
- Live mode error: say the data source is down; show Simulation.
- Roads panel empty: the road cache was not built (`python -m scripts.build_roads --region nilgiris`).
- Anything else: stay calm, show the tests (`pytest` shows 55 passing) and the code structure.
