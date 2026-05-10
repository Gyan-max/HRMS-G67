"""
feature_engineering.py — Behavioral feature extraction from check-in history.

Transforms raw 7-day check-in DataFrames into a rich feature vector with
15+ engineered features spanning sleep, mood, social, activity, and
composite behavioral dimensions. These features feed into the anomaly
detector and risk classifier.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Activity level → numeric mapping
# ---------------------------------------------------------------------------
ACTIVITY_MAP = {
    "sedentary": 1,
    "light": 2,
    "moderate": 3,
    "active": 4,
}


def _safe_linear_slope(series: pd.Series) -> float:
    """
    Compute the linear regression slope of a numeric series.

    Uses a simple least-squares fit against a 0-indexed time axis.
    Returns 0.0 if the series has fewer than 2 non-NaN values.
    """
    clean = series.dropna()
    if len(clean) < 2:
        return 0.0
    x = np.arange(len(clean), dtype=float)
    y = clean.values.astype(float)
    # Least-squares slope = cov(x,y) / var(x)
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def extract_features(history_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract a comprehensive feature vector from a user's recent check-in history.

    The function is designed to be robust:
      - Missing columns are filled with safe defaults.
      - NaN values in numeric columns are imputed with the column median.
      - If the history has fewer than 2 rows, features that require
        variance / trend calculations default to zero.

    Args:
        history_df: DataFrame with columns: sleep_hours, mood_score,
                    activity_level, social_interactions. Typically the
                    last 7 days of data.

    Returns:
        Single-row DataFrame with 15+ engineered features ready for
        model input.
    """
    features: dict = {}

    # ------------------------------------------------------------------
    # Guard: empty or very short history
    # ------------------------------------------------------------------
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
            # If every value is NaN, use a safe fallback
            fill_val = median_val if not np.isnan(median_val) else 0.0
            df[col] = df[col].fillna(fill_val)

    # Convert activity level to numeric score
    if "activity_level" in df.columns:
        df["activity_score"] = df["activity_level"].map(ACTIVITY_MAP).fillna(1)
    else:
        df["activity_score"] = 1

    # ==================================================================
    # SLEEP FEATURES
    # ==================================================================
    sleep = df["sleep_hours"] if "sleep_hours" in df.columns else pd.Series([7.0])

    features["avg_sleep"] = float(sleep.mean())
    features["sleep_variance"] = float(sleep.var()) if len(sleep) > 1 else 0.0
    features["sleep_trend"] = _safe_linear_slope(sleep)
    # Count days with fewer than 6 hours of sleep (sleep deficit)
    features["sleep_deficit_days"] = int((sleep < 6.0).sum())

    # ==================================================================
    # MOOD FEATURES
    # ==================================================================
    mood = df["mood_score"] if "mood_score" in df.columns else pd.Series([5])

    features["avg_mood"] = float(mood.mean())
    features["mood_trend"] = _safe_linear_slope(mood)
    # Mood volatility = standard deviation of mood scores
    features["mood_volatility"] = float(mood.std()) if len(mood) > 1 else 0.0
    features["lowest_mood"] = float(mood.min())

    # ==================================================================
    # SOCIAL FEATURES
    # ==================================================================
    social = df["social_interactions"] if "social_interactions" in df.columns else pd.Series([3])

    features["avg_social"] = float(social.mean())
    features["social_trend"] = _safe_linear_slope(social)
    # Isolation days = days with 0 or 1 social interactions
    features["isolation_days"] = int((social <= 1).sum())

    # ==================================================================
    # ACTIVITY FEATURES
    # ==================================================================
    activity = df["activity_score"]

    features["avg_activity_score"] = float(activity.mean())
    features["activity_trend"] = _safe_linear_slope(activity)
    # Sedentary days = days scored as 1 (sedentary)
    features["sedentary_days"] = int((activity <= 1).sum())

    # ==================================================================
    # COMPOSITE FEATURES
    # ==================================================================

    # Sleep–mood correlation: negative correlation suggests that poor
    # sleep co-occurs with low mood, a clinically relevant signal.
    if len(df) >= 3 and sleep.std() > 0 and mood.std() > 0:
        features["sleep_mood_correlation"] = float(sleep.corr(mood))
    else:
        features["sleep_mood_correlation"] = 0.0

    # Behavioral consistency score:
    # Low variance across all daily metrics → high consistency (good).
    # High variance → low consistency (concerning).
    # Normalized to 0–1 where 1 = perfectly consistent.
    variances = [
        features["sleep_variance"] / 4.0,      # Normalize: max expected ~4
        features["mood_volatility"] / 3.0,      # Normalize: max expected ~3
        float(social.var() / 25.0) if len(social) > 1 else 0.0,  # max ~25
        float(activity.var() / 2.0) if len(activity) > 1 else 0.0,
    ]
    avg_normalized_var = np.mean(variances)
    features["behavioral_consistency_score"] = float(
        max(0.0, 1.0 - avg_normalized_var)
    )

    # ------------------------------------------------------------------
    # Clamp NaN/inf to safe values
    # ------------------------------------------------------------------
    for key, val in features.items():
        if np.isnan(val) or np.isinf(val):
            features[key] = 0.0

    return pd.DataFrame([features])


def _default_features() -> pd.DataFrame:
    """
    Return a single-row DataFrame of neutral default features.

    Used when a user has no check-in history yet, so the ML pipeline
    can still produce a (neutral) prediction without crashing.
    """
    defaults = {
        "avg_sleep": 7.0,
        "sleep_variance": 0.0,
        "sleep_trend": 0.0,
        "sleep_deficit_days": 0,
        "avg_mood": 5.0,
        "mood_trend": 0.0,
        "mood_volatility": 0.0,
        "lowest_mood": 5.0,
        "avg_social": 3.0,
        "social_trend": 0.0,
        "isolation_days": 0,
        "avg_activity_score": 2.5,
        "activity_trend": 0.0,
        "sedentary_days": 0,
        "sleep_mood_correlation": 0.0,
        "behavioral_consistency_score": 0.8,
    }
    return pd.DataFrame([defaults])


def get_feature_names() -> list:
    """Return the ordered list of feature column names expected by the models."""
    return [
        "avg_sleep", "sleep_variance", "sleep_trend", "sleep_deficit_days",
        "avg_mood", "mood_trend", "mood_volatility", "lowest_mood",
        "avg_social", "social_trend", "isolation_days",
        "avg_activity_score", "activity_trend", "sedentary_days",
        "sleep_mood_correlation", "behavioral_consistency_score",
    ]
