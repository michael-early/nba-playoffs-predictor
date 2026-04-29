# Architecture Research

**Domain:** Multi-sport ML research repository (NFL, NBA, MLB)
**Researched:** 2026-04-29
**Confidence:** HIGH — patterns are well-established for Python research repos of this shape

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Sport Workspaces                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     NFL/     │  │     NBA/     │  │     MLB/     │          │
│  │  notebooks/  │  │  notebooks/  │  │  notebooks/  │          │
│  │  scripts/    │  │  scripts/    │  │  scripts/    │          │
│  │  data/       │  │  data/       │  │  data/       │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
├─────────┴─────────────────┴─────────────────┴───────────────────┤
│                      Shared Utilities                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │  data.py   │  │  models.py │  │  viz.py    │                 │
│  │ (loaders,  │  │ (sklearn   │  │ (plot      │                 │
│  │  caching)  │  │  helpers)  │  │  helpers)  │                 │
│  └────────────┘  └────────────┘  └────────────┘                 │
├─────────────────────────────────────────────────────────────────┤
│                      Data Cache Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  data/raw/   (immutable fetched files, gitignored)       │   │
│  │  data/processed/  (parquet outputs, gitignored)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `NFL/notebooks/` | EDA, exploration, hypothesis development | Jupyter notebooks, run top-to-bottom |
| `NFL/scripts/` | Repeatable model runs, data prep pipelines | Plain `.py` files, invoked via CLI |
| `NFL/data/` | Sport-local raw/processed cache | CSV or Parquet, gitignored |
| `shared/` | Cross-sport helpers that don't belong to any sport | Python package (`__init__.py`) |
| `data/` (root) | Shared cache for truly cross-sport reference data | Optional; keep per-sport if data shapes differ |

## Recommended Project Structure

```
Sports/
├── NFL/
│   ├── notebooks/
│   │   ├── 01_eda_combine.ipynb       # exploration: combine measurables
│   │   ├── 02_feature_engineering.ipynb
│   │   └── 03_model_evaluation.ipynb
│   ├── scripts/
│   │   ├── fetch_data.py              # pull raw data from nflverse/nfl_data_py
│   │   ├── build_features.py          # transform raw → feature matrix
│   │   └── train_model.py             # fit, evaluate, persist results
│   ├── data/
│   │   ├── raw/                       # fetched files, never modified (gitignored)
│   │   └── processed/                 # feature matrices, model inputs (gitignored)
│   ├── outputs/
│   │   └── figures/                   # saved plots (gitignored or committed selectively)
│   └── README.md                      # what analyses exist, how to run
├── NBA/
│   ├── notebooks/
│   ├── scripts/
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   └── README.md
├── MLB/
│   ├── notebooks/
│   ├── scripts/
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   └── README.md
├── shared/
│   ├── __init__.py
│   ├── cache.py                       # disk-based fetch caching
│   ├── models.py                      # sklearn pipeline wrappers, CV helpers
│   ├── metrics.py                     # shared evaluation metrics
│   └── viz.py                         # matplotlib/plotly plot helpers
├── .venv/                             # single shared venv (per PROJECT.md intent)
├── requirements.txt                   # or pyproject.toml
├── .gitignore                         # data/, outputs/figures/, .venv/
└── README.md
```

### Structure Rationale

- **Per-sport `data/raw/` and `data/processed/`:** Keeps data close to the analysis that uses it. NFL combine data has no business in the NBA folder. Avoids accidental cross-contamination.
- **Per-sport `notebooks/` numbered prefix:** Enforces run order and makes the research narrative legible without opening files.
- **Per-sport `scripts/`:** Separates one-time exploration (notebooks) from repeatable operations (scripts). Scripts are safe to re-run; notebooks are not assumed idempotent.
- **`shared/` as a package:** Imported as `from shared.cache import load_or_fetch`. Avoids copy-paste of caching logic across three sport folders. Only put things here that genuinely recur across sports (disk caching, CV wrappers) — not sport-specific transforms.
- **`outputs/figures/`:** Decouples saved artifacts from source code. Gitignore by default; commit selectively when figures matter for the record.

## Architectural Patterns

### Pattern 1: Load-or-Cache

**What:** Every data fetch function checks for a local file before hitting the remote API. If cached, load from disk; if not, fetch and write to disk.
**When to use:** All data loading in `scripts/fetch_data.py` and notebook config cells. Free APIs (nflverse, nba_api, pybaseball) are slow and rate-limited.
**Trade-offs:** Simple and effective for batch/historical research. Not appropriate for real-time data (out of scope here).

**Example:**
```python
# shared/cache.py
from pathlib import Path
import pandas as pd

def load_or_fetch(cache_path: Path, fetch_fn, **kwargs) -> pd.DataFrame:
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    df = fetch_fn(**kwargs)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False)
    return df
```

### Pattern 2: Config Cell First (Notebooks)

**What:** Every notebook opens with a single config cell that defines all paths, parameters, and flags. No hardcoded paths or magic numbers elsewhere in the notebook.
**When to use:** Every notebook without exception.
**Trade-offs:** Slightly verbose at the top of notebooks. Pays for itself immediately when someone clones the repo and needs to change `DATA_DIR`.

**Example:**
```python
# Cell 1 — CONFIG (modify before running)
from pathlib import Path

SPORT_DIR = Path("../")           # relative to notebooks/
DATA_DIR  = SPORT_DIR / "data"
RAW_DIR   = DATA_DIR / "raw"
PROC_DIR  = DATA_DIR / "processed"
SEASON    = 2023
POSITION  = "WR"                  # filter scope
```

### Pattern 3: Script as Reproducible Pipeline Stage

**What:** Each script in `scripts/` corresponds to one pipeline stage (fetch → build_features → train). Scripts are idempotent — re-running produces the same output. They accept no mandatory interactive input; all configuration via constants at the top or argparse.
**When to use:** Any analysis you want to reproduce without re-running a notebook manually.
**Trade-offs:** More upfront effort than notebooks. Worth it once EDA is done and you want a stable, shareable result.

**Example:**
```python
# scripts/build_features.py
RAW_PATH  = Path("data/raw/combine_2000_2023.parquet")
OUT_PATH  = Path("data/processed/combine_features.parquet")

def main():
    df = pd.read_parquet(RAW_PATH)
    # ... transforms ...
    df.to_parquet(OUT_PATH, index=False)

if __name__ == "__main__":
    main()
```

## Data Flow

### Research Flow (Notebook Path)

```
External API (nflverse / nba_api / pybaseball)
    ↓ fetch (first run only)
data/raw/           ← immutable, gitignored
    ↓ load
Notebook config cell
    ↓ transform
In-memory DataFrame (pandas)
    ↓ explore / visualize
outputs/figures/    ← saved plots
```

### Reproducible Run Flow (Script Path)

```
scripts/fetch_data.py     → data/raw/
scripts/build_features.py → data/processed/
scripts/train_model.py    → outputs/results/
```

Each stage reads from the previous stage's output. Stages can be re-run independently as long as their inputs exist.

### Key Data Flows

1. **Raw ingest:** API call → Parquet on disk. Happens once per dataset refresh. Raw files are never modified by downstream scripts.
2. **Feature build:** Raw Parquet → cleaned/engineered feature matrix → Parquet. Deterministic; safe to re-run.
3. **Model train:** Feature Parquet → fitted model artifacts + evaluation metrics → saved to `outputs/`. Model artifacts optionally gitignored (large); metrics CSV usually committed.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-3 sports, 1 analyst | Current structure — single `.venv`, scripts per sport |
| 3+ sports, multiple analysts | Add `Makefile` or `dvc` for pipeline orchestration; consider DVC for data versioning |
| Large datasets (>1 GB) | Move from CSV to Parquet everywhere (already recommended); consider chunked processing in scripts |

### Scaling Priorities

1. **First bottleneck:** Duplicate data loading code across sports. Fix by expanding `shared/cache.py` before the pattern spreads.
2. **Second bottleneck:** Notebook state drift (re-running cells out of order). Fix by promoting stable analyses to scripts early.

## Anti-Patterns

### Anti-Pattern 1: Monolithic Cross-Sport Module

**What people do:** Create a single `sports_utils.py` that imports nflverse, nba_api, and pybaseball, with one giant `load_data(sport=...)` dispatcher.
**Why it's wrong:** Each sport's data shape is fundamentally different (play-by-play vs box score vs pitch-by-pitch). Forcing a unified interface produces leaky abstractions and makes sport-specific transforms awkward. PROJECT.md explicitly calls this out as out of scope.
**Do this instead:** Keep sport-specific loaders in each sport's `scripts/fetch_data.py`. Only put genuinely generic utilities (disk caching, sklearn wrappers, plot helpers) in `shared/`.

### Anti-Pattern 2: Data Files Committed to Git

**What people do:** Commit raw CSVs or Parquets to the repo for convenience.
**Why it's wrong:** Sports datasets grow quickly (nflverse play-by-play is hundreds of MB per season). Git history bloats permanently; cloning becomes painful.
**Do this instead:** Gitignore all `data/` directories. Include a `scripts/fetch_data.py` per sport that any analyst can run to reproduce the local cache. Document the fetch command in each sport's `README.md`.

### Anti-Pattern 3: Notebooks as the Reproducibility Artifact

**What people do:** Treat notebooks as the "final" analysis — run them manually, screenshot results, call it done.
**Why it's wrong:** Notebooks accumulate hidden state. Cell execution order matters. A notebook that "works" on one machine may silently fail on another due to cell-order dependencies or environment drift.
**Do this instead:** Notebooks are for exploration only. Once an analysis is validated, extract the stable logic into `scripts/`. The scripts are the reproducibility artifact.

### Anti-Pattern 4: Hardcoded Paths in Notebooks

**What people do:** `df = pd.read_csv("/Users/mearly/dev/playground/Sports/NFL/data/raw/combine.csv")`
**Why it's wrong:** Breaks on any other machine, any other user, any path change.
**Do this instead:** Config cell at the top of every notebook with `Path`-based relative paths. All subsequent cells derive paths from config variables.

## Integration Points

### External Data Sources

| Source | Integration Pattern | Notes |
|--------|---------------------|-------|
| nflverse / nfl_data_py | Python package, returns DataFrames | Caches well; wrap with `load_or_fetch`. Season-level granularity. |
| nba_api | REST calls via Python wrapper | Rate-limited; cache aggressively. Per-game or per-player endpoints. |
| pybaseball | Python package, scrapes Baseball Reference / FanGraphs | Slow; always cache. Statcast data can be large. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `shared/` ↔ sport scripts | Direct import (`from shared.cache import load_or_fetch`) | `shared/` must never import from sport-specific modules — one-directional dependency only |
| notebooks ↔ scripts | Shared `data/` directory on disk | Notebooks and scripts for the same sport read from the same `data/raw/` and `data/processed/` paths |
| NFL ↔ NBA ↔ MLB | None at runtime | Sport folders are independent. Cross-sport comparisons, if ever needed, belong in a separate top-level notebook, not in a sport folder. |

## Suggested Build Order

Build order flows from dependencies. Each layer must exist before the layer above it can be useful.

| Order | What to Build | Why First |
|-------|---------------|-----------|
| 1 | Repo scaffold + `.gitignore` | Everything else lands inside this structure |
| 2 | `shared/cache.py` (load-or-fetch) | All data fetching depends on it; implement once, not three times |
| 3 | `NFL/scripts/fetch_data.py` + `NFL/data/raw/` | Raw data must exist before any notebook or model script can run |
| 4 | `NFL/notebooks/01_eda_combine.ipynb` | First concrete analysis per PROJECT.md; validates data shape and research questions |
| 5 | `NFL/scripts/build_features.py` | Graduates EDA findings to a reproducible feature matrix |
| 6 | `NFL/scripts/train_model.py` | Completes the NFL pipeline |
| 7 | `NBA/` scaffold (fetch_data stub, empty notebooks/) | Placeholder per PROJECT.md; no active analysis yet |
| 8 | `MLB/` scaffold | Same as NBA |

NBA and MLB scaffolds (steps 7–8) need only a `README.md`, empty `notebooks/` and `scripts/` directories, and a `data/raw/.gitkeep`. No real analysis until NFL pipeline is validated.

## Sources

- Architecture patterns: training knowledge from public sports ML repos (nfl-big-data-bowl entrants, Kaggle sports notebooks), cross-referenced against PROJECT.md constraints
- Notebook conventions: consistent with CLAUDE.md project conventions (`config cells first`, `top-to-bottom`, `no hardcoded paths`)
- Data source notes: nfl_data_py/nflverse, nba_api, pybaseball public documentation (HIGH confidence for existence; MEDIUM confidence for specific API details — verify per-sport during implementation)
- Confidence overall: HIGH for structural patterns (well-established Python research repo conventions); MEDIUM for sport-specific library details (verify during per-sport phases)

---
*Architecture research for: Multi-sport ML research repository (NFL, NBA, MLB)*
*Researched: 2026-04-29*
