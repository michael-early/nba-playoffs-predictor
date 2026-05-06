# Phase 1: Foundation - Research

**Researched:** 2026-04-29
**Domain:** Python project scaffold — venv, tooling, pre-commit hooks, shared cache utility
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Single shared top-level `.venv` — all sports use the same environment. One `pip install -r requirements.txt` from the repo root installs everything.
- **D-02:** Python version pinned in `.python-version` (target 3.11.x). Compatible with pyenv and `uv venv --python`.
- **D-03:** `load_or_fetch(key: str, fetch_fn: Callable, force_refresh: bool = False) -> pd.DataFrame` — caller provides an explicit string key. Cache writes/reads `.cache/{key}.parquet` at repo root.
- **D-04:** `.cache/` directory lives at repo root, gitignored. Callers namespace keys by sport (e.g., `"nfl_combine_2000_2023"`) to avoid collisions.
- **D-05:** `force_refresh=False` default — pass `True` to bypass the cache and re-fetch without deleting the file.
- **D-06:** `uv` for venv creation (fast); user-facing onboarding command stays `pip install -r requirements.txt` — no pyproject.toml required for install.
- **D-07:** Split requirements: `requirements.txt` (runtime) and `requirements-dev.txt` (dev: ruff, pre-commit, nbstripout, pytest). Researchers who only run notebooks install only `requirements.txt`.
- **D-08:** Ruff configured in `pyproject.toml` with rules: E, W, F, I, line-length = 88.
- **D-09:** `ruff format` enabled alongside `ruff check` — one tool for both linting and formatting. Pre-commit runs both on commit.
- **D-10:** `nbstripout` as a pre-commit hook strips cell outputs before commit.

### Claude's Discretion
- Pre-commit hook order (ruff → nbstripout vs reversed) — standard ordering is fine.
- Exact Python patch version to pin in `.python-version` (3.11.x) — use latest 3.11 stable.
- Whether to include a `pyproject.toml` `[project]` metadata section or just `[tool.ruff]` — minimal tooling section only.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | User can run `git clone` + `pip install -r requirements.txt` + `jupyter lab` and have a working environment — repo scaffold with sport-specific folders (nfl/, nba/, mlb/, shared/), .venv, .gitignore, pre-commit hooks (ruff + nbstripout) | Covered by Standard Stack, Architecture Patterns, and Code Examples sections |
| INFRA-02 | Data fetches check disk cache before hitting any remote API — shared `shared/cache.py` load-or-fetch utility caching to parquet | Covered by cache implementation pattern in Code Examples |
</phase_requirements>

---

## Summary

This phase is a greenfield Python project scaffold. Nothing exists in the repo yet — no `.venv`, no `pyproject.toml`, no `.gitignore`, no `requirements.txt`. Every artifact must be created from scratch.

Two facts discovered during research materially affect planning decisions relative to CONTEXT.md assumptions:

First, **nfl-data-py is deprecated.** The nflverse org archived the repo on Sep 25, 2025 and explicitly redirects to `nflreadpy`. This affects `requirements.txt` content but not the cache utility design. The planner must decide: stub requirements.txt with the replacement (`nflreadpy`) or note the migration. Since nflreadpy is beta (0.1.5) and returns Polars by default, this introduces a `.to_pandas()` call in Phase 2 data pipelines — not a Phase 1 concern, but the requirements file must reference `nflreadpy` not `nfl-data-py`.

Second, **pandas 3.0 is now current (3.0.2 on PyPI)**. The CLAUDE.md stack doc recommends pandas 2.2.x. The sport-specific libraries (nba_api 1.11.4, pybaseball 2.2.7) have not been explicitly confirmed against pandas 3.0. For a research repo pinning to exact versions, pandas 2.2.3 remains the safe conservative pin — it is the latest 2.2.x release and avoids unverified compatibility risks with pandas 3.0 string dtype changes and CoW enforcement.

**Primary recommendation:** Pin pandas==2.2.3, use nflreadpy==0.1.5 in requirements.txt (not nfl-data-py), and use the pre-commit hook approach for nbstripout (which strips working copy files, not just git staging — acceptable for a research repo where outputs should not be committed).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Venv + dependency management | Dev machine (local) | — | One-time setup; no server or CI tier in scope |
| Pre-commit hooks | Dev machine (git hook runner) | — | Enforced at commit time on dev machine |
| Cache utility (load_or_fetch) | Shared Python module | — | Called by sport-specific scripts; lives in shared/ |
| Parquet read/write | Disk (local .cache/) | — | No cloud storage; pure local filesystem |
| Folder scaffold (nfl/, nba/, mlb/) | Repo structure | — | Static directories with README stubs; no runtime tier |

---

## Standard Stack

### Core (requirements.txt — runtime)
| Library | Pinned Version | Purpose | Source |
|---------|---------------|---------|--------|
| pandas | 2.2.3 | DataFrames, parquet I/O | [VERIFIED: PyPI registry] |
| numpy | 1.26.4 | Array math; safe baseline for all deps | [VERIFIED: PyPI registry] |
| scikit-learn | 1.6.1 | ML pipelines (later phases) | [VERIFIED: PyPI registry — 1.8.0 is latest but 1.6.1 is stable LTS-equivalent] |
| statsmodels | 0.14.6 | OLS, diagnostics (later phases) | [VERIFIED: PyPI registry] |
| scipy | 1.13.1 | Statistical tests; statsmodels dep | [VERIFIED: PyPI registry] |
| nflreadpy | 0.1.5 | NFL data (replaces deprecated nfl-data-py) | [VERIFIED: PyPI registry; CITED: github.com/nflverse/nfl_data_py archived notice] |
| nba_api | 1.11.4 | NBA.com endpoints | [VERIFIED: PyPI registry] |
| pybaseball | 2.2.7 | Statcast, FanGraphs, Baseball Reference | [VERIFIED: PyPI registry] |
| matplotlib | 3.9.4 | Base plotting; seaborn dependency | [VERIFIED: PyPI registry — pinning 3.9.x per CLAUDE.md seaborn compatibility note] |
| seaborn | 0.13.2 | Statistical visualization | [VERIFIED: PyPI registry] |
| plotly | 5.24.1 | Interactive notebook charts | [VERIFIED: PyPI registry — latest 5.x] |
| requests | 2.32.3 | HTTP (nba_api dependency) | [VERIFIED: PyPI registry] |
| python-dotenv | 1.0.1 | Env var management | [VERIFIED: PyPI registry] |
| tqdm | 4.67.3 | Progress bars for data loops | [VERIFIED: PyPI registry] |
| jupyterlab | 4.4.4 | Notebook environment | [VERIFIED: PyPI registry — 4.4.x stable, 4.5.x is latest] |
| pyarrow | — | Parquet read/write backend for pandas | [ASSUMED — pyarrow is the standard parquet engine; fastparquet is the alternative] |

> **Version note on scikit-learn:** Latest is 1.8.0 but this phase only scaffolds; 1.6.1 is the last minor before 1.7/1.8. Given sport-data-library test coverage is unverified against 1.8.0, 1.6.1 is conservative. Planner may choose 1.7.2 as a reasonable middle ground. [ASSUMED — no direct test evidence; conservative choice]

> **Version note on pandas:** pandas 3.0.2 is current on PyPI. Pinning 2.2.3 because nflreadpy, nba_api, and pybaseball compatibility with pandas 3.0 is unconfirmed. pandas 3.0 changed string dtype inference (object → str) and enforces CoW — both can break library internals that check `dtype == 'object'`. [CITED: pandas.pydata.org/community/blog/pandas-3.0.html]

> **pyarrow note:** Required to use `pd.read_parquet` / `pd.to_parquet` without fastparquet. Not in CLAUDE.md stack doc but is the standard pandas parquet engine. [ASSUMED — standard ecosystem knowledge; verify with `pip install pyarrow` in venv setup step]

### Dev (requirements-dev.txt)
| Library | Pinned Version | Purpose | Source |
|---------|---------------|---------|--------|
| ruff | 0.15.12 | Linting + formatting | [VERIFIED: PyPI registry] |
| pre-commit | 4.6.0 | Git hook runner | [VERIFIED: PyPI registry] |
| nbstripout | 0.9.1 | Strip notebook outputs before commit | [VERIFIED: PyPI registry] |
| pytest | 9.0.3 | Test runner for shared/ utilities | [VERIFIED: PyPI registry] |

**Installation (onboarding sequence):**
```bash
# Step 1 — create venv (developer uses uv; plain python works too)
uv venv --python 3.11 .venv
source .venv/bin/activate

# Step 2 — install runtime deps (this is the pip command researchers use)
pip install -r requirements.txt

# Step 3 — install dev deps (only needed for contributors)
pip install -r requirements-dev.txt

# Step 4 — register pre-commit hooks
pre-commit install
```

> `pip install -r requirements.txt` works inside a uv-created venv — uv venv produces a standard PEP 405 virtual environment that pip can install into. [VERIFIED: uv docs — `uv pip install -r requirements.txt` also works as a faster equivalent] [CITED: docs.astral.sh/uv/concepts/python-versions/]

---

## Architecture Patterns

### System Architecture Diagram

```
Researcher
    |
    | git clone + pip install -r requirements.txt
    v
.venv (Python 3.11.14, shared across all sports)
    |
    +-- nfl/ notebooks & scripts ----+
    |                                |
    +-- nba/ notebooks & scripts ----+--> shared/cache.py
    |                                |         |
    +-- mlb/ notebooks & scripts ----+         |
                                               |
                     .cache/{key}.parquet <----+----> Remote APIs
                     (disk, gitignored)    hit     (nflreadpy, nba_api,
                                          only     pybaseball)
                                          on miss
                                          or force_refresh=True

git commit
    |
    v
pre-commit hooks (run automatically)
    |
    +-- ruff-check (lint, --fix)
    +-- ruff-format (format)
    +-- nbstripout (strip cell outputs from .ipynb)
```

### Recommended Project Structure
```
Sports/
├── .venv/                   # gitignored; uv venv --python 3.11 .venv
├── .cache/                  # gitignored; parquet cache files per key
├── .python-version          # "3.11.14" — read by uv and pyenv
├── .pre-commit-config.yaml  # ruff + nbstripout hooks
├── .gitignore               # venv, cache, pyc, checkpoints
├── pyproject.toml           # [tool.ruff] only — no [project] section
├── requirements.txt         # pinned runtime deps
├── requirements-dev.txt     # pinned dev deps
├── shared/
│   ├── __init__.py          # empty
│   └── cache.py             # load_or_fetch utility
├── nfl/
│   ├── README.md            # scope and planned analyses
│   └── __init__.py          # empty (makes it importable)
├── nba/
│   ├── README.md
│   └── __init__.py
└── mlb/
    ├── README.md
    └── __init__.py
```

> **On `__init__.py` in sport folders:** Needed if any notebook does `from shared.cache import load_or_fetch` with a sys.path that includes the repo root. An empty `__init__.py` also prevents accidental package discovery collisions. Alternatively, notebooks add repo root to `sys.path` at top. Either approach works; `__init__.py` is the more conventional choice. [ASSUMED]

### Pattern 1: pyproject.toml (ruff only, no [project] section)
**What:** Minimal pyproject.toml that configures ruff without declaring a Python package.
**When to use:** Tooling-only configuration for a research repo that installs via requirements.txt.
```toml
# Source: docs.astral.sh/ruff/configuration/
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I"]

[tool.ruff.format]
# Defaults match Black: double quotes, space indent
```

### Pattern 2: .pre-commit-config.yaml
**What:** Pre-commit hooks for ruff (lint + format) then nbstripout.
**When to use:** Registers on `pre-commit install`; runs on every `git commit`.
```yaml
# Source: github.com/astral-sh/ruff-pre-commit (verified rev: v0.15.12)
# Source: github.com/kynan/nbstripout (verified rev: 0.9.1)
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/kynan/nbstripout
    rev: 0.9.1
    hooks:
      - id: nbstripout
```

> **Hook order:** ruff-check (with --fix) → ruff-format → nbstripout. Linter fixes first, then formatter normalizes, then notebook outputs stripped. [CITED: astral.sh/ruff-pre-commit — linter before formatter when using --fix]

> **nbstripout hook behavior:** Using nbstripout as a pre-commit hook modifies the working copy (strips outputs from the actual .ipynb file on disk before committing). This differs from the `nbstripout --install` git-filter approach, which only modifies what git sees. For this project, hook mode is fine — researchers understand outputs are not committed. [CITED: github.com/kynan/nbstripout README]

> **Hook IDs:** The ruff pre-commit hook uses `ruff-check` (not `ruff`) and `ruff-format` as of ruff >=0.3.0. Earlier docs show `ruff` as the id. Use the current IDs. [VERIFIED: github.com/astral-sh/ruff-pre-commit, rev v0.15.12]

### Pattern 3: .python-version
**What:** Single line file read by both uv and pyenv.
```
3.11.14
```
`uv venv --python 3.11 .venv` will respect this file and download 3.11.14 if needed. [CITED: docs.astral.sh/uv/concepts/python-versions/]

### Pattern 4: shared/cache.py
**What:** Load-or-fetch utility with parquet backing.
**When to use:** All sport-specific data fetch calls go through this; callers own the fetch_fn.
```python
# Source: standard pandas parquet I/O + pathlib pattern [ASSUMED implementation]
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).parents[1] / ".cache"


def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Return cached DataFrame or call fetch_fn and cache the result.

    Args:
        key: Cache key; no slashes. Maps to .cache/{key}.parquet.
        fetch_fn: Zero-argument callable that fetches and returns a DataFrame.
        force_refresh: If True, bypass cache and re-fetch even if file exists.

    Returns:
        DataFrame loaded from cache or freshly fetched.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / f"{key}.parquet"

    if not force_refresh and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = fetch_fn()
    df.to_parquet(cache_path, index=False)
    return df
```

> **pyarrow required:** `pd.read_parquet` and `pd.to_parquet` require either `pyarrow` or `fastparquet`. pyarrow is the standard choice. Add `pyarrow` to `requirements.txt`. [ASSUMED — standard pandas ecosystem knowledge]

> **fetch_fn signature:** `Callable[[], pd.DataFrame]` (zero-argument callable). Callers use `functools.partial` or a lambda to bind arguments: `load_or_fetch("nfl_combine", lambda: nflreadpy.load_combine())`. [ASSUMED]

### Anti-Patterns to Avoid
- **`nbstripout --install` (git filter mode) instead of pre-commit hook:** The `--install` approach requires each developer to run the command manually after cloning. pre-commit hook mode is enforced automatically once `pre-commit install` is run. Downside of hook mode: it modifies the working copy. Acceptable trade-off for this project. [CITED: github.com/kynan/nbstripout]
- **Using `nfl-data-py` in requirements.txt:** Archived Sep 2025; no further maintenance. Use `nflreadpy` instead. [VERIFIED: github.com/nflverse/nfl_data_py archived notice]
- **Pinning pandas>=3.0:** nflreadpy, nba_api, pybaseball compatibility with pandas 3.0 is unconfirmed. Pin `pandas==2.2.3` until libraries are verified. [ASSUMED — conservative]
- **No `pyarrow` in requirements.txt:** `pd.to_parquet` fails at runtime without a parquet engine installed. pyarrow must be explicit. [ASSUMED]
- **Putting `.cache/` in the repo root without gitignoring it:** Parquet files can be large (hundreds of MB for full seasons of Statcast data). Always gitignore `.cache/`. [ASSUMED]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notebook output stripping | Custom git filter script | nbstripout 0.9.1 | Handles edge cases (execution counts, metadata variants, empty cell arrays) |
| Linting + formatting | flake8 + black + isort separately | ruff 0.15.12 | Single binary, 10-100x faster, same rules |
| Parquet serialization | Custom CSV/pickle cache | `pd.to_parquet` / `pd.read_parquet` | Type-preserving, compressed, fast; CSV loses dtypes |
| Python version management | Hardcoded shebang or OS Python | `.python-version` + uv | Reproducible across machines |
| Pre-commit orchestration | Shell script with git hooks | pre-commit 4.6.0 | Auto-updates hook revisions, handles staged-file scoping |

**Key insight:** Every tool in this phase is infrastructure glue. Custom implementations of any of these have the same functionality but with maintenance burden, edge cases, and no community support.

---

## Common Pitfalls

### Pitfall 1: nfl-data-py still in requirements.txt
**What goes wrong:** `pip install -r requirements.txt` installs a deprecated, unmaintained library. Future Python version or pandas upgrades will break it with no fix available.
**Why it happens:** CLAUDE.md and earlier research recommended nfl-data-py; its deprecation occurred Sep 2025 after that research was written.
**How to avoid:** Use `nflreadpy==0.1.5`. Note: nflreadpy returns Polars DataFrames by default — Phase 2 data pipelines must call `.to_pandas()` or use the pandas extra.
**Warning signs:** `import nfl_data_py` still works (0.3.3 installable) but is frozen.

### Pitfall 2: Missing pyarrow in requirements.txt
**What goes wrong:** `df.to_parquet(...)` raises `ImportError: Missing optional dependency 'pyarrow'` at first cache write. Researcher hits error on first data fetch.
**Why it happens:** pandas does not install pyarrow automatically; it's an optional dependency.
**How to avoid:** Add `pyarrow` to `requirements.txt` explicitly.
**Warning signs:** Error only appears at runtime when cache.py is first called, not at import time.

### Pitfall 3: ruff hook ID mismatch (old `ruff` id vs new `ruff-check`)
**What goes wrong:** Using `id: ruff` in pre-commit config causes a hook-not-found error with ruff >=0.3.0.
**Why it happens:** ruff renamed its pre-commit hook from `ruff` to `ruff-check` and added `ruff-format` as a separate hook.
**How to avoid:** Use `id: ruff-check` and `id: ruff-format`. Pin `rev: v0.15.12`.
**Warning signs:** `pre-commit install` succeeds but `git commit` errors with "No hook with id 'ruff'".

### Pitfall 4: nbstripout not clearing execution_count
**What goes wrong:** Notebook diffs still show execution_count changes even after nbstripout.
**Why it happens:** Default nbstripout behavior clears outputs and execution_count. This is correct behavior. If diffs still appear, the hook is not running (pre-commit not installed, or wrong file type detection).
**How to avoid:** Confirm `pre-commit install` was run. Verify `.pre-commit-config.yaml` has `id: nbstripout`.
**Warning signs:** `git diff --cached` shows `"execution_count": 5` lines.

### Pitfall 5: pandas 3.0 silent dtype breakage
**What goes wrong:** Upgrading `pandas` to 3.x breaks nflreadpy, nba_api, or pybaseball internally — columns that returned `object` dtype now return `str` dtype, causing downstream `dtype == 'object'` checks in those libraries to silently fail or raise.
**Why it happens:** pandas 3.0 changed default string inference. Sport data libraries may not yet handle this.
**How to avoid:** Pin `pandas==2.2.3`. Do not use `pandas>=2.2` (open-ended).
**Warning signs:** Type errors or empty DataFrames from sport data libraries after any pandas upgrade.

### Pitfall 6: uv venv Python version not matching .python-version
**What goes wrong:** `uv venv .venv` creates a venv with system Python (3.14.2 on this machine) rather than 3.11.14.
**Why it happens:** uv reads `.python-version` only after the file exists. If the file is created after the venv, or if the developer runs `uv venv` before `echo "3.11.14" > .python-version`, the venv gets the wrong Python.
**How to avoid:** Create `.python-version` first, then run `uv venv --python 3.11 .venv`. Or: always use the explicit flag `uv venv --python 3.11 .venv`.
**Warning signs:** `python --version` inside the venv shows 3.14.x.

---

## Code Examples

### requirements.txt (pinned runtime)
```
# Core data science
pandas==2.2.3
numpy==1.26.4
scikit-learn==1.6.1
statsmodels==0.14.6
scipy==1.13.1

# Parquet engine (required by shared/cache.py)
pyarrow==18.1.0

# NFL data
nflreadpy==0.1.5

# NBA data
nba_api==1.11.4

# MLB data
pybaseball==2.2.7

# Visualization
matplotlib==3.9.4
seaborn==0.13.2
plotly==5.24.1

# Notebook
jupyterlab==4.4.4

# Utilities
requests==2.32.3
python-dotenv==1.0.1
tqdm==4.67.3
```

> **pyarrow version note:** pyarrow 18.1.0 is a plausible recent version. [ASSUMED — verify with `pip3 index versions pyarrow | head -1` before writing requirements.txt]

### requirements-dev.txt
```
-r requirements.txt
ruff==0.15.12
pre-commit==4.6.0
nbstripout==0.9.1
pytest==9.0.3
```

### .gitignore (minimum viable)
```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Cache
.cache/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Environment
.env
.env.*

# OS
.DS_Store
Thumbs.db

# Build / dist
*.egg-info/
dist/
build/
```

### shared/cache.py (full implementation)
See Pattern 4 in Architecture Patterns above.

### Notebook preamble pattern (for nfl/ nba/ mlb/ stubs)
```python
# Config cell — modify before running
import sys
from pathlib import Path

# Add repo root to path so `from shared.cache import load_or_fetch` works
sys.path.insert(0, str(Path.cwd().parents[0]))  # adjust depth if needed

from shared.cache import load_or_fetch
```

### nflreadpy usage (Phase 2 preview — not Phase 1 work)
```python
# nflreadpy returns Polars by default; convert to pandas for cache.py
import nflreadpy

def _fetch_combine() -> pd.DataFrame:
    return nflreadpy.load_combine().to_pandas()

combine_df = load_or_fetch("nfl_combine", _fetch_combine)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nfl-data-py | nflreadpy | Sep 2025 (archived) | Phase 2 must use nflreadpy + .to_pandas() |
| `id: ruff` in pre-commit | `id: ruff-check` + `id: ruff-format` | ruff >=0.3.0 | Old hook id causes error |
| `%matplotlib inline` | Remove magic; outputs render by default | JupyterLab 3+ | Do not add this magic to stub notebooks |
| pandas 2.2.x as "latest stable" | pandas 3.0.2 is current | Jan 2026 | Pin 2.2.3 until library compat confirmed |
| `pip` for venv creation | `uv venv` (10-100x faster) | 2024 | Still use `pip install -r` for onboarding UX |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pyarrow is required for `pd.to_parquet`; must be in requirements.txt | Standard Stack, Code Examples | RuntimeError on first cache write |
| A2 | pyarrow 18.1.0 is a current version; planner should verify with `pip3 index versions pyarrow` | Code Examples | Wrong pin in requirements.txt |
| A3 | `__init__.py` in sport folders enables `from shared.cache import load_or_fetch` via sys.path | Architecture Patterns | ImportError in notebooks if wrong |
| A4 | nba_api 1.11.4 and pybaseball 2.2.7 are compatible with pandas 2.2.3 | Standard Stack | Install conflicts or runtime dtype errors |
| A5 | scikit-learn 1.6.1 (not 1.8.0) is the safer pin for initial setup | Standard Stack | Missed features in 1.7/1.8; low risk for Phase 1 |
| A6 | nflreadpy 0.1.5 `load_combine()` returns same columns as nfl-data-py `import_combine_data()` | Standard Stack | Phase 2 data pipeline needs column mapping |

---

## Open Questions

1. **pyarrow version to pin**
   - What we know: pyarrow is required for parquet; standard pandas parquet engine
   - What's unclear: exact current version on PyPI (not checked)
   - Recommendation: Run `pip3 index versions pyarrow | head -1` and pin latest

2. **nflreadpy `load_combine()` column parity with nfl-data-py**
   - What we know: nflreadpy is the official replacement; returns Polars by default
   - What's unclear: column names match exactly or require renaming in Phase 2
   - Recommendation: Not a Phase 1 concern; note as Phase 2 risk. Phase 1 only needs nflreadpy in requirements.txt.

3. **pandas 3.0 compatibility with nba_api and pybaseball**
   - What we know: pandas 3.0.2 is current; 3.0 has breaking string dtype and CoW changes
   - What's unclear: whether nba_api 1.11.4 and pybaseball 2.2.7 pass tests against pandas 3.0
   - Recommendation: Pin pandas==2.2.3 now; revisit after testing in Phase 2.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | .python-version, venv | Download available | 3.11.14 via uv | — |
| uv | Fast venv creation | Yes | 0.10.6 | `python3 -m venv .venv` |
| pre-commit | Hook registration | No (not installed) | — | Install via requirements-dev.txt |
| ruff | Lint/format | No (not installed) | — | Install via requirements-dev.txt |
| nbstripout | Notebook output stripping | No (not installed) | — | Install via requirements-dev.txt |
| pip | Package install | Yes | 25.3 | — |
| git | Version control | Yes (assumed, repo exists) | — | — |

**Missing dependencies with no fallback:** None — all missing items install from requirements-dev.txt.

**Missing dependencies with fallback:** uv is available and preferred; `python3 -m venv` is the fallback if uv is unavailable on a different machine.

---

## Sources

### Primary (HIGH confidence)
- PyPI registry (pip3 index versions) — all package versions in Standard Stack table
- `github.com/astral-sh/ruff-pre-commit` — ruff pre-commit hook IDs and rev v0.15.12
- `docs.astral.sh/ruff/configuration/` — pyproject.toml [tool.ruff] and [tool.ruff.lint] sections
- `docs.astral.sh/uv/concepts/python-versions/` — .python-version file behavior with uv
- `github.com/kynan/nbstripout` — pre-commit hook YAML, behavior difference from git filter mode
- `github.com/nflverse/nfl_data_py` — archived Sep 2025, deprecated in favor of nflreadpy

### Secondary (MEDIUM confidence)
- `pypi.org/project/nflreadpy/` — version 0.1.5, Polars-first, load_combine() function
- `pandas.pydata.org/community/blog/pandas-3.0.html` — pandas 3.0 breaking changes (string dtype, CoW)

### Tertiary (LOW confidence)
- Assumed: pyarrow required in requirements.txt (standard ecosystem knowledge, not verified in session)
- Assumed: column parity between nflreadpy.load_combine() and nfl-data-py.import_combine_data()

---

## Metadata

**Confidence breakdown:**
- Standard Stack versions: HIGH — verified via `pip3 index versions` against live PyPI
- Pre-commit hook config: HIGH — verified against official repos
- cache.py implementation: MEDIUM — correct pattern, pyarrow dependency is ASSUMED
- nflreadpy as nfl-data-py replacement: HIGH — verified via archived repo notice
- pandas version pin rationale: MEDIUM — breaking changes verified, library compat with 2.2.3 assumed

**Research date:** 2026-04-29
**Valid until:** 2026-07-29 (90 days — stable tooling ecosystem; nflreadpy is beta, check for updates)
