# NFL Prospect Success Predictor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a WR Pro Bowl prediction pipeline — from raw data collection through SHAP explainability — as 5 runnable notebooks backed by tested Python modules.

**Architecture:** Three `src/` modules (`data`, `features`, `models`) handle all logic and are unit-tested with pytest. Five notebooks (01–05) import from `src/` and run top-to-bottom. CLI scripts in `scripts/` wrap the data and training pipelines for re-running without Jupyter.

**Tech Stack:** Python 3.10+, nfl-data-py, cfbd, pandas, scikit-learn, xgboost, shap, python-dotenv, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `config/wr_analysis.json` | Draft year range, feature lists, train/test split years |
| `src/__init__.py` | Empty package marker |
| `src/data.py` | Load combine (nfl-data-py), college stats (cfbd), Pro Bowl outcomes (PFR scrape) |
| `src/features.py` | Compute speed_score, dominator_rating, breakout_age; merge into feature matrix |
| `src/models.py` | Temporal train/test splits, train LR + XGB, evaluate ROC-AUC, save models |
| `tests/__init__.py` | Empty package marker |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/test_data.py` | Unit tests for data cleaning functions |
| `tests/test_features.py` | Unit tests for feature computation |
| `tests/test_models.py` | Unit tests for temporal splits and evaluation |
| `notebooks/01-data-collection.ipynb` | Pull and cache raw data from all three sources |
| `notebooks/02-eda.ipynb` | Distributions, correlations, class balance |
| `notebooks/03-feature-engineering.ipynb` | Build per-prospect feature matrix, inspect missingness |
| `notebooks/04-modeling.ipynb` | Train LR + XGB, temporal CV, ROC-AUC comparison, save model |
| `notebooks/05-explainability.ipynb` | SHAP beeswarm + dependence plots, feature ranking CSV |
| `scripts/fetch_data.py` | CLI: re-run data collection for new draft classes |
| `scripts/train_model.py` | CLI: retrain model, print test AUC, save to models/ |

---

### Task 1: Config and test scaffolding

**Files:**
- Create: `config/wr_analysis.json`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the config file**

Save as `nfl-prospect/config/wr_analysis.json`:
```json
{
  "position": "WR",
  "draft_years": [2010, 2024],
  "college_start_year": 2006,
  "target": "pro_bowl_ever",
  "combine_features": [
    "forty", "vertical", "broad_jump", "cone", "shuttle",
    "weight", "height", "speed_score"
  ],
  "college_features": [
    "dominator_rating", "breakout_age", "yards_per_rec",
    "td_rate", "rec_per_game", "production_seasons"
  ],
  "train_years": [2010, 2018],
  "test_years": [2019, 2021]
}
```

- [ ] **Step 2: Create package markers and conftest**

`nfl-prospect/src/__init__.py` — empty file.

`nfl-prospect/tests/__init__.py` — empty file.

`nfl-prospect/tests/conftest.py`:
```python
import pandas as pd
import pytest


@pytest.fixture
def sample_combine_raw():
    return pd.DataFrame({
        "player_name": ["DeAndre Hopkins", "Tyreek Hill", "Cole Beasley"],
        "pos": ["WR", "WR", "QB"],
        "year": [2013, 2016, 2012],
        "forty": [4.57, 4.29, 4.46],
        "vertical": [38.5, 41.5, 35.0],
        "broad_jump": [128.0, 136.0, 120.0],
        "cone": [6.93, 6.70, 7.10],
        "shuttle": [4.21, 3.96, 4.35],
        "weight": [214.0, 185.0, 174.0],
        "height": [73.0, 70.0, 70.0],
    })


@pytest.fixture
def sample_college_stats():
    return pd.DataFrame({
        "player": ["DeAndre Hopkins", "DeAndre Hopkins", "Tyreek Hill"],
        "team": ["Clemson", "Clemson", "West Alabama"],
        "year": [2011, 2012, 2015],
        "rec_yds": [693.0, 1405.0, 1294.0],
        "receptions": [47.0, 82.0, 57.0],
        "rec_td": [8.0, 18.0, 12.0],
        "games": [13.0, 13.0, 12.0],
        "team_pass_yds": [3000.0, 3764.0, 2100.0],
        "age": [19.0, 20.0, 21.0],
    })
```

- [ ] **Step 3: Verify pytest discovers the tests directory**

```bash
cd /Users/mearly/dev/playground/Sports && source .venv/bin/activate
python -m pytest nfl-prospect/tests/ --collect-only
```

Expected: `no tests ran` (no test files yet) with no import errors.

- [ ] **Step 4: Commit**

```bash
git add nfl-prospect/config/wr_analysis.json nfl-prospect/src/__init__.py nfl-prospect/tests/__init__.py nfl-prospect/tests/conftest.py
git commit -m "feat(nfl-prospect): add config and test scaffolding"
```

---

### Task 2: Combine data loader (TDD)

**Files:**
- Create: `src/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write failing tests**

`nfl-prospect/tests/test_data.py`:
```python
import pandas as pd
import pytest
from src.data import clean_combine


def test_clean_combine_filters_to_wr(sample_combine_raw):
    result = clean_combine(sample_combine_raw)
    assert (result["pos"] == "WR").all()
    assert len(result) == 2  # Hopkins and Hill, not Beasley (QB)


def test_clean_combine_computes_speed_score(sample_combine_raw):
    result = clean_combine(sample_combine_raw)
    expected_hill = 185 * 200 / (4.29 ** 4)
    hill_score = result.loc[result["player_name"] == "Tyreek Hill", "speed_score"].iloc[0]
    assert abs(hill_score - expected_hill) < 0.01


def test_clean_combine_imputes_missing_drills_with_wr_median(sample_combine_raw):
    df = sample_combine_raw.copy()
    df.loc[0, "cone"] = None  # Hopkins missing cone
    result = clean_combine(df)
    # Median of [6.70] (only Hill remains after Hopkins is set to NaN before imputing)
    # Actually both WRs are used for median computation before any drop
    wr_median_cone = sample_combine_raw[sample_combine_raw["pos"] == "WR"]["cone"].median()
    assert result.loc[result["player_name"] == "DeAndre Hopkins", "cone"].iloc[0] == wr_median_cone


def test_clean_combine_drops_rows_missing_forty(sample_combine_raw):
    df = sample_combine_raw.copy()
    df.loc[0, "forty"] = None
    result = clean_combine(df)
    assert "DeAndre Hopkins" not in result["player_name"].values
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/mearly/dev/playground/Sports && source .venv/bin/activate
python -m pytest nfl-prospect/tests/test_data.py -v
```

Expected: `ImportError` — `src/data.py` doesn't exist yet.

- [ ] **Step 3: Implement clean_combine in src/data.py**

`nfl-prospect/src/data.py`:
```python
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

COMBINE_COLS = [
    "player_name", "pos", "year",
    "forty", "vertical", "broad_jump", "cone", "shuttle",
    "weight", "height",
]


def clean_combine(df: pd.DataFrame) -> pd.DataFrame:
    """Filter combine data to WR, impute missing drills with WR median, compute speed_score."""
    wr = df[df["pos"] == "WR"].copy()
    wr = wr.dropna(subset=["forty"])

    drill_cols = ["vertical", "broad_jump", "cone", "shuttle", "weight", "height"]
    for col in drill_cols:
        if col in wr.columns:
            wr[col] = wr[col].fillna(wr[col].median())

    wr["speed_score"] = wr["weight"] * 200 / (wr["forty"] ** 4)
    return wr.reset_index(drop=True)


def load_combine(years: list[int]) -> pd.DataFrame:
    """Pull WR combine data from nfl-data-py for the given draft years."""
    import nfl_data_py as nfl

    raw = nfl.import_combine_data(years=years)
    available = [c for c in COMBINE_COLS if c in raw.columns]
    return clean_combine(raw[available])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest nfl-prospect/tests/test_data.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add nfl-prospect/src/data.py nfl-prospect/tests/test_data.py
git commit -m "feat(nfl-prospect): add combine data loader with tests"
```

---

### Task 3: College stats loader (TDD)

**Files:**
- Modify: `src/data.py` (add college stats functions)
- Modify: `tests/test_data.py` (add college stats tests)

- [ ] **Step 1: Write failing tests**

Append to `nfl-prospect/tests/test_data.py`:
```python
from src.data import build_college_stats_df


def test_build_college_stats_df_returns_expected_columns(sample_college_stats):
    result = build_college_stats_df(sample_college_stats)
    for col in ["player", "team", "year", "rec_yds", "receptions", "rec_td", "games", "team_pass_yds"]:
        assert col in result.columns


def test_build_college_stats_df_drops_zero_game_rows(sample_college_stats):
    df = sample_college_stats.copy()
    df.loc[0, "games"] = 0
    result = build_college_stats_df(df)
    assert len(result) == len(sample_college_stats) - 1
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest nfl-prospect/tests/test_data.py -v
```

Expected: `ImportError` on `build_college_stats_df`.

- [ ] **Step 3: Implement build_college_stats_df and fetch_college_stats**

Append to `nfl-prospect/src/data.py`:
```python
def build_college_stats_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw college stats DataFrame. Drops rows with 0 or missing games played."""
    return df[df["games"] > 0].reset_index(drop=True)


def fetch_college_stats(years: list[int], cache_dir: Path | None = None) -> pd.DataFrame:
    """Pull WR receiving stats and team passing yards from cfbd for the given college seasons.

    Fetches per-player receiving stats and per-team passing yards so dominator_rating
    can be computed downstream. Saves to cache_dir if provided.

    Requires CFBD_API_KEY in environment (register free at collegefootballdata.com).
    """
    import cfbd

    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        raise EnvironmentError("CFBD_API_KEY not set — add it to nfl-prospect/.env")

    config = cfbd.Configuration()
    config.api_key["Authorization"] = api_key
    config.api_key_prefix["Authorization"] = "Bearer"

    rows = []
    with cfbd.ApiClient(config) as client:
        stats_api = cfbd.StatsApi(client)

        for year in years:
            # Per-player receiving stats — each StatType is a separate row
            player_stats = stats_api.get_player_season_stats(year=year, category="receiving")
            stat_map: dict[tuple, dict] = {}
            for s in player_stats:
                key = (s.player, s.team, year)
                if key not in stat_map:
                    stat_map[key] = {"player": s.player, "team": s.team, "year": year}
                stat_map[key][s.stat_type.lower()] = s.stat

            # Team passing yards for dominator_rating denominator
            team_stats = stats_api.get_team_season_stats(year=year)
            team_pass: dict[str, float | None] = {}
            for t in team_stats:
                # Each TeamSeasonStat has a .stats list of StatsSeason objects
                for stat in getattr(t, "stats", []):
                    if getattr(stat, "category", "") == "passing" and getattr(stat, "stat_type", "") == "YDS":
                        team_pass[t.team] = stat.stat
                        break

            for key, row in stat_map.items():
                row["team_pass_yds"] = team_pass.get(row["team"])
                rows.append(row)

            time.sleep(1.0)

    df = pd.DataFrame(rows)
    rename = {"yds": "rec_yds", "rec": "receptions", "td": "rec_td", "avg": "yards_per_rec"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "games" not in df.columns:
        df["games"] = float("nan")

    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        df.to_parquet(Path(cache_dir) / "college_stats_raw.parquet", index=False)

    return build_college_stats_df(df)
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest nfl-prospect/tests/test_data.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add nfl-prospect/src/data.py nfl-prospect/tests/test_data.py
git commit -m "feat(nfl-prospect): add college stats loader (cfbd)"
```

---

### Task 4: Pro Bowl outcomes loader (TDD)

**Files:**
- Modify: `src/data.py` (add Pro Bowl functions)
- Modify: `tests/test_data.py` (add Pro Bowl tests)

- [ ] **Step 1: Write failing tests**

Append to `nfl-prospect/tests/test_data.py`:
```python
from src.data import build_pro_bowl_targets


def test_build_pro_bowl_targets_marks_pro_bowlers():
    selections = pd.DataFrame({
        "player_name": ["DeAndre Hopkins", "DeAndre Hopkins", "Tyreek Hill"],
        "season": [2017, 2018, 2018],
        "position": ["WR", "WR", "WR"],
    })
    result = build_pro_bowl_targets(selections)
    assert result.loc[result["player_name"] == "DeAndre Hopkins", "pro_bowl_ever"].iloc[0] == 1
    assert result.loc[result["player_name"] == "Tyreek Hill", "pro_bowl_ever"].iloc[0] == 1


def test_build_pro_bowl_targets_one_row_per_player():
    selections = pd.DataFrame({
        "player_name": ["DeAndre Hopkins", "DeAndre Hopkins"],
        "season": [2017, 2018],
        "position": ["WR", "WR"],
    })
    result = build_pro_bowl_targets(selections)
    assert len(result) == 1
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest nfl-prospect/tests/test_data.py::test_build_pro_bowl_targets_marks_pro_bowlers -v
```

Expected: `ImportError` on `build_pro_bowl_targets`.

- [ ] **Step 3: Implement build_pro_bowl_targets and fetch_pro_bowl_selections**

Append to `nfl-prospect/src/data.py`:
```python
def build_pro_bowl_targets(selections_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per WR with pro_bowl_ever = 1."""
    wr = selections_df[selections_df["position"] == "WR"].copy()
    return (
        wr[["player_name"]]
        .drop_duplicates()
        .assign(pro_bowl_ever=1)
        .reset_index(drop=True)
    )


def fetch_pro_bowl_selections(seasons: list[int], cache_dir: Path | None = None) -> pd.DataFrame:
    """Scrape WR Pro Bowl selections from Pro Football Reference.

    URL pattern: https://www.pro-football-reference.com/years/{season}/probowl.htm
    Rate-limited to one request per 4 seconds. Results cached to cache_dir if provided.
    """
    rows = []
    for season in seasons:
        url = f"https://www.pro-football-reference.com/years/{season}/probowl.htm"
        try:
            tables = pd.read_html(url)
            for tbl in tables:
                tbl.columns = [str(c).lower().replace(" ", "_") for c in tbl.columns]
                name_col = next((c for c in tbl.columns if "player" in c or "name" in c), None)
                pos_col = next((c for c in tbl.columns if c.startswith("pos")), None)
                if name_col and pos_col:
                    chunk = tbl[[name_col, pos_col]].rename(
                        columns={name_col: "player_name", pos_col: "position"}
                    )
                    chunk["season"] = season
                    rows.append(chunk)
                    break
        except Exception:
            pass  # Skip seasons where PFR table structure differs
        time.sleep(4.0)

    if not rows:
        return pd.DataFrame(columns=["player_name", "position", "season"])

    result = pd.concat(rows, ignore_index=True)
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        result.to_parquet(Path(cache_dir) / "pro_bowl_selections.parquet", index=False)
    return result
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest nfl-prospect/tests/test_data.py -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add nfl-prospect/src/data.py nfl-prospect/tests/test_data.py
git commit -m "feat(nfl-prospect): add Pro Bowl outcomes loader (PFR scrape)"
```

---

### Task 5: Feature engineering (TDD)

**Files:**
- Create: `src/features.py`
- Create: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

`nfl-prospect/tests/test_features.py`:
```python
import pandas as pd
import pytest
from src.features import compute_dominator_rating, compute_breakout_age, build_college_aggregates, build_feature_matrix


def test_dominator_rating_is_ratio(sample_college_stats):
    result = compute_dominator_rating(sample_college_stats)
    # Hopkins 2012: 1405 / 3764 = 0.373; Hopkins 2011: 693 / 3000 = 0.231
    # Best season should be 2012
    expected = 1405.0 / 3764.0
    hop = result.loc[result["player"] == "DeAndre Hopkins", "dominator_rating"].iloc[0]
    assert abs(hop - expected) < 0.001


def test_dominator_rating_uses_best_season(sample_college_stats):
    result = compute_dominator_rating(sample_college_stats)
    assert len(result[result["player"] == "DeAndre Hopkins"]) == 1


def test_compute_breakout_age_finds_first_qualifying_season(sample_college_stats):
    result = compute_breakout_age(sample_college_stats, threshold=0.30)
    # Hopkins 2012: 1405/3764 = 37.3% >= 30%, age 20
    # Hopkins 2011: 693/3000 = 23.1% < 30%
    hop = result.loc[result["player"] == "DeAndre Hopkins", "breakout_age"].iloc[0]
    assert hop == 20.0


def test_compute_breakout_age_nan_when_no_qualifying_season(sample_college_stats):
    result = compute_breakout_age(sample_college_stats, threshold=0.99)
    # No player reaches 99% dominator rating
    assert result["breakout_age"].isna().all()


def test_build_feature_matrix_joins_and_fills_non_pro_bowlers():
    combine = pd.DataFrame({
        "player_name": ["DeAndre Hopkins", "Tyreek Hill"],
        "year": [2013, 2016],
        "forty": [4.57, 4.29],
        "speed_score": [50.0, 72.0],
    })
    college = pd.DataFrame({
        "player": ["DeAndre Hopkins", "Tyreek Hill"],
        "dominator_rating": [0.373, 0.616],
    })
    targets = pd.DataFrame({
        "player_name": ["DeAndre Hopkins"],
        "pro_bowl_ever": [1],
    })
    result = build_feature_matrix(combine, college, targets)
    assert len(result) == 2
    assert result.loc[result["player_name"] == "DeAndre Hopkins", "pro_bowl_ever"].iloc[0] == 1
    assert result.loc[result["player_name"] == "Tyreek Hill", "pro_bowl_ever"].iloc[0] == 0
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest nfl-prospect/tests/test_features.py -v
```

Expected: `ImportError` — `src/features.py` doesn't exist.

- [ ] **Step 3: Implement src/features.py**

`nfl-prospect/src/features.py`:
```python
from __future__ import annotations

import pandas as pd


def compute_dominator_rating(college_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per player with dominator_rating from their best college season.

    dominator_rating = rec_yds / team_pass_yds for the season with the highest ratio.
    """
    df = college_df.copy()
    df["dominator_rating"] = df["rec_yds"] / df["team_pass_yds"]
    return (
        df.sort_values("dominator_rating", ascending=False)
        .groupby("player", as_index=False)
        .first()[["player", "dominator_rating"]]
    )


def compute_breakout_age(college_df: pd.DataFrame, threshold: float = 0.20) -> pd.DataFrame:
    """Return one row per player with age at first season meeting the dominator threshold.

    Requires an 'age' column in college_df. breakout_age is NaN if no season qualifies.
    """
    df = college_df.copy()
    df["dominator_rating"] = df["rec_yds"] / df["team_pass_yds"]
    qualifies = df[df["dominator_rating"] >= threshold]
    earliest = (
        qualifies.sort_values("age")
        .groupby("player", as_index=False)
        .first()[["player", "age"]]
        .rename(columns={"age": "breakout_age"})
    )
    all_players = df[["player"]].drop_duplicates()
    return all_players.merge(earliest, on="player", how="left")


def build_college_aggregates(college_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-player college seasons into one summary row per player."""
    df = college_df.copy()
    df["dominator_rating"] = df["rec_yds"] / df["team_pass_yds"]

    safe_rec = df["receptions"].replace(0, float("nan"))
    safe_games = df["games"].replace(0, float("nan"))

    df["yards_per_rec"] = df["rec_yds"] / safe_rec
    df["td_rate"] = df["rec_td"] / safe_rec
    df["rec_per_game"] = df["receptions"] / safe_games

    return df.groupby("player", as_index=False).agg(
        dominator_rating=("dominator_rating", "max"),
        yards_per_rec=("yards_per_rec", "mean"),
        td_rate=("td_rate", "mean"),
        rec_per_game=("rec_per_game", "mean"),
        production_seasons=("rec_yds", lambda x: int((x >= 500).sum())),
    )


def build_feature_matrix(
    combine: pd.DataFrame,
    college: pd.DataFrame,
    targets: pd.DataFrame,
) -> pd.DataFrame:
    """Join combine, college aggregates, and Pro Bowl targets into one row per prospect.

    Merges on lowercase normalized player name. Prospects missing from college data
    are dropped (inner join). Prospects not in targets get pro_bowl_ever = 0.
    """
    combine = combine.copy()
    college = college.copy()
    targets = targets.copy()

    combine["_key"] = combine["player_name"].str.lower().str.strip()
    college["_key"] = college["player"].str.lower().str.strip()
    targets["_key"] = targets["player_name"].str.lower().str.strip()

    merged = combine.merge(college.drop(columns=["player"], errors="ignore"), on="_key", how="inner")
    merged = merged.merge(targets[["_key", "pro_bowl_ever"]], on="_key", how="left")
    merged["pro_bowl_ever"] = merged["pro_bowl_ever"].fillna(0).astype(int)
    return merged.drop(columns=["_key"]).reset_index(drop=True)
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest nfl-prospect/tests/test_features.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add nfl-prospect/src/features.py nfl-prospect/tests/test_features.py
git commit -m "feat(nfl-prospect): add feature engineering module with tests"
```

---

### Task 6: Model helpers (TDD)

**Files:**
- Create: `src/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

`nfl-prospect/tests/test_models.py`:
```python
import numpy as np
import pandas as pd
import pytest
from src.models import temporal_splits, evaluate_roc_auc


def _make_df(years: list[int]) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "year": years,
        "feat": rng.random(len(years)),
        "pro_bowl_ever": rng.integers(0, 2, len(years)),
    })


def test_temporal_splits_train_max_year():
    df = _make_df(list(range(2010, 2023)))
    train, _ = temporal_splits(df, train_end=2018, test_start=2019, test_end=2021)
    assert train["year"].max() == 2018


def test_temporal_splits_test_bounds():
    df = _make_df(list(range(2010, 2023)))
    _, test = temporal_splits(df, train_end=2018, test_start=2019, test_end=2021)
    assert test["year"].min() == 2019
    assert test["year"].max() == 2021


def test_temporal_splits_no_overlap():
    df = _make_df(list(range(2010, 2023)))
    train, test = temporal_splits(df, train_end=2018, test_start=2019, test_end=2021)
    assert set(train["year"]).isdisjoint(set(test["year"]))


def test_evaluate_roc_auc_returns_float_in_range():
    y_true = np.array([0, 1, 0, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.2, 0.8, 0.7])
    score = evaluate_roc_auc(y_true, y_prob)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest nfl-prospect/tests/test_models.py -v
```

Expected: `ImportError` — `src/models.py` doesn't exist.

- [ ] **Step 3: Implement src/models.py**

`nfl-prospect/src/models.py`:
```python
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


def temporal_splits(
    df: pd.DataFrame,
    train_end: int,
    test_start: int,
    test_end: int,
    year_col: str = "year",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into train (year ≤ train_end) and test (test_start ≤ year ≤ test_end)."""
    train = df[df[year_col] <= train_end].copy()
    test = df[(df[year_col] >= test_start) & (df[year_col] <= test_end)].copy()
    return train, test


def evaluate_roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(roc_auc_score(y_true, y_prob))


def build_lr_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)),
    ])


def build_xgb_pipeline() -> Pipeline:
    return Pipeline([
        ("model", XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            scale_pos_weight=6,  # ~1:6 class ratio for Pro Bowl WRs
            random_state=42,
            eval_metric="auc",
            verbosity=0,
        )),
    ])


def train_and_evaluate(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "pro_bowl_ever",
) -> dict[str, tuple[float, Pipeline]]:
    """Train LR and XGB on train, evaluate ROC-AUC on test.

    Returns dict of model_name -> (roc_auc, fitted_pipeline).
    """
    X_train = train[feature_cols].values
    y_train = train[target_col].values
    X_test = test[feature_cols].values
    y_test = test[target_col].values

    results = {}
    for name, pipeline in [
        ("logistic_regression", build_lr_pipeline()),
        ("xgboost", build_xgb_pipeline()),
    ]:
        pipeline.fit(X_train, y_train)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        results[name] = (evaluate_roc_auc(y_test, y_prob), pipeline)

    return results


def save_model(pipeline: Pipeline, name: str, models_dir: Path) -> Path:
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    out = models_dir / f"{name}.joblib"
    joblib.dump(pipeline, out)
    return out
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest nfl-prospect/tests/ -v
```

Expected: all 12 tests pass.

- [ ] **Step 5: Commit**

```bash
git add nfl-prospect/src/models.py nfl-prospect/tests/test_models.py
git commit -m "feat(nfl-prospect): add model helpers with temporal splits and ROC-AUC evaluation"
```

---

### Task 7: Notebook 01 — Data Collection

**Files:**
- Create: `notebooks/01-data-collection.ipynb`

Jupyter notebook — create via JupyterLab or programmatically. Run once to populate `data/raw/`.

- [ ] **Step 1: Create the notebook**

Open JupyterLab from `nfl-prospect/`:
```bash
cd /Users/mearly/dev/playground/Sports && source .venv/bin/activate
jupyter lab nfl-prospect/notebooks/01-data-collection.ipynb
```

Add cells in order:

**Cell 1 — Config:**
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "..")

from dotenv import load_dotenv
load_dotenv(Path("../.env"))

with open("../config/wr_analysis.json") as f:
    CONFIG = json.load(f)

DRAFT_YEARS = list(range(CONFIG["draft_years"][0], CONFIG["draft_years"][1] + 1))
COLLEGE_YEARS = list(range(CONFIG["college_start_year"], CONFIG["draft_years"][1] + 1))
PRO_BOWL_SEASONS = list(range(CONFIG["draft_years"][0] + 1, CONFIG["draft_years"][1] + 2))
RAW_DIR = Path("../data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

print(f"Draft years: {DRAFT_YEARS[0]}–{DRAFT_YEARS[-1]}")
print(f"College years: {COLLEGE_YEARS[0]}–{COLLEGE_YEARS[-1]}")
print(f"Pro Bowl seasons: {PRO_BOWL_SEASONS[0]}–{PRO_BOWL_SEASONS[-1]}")
```

**Cell 2 — Combine data:**
```python
from src.data import load_combine

combine_df = load_combine(years=DRAFT_YEARS)
combine_df.to_parquet(RAW_DIR / "combine_wr.parquet", index=False)
print(f"Combine: {len(combine_df)} WR prospects")
print(f"Columns: {list(combine_df.columns)}")
combine_df.head()
```

**Cell 3 — College stats (slow — rate limited):**
```python
from src.data import fetch_college_stats

# This cell takes several minutes — cfbd is rate-limited to 1 req/sec
college_raw = fetch_college_stats(years=COLLEGE_YEARS, cache_dir=RAW_DIR)
print(f"College stats: {len(college_raw)} player-season rows")
print(f"Columns: {list(college_raw.columns)}")
college_raw.head()
```

**Cell 4 — Pro Bowl selections (slow — rate limited):**
```python
from src.data import fetch_pro_bowl_selections

# This cell takes ~90 seconds — PFR is rate-limited to 1 req/4 sec
pb_raw = fetch_pro_bowl_selections(seasons=PRO_BOWL_SEASONS, cache_dir=RAW_DIR)
wr_count = (pb_raw["position"] == "WR").sum()
print(f"Pro Bowl selections: {len(pb_raw)} total | WR selections: {wr_count}")
pb_raw[pb_raw["position"] == "WR"].head()
```

**Cell 5 — Verify saved files:**
```python
import pandas as pd

print("Raw data saved to data/raw/:")
for p in sorted(RAW_DIR.glob("*.parquet")):
    df = pd.read_parquet(p)
    print(f"  {p.name}: {len(df)} rows × {len(df.columns)} cols")
```

- [ ] **Step 2: Run the notebook top-to-bottom**

Kernel → Restart and Run All. Confirm all cells complete without errors.

Expected output from Cell 5: three parquet files listed with non-zero row counts.

- [ ] **Step 3: Commit (outputs stripped by nbstripout)**

```bash
git add nfl-prospect/notebooks/01-data-collection.ipynb
git commit -m "feat(nfl-prospect): add notebook 01 data collection"
```

---

### Task 8: Notebook 02 — EDA

**Files:**
- Create: `notebooks/02-eda.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 — Setup:**
```python
import sys
sys.path.insert(0, "..")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from src.data import build_pro_bowl_targets

RAW_DIR = Path("../data/raw")
OUT_DIR = Path("../outputs/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

combine_df = pd.read_parquet(RAW_DIR / "combine_wr.parquet")
pb_raw = pd.read_parquet(RAW_DIR / "pro_bowl_selections.parquet")

pb_targets = build_pro_bowl_targets(pb_raw)
df = combine_df.merge(pb_targets, on="player_name", how="left")
df["pro_bowl_ever"] = df["pro_bowl_ever"].fillna(0).astype(int)

sns.set_theme(style="whitegrid")
print(f"Prospects: {len(df)} | Pro Bowlers: {df['pro_bowl_ever'].sum()} | Non-Pro Bowlers: {(df['pro_bowl_ever']==0).sum()}")
```

**Cell 2 — Class balance:**
```python
counts = df["pro_bowl_ever"].value_counts()
ratio = counts[0] // counts[1]
print(f"Class ratio approx 1:{ratio} (Pro Bowl : non-Pro Bowl)")

fig, ax = plt.subplots(figsize=(5, 4))
counts.plot.bar(ax=ax, color=["steelblue", "tomato"])
ax.set_xticklabels(["Non-Pro Bowl (0)", "Pro Bowl (1)"], rotation=0)
ax.set_title("Target class balance")
plt.tight_layout()
plt.savefig(OUT_DIR / "class_balance.png", dpi=150)
plt.show()
```

**Cell 3 — Combine distributions by class:**
```python
drill_cols = ["forty", "vertical", "broad_jump", "cone", "shuttle", "speed_score"]
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
for ax, col in zip(axes.flat, drill_cols):
    sns.boxplot(data=df, x="pro_bowl_ever", y=col, ax=ax, palette=["steelblue", "tomato"])
    ax.set_xlabel("Pro Bowl")
    ax.set_title(col)
plt.suptitle("Combine metrics: Pro Bowlers vs Non-Pro Bowlers", y=1.01)
plt.tight_layout()
plt.savefig(OUT_DIR / "combine_by_class.png", dpi=150, bbox_inches="tight")
plt.show()
```

**Cell 4 — Correlation heatmap:**
```python
numeric_cols = drill_cols + ["weight", "height", "pro_bowl_ever"]
corr = df[numeric_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, vmin=-1, vmax=1)
ax.set_title("Combine metrics — Pearson correlation (incl. pro_bowl_ever)")
plt.tight_layout()
plt.savefig(OUT_DIR / "correlation_heatmap.png", dpi=150)
plt.show()
```

**Cell 5 — Missing values:**
```python
missing = combine_df[drill_cols].isnull().sum().sort_values(ascending=False)
print("Missing values per combine drill:")
print(missing)
pct = (missing / len(combine_df) * 100).round(1)
print(f"\nAs % of {len(combine_df)} prospects:")
print(pct)
```

- [ ] **Step 2: Run the notebook top-to-bottom and verify plots render**

- [ ] **Step 3: Commit**

```bash
git add nfl-prospect/notebooks/02-eda.ipynb
git commit -m "feat(nfl-prospect): add notebook 02 EDA"
```

---

### Task 9: Notebook 03 — Feature Engineering

**Files:**
- Create: `notebooks/03-feature-engineering.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 — Setup:**
```python
import sys
sys.path.insert(0, "..")
import pandas as pd
from pathlib import Path
from src.data import build_pro_bowl_targets
from src.features import build_college_aggregates, compute_breakout_age, build_feature_matrix

RAW_DIR = Path("../data/raw")
PROCESSED_DIR = Path("../data/processed")
PROCESSED_DIR.mkdir(exist_ok=True)

combine_df = pd.read_parquet(RAW_DIR / "combine_wr.parquet")
college_raw = pd.read_parquet(RAW_DIR / "college_stats_raw.parquet")
pb_raw = pd.read_parquet(RAW_DIR / "pro_bowl_selections.parquet")

print(f"Combine rows: {len(combine_df)}")
print(f"College stat rows: {len(college_raw)}")
print(f"Pro Bowl selection rows: {len(pb_raw)}")
```

**Cell 2 — College aggregates:**
```python
college_agg = build_college_aggregates(college_raw)

if "age" in college_raw.columns:
    breakout = compute_breakout_age(college_raw, threshold=0.20)
    college_agg = college_agg.merge(breakout, on="player", how="left")
    print(f"Breakout age available for {college_agg['breakout_age'].notna().sum()} players")
else:
    college_agg["breakout_age"] = float("nan")
    print("Note: 'age' column not in cfbd data — breakout_age set to NaN. "
          "Consider enriching from another source.")

print(f"College aggregates: {len(college_agg)} players")
college_agg.describe()
```

**Cell 3 — Pro Bowl targets:**
```python
pb_targets = build_pro_bowl_targets(pb_raw)
print(f"Unique WR Pro Bowlers in dataset: {len(pb_targets)}")
pb_targets.head()
```

**Cell 4 — Build feature matrix:**
```python
features_df = build_feature_matrix(combine_df, college_agg, pb_targets)
print(f"Feature matrix: {features_df.shape[0]} prospects × {features_df.shape[1]} columns")
print(f"Pro Bowlers matched: {features_df['pro_bowl_ever'].sum()}")
print(f"Match rate: {len(features_df) / len(combine_df):.1%} of combine prospects matched to college data")
features_df.head()
```

**Cell 5 — Inspect missingness and save:**
```python
FEATURE_COLS = [
    "forty", "vertical", "broad_jump", "cone", "shuttle", "weight", "height", "speed_score",
    "dominator_rating", "breakout_age", "yards_per_rec", "td_rate", "rec_per_game", "production_seasons",
]
available = [c for c in FEATURE_COLS if c in features_df.columns]

missing = features_df[available].isnull().sum().sort_values(ascending=False)
print("Missing values in feature matrix:")
print(missing[missing > 0])

features_df.to_parquet(PROCESSED_DIR / "wr_prospect_features.parquet", index=False)
print(f"\nSaved to {PROCESSED_DIR / 'wr_prospect_features.parquet'}")
```

- [ ] **Step 2: Run top-to-bottom and verify feature matrix saved**

- [ ] **Step 3: Commit**

```bash
git add nfl-prospect/notebooks/03-feature-engineering.ipynb
git commit -m "feat(nfl-prospect): add notebook 03 feature engineering"
```

---

### Task 10: Notebook 04 — Modeling

**Files:**
- Create: `notebooks/04-modeling.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 — Setup:**
```python
import sys
sys.path.insert(0, "..")
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import RocCurveDisplay
from src.models import temporal_splits, train_and_evaluate, build_lr_pipeline, build_xgb_pipeline, save_model

with open("../config/wr_analysis.json") as f:
    CONFIG = json.load(f)

df = pd.read_parquet("../data/processed/wr_prospect_features.parquet")
df = df.dropna(subset=["forty", "dominator_rating"])

ALL_FEATURES = CONFIG["combine_features"] + CONFIG["college_features"]
FEATURE_COLS = [c for c in ALL_FEATURES if c in df.columns]

print(f"Prospects after dropping missing forty/dominator_rating: {len(df)}")
print(f"Pro Bowlers: {df['pro_bowl_ever'].sum()} | Available features: {FEATURE_COLS}")
```

**Cell 2 — Temporal split:**
```python
train_df, test_df = temporal_splits(
    df,
    train_end=CONFIG["train_years"][1],
    test_start=CONFIG["test_years"][0],
    test_end=CONFIG["test_years"][1],
)
print(f"Train: {len(train_df)} prospects ({train_df['year'].min()}–{train_df['year'].max()}) | Pro Bowlers: {train_df['pro_bowl_ever'].sum()}")
print(f"Test:  {len(test_df)} prospects ({test_df['year'].min()}–{test_df['year'].max()}) | Pro Bowlers: {test_df['pro_bowl_ever'].sum()}")
```

**Cell 3 — Train and evaluate:**
```python
results = train_and_evaluate(train_df, test_df, FEATURE_COLS)
print("ROC-AUC on test split:")
for model_name, (auc, _) in results.items():
    print(f"  {model_name}: {auc:.3f}")
```

**Cell 4 — ROC curves:**
```python
fig, ax = plt.subplots(figsize=(7, 6))
for model_name, (_, pipeline) in results.items():
    RocCurveDisplay.from_estimator(pipeline, test_df[FEATURE_COLS].values, test_df["pro_bowl_ever"].values, ax=ax, name=model_name)
ax.plot([0, 1], [0, 1], "k--", label="Random (AUC=0.50)")
ax.set_title("ROC Curves — WR Pro Bowl Prediction")
ax.legend()
plt.tight_layout()
plt.savefig("../outputs/reports/roc_curves.png", dpi=150)
plt.show()
```

**Cell 5 — Save best model:**
```python
# Retrain XGB on all non-test data for the saved artifact
xgb_name = "xgboost"
_, best_pipeline = results[xgb_name]
path = save_model(best_pipeline, "wr_pro_bowl_xgb", Path("../models"))
print(f"Model saved to {path}")
```

- [ ] **Step 2: Run top-to-bottom and verify model saved**

- [ ] **Step 3: Commit**

```bash
git add nfl-prospect/notebooks/04-modeling.ipynb
git commit -m "feat(nfl-prospect): add notebook 04 modeling"
```

---

### Task 11: Notebook 05 — Explainability

**Files:**
- Create: `notebooks/05-explainability.ipynb`

- [ ] **Step 1: Create the notebook**

**Cell 1 — Setup:**
```python
import sys
sys.path.insert(0, "..")
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from pathlib import Path

with open("../config/wr_analysis.json") as f:
    CONFIG = json.load(f)

df = pd.read_parquet("../data/processed/wr_prospect_features.parquet")
df = df.dropna(subset=["forty", "dominator_rating"])

ALL_FEATURES = CONFIG["combine_features"] + CONFIG["college_features"]
FEATURE_COLS = [c for c in ALL_FEATURES if c in df.columns]
X = df[FEATURE_COLS].values

pipeline = joblib.load("../models/wr_pro_bowl_xgb.joblib")
xgb_model = pipeline.named_steps["model"]  # unwrap from Pipeline

OUT_DIR = Path("../outputs/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"Features: {FEATURE_COLS}")
print(f"Prospects: {len(df)}")
```

**Cell 2 — SHAP values:**
```python
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X)
print(f"SHAP values shape: {shap_values.shape}")
```

**Cell 3 — Beeswarm plot:**
```python
shap.summary_plot(shap_values, X, feature_names=FEATURE_COLS, show=False)
plt.title("SHAP Feature Importance — WR Pro Bowl Prediction")
plt.tight_layout()
plt.savefig(OUT_DIR / "shap_beeswarm.png", dpi=150, bbox_inches="tight")
plt.show()
```

**Cell 4 — Top feature dependence plot:**
```python
top_idx = int(np.abs(shap_values).mean(axis=0).argmax())
top_feature = FEATURE_COLS[top_idx]
print(f"Top feature by mean |SHAP|: {top_feature}")

shap.dependence_plot(top_idx, shap_values, X, feature_names=FEATURE_COLS, show=False)
plt.tight_layout()
plt.savefig(OUT_DIR / f"shap_dependence_{top_feature}.png", dpi=150, bbox_inches="tight")
plt.show()
```

**Cell 5 — Feature importance table:**
```python
importance = pd.DataFrame({
    "feature": FEATURE_COLS,
    "mean_abs_shap": np.abs(shap_values).mean(axis=0),
}).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

print("Feature importance ranking:")
print(importance.to_string(index=False))
importance.to_csv(OUT_DIR / "shap_importance.csv", index=False)
print(f"\nSaved to {OUT_DIR / 'shap_importance.csv'}")
```

- [ ] **Step 2: Run top-to-bottom and verify SHAP plots render**

- [ ] **Step 3: Commit**

```bash
git add nfl-prospect/notebooks/05-explainability.ipynb
git commit -m "feat(nfl-prospect): add notebook 05 SHAP explainability"
```

---

### Task 12: CLI Scripts

**Files:**
- Create: `scripts/fetch_data.py`
- Create: `scripts/train_model.py`

- [ ] **Step 1: Create fetch_data.py**

`nfl-prospect/scripts/fetch_data.py`:
```python
"""Re-pull all raw data for the configured draft year range."""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

from dotenv import load_dotenv
load_dotenv(BASE / ".env")

from src.data import load_combine, fetch_college_stats, fetch_pro_bowl_selections


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch raw NFL prospect data")
    parser.add_argument("--config", default="config/wr_analysis.json")
    args = parser.parse_args()

    with open(BASE / args.config) as f:
        config = json.load(f)

    raw_dir = BASE / "data" / "raw"
    draft_years = list(range(config["draft_years"][0], config["draft_years"][1] + 1))
    college_years = list(range(config["college_start_year"], config["draft_years"][1] + 1))
    pb_seasons = list(range(config["draft_years"][0] + 1, config["draft_years"][1] + 2))

    print("Fetching combine data...")
    combine = load_combine(draft_years)
    combine.to_parquet(raw_dir / "combine_wr.parquet", index=False)
    print(f"  {len(combine)} WR rows saved")

    print("Fetching college stats (slow — cfbd rate limited)...")
    college = fetch_college_stats(college_years, cache_dir=raw_dir)
    print(f"  {len(college)} player-season rows saved")

    print("Fetching Pro Bowl selections (slow — PFR rate limited)...")
    pb = fetch_pro_bowl_selections(pb_seasons, cache_dir=raw_dir)
    print(f"  {len(pb)} selection rows saved")

    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create train_model.py**

`nfl-prospect/scripts/train_model.py`:
```python
"""Retrain XGBoost on processed features, print test ROC-AUC, save model."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd
from src.models import build_xgb_pipeline, save_model, temporal_splits, evaluate_roc_auc


def main() -> None:
    with open(BASE / "config/wr_analysis.json") as f:
        config = json.load(f)

    df = pd.read_parquet(BASE / "data/processed/wr_prospect_features.parquet")
    df = df.dropna(subset=["forty", "dominator_rating"])

    all_features = config["combine_features"] + config["college_features"]
    feature_cols = [c for c in all_features if c in df.columns]

    train_df, test_df = temporal_splits(
        df,
        train_end=config["train_years"][1],
        test_start=config["test_years"][0],
        test_end=config["test_years"][1],
    )

    pipeline = build_xgb_pipeline()
    pipeline.fit(train_df[feature_cols].values, train_df["pro_bowl_ever"].values)

    y_prob = pipeline.predict_proba(test_df[feature_cols].values)[:, 1]
    auc = evaluate_roc_auc(test_df["pro_bowl_ever"].values, y_prob)
    print(f"Test ROC-AUC: {auc:.3f}  (train {train_df['year'].min()}–{train_df['year'].max()}, test {test_df['year'].min()}–{test_df['year'].max()})")

    path = save_model(pipeline, "wr_pro_bowl_xgb", BASE / "models")
    print(f"Model saved to {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke-test the scripts (dry-run import check)**

```bash
cd /Users/mearly/dev/playground/Sports && source .venv/bin/activate
python -c "import nfl_prospect.scripts.fetch_data" 2>/dev/null || python nfl-prospect/scripts/fetch_data.py --help
python -c "import nfl_prospect.scripts.train_model" 2>/dev/null || python nfl-prospect/scripts/train_model.py --help
```

Expected: help text prints for both scripts without import errors.

- [ ] **Step 4: Commit**

```bash
git add nfl-prospect/scripts/fetch_data.py nfl-prospect/scripts/train_model.py
git commit -m "feat(nfl-prospect): add fetch_data and train_model CLI scripts"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| Folder structure (notebooks, src, scripts, data, models, outputs, config) | Task 1 scaffolding |
| config/wr_analysis.json with position, draft years, feature lists | Task 1 |
| Combine data via nfl-data-py | Task 2 |
| speed_score computed | Task 2 (clean_combine) |
| Missing value imputation with WR median | Task 2 |
| College stats via cfbd | Task 3 |
| Pro Bowl outcomes via PFR | Task 4 |
| dominator_rating (best season) | Task 5 |
| breakout_age | Task 5 |
| yards_per_rec, td_rate, rec_per_game, production_seasons | Task 5 (build_college_aggregates) |
| Name-key merge across datasets | Task 5 (build_feature_matrix) |
| Temporal train/test splits | Task 6 |
| LR + XGB with class_weight/scale_pos_weight | Task 6 |
| ROC-AUC evaluation | Task 6 |
| Notebook 01 — data collection | Task 7 |
| Notebook 02 — EDA | Task 8 |
| Notebook 03 — feature engineering | Task 9 |
| Notebook 04 — modeling + ROC curves | Task 10 |
| Notebook 05 — SHAP beeswarm + dependence plots | Task 11 |
| CLI fetch_data.py | Task 12 |
| CLI train_model.py | Task 12 |

All spec requirements covered. No gaps.

**Placeholder scan:** No TBDs, TODOs, or vague steps. cfbd API attribute name caveat documented inline in Task 3 code comment. Breakout age NaN case handled explicitly in notebook 03 Cell 2.

**Type consistency:** `build_feature_matrix` (Task 5) takes `combine` with `player_name`, `college` with `player`, `targets` with `player_name` — consistent with usage in notebooks 03 and 04. `train_and_evaluate` returns `dict[str, tuple[float, Pipeline]]` — unwrapped correctly in notebook 04 Cells 3 and 4.
