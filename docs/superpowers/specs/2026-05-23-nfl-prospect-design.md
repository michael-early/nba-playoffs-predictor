# NFL Prospect Success Predictor — Design Spec

**Date:** 2026-05-23
**Status:** Approved
**Scope:** WR position, 2010–2024 draft classes

---

## 1. Problem Statement

Identify which pre-draft metrics — combine athleticism measurements and college production statistics — best predict whether a WR prospect will reach elite NFL success (Pro Bowl selection).

**Target variable:** `pro_bowl_ever` — binary 1/0 (ever selected to a Pro Bowl during NFL career).

**Why Pro Bowl?** Defines elite ceiling rather than "good enough." Pro Bowl WRs represent roughly the top 15–20% of starters — a meaningful threshold that separates elite from solid.

---

## 2. Folder Structure

```
nfl-prospect/
├── notebooks/
│   ├── 01-data-collection.ipynb     # Pull combine + college stats + career outcomes
│   ├── 02-eda.ipynb                 # Distributions, correlations, class balance
│   ├── 03-feature-engineering.ipynb # Athletic composites, dominator rating, breakout age
│   ├── 04-modeling.ipynb            # Binary classifier, XGBoost + LR, cross-validation
│   └── 05-explainability.ipynb      # SHAP values — which metrics drive elite WR success
├── scripts/
│   ├── fetch_data.py                # CLI: re-pull data for a new draft class
│   └── train_model.py               # CLI: retrain model
├── src/
│   ├── __init__.py
│   ├── data.py                      # Data loading helpers
│   ├── features.py                  # Feature engineering functions
│   └── models.py                    # Model training/evaluation helpers
├── data/
│   ├── raw/                         # Parquet files from each API source
│   └── processed/                   # Merged, cleaned per-prospect feature matrix
├── models/                          # Saved .joblib model files
├── outputs/
│   └── reports/                     # SHAP plots, feature importance CSVs
├── config/
│   └── wr_analysis.json             # Position, draft year range, feature flags
└── README.md
```

---

## 3. Data Sources

| Source | Library | Data |
|--------|---------|------|
| NFL Combine | `nfl-data-py` → `import_combine_data()` | 40-yd dash, vertical, broad jump, 3-cone, 20-yd shuttle, height, weight, arm length, hand size |
| College production | `cfbd` (College Football Data API — free API key required, register at collegefootballdata.com) | Receiving yards, receptions, TD rate, yards-per-target, team passing yards |
| Career outcomes | Pro Football Reference — `pandas.read_html()` on PFR Pro Bowl history tables | Pro Bowl selections by year, career games played |

**Draft class scope:** 2010–2024. Gives ~15 seasons of combine data and enough career time for most prospects to have established (or failed to establish) Pro Bowl-level careers. 2022–2024 prospects may have incomplete careers — flag these and handle carefully (exclude from training, use for "current prospects" inference).

---

## 4. Feature Engineering

**Note on missing combine values:** Many prospects skip individual drills (3-cone and 20-shuttle have the most missingness). Strategy: impute with position-group median. Flag prospects with >3 missing measurements — they may need to be excluded from athletic-only features.

### Athletic Profile (combine-derived)

| Feature | Definition | Notes |
|---------|-----------|-------|
| `speed_score` | `weight × 200 / (40_time⁴)` | Classic WR athleticism composite — rewards fast + heavy |
| `forty_time` | 40-yard dash (seconds) | Raw; used alongside speed_score |
| `vertical` | Vertical jump (inches) | Ball-tracking proxy |
| `broad_jump` | Broad jump (inches) | Explosiveness |
| `three_cone` | 3-cone drill (seconds) | Change-of-direction / route running proxy |
| `twenty_shuttle` | 20-yard shuttle (seconds) | Lateral agility |
| `weight` | Weight (lbs) | |
| `height` | Height (inches) | |
| `arm_length` | Arm length (inches) | Catch radius |
| `hand_size` | Hand size (inches) | Ball security |

### College Production (cfbd-derived)

| Feature | Definition | Notes |
|---------|-----------|-------|
| `dominator_rating` | Player receiving yards ÷ team passing yards (best season) | Cross-school comparability — accounts for team quality |
| `breakout_age` | Age at first season ≥20% dominator rating | Earlier breakout → better NFL projection |
| `yards_per_target` | Career college receiving yards ÷ targets | Efficiency |
| `td_rate` | TDs ÷ receptions | Red-zone/big-play ability |
| `receptions_per_game` | Career college receptions ÷ games | Volume |
| `production_seasons` | Seasons with ≥500 receiving yards | Consistency |

### Target

`pro_bowl_ever`: 1 if prospect was selected to at least one Pro Bowl during career, 0 otherwise. Expected class ratio ~1:6 across 2010–2022 draft classes (≥2023 draft: exclude from training, use as current prospects).

---

## 5. Modeling

### Class Imbalance

~1:6 positive/negative ratio. Strategy:
- `class_weight='balanced'` on all classifiers
- Stratified k-fold to preserve class ratio in each fold
- Primary eval metric: **ROC-AUC** (robust to imbalance)
- Secondary: precision-recall AUC and F1 at 0.5 threshold

### Models

| Model | Role | Why |
|-------|------|-----|
| Logistic Regression | Interpretable baseline | Coefficients provide direct "which metric matters most" story |
| XGBoost classifier | Main model | Captures non-linearities and interactions (e.g., speed matters more when dominator_rating is high) |

### Cross-Validation

Temporal splits — hold out 2–3 draft years at a time (e.g., train on 2010–2018, test on 2019–2021). Prevents leakage from data correlation across draft classes.

---

## 6. Explainability (Notebook 05)

SHAP TreeExplainer on the XGBoost model:
- **Beeswarm plot** — which features have the widest impact distribution
- **Dependence plots** — how `speed_score` interacts with `dominator_rating`
- **Individual force plots** — explain why a specific prospect scores high or low

**Key research question output:** "Which pre-draft metrics most reliably separate future Pro Bowl WRs from busts?"

---

## 7. Config File

`config/wr_analysis.json` controls:
```json
{
  "position": "WR",
  "draft_years": [2010, 2024],
  "target": "pro_bowl_ever",
  "combine_features": ["forty_time", "vertical", "broad_jump", "three_cone", "twenty_shuttle", "weight", "height", "arm_length", "hand_size"],
  "college_features": ["dominator_rating", "breakout_age", "yards_per_target", "td_rate", "receptions_per_game", "production_seasons"],
  "test_years": [2019, 2021]
}
```

---

## 8. Out of Scope

- Other positions (QB, RB, TE) — designed to add later by extending config
- Real-time data or live draft feeds
- Betting / wagering outputs
- Deep learning / sequence modeling of career trajectories
