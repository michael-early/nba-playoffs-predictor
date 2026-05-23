---
phase: 01-foundation
reviewed: 2026-05-23T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - .pre-commit-config.yaml
  - .python-version
  - mlb/__init__.py
  - mlb/README.md
  - nba/__init__.py
  - nba/README.md
  - nfl/__init__.py
  - nfl/README.md
  - pyproject.toml
  - requirements-dev.txt
  - requirements.txt
  - shared/__init__.py
  - shared/cache.py
  - tests/__init__.py
  - tests/test_cache.py
findings:
  critical: 2
  warning: 4
  info: 1
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-23
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

The foundation scaffold is small and mostly correct. The critical issues are both in `shared/cache.py`: a path-traversal vulnerability via unsanitized cache keys, and a corrupted-cache scenario where a failed write leaves a partial parquet file that subsequent reads will error on. The test suite covers the happy paths well but misses both of those failure modes, plus the key-contains-slash edge case that the docstring explicitly warns against. Requirements pinning is solid but `pytest==9.0.3` does not exist, which will break `pip install -r requirements-dev.txt` for any new contributor.

---

## Critical Issues

### CR-01: Path traversal in `load_or_fetch` via unsanitized `key`

**File:** `shared/cache.py:35`

**Issue:** `cache_path = CACHE_DIR / f"{key}.parquet"` performs no validation on `key`. A caller passing `key="../../etc/passwd"` (or any string containing `..` or an absolute `/` prefix) will write or read outside `.cache/`. The docstring says "no slashes" but that is an undocumented convention with zero enforcement. Any future notebook author who forgets (or any upstream value that smuggles a slash) silently escapes the cache directory.

**Fix:**
```python
import re

_VALID_KEY = re.compile(r'^[A-Za-z0-9_\-]+$')

def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
) -> pd.DataFrame:
    if not _VALID_KEY.match(key):
        raise ValueError(
            f"Cache key {key!r} is invalid. Use only [A-Za-z0-9_-]."
        )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{key}.parquet"
    # ... rest unchanged
```

Reject at the call site rather than silently allowing path escape.

---

### CR-02: Partial/corrupt parquet file left on disk when `fetch_fn` succeeds but `to_parquet` raises

**File:** `shared/cache.py:40-42`

**Issue:** If `df.to_parquet(cache_path, index=False)` raises mid-write (disk full, permission error, KeyboardInterrupt) the file at `cache_path` is left in a truncated/corrupt state. The next call finds `cache_path.exists() == True` and calls `pd.read_parquet(cache_path)`, which raises an ArrowInvalid or similar exception — the fetch function is never retried and the data is inaccessible until the user manually deletes the corrupt file.

**Fix:** Write to a temp file and atomically rename, which is the standard pattern for safe cache writes:

```python
import tempfile
import os

def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{key}.parquet"

    if not force_refresh and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = fetch_fn()

    tmp_fd, tmp_path = tempfile.mkstemp(dir=CACHE_DIR, suffix=".parquet.tmp")
    try:
        os.close(tmp_fd)
        df.to_parquet(tmp_path, index=False)
        Path(tmp_path).replace(cache_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return df
```

---

## Warnings

### WR-01: `pytest==9.0.3` does not exist — `requirements-dev.txt` will fail to install

**File:** `requirements-dev.txt:5`

**Issue:** The latest pytest release as of May 2026 is in the 8.x line (`pytest==8.x`). `9.0.3` does not exist on PyPI. `pip install -r requirements-dev.txt` will fail with a `ResolutionImpossible` error for any new contributor setting up the project.

**Fix:** Pin to the actual latest stable release: `pytest==8.3.5` (verify against PyPI before committing). The project CLAUDE.md recommends `pytest 8.x`.

---

### WR-02: `monkeypatch` of `CACHE_DIR` does not isolate `load_or_fetch` — the module-level constant is captured correctly but the fix only works because of Python name resolution

**File:** `tests/test_cache.py:21`

**Issue:** `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` works here because `load_or_fetch` references `CACHE_DIR` as a global lookup at call time, not as a closure over a local binding. This is currently correct, but is a fragile implicit contract: if `cache.py` is ever refactored to pass `CACHE_DIR` as a default argument (e.g., `def load_or_fetch(..., cache_dir=CACHE_DIR)`) the monkeypatch silently stops working and tests continue to pass while writing to the real `.cache/` directory. The test suite provides no safety net for that refactor.

**Fix:** Add a `cache_dir` parameter to `load_or_fetch` (defaulting to `CACHE_DIR`) and pass it explicitly in tests. This makes the isolation explicit and survives refactoring:

```python
def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
    *,
    cache_dir: Path = CACHE_DIR,
) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{key}.parquet"
    ...
```

Tests then pass `cache_dir=tmp_path` directly — no monkeypatching needed.

---

### WR-03: No test for key containing a slash (the documented constraint has no enforcement test)

**File:** `tests/test_cache.py`

**Issue:** The `load_or_fetch` docstring says "no slashes" but there is no test that verifies a key like `"nfl/combine_2023"` raises an error — because right now it does not raise; it silently path-traverses (CR-01). Once CR-01 is fixed with a validator, a test asserting `pytest.raises(ValueError)` for slash-containing keys must accompany it. Currently neither the guard nor the test exists.

**Fix:** After implementing CR-01's key validation, add:

```python
def test_invalid_key_raises() -> None:
    with pytest.raises(ValueError, match="invalid"):
        load_or_fetch("bad/key", lambda: pd.DataFrame())

def test_invalid_key_dotdot_raises() -> None:
    with pytest.raises(ValueError, match="invalid"):
        load_or_fetch("../../etc/passwd", lambda: pd.DataFrame())
```

---

### WR-04: `fetch_fn` failure leaves no cache file but also returns no useful error context

**File:** `shared/cache.py:40`

**Issue:** If `fetch_fn()` raises an exception, it propagates to the caller raw — which is fine. However, there is no test covering this path. More importantly, `df = fetch_fn()` has no type guard: if a future `fetch_fn` returns `None` (e.g., a poorly-implemented API wrapper that returns `None` on rate-limit), the code proceeds to `None.to_parquet(...)` and raises `AttributeError`, giving the caller no indication that `fetch_fn` was the problem.

**Fix:** Add a guard immediately after the fetch:

```python
df = fetch_fn()
if not isinstance(df, pd.DataFrame):
    raise TypeError(
        f"fetch_fn must return a pd.DataFrame, got {type(df).__name__!r}"
    )
```

Add a corresponding test:

```python
def test_fetch_fn_returning_none_raises(isolated_cache: Path) -> None:
    with pytest.raises(TypeError, match="pd.DataFrame"):
        load_or_fetch("bad_fn", lambda: None)
```

---

## Info

### IN-01: `ruff==0.15.12` version in pre-commit and requirements is ahead of public stable releases

**File:** `.pre-commit-config.yaml:3`, `requirements-dev.txt:2`

**Issue:** Both files pin `ruff` at `0.15.12`. Ruff's public versioning as of August 2025 training data reached the `0.9.x` range. A `0.15.x` version either post-dates the knowledge cutoff or is an invented version number. If it is a real future version, this is fine — but if the version does not exist on PyPI, installation will fail silently in CI environments that pull from PyPI. The pre-commit `rev: v0.15.12` points to a GitHub tag that must exist in `astral-sh/ruff-pre-commit`.

**Fix:** Verify `ruff==0.15.12` resolves on PyPI (`pip index versions ruff`) and that the pre-commit tag `v0.15.12` exists at `https://github.com/astral-sh/ruff-pre-commit/releases`. If this is a future version already installed in the project venv, ensure `requirements-dev.txt` and the pre-commit rev are kept in sync (they currently are — both at `0.15.12` — which is correct).

---

_Reviewed: 2026-05-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
