"""
feature_engineering.py — Behavioral feature extraction from check-in history.

Transforms raw 7-day (and optionally 14/30-day) check-in DataFrames into a
rich feature vector with 26+ engineered features spanning sleep, mood, social,
activity, streak, velocity, and composite behavioral dimensions.

New clinical features added:
  - Streak features: consecutive low-mood/sleep/isolation days at end of window
  - Velocity features: rate-of-change acceleration (is the decline speeding up?)
  - Debt features: cumulative sleep deficit below the 7h healthy threshold
  - Drop features: distance from recent peak to current value
  - Cross-signal distress: simultaneous bad sleep + bad mood + isolation
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Activity level → numeric mapping
# ---------------------------------------------------------------------------
ACTIVITY_MAP = {
    "sedentary": 1,
    "light":     2,
    "moderate":  3,
    "active":    4,
}

HEALTHY_SLEEP_TARGET = 7.0   # hours
LOW_MOOD_THRESHOLD   = 5.0   # out of 10
LOW_SLEEP_THRESHOLD  = 6.0   # hours
LOW_SOCIAL_THRESHOLD = 1     # interactions/day


def _safe_linear_slope(series: pd.Series) -> float:
    """Least-squares slope of a numeric series vs a 0-indexed time axis."""
    clean = series.dropna()
    if len(clean) < 2:
        return 0.0
    x = np.arange(len(clean), dtype=float)
    y = clean.values.astype(float)
    return float(np.polyfit(x, y, 1)[0])


def _trailing_streak(values: list, condition) -> int:
    """Count consecutive values at the *end* of a list satisfying condition."""
    count = 0
    for v in reversed(values):
        if condition(v):
            count += 1
        else:
            break
    return count


def _velocity(series: pd.Series) -> float:
    """
    Compute the change in slope between the first half and second half of the
    series — i.e. is the decline/rise *accelerating*?

    Positive → situation is deteriorating faster recently.
    Negative → things are improving or slowing down.
    Returns 0.0 when the series is too short to split meaningfully.
    """
    clean = series.dropna()
    if len(clean) < 4:
        return 0.0
    mid = len(clean) // 2
    first_slope = _safe_linear_slope(clean.iloc[:mid])
    second_slope = _safe_linear_slope(clean.iloc[mid:])
    return float(second_slope - first_slope)


def extract_features(history_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract a comprehensive feature vector from a user's recent check-in history.

    Args:
        history_df: DataFrame with columns: sleep_hours, mood_score,
                    activity_level, social_interactions. Typically the
                    last 7 days (or more) of data, ordered oldest→newest.

    Returns:
        Single-row DataFrame with 26+ engineered features.
    """
    if history_df is None or len(history_df) == 0:
        return _default_features()

    df = history_df.copy()

    # ------------------------------------------------------------------
    # Pre-processing: coerce types and fill NaNs
    # ------------------------------------------------------------------
    numeric_cols = ["sleep_hours", "mood_score", "social_interactions"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            median_val = df[col].median()
            fill_val = median_val if not np.isnan(median_val) else 0.0
            df[col] = df[col].fillna(fill_val)

    if "activity_level" in df.columns:
        df["activity_score"] = df["activity_level"].map(ACTIVITY_MAP).fillna(1)
    else:
        df["activity_score"] = 1

    features: dict = {}

    # ==================================================================
    # SLEEP FEATURES
    # ==================================================================
    sleep = df["sleep_hours"] if "sleep_hours" in df.columns else pd.Series([7.0])
    sleep_vals = sleep.tolist()

    features["avg_sleep"]          = float(sleep.mean())
    features["sleep_variance"]     = float(sleep.var()) if len(sleep) > 1 else 0.0
    features["sleep_trend"]        = _safe_linear_slope(sleep)
    features["sleep_deficit_days"] = int((sleep < LOW_SLEEP_THRESHOLD).sum())

    # NEW: streak of low-sleep nights at the end of the window
    features["consecutive_low_sleep_days"] = _trailing_streak(
        sleep_vals, lambda v: v < LOW_SLEEP_THRESHOLD
    )
    # NEW: total hours of sleep debt below the healthy target
    features["sleep_debt"] = float(max(
        0.0, HEALTHY_SLEEP_TARGET * len(sleep) - sleep.sum()
    ))
    # NEW: is the rate of sleep deterioration accelerating?
    features["sleep_velocity"] = _velocity(sleep)

    # ==================================================================
    # MOOD FEATURES
    # ==================================================================
    mood = df["mood_score"] if "mood_score" in df.columns else pd.Series([5])
    mood_vals = mood.tolist()

    features["avg_mood"]        = float(mood.mean())
    features["mood_trend"]      = _safe_linear_slope(mood)
    features["mood_volatility"] = float(mood.std()) if len(mood) > 1 else 0.0
    features["lowest_mood"]     = float(mood.min())

    # NEW: consecutive days with mood below threshold at end of window
    features["consecutive_low_mood_days"] = _trailing_streak(
        mood_vals, lambda v: v < LOW_MOOD_THRESHOLD
    )
    # NEW: how far has mood dropped from its recent peak? (drift detector)
    peak_mood = float(mood.max()) if len(mood) > 0 else 5.0
    current_mood = float(mood.iloc[-1]) if len(mood) > 0 else 5.0
    features["mood_drop_from_peak"] = max(0.0, peak_mood - current_mood)
    # NEW: acceleration — is the mood decline speeding up?
    features["mood_velocity"] = _velocity(mood)

    # ==================================================================
    # SOCIAL FEATURES
    # ==================================================================
    social = (
        df["social_interactions"]
        if "social_interactions" in df.columns
        else pd.Series([3])
    )
    social_vals = social.tolist()

    features["avg_social"]    = float(social.mean())
    features["social_trend"]  = _safe_linear_slope(social)
    features["isolation_days"] = int((social <= LOW_SOCIAL_THRESHOLD).sum())

    # NEW: consecutive days of near-total isolation at end of window
    features["social_isolation_streak"] = _trailing_streak(
        social_vals, lambda v: v <= LOW_SOCIAL_THRESHOLD
    )

    # ==================================================================
    # ACTIVITY FEATURES
    # ==================================================================
    activity = df["activity_score"]

    features["avg_activity_score"] = float(activity.mean())
    features["activity_trend"]     = _safe_linear_slope(activity)
    features["sedentary_days"]     = int((activity <= 1).sum())

    # ==================================================================
    # COMPOSITE FEATURES
    # ==================================================================
    # Sleep-mood correlation
    if len(df) >= 3 and sleep.std() > 0 and mood.std() > 0:
        features["sleep_mood_correlation"] = float(sleep.corr(mood))
    else:
        features["sleep_mood_correlation"] = 0.0

    # Behavioral consistency score
    variances = [
        features["sleep_variance"] / 4.0,
        features["mood_volatility"] / 3.0,
        float(social.var() / 25.0) if len(social) > 1 else 0.0,
        float(activity.var() / 2.0) if len(activity) > 1 else 0.0,
    ]
    features["behavioral_consistency_score"] = float(
        max(0.0, 1.0 - np.mean(variances))
    )

    # NEW: cross-signal distress — all three primary signals in bad shape
    # simultaneously is a stronger signal than any single metric alone.
    distress_flags = (
        (1.0 if features["avg_sleep"] < LOW_SLEEP_THRESHOLD else 0.0)
        + (1.0 if features["avg_mood"] < LOW_MOOD_THRESHOLD else 0.0)
        + (1.0 if features["avg_social"] < 2.0 else 0.0)
    )
    features["cross_signal_distress"] = distress_flags / 3.0

    # ------------------------------------------------------------------
    # Clamp NaN/inf to safe values
    # ------------------------------------------------------------------
    for key, val in features.items():
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            features[key] = 0.0

    return pd.DataFrame([features])


def _default_features() -> pd.DataFrame:
    """
    Return a single-row DataFrame of neutral default features for users with
    no check-in history yet (all new features default to safe neutral values).
    """
    defaults = {
        # Core sleep
        "avg_sleep":                   7.0,
        "sleep_variance":              0.0,
        "sleep_trend":                 0.0,
        "sleep_deficit_days":          0,
        "consecutive_low_sleep_days":  0,
        "sleep_debt":                  0.0,
        "sleep_velocity":              0.0,
        # Core mood
        "avg_mood":                    5.0,
        "mood_trend":                  0.0,
        "mood_volatility":             0.0,
        "lowest_mood":                 5.0,
        "consecutive_low_mood_days":   0,
        "mood_drop_from_peak":         0.0,
        "mood_velocity":               0.0,
        # Core social
        "avg_social":                  3.0,
        "social_trend":                0.0,
        "isolation_days":              0,
        "social_isolation_streak":     0,
        # Activity
        "avg_activity_score":          2.5,
        "activity_trend":              0.0,
        "sedentary_days":              0,
        # Composite
        "sleep_mood_correlation":      0.0,
        "behavioral_consistency_score": 0.8,
        "cross_signal_distress":       0.0,
        "mood_drop_from_peak":         0.0,  # already above, harmless duplicate
    }
    # Remove the duplicate key from the dict (Python keeps last)
    defaults.pop("mood_drop_from_peak", None)
    defaults["mood_drop_from_peak"] = 0.0
    return pd.DataFrame([defaults])


def get_feature_names() -> list:
    """Return the ordered list of all feature column names."""
    return [
        # Sleep
        "avg_sleep", "sleep_variance", "sleep_trend", "sleep_deficit_days",
        "consecutive_low_sleep_days", "sleep_debt", "sleep_velocity",
        # Mood
        "avg_mood", "mood_trend", "mood_volatility", "lowest_mood",
        "consecutive_low_mood_days", "mood_drop_from_peak", "mood_velocity",
        # Social
        "avg_social", "social_trend", "isolation_days", "social_isolation_streak",
        # Activity
        "avg_activity_score", "activity_trend", "sedentary_days",
        # Composite
        "sleep_mood_correlation", "behavioral_consistency_score",
        "cross_signal_distress",
    ]
