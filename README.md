# NBA Playoff Series Outcome Predictor

Predicts which team wins each NBA playoff series using pre-series regular season data. Built as an end-to-end machine learning pipeline: data collection, EDA, feature engineering, model comparison, and SHAP explainability.

**Stack:** Python 3.11 · nba_api · pandas · scikit-learn · XGBoost · SHAP

---

## Results

**Best model:** XGBoost — **AUC 0.683** on held-out 2022–24 seasons  
**Naive baseline:** 56.7% (always pick the higher seed)

| Model | Accuracy | ROC-AUC |
|-------|----------|---------|
| XGBoost | 53.3% | **0.683** |
| Random Forest | 56.7% | 0.674 |
| Logistic Regression | 53.3% | 0.647 |

> Accuracy looks modest because 2022–24 were upset-heavy seasons. AUC is the right metric here — it measures how well the model ranks probabilities, not just whether it picks the right binary outcome.

### Why series, not individual games?

Individual game outcomes have ~40% irreducible variance (a 10-point favorite loses 40% of the time). Averaging over 4–7 games in a series dramatically reduces noise, making team quality a much stronger signal. Series-level AUC (~0.68) consistently outperforms game-level AUC (~0.60) with the same feature set.

---

## What Drives Playoff Series Outcomes (SHAP)

Top features by mean absolute SHAP value:

| Rank | Feature | Interpretation |
|------|---------|---------------|
| 1 | `ortg_diff` | Offensive rating gap — scoring edge is the strongest signal |
| 2 | `home_tov_pct` | Turnover rate — sloppier teams get exposed over 4–7 games |
| 3 | `away_win_pct` | Lower seed's regular season win % — a 6-seed with 48 wins is dangerous |
| 4 | `away_net_rtg` | Lower seed's overall efficiency — quality of the opponent matters |
| 5 | `home_playoff_win_pct_3yr` | Playoff experience — teams that have been here before |

**Key finding:** Offensive rating differential is the single strongest predictor — not seeding, not win percentage, not playoff history. And the *lower seed's* quality features rank almost as highly as the higher seed's, capturing the "dangerous underdog" effect.

---

## Data

- **Source:** `nba_api` (stats.nba.com — public, no API key required)
- **Scope:** 2015–2024 NBA playoffs (9 seasons · 135 series · 748 games)
- **Split:** Train on 2015–2022, hold out 2023–2024

---

## Features (23 total)

| Group | Features |
|-------|---------|
| Team efficiency | ORtg, DRtg, net rating, pace (home + away + differentials) |
| Team quality | Regular season win %, offensive rebound %, turnover % |
| Historical | Playoff win % over prior 3 seasons, Finals appearances in prior 5 years |

---

## Notebooks

Run in order — each depends on the previous output:

| # | Notebook | What it does |
|---|----------|-------------|
| 01 | `01-data-collection.ipynb` | Fetch playoff game logs + team metrics via nba_api |
| 02 | `02-eda.ipynb` | Home court advantage, efficiency distributions, rest days |
| 03b | `03b-series-feature-engineering.ipynb` | Aggregate games → series, build feature matrix |
| 04b | `04b-series-modeling.ipynb` | Train LR / RF / XGBoost, compare on holdout |
| 05b | `05b-series-explainability.ipynb` | SHAP analysis on best model |

---

## Setup

```bash
git clone https://github.com/<your-username>/Sports.git
cd Sports/nba-playoffs
python3 -m venv .venv && source .venv/bin/activate
pip install nba_api pandas numpy scikit-learn xgboost shap matplotlib seaborn joblib tqdm pyarrow jupyterlab
jupyter lab
```

Data collection (~5–10 min first run, cached after):
```bash
# Open and run notebooks in order starting with 01-data-collection.ipynb
```

---

## Project Structure

```
nba-playoffs/
├── notebooks/          ← 5 notebooks, run in order
├── src/
│   ├── data.py         ← nba_api fetch helpers with parquet caching
│   ├── features.py     ← feature engineering functions
│   └── models.py       ← pipeline builders, eval, SHAP helpers
├── data/
│   ├── raw/            ← gitignored — nba_api parquet cache
│   └── processed/      ← gitignored — feature matrices
├── models/             ← gitignored — saved .joblib artifacts
└── PRD.md              ← full project requirements and feature spec
```

---

## Key Design Decisions

**Series vs. game prediction** — Tried individual game prediction first (AUC ~0.60), then switched to series-level aggregation which improved AUC to ~0.68 with the same features.

**Logistic Regression as baseline** — Always establish an interpretable linear baseline before using tree models. LR showed that the features have genuine linear signal; XGBoost added ~3% AUC via non-linear interactions.

**Temporal train/test split** — Used `TimeSeriesSplit` for cross-validation and held out the two most recent seasons (2023–24) as the final test set. Never trained on future data.

**Why not player-level stats** — `nba_api` rate limits made fetching per-player data for 135+ team-seasons impractical. Team-level efficiency metrics (ORtg, DRtg) capture aggregate quality effectively and are well-documented to be predictive.
