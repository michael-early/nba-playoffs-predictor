# Requirements — Sports ML Research

**Project:** Sports ML Research (NFL, NBA, MLB)
**Version:** v1
**Last updated:** 2026-04-29

---

## v1 Requirements

### Infrastructure

- [ ] **INFRA-01**: User can run `git clone` + `pip install -r requirements.txt` + `jupyter lab` and have a working environment — repo scaffold with sport-specific folders (nfl/, nba/, mlb/, shared/), .venv, .gitignore, pre-commit hooks (ruff + nbstripout)
- [ ] **INFRA-02**: Data fetches check disk cache before hitting any remote API — shared `shared/cache.py` load-or-fetch utility caching to parquet

### NFL Combine Analysis

- [ ] **NFL-01**: User can run the data pipeline and get a clean joined dataframe of combine measurables + career stats, cached to parquet, with sample definition documented (drafted / undrafted / not invited)
- [ ] **NFL-02**: User can open the EDA notebook, run top-to-bottom, and see distributions, opt-out rates, missingness audit, and position breakdowns
- [ ] **NFL-03**: User can see Pearson + Spearman correlations between combine drills and career outcomes per position group, with multiple-comparison correction (Bonferroni or BH)
- [ ] **NFL-04**: User can run OLS regression per position group with temporal train/test split and see coefficient plots with confidence intervals
- [ ] **NFL-05**: User can run a Random Forest model and see feature importances per position group
- [ ] **NFL-06**: User can run an XGBoost model and compare performance against OLS baseline
- [ ] **NFL-07**: User can run an MLP neural net on Colab (GPU-compatible notebook) and compare against other models
- [ ] **NFL-08**: User can see PCA athleticism composites per position group with named components (e.g., "explosion" vs "change-of-direction")
- [ ] **NFL-09**: OLS and ensemble models include draft round as a confounder covariate to isolate pure athleticism signal
- [ ] **NFL-10**: User can see an opt-out bias analysis comparing career outcomes of combine drill skippers vs. participants

### Stubs

- [ ] **SCAF-01**: NBA folder exists with README describing planned analyses and a stub notebook with data loading skeleton
- [ ] **SCAF-02**: MLB folder exists with README describing planned analyses and a stub notebook with data loading skeleton

---

## v2 Requirements (Deferred)

- Career trajectory / panel models — season-by-season outcome modeling; requires significant data prep
- NBA role clustering — k-means / GMM on box-score + play-by-play features
- MLB Statcast clustering — batted-ball profile clustering on pybaseball data

---

## Out of Scope

- Real-time / live data pipelines — batch historical data only; ops complexity without research value
- Model deployment / serving layer — notebook outputs + saved artifacts only; no serving infrastructure
- Betting-oriented framing — all analyses framed as "what predicts career performance"
- Single unified cross-sport framework — sport folders kept independent; only pure utilities shared
- Automated hyperparameter tuning (AutoML) — obscures what the model learned; manual search preferred
- Per-player prediction dashboards — export findings as CSV/tables; no UI layer

---

## Traceability

*(Filled by roadmapper)*

| REQ-ID | Phase |
|--------|-------|
| INFRA-01 | — |
| INFRA-02 | — |
| NFL-01 | — |
| NFL-02 | — |
| NFL-03 | — |
| NFL-04 | — |
| NFL-05 | — |
| NFL-06 | — |
| NFL-07 | — |
| NFL-08 | — |
| NFL-09 | — |
| NFL-10 | — |
| SCAF-01 | — |
| SCAF-02 | — |
