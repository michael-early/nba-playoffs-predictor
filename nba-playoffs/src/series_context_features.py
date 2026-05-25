"""Derived features for series-level playoff prediction."""

from __future__ import annotations

import pandas as pd

SERIES_BASE_FEATURE_COLS = [
    "home_ortg", "away_ortg", "home_drtg", "away_drtg",
    "home_net_rtg", "away_net_rtg", "net_rtg_diff",
    "home_pace", "away_pace", "ortg_diff", "drtg_diff",
    "home_win_pct", "away_win_pct", "win_pct_diff",
    "home_oreb_pct", "away_oreb_pct",
    "home_tov_pct", "away_tov_pct",
    "home_playoff_win_pct_3yr", "away_playoff_win_pct_3yr", "playoff_win_pct_diff",
    "home_finals_apps_5yr", "away_finals_apps_5yr",
]

SERIES_CONTEXT_FEATURE_COLS = [
    "round",
    "is_first_round",
    "is_conference_semis",
    "is_conference_finals",
    "is_finals",
    "net_rtg_abs_diff",
    "win_pct_abs_diff",
    "pace_diff",
    "pace_abs_diff",
    "tov_pct_diff",
    "oreb_pct_diff",
    "favorite_quality_index",
    "underdog_quality_index",
    "quality_index_diff",
    "underdog_net_rtg",
    "underdog_win_pct",
    "underdog_playoff_win_pct_3yr",
    "underdog_finals_apps_5yr",
    "favorite_turnover_risk",
    "underdog_rebounding_edge",
    "small_gap_series",
    "dangerous_underdog",
    "favorite_overconfidence_risk",
]

SERIES_CONTEXT_MODEL_FEATURE_COLS = SERIES_BASE_FEATURE_COLS + SERIES_CONTEXT_FEATURE_COLS


def add_series_context_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add trainable context proxies using only pre-series information.

    The model treats the higher seed as `home` and lower seed as `away`.
    These features are deliberately computable for both historical and future
    brackets without external player-status data.
    """
    out = df.copy()

    if "round" not in out.columns:
        out["round"] = 0

    out["is_first_round"] = (out["round"] == 1).astype(int)
    out["is_conference_semis"] = (out["round"] == 2).astype(int)
    out["is_conference_finals"] = (out["round"] == 3).astype(int)
    out["is_finals"] = (out["round"] == 4).astype(int)

    out["net_rtg_abs_diff"] = out["net_rtg_diff"].abs()
    out["win_pct_abs_diff"] = out["win_pct_diff"].abs()
    out["pace_diff"] = out["home_pace"] - out["away_pace"]
    out["pace_abs_diff"] = out["pace_diff"].abs()
    out["tov_pct_diff"] = out["home_tov_pct"] - out["away_tov_pct"]
    out["oreb_pct_diff"] = out["home_oreb_pct"] - out["away_oreb_pct"]

    out["favorite_quality_index"] = (
        out["home_net_rtg"] + 20 * out["home_win_pct"] + 2 * out["home_playoff_win_pct_3yr"]
    )
    out["underdog_quality_index"] = (
        out["away_net_rtg"] + 20 * out["away_win_pct"] + 2 * out["away_playoff_win_pct_3yr"]
    )
    out["quality_index_diff"] = out["favorite_quality_index"] - out["underdog_quality_index"]

    out["underdog_net_rtg"] = out["away_net_rtg"]
    out["underdog_win_pct"] = out["away_win_pct"]
    out["underdog_playoff_win_pct_3yr"] = out["away_playoff_win_pct_3yr"]
    out["underdog_finals_apps_5yr"] = out["away_finals_apps_5yr"]

    out["favorite_turnover_risk"] = (out["home_tov_pct"] > out["away_tov_pct"]).astype(int)
    out["underdog_rebounding_edge"] = (out["away_oreb_pct"] > out["home_oreb_pct"]).astype(int)
    out["small_gap_series"] = ((out["net_rtg_abs_diff"] <= 3.0) | (out["win_pct_abs_diff"] <= 0.075)).astype(int)
    out["dangerous_underdog"] = ((out["away_net_rtg"] >= 2.0) | (out["away_win_pct"] >= 0.55)).astype(int)
    out["favorite_overconfidence_risk"] = (
        (out["home_win_pct"] >= 0.65) & (out["away_net_rtg"] >= 0.0)
    ).astype(int)

    return out
