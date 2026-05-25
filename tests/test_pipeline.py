"""Tests for nfl/pipeline.py.

Covers: position mapping, sample membership, CLI cache integration.
"""
from __future__ import annotations

import sys

import pandas as pd
import polars as pl
import pytest

from nfl import pipeline as pipeline_mod
from nfl.pipeline import (
    CACHE_KEY,
    END_SEASON,
    POSITION_GROUP_MAP,
    START_SEASON,
)
from shared.cache import load_or_fetch

EXPECTED_MAPPING = {
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


def test_position_group_map_covers_all_documented_positions() -> None:
    for raw, expected in EXPECTED_MAPPING.items():
        assert POSITION_GROUP_MAP.get(raw) == expected, raw


def test_position_group_map_default_for_specialists() -> None:
    s = pl.Series("pos", ["K", "P", "LS", "QB"])
    out = s.replace_strict(POSITION_GROUP_MAP, default="Other").to_list()
    assert out == ["Other", "Other", "Other", "QB"]


def test_cache_key_format_is_parameterized() -> None:
    assert CACHE_KEY == f"nfl_combine_pipeline_{START_SEASON}_{END_SEASON}"
    assert CACHE_KEY == "nfl_combine_pipeline_2000_2023"


def test_main_uses_load_or_fetch_and_hits_cache_second_call(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_df = pd.DataFrame(
        {
            "pfr_id": ["A"],
            "w_av": [10],
            "sample_membership": ["drafted"],
            "position_group": ["QB"],
        }
    )
    call_count = {"n": 0}

    def fake_build() -> pd.DataFrame:
        call_count["n"] += 1
        return fake_df

    monkeypatch.setattr(pipeline_mod, "_build_dataset", fake_build)

    # Route load_or_fetch through an isolated cache_dir
    def wrapped_load(key: str, fn, force_refresh: bool = False) -> pd.DataFrame:
        return load_or_fetch(key, fn, force_refresh=force_refresh, cache_dir=tmp_path)

    monkeypatch.setattr(pipeline_mod, "load_or_fetch", wrapped_load)
    monkeypatch.setattr(sys, "argv", ["pipeline.py"])

    rc1 = pipeline_mod.main()
    rc2 = pipeline_mod.main()

    assert rc1 == 0
    assert rc2 == 0
    assert call_count["n"] == 1, "second call must hit cache"
    assert (tmp_path / f"{CACHE_KEY}.parquet").exists()
