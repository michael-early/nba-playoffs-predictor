# PRD: NBA Playoffs Game Outcome Predictor

**Version:** 1.0  
**Date:** 2026-05-09  
**Status:** Ready for implementation

---

## 1. Overview

A binary classification pipeline that predicts whether the home team wins a given NBA playoff game. Built for the 2015–2024 playoff era using publicly available data from the NBA Stats API (`nba_api`).

**Resume positioning:** Demonstrates end-to-end data science competency — data acquisition, EDA, feature engineering, model comparison, and explainability — using a domain with rich public data and a well-defined prediction task.

---

## 2. Problem Statement

Given pre-game information available before tip-off, predict:

> **Will the home team win this playoff game?**

- **Type:** Binary classification  
- **Target variable:** `home_win` (1 = home team wins, 0 = away team wins)  
- **Unit of prediction:** Individual playoff game  
- **Naive baseline:** ~58% (home teams win ~58% of playoff games historically)

**Why playoffs only?**  
Playoff games have higher stakes, more media coverage, and more consistent team compositions than the regular season. The smaller, curated dataset keeps the project scope manageable while telling a compelling story.

---

## 3. Data Requirements

### Source
- **Library:** `nba_api` (Python wrapper for stats.nba.com)
- **No API key required** — public data, rate-limit courtesy sleep of 0.6s between calls

### Scope
| Dimension | Value |
|-----------|-------|
| Seasons | 2014–15 through 2023–24 (10 seasons) |
| Rounds | First Round, Conference Semifinals, Conference Finals, NBA Finals |
| Expected rows | 600–800 playoff games |

### Key nba_api Endpoints

| Endpoint | Data Pulled | Used For |
|----------|-------------|---------|
| `LeagueGameFinder` | Playoff game log (date, teams, scores, home/away) | Game rows + target |
| `TeamEstimatedMetrics` | ORtg, DRtg, net rating, pace, eFG% by season | Group 1 features |
| `PlayerCareerStats` / `CommonTeamRoster` | Top player by minutes per team per season | Group 2 features |
| `TeamGameLog` | Per-game dates for rest day calculation | Group 3 features |

### Data Storage
- Raw API responses: `data/raw/` (parquet, one file per endpoint per season)
- Feature matrix: `data/processed/playoff_features.parquet`
- Both directories are gitignored

---

## 4. Feature Specification

### Group 1 — Team Regular Season Efficiency (10 features)

| Feature | Description |
|---------|-------------|
| `home_ortg` | Home team offensive rating (pts per 100 possessions) |
| `away_ortg` | Away team offensive rating |
| `home_drtg` | Home team defensive rating (lower = better) |
| `away_drtg` | Away team defensive rating |
| `home_net_rtg` | Home team net rating (ortg − drtg) |
| `away_net_rtg` | Away team net rating |
| `home_pace` | Home team pace (possessions per 48 min) |
| `away_pace` | Away team pace |
| `ortg_diff` | `home_ortg − away_ortg` (engineered) |
| `drtg_diff` | `home_drtg − away_drtg` (engineered — positive = home team worse defense) |

**Source:** Regular season stats from the same season as the game. No playoff leakage.

### Group 2 — Star Player Quality (4 features)

| Feature | Description |
|---------|-------------|
| `home_star_pts_avg` | Regular season PPG of home team's highest-minutes player |
| `away_star_pts_avg` | Same for away team |
| `home_star_plus_minus` | Season +/- per game of home team's top player |
| `away_star_plus_minus` | Same for away team |

**Source:** `PlayerCareerStats` filtered to regular season, joined to team roster.

### Group 3 — Game Context (5 features)

| Feature | Description |
|---------|-------------|
| `home_rest_days` | Days since home team's last game (capped at 7) |
| `away_rest_days` | Days since away team's last game (capped at 7) |
| `rest_advantage` | `home_rest_days − away_rest_days` |
| `game_number` | Game number within series (1–7) |
| `is_elimination_game` | 1 if loser is eliminated from playoffs, else 0 |

**Source:** Game dates from `TeamGameLog`; series game number derived from game sequence.

### Group 4 — Historical Playoff Record (4 features)

| Feature | Description |
|---------|-------------|
| `home_playoff_win_pct_3yr` | Playoff win % over the prior 3 seasons |
| `away_playoff_win_pct_3yr` | Same for away team |
| `home_finals_apps_5yr` | Number of Finals appearances in prior 5 seasons |
| `away_finals_apps_5yr` | Same for away team |

**Source:** Computed from historical game log (seasons prior to the game's season only — no leakage).

---

## 5. Model Requirements

### Train / Test Split
- **Training set:** Seasons 2014–15 through 2021–22 (8 seasons, ~480–640 games)
- **Holdout test set:** Seasons 2022–23 and 2023–24 (2 seasons, ~120–160 games)
- **Cross-validation:** `TimeSeriesSplit(n_splits=5)` with season as the time unit (no future data leaks into past folds)

### Models to Train

| Model | Library | Role |
|-------|---------|------|
| Logistic Regression | `sklearn.linear_model` | Interpretable baseline — evaluate before adding complexity |
| Random Forest | `sklearn.ensemble` | Ensemble baseline — captures feature interactions |
| XGBoost | `xgboost` | Primary model — typically best performance on tabular data |
| SHAP | `shap` | Explainability layer applied to the best-performing model |

### Evaluation Metrics

| Metric | Target (holdout) | Why |
|--------|-----------------|-----|
| Accuracy | ≥ 65% | Primary headline metric |
| ROC-AUC | ≥ 0.68 | Ranks probability estimates correctly |
| Log loss | Minimize | Penalizes confident wrong predictions |
| Brier score | ≤ 0.22 | Calibration quality |
| Calibration curve | Visual | Confirms probabilities are trustworthy |

### Hyperparameter Tuning
- Use `GridSearchCV` or `RandomizedSearchCV` with `TimeSeriesSplit`
- Random Forest: `n_estimators`, `max_depth`, `min_samples_leaf`
- XGBoost: `n_estimators`, `max_depth`, `learning_rate`, `subsample`

---

## 6. Notebook Structure

Each notebook runs top-to-bottom from a clean kernel. Config cell is always second (after imports).

| Notebook | Scope | Outputs |
|----------|-------|---------|
| `01-data-collection.ipynb` | Fetch all raw data via nba_api, save to `data/raw/` | Parquet files per endpoint per season |
| `02-eda.ipynb` | Distributions, correlations, home court advantage analysis | EDA plots, summary stats |
| `03-feature-engineering.ipynb` | Join raw tables, compute all features, save feature matrix | `data/processed/playoff_features.parquet` |
| `04-modeling.ipynb` | Train all 3 models, cross-validate, compare metrics, select best | Metrics table, ROC curves, calibration plots |
| `05-explainability.ipynb` | SHAP analysis on best model | Beeswarm plot, dependence plots, example game explanations |

**Run order is sequential** — each notebook depends on the output of the previous.

---

## 7. Success Criteria

- [ ] Data collection notebook fetches 2015–2024 playoff games and saves to `data/raw/` without errors
- [ ] Feature matrix contains 600–800 rows with no more than 5% missing values
- [ ] All 23 features present in `playoff_features.parquet`
- [ ] Best model accuracy ≥ 65% on 2023–2024 holdout (naive baseline = 58%)
- [ ] ROC-AUC ≥ 0.68 on holdout
- [ ] Brier score ≤ 0.22 on holdout
- [ ] SHAP beeswarm plot clearly identifies top 5 predictive features
- [ ] All 5 notebooks run top-to-bottom without errors after `pip install -r requirements.txt`
- [ ] `README.md` reproduces full results in 5 commands or fewer

---

## 8. Out of Scope

| Item | Why Excluded |
|------|-------------|
| Real-time / live game predictions | Requires a serving layer outside research scope |
| Injury modeling | Reliable injury data not available via nba_api |
| Betting odds integration | Out of project constraints (no paid APIs) |
| Regular season game prediction | Different dynamics; keep scope tight for resume |
| Cross-sport framework | Separate concern; handled by Sports repo scaffold |
| Career trajectory / panel models | Deferred to v2 |
| Neural networks (LSTM, MLP) | Tabular data doesn't benefit; adds complexity without story |

---

## 9. Dependencies

Add to `requirements.txt` (or the shared repo venv):

```
nba_api>=1.4
pandas>=2.2
numpy>=1.26
scikit-learn>=1.5
xgboost>=2.0
shap>=0.45
matplotlib>=3.9
seaborn>=0.13
joblib>=1.3
tqdm>=4.0
python-dotenv>=1.0
```

---

## 10. File Layout Reference

```
nba-playoffs/
├── PRD.md                          ← this file
├── README.md                       ← setup + run instructions
├── data/
│   ├── raw/                        ← gitignored
│   └── processed/                  ← gitignored
├── notebooks/
│   ├── 01-data-collection.ipynb
│   ├── 02-eda.ipynb
│   ├── 03-feature-engineering.ipynb
│   ├── 04-modeling.ipynb
│   └── 05-explainability.ipynb
├── src/
│   ├── __init__.py
│   ├── data.py                     ← nba_api fetch + cache helpers
│   ├── features.py                 ← feature engineering functions
│   └── models.py                   ← train/eval helpers
└── models/                         ← gitignored (serialized .joblib files)
```
