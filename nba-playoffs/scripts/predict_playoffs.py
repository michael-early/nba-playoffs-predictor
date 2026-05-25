#!/usr/bin/env python3
"""Run round-by-round NBA playoff predictions from a JSON playoff state file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.playoff_predictions import PlayoffPredictor  # noqa: E402


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def save_config(path: Path, config: dict) -> None:
    with path.open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def record_result(config: dict, stage_name: str, slot: str, team_id: int) -> None:
    stage = config["stages"][stage_name]
    for matchup in stage["matchups"]:
        if matchup["slot"] == slot:
            matchup["winner_team_id"] = team_id
            return
    raise ValueError(f"Unknown slot {slot!r} in stage {stage_name!r}")


def print_predictions(label: str, df: pd.DataFrame) -> None:
    print(f"\n=== {label} ===")
    if df.empty:
        print("No matchups configured for this stage.")
        return
    for _, row in df.iterrows():
        actual = f" | actual: {row.actual_winner}" if row.actual_winner else ""
        raw = ""
        if "model_prob_higher_seed" in df.columns:
            raw_prob = float(row.model_prob_higher_seed)
            adj_prob = float(row.prob_higher_seed)
            if abs(raw_prob - adj_prob) >= 0.005:
                raw = f"; raw {raw_prob:.0%}"
        notes = f" | adj: {row.adjustment_notes}" if row.adjustment_notes else ""
        print(
            f"{row.slot}: {row.matchup} -> {row.predicted_winner} "
            f"({row.confidence:.0%} confidence; P higher seed {row.prob_higher_seed:.0%}{raw})"
            f"{actual}{notes}"
        )


def write_outputs(
    out_dir: Path,
    season: str,
    stage_name: str,
    label: str,
    df: pd.DataFrame,
    plot: bool = False,
) -> None:
    if df.empty:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{season}_{stage_name}_predictions.csv"
    df.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}")

    if not plot:
        return

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    png_path = out_dir / f"{season}_{stage_name}_predictions.png"

    fig, ax = plt.subplots(figsize=(10, max(3.5, len(df) * 0.65 + 1.5)))
    colors = ["steelblue" if p >= 0.5 else "coral" for p in df["prob_higher_seed"]]
    ax.barh(df["matchup"], df["prob_higher_seed"], color=colors, alpha=0.85)
    ax.axvline(0.5, color="black", linewidth=1.1, linestyle="--")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Probability higher seed wins series")
    ax.set_title(f"{season} NBA Playoffs - {label}")
    for idx, row in df.iterrows():
        offset = 0.01 if row.prob_higher_seed < 0.88 else -0.01
        ha = "left" if row.prob_higher_seed < 0.88 else "right"
        ax.text(
            row.prob_higher_seed + offset,
            idx,
            f"{row.prob_higher_seed:.0%}  {row.predicted_winner}",
            va="center",
            ha=ha,
            fontsize=9,
        )
    ax.legend(
        handles=[
            mpatches.Patch(color="steelblue", alpha=0.85, label="Higher seed predicted"),
            mpatches.Patch(color="coral", alpha=0.85, label="Upset predicted"),
        ],
        loc="lower right",
        fontsize=8,
    )
    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {png_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_DIR / "config" / "playoffs_2025-26.json",
        help="Path to playoff state JSON.",
    )
    parser.add_argument(
        "--stage",
        help="Stage to predict. Stage names from the config are also accepted.",
    )
    parser.add_argument(
        "--record-result",
        nargs=3,
        metavar=("STAGE", "SLOT", "TEAM_ID"),
        help="Update winner_team_id for a completed matchup, then save the config.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_DIR / "outputs" / "predictions",
        help="Directory for CSV and PNG outputs.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Also write a PNG chart. Text and CSV output are always generated.",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.record_result:
        stage_name, slot, team_id = args.record_result
        record_result(config, stage_name, slot, int(team_id))
        save_config(args.config, config)
        print(f"Recorded {team_id} as winner for {stage_name}/{slot} in {args.config}")
        if not args.stage:
            return 0

    predictor = PlayoffPredictor(config)
    stage_order = config["stage_order"]

    if args.stage == "all":
        stages = stage_order
    elif args.stage == "next" or args.stage is None:
        stages = [
            name for name in stage_order
            if any(m.get("winner_team_id") is None for m in config["stages"][name].get("matchups", []))
        ][:1]
    else:
        if args.stage not in config["stages"]:
            raise ValueError(f"Unknown stage {args.stage!r}. Valid stages: {', '.join(stage_order)}")
        stages = [args.stage]

    for stage_name in stages:
        stage = config["stages"][stage_name]
        df = predictor.stage_predictions(stage_name)
        print_predictions(stage["label"], df)
        write_outputs(args.out_dir, config["season"], stage_name, stage["label"], df, plot=args.plot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
