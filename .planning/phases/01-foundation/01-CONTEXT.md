# Phase 1: Foundation - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Repo scaffold + shared environment + cache utility. Any researcher can `git clone`, `pip install -r requirements.txt`, and `jupyter lab` into a working environment with `nfl/`, `nba/`, `mlb/`, and `shared/` folders present. Pre-commit hooks (ruff + nbstripout) run automatically. `shared/cache.py` provides a `load_or_fetch` utility that caches data to parquet and skips remote API calls on repeat runs.

Requirements: INFRA-01, INFRA-02

</domain>

<decisions>
## Implementation Decisions

### Venv & Environment
- **D-01:** Single shared top-level `.venv` — all sports use the same environment. One `pip install -r requirements.txt` from the repo root installs everything.
- **D-02:** Python version pinned in `.python-version` (target 3.11.x). Compatible with pyenv and `uv venv --python`.

### Cache Design (`shared/cache.py`)
- **D-03:** `load_or_fetch(key: str, fetch_fn: Callable, force_refresh: bool = False) -> pd.DataFrame` — caller provides an explicit string key. Cache writes/reads `.cache/{key}.parquet` at repo root.
- **D-04:** `.cache/` directory lives at repo root, gitignored. Callers namespace keys by sport (e.g., `"nfl_combine_2000_2023"`) to avoid collisions.
- **D-05:** `force_refresh=False` default — pass `True` to bypass the cache and re-fetch without deleting the file.

### Python Tooling
- **D-06:** `uv` for venv creation (fast); user-facing onboarding command stays `pip install -r requirements.txt` — no pyproject.toml required for install.
- **D-07:** Split requirements: `requirements.txt` (runtime: pandas, scikit-learn, statsmodels, nfl-data-py, nba_api, pybaseball, etc.) and `requirements-dev.txt` (dev: ruff, pre-commit, nbstripout, pytest). Researchers who only run notebooks install only `requirements.txt`.

### Ruff & Pre-commit
- **D-08:** Ruff configured in `pyproject.toml` with rules: E, W (pycodestyle), F (pyflakes), I (isort), line-length = 88 (Black-compatible).
- **D-09:** `ruff format` enabled alongside `ruff check` — one tool for both linting and formatting. Pre-commit runs both on commit.
- **D-10:** `nbstripout` as a pre-commit hook strips cell outputs before commit to keep notebook diffs clean.

### Claude's Discretion
- Pre-commit hook order (ruff → nbstripout vs reversed) — standard ordering is fine.
- Exact Python patch version to pin in `.python-version` (3.11.x) — use latest 3.11 stable.
- Whether to include a `pyproject.toml` `[project]` metadata section or just `[tool.ruff]` — minimal tooling section only.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — INFRA-01 and INFRA-02 define the Phase 1 success criteria verbatim
- `.planning/ROADMAP.md` — Phase 1 success criteria (3 items) are the acceptance gate

### Tech Stack Guidance
- `CLAUDE.md` §Technology Stack — recommended versions for all libraries, uv tooling rationale, nbstripout/pre-commit rationale, "What NOT to Use" table

No external ADRs or specs — all decisions captured above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield repo. No existing code.

### Established Patterns
- None yet — this phase establishes the baseline patterns all subsequent phases will follow.

### Integration Points
- `shared/cache.py` is the Phase 1 output that Phase 2 (NFL Data Pipeline) depends on directly. The `load_or_fetch` signature (D-03) must be stable before Phase 2 begins.

</code_context>

<specifics>
## Specific Ideas

- Cache key naming convention: sport-prefixed strings like `"nfl_combine_2000_2023"` — no slashes in keys (maps to flat `.cache/` files).
- `requirements.txt` should pin exact versions (e.g., `pandas==2.2.2`) for reproducibility, not ranges.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Foundation*
*Context gathered: 2026-04-29*
