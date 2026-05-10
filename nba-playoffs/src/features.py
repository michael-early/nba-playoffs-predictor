"""Feature engineering functions for the NBA playoffs prediction pipeline."""

import pandas as pd
import numpy as np


def compute_rest_days(game_date: pd.Timestamp, team_game_log: pd.DataFrame) -> int:
    """Return number of rest days before game_date for a team (capped at 7).

    team_game_log must have a GAME_DATE column (string 'MMM DD, YYYY' or datetime).
    Returns 7 if no prior game found in the log.
    """
    dates = pd.to_datetime(team_game_log["GAME_DATE"], format="mixed", dayfirst=False)
    prior = dates[dates < game_date]
    if prior.empty:
        return 7
    return min(int((game_date - prior.max()).days), 7)


def add_rest_days_from_playoff_log(games: pd.DataFrame) -> pd.DataFrame:
    """Add rest_days column to a playoff game log using only playoff game dates.

    games must have TEAM_ID, GAME_DATE (string YYYY-MM-DD), season, GAME_ID columns.
    Each row is one team in one game.

    Returns games with a new 'rest_days' column (int, capped at 7).
    First game of the playoffs per team per season gets 7 (typical week off after regular season).
    """
    df = games.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["season", "TEAM_ID", "GAME_DATE"]).reset_index(drop=True)

    df["prev_game_date"] = df.groupby(["season", "TEAM_ID"])["GAME_DATE"].shift(1)
    df["rest_days"] = (df["GAME_DATE"] - df["prev_game_date"]).dt.days
    df["rest_days"] = df["rest_days"].fillna(7).clip(upper=7).astype(int)

    return df


def build_efficiency_features(
    home_team_id: int,
    away_team_id: int,
    team_metrics: pd.DataFrame,
) -> dict:
    """Extract Group 1 efficiency features (ORtg, DRtg, net rating, pace) for both teams.

    team_metrics: DataFrame from fetch_team_estimated_metrics with columns
    TEAM_ID, E_OFF_RATING, E_DEF_RATING, E_NET_RATING, E_PACE.

    Returns dict with home_ortg, away_ortg, home_drtg, away_drtg,
    home_net_rtg, away_net_rtg, home_pace, away_pace, ortg_diff, drtg_diff.
    Raises KeyError if team not found.
    """
    home = team_metrics[team_metrics["TEAM_ID"] == home_team_id].iloc[0]
    away = team_metrics[team_metrics["TEAM_ID"] == away_team_id].iloc[0]

    return {
        "home_ortg": home["E_OFF_RATING"],
        "away_ortg": away["E_OFF_RATING"],
        "home_drtg": home["E_DEF_RATING"],
        "away_drtg": away["E_DEF_RATING"],
        "home_net_rtg": home["E_NET_RATING"],
        "away_net_rtg": away["E_NET_RATING"],
        "home_pace": home["E_PACE"],
        "away_pace": away["E_PACE"],
        "ortg_diff": home["E_OFF_RATING"] - away["E_OFF_RATING"],
        "drtg_diff": home["E_DEF_RATING"] - away["E_DEF_RATING"],
    }


def build_star_player_features(
    home_team_id: int,
    away_team_id: int,
    player_stats_lookup: dict,
) -> dict:
    """Extract Group 2 star player features (top player by minutes, PPG + plus/minus).

    player_stats_lookup: {team_id: DataFrame} where each DataFrame has PTS, PLUS_MINUS, MIN
    for each player on the roster for the season.

    Returns dict with home_star_pts_avg, away_star_pts_avg,
    home_star_plus_minus, away_star_plus_minus.
    Returns NaN for a team if no player data found.
    """

    def _top_player_stats(team_id: int) -> tuple[float, float]:
        df = player_stats_lookup.get(team_id)
        if df is None or df.empty:
            return np.nan, np.nan
        top = df.sort_values("MIN", ascending=False).iloc[0]
        return float(top.get("PTS", np.nan)), float(top.get("PLUS_MINUS", np.nan))

    home_pts, home_pm = _top_player_stats(home_team_id)
    away_pts, away_pm = _top_player_stats(away_team_id)

    return {
        "home_star_pts_avg": home_pts,
        "away_star_pts_avg": away_pts,
        "home_star_plus_minus": home_pm,
        "away_star_plus_minus": away_pm,
    }


def build_context_features(
    home_rest: int,
    away_rest: int,
    game_number: int,
    series_home_wins: int,
    series_away_wins: int,
) -> dict:
    """Compute Group 3 game context features.

    game_number: 1-indexed game number within the series.
    series_home_wins / series_away_wins: wins so far (not including this game).

    Returns dict with home_rest_days, away_rest_days, rest_advantage,
    game_number, is_elimination_game.
    """
    home_at_risk = series_home_wins == 3
    away_at_risk = series_away_wins == 3
    is_elim = int(home_at_risk or away_at_risk)

    return {
        "home_rest_days": home_rest,
        "away_rest_days": away_rest,
        "rest_advantage": home_rest - away_rest,
        "game_number": game_number,
        "is_elimination_game": is_elim,
    }


def build_historical_features(
    home_team_id: int,
    away_team_id: int,
    current_season: str,
    historical_game_log: pd.DataFrame,
) -> dict:
    """Compute Group 4 historical playoff record features.

    historical_game_log: all playoff game rows for all prior seasons,
    columns: TEAM_ID, WL, SEASON_ID, MATCHUP (contains 'vs.' for home games).

    Computes win % over prior 3 seasons and Finals appearances in prior 5 seasons.
    Returns NaN if no historical data found.
    """

    def _prior_seasons(current: str, n: int) -> list[str]:
        year = int(current.split("-")[0])
        return [f"{y}-{str(y + 1)[-2:]}" for y in range(year - n, year)]

    def _playoff_win_pct(team_id: int, seasons: list[str]) -> float:
        mask = (historical_game_log["TEAM_ID"] == team_id) & (
            historical_game_log["SEASON_ID"].isin(seasons)
        )
        sub = historical_game_log[mask]
        if sub.empty:
            return np.nan
        return float((sub["WL"] == "W").sum() / len(sub))

    def _finals_apps(team_id: int, seasons: list[str]) -> int:
        mask = (historical_game_log["TEAM_ID"] == team_id) & (
            historical_game_log["SEASON_ID"].isin(seasons)
        )
        sub = historical_game_log[mask]
        if sub.empty:
            return 0
        finals = sub[sub["MATCHUP"].str.contains("Finals", na=False)]
        return int(finals["SEASON_ID"].nunique())

    prior_3 = _prior_seasons(current_season, 3)
    prior_5 = _prior_seasons(current_season, 5)

    return {
        "home_playoff_win_pct_3yr": _playoff_win_pct(home_team_id, prior_3),
        "away_playoff_win_pct_3yr": _playoff_win_pct(away_team_id, prior_3),
        "home_finals_apps_5yr": _finals_apps(home_team_id, prior_5),
        "away_finals_apps_5yr": _finals_apps(away_team_id, prior_5),
    }


def build_feature_matrix(game_rows: list[dict]) -> pd.DataFrame:
    """Assemble list of per-game feature dicts into a clean DataFrame.

    Drops rows with target variable missing.
    Returns DataFrame with all 23 features + target + metadata columns.
    """
    df = pd.DataFrame(game_rows)
    df = df.dropna(subset=["home_win"])
    df["home_win"] = df["home_win"].astype(int)
    return df.reset_index(drop=True)
