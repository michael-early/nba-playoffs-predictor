"""Model training, evaluation, and serialization helpers."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODELS_DIR = Path(__file__).parents[1] / "models"

FEATURE_COLS = [
    # Group 1 — team efficiency
    "home_ortg", "away_ortg", "home_drtg", "away_drtg",
    "home_net_rtg", "away_net_rtg", "home_pace", "away_pace",
    "ortg_diff", "drtg_diff",
    # Group 2 — team quality proxies
    "home_win_pct", "away_win_pct", "home_oreb_pct", "away_oreb_pct",
    # Group 3 — game context
    "home_rest_days", "away_rest_days", "rest_advantage",
    "game_number", "is_elimination_game",
    # Group 4 — historical playoff record
    "home_playoff_win_pct_3yr", "away_playoff_win_pct_3yr",
    "home_finals_apps_5yr", "away_finals_apps_5yr",
    # Group 5 — in-series momentum
    "home_series_wins", "away_series_wins",
    "last_game_margin", "cumulative_pts_diff", "home_won_last_game",
]
TARGET_COL = "home_win"


def train_test_split_by_season(
    df: pd.DataFrame,
    test_seasons: list[str],
    season_col: str = "season",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into train/test by season (temporal split, no leakage).

    test_seasons: e.g. ['2022-23', '2023-24']
    Returns (train_df, test_df).
    """
    test_mask = df[season_col].isin(test_seasons)
    return df[~test_mask].copy(), df[test_mask].copy()


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Return accuracy, ROC-AUC, log loss, and Brier score for a fitted model.

    model must implement predict() and predict_proba().
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "log_loss": round(log_loss(y_test, y_prob), 4),
        "brier_score": round(brier_score_loss(y_test, y_prob), 4),
    }


def cross_validate_temporal(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    scoring: str = "roc_auc",
) -> np.ndarray:
    """Run TimeSeriesSplit cross-validation and return per-fold scores.

    Uses TimeSeriesSplit to respect temporal order (no future leakage).
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    return cross_val_score(model, X, y, cv=tscv, scoring=scoring)


def save_model(model, name: str) -> Path:
    """Serialize a fitted model to models/{name}.joblib and return the path."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    return path


def load_model(name: str):
    """Load and return a serialized model from models/{name}.joblib."""
    path = MODELS_DIR / f"{name}.joblib"
    return joblib.load(path)


def build_logistic_pipeline() -> Pipeline:
    """Return an unfitted sklearn Pipeline: StandardScaler + LogisticRegression."""
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415

    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def build_random_forest_pipeline() -> Pipeline:
    """Return an unfitted sklearn Pipeline: StandardScaler + RandomForestClassifier."""
    from sklearn.ensemble import RandomForestClassifier  # noqa: PLC0415

    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)),
    ])


def build_xgboost_pipeline() -> Pipeline:
    """Return an unfitted sklearn Pipeline: StandardScaler + XGBClassifier."""
    from xgboost import XGBClassifier  # noqa: PLC0415

    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
            eval_metric="logloss",
        )),
    ])


def compare_models(results: dict[str, dict]) -> pd.DataFrame:
    """Format a dict of {model_name: metrics_dict} into a sorted comparison DataFrame.

    Sorted by ROC-AUC descending.
    """
    df = pd.DataFrame(results).T
    df.index.name = "model"
    return df.sort_values("roc_auc", ascending=False)
