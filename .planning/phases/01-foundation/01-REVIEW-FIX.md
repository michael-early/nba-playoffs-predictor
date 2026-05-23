---
phase: 01-foundation
fixed_at: 2026-05-23T00:00:00Z
review_path: .planning/phases/01-foundation/01-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-23
**Source review:** .planning/phases/01-foundation/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (CR-01, CR-02, WR-01, WR-02, WR-03, WR-04)
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: Path traversal in `load_or_fetch` via unsanitized `key`

**Files modified:** `shared/cache.py`
**Commit:** 72dcbcb
**Applied fix:** Added `_VALID_KEY = re.compile(r"^[A-Za-z0-9_\-]+$")` module-level constant and a guard at the top of `load_or_fetch` that raises `ValueError` with a clear message for any key that does not match the allowlist. Import of `re` added.

---

### CR-02: Partial/corrupt parquet file left on disk when `to_parquet` raises

**Files modified:** `shared/cache.py`
**Commit:** 72dcbcb
**Applied fix:** Replaced `df.to_parquet(cache_path, index=False)` with an atomic tempfile-then-rename pattern using `tempfile.mkstemp` + `os.close` + `df.to_parquet(tmp_path)` + `Path(tmp_path).replace(cache_path)`. A `try/except` block cleans up the temp file and re-raises on any write failure. Imports of `os` and `tempfile` added.

---

### WR-01: `pytest==9.0.3` does not exist on PyPI

**Files modified:** `requirements-dev.txt`
**Commit:** c4d905e
**Applied fix:** Changed `pytest==9.0.3` to `pytest==8.3.5` per the project CLAUDE.md spec (pytest 8.x) and the reviewer's recommended version.

---

### WR-02: `monkeypatch` of `CACHE_DIR` is fragile — breaks silently on refactor

**Files modified:** `shared/cache.py`, `tests/test_cache.py`
**Commit:** 72dcbcb (cache.py), 759447c (test_cache.py)
**Applied fix:** Added `cache_dir: Path = CACHE_DIR` as an explicit keyword-only parameter to `load_or_fetch`. All internal references to `CACHE_DIR` inside the function body replaced with `cache_dir`. Tests updated to pass `cache_dir=isolated_cache` directly; `isolated_cache` fixture simplified to `return tmp_path` with no monkeypatching.

---

### WR-03: No test for key containing a slash

**Files modified:** `tests/test_cache.py`
**Commit:** 759447c
**Applied fix:** Added `test_invalid_key_slash_raises` (tests `"bad/key"`) and `test_invalid_key_dotdot_raises` (tests `"../../etc/passwd"`), both asserting `pytest.raises(ValueError, match="invalid")`. These tests exercise the CR-01 allowlist guard directly.

---

### WR-04: No guard on `fetch_fn` return type

**Files modified:** `shared/cache.py`, `tests/test_cache.py`
**Commit:** 72dcbcb (cache.py), 759447c (test_cache.py)
**Applied fix:** Added `isinstance(df, pd.DataFrame)` check immediately after `df = fetch_fn()`, raising `TypeError` with `"fetch_fn must return a pd.DataFrame, got {type(df).__name__!r}"` on failure. Added `test_fetch_fn_returning_none_raises` in the test file asserting `TypeError` is raised when `fetch_fn` returns `None`.

---

## Skipped Issues

None — all findings were fixed.

---

_Fixed: 2026-05-23_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
