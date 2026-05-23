# Phase 2: NFL Data Pipeline - Research

**Researched:** 2026-05-23
**Domain:** nflreadpy data ingestion, Polars/pandas interchange, parquet caching, EDA notebook design
**Confidence:** HIGH (all critical API facts live-verified against installed nflreadpy 0.1.5)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 (Career Outcome - Primary):** AV (Approximate Value, from Pro Football Reference via nflreadr) is the primary career outcome — continuous, cross-position, used for OLS regressions in Phase 3.

**D-02 (Career Outcome - Secondary):** Pro Bowl / All-Pro appearances as secondary binary outcome — surfaced in EDA descriptive stats, not used for primary regressions. Fetch alongside AV.

**D-03 (Career Window):** Full career to date (all available seasons summed). Recent draftees (2021–2023) will have lower AV by nature — document explicitly as a sample limitation in the pipeline README cell and the EDA notebook.

**D-04 (Position Groups):** Standard NFL position groups — QB, RB, WR/TE, OL, DL, LB, DB. Applied consistently in pipeline output column and in all EDA position breakdowns.

**D-05 (Season Range):** Combine data window: 2000–2023. Pre-2000 data is noisy. 2024 excluded — <2 seasons of career data for that class.

**D-06 (Constants):** Season range configured as constants at the top of the pipeline script: `START_SEASON = 2000` / `END_SEASON = 2023`.

**D-07 (Pipeline Output):** Single joined parquet via `shared.cache.load_or_fetch`. Cache key: `"nfl_combine_pipeline_2000_2023"` (or parameterized from constants). EDA notebook loads from the same cache key — no separate `nfl/data/` folder.

**D-08 (Stdout):** Minimal progress prints at key steps. No tqdm.

**D-09 (CLI Flag):** `--force-refresh` argparse flag — passes `force_refresh=True` to `load_or_fetch`. Only argparse argument.

**D-10 (EDA Notebook):** One notebook `nfl/nfl_eda.ipynb` covering NFL-02 and NFL-10. Structure: config cell → data load (from cache) → distributions → missingness audit → opt-out rates by position → opt-out bias comparison → summary.

**D-11 (Opt-out Bias):** Descriptive comparison: mean/median AV and Pro Bowl rate by drill-skipped status, grouped by position. No formal statistical tests in Phase 2.

### Claude's Discretion

- Exact cache key format for parameterized season range (e.g., `"nfl_combine_pipeline_2000_2023"` or `f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"`).
- Column naming for AV vs Pro Bowl columns in the joined output.
- Whether opt-out is defined per-drill or as "skipped any drill."

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NFL-01 | User can run the data pipeline and get a clean joined dataframe of combine measurables + career stats, cached to parquet, with sample definition documented (drafted / undrafted / not invited) | `nfl.load_combine()` + `nfl.load_draft_picks()` verified; join key is `pfr_id` → `pfr_player_id`; draft_round null signals undrafted; not-invited players are absent from the combine table entirely |
| NFL-02 | User can open the EDA notebook, run top-to-bottom, and see distributions, opt-out rates, missingness audit, and position breakdowns | All drill columns verified with real null rates; position mapping from 22 raw values to 7 groups specified below |
| NFL-10 | User can see an opt-out bias analysis comparing career outcomes of combine drill skippers vs. participants | Drill-null = opt-out (or not-tested); `w_av`, `allpro`, `probowls` are the outcome columns available after join |

</phase_requirements>

---

## Summary

Phase 2 delivers a joined parquet of NFL Combine measurables and career outcomes, plus an EDA notebook. All data comes from nflreadpy 0.1.5 (installed), which returns Polars DataFrames. Two nflreadpy functions cover the entire data need: `nfl.load_combine()` for combine measurables (18 columns, 7,999 rows for 2000–2023) and `nfl.load_draft_picks()` for career stats (36 columns, 6,130 rows for the same range). The join key is `pfr_id` (combine) → `pfr_player_id` (draft picks); 93.2% of drafted combine participants match successfully.

The most critical verified finding that overrides the CONTEXT.md assumption: `car_av` (Career Approximate Value) is **100% null** in the nflreadpy dataset. The usable AV column is `w_av` (Weighted Approximate Value from PFR). This must be acknowledged and `w_av` used as the primary career outcome. Weighted AV is the standard PFR measure for cross-era career value and is appropriate for regression in Phase 3. The CONTEXT.md decision D-01 stands; only the column name changes.

The nflreadpy internal cache uses in-memory memoization (per-process, `CacheMode.MEMORY`), not filesystem persistence. This means there is no conflict with `shared/cache.py` — the two cache layers are orthogonal. The pipeline should call nflreadpy inside the `fetch_fn` lambda passed to `load_or_fetch`; the outer disk cache is the persistence layer.

**Primary recommendation:** Use `nfl.load_combine(list(range(START_SEASON, END_SEASON + 1)))` and `nfl.load_draft_picks(list(range(START_SEASON, END_SEASON + 1)))`, join in-memory on `pfr_id`/`pfr_player_id`, call `.to_pandas()` on the result, and cache the joined pandas DataFrame under a single key.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Combine data fetch | Pipeline script (`nfl/pipeline.py`) | shared/cache.py (disk) | Network call wrapped in load_or_fetch; script owns the fetch logic |
| Career stats fetch | Pipeline script (`nfl/pipeline.py`) | shared/cache.py (disk) | Same pattern — one or two raw fetches inside the joined fetch_fn |
| In-memory join | Pipeline script (`nfl/pipeline.py`) | — | Polars join before .to_pandas(); happens inside the fetch_fn |
| Disk caching | `shared/cache.py` | — | Existing utility; all fetches must go through it |
| Position group mapping | Pipeline script (`nfl/pipeline.py`) | — | Applied before writing the cache artifact so EDA can group without re-mapping |
| EDA/visualizations | `nfl/nfl_eda.ipynb` | — | Reads the cache key; no data fetch logic in the notebook |
| Opt-out bias analysis | `nfl/nfl_eda.ipynb` | — | Descriptive stats only in Phase 2; notebook cell within the EDA notebook |
| Sample membership doc | `nfl/nfl_eda.ipynb` + `nfl/pipeline.py` | — | Pipeline prints summary; EDA notebook includes the markdown cell |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nflreadpy | 0.1.5 [VERIFIED: pip freeze] | NFL data — combine + draft picks | Only maintained Python port of nflverse; returns Polars DataFrames |
| polars | 1.41.0 [VERIFIED: pip freeze] | In-memory join and Polars → pandas conversion | nflreadpy returns Polars; join in Polars before .to_pandas() |
| pandas | 2.2.3 [VERIFIED: pip freeze] | Final output format; required by load_or_fetch | shared/cache.py accepts and writes pd.DataFrame |
| pyarrow | 18.1.0 [VERIFIED: pip freeze] | Parquet engine for shared/cache.py | Required by pd.to_parquet() / pd.read_parquet() |
| seaborn | 0.13.2 [VERIFIED: pip freeze] | EDA plots — distributions, heatmaps | Project stack; seaborn 0.13 objects API for faceted plots |
| matplotlib | 3.9.4 [VERIFIED: pip freeze] | Base plotting backend for seaborn | Required by seaborn |

### No Additional Installs Needed

All libraries are already pinned in `requirements.txt` and present in `.venv`. The pipeline and EDA notebook require no new dependencies.

---

## Architecture Patterns

### System Architecture Diagram

```
nfl/pipeline.py
  ├── argparse: --force-refresh
  ├── START_SEASON = 2000 / END_SEASON = 2023 (module constants)
  └── shared.cache.load_or_fetch(
          key = f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}",
          fetch_fn = _build_dataset,
          force_refresh = args.force_refresh
      )
          │
          ▼ (cache miss or --force-refresh)
      _build_dataset()
          ├── nfl.load_combine(seasons)   → Polars DataFrame (7,999 rows × 18 cols)
          ├── nfl.load_draft_picks(seasons) → Polars DataFrame (6,130 rows × 36 cols)
          ├── Polars left join on pfr_id → pfr_player_id (result: 7,999 rows × 25 cols)
          ├── add position_group column (map 22 raw pos values → 7 groups)
          ├── add sample_membership column ("drafted" / "undrafted")
          └── .to_pandas() → pd.DataFrame → returned to load_or_fetch → cached to .cache/

.cache/nfl_combine_pipeline_2000_2023.parquet
          │
          ▼ (both pipeline and notebook read from here)
nfl/nfl_eda.ipynb
  ├── Config cell: CACHE_KEY = "nfl_combine_pipeline_2000_2023"
  ├── Data load: df = shared.cache.load_or_fetch(CACHE_KEY, fetch_fn=pipeline._build_dataset)
  ├── Distributions: per-drill histograms, by position_group
  ├── Missingness audit: null % heatmap (drill × position_group)
  ├── Opt-out rates: per-drill, per-position (null = opted out / not tested)
  ├── Opt-out bias: mean/median w_av, probowl_flag by drill × opted_out status
  └── Summary: sample counts, limitations markdown cell
```

### Recommended Project Structure
```
nfl/
├── __init__.py           # empty (exists)
├── README.md             # exists; no changes needed
├── pipeline.py           # NEW: data fetch + join + cache write
└── nfl_eda.ipynb         # NEW: EDA notebook

shared/
└── cache.py              # EXISTS: load_or_fetch utility (read-only)

.cache/                   # auto-created by load_or_fetch
└── nfl_combine_pipeline_2000_2023.parquet   # output artifact
```

### Pattern 1: Two Fetches, One Cache Key

**What:** Fetch combine and draft_picks separately inside a single `fetch_fn`, join in-memory, return one DataFrame. Cache only the joined output.

**When to use:** Always — the raw sources are small (<1 MB each), the join is trivial, and downstream consumers (notebook, Phase 3) only need the joined artifact. Separate raw caches would add complexity with no benefit.

**Example:**
```python
# Source: verified against nflreadpy 0.1.5 docs + live execution
import nflreadpy as nfl
import polars as pl
import pandas as pd
from shared.cache import load_or_fetch

START_SEASON = 2000
END_SEASON = 2023

SEASONS = list(range(START_SEASON, END_SEASON + 1))

POSITION_GROUP_MAP = {
    "QB": "QB",
    "RB": "RB", "FB": "RB",
    "WR": "WR/TE", "TE": "WR/TE",
    "OT": "OL", "OG": "OL", "C": "OL", "OL": "OL",
    "DE": "DL", "DT": "DL", "DL": "DL", "EDGE": "DL",
    "OLB": "LB", "ILB": "LB", "LB": "LB",
    "CB": "DB", "S": "DB", "DB": "DB",
}

def _build_dataset() -> pd.DataFrame:
    print("Fetching combine data...", end=" ", flush=True)
    combine = nfl.load_combine(SEASONS)
    print(f"done ({len(combine)} rows)")

    print("Fetching draft picks (career stats)...", end=" ", flush=True)
    picks = nfl.load_draft_picks(SEASONS)
    picks_slim = picks.select([
        "pfr_player_id", "w_av", "allpro", "probowls",
        "dr_av", "hof", "round", "pick",
    ])
    print(f"done ({len(picks_slim)} rows)")

    print("Joining...", end=" ", flush=True)
    joined = combine.join(
        picks_slim,
        left_on="pfr_id",
        right_on="pfr_player_id",
        how="left",
    )

    # Add derived columns
    joined = joined.with_columns([
        pl.col("pos").replace_strict(POSITION_GROUP_MAP, default="Other")
          .alias("position_group"),
        pl.when(pl.col("draft_round").is_not_null())
          .then(pl.lit("drafted"))
          .otherwise(pl.lit("undrafted"))
          .alias("sample_membership"),
    ])

    df = joined.to_pandas()
    print(f"final shape {df.shape[0]}×{df.shape[1]}")
    return df
```

### Pattern 2: EDA Notebook Config Cell Pattern

**What:** All configurable values in the first cell; notebook is runnable top-to-bottom without edits.

**Example:**
```python
# Cell 1: Config
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd().parent))  # project root on path

from nfl.pipeline import _build_dataset, START_SEASON, END_SEASON
from shared.cache import load_or_fetch

CACHE_KEY = f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"
FORCE_REFRESH = False  # set True to re-fetch

# Cell 2: Data load
df = load_or_fetch(CACHE_KEY, _build_dataset, force_refresh=FORCE_REFRESH)
print(f"Loaded {df.shape[0]} rows × {df.shape[1]} cols")
```

### Anti-Patterns to Avoid

- **Using `car_av` as the AV column:** It is 100% null in the current nflreadpy dataset. Use `w_av` (Weighted Approximate Value).
- **Calling `nfl.load_combine()` with `seasons=True` (all seasons):** Returns data back to the 1970s with poor drill coverage. Always pass the explicit season list.
- **Putting `sys.path` manipulation in the pipeline script:** Only needed in notebooks. Scripts are run from the project root with `python nfl/pipeline.py`.
- **Using pandas `.inplace=True`:** Per project CLAUDE.md, always assign: `df = df.method()`.
- **Defining opt-out as "skipped at least one drill":** This collapses meaningful per-drill variation. Opt-out should be defined per-drill (null = skipped). The EDA can show both per-drill and "any drill" summaries.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Disk-backed parquet cache | Custom parquet write logic | `shared.cache.load_or_fetch` | Already built and tested in Phase 1; atomic write via tempfile |
| Cross-platform player ID mapping | Name matching / fuzzy join | `pfr_id` → `pfr_player_id` exact join | 93.2% match rate on drafted players; name matching would introduce false matches |
| Polars → pandas conversion | Custom dtype reconciliation | `.to_pandas()` | Polars 1.41 handles all numeric types cleanly; pyarrow handles the conversion |

---

## Verified API Reference

### nfl.load_combine(seasons)

**Source:** [VERIFIED: live execution against nflreadpy 0.1.5]

- Signature: `nfl.load_combine(seasons=True)` — pass `list[int]` for season filtering
- Returns: Polars DataFrame
- Columns (18): `season`, `draft_year`, `draft_team`, `draft_round`, `draft_ovr`, `pfr_id`, `cfb_id`, `player_name`, `pos`, `school`, `ht`, `wt`, `forty`, `bench`, `vertical`, `broad_jump`, `cone`, `shuttle`
- Player ID column: `pfr_id` (str) — 17.4% null overall; non-null for ~97% of drafted players
- Position column: `pos` (22 unique values; see position mapping table below)
- Draft info: `draft_round` (null = undrafted combine invitee), `draft_ovr` (overall pick)
- Shape for 2000–2023: **7,999 rows × 18 cols** (~1.1 MB Polars, ~4.5 MB pandas)

### nfl.load_draft_picks(seasons)

**Source:** [VERIFIED: live execution against nflreadpy 0.1.5]

- Signature: `nfl.load_draft_picks(seasons=True)` — pass `list[int]` for season filtering
- Returns: Polars DataFrame
- Key columns: `pfr_player_id` (join key), `pfr_player_name`, `season`, `round`, `pick`, `w_av`, `dr_av`, `allpro`, `probowls`, `hof`, `position`, `category`
- **`car_av` is 100% null — do not use.** Use `w_av` (Weighted Approximate Value).
- `w_av`: 8.8% null (2000–2023 range); near-zero null for 2021–2023 cohort
- `allpro`, `probowls`: 0% null (integer count, 0 = none)
- Shape for 2000–2023: **6,130 rows × 36 cols** (~1.0 MB Polars)

### Join Key

**Source:** [VERIFIED: live execution]

- `combine.pfr_id` LEFT JOIN `picks.pfr_player_id`
- Join success rate: **93.2%** of drafted combine invitees (2000–2023)
- Failure modes: `pfr_id` null in combine (17.4%), or ID mismatch (~7% of drafted players with non-null IDs)
- Use a LEFT join — preserve all combine rows; undrafted players get null AV

---

## Sample Membership Logic

**Source:** [VERIFIED: live execution]

The combine dataset only contains players who were *invited to the combine*. There is no nflreadpy table that lists "not-invited" prospects — those players simply do not appear.

| `sample_membership` Value | Derivation | Row Count (2000–2023) |
|--------------------------|------------|----------------------|
| `"drafted"` | `draft_round` is not null | 5,128 (64.1%) |
| `"undrafted"` | `draft_round` is null, but player is in combine data | 2,871 (35.9%) |
| `"not_invited"` | Not representable from combine data alone | N/A — document as limitation |

**Documentation requirement (NFL-01):** The pipeline output README cell and the EDA notebook must explicitly state: "This dataset covers only players invited to the NFL Combine. Players who were neither drafted nor invited to the combine are not represented. 'Not-invited' prospects cannot be reconstructed from this data source."

---

## Position Group Mapping

**Source:** [VERIFIED: live execution — all 22 raw `pos` values enumerated]

| Raw `pos` Values | Target Group | Count (2000–2023) |
|-----------------|-------------|-------------------|
| QB | QB | 432 |
| RB, FB | RB | 699 + 121 = 820 |
| WR, TE | WR/TE | 1,113 + 448 = 1,561 |
| OT, OG, C, OL | OL | 548 + 420 + 194 + 141 = 1,303 |
| DE, DT, DL, EDGE | DL | 528 + 517 + 120 + 100 = 1,265 |
| OLB, ILB, LB | LB | 430 + 276 + 179 = 885 |
| CB, S, DB | DB | 798 + 563 + 83 = 1,444 |
| K, P, LS | Other / exclude | 110 + 147 + 32 = 289 |

**Note:** K, P, LS are specialists. Include them in the dataset but exclude from position-grouped regressions in Phase 3. The pipeline should assign them `"Other"` in `position_group`; the EDA notebook should show their distributions separately or footnote their exclusion.

---

## Missingness Audit (Pre-Verified)

**Source:** [VERIFIED: live execution on 2000–2023 combine data, 7,999 rows]

| Drill | Null Count | Null % | Key Pattern |
|-------|-----------|--------|-------------|
| `forty` | 570 | 7.1% | Low missingness; most positions complete it |
| `bench` | 2,802 | 35.0% | WR: 52.6% null; QB: 95.4% null — positions rarely bench press |
| `vertical` | 1,837 | 23.0% | Moderate; consistent across positions |
| `broad_jump` | 1,913 | 23.9% | Similar to vertical |
| `cone` | 3,126 | 39.1% | High; agility drills skipped more often |
| `shuttle` | 3,006 | 37.6% | High; correlated with cone missingness |

**Position-specific extremes (bench press):**
- QB: ~95.4% null — almost no QBs bench press at the combine
- WR: ~52.6% null — nearly half opt out
- OLB, OT, OG, DT, DE: 21–27% null

**Implication for opt-out analysis:** Bench press opt-out is dominated by position, not individual player choice. The EDA should show opt-out rate by position AND note that bench press missing data is structurally MNAR (Missing Not At Random) — it reflects combine norms for the position, not pure selection.

---

## nflreadpy Cache Behavior

**Source:** [VERIFIED: live execution — `nfl.config.get_config()` output]

Default configuration:
```
cache_mode = CacheMode.MEMORY  (not filesystem)
cache_dir  = ~/Library/Caches/nflreadpy
cache_duration = 86400 (24h, applies to memory cache only)
```

The memory cache is **per-process memoization** — it prevents repeated network calls within a single Python session but does not persist between script invocations. This means:

1. **No conflict with `shared/cache.py`**: They serve different purposes. nflreadpy in-memory cache prevents double-fetching within one pipeline run; `shared/cache.py` persists across runs.
2. **Pattern:** Call `nfl.load_combine()` and `nfl.load_draft_picks()` inside `_build_dataset()`. `load_or_fetch` only calls `_build_dataset` on a cache miss. On subsequent runs, `shared/cache.py` returns the parquet without ever calling nflreadpy.
3. **No need to disable nflreadpy cache.** It is benign.

---

## Common Pitfalls

### Pitfall 1: Using `car_av` as the AV Column

**What goes wrong:** `car_av` exists in the schema but is 100% null in the current nflreadpy dataset. Any analysis using `car_av` produces all-null results silently.

**Why it happens:** The column exists in PFR's schema but nflreadpy's current data export does not populate it. `w_av` (Weighted AV) is populated and is the standard PFR career value metric.

**How to avoid:** Use `w_av` throughout. Rename to `career_av` in the output schema for clarity.

**Warning signs:** `df['car_av'].isnull().all()` returns True.

### Pitfall 2: Draft Picks Cover Only Drafted Players — Undrafted Get Null AV

**What goes wrong:** Left-joining combine to draft_picks means undrafted players (2,871 rows, 35.9%) get `w_av = null`. This is correct behavior, but code that drops nulls before analysis will silently exclude the entire undrafted cohort.

**Why it happens:** `load_draft_picks()` only covers drafted players, by definition.

**How to avoid:** Set `w_av = 0` for undrafted players, or keep nulls and document them. For opt-out bias analysis (NFL-10), treat null AV as "no NFL career" = AV 0 is the correct interpretation. For Phase 3 regression, exclude or impute explicitly.

**Warning signs:** Analysis sample drops from ~8,000 to ~5,000 after dropna on `w_av`.

### Pitfall 3: Position Group Mapping Misses New Position Labels

**What goes wrong:** nflreadpy has added position labels like `EDGE` and `DL` as generics in recent years. Code that hard-codes only the classic positions (DE, DT) will leave some rows as unmapped.

**Why it happens:** PFR's position classification has evolved; nflreadpy mirrors it.

**How to avoid:** Use the full POSITION_GROUP_MAP provided above, including `EDGE` → DL and `DL` → DL. Use `replace_strict(..., default="Other")` to surface any new unmapped values rather than silently dropping them.

**Warning signs:** Unexpected "Other" values appearing in position_group counts.

### Pitfall 4: Cache Key Invalidation After Parameter Change

**What goes wrong:** Developer changes `START_SEASON` / `END_SEASON` but the old parquet is still on disk under the same key. `load_or_fetch` returns the stale data.

**Why it happens:** `load_or_fetch` uses the key as the only cache-bust signal.

**How to avoid:** Parameterize the cache key from the constants: `f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"`. Changing the constants changes the key and forces a re-fetch. The `--force-refresh` flag is the escape hatch for all other invalidation scenarios.

**Warning signs:** Shape mismatch between what the pipeline prints and what the notebook loads.

### Pitfall 5: Bench Press as an Opt-Out Signal Is Structurally MNAR

**What goes wrong:** Treating bench press nulls as "player opted out" is misleading for QBs and WRs — the norm for those positions is not to test bench press. Including bench press in an opt-out bias analysis without this caveat produces misleading conclusions.

**Why it happens:** Combine testing norms differ by position — QBs routinely skip bench press.

**How to avoid:** In the opt-out bias analysis (NFL-10), always condition on position group. Compute opt-out rates per drill × position_group, not per drill across all positions. The EDA should surface this with a missingness heatmap.

---

## Code Examples

### Full Pipeline Script Skeleton

```python
# Source: derived from verified nflreadpy 0.1.5 API + shared/cache.py signature
"""nfl/pipeline.py — Build NFL Combine + Career Stats joined parquet."""
from __future__ import annotations

import argparse

import nflreadpy as nfl
import polars as pl

from shared.cache import load_or_fetch

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


def _build_dataset():
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


def main():
    parser = argparse.ArgumentParser(description="NFL Combine pipeline")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    df = load_or_fetch(CACHE_KEY, _build_dataset, force_refresh=args.force_refresh)
    print(f"Dataset ready: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Cached to .cache/{CACHE_KEY}.parquet")


if __name__ == "__main__":
    main()
```

### EDA Notebook Missingness Heatmap Pattern

```python
# Source: seaborn 0.13.x + pandas 2.2.x — standard pattern
import seaborn as sns
import matplotlib.pyplot as plt

drills = ["forty", "bench", "vertical", "broad_jump", "cone", "shuttle"]

# Missingness rate per drill × position group
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

### Opt-Out Bias Comparison Pattern

```python
# NFL-10: descriptive comparison — mean w_av by drill-skipped status
import pandas as pd

# For each drill, compute mean w_av for skippers vs completers (drafted only)
drafted = df[df["sample_membership"] == "drafted"].copy()
# Treat null w_av as 0 for undrafted players — no NFL career
drafted["career_av"] = drafted["w_av"].fillna(0)

results = []
for drill in drills:
    skipped = drafted[drill].isnull()
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

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nfl-data-py | nflreadpy | 2024–2025 | nfl-data-py is archived; nflreadpy is the maintained Python mirror of nflreadr |
| `car_av` for career value | `w_av` (Weighted AV) | Current nflreadpy 0.1.5 | `car_av` column exists in schema but is 100% null; `w_av` is the populated career metric |
| Pandas DataFrames from nflverse | Polars DataFrames | nflreadpy 0.1.x | All nflreadpy functions return Polars; `.to_pandas()` is the explicit conversion step |

---

## Open Questions

1. **`pfr_id` null for 17.4% of combine rows**
   - What we know: 1,392 of 7,999 combine rows have `pfr_id = null`
   - What's unclear: Are these predominantly undrafted players (low AV anyway) or a data quality issue for some drafted players?
   - Recommendation: In the pipeline, log a count of drafted players with null pfr_id. If >5% of drafted players lack a pfr_id, flag it in the EDA notebook as a data quality note. Based on live checks, most null pfr_ids appear to be in the undrafted cohort, so this is low risk for the regression analyses.

2. **Opt-out definition: per-drill vs any-drill**
   - What we know: CONTEXT.md leaves this to Claude's discretion
   - What's unclear: A player can skip cone but run the forty — "any drill" collapses this
   - Recommendation: Define opt-out per-drill in the joined output (null in a drill column = opted out of that drill). Add a derived `skipped_any_drill` boolean column for the aggregate view. This gives the EDA and Phase 3 maximum flexibility.

3. **Recent cohort (2021–2023) AV interpretation**
   - What we know: Mean w_av for 2021–2023 draftees is ~10 vs ~18 overall; this is expected (career truncated)
   - What's unclear: How to present this in the EDA without misleading readers
   - Recommendation: Add a scatter plot of mean AV by draft year in the EDA to visually show the right-truncation. Include a markdown cell explaining this is a sample limitation, not evidence that recent prospects are worse.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| nflreadpy | Pipeline data fetch | Yes | 0.1.5 | — |
| polars | Polars→pandas join | Yes | 1.41.0 | — |
| pandas | load_or_fetch return type | Yes | 2.2.3 | — |
| pyarrow | Parquet I/O | Yes | 18.1.0 | — |
| seaborn | EDA plots | Yes | 0.13.2 | — |
| matplotlib | Seaborn backend | Yes | 3.9.4 | — |
| .cache/ dir | Cache writes | No (auto-created) | — | load_or_fetch creates it |

**No missing dependencies.** All required libraries are installed in `.venv`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "Not-invited" prospects cannot be reconstructed from nflreadpy alone | Sample Membership | Low — nflreadpy only mirrors PFR combine data; if a player wasn't at the combine, they're not in the data |
| A2 | `w_av` is appropriate as a substitute for `car_av` in Phase 3 OLS regressions | Standard Stack / AV column | Low — Weighted AV is PFR's preferred summary metric; CONTEXT.md D-01 says "AV from PFR via nflreadr" which is exactly what w_av is |
| A3 | nflreadpy memory cache does not interfere with shared/cache.py | nflreadpy Cache Behavior | Low — verified by get_config(); memory mode means per-process only |

**Three assumed claims, all low risk.** No user confirmation needed before planning.

---

## Sources

### Primary (HIGH confidence)
- nflreadpy 0.1.5 installed in `.venv` — all API calls live-verified in this session
- `shared/cache.py` source read directly — signature and key validation confirmed
- `.planning/phases/02-nfl-data-pipeline/02-CONTEXT.md` — all locked decisions copied verbatim

### Secondary (MEDIUM confidence)
- [nflreadr draft picks data dictionary](https://nflreadr.nflverse.com/articles/dictionary_draft_picks.html) — column names for w_av, car_av, allpro, probowls verified
- [nflreadpy load functions reference](https://nflreadpy.nflverse.com/api/load_functions/) — complete function list confirmed
- [nflreadr load_combine reference](https://nflreadr.nflverse.com/reference/load_combine.html) — 18-column schema confirmed

### Tertiary (LOW confidence)
- None — all critical facts verified via live execution or official docs

---

## Metadata

**Confidence breakdown:**
- nflreadpy API: HIGH — live-executed every critical call
- Column schemas: HIGH — enumerated from actual DataFrames
- Join strategy: HIGH — 93.2% match rate verified empirically
- Missingness patterns: HIGH — computed from actual 2000–2023 data
- Cache interaction: HIGH — get_config() output verified
- Position mapping: HIGH — all 22 raw values enumerated and mapped

**Research date:** 2026-05-23
**Valid until:** 2026-08-23 (stable nflreadr data; 90-day window; re-verify if nflreadpy upgrades past 0.1.x)
