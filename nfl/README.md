# NFL Combine Analysis

Research workspace for analyzing how NFL Combine measurables predict career outcomes.

## Planned Analyses (v1)

- **NFL-01**: Joined dataset of combine measurables + career stats with sample membership (drafted / undrafted / not-invited) documented.
- **NFL-02**: EDA notebook — distributions, opt-out rates, missingness audit, position breakdowns.
- **NFL-03**: Pearson + Spearman correlations between combine drills and career outcomes per position group, with multiple-comparison correction.
- **NFL-04**: OLS regression per position group with temporal train/test split and coefficient plots with confidence intervals.
- **NFL-05**: Random Forest with per-position feature importances.
- **NFL-06**: XGBoost vs OLS performance comparison.
- **NFL-07**: MLP neural net on Colab (GPU-compatible).
- **NFL-08**: PCA athleticism composites with named components (e.g., "explosion", "change-of-direction").
- **NFL-09**: Draft round as a confounder covariate to isolate athleticism signal.
- **NFL-10**: Opt-out bias analysis (skippers vs participants).

## Data Source

`nflreadpy` (replaces archived `nfl-data-py`). Returns Polars by default; convert with `.to_pandas()` before passing to `shared.cache.load_or_fetch`.

## Conventions

- All data fetches go through `shared.cache.load_or_fetch` so the second run hits disk, not the network.
- Cache keys are sport-prefixed strings (e.g., `"nfl_combine_2000_2023"`) — no slashes.
- Notebooks run top-to-bottom; config cells first; no hardcoded paths.
