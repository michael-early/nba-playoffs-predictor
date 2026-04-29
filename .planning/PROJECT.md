# Sports ML Research

## What This Is

A multi-sport machine learning research repository organized by league (NFL, NBA, MLB). Each sport has its own folder with Jupyter notebooks for exploration and Python scripts for repeatable model runs. The goal is pure research — understanding what drives player performance.

## Core Value

Each sport folder is a self-contained research workspace where any analysis can be run top-to-bottom.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] NFL folder with combine-metrics → positional performance regression
- [ ] NBA folder scaffolded for future analyses
- [ ] MLB folder scaffolded for future analyses
- [ ] Shared utilities for common data loading and model helpers
- [ ] Notebooks for EDA, scripts for repeatable model runs

### Out of Scope

- Betting / line comparison — pure research focus
- Real-time data pipelines — batch / historical data only
- A single unified cross-sport framework — sport-specific folders kept independent

## Context

- Python project, each sport folder uses its own virtual environment or shared top-level `.venv`
- Free data sources preferred: nflverse, nba_api, pybaseball — not yet decided, will be resolved per sport
- First concrete analysis: NFL combine measurables (40-yard dash, vertical, bench press, etc.) correlated with career/game performance by position
- NBA and MLB folders are placeholders for future work

## Constraints

- **Stack**: Python 3.10+, pandas, scikit-learn, statsmodels, Jupyter notebooks
- **Data**: Free/public sources only for now
- **Style**: Notebooks run top-to-bottom; config cells first; no hardcoded paths

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sport-specific folders over unified framework | Each sport has different data shape and research questions | — Pending |
| Mixed notebooks + scripts | Notebooks for EDA, scripts for repeatable runs | — Pending |

---
*Last updated: 2026-04-29 after initialization*

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state
