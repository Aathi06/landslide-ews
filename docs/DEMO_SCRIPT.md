# Demo script (about 6 minutes)

Before starting: server running (`uvicorn api.main:app`), browser at http://localhost:8000, internet on (map tiles and
live rainfall), one rehearsal done. Check the note under the buttons says: real 30 m terrain, OpenStreetMap
settlements, and the roads panel shows percentages (not "road data not built yet").

1. **The problem (30 s).** Landslides in the Nilgiris follow heavy rain on steep ground and cut roads to villages.
2. **The map (30 s).** Tilt and rotate. Each column is a 250 m cell; height and colour show risk, teal stable to crimson likely to slide.
   Circles are real settlements from OpenStreetMap.
3. **Live mode (60 s).** Click **Live rainfall**. It fetches real rainfall and forecast; "Now" is marked in the timeline clock.
   On a dry day the map stays calm: say so, that is correct. Press play to scrub the last 72 hours and the next 48.
4. **Simulation (90 s).** Click **Simulation**, set 240 mm over 48 h, **Cloudburst**, **Run storm**. Point at the rain front,
   columns rising, settlements pulsing on alert, and the alert feed filling up in time order.
   At 240 mm expect about 30% of the area above 70% risk.
5. **The right-hand numbers (45 s).** Settlements on alert, people in them, area above 70% risk, **roads cut at peak** and
   **settlements cut off at peak**. Drag the timeline to the peak hour shown in the roads label: cut roads then appear as
   red lines and cut-off settlements get a purple ring. Hover a settlement (at or after the peak): it says "Cut off from
   hospital at peak" or the hospital detour in km. At 240 mm expect about 4% of roads cut and 3 of 30 settlements cut off
   (at 200 mm: Burliar, Mavanalla, Katteri). A small road percentage is correct: most roads follow valleys.
6. **Show the cause (30 s).** Drag rainfall down to 150 mm and run again: about 14% of the area, under 1% of roads and no
   settlement cut off. Nothing passes 70% below about 100 mm.
   Steep slopes go first because the rain trigger multiplies a slope-based susceptibility.
7. **Alerts (60 s).** Click **Messages** next to Alerts. Show English, then Tamil and Hindi. The button says
   "Dry run (nothing is sent)": sending to Telegram is off unless started with EWS_ALERTS_SEND=1 and the bot credentials.
   Each settlement is alerted once per level; it is alerted again only if its level rises.
8. **Honest limits (60 s).** Say it plainly: the learned model did not beat chance on the 13 usable landslides
   (0.36 vs 0.48 for slope alone), so the map is a slope prior times a published rainfall trigger. It is a relative
   index, not a probability. The rainfall threshold is also unvalidated locally: 0 of 22 recorded landslide days reached it in
   ERA5 rainfall, which we think reflects coarse rainfall data and noisy event dates, so we kept the published value.
   Next step: train on the 82 Western Ghats events with better sampling and calibrate with IMD rain-gauge data.

Backup plan: if the network fails, live mode shows cached rainfall and says so; the simulator needs no network except
map tiles. Keep a screen recording of one full 240 mm run.

If the roads panel says "road data not built yet": run `python -m scripts.build_roads --region nilgiris` before the demo.

Likely questions are answered in `docs/REVIEW_PREP.md`.
