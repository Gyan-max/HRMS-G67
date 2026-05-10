"""
Tests for behavioural feature extraction.

The feature extractor must be robust to:
  - Empty / single-row history
  - Missing columns
  - NaN / inf values
  - Mixed activity-level strings
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from feature_engineering import (
    ACTIVITY_MAP,
    extract_features,
    get_feature_names,
)


def test_extract_features_empty_history_returns_defaults() -> None:
    """An empty history must return a single row of safe defaults."""
    out = extract_features(pd.DataFrame())
    assert len(out) == 1
    # All declared feature columns should be present.
    for name in get_feature_names():
        assert name in out.columns


def test_extract_features_none_input_returns_defaults() -> None:
    out = extract_features(None)
    assert len(out) == 1


def test_extract_features_single_row_does_not_crash() -> None:
    history = pd.DataFrame([{
        "sleep_hours": 4.0,
        "mood_score": 3,
        "activity_level": "sedentary",
        "social_interactions": 0,
    }])
    out = extract_features(history)
    assert len(out) == 1
    assert "avg_sleep" in out.columns
    # With a single row, variance / volatility must be 0 (not NaN).
    assert out.iloc[0]["sleep_variance"] == 0.0
    assert out.iloc[0]["mood_volatility"] == 0.0


def test_extract_features_high_risk_profile() -> None:
    history = pd.DataFrame([
        {"sleep_hours": 4.0, "mood_score": 3, "activity_level": "sedentary", "social_interactions": 0},
        {"sleep_hours": 4.5, "mood_score": 2, "activity_level": "sedentary", "social_interactions": 1},
        {"sleep_hours": 3.5, "mood_score": 2, "activity_level": "sedentary", "social_interactions": 0},
        {"sleep_hours": 5.0, "mood_score": 3, "activity_level": "sedentary", "social_interactions": 0},
        {"sleep_hours": 4.0, "mood_score": 1, "activity_level": "sedentary", "social_interactions": 0},
    ])
    out = extract_features(history).iloc[0]

    assert out["avg_sleep"] < 5.0
    assert out["avg_mood"] < 3.5
    assert out["avg_social"] < 1.0
    assert out["sleep_deficit_days"] >= 4
    assert out["isolation_days"] >= 4
    assert out["sedentary_days"] == 5


def test_extract_features_handles_nan_values() -> None:
    history = pd.DataFrame([
        {"sleep_hours": np.nan, "mood_score": 5, "activity_level": "light", "social_interactions": 3},
        {"sleep_hours": 7.0, "mood_score": np.nan, "activity_level": "light", "social_interactions": 4},
        {"sleep_hours": 8.0, "mood_score": 6, "activity_level": "moderate", "social_interactions": np.nan},
    ])
    out = extract_features(history).iloc[0]

    # No NaNs / infs should leak through to the output.
    for value in out.values:
        if isinstance(value, (int, float)):
            assert not np.isnan(value)
            assert not np.isinf(value)


def test_activity_map_covers_expected_levels() -> None:
    assert set(ACTIVITY_MAP.keys()) == {"sedentary", "light", "moderate", "active"}
    assert ACTIVITY_MAP["sedentary"] < ACTIVITY_MAP["active"]


def test_get_feature_names_is_stable_and_deterministic() -> None:
    names = get_feature_names()
    # Important features must be present.
    for required in (
        "avg_sleep", "avg_mood", "avg_social", "isolation_days",
        "sleep_deficit_days", "behavioral_consistency_score",
    ):
        assert required in names
    # Calling twice gives the same list.
    assert names == get_feature_names()


def test_extract_features_trend_increasing_for_improving_mood() -> None:
    history = pd.DataFrame([
        {"sleep_hours": 7.0, "mood_score": 3, "activity_level": "light", "social_interactions": 2},
        {"sleep_hours": 7.0, "mood_score": 4, "activity_level": "light", "social_interactions": 3},
        {"sleep_hours": 7.0, "mood_score": 5, "activity_level": "light", "social_interactions": 4},
        {"sleep_hours": 7.0, "mood_score": 6, "activity_level": "light", "social_interactions": 5},
        {"sleep_hours": 7.0, "mood_score": 7, "activity_level": "light", "social_interactions": 6},
    ])
    out = extract_features(history).iloc[0]
    assert out["mood_trend"] > 0
    assert out["social_trend"] > 0
