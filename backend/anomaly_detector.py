"""
anomaly_detector.py — Behavioral anomaly detection using Isolation Forest.

v2 improvements:
  - Per-user personal models: after 14 days of data, a user-specific
    IsolationForest is trained on their own history. This answers
    "is today unusual *for you*?" rather than "is today unusual for a
    synthetic population?" — a far more clinically meaningful question.
  - Population model retained as fallback for new users (<14 days).
  - Personal models are persisted to disk with a user-prefixed filename
    and cached in memory across requests.
"""

import logging
import os
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ANOMALY_MODEL_PATH  = os.path.join(MODELS_DIR, "anomaly_model.pkl")
ANOMALY_SCALER_PATH = os.path.join(MODELS_DIR, "anomaly_scaler.pkl")
DATA_ANOMALY_MODEL_PATH  = os.path.join(DATA_DIR, "anomaly_detector.pkl")
DATA_ANOMALY_SCALER_PATH = os.path.join(DATA_DIR, "anomaly_scaler.pkl")

MIN_DAYS_FOR_PERSONAL_MODEL = 14  # minimum personal history before we trust a per-user model


class BehavioralAnomalyDetector:
    """
    Behavioral anomaly detection with per-user personalization.

    Population model (always available):
        Trained on synthetic data. Answers "is this person's behaviour
        unusual compared to a typical person?"

    Personal model (available after MIN_DAYS_FOR_PERSONAL_MODEL check-ins):
        Trained on this specific user's own history. Answers "is today
        unusual *compared to how this person usually behaves*?" — a much
        stronger signal. Cached in memory and on disk.
    """

    # Class-level in-memory cache: user_id → {model, scaler}
    _user_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.model:  Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler]  = None
        self.is_fitted = False

        # Load population-level model
        candidate_pairs = [
            (DATA_ANOMALY_MODEL_PATH,  DATA_ANOMALY_SCALER_PATH),
            (ANOMALY_MODEL_PATH, ANOMALY_SCALER_PATH),
        ]
        for model_path, scaler_path in candidate_pairs:
            if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
                continue
            try:
                self.model  = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.is_fitted = True
                logger.info("Loaded population anomaly model from %s", model_path)
                break
            except Exception as exc:
                logger.warning("Could not load anomaly model from %s: %s", model_path, exc)

    # ------------------------------------------------------------------
    # Population model training (called during startup on synthetic data)
    # ------------------------------------------------------------------

    def fit(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Train the population-level Isolation Forest."""
        if features_df is None or len(features_df) < 5:
            return {
                "status":  "insufficient_data",
                "message": "Need at least 5 samples.",
                "samples": len(features_df) if features_df is not None else 0,
            }

        X = self._clean(features_df)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=150,
            contamination=0.1,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.is_fitted = True

        joblib.dump(self.model,  ANOMALY_MODEL_PATH)
        joblib.dump(self.scaler, ANOMALY_SCALER_PATH)

        return {"status": "trained", "samples": len(features_df), "features": list(X.columns)}

    # ------------------------------------------------------------------
    # Per-user personal model training
    # ------------------------------------------------------------------

    def fit_for_user(
        self,
        user_id: str,
        user_history_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Train a personal anomaly model on a specific user's own history.

        Should be called asynchronously (e.g. via asyncio.to_thread) when the
        user reaches MIN_DAYS_FOR_PERSONAL_MODEL check-ins. The personal model
        is then used in subsequent detect() calls for this user.

        Args:
            user_id:         Unique user identifier.
            user_history_df: DataFrame of this user's check-ins (feature columns).

        Returns:
            Status dict with training result.
        """
        if user_history_df is None or len(user_history_df) < MIN_DAYS_FOR_PERSONAL_MODEL:
            return {
                "status":   "insufficient_data",
                "user_id":  user_id,
                "days":     len(user_history_df) if user_history_df is not None else 0,
                "required": MIN_DAYS_FOR_PERSONAL_MODEL,
            }

        X = self._clean(user_history_df)
        if X.empty:
            return {"status": "no_numeric_features", "user_id": user_id}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Higher contamination for personal models — individual variation is
        # expected to be tighter than population-level variation.
        personal_model = IsolationForest(
            n_estimators=100,
            contamination=0.08,
            random_state=42,
        )
        personal_model.fit(X_scaled)

        # Persist to disk
        model_path  = self._personal_model_path(user_id)
        scaler_path = self._personal_scaler_path(user_id)
        joblib.dump(personal_model, model_path)
        joblib.dump(scaler,         scaler_path)

        # Update in-memory cache
        BehavioralAnomalyDetector._user_cache[user_id] = {
            "model":  personal_model,
            "scaler": scaler,
        }

        logger.info(
            "anomaly_detector.personal_model_trained user=%s days=%d",
            user_id, len(user_history_df),
        )
        return {
            "status":  "trained",
            "user_id": user_id,
            "days":    len(user_history_df),
        }

    def load_personal_model(self, user_id: str) -> bool:
        """
        Load a user's personal model from disk into the in-memory cache.
        Returns True if successful.
        """
        if user_id in BehavioralAnomalyDetector._user_cache:
            return True   # already cached

        model_path  = self._personal_model_path(user_id)
        scaler_path = self._personal_scaler_path(user_id)

        if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
            return False

        try:
            BehavioralAnomalyDetector._user_cache[user_id] = {
                "model":  joblib.load(model_path),
                "scaler": joblib.load(scaler_path),
            }
            logger.info("Loaded personal anomaly model for user=%s", user_id)
            return True
        except Exception as exc:
            logger.warning("Could not load personal model for %s: %s", user_id, exc)
            return False

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(
        self,
        features_df: pd.DataFrame,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect whether a new feature vector is anomalous.

        If user_id is provided and a personal model is available, it is
        used instead of (and as a complement to) the population model.
        The result includes a flag indicating which model was used.

        Args:
            features_df: Single-row DataFrame of behavioral features.
            user_id:     Optional user identifier for personal model lookup.

        Returns:
            Dict with is_anomaly, normalized_risk, anomaly_score, model_used.
        """
        personal_available = False
        if user_id:
            personal_available = self.load_personal_model(user_id)

        if personal_available:
            return self._detect_with(
                features_df,
                BehavioralAnomalyDetector._user_cache[user_id]["model"],
                BehavioralAnomalyDetector._user_cache[user_id]["scaler"],
                model_used="personal",
            )

        if not self.is_fitted or self.model is None or self.scaler is None:
            return {
                "is_anomaly":      False,
                "anomaly_score":   0.0,
                "normalized_risk": 0.0,
                "model_used":      "none",
                "status":          "insufficient_data",
            }

        return self._detect_with(features_df, self.model, self.scaler, model_used="population")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _detect_with(
        self,
        features_df: pd.DataFrame,
        model: IsolationForest,
        scaler: StandardScaler,
        model_used: str,
    ) -> Dict[str, Any]:
        try:
            X = self._clean(features_df)
            expected = scaler.feature_names_in_
            for col in expected:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[expected]

            X_scaled   = scaler.transform(X)
            prediction = model.predict(X_scaled)[0]       # 1=normal, -1=anomaly
            raw_score  = model.decision_function(X_scaled)[0]
            is_anomaly = bool(prediction == -1)

            # Normalize: raw score typically in [-0.5, 0.5]; invert so that
            # negative (anomalous) scores map to high risk.
            normalized_risk = float(max(0.0, min(1.0, 0.5 - raw_score)))

            return {
                "is_anomaly":      is_anomaly,
                "anomaly_score":   float(raw_score),
                "normalized_risk": round(normalized_risk, 4),
                "model_used":      model_used,
                "status":          "analyzed",
            }
        except Exception as exc:
            logger.exception("Anomaly detection failed: %s", exc)
            return {
                "is_anomaly":      False,
                "anomaly_score":   0.0,
                "normalized_risk": 0.0,
                "model_used":      model_used,
                "status":          f"error: {exc}",
            }

    @staticmethod
    def _clean(df: pd.DataFrame) -> pd.DataFrame:
        X = df.select_dtypes(include=[np.number]).copy()
        return X.fillna(X.median()).replace([np.inf, -np.inf], 0)

    @staticmethod
    def _personal_model_path(user_id: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in user_id)
        return os.path.join(MODELS_DIR, f"anomaly_personal_{safe}.pkl")

    @staticmethod
    def _personal_scaler_path(user_id: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in user_id)
        return os.path.join(MODELS_DIR, f"anomaly_scaler_{safe}.pkl")
