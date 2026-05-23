---
phase: 01-foundation
plan: "01"
subsystem: scaffold
tags:
  - python
  - scaffold
  - tooling
  - ruff
  - pre-commit
dependency_graph:
  requires: []
  provides:
    - requirements.txt (pinned runtime deps)
    - requirements-dev.txt (pinned dev deps)
    - pyproject.toml (ruff config)
    - .python-version (Python 3.11.14 pin)
    - .gitignore (excludes .venv/, .cache/, outputs)
    - .pre-commit-config.yaml (ruff-check, ruff-format, nbstripout)
    - shared/ package directory
    - nfl/ package directory with README
    - nba/ package directory with README stub
    - mlb/ package directory with README stub
  affects:
    - 01-02 (cache utility depends on shared/__init__.py and requirements.txt)
tech_stack:
  added:
    - pandas==2.2.3
    - numpy==1.26.4
    - scikit-learn==1.6.1
    - statsmodels==0.14.6
    - scipy==1.13.1
    - pyarrow==18.1.0
    - nflreadpy==0.1.5
    - nba_api==1.11.4
    - pybaseball==2.2.7
    - matplotlib==3.9.4
    - seaborn==0.13.2
    - plotly==5.24.1
    - jupyterlab==4.4.4
    - requests==2.32.3
    - python-dotenv==1.0.1
    - tqdm==4.67.3
    - ruff==0.15.12
    - pre-commit==4.6.0
    - nbstripout==0.9.1
    - pytest==9.0.3
  patterns:
    - Split requirements (runtime vs dev) — researchers install requirements.txt only
    - pyproject.toml ruff-only (no [project] section) for tooling-only config
    - pre-commit hooks: ruff-check --fix -> ruff-format -> nbstripout (lint before format before strip)
    - Empty __init__.py marks each sport folder as an importable Python package
key_files:
  created:
    - .python-version
    - pyproject.toml
    - requirements.txt
    - requirements-dev.txt
    - .pre-commit-config.yaml
    - shared/__init__.py
    - nfl/__init__.py
    - nfl/README.md
    - nba/__init__.py
    - nba/README.md
    - mlb/__init__.py
    - mlb/README.md
  modified:
    - .gitignore (replaced prior project-specific content with standard plan content)
decisions:
  - "Used nflreadpy==0.1.5 instead of deprecated nfl-data-py (archived Sep 2025 per nflverse org)"
  - "Pinned pandas==2.2.3 not 3.x — nba_api/pybaseball compat with pandas 3.0 unconfirmed"
  - "Used ruff hook IDs ruff-check and ruff-format (not legacy 'ruff' id deprecated in ruff >=0.3.0)"
  - "Removed nfl-data-py reference from requirements.txt comment — acceptance criteria grep excludes it entirely"
metrics:
  duration: "3 minutes"
  completed: "2026-05-23"
  tasks_completed: 4
  tasks_total: 4
  files_created: 12
  files_modified: 1
---

# Phase 01 Plan 01: Python Repo Scaffold Summary

Single line: Greenfield Python repo scaffold with pinned runtime + dev requirements, ruff + nbstripout pre-commit hooks, and importable nfl/nba/mlb/shared package directories.

## What Was Built

The complete project scaffold for the Sports ML Research repository. A researcher can now:
1. Run `uv venv --python 3.11 .venv && source .venv/bin/activate`
2. Run `pip install -r requirements.txt` — all runtime deps installed deterministically
3. Run `pip install -r requirements-dev.txt && pre-commit install` — dev tools + hooks registered
4. Import `shared`, `nfl`, `nba`, `mlb` from any Python interpreter at the repo root
5. Make a `git commit` and see ruff-check, ruff-format, and nbstripout fire automatically

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Python version pin, .gitignore, pyproject.toml, requirements files | d37fcf6 | .python-version, .gitignore, pyproject.toml, requirements.txt, requirements-dev.txt |
| 2 | Package skeletons (shared, nfl, nba, mlb) with __init__.py and README stubs | 1476b83 | shared/__init__.py, nfl/__init__.py, nfl/README.md, nba/__init__.py, nba/README.md, mlb/__init__.py, mlb/README.md |
| 3 | .pre-commit-config.yaml with ruff-check, ruff-format, nbstripout hooks | 9c51c51 | .pre-commit-config.yaml |
| 4 | Human verification — complete and close | a014d4d | pyproject.toml, nba-playoffs/notebooks/*.ipynb (10 files) |

## Verification Result

Task 4 (`checkpoint:human-verify`) — **APPROVED** (all 7 steps passed).

Two outcomes recorded during verification:
1. `exclude = ["nba-playoffs/"]` added to `[tool.ruff]` in `pyproject.toml` — prevents ruff from linting pre-existing legacy notebooks outside the scaffold scope.
2. nbstripout hook ran and stripped cell outputs from all 10 nba-playoffs/ notebooks — correct behavior (hook worked as intended).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Config] Added ruff exclude for nba-playoffs/ legacy directory**
- **Found during:** Task 4 (human verification)
- **Issue:** ruff linted nba-playoffs/ notebooks during `pre-commit run --all-files`, producing errors in pre-existing code outside the scaffold scope
- **Fix:** Added `exclude = ["nba-playoffs/"]` to `[tool.ruff]` in pyproject.toml
- **Files modified:** pyproject.toml
- **Commit:** a014d4d

**2. [Rule 1 - Bug] Removed nfl-data-py string from requirements.txt comment**
- **Found during:** Task 1 verification
- **Issue:** The plan's action block included a comment `# NFL data (nflreadpy replaces deprecated nfl-data-py)` which caused the acceptance criteria grep `! grep -q "nfl-data-py" requirements.txt` to fail
- **Fix:** Changed comment to `# NFL data` — the plan's acceptance criteria explicitly prohibit the string nfl-data-py anywhere in requirements.txt
- **Files modified:** requirements.txt
- **Commit:** d37fcf6

### Replaced Existing .gitignore

- **Found during:** Task 1
- **Situation:** A project-specific .gitignore already existed with nba-playoffs/ and nfl-prospect/ data exclusions
- **Action:** Replaced with the plan-specified standard .gitignore per plan instructions. The data paths (nfl/data/, nba/data/, mlb/data/) were already in the original and are now included via pattern matching in the new file indirectly — however the sport-specific data patterns were removed.
- **Note:** The original .gitignore had `nfl/data/`, `nba/data/`, `mlb/data/` which are not in the plan's .gitignore. These will need to be re-added if data directories are created in future phases.

## Known Stubs

- `nba/__init__.py` and `nba/README.md` — NBA stub only; full analyses deferred to v2
- `mlb/__init__.py` and `mlb/README.md` — MLB stub only; full analyses deferred to v2

These are intentional stubs per plan scope (SCAF-01, SCAF-02 deferred to v2).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: supply-chain | requirements.txt | 19 pinned PyPI packages — exact version pins mitigate substitution attacks per T-01-01 |
| threat_flag: hook-bypass | .pre-commit-config.yaml | Pinned revs mitigate T-01-02; `git commit --no-verify` bypass is accepted per T-01-08 |

## Self-Check: PASSED
