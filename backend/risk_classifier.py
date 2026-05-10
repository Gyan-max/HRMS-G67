"""
risk_classifier.py — XGBoost-based multi-class risk classification.

Trains an XGBoost classifier to predict risk levels (LOW=0, MEDIUM=1, HIGH=2)
from behavioral feature vectors. Acts as the ML-based risk predictor,
complementing the rule-based RiskScoringEngine.
"""

import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, Optional

# Directory for persisting trained models
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

CLASSIFIER_MODEL_PATH = os.path.join(MODELS_DIR, "risk_classifier.pkl")
CLASSIFIER_SCALER_PATH = os.path.join(MODELS_DIR, "risk_classifier_scaler.pkl")

# Label mapping
RISK_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}


class RiskClassifier:
    """
    Multi-class risk classifier using XGBoost.

    Predicts behavioral health risk levels (LOW / MEDIUM / HIGH) from
    engineered feature vectors. The model is trained on synthetic data
    and fine-tuned to balance sensitivity with specificity.

    Design choices:
      - XGBoost: Handles mixed feature types, missing values, and
        non-linear relationships well.
      - max_depth=4: Prevents overfitting on small datasets.
      - learning_rate=0.1: Moderate learning rate for stable convergence.
      - n_estimators=200: Enough trees for complex patterns.

    Usage::

        classifier = RiskClassifier()
        classifier.train(X_train, y_train)
        result = classifier.predict(X_test_row)
        # result["predicted_class"]  → 2  (HIGH)
        # result["probabilities"]    → {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80}
    """

    def __init__(self):
        """
        Initialize the classifier, loading saved models if available.
        """
        self.model = None
        self.scaler = None
        self.is_fitted = False

        if os.path.exists(CLASSIFIER_MODEL_PATH) and os.path.exists(CLASSIFIER_SCALER_PATH):
            try:
                self.model = joblib.load(CLASSIFIER_MODEL_PATH)
                self.scaler = joblib.load(CLASSIFIER_SCALER_PATH)
                self.is_fitted = True
            except Exception as e:
                print(f"[RiskClassifier] Warning: Could not load saved models: {e}")
                self.is_fitted = False

    def train(self, X_df: pd.DataFrame, y_series: pd.Series) -> Dict[str, Any]:
        """
        Train the XGBoost classifier on labeled feature data.

        Args:
            X_df: Feature DataFrame (rows = samples, cols = features).
            y_series: Target labels (0=LOW, 1=MEDIUM, 2=HIGH).

        Returns:
            Dict with training status, accuracy, and class distribution.
        """
        if X_df is None or len(X_df) < 10:
            return {
                "status": "insufficient_data",
                "message": "Need at least 10 samples to train classifier.",
            }

        # Clean the feature matrix
        X = X_df.select_dtypes(include=[np.number]).copy()
        X = X.fillna(X.median())
        X = X.replace([np.inf, -np.inf], 0)

        y = y_series.astype(int).values

        # Fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train XGBoost with multi-class softmax objective
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            use_label_encoder=False,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        # Persist models
        joblib.dump(self.model, CLASSIFIER_MODEL_PATH)
        joblib.dump(self.scaler, CLASSIFIER_SCALER_PATH)

        # Compute training accuracy for reporting
        train_pred = self.model.predict(X_scaled)
        accuracy = float(np.mean(train_pred == y))

        # Class distribution
        unique, counts = np.unique(y, return_counts=True)
        class_dist = {RISK_LABELS.get(int(u), str(u)): int(c) for u, c in zip(unique, counts)}

        return {
            "status": "trained",
            "samples": len(X_df),
            "features": list(X.columns),
            "training_accuracy": round(accuracy, 4),
            "class_distribution": class_dist,
        }

    def predict(self, features_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Predict the risk class for a single feature vector.

        Args:
            features_df: Single-row DataFrame of behavioral features.

        Returns:
            Dict with predicted class, probabilities, and confidence.
            Returns None if the model hasn't been trained yet, signaling
            the risk engine to fall back to rule-based scoring.
        """
        if not self.is_fitted or self.model is None or self.scaler is None:
            return None

        try:
            # Prepare feature vector
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

            predicted_class = int(self.model.predict(X_scaled)[0])
            probabilities = self.model.predict_proba(X_scaled)[0]

            # Build probability dict
            prob_dict = {
                RISK_LABELS[i]: round(float(probabilities[i]), 4)
                for i in range(len(probabilities))
            }

            # Confidence = probability of the predicted class
            confidence = float(probabilities[predicted_class])

            return {
                "predicted_class": predicted_class,
                "predicted_label": RISK_LABELS[predicted_class],
                "probabilities": prob_dict,
                "confidence": round(confidence, 4),
                "status": "predicted",
            }

        except Exception as e:
            print(f"[RiskClassifier] Error during prediction: {e}")
            return None
