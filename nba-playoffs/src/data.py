"""nba_api fetch helpers with parquet caching."""

from pathlib import Path
import time

import pandas as pd

RAW_DIR = Path(__file__).parents[1] / "data" / "raw"
SLEEP_SEC = 2.0  # courtesy sleep between nba_api calls

# stats.nba.com requires browser-like headers or returns empty responses
_HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer": "https://www.nba.com/",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def fetch_playoff_games(season: str, force: bool = False) -> pd.DataFrame:
    """Return playoff game log for a season (e.g. '2023-24').

    Caches to data/raw/playoff_games_{season}.parquet.
    Uses LeagueGameFinder with season_type_nullable='Playoffs'.
    """
    cache = RAW_DIR / f"playoff_games_{season}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    from nba_api.stats.endpoints import LeagueGameFinder  # noqa: PLC0415

    finder = LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Playoffs",
        league_id_nullable="00",
        headers=_HEADERS,
        timeout=30,
    )
    time.sleep(SLEEP_SEC)
    df = finder.get_data_frames()[0]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def fetch_team_estimated_metrics(season: str, force: bool = False) -> pd.DataFrame:
    """Return team estimated metrics (ORtg, DRtg, net rating, pace) for a season.

    Caches to data/raw/team_metrics_{season}.parquet.
    Uses TeamEstimatedMetrics endpoint.
    """
    cache = RAW_DIR / f"team_metrics_{season}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    from nba_api.stats.endpoints import TeamEstimatedMetrics  # noqa: PLC0415

    endpoint = TeamEstimatedMetrics(season=season, league_id="00", headers=_HEADERS, timeout=30)
    time.sleep(SLEEP_SEC)
    df = endpoint.get_data_frames()[0]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def fetch_team_game_log(team_id: int, season: str, force: bool = False, retries: int = 3) -> pd.DataFrame:
    """Return regular season game log for a team (for rest day calculation).

    Caches to data/raw/team_gamelog_{team_id}_{season}.parquet.
    Uses TeamGameLog endpoint. Retries with exponential backoff on timeout.
    """
    cache = RAW_DIR / f"team_gamelog_{team_id}_{season}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    from nba_api.stats.endpoints import TeamGameLog  # noqa: PLC0415

    for attempt in range(retries):
        try:
            time.sleep(SLEEP_SEC * (2 ** attempt))  # 2s, 4s, 8s
            endpoint = TeamGameLog(
                team_id=team_id,
                season=season,
                season_type_all_star="Regular Season",
                headers=_HEADERS,
                timeout=60,
            )
            df = endpoint.get_data_frames()[0]
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            df.to_parquet(cache, index=False)
            return df
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  Retry {attempt + 1}/{retries} for team {team_id} {season}: {e}")

    raise RuntimeError("unreachable")


def fetch_team_roster(team_id: int, season: str, force: bool = False) -> pd.DataFrame:
    """Return team roster for a season (used to identify top player by minutes).

    Caches to data/raw/roster_{team_id}_{season}.parquet.
    Uses CommonTeamRoster endpoint.
    """
    cache = RAW_DIR / f"roster_{team_id}_{season}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    from nba_api.stats.endpoints import CommonTeamRoster  # noqa: PLC0415

    endpoint = CommonTeamRoster(team_id=team_id, season=season, headers=_HEADERS, timeout=30)
    time.sleep(SLEEP_SEC)
    df = endpoint.get_data_frames()[0]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def fetch_player_season_stats(player_id: int, season: str, force: bool = False) -> pd.DataFrame:
    """Return a player's regular season per-game stats for a given season.

    Caches to data/raw/player_stats_{player_id}_{season}.parquet.
    Uses PlayerCareerStats filtered to the target season.
    """
    cache = RAW_DIR / f"player_stats_{player_id}_{season}.parquet"
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    from nba_api.stats.endpoints import PlayerCareerStats  # noqa: PLC0415

    endpoint = PlayerCareerStats(player_id=player_id, per_mode36="PerGame", headers=_HEADERS, timeout=30)
    time.sleep(SLEEP_SEC)
    df = endpoint.get_data_frames()[0]
    df = df[df["SEASON_ID"] == season]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df
