# Phase 2: NFL Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 2-NFL Data Pipeline
**Areas discussed:** Career outcome metric, Season range, Notebook vs notebook split, Pipeline script design

---

## Career Outcome Metric

| Option | Description | Selected |
|--------|-------------|----------|
| AV (Approximate Value) | PFR catch-all; continuous, cross-position; gold standard for combine research | ✓ (primary) |
| Games started (career) | Simple, position-agnostic; noisier for players who changed roles | |
| Multiple metrics | AV + games started; richer but adds join complexity | |
| Pro Bowl/All-Pro (user freeform) | Binary flag for elite career; class imbalance risk; fewer data points | ✓ (secondary) |

**User's choice:** Both — AV as primary outcome for regressions, Pro Bowl/All-Pro as secondary shown in EDA descriptive stats.
**Notes:** User initially asked "pro bowls/all pro?" — discussion surfaced that AV avoids class imbalance and provides continuous signal better suited for OLS. User agreed to use AV as primary with Pro Bowl as a secondary cut.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full career to date | All available seasons summed; recent draftees have lower AV by design | ✓ |
| First 3 seasons only | Normalizes window so all draftees are comparable; loses veteran info | |
| You decide | Claude picks standard approach | |

**User's choice:** Full career to date.
**Notes:** Recent draftees (2021–2023) will have lower AV — document explicitly as a sample limitation.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Standard NFL position groups | QB, RB, WR/TE, OL, DL, LB, DB | ✓ |
| Broad offense/defense/special teams | Simpler, more samples per group, less within-group granularity | |
| You decide | Claude uses standard groups | |

**User's choice:** Standard NFL position groups.

---

## Season Range

| Option | Description | Selected |
|--------|-------------|----------|
| 2000–2023 | Standard window; pre-2000 noisy; 2024 excluded (limited career data) | ✓ |
| 2000–2024 | One more draft class; 2024 rookies have ~1 season of AV | |
| 1987–2023 | Longest window; significant pre-2000 data quality issues | |

**User's choice:** 2000–2023.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Configurable constants at top of script | START_SEASON = 2000 / END_SEASON = 2023; consistent with config-cells-first convention | ✓ |
| CLI args (argparse) | --start-season / --end-season flags; more scriptable but less notebook-friendly | |

**User's choice:** Configurable constants at top of script.

---

## Notebook vs Notebook Split

| Option | Description | Selected |
|--------|-------------|----------|
| One notebook: nfl_eda.ipynb | EDA first, opt-out bias second; single top-to-bottom file | ✓ |
| Two notebooks | nfl_eda.ipynb + nfl_optout_bias.ipynb; cleaner separation, two files to run | |

**User's choice:** One notebook.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Descriptive comparison | Mean/median AV and Pro Bowl rate by drill-skipped status, by position; no formal tests | ✓ |
| Statistical test included | Mann-Whitney U per drill per position; more rigorous | |

**User's choice:** Descriptive comparison. Formal tests deferred to Phase 3.

---

## Pipeline Script Design

| Option | Description | Selected |
|--------|-------------|----------|
| Single joined parquet via cache | load_or_fetch to .cache/; EDA loads from same key; no extra output dir | ✓ |
| Parquet in nfl/data/ folder | More visible; adds second artifact location to manage | |

**User's choice:** Single joined parquet via cache.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal progress prints | print() at key steps (fetch start/end, final shape) | ✓ |
| tqdm progress bars | Visual bar for long fetches; already in requirements | |
| Silent (only on error) | Cleanest for scripted environments | |

**User's choice:** Minimal progress prints.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — --force-refresh CLI flag | Single argparse arg; passes force_refresh=True to load_or_fetch | ✓ |
| No — constants only | FORCE_REFRESH = False constant at top | |

**User's choice:** --force-refresh CLI flag.

---

## Claude's Discretion

- Exact cache key format for parameterized season range.
- Column naming for AV vs Pro Bowl columns in joined output.
- Whether "opt-out" is defined per-drill or as "skipped any drill."
- Pre-commit hook order (ruff → nbstripout) — carried from Phase 1.

## Deferred Ideas

None — discussion stayed within Phase 2 scope.
