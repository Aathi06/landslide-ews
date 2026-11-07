# Susceptibility model results (Nilgiris, Tamil Nadu, generated 2026-11-07)

- Landslide cells used: 13 (from 22 catalogue events; location accuracy exact, 1km, 5km)
- Method: frequency ratio over slope_mean, elevation, curvature; score is the percentile rank of the summed log(FR)
- Validation: leave-one-block-out (8 km blocks), 5 folds, 13 held-out landslides
  - frequency ratio: AUC 0.36 +/- 0.08
  - slope-only baseline: AUC 0.48 +/- 0.09
- Model used by the dashboard: slope-rank fallback (FR did not beat it)

| factor | bin edges (equal-area bins) | frequency ratio per bin |
|---|---|---|
| slope_mean | [11.0, 15.0, 18.6, 24.3] | [1.39, 0.83, 0.83, 0.83, 1.11] |
| elevation | [1016.0, 1685.3, 1917.8, 2105.7] | [1.67, 1.11, 1.11, 0.56, 0.56] |
| curvature | [-0.0015, -0.0002, 0.0005, 0.0015] | [0.56, 1.39, 1.11, 1.11, 0.83] |

AUC here is presence versus background: how highly the held-out landslide cells rank among all cells (0.5 = chance).

Caveats: the inventory is news-reported, biased towards roads and railways, and positions are only accurate to
1-5 km, so the model sees blurred terrain at landslide sites. With so few events the standard error is large.
