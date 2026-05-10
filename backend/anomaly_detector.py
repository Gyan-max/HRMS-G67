"""
anomaly_detector.py — Behavioral anomaly detection using Isolation Forest.

Detects unusual behavioral patterns by training an Isolation Forest on
historical feature vectors. Anomalies may indicate sudden behavioral
shifts (e.g., drastic sleep change, social withdrawal) that aren't
captured by gradual trend analysis.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any

# Directory for persisting trained models
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

ANOMALY_MODEL_PATH = os.path.join(MODELS_DIR, "anomaly_model.pkl")
ANOMALY_SCALER_PATH = os.path.join(MODELS_DIR, "anomaly_scaler.pkl")


class BehavioralAnomalyDetector:
    """
    Detects anomalous behavioral patterns using Isolation Forest.

    The detector learns what "normal" behavior looks like from historical
    data and flags data points that deviate significantly. This captures
    sudden changes that rule-based systems might miss.

    Workflow:
        1. Train on historical feature vectors (fit)
        2. Score new data points as anomalous or normal (detect)
        3. Models are persisted to disk for reuse across server restarts

    Usage::

        detector = BehavioralAnomalyDetector()
        detector.fit(training_features_df)
        result = detector.detect(new_features_df)
        # result["is_anomaly"]  → True/False
    """

    def __init__(self):
        """
        Initialize the detector, loading saved models if available.

        If no saved models exist, the detector operates in an "unfitted"
        state and returns safe defaults until training data is provided.
        """
        self.model = None
        self.scaler = None
        self.is_fitted = False

        # Attempt to load previously trained models
        if os.path.exists(ANOMALY_MODEL_PATH) and os.path.exists(ANOMALY_SCALER_PATH):
            try:
                self.model = joblib.load(ANOMALY_MODEL_PATH)
                self.scaler = joblib.load(ANOMALY_SCALER_PATH)
                self.is_fitted = True
            except Exception as e:
                print(f"[AnomalyDetector] Warning: Could not load saved models: {e}")
                self.is_fitted = False

    def fit(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the Isolation Forest on a DataFrame of behavioral features.

        Args:
            features_df: DataFrame where each row is a feature vector.
                         Should contain at least 10 samples for reliable
                         training.

        Returns:
            Dict with training status and sample count.
        """
        if features_df is None or len(features_df) < 5:
            return {
                "status": "insufficient_data",
                "message": "Need at least 5 samples to train anomaly detector.",
                "samples": len(features_df) if features_df is not None else 0,
            }

        # Replace any remaining NaN/inf values
        X = features_df.select_dtypes(include=[np.number]).copy()
        X = X.fillna(X.median())
        X = X.replace([np.inf, -np.inf], 0)

        # Fit the StandardScaler for feature normalization
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train the Isolation Forest
        # contamination=0.1 means we expect ~10% of data to be anomalous
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.is_fitted = True

        # Persist models to disk
        joblib.dump(self.model, ANOMALY_MODEL_PATH)
        joblib.dump(self.scaler, ANOMALY_SCALER_PATH)

        return {
            "status": "trained",
            "samples": len(features_df),
            "features": list(X.columns),
        }

    def detect(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check whether a new feature vector represents anomalous behavior.

        The Isolation Forest assigns an anomaly score where:
          - Negative scores indicate anomalies (more negative = more anomalous)
          - Positive scores indicate normal behavior
          - The decision boundary is at 0

        We normalize the raw score to a 0–1 risk scale for consistency
        with other risk components.

        Args:
            features_df: Single-row DataFrame of behavioral features.

        Returns:
            Dict with anomaly status, raw score, and normalized risk.
        """
        # Graceful fallback if the model hasn't been trained yet
        if not self.is_fitted or self.model is None or self.scaler is None:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "normalized_risk": 0.0,
                "status": "insufficient_data",
            }

        try:
            # Prepare the feature vector
            X = features_df.select_dtypes(include=[np.number]).copy()
            X = X.fillna(0)
            X = X.replace([np.inf, -np.inf], 0)

            # Ensure column alignment with training data
            expected_features = self.scaler.feature_names_in_
            for col in expected_features:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[expected_features]

            # Scale and predict
            X_scaled = self.scaler.transform(X)

            # IsolationForest.predict: 1 = normal, -1 = anomaly
            prediction = self.model.predict(X_scaled)[0]
            # decision_function: more negative = more anomalous
            raw_score = self.model.decision_function(X_scaled)[0]

            is_anomaly = bool(prediction == -1)

            # Normalize raw score to [0, 1] risk scale
            # Raw scores typically range from -0.5 to 0.5
            # We invert and scale: negative → high risk, positive → low risk
            normalized_risk = float(max(0.0, min(1.0, 0.5 - raw_score)))

            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": float(raw_score),
                "normalized_risk": round(normalized_risk, 4),
                "status": "analyzed",
            }

        except Exception as e:
            # Never crash the pipeline — return safe defaults on error
            print(f"[AnomalyDetector] Error during detection: {e}")
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "normalized_risk": 0.0,
                "status": f"error: {str(e)}",
            }
