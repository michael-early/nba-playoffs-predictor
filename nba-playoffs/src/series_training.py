"""Shared utilities for series model training and backtesting."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"


def add_series_start_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Attach first game date for each historical series if absent."""
    if "series_start_date" in df.columns:
        return df

    seasons = sorted(df["season"].unique())
    games = pd.concat(
        [pd.read_parquet(RAW_DIR / f"playoff_games_{season}.parquet").assign(season=season)
         for season in seasons],
        ignore_index=True,
    )
    games["round"] = games["GAME_ID"].str[6:8].astype(int)
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"])
    home = games[games["MATCHUP"].str.contains(r"vs\.")].copy()
    away = games[games["MATCHUP"].str.contains("@")][["GAME_ID", "TEAM_ID"]].rename(
        columns={"TEAM_ID": "away_team_id"}
    )
    game_df = home.merge(away, on="GAME_ID", how="inner").rename(columns={"TEAM_ID": "home_team_id"})
    game_df["series_key"] = game_df.apply(
        lambda r: (
            f"{r['season']}_{r['round']}_"
            f"{min(r['home_team_id'], r['away_team_id'])}_{max(r['home_team_id'], r['away_team_id'])}"
        ),
        axis=1,
    )
    starts = game_df.groupby("series_key", as_index=False)["GAME_DATE"].min()
    starts = starts.rename(columns={"GAME_DATE": "series_start_date"})
    return df.merge(starts, on="series_key", how="left")
