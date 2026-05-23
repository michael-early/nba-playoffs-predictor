# NFL Prospect Success Predictor

**Research question:** Which pre-draft metrics best predict whether a WR becomes a Pro Bowl-caliber NFL player?

**Scope:** Wide receivers, 2010–2024 draft classes. Combines NFL combine athleticism measurements with college production statistics to predict `pro_bowl_ever` (binary: ever selected to a Pro Bowl).

---

## Approach

Two feature groups feed a binary classifier:

- **Athletic profile** — combine measurables: 40-yard dash, vertical, broad jump, 3-cone, speed score, height, weight, arm/hand size
- **College production** — dominator rating, breakout age, yards-per-target, TD rate, receptions-per-game

Models: Logistic Regression (interpretable baseline) + XGBoost (captures non-linearities). Evaluated by ROC-AUC with temporal cross-validation (hold out draft years, not random splits). SHAP for explainability.

---

## Data Sources

| Data | Source | Notes |
|------|--------|-------|
| Combine metrics | `nfl-data-py` → `import_combine_data()` | No key required |
| College stats | `cfbd` — College Football Data API | Free API key required: collegefootballdata.com |
| Pro Bowl outcomes | Pro Football Reference — `pandas.read_html()` | No key required |

---

## Folder Structure

```
nfl-prospect/
├── notebooks/
│   ├── 01-data-collection.ipynb
│   ├── 02-eda.ipynb
│   ├── 03-feature-engineering.ipynb
│   ├── 04-modeling.ipynb
│   └── 05-explainability.ipynb
├── scripts/
│   ├── fetch_data.py
│   └── train_model.py
├── src/
│   ├── data.py
│   ├── features.py
│   └── models.py
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── outputs/reports/
└── config/wr_analysis.json
```

---

## Setup

```bash
# From Sports/ root
source .venv/bin/activate

# Install cfbd if not already present
pip install cfbd nfl-data-py
```

Set `CFBD_API_KEY` in your environment (free key from collegefootballdata.com):

```bash
export CFBD_API_KEY=your_key_here
```

Run notebooks top-to-bottom, starting with `01-data-collection.ipynb`.

---

## Key Findings

*To be populated as analysis runs.*
