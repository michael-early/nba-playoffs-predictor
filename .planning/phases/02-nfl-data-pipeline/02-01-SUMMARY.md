---
phase: 02-nfl-data-pipeline
plan: "01"
subsystem: data-pipeline
tags: [nfl, nflreadpy, polars, pandas, parquet, cache, pytest]

requires:
  - phase: 01-foundation
    provides: shared.cache.load_or_fetch — the cache contract this pipeline uses

provides:
  - "nfl/pipeline.py — CLI data pipeline exposing CACHE_KEY, START_SEASON, END_SEASON, _build_dataset, POSITION_GROUP_MAP as public contract"
  - ".cache/nfl_combine_pipeline_2000_2023.parquet — joined Combine + draft career stats, 7999×25"
  - "tests/test_pipeline.py — 4 passing tests covering position mapping, specialist fallback, cache key parameterization, CLI cache-hit smoke"

affects: [02-02-nfl-eda, phase-03-nfl-analysis]

tech-stack:
  added: [nflreadpy, polars]
  patterns: [fetch-via-load_or_fetch, polars-join-then-to_pandas, argparse-main-pattern]

key-files:
  created:
    - nfl/pipeline.py
    - tests/test_pipeline.py
  modified: []

key-decisions:
  - "Use w_av not car_av — car_av is 100% null in nflreadpy 0.1.5"
  - "7 position groups + Other for specialists (K/P/LS/unmapped)"
  - "sample_membership is exactly drafted/undrafted; not-invited is documented as limitation in module docstring"
  - "Cache key parameterized by START_SEASON/END_SEASON so window changes auto-invalidate"
  - "Polars for fetch+join, then .to_pandas() for cache layer (load_or_fetch requires pd.DataFrame)"

patterns-established:
  - "fetch-via-load_or_fetch: all data acquisition goes through shared.cache.load_or_fetch, never df.to_parquet directly"
  - "polars-join-then-to_pandas: use Polars for join performance, hand off pandas DataFrame to cache layer"

requirements-completed:
  - NFL-01

duration: ~7h (agent runtime including socket recovery)
completed: 2026-05-25
---

# Plan 02-01: NFL Data Pipeline Summary

**Combine measurables + draft career stats joined to parquet via nflreadpy + Polars, with cache contract and 4-test suite**

## Performance

- **Duration:** ~7h (elapsed including socket timeout recovery)
- **Completed:** 2026-05-25
- **Tasks:** 3/3
- **Files created:** 2 (+ 1 binary cache artifact)

## Accomplishments

- `nfl/pipeline.py` — CLI script with all required constants, `_build_dataset`, and `main(--force-refresh)`; exposes public contract for Plan 02 EDA notebook
- `tests/test_pipeline.py` — 4 passing tests: position group map exhaustive coverage, specialist→Other fallback, cache key parameterization, and CLI cache-hit smoke test
- `.cache/nfl_combine_pipeline_2000_2023.parquet` — joined dataset (7999×25) ready for downstream consumption

## Task Commits

1. **Task 1: Implement nfl/pipeline.py** — `d8359cc` (feat(02-01))
2. **Task 2: Write tests/test_pipeline.py** — `a1bd01e` (test(02-01))
3. **Task 3: Generate cache artifact** — run completed, artifact verified (not committed — binary parquet, gitignored)

## Files Created

- `nfl/pipeline.py` — constants, `_build_dataset` (nflreadpy fetch + Polars join + .to_pandas()), `main(--force-refresh)`
- `tests/test_pipeline.py` — 4 tests covering all plan acceptance criteria

## Public Contract for Plan 02

Plan 02-02 (EDA notebook) imports:
```python
from nfl.pipeline import CACHE_KEY, START_SEASON, END_SEASON, _build_dataset, POSITION_GROUP_MAP
```

Observed dataset stats:
- **Shape:** 7999 rows × 25 columns
- **sample_membership:** `{'drafted': 5128, 'undrafted': 2871}`
- **position_group:** `{'WR/TE': 1561, 'DB': 1444, 'OL': 1303, 'DL': 1265, 'LB': 885, 'RB': 820, 'QB': 432, 'Other': 289}`
- **w_av null rate:** 0.403 (undrafted players; within expected 0.30–0.50 range)
- **Drafted rows with null pfr_id:** logged at runtime (Open Question 1 data point)

## Decisions Made

- `w_av` used throughout; `car_av` excluded (100% null in nflreadpy 0.1.5 — Pitfall 1)
- `EDGE` maps to `DL` (Pitfall 3 mitigated)
- Cache key `f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"` is parameterized (Pitfall 4 mitigated)
- `not-invited` prospects documented as limitation in module docstring; not represented in data (only combine-invited players in source)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Socket timeout on second executor agent attempt; work was complete (all 3 tasks committed/run) but SUMMARY.md was not written before disconnect. Recovered via orchestrator rescue.

## Next Phase Readiness

Plan 02-02 (EDA notebook) can proceed immediately:
- Cache artifact at `.cache/nfl_combine_pipeline_2000_2023.parquet` ready
- Public contract (`CACHE_KEY`, `_build_dataset`, `POSITION_GROUP_MAP`) importable from `nfl.pipeline`
- Observed stats above confirm expected distributions match RESEARCH.md predictions

---
*Phase: 02-nfl-data-pipeline*
*Completed: 2026-05-25*
