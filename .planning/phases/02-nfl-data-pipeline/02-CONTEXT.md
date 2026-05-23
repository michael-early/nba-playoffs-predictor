# Phase 2: NFL Data Pipeline - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Clean joined dataset of NFL Combine measurables + career stats, cached to parquet and ready for analysis. Includes an EDA notebook (`nfl_eda.ipynb`) covering distributions, opt-out rates, missingness audit, position breakdowns, and a descriptive opt-out bias comparison (career AV + Pro Bowl rate by drill-skipped status). Sample membership (drafted / undrafted / not-invited) is documented.

Requirements: NFL-01, NFL-02, NFL-10

</domain>

<decisions>
## Implementation Decisions

### Career Outcome Metrics
- **D-01:** AV (Approximate Value, from Pro Football Reference via nflreadr) is the **primary** career outcome — continuous, cross-position, used for OLS regressions in Phase 3.
- **D-02:** Pro Bowl / All-Pro appearances as **secondary** binary outcome — surfaced in EDA descriptive stats, not used for primary regressions. Fetch alongside AV.
- **D-03:** Career window = **full career to date** (all available seasons summed). Recent draftees (2021–2023) will have lower AV by nature — document explicitly as a sample limitation in the pipeline README cell and the EDA notebook.
- **D-04:** Position grouping: **standard NFL position groups** — QB, RB, WR/TE, OL, DL, LB, DB. Applied consistently in pipeline output column and in all EDA position breakdowns.

### Season Range
- **D-05:** Combine data window: **2000–2023**. Pre-2000 data is noisy (fewer drills tracked, inconsistent position reporting). 2024 excluded — <2 seasons of career data for that class.
- **D-06:** Season range configured as **constants at the top of the pipeline script**: `START_SEASON = 2000` / `END_SEASON = 2023`. Consistent with "config cells first" convention adapted for scripts.

### Pipeline Script (`nfl/pipeline.py` or similar)
- **D-07:** Output: **single joined parquet via `shared.cache.load_or_fetch`**. Cache key: `"nfl_combine_pipeline_2000_2023"` (or parameterized from constants). EDA notebook loads from the same cache key — no separate `nfl/data/` folder.
- **D-08:** Stdout: **minimal progress prints** at key steps (fetching combine… done (N rows), fetching career stats… done, joining… final shape N×M). No tqdm.
- **D-09:** **`--force-refresh` CLI flag** (argparse) — passes `force_refresh=True` to `load_or_fetch`. All other config (season range, position groups) uses top-of-script constants. This is the only argparse argument.

### EDA Notebook (`nfl/nfl_eda.ipynb`)
- **D-10:** **One notebook** covering both NFL-02 (EDA) and NFL-10 (opt-out bias). Structure: config cell → data load (from cache) → distributions → missingness audit → opt-out rates by position → opt-out bias comparison → summary.
- **D-11:** Opt-out bias analysis (NFL-10) = **descriptive comparison**: mean/median AV and Pro Bowl rate by drill-skipped status, grouped by position. No formal statistical tests in Phase 2 — those belong in Phase 3.

### Claude's Discretion
- Exact cache key format for parameterized season range (e.g., `"nfl_combine_pipeline_2000_2023"` or `f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"`).
- Column naming for AV vs Pro Bowl columns in the joined output.
- Whether opt-out is defined per-drill or as "skipped any drill."

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements & Scope
- `.planning/REQUIREMENTS.md` — NFL-01, NFL-02, NFL-10 define Phase 2 success criteria verbatim; traceability table confirms which requirements map to this phase
- `.planning/ROADMAP.md` — Phase 2 success criteria (3 items) are the acceptance gate

### Phase 1 Decisions (carry-forward constraints)
- `.planning/phases/01-foundation/01-CONTEXT.md` — D-03 (`load_or_fetch` signature, stable API), D-04 (cache key naming convention: sport-prefixed, no slashes), D-05 (`force_refresh` semantics)

### Data Source
- `nfl/README.md` — confirms `nflreadpy` (replaces archived `nfl-data-py`) as data source; convert to pandas with `.to_pandas()` before passing to `shared.cache.load_or_fetch`
- `shared/cache.py` — `load_or_fetch(key, fetch_fn, force_refresh=False, *, cache_dir=CACHE_DIR)` — read before writing any fetch code

### Tech Stack
- `CLAUDE.md` §Technology Stack — recommended library versions; "What NOT to Use" table; nfl-data-py → nflreadpy migration note

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `shared/cache.py` — `load_or_fetch(key, fetch_fn, force_refresh, cache_dir)` is the ONLY approved path for data fetches. Both combine and career stat fetches go through it. Two separate cache keys (one per source) or a single joined key after an in-memory merge — planner should decide based on whether raw data re-use is valuable.
- `nfl/__init__.py` — exists (empty), provides the `nfl` package namespace.

### Established Patterns
- **Config constants at top**: Season range as module-level constants mirrors the notebook "config cells first" pattern. Follow this for the pipeline script.
- **Cache key convention**: `"sport_dataset_startyear_endyear"` — e.g., `"nfl_combine_2000_2023"`. Flat keys, no slashes.
- **pandas as interchange format**: nflreadpy returns Polars by default; `.to_pandas()` converts before passing to `load_or_fetch` (confirmed in nfl/README.md).

### Integration Points
- The pipeline script's cache key is the **integration contract** between `nfl/pipeline.py` and `nfl/nfl_eda.ipynb`. Both must reference the same key string — define it as a shared constant or document it explicitly.
- Phase 3 (Statistical Analysis) will load from the same cache artifact — the joined parquet schema is a public contract. Column names (combine drills, position group, AV, Pro Bowl flag) must be stable.

</code_context>

<specifics>
## Specific Ideas

- User initially asked about Pro Bowl / All-Pro as the career outcome. Discussion surfaced that AV is better for regression (continuous, no class imbalance), but Pro Bowl is worth showing descriptively. Both fetched in Phase 2.
- Cache key for the final joined output should embed the season range so it's self-describing (e.g., `"nfl_combine_pipeline_2000_2023"`), making it easy to distinguish from raw intermediate caches.
- Opt-out rate in NFL-02 = rate at which players skip each specific drill (e.g., 40-yard dash opt-out rate by position). Opt-out bias in NFL-10 = whether career AV/Pro Bowl rate differs between skippers and completers for each drill.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-NFL Data Pipeline*
*Context gathered: 2026-05-23*
