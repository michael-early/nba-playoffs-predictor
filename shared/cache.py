"""Disk-backed parquet cache for sport-specific data fetches.

Public API:
    load_or_fetch(key, fetch_fn, force_refresh=False) -> pd.DataFrame

All fetches across nfl/, nba/, mlb/ go through this single utility so that
repeat runs of any notebook do not re-hit remote APIs.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).parents[1] / ".cache"

_VALID_KEY = re.compile(r"^[A-Za-z0-9_\-]+$")


def load_or_fetch(
    key: str,
    fetch_fn: Callable[[], pd.DataFrame],
    force_refresh: bool = False,
    *,
    cache_dir: Path = CACHE_DIR,
) -> pd.DataFrame:
    """Return cached DataFrame or call fetch_fn and cache the result.

    Args:
        key: Cache key; only ``[A-Za-z0-9_-]`` characters allowed.
            Maps to ``{cache_dir}/{key}.parquet``.
        fetch_fn: Zero-argument callable that returns a DataFrame.
        force_refresh: If True, bypass cache and re-fetch even if file exists.
        cache_dir: Directory used for cache storage. Defaults to the
            repo-root ``.cache/`` directory. Callers (and tests) can pass an
            explicit path to avoid relying on module-level monkeypatching.

    Returns:
        DataFrame loaded from cache or freshly fetched.

    Raises:
        ValueError: If ``key`` contains characters outside ``[A-Za-z0-9_-]``.
        TypeError: If ``fetch_fn`` does not return a ``pd.DataFrame``.
    """
    if not _VALID_KEY.match(key):
        raise ValueError(f"Cache key {key!r} is invalid. Use only [A-Za-z0-9_-].")

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{key}.parquet"

    if not force_refresh and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = fetch_fn()
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"fetch_fn must return a pd.DataFrame, got {type(df).__name__!r}"
        )

    tmp_fd, tmp_path = tempfile.mkstemp(dir=cache_dir, suffix=".parquet.tmp")
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
