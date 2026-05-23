"""Tests for shared.cache.load_or_fetch.

Each test passes ``cache_dir=tmp_path`` (or ``isolated_cache``) directly to
``load_or_fetch`` so isolation is explicit and survives any future refactoring
of module-level constants.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

import shared.cache as cache_mod
from shared.cache import load_or_fetch


@pytest.fixture
def isolated_cache(tmp_path: Path) -> Path:
    """Return a temp directory to use as the cache_dir for one test."""
    return tmp_path


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_cache_miss_writes_and_returns(isolated_cache: Path) -> None:
    fetch_fn = Mock(return_value=_sample_df())

    result = load_or_fetch("test_key", fetch_fn, cache_dir=isolated_cache)

    fetch_fn.assert_called_once()
    assert (isolated_cache / "test_key.parquet").exists()
    pd.testing.assert_frame_equal(result, _sample_df())


def test_cache_hit_skips_fetch_fn(isolated_cache: Path) -> None:
    # Prime the cache.
    load_or_fetch("test_key", lambda: _sample_df(), cache_dir=isolated_cache)

    # Second call must not invoke fetch_fn.
    fetch_fn = Mock(
        side_effect=AssertionError("fetch_fn must not be called on cache hit")
    )
    result = load_or_fetch("test_key", fetch_fn, cache_dir=isolated_cache)

    fetch_fn.assert_not_called()
    pd.testing.assert_frame_equal(result, _sample_df())


def test_force_refresh_bypasses_cache(isolated_cache: Path) -> None:
    # Prime cache with v1.
    load_or_fetch(
        "test_key", lambda: pd.DataFrame({"v": [1]}), cache_dir=isolated_cache
    )

    v2 = pd.DataFrame({"v": [2]})
    fetch_fn = Mock(return_value=v2)

    result = load_or_fetch(
        "test_key", fetch_fn, force_refresh=True, cache_dir=isolated_cache
    )

    fetch_fn.assert_called_once()
    pd.testing.assert_frame_equal(result, v2)

    # And the on-disk cache now reflects v2.
    after = load_or_fetch(
        "test_key", lambda: pd.DataFrame({"v": [999]}), cache_dir=isolated_cache
    )
    pd.testing.assert_frame_equal(after, v2)


def test_dtype_round_trip(isolated_cache: Path) -> None:
    original = pd.DataFrame(
        {
            "i": pd.Series([1, 2, 3], dtype="int64"),
            "f": pd.Series([1.5, 2.5, 3.5], dtype="float64"),
            "s": pd.Series(["a", "b", "c"], dtype="object"),
        }
    )
    load_or_fetch("dtype_key", lambda: original, cache_dir=isolated_cache)

    # Second call reads from parquet.
    reread = load_or_fetch(
        "dtype_key", lambda: pd.DataFrame(), cache_dir=isolated_cache
    )

    assert reread["i"].dtype == original["i"].dtype
    assert reread["f"].dtype == original["f"].dtype
    assert reread["s"].dtype == original["s"].dtype


def test_cache_dir_is_repo_root_anchored() -> None:
    # NB: this test does NOT use the isolated_cache fixture — it asserts
    # the unmonkeypatched module-level value.
    expected = Path(cache_mod.__file__).parents[1] / ".cache"
    assert cache_mod.CACHE_DIR == expected


def test_cache_dir_autocreated(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "cache"
    assert not target.exists()

    result = load_or_fetch("autocreate_key", lambda: _sample_df(), cache_dir=target)

    assert target.exists() and target.is_dir()
    assert (target / "autocreate_key.parquet").exists()
    pd.testing.assert_frame_equal(result, _sample_df())


# --- Key validation tests (CR-01 / WR-03) ---


def test_invalid_key_slash_raises() -> None:
    with pytest.raises(ValueError, match="invalid"):
        load_or_fetch("bad/key", lambda: pd.DataFrame())


def test_invalid_key_dotdot_raises() -> None:
    with pytest.raises(ValueError, match="invalid"):
        load_or_fetch("../../etc/passwd", lambda: pd.DataFrame())


# --- fetch_fn return type guard tests (WR-04) ---


def test_fetch_fn_returning_none_raises(isolated_cache: Path) -> None:
    with pytest.raises(TypeError, match="pd.DataFrame"):
        load_or_fetch("bad_fn", lambda: None, cache_dir=isolated_cache)
