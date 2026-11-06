# Demo script (about 5 minutes)

Before starting: server running, browser at http://localhost:8000, internet on, one rehearsal done.

1. **The problem (30 s).** One sentence on landslides and why early warning matters in the Nilgiris.
2. **The map (30 s).** Tilt and rotate. Columns are risk per 250 m cell: teal stable, crimson likely to slide.
3. **Live mode (60 s).** Click Live rainfall. Say it fetches real rainfall and forecast. Press play to scrub the last
   72 hours and the next 48. Point at the "Now" label. Expect calm on a dry day, and say so.
4. **Simulation (90 s).** Switch to Simulation, set 240 mm over 48 h, Cloudburst, Run storm. Watch the rain front,
   the columns rising and settlements pulsing on alert. Point at the alert feed and counters.
5. **Show the cause (30 s).** Reduce rainfall to 150 mm: fewer cells light up. Steep slopes go red first.
6. **Alerts / roads (60 s).** Show the Telegram message in English and Tamil, and the road cascade if finished.
7. **Limits and next steps (30 s).** Prototype, sparse landslide data, what is future work.

Backup plan: if the network fails, live mode shows cached data (the note says so); keep a screen recording of a full
simulation run ready.

Likely questions: Why XGBoost / this heuristic? How did you validate? What does the data bias do? What is real and
what is placeholder? Know the answers before the review.
