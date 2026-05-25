"""Round-by-round playoff prediction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.models import load_model
from src.series_context_features import add_series_context_features

PROJECT_DIR = Path(__file__).parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"

DEFAULT_FEATURE_COLS = [
    "home_ortg", "away_ortg", "home_drtg", "away_drtg",
    "home_net_rtg", "away_net_rtg", "net_rtg_diff",
    "home_pace", "away_pace", "ortg_diff", "drtg_diff",
    "home_win_pct", "away_win_pct", "win_pct_diff",
    "home_oreb_pct", "away_oreb_pct",
    "home_tov_pct", "away_tov_pct",
    "home_playoff_win_pct_3yr", "away_playoff_win_pct_3yr",
    "playoff_win_pct_diff",
    "home_finals_apps_5yr", "away_finals_apps_5yr",
]


@dataclass(frozen=True)
class Team:
    name: str
    team_id: int


class PlayoffPredictor:
    """Predict configured playoff stages, using actual winners when provided."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.pipeline = load_model(config.get("model_name", "series_xgboost"))
        self.feature_cols = self._feature_cols()
        metrics_season = config.get("metrics_season", config["season"])
        self.metrics_season = metrics_season
        self.seed_eff = pd.read_parquet(RAW_DIR / f"team_metrics_{metrics_season}.parquet").set_index("TEAM_ID")
        self.eff = self._apply_team_adjustments(self.seed_eff.copy())
        self.season_stats = self._load_history()
        self._prediction_cache: dict[tuple[str, str], Team] = {}

    def stage_predictions(self, stage_name: str) -> pd.DataFrame:
        rows = []
        stage = self.config["stages"][stage_name]
        for matchup in stage.get("matchups", []):
            higher, lower = self.resolve_matchup(stage_name, matchup["slot"])
            row = self._build_row(higher, lower)
            raw_prob = self._model_probability(row)
            prob, notes = self._adjust_probability(stage_name, matchup["slot"], raw_prob)
            winner = higher if prob >= 0.5 else lower
            actual = self._actual_winner(stage_name, matchup)
            rows.append({
                "stage": stage_name,
                "slot": matchup["slot"],
                "conference": matchup.get("conference", ""),
                "matchup": f"{higher.name} vs {lower.name}",
                "higher_seed": higher.name,
                "lower_seed": lower.name,
                "model_prob_higher_seed": raw_prob,
                "prob_higher_seed": prob,
                "predicted_winner": winner.name,
                "confidence": max(prob, 1 - prob),
                "actual_winner": actual.name if actual else "",
                "adjustment_notes": "; ".join(notes),
            })
        return pd.DataFrame(rows)

    def all_predictions(self) -> dict[str, pd.DataFrame]:
        return {
            stage_name: self.stage_predictions(stage_name)
            for stage_name in self.config["stage_order"]
            if self.config["stages"][stage_name].get("matchups")
        }

    def resolve_matchup(self, stage_name: str, slot: str) -> tuple[Team, Team]:
        stage = self.config["stages"][stage_name]
        matchup = next(m for m in stage["matchups"] if m["slot"] == slot)
        if "higher_seed" in matchup and "lower_seed" in matchup:
            return self._team(matchup["higher_seed"]), self._team(matchup["lower_seed"])

        sources = matchup["source_slots"]
        teams = [self.resolve_winner(src["stage"], src["slot"]) for src in sources]
        return self._order_by_seed(teams[0], teams[1])

    def resolve_winner(self, stage_name: str, slot: str) -> Team:
        key = (stage_name, slot)
        if key in self._prediction_cache:
            return self._prediction_cache[key]

        stage = self.config["stages"][stage_name]
        matchup = next(m for m in stage["matchups"] if m["slot"] == slot)
        actual = self._actual_winner(stage_name, matchup)
        if actual:
            self._prediction_cache[key] = actual
            return actual

        higher, lower = self.resolve_matchup(stage_name, slot)
        row = self._build_row(higher, lower)
        raw_prob = self._model_probability(row)
        prob, _ = self._adjust_probability(stage_name, slot, raw_prob)
        winner = higher if prob >= 0.5 else lower
        self._prediction_cache[key] = winner
        return winner

    def _feature_cols(self) -> list[str]:
        scaler = getattr(self.pipeline, "named_steps", {}).get("scaler")
        learned = getattr(scaler, "feature_names_in_", None)
        return list(learned) if learned is not None else DEFAULT_FEATURE_COLS

    def _load_history(self) -> pd.DataFrame:
        seasons = self.config.get("historical_seasons", ["2021-22", "2022-23", "2023-24"])
        hist_games = pd.concat(
            [pd.read_parquet(RAW_DIR / f"playoff_games_{season}.parquet").assign(season=season)
             for season in seasons],
            ignore_index=True,
        )
        hist_games["round"] = hist_games["GAME_ID"].str[6:8].astype(int)
        hist_games["win"] = (hist_games["WL"] == "W").astype(int)
        hist_games["is_finals"] = (hist_games["round"] == 4).astype(int)
        season_stats = hist_games.groupby(["season", "TEAM_ID"]).agg(
            playoff_wins=("win", "sum"),
            playoff_games=("win", "count"),
            reached_finals=("is_finals", "max"),
        ).reset_index()
        season_stats["playoff_win_pct"] = season_stats["playoff_wins"] / season_stats["playoff_games"]
        season_stats["season_year"] = season_stats["season"].str[:4].astype(int)
        return season_stats

    def _build_row(self, higher: Team, lower: Team) -> dict[str, Any]:
        h = self.eff.loc[higher.team_id]
        a = self.eff.loc[lower.team_id]
        h_hist, h_fin = self._prior_stats(higher.team_id)
        a_hist, a_fin = self._prior_stats(lower.team_id)
        return {
            "matchup": f"{higher.name} vs {lower.name}",
            "home_ortg": h["E_OFF_RATING"],
            "away_ortg": a["E_OFF_RATING"],
            "home_drtg": h["E_DEF_RATING"],
            "away_drtg": a["E_DEF_RATING"],
            "home_net_rtg": h["E_NET_RATING"],
            "away_net_rtg": a["E_NET_RATING"],
            "net_rtg_diff": h["E_NET_RATING"] - a["E_NET_RATING"],
            "home_pace": h["E_PACE"],
            "away_pace": a["E_PACE"],
            "ortg_diff": h["E_OFF_RATING"] - a["E_OFF_RATING"],
            "drtg_diff": h["E_DEF_RATING"] - a["E_DEF_RATING"],
            "home_win_pct": h["W_PCT"],
            "away_win_pct": a["W_PCT"],
            "win_pct_diff": h["W_PCT"] - a["W_PCT"],
            "home_oreb_pct": h["E_OREB_PCT"],
            "away_oreb_pct": a["E_OREB_PCT"],
            "home_tov_pct": h["E_TM_TOV_PCT"],
            "away_tov_pct": a["E_TM_TOV_PCT"],
            "home_playoff_win_pct_3yr": h_hist,
            "away_playoff_win_pct_3yr": a_hist,
            "playoff_win_pct_diff": h_hist - a_hist,
            "home_finals_apps_5yr": h_fin,
            "away_finals_apps_5yr": a_fin,
        }

    def _model_probability(self, row: dict[str, Any]) -> float:
        df = add_series_context_features(pd.DataFrame([row]))
        return float(self.pipeline.predict_proba(df[self.feature_cols])[0, 1])

    def _adjust_probability(self, stage_name: str, slot: str, prob: float) -> tuple[float, list[str]]:
        context = self.config.get("context_adjustments", {})
        notes = []

        shrinkage = float(context.get("probability_shrinkage", 0.0))
        if shrinkage:
            prob = 0.5 + (prob - 0.5) * (1 - shrinkage)
            notes.append(f"shrinkage={shrinkage:.2f}")

        key = f"{stage_name}:{slot}"
        matchup_adj = context.get("matchup_adjustments", {}).get(key, {})
        delta = float(matchup_adj.get("prob_delta", 0.0))
        if delta:
            prob += delta
            reason = matchup_adj.get("reason", "manual matchup adjustment")
            notes.append(f"{reason} ({delta:+.2f})")

        return min(max(prob, 0.01), 0.99), notes

    def _apply_team_adjustments(self, eff: pd.DataFrame) -> pd.DataFrame:
        context = self.config.get("context_adjustments", {})
        adjustments = context.get("team_adjustments", {})
        col_map = {
            "ortg_delta": "E_OFF_RATING",
            "drtg_delta": "E_DEF_RATING",
            "net_rtg_delta": "E_NET_RATING",
            "pace_delta": "E_PACE",
            "win_pct_delta": "W_PCT",
            "oreb_pct_delta": "E_OREB_PCT",
            "tov_pct_delta": "E_TM_TOV_PCT",
        }
        for raw_team_id, deltas in adjustments.items():
            team_id = int(raw_team_id)
            if team_id not in eff.index:
                raise ValueError(f"context adjustment references unknown team_id {team_id}")
            for field, col in col_map.items():
                if field in deltas:
                    eff.at[team_id, col] = eff.at[team_id, col] + float(deltas[field])
        return eff

    def _prior_stats(self, team_id: int) -> tuple[float, int]:
        current_year = int(self.config["season"].split("-")[0])
        hist = self.season_stats[self.season_stats["TEAM_ID"] == team_id]
        p3 = hist[hist["season_year"] >= current_year - 3]
        p5 = hist[hist["season_year"] >= current_year - 5]
        playoff_pct = round(float(p3["playoff_win_pct"].mean()), 3) if len(p3) > 0 else 0.5
        finals = int(p5["reached_finals"].sum())
        return playoff_pct, finals

    def _actual_winner(self, stage_name: str, matchup: dict[str, Any]) -> Team | None:
        winner_id = matchup.get("winner_team_id")
        if winner_id is None:
            return None
        for key in ("higher_seed", "lower_seed"):
            if key in matchup and matchup[key]["team_id"] == winner_id:
                return self._team(matchup[key])
        if "source_slots" in matchup:
            higher, lower = self.resolve_matchup(stage_name, matchup["slot"])
            for team in (higher, lower):
                if team.team_id == winner_id:
                    return team
        raise ValueError(f"winner_team_id {winner_id} is not in matchup {matchup['slot']}")

    def _team(self, payload: dict[str, Any]) -> Team:
        return Team(name=payload["name"], team_id=int(payload["team_id"]))

    def _order_by_seed(self, team_a: Team, team_b: Team) -> tuple[Team, Team]:
        a = self.seed_eff.loc[team_a.team_id]
        b = self.seed_eff.loc[team_b.team_id]
        if (a["W_PCT"], a["E_NET_RATING"]) >= (b["W_PCT"], b["E_NET_RATING"]):
            return team_a, team_b
        return team_b, team_a
