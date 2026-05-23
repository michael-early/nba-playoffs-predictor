"""Disk-backed parquet cache for sport-specific data fetches.

Public API:
    load_or_fetch(key, fetch_fn, force_refresh=False) -> pd.DataFrame

All fetches across nfl/, nba/, mlb/ go through this single utility so that
repeat runs of any notebook do not re-hit remote APIs.
"""
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
        key: Cache key; no slashes. Maps to ``.cache/{key}.parquet``.
        fetch_fn: Zero-argument callable that returns a DataFrame.
        force_refresh: If True, bypass cache and re-fetch even if file exists.

    Returns:
        DataFrame loaded from cache or freshly fetched.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{key}.parquet"

    if not force_refresh and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = fetch_fn()
    df.to_parquet(cache_path, index=False)
    return df
