# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-29
**Phase:** 1-Foundation
**Areas discussed:** Venv scope, Cache key design, Python tooling, Ruff config

---

## Venv scope

| Option | Description | Selected |
|--------|-------------|----------|
| Shared top-level .venv | All sports use one env; single pip install; simpler onboarding | ✓ |
| Sport-specific .venvs | Isolated per-sport envs; more overhead; pays off if deps diverge heavily | |

**User's choice:** Shared top-level .venv

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pin with .python-version | Works with pyenv/uv; eliminates version drift | ✓ |
| Just require 3.10+ in README | Simpler; slight risk of version drift | |

**User's choice:** Pin with .python-version

---

## Cache key design

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit string key | Caller passes key; readable; predictable path | ✓ |
| Auto-derived from function + args | No key needed; hash collisions possible; opaque paths | |
| File-path-based | Maximum control; more verbose | |

**User's choice:** Explicit string key

---

| Option | Description | Selected |
|--------|-------------|----------|
| .cache/ at repo root | Single gitignored dir; easy to nuke | ✓ |
| data/ per sport folder | Co-located; requires sport-context awareness in cache module | |

**User's choice:** .cache/ at repo root

---

| Option | Description | Selected |
|--------|-------------|----------|
| force_refresh=False default | Programmatic cache bust without deleting files | ✓ |
| No force_refresh — delete file to refresh | Simpler API; less ergonomic mid-research | |

**User's choice:** force_refresh=False default

---

## Python tooling

| Option | Description | Selected |
|--------|-------------|----------|
| uv + requirements.txt | 10-100x faster venv; pip install still works as user command | ✓ |
| Pure pip + requirements.txt | No new tooling; slower; universally familiar | |

**User's choice:** uv + requirements.txt

---

| Option | Description | Selected |
|--------|-------------|----------|
| Split requirements.txt + requirements-dev.txt | Researchers only need runtime deps to run notebooks | ✓ |
| Single requirements.txt | Simpler; fine for a research repo | |

**User's choice:** Split requirements.txt + requirements-dev.txt

---

## Ruff config

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit rules in pyproject.toml | E/W/F/I rules + line-length 88; catches real issues | ✓ |
| ruff.toml with same rules | Same rules; separate file | |
| Zero config / defaults | F only; misses style/import issues | |

**User's choice:** Explicit rules in pyproject.toml

---

| Option | Description | Selected |
|--------|-------------|----------|
| ruff format as formatter | One tool for lint + format; pre-commit runs both | ✓ |
| ruff check only | Lint only; no auto-formatting | |

**User's choice:** ruff format as formatter

---

## Claude's Discretion

- Pre-commit hook ordering (ruff vs nbstripout order)
- Exact Python 3.11.x patch version for .python-version
- Whether pyproject.toml includes a [project] metadata section or just [tool.ruff]

## Deferred Ideas

None.
