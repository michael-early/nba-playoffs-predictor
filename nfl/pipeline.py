#!/usr/bin/env python3
"""nfl/pipeline.py — Build NFL Combine + Career Stats joined parquet.

This dataset covers only players invited to the NFL Combine. Players who were
neither drafted nor invited to the combine are not represented. 'Not-invited'
prospects cannot be reconstructed from this data source.

Use ``--force-refresh`` to bypass the on-disk cache and re-fetch from nflreadpy.
The cache artifact at ``.cache/nfl_combine_pipeline_2000_2023.parquet`` is the
integration contract for the EDA notebook (Plan 02) and Phase 3 analyses.
"""
from __future__ import annotations

import argparse

import nflreadpy as nfl
import pandas as pd
import polars as pl

from shared.cache import load_or_fetch

# ---------------------------------------------------------------------------
# Constants — change these to adjust the season window; cache key auto-updates.
# ---------------------------------------------------------------------------

START_SEASON: int = 2000
END_SEASON: int = 2023
SEASONS: list[int] = list(range(START_SEASON, END_SEASON + 1))
CACHE_KEY: str = f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"

# 22 verified raw pos values → 7 standard NFL groups.
# Specialists (K/P/LS) and any unknown values map to "Other".
POSITION_GROUP_MAP: dict[str, str] = {
    "QB": "QB",
    "RB": "RB",
    "FB": "RB",
    "WR": "WR/TE",
    "TE": "WR/TE",
    "OT": "OL",
    "OG": "OL",
    "C": "OL",
    "OL": "OL",
    "DE": "DL",
    "DT": "DL",
    "DL": "DL",
    "EDGE": "DL",
    "OLB": "LB",
    "ILB": "LB",
    "LB": "LB",
    "CB": "DB",
    "S": "DB",
    "DB": "DB",
}


# ---------------------------------------------------------------------------
# Core dataset builder (called by load_or_fetch on cache miss only)
# ---------------------------------------------------------------------------


def _build_dataset() -> pd.DataFrame:
    """Fetch combine + draft picks, join, add derived columns, return pandas DataFrame.

    Called by load_or_fetch on cache miss only.
    """
    print("Fetching combine data...", end=" ", flush=True)
    combine = nfl.load_combine(SEASONS)
    print(f"done ({len(combine)} rows)")

    # Open Question 1 (RESEARCH.md): count drafted rows with null pfr_id before join.
    n_drafted_null_pfr = combine.filter(
        pl.col("draft_round").is_not_null() & pl.col("pfr_id").is_null()
    ).height
    print(f"note: {n_drafted_null_pfr} drafted rows have null pfr_id")

    print("Fetching draft picks (career stats)...", end=" ", flush=True)
    picks = nfl.load_draft_picks(SEASONS)
    # Select only the columns needed; car_av is 100% null — do not use (Pitfall 1).
    picks_slim = picks.select(
        ["pfr_player_id", "w_av", "allpro", "probowls", "dr_av", "hof"]
    )
    print(f"done ({len(picks_slim)} rows)")

    print("Joining...", end=" ", flush=True)
    joined = combine.join(
        picks_slim,
        left_on="pfr_id",
        right_on="pfr_player_id",
        how="left",
    ).with_columns(
        [
            pl.col("pos")
            .replace_strict(POSITION_GROUP_MAP, default="Other")
            .alias("position_group"),
            pl.when(pl.col("draft_round").is_not_null())
            .then(pl.lit("drafted"))
            .otherwise(pl.lit("undrafted"))
            .alias("sample_membership"),
        ]
    )

    df = joined.to_pandas()
    print(f"done — final shape {df.shape[0]}x{df.shape[1]}")
    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass cache and re-fetch from nflreadpy.",
    )
    args = parser.parse_args()

    df = load_or_fetch(CACHE_KEY, _build_dataset, force_refresh=args.force_refresh)
    print(f"Dataset ready: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Cached to .cache/{CACHE_KEY}.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
