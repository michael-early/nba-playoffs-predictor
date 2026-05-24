# Phase 2: NFL Data Pipeline - Pattern Map

**Mapped:** 2026-05-23
**Files analyzed:** 2
**Analogs found:** 2 / 2

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `nfl/pipeline.py` | service + CLI script | batch / request-response | `nba-playoffs/scripts/retrain_series_xgboost.py` + `nba-playoffs/src/data.py` | role-match (script structure from retrain; fetch-then-cache pattern from data.py) |
| `nfl/nfl_eda.ipynb` | notebook | batch / transform | `nba-playoffs/notebooks/02-eda.ipynb` (structure); patterns extracted below from existing scripts | role-match |

---

## Pattern Assignments

### `nfl/pipeline.py` (CLI script / data pipeline, batch)

**Primary analog:** `nba-playoffs/scripts/retrain_series_xgboost.py` (argparse + `from __future__ import annotations` + `if __name__ == "__main__": raise SystemExit(main())`)

**Secondary analog:** `nba-playoffs/src/data.py` (fetch-then-cache pattern; parquet write; `force` flag)

**Note on key difference:** `nba-playoffs/src/data.py` uses its own ad-hoc parquet write. `nfl/pipeline.py` must use `shared.cache.load_or_fetch` exclusively — do not copy the manual `df.to_parquet(cache, index=False)` pattern from `data.py`. The `load_or_fetch` wrapper handles atomic writes and key validation.

---

**Imports pattern** (`nba-playoffs/scripts/retrain_series_xgboost.py`, lines 1-9):
```python
#!/usr/bin/env python3
"""Retrain series XGBoost with derived context features."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
```

**Adaptation for `nfl/pipeline.py`:**
```python
#!/usr/bin/env python3
"""nfl/pipeline.py — Build NFL Combine + Career Stats joined parquet."""

from __future__ import annotations

import argparse

import nflreadpy as nfl
import polars as pl

from shared.cache import load_or_fetch
```

Note: No `sys.path.insert` in the script — scripts run from project root (`python nfl/pipeline.py`). `sys.path` manipulation belongs only in notebooks.

---

**Module-level constants pattern** (project convention: "config cells first", adapted for scripts; see `nfl/README.md` and CONTEXT.md D-06):
```python
# Place immediately after imports — before any function definitions
START_SEASON: int = 2000
END_SEASON: int = 2023

SEASONS = list(range(START_SEASON, END_SEASON + 1))
CACHE_KEY = f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"

POSITION_GROUP_MAP = {
    "QB": "QB",
    "RB": "RB", "FB": "RB",
    "WR": "WR/TE", "TE": "WR/TE",
    "OT": "OL", "OG": "OL", "C": "OL", "OL": "OL",
    "DE": "DL", "DT": "DL", "DL": "DL", "EDGE": "DL",
    "OLB": "LB", "ILB": "LB", "LB": "LB",
    "CB": "DB", "S": "DB", "DB": "DB",
}
```

Cache key is parameterized from constants (not hardcoded string) so changing `START_SEASON`/`END_SEASON` automatically invalidates the cache.

---

**Fetch + cache core pattern** (`shared/cache.py` lines 25-31 + `nba-playoffs/src/data.py` fetch structure):

`load_or_fetch` signature (copy from `shared/cache.py` lines 25-31):
```python
def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
    *,
    cache_dir: Path = CACHE_DIR,
) -> pd.DataFrame:
```

Wrap the entire build (two nflreadpy calls + in-memory join) in a single `fetch_fn` named `_build_dataset`. This is the approved pattern — `load_or_fetch` calls it only on cache miss.

```python
def _build_dataset() -> pd.DataFrame:
    print("Fetching combine data...", end=" ", flush=True)
    combine = nfl.load_combine(SEASONS)
    print(f"done ({len(combine)} rows)")

    print("Fetching draft picks (career stats)...", end=" ", flush=True)
    picks = nfl.load_draft_picks(SEASONS)
    picks_slim = picks.select([
        "pfr_player_id", "w_av", "allpro", "probowls", "dr_av", "hof",
    ])
    print(f"done ({len(picks_slim)} rows)")

    print("Joining...", end=" ", flush=True)
    joined = combine.join(
        picks_slim,
        left_on="pfr_id",
        right_on="pfr_player_id",
        how="left",
    ).with_columns([
        pl.col("pos")
          .replace_strict(POSITION_GROUP_MAP, default="Other")
          .alias("position_group"),
        pl.when(pl.col("draft_round").is_not_null())
          .then(pl.lit("drafted"))
          .otherwise(pl.lit("undrafted"))
          .alias("sample_membership"),
    ])

    df = joined.to_pandas()
    print(f"done — final shape {df.shape[0]}x{df.shape[1]}")
    return df
```

Key rules enforced here:
- Returns `pd.DataFrame` (required by `load_or_fetch` type guard, `shared/cache.py` line 60-62)
- No `inplace=True` anywhere (CLAUDE.md: always assign)
- `w_av` not `car_av` (100% null per RESEARCH.md)
- `replace_strict(..., default="Other")` to surface unmapped positions rather than silently dropping

---

**Argparse / main pattern** (`nba-playoffs/scripts/retrain_series_xgboost.py` lines 115-181, adapted):
```python
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-refresh", action="store_true",
                        help="Bypass cache and re-fetch from nflreadpy.")
    args = parser.parse_args()

    df = load_or_fetch(CACHE_KEY, _build_dataset, force_refresh=args.force_refresh)
    print(f"Dataset ready: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Cached to .cache/{CACHE_KEY}.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Copy the `raise SystemExit(main())` idiom from `retrain_series_xgboost.py` line 181. Copy `return int` from `main()` signature. `--force-refresh` is the only argparse argument (CONTEXT.md D-09).

---

**Progress print pattern** (`nba-playoffs/src/data.py` lines 46-49 style; D-08 no tqdm):
```python
print("Fetching combine data...", end=" ", flush=True)
# ... do work ...
print(f"done ({len(combine)} rows)")
```

Use `end=" ", flush=True` on the "Fetching..." line so the count appears on the same line. No tqdm.

---

### `nfl/nfl_eda.ipynb` (notebook, batch / transform)

**Analog:** `nba-playoffs/notebooks/02-eda.ipynb` (same role — EDA notebook reading cached data). No direct code is extracted from the notebook file (notebooks are binary JSON; patterns are derived from project conventions and RESEARCH.md verified examples).

**Project notebook conventions** (from `nfl/README.md` + CLAUDE.md §Notebook conventions):
- Cell 1: config cell — all constants and imports here; notebook is runnable top-to-bottom without edits
- `sys.path.insert(0, str(Path.cwd().parent))` goes in the config cell (needed in notebooks; not in scripts)
- No `%matplotlib inline` magic — omit entirely
- Use `plt.show()` or return fig objects
- No hardcoded paths — use `CACHE_KEY` constant

---

**Config cell pattern** (RESEARCH.md Pattern 2; project convention):
```python
# Cell 1 — Config (edit here only)
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd().parent))  # project root on sys.path

from nfl.pipeline import _build_dataset, START_SEASON, END_SEASON, CACHE_KEY
from shared.cache import load_or_fetch

FORCE_REFRESH = False  # set True to re-fetch from nflreadpy
```

Importing `CACHE_KEY` from `pipeline.py` (rather than re-defining it) is the integration contract — ensures notebook and script always use the same key (CONTEXT.md code_context: "define it as a shared constant or document it explicitly").

---

**Data load cell pattern** (follows config cell immediately):
```python
# Cell 2 — Data load
df = load_or_fetch(CACHE_KEY, _build_dataset, force_refresh=FORCE_REFRESH)
print(f"Loaded {df.shape[0]} rows × {df.shape[1]} cols")
print(df.dtypes)
```

---

**Missingness heatmap pattern** (`seaborn 0.13.x` — RESEARCH.md Code Examples):
```python
import seaborn as sns
import matplotlib.pyplot as plt

drills = ["forty", "bench", "vertical", "broad_jump", "cone", "shuttle"]

null_matrix = (
    df.groupby("position_group")[drills]
    .apply(lambda g: g.isnull().mean())
    .T  # drills as rows, position_groups as columns
)

fig, ax = plt.subplots(figsize=(10, 4))
sns.heatmap(null_matrix, annot=True, fmt=".0%", cmap="Reds", ax=ax)
ax.set_title("Combine Drill Missing Data Rate by Position Group")
plt.tight_layout()
plt.show()
```

---

**Opt-out bias comparison pattern** (NFL-10; RESEARCH.md Code Examples):
```python
# Drafted players only; treat null w_av as 0 (no NFL career)
drafted = df[df["sample_membership"] == "drafted"].copy()
drafted["career_av"] = drafted["w_av"].fillna(0)

results = []
for drill in drills:
    for pos_grp in drafted["position_group"].unique():
        sub = drafted[drafted["position_group"] == pos_grp]
        row = {
            "drill": drill,
            "position_group": pos_grp,
            "n_completed": (~sub[drill].isnull()).sum(),
            "n_skipped": sub[drill].isnull().sum(),
            "mean_av_completed": sub.loc[~sub[drill].isnull(), "career_av"].mean(),
            "mean_av_skipped": sub.loc[sub[drill].isnull(), "career_av"].mean(),
        }
        results.append(row)

bias_df = pd.DataFrame(results)
```

Note: opt-out defined **per-drill** (null in drill column = opted out of that drill). Always condition on `position_group` — bench press MNAR by position (QB ~95% null, WR ~53% null) means cross-position opt-out analysis is misleading (RESEARCH.md Pitfall 5).

---

## Shared Patterns

### Cache Interface
**Source:** `shared/cache.py` lines 25-77
**Apply to:** `nfl/pipeline.py` (write), `nfl/nfl_eda.ipynb` (read)

All data access goes through `load_or_fetch`. Never call `df.to_parquet()` directly in pipeline or notebook code. The cache key is the integration contract between the two files — import it from `pipeline.py` in the notebook rather than duplicating the string.

Key constraint from `shared/cache.py` line 50-51: cache keys must match `^[A-Za-z0-9_\-]+$`. The parameterized key `f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"` (e.g., `"nfl_combine_pipeline_2000_2023"`) satisfies this — no slashes.

### `from __future__ import annotations`
**Source:** `shared/cache.py` line 10; `nba-playoffs/scripts/retrain_series_xgboost.py` line 4
**Apply to:** `nfl/pipeline.py`
Present in all project Python files. Include as first import.

### No `inplace=True`
**Source:** CLAUDE.md §Code style; project CLAUDE.md §What NOT to Use
**Apply to:** `nfl/pipeline.py`, `nfl/nfl_eda.ipynb`
Always assign: `df = df.method()`. This includes pandas `.fillna()`, `.rename()`, `.drop()`, etc.

### Polars → pandas conversion
**Source:** `nfl/README.md`; RESEARCH.md Standard Stack
**Apply to:** `nfl/pipeline.py` (`_build_dataset` function)
nflreadpy returns Polars DataFrames. All Polars operations (join, `with_columns`, `select`) happen before `.to_pandas()`. The returned `pd.DataFrame` is what `load_or_fetch` persists to parquet.

---

## No Analog Found

None — both files have sufficiently close analogs in the codebase.

---

## Anti-Patterns (do not copy from analogs)

| Pattern in Analog | Why to Avoid | Use Instead |
|-------------------|-------------|-------------|
| `nba-playoffs/src/data.py` manual `df.to_parquet(cache, index=False)` | Bypasses `load_or_fetch`; no atomic write, no key validation | `shared.cache.load_or_fetch` |
| `nba-playoffs/scripts/*.py` lines `sys.path.insert(0, ...)` | Scripts run from project root — sys.path manipulation not needed | Import directly; `sys.path.insert` only in notebooks |
| `nba-playoffs/src/data.py` per-function `force` flag on individual fetch functions | NFL pipeline uses a single joined artifact; `--force-refresh` on the CLI is the only invalidation path | Single `load_or_fetch` call in `main()` |
| `car_av` column | 100% null in nflreadpy 0.1.5 | `w_av` (Weighted Approximate Value) |

---

## Metadata

**Analog search scope:** `/Users/mearly/dev/playground/Sports/nba-playoffs/scripts/`, `/Users/mearly/dev/playground/Sports/nba-playoffs/src/`, `/Users/mearly/dev/playground/Sports/shared/`, `/Users/mearly/dev/playground/Sports/tests/`
**Files scanned:** 7 (`shared/cache.py`, `tests/test_cache.py`, `nba-playoffs/scripts/predict_playoffs.py`, `nba-playoffs/scripts/retrain_series_xgboost.py`, `nba-playoffs/src/data.py`, `nba-playoffs/src/models.py` header only, `nfl/README.md`)
**Pattern extraction date:** 2026-05-23
