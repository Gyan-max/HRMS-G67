"""
generate_synthetic_data.py — Generate labeled synthetic training data.

Creates 500 realistic behavioral feature vectors with risk labels for
training the anomaly detector and risk classifier. The data distribution
mimics real-world patterns with Gaussian noise for realism.

Risk distribution:
  - 150 LOW risk samples (30%)
  - 200 MEDIUM risk samples (40%)
  - 150 HIGH risk samples (30%)

When run as a script, this also trains and saves the initial ML models
so the system works out-of-the-box.
"""

import os
import sys
import numpy as np
import pandas as pd

# Add backend to path for model training
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# Ensure output directories exist
DATA_DIR = SCRIPT_DIR
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Seed for reproducibility
np.random.seed(42)

# Noise standard deviation for realism
NOISE_STD = 0.3


def generate_low_risk_samples(n: int = 150) -> pd.DataFrame:
    """
    Generate LOW risk behavioral profiles.

    Characteristics:
      - Healthy sleep: 7–9 hours, low variance
      - Good mood: 7–9 on 1–10 scale
      - Active lifestyle: moderate to active
      - Healthy social life: 5–10 daily interactions
      - Positive or neutral journal sentiment
    """
    data = {
        "avg_sleep": np.clip(np.random.normal(7.8, 0.5, n) + np.random.normal(0, NOISE_STD, n), 6.5, 9.5),
        "sleep_variance": np.clip(np.random.exponential(0.3, n), 0, 2.0),
        "sleep_trend": np.random.normal(0.05, 0.1, n),  # Slight positive trend
        "sleep_deficit_days": np.random.choice([0, 0, 0, 1], n),  # Rarely any deficit

        "avg_mood": np.clip(np.random.normal(7.5, 0.8, n) + np.random.normal(0, NOISE_STD, n), 6.0, 10.0),
        "mood_trend": np.random.normal(0.1, 0.15, n),  # Slightly positive
        "mood_volatility": np.clip(np.random.exponential(0.5, n), 0, 2.5),
        "lowest_mood": np.clip(np.random.normal(6.0, 1.0, n), 4, 9),

        "avg_social": np.clip(np.random.normal(7.0, 1.5, n) + np.random.normal(0, NOISE_STD, n), 4.0, 15.0),
        "social_trend": np.random.normal(0.0, 0.2, n),
        "isolation_days": np.random.choice([0, 0, 0, 0, 1], n),  # Very rare

        "avg_activity_score": np.clip(np.random.normal(3.2, 0.5, n), 2.0, 4.0),
        "activity_trend": np.random.normal(0.05, 0.1, n),
        "sedentary_days": np.random.choice([0, 0, 0, 1], n),

        "sleep_mood_correlation": np.clip(np.random.normal(0.5, 0.2, n), -1, 1),
        "behavioral_consistency_score": np.clip(np.random.normal(0.85, 0.08, n), 0.5, 1.0),
    }

    df = pd.DataFrame(data)
    df["risk_label"] = 0  # LOW
    return df


def generate_medium_risk_samples(n: int = 200) -> pd.DataFrame:
    """
    Generate MEDIUM risk behavioral profiles.

    Characteristics:
      - Mildly disrupted sleep: 6–7.5 hours
      - Moderate mood: 5–7
      - Mixed activity levels
      - Some social withdrawal: 2–5 interactions
      - Mixed journal sentiment
    """
    data = {
        "avg_sleep": np.clip(np.random.normal(6.5, 0.7, n) + np.random.normal(0, NOISE_STD, n), 5.0, 8.5),
        "sleep_variance": np.clip(np.random.exponential(0.8, n), 0.1, 3.5),
        "sleep_trend": np.random.normal(-0.1, 0.15, n),  # Slight negative trend
        "sleep_deficit_days": np.random.choice([0, 1, 1, 2, 2, 3], n),

        "avg_mood": np.clip(np.random.normal(5.5, 0.8, n) + np.random.normal(0, NOISE_STD, n), 4.0, 7.5),
        "mood_trend": np.random.normal(-0.15, 0.2, n),  # Mildly declining
        "mood_volatility": np.clip(np.random.normal(1.5, 0.5, n), 0.5, 3.5),
        "lowest_mood": np.clip(np.random.normal(4.0, 1.0, n), 2, 7),

        "avg_social": np.clip(np.random.normal(3.5, 1.2, n) + np.random.normal(0, NOISE_STD, n), 1.0, 8.0),
        "social_trend": np.random.normal(-0.1, 0.2, n),
        "isolation_days": np.random.choice([0, 1, 1, 2, 2, 3], n),

        "avg_activity_score": np.clip(np.random.normal(2.3, 0.6, n), 1.0, 3.5),
        "activity_trend": np.random.normal(-0.05, 0.15, n),
        "sedentary_days": np.random.choice([1, 1, 2, 2, 3], n),

        "sleep_mood_correlation": np.clip(np.random.normal(0.2, 0.3, n), -1, 1),
        "behavioral_consistency_score": np.clip(np.random.normal(0.6, 0.12, n), 0.2, 0.9),
    }

    df = pd.DataFrame(data)
    df["risk_label"] = 1  # MEDIUM
    return df


def generate_high_risk_samples(n: int = 150) -> pd.DataFrame:
    """
    Generate HIGH risk behavioral profiles.

    Characteristics:
      - Poor sleep: <6 hours or >10 hours (hypersomnia)
      - Low mood: <5 on 1–10 scale
      - Sedentary lifestyle
      - Social isolation: 0–2 interactions
      - Negative journal sentiment
    """
    # Split between sleep-deprived and hypersomnia patterns
    n_deprived = n * 3 // 4  # 75% sleep deprived
    n_hyper = n - n_deprived  # 25% hypersomnia

    sleep_deprived = np.clip(np.random.normal(4.5, 0.8, n_deprived), 2.0, 6.0)
    sleep_hyper = np.clip(np.random.normal(10.5, 0.5, n_hyper), 9.5, 12.0)
    avg_sleep = np.concatenate([sleep_deprived, sleep_hyper])
    np.random.shuffle(avg_sleep)

    data = {
        "avg_sleep": avg_sleep + np.random.normal(0, NOISE_STD, n),
        "sleep_variance": np.clip(np.random.normal(2.0, 0.7, n), 0.5, 5.0),
        "sleep_trend": np.random.normal(-0.2, 0.15, n),  # Declining
        "sleep_deficit_days": np.random.choice([3, 4, 4, 5, 5, 6, 7], n),

        "avg_mood": np.clip(np.random.normal(3.5, 0.9, n) + np.random.normal(0, NOISE_STD, n), 1.0, 5.5),
        "mood_trend": np.random.normal(-0.3, 0.2, n),  # Strongly declining
        "mood_volatility": np.clip(np.random.normal(2.5, 0.6, n), 1.0, 4.5),
        "lowest_mood": np.clip(np.random.normal(2.0, 0.8, n), 1, 4),

        "avg_social": np.clip(np.random.normal(1.0, 0.7, n) + np.random.normal(0, NOISE_STD, n), 0.0, 3.0),
        "social_trend": np.random.normal(-0.2, 0.2, n),  # Declining
        "isolation_days": np.random.choice([3, 4, 4, 5, 5, 6, 7], n),

        "avg_activity_score": np.clip(np.random.normal(1.3, 0.4, n), 1.0, 2.5),
        "activity_trend": np.random.normal(-0.1, 0.15, n),
        "sedentary_days": np.random.choice([4, 5, 5, 6, 6, 7], n),

        "sleep_mood_correlation": np.clip(np.random.normal(-0.2, 0.3, n), -1, 1),
        "behavioral_consistency_score": np.clip(np.random.normal(0.3, 0.12, n), 0.0, 0.6),
    }

    df = pd.DataFrame(data)
    df["risk_label"] = 2  # HIGH
    return df


def generate_full_dataset() -> pd.DataFrame:
    """
    Generate the complete synthetic training dataset with 500 samples.

    Returns:
        DataFrame with 16 features + 1 label column, shuffled randomly.
    """
    print("Generating synthetic behavioral data...")
    print("  → 150 LOW risk samples")
    low = generate_low_risk_samples(150)

    print("  → 200 MEDIUM risk samples")
    medium = generate_medium_risk_samples(200)

    print("  → 150 HIGH risk samples")
    high = generate_high_risk_samples(150)

    # Combine and shuffle
    full_dataset = pd.concat([low, medium, high], ignore_index=True)
    full_dataset = full_dataset.sample(frac=1, random_state=42).reset_index(drop=True)

    # Clip extreme values that noise might have pushed out of range
    full_dataset["avg_sleep"] = full_dataset["avg_sleep"].clip(0, 14)
    full_dataset["avg_mood"] = full_dataset["avg_mood"].clip(1, 10)
    full_dataset["avg_social"] = full_dataset["avg_social"].clip(0, 30)
    full_dataset["behavioral_consistency_score"] = full_dataset["behavioral_consistency_score"].clip(0, 1)

    return full_dataset


def train_initial_models(dataset: pd.DataFrame):
    """
    Train and save the anomaly detector and risk classifier on synthetic data.

    This is called when running this script directly, ensuring models
    are ready before the first server start.
    """
    from anomaly_detector import BehavioralAnomalyDetector
    from risk_classifier import RiskClassifier
    from feature_engineering import get_feature_names

    feature_cols = get_feature_names()
    available_cols = [c for c in feature_cols if c in dataset.columns]
    X = dataset[available_cols]
    y = dataset["risk_label"]

    # Train anomaly detector
    print("\n--- Training Anomaly Detector ---")
    detector = BehavioralAnomalyDetector()
    result = detector.fit(X)
    print(f"  Status: {result['status']}")
    print(f"  Samples: {result.get('samples', 'N/A')}")

    # Train risk classifier
    print("\n--- Training Risk Classifier ---")
    classifier = RiskClassifier()
    result = classifier.train(X, y)
    print(f"  Status: {result['status']}")
    print(f"  Training accuracy: {result.get('training_accuracy', 'N/A')}")
    print(f"  Class distribution: {result.get('class_distribution', 'N/A')}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Synthetic Training Data Generator")
    print("=" * 60)

    # Generate the dataset
    dataset = generate_full_dataset()

    # Save to CSV
    output_path = os.path.join(DATA_DIR, "synthetic_training_data.csv")
    dataset.to_csv(output_path, index=False)
    print(f"\n✅ Saved {len(dataset)} samples to: {output_path}")
    print(f"\nDataset shape: {dataset.shape}")
    print(f"Label distribution:\n{dataset['risk_label'].value_counts().sort_index().to_string()}")
    print(f"\nFeature statistics:")
    print(dataset.describe().round(3).to_string())

    # Train models
    print("\n" + "=" * 60)
    print("  Training Initial ML Models")
    print("=" * 60)
    train_initial_models(dataset)

    print("\n✅ All done! Models saved to: models/")
    print("You can now start the server with: bash run.sh")
