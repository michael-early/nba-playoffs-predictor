# Roadmap: Sports ML Research

## Overview

Four phases deliver the NFL combine analysis pipeline end-to-end, starting from repo scaffold and shared cache infrastructure, through data ingestion and EDA, into statistical modeling, and finally ensemble and neural net comparisons alongside NBA/MLB stubs for future work.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Repo scaffold, virtual environment, shared cache utility
- [ ] **Phase 2: NFL Data Pipeline** - Clean joined dataset, EDA notebook, opt-out bias analysis
- [ ] **Phase 3: NFL Statistical Analysis** - Correlations, OLS regression, PCA composites, draft confounder
- [ ] **Phase 4: NFL Advanced Models + Stubs** - Random Forest, XGBoost, MLP neural net, NBA/MLB stubs

## Phase Details

### Phase 1: Foundation
**Goal**: Any researcher can clone the repo and have a working, cache-aware environment
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02
**Success Criteria** (what must be TRUE):
  1. User can run `git clone` + `pip install -r requirements.txt` + `jupyter lab` and land in a working environment with nfl/, nba/, mlb/, and shared/ folders present
  2. Pre-commit hooks (ruff + nbstripout) run on `git commit` without manual setup
  3. `shared/cache.py` load-or-fetch utility returns cached parquet on second call without hitting any remote API
**Plans:** 2 plans
- [ ] 01-01-PLAN.md — Repo scaffold: requirements, pyproject, pre-commit config, sport package skeletons
- [ ] 01-02-PLAN.md — shared/cache.py load_or_fetch utility (TDD)

### Phase 2: NFL Data Pipeline
**Goal**: Users have a clean, documented dataset ready for analysis with sample edge cases handled
**Depends on**: Phase 1
**Requirements**: NFL-01, NFL-02, NFL-10
**Success Criteria** (what must be TRUE):
  1. User can run the data pipeline script and get a joined parquet of combine measurables + career stats with sample membership (drafted / undrafted / not-invited) documented in a README or notebook cell
  2. User can open the EDA notebook, run top-to-bottom, and see distributions, opt-out rates, missingness audit, and position breakdowns without errors
  3. User can see an opt-out bias analysis comparing career outcomes of combine drill skippers vs. participants
**Plans**: TBD

### Phase 3: NFL Statistical Analysis
**Goal**: Users can see interpretable statistical relationships between combine drills and career outcomes, with confounders controlled
**Depends on**: Phase 2
**Requirements**: NFL-03, NFL-04, NFL-08, NFL-09
**Success Criteria** (what must be TRUE):
  1. User can see Pearson + Spearman correlations between combine drills and career outcomes per position group with multiple-comparison correction applied
  2. User can run OLS regression per position group with temporal train/test split and see coefficient plots with confidence intervals
  3. User can see PCA athleticism composites per position group with human-readable component names (e.g., "explosion", "change-of-direction")
  4. OLS and PCA models include draft round as a covariate so athleticism signal is isolated from selection bias
**Plans**: TBD

### Phase 4: NFL Advanced Models + Stubs
**Goal**: Users can compare ensemble and neural net models against the OLS baseline, and NBA/MLB folders exist as research-ready stubs
**Depends on**: Phase 3
**Requirements**: NFL-05, NFL-06, NFL-07, SCAF-01, SCAF-02
**Success Criteria** (what must be TRUE):
  1. User can run a Random Forest model and see feature importances per position group
  2. User can run an XGBoost model and see a performance comparison table against the OLS baseline
  3. User can run the MLP notebook on Colab (GPU-compatible) and see results compared against OLS and ensemble models
  4. NBA and MLB folders each contain a README describing planned analyses and a stub notebook with a data loading skeleton that runs top-to-bottom
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/TBD | Not started | - |
| 2. NFL Data Pipeline | 0/TBD | Not started | - |
| 3. NFL Statistical Analysis | 0/TBD | Not started | - |
| 4. NFL Advanced Models + Stubs | 0/TBD | Not started | - |
