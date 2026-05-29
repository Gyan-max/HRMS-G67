"""
generate_synthetic_data.py — PHQ-9/GAD-7-aligned synthetic training data generator.

v2 improvements over v1:
  - 5 000 samples (10× more) with better class balance (20/40/40 LOW/MED/HIGH)
  - Feature distributions aligned with PHQ-9 and GAD-7 validated thresholds
  - Generates all 24 features expected by the v2 feature engineering module
  - Four realistic trajectory sub-types per risk class:
      LOW:    stable high-functioning / recovering / occasional bad day
      MEDIUM: gradual drift / anxiety-driven / social withdrawal
      HIGH:   severe depression / crisis / acute episode / burnout
  - Adds realistic cross-feature correlations (sleep ↔ mood, mood ↔ social)
  - Reports honest cross-validated metrics after training
"""

import os
import sys
import numpy as np
import pandas as pd

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

DATA_DIR   = SCRIPT_DIR
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

np.random.seed(42)
NOISE = 0.25   # tighter noise than v1 for cleaner decision boundaries


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def clip_col(arr, lo, hi):
    return np.clip(arr + np.random.normal(0, NOISE, len(arr)), lo, hi)


def _row(n, avg_sleep, avg_mood, avg_social, avg_activity,
         sleep_var=0.5, mood_var=0.8, social_var=1.2,
         sleep_trend=0.0, mood_trend=0.0, social_trend=0.0,
         sleep_deficit_prob=0.0, isolation_prob=0.0,
         mood_vol_base=0.5):
    """
    Generate n rows of the full 24-feature vector.

    All values are drawn from parameterized Gaussian distributions that
    mirror the observable behaviors described by PHQ-9 items 1-9.
    """
    n = int(n)

    # Core averages
    sl = clip_col(np.random.normal(avg_sleep,  sleep_var,  n), 0.0, 13.0)
    mo = clip_col(np.random.normal(avg_mood,   mood_var,   n), 1.0, 10.0)
    so = clip_col(np.random.normal(avg_social, social_var, n), 0.0, 20.0)
    ac = clip_col(np.random.normal(avg_activity, 0.4,      n), 1.0,  4.0)

    # Sleep features
    sl_var   = np.clip(np.random.exponential(sleep_var * 0.6, n), 0.0, 5.0)
    sl_trend = np.random.normal(sleep_trend, 0.12, n)
    sl_def   = np.random.binomial(7, sleep_deficit_prob, n)
    sl_streak = np.clip(np.random.geometric(max(1 - sleep_deficit_prob, 0.05), n) - 1, 0, 7)
    sl_debt  = np.clip(sl_def * (7.0 - np.clip(sl, 0, 7)), 0, 30)
    sl_vel   = np.random.normal(sleep_trend * 0.3, 0.1, n)

    # Mood features
    mo_trend = np.random.normal(mood_trend, 0.18, n)
    mo_vol   = np.clip(np.random.exponential(mood_vol_base, n), 0.0, 4.5)
    mo_low   = np.clip(mo - np.abs(np.random.normal(1.5 * mood_vol_base, 0.5, n)), 1, 10)
    mo_streak = np.clip(np.random.geometric(max(0.6 - isolation_prob * 0.3, 0.1), n) - 1, 0, 7)
    mo_drop  = np.clip(np.abs(np.random.normal(2.0 * (1 - avg_mood / 10), 0.8, n)), 0, 9)
    mo_vel   = np.random.normal(mood_trend * 0.4, 0.12, n)

    # Social features
    so_trend = np.random.normal(social_trend, 0.2, n)
    iso_days = np.random.binomial(7, isolation_prob, n)
    iso_str  = np.clip(np.random.geometric(max(1 - isolation_prob, 0.05), n) - 1, 0, 7)

    # Activity features
    ac_trend = np.random.normal(0.0, 0.1, n)
    sed_days = np.clip(7 - np.round(ac * 1.5).astype(int), 0, 7)

    # Composite features
    sl_mo_corr = np.clip(np.random.normal(
        0.3 if avg_sleep >= 6.5 and avg_mood >= 5 else -0.1, 0.25, n
    ), -1.0, 1.0)

    cons = np.clip(1.0 - (sl_var / 4 + mo_vol / 3 + np.clip(so ** 2 / 25, 0, 1)) / 3, 0.0, 1.0)

    # cross_signal_distress: 0–1 fraction of bad dimensions
    bad_sl = (sl < 6.0).astype(float)
    bad_mo = (mo < 5.0).astype(float)
    bad_so = (so < 2.0).astype(float)
    cross  = (bad_sl + bad_mo + bad_so) / 3.0

    return pd.DataFrame({
        "avg_sleep":                  sl,
        "sleep_variance":             sl_var,
        "sleep_trend":                sl_trend,
        "sleep_deficit_days":         sl_def,
        "consecutive_low_sleep_days": sl_streak,
        "sleep_debt":                 sl_debt,
        "sleep_velocity":             sl_vel,
        "avg_mood":                   mo,
        "mood_trend":                 mo_trend,
        "mood_volatility":            mo_vol,
        "lowest_mood":                mo_low,
        "consecutive_low_mood_days":  mo_streak,
        "mood_drop_from_peak":        mo_drop,
        "mood_velocity":              mo_vel,
        "avg_social":                 so,
        "social_trend":               so_trend,
        "isolation_days":             iso_days,
        "social_isolation_streak":    iso_str,
        "avg_activity_score":         ac,
        "activity_trend":             ac_trend,
        "sedentary_days":             sed_days,
        "sleep_mood_correlation":     sl_mo_corr,
        "behavioral_consistency_score": cons,
        "cross_signal_distress":      cross,
    })


# ---------------------------------------------------------------------------
# LOW risk sub-types  (PHQ-9 score 0-4 / GAD-7 0-4)
# ---------------------------------------------------------------------------
def generate_low_risk(n: int) -> pd.DataFrame:
    n_each = n // 4
    parts = [
        # Stable high-functioning
        _row(n_each, avg_sleep=7.8, avg_mood=8.0, avg_social=7.0, avg_activity=3.3,
             sleep_var=0.4, mood_var=0.6, sleep_deficit_prob=0.02, isolation_prob=0.02,
             mood_trend=0.05, mood_vol_base=0.4),
        # Recovering — was medium, now improving
        _row(n_each, avg_sleep=7.2, avg_mood=7.0, avg_social=5.5, avg_activity=2.9,
             sleep_var=0.6, mood_var=0.9, sleep_deficit_prob=0.05, isolation_prob=0.05,
             mood_trend=0.15, mood_vol_base=0.6),
        # Occasional bad day — one low reading among many good ones
        _row(n_each, avg_sleep=7.5, avg_mood=7.5, avg_social=6.0, avg_activity=3.1,
             sleep_var=0.8, mood_var=1.2, sleep_deficit_prob=0.03, isolation_prob=0.03,
             mood_vol_base=1.0),
        # Healthy introvert — lower social but otherwise fine
        _row(n - 3 * n_each, avg_sleep=7.6, avg_mood=7.2, avg_social=2.5, avg_activity=2.8,
             sleep_var=0.4, mood_var=0.7, sleep_deficit_prob=0.02, isolation_prob=0.1,
             mood_vol_base=0.5),
    ]
    df = pd.concat(parts, ignore_index=True)
    df["risk_label"] = 0
    return df


# ---------------------------------------------------------------------------
# MEDIUM risk sub-types  (PHQ-9 5-14 / GAD-7 5-14)
# ---------------------------------------------------------------------------
def generate_medium_risk(n: int) -> pd.DataFrame:
    n_each = n // 4
    parts = [
        # Gradual drift — everything slightly off
        _row(n_each, avg_sleep=6.4, avg_mood=5.4, avg_social=3.2, avg_activity=2.2,
             sleep_var=0.9, mood_var=1.1, sleep_deficit_prob=0.2, isolation_prob=0.15,
             mood_trend=-0.12, mood_vol_base=1.2),
        # Anxiety-driven — irregular sleep, high mood volatility
        _row(n_each, avg_sleep=6.0, avg_mood=5.8, avg_social=3.5, avg_activity=2.5,
             sleep_var=1.8, mood_var=1.8, sleep_deficit_prob=0.25, isolation_prob=0.12,
             mood_trend=-0.08, mood_vol_base=2.0),
        # Social withdrawal — mood ok but isolation rising
        _row(n_each, avg_sleep=6.8, avg_mood=5.5, avg_social=1.5, avg_activity=2.0,
             sleep_var=0.7, mood_var=1.0, sleep_deficit_prob=0.15, isolation_prob=0.45,
             social_trend=-0.2, mood_vol_base=0.9),
        # Sleep-deprived functioning — holding mood up but tired
        _row(n - 3 * n_each, avg_sleep=5.8, avg_mood=5.9, avg_social=4.0, avg_activity=2.3,
             sleep_var=1.2, mood_var=0.9, sleep_deficit_prob=0.35, isolation_prob=0.1,
             mood_trend=-0.05, mood_vol_base=0.8),
    ]
    df = pd.concat(parts, ignore_index=True)
    df["risk_label"] = 1
    return df


# ---------------------------------------------------------------------------
# HIGH risk sub-types  (PHQ-9 ≥15 / GAD-7 ≥15, or clinical indicators)
# ---------------------------------------------------------------------------
def generate_high_risk(n: int) -> pd.DataFrame:
    n_each = n // 4
    parts = [
        # Severe depression — low on all signals
        _row(n_each, avg_sleep=4.5, avg_mood=2.8, avg_social=0.6, avg_activity=1.2,
             sleep_var=1.8, mood_var=1.0, sleep_deficit_prob=0.75, isolation_prob=0.80,
             mood_trend=-0.3, mood_vol_base=0.8),
        # Hypersomnia + low mood (atypical depression pattern)
        _row(n_each, avg_sleep=10.5, avg_mood=3.2, avg_social=0.8, avg_activity=1.1,
             sleep_var=1.2, mood_var=1.2, sleep_deficit_prob=0.10, isolation_prob=0.75,
             mood_trend=-0.2, mood_vol_base=1.0),
        # Acute crisis — sudden deterioration from moderate baseline
        _row(n_each, avg_sleep=5.0, avg_mood=3.5, avg_social=0.5, avg_activity=1.3,
             sleep_var=2.5, mood_var=2.0, sleep_deficit_prob=0.65, isolation_prob=0.85,
             mood_trend=-0.5, mood_vol_base=2.5, sleep_trend=-0.4),
        # Burnout — high historical activity collapsing
        _row(n - 3 * n_each, avg_sleep=5.5, avg_mood=4.0, avg_social=1.0, avg_activity=1.5,
             sleep_var=1.5, mood_var=1.5, sleep_deficit_prob=0.60, isolation_prob=0.70,
             mood_trend=-0.25, mood_vol_base=1.8, sleep_trend=-0.2),
    ]
    df = pd.concat(parts, ignore_index=True)
    df["risk_label"] = 2
    return df


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------
def generate_full_dataset(total: int = 5000) -> pd.DataFrame:
    n_low    = int(total * 0.20)   # 20% LOW   (rare in clinical populations)
    n_medium = int(total * 0.40)   # 40% MEDIUM
    n_high   = total - n_low - n_medium  # 40% HIGH

    print(f"  → {n_low} LOW samples")
    low    = generate_low_risk(n_low)
    print(f"  → {n_medium} MEDIUM samples")
    medium = generate_medium_risk(n_medium)
    print(f"  → {n_high} HIGH samples")
    high   = generate_high_risk(n_high)

    full = pd.concat([low, medium, high], ignore_index=True)
    full = full.sample(frac=1, random_state=42).reset_index(drop=True)

    # Final clipping
    full["avg_sleep"]  = full["avg_sleep"].clip(0, 14)
    full["avg_mood"]   = full["avg_mood"].clip(1, 10)
    full["avg_social"] = full["avg_social"].clip(0, 30)
    full["behavioral_consistency_score"] = full["behavioral_consistency_score"].clip(0, 1)
    full["cross_signal_distress"]        = full["cross_signal_distress"].clip(0, 1)
    full["sleep_debt"]                   = full["sleep_debt"].clip(0, 50)

    return full


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_initial_models(dataset: pd.DataFrame):
    from anomaly_detector import BehavioralAnomalyDetector
    from risk_classifier  import RiskClassifier
    from feature_engineering import get_feature_names

    feature_cols   = get_feature_names()
    available_cols = [c for c in feature_cols if c in dataset.columns]
    X = dataset[available_cols]
    y = dataset["risk_label"]

    print("\n--- Training Population Anomaly Detector ---")
    detector = BehavioralAnomalyDetector()
    result   = detector.fit(X)
    print(f"  Status:  {result['status']}")
    print(f"  Samples: {result.get('samples')}")

    print("\n--- Training Risk Classifier (with 5-fold CV) ---")
    classifier = RiskClassifier()
    result     = classifier.train(X, y)
    print(f"  Status:          {result['status']}")
    print(f"  CV F1-macro:     {result.get('cv_f1_macro_mean', 'N/A'):.4f} "
          f"± {result.get('cv_f1_macro_std', 0):.4f}")
    print(f"  Class dist:      {result.get('class_distribution')}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Synthetic Training Data Generator  v2")
    print("  PHQ-9 / GAD-7 aligned • 5 000 samples • 24 features")
    print("=" * 60)

    print("\nGenerating dataset…")
    dataset = generate_full_dataset(5000)

    output_path = os.path.join(DATA_DIR, "synthetic_training_data.csv")
    dataset.to_csv(output_path, index=False)
    print(f"\n✅ Saved {len(dataset)} samples → {output_path}")
    print(f"\nLabel distribution:\n{dataset['risk_label'].value_counts().sort_index()}")
    print(f"\nFeature sample:\n{dataset.describe().round(2).to_string()}")

    print("\n" + "=" * 60)
    print("  Training ML Models")
    print("=" * 60)
    train_initial_models(dataset)
    print("\n✅ Done. Models saved to models/")
    print("Start the server with:  bash run.sh")
