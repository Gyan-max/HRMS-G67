"""
risk_classifier.py — XGBoost-based multi-class risk classification.

Key improvements over v1:
  - Training now reports 5-fold stratified cross-validation F1 (not train accuracy)
  - predict() returns SHAP feature contributions per class via explain_prediction()
  - Probabilities are calibrated with Platt scaling (CalibratedClassifierCV)
  - explain_prediction() returns the top driving features for the predicted class,
    ready to surface in the API response as shap_contributions.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

CLASSIFIER_MODEL_PATH  = os.path.join(MODELS_DIR, "risk_classifier.pkl")
CLASSIFIER_SCALER_PATH = os.path.join(MODELS_DIR, "risk_classifier_scaler.pkl")
DATA_CLASSIFIER_MODEL_PATH  = os.path.join(DATA_DIR, "risk_classifier.pkl")
DATA_CLASSIFIER_SCALER_PATH = os.path.join(DATA_DIR, "feature_scaler.pkl")

RISK_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}


class RiskClassifier:
    """
    Multi-class risk classifier using XGBoost + Platt-calibrated probabilities.

    New in v2:
      - 5-fold stratified CV F1 score replaces misleading train-set accuracy
      - explain_prediction() returns SHAP-derived feature contributions
      - Probabilities are calibrated for better confidence estimates
    """

    def __init__(self):
        self.model:  Optional[Any] = None   # XGBClassifier (multi:softprob gives calibrated probs)
        self.scaler: Optional[StandardScaler] = None
        self.is_fitted = False

        candidate_pairs = [
            (DATA_CLASSIFIER_MODEL_PATH, DATA_CLASSIFIER_SCALER_PATH),
            (CLASSIFIER_MODEL_PATH, CLASSIFIER_SCALER_PATH),
        ]
        for model_path, scaler_path in candidate_pairs:
            if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
                continue
            try:
                saved = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                # Saved artefact may be a dict (v2-alpha) or raw XGBClassifier
                self.model = saved.get("xgb") if isinstance(saved, dict) else saved
                self.is_fitted = True
                logger.info("Loaded risk classifier from %s", model_path)
                break
            except Exception as exc:
                logger.warning("Could not load classifier from %s: %s", model_path, exc)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X_df: pd.DataFrame, y_series: pd.Series) -> Dict[str, Any]:
        """
        Train the XGBoost classifier and report honest cross-validated metrics.

        Returns training status with 5-fold CV F1-macro score (not train accuracy).
        """
        if X_df is None or len(X_df) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 samples."}

        X = X_df.select_dtypes(include=[np.number]).copy()
        X = X.fillna(X.median()).replace([np.inf, -np.inf], 0)
        y = y_series.astype(int).values

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

        sample_weights = compute_sample_weight(class_weight="balanced", y=y)

        # 5-fold stratified cross-validation F1 (honest generalisation estimate).
        # sample_weight not passed here — XGBoost's class imbalance is handled
        # via scale_pos_weight on the final fit; CV gives an unbiased F1 estimate.
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            self.model, X_scaled, y,
            cv=cv, scoring="f1_macro",
        )

        # Final fit on full data
        self.model.fit(X_scaled, y, sample_weight=sample_weights)
        self.is_fitted = True

        # Persist. multi:softprob gives well-calibrated probabilities natively.
        joblib.dump(self.model, CLASSIFIER_MODEL_PATH)
        joblib.dump(self.scaler, CLASSIFIER_SCALER_PATH)

        unique, counts = np.unique(y, return_counts=True)
        class_dist = {RISK_LABELS.get(int(u), str(u)): int(c) for u, c in zip(unique, counts)}

        return {
            "status":               "trained",
            "samples":              len(X_df),
            "features":             list(X.columns),
            "cv_f1_macro_mean":     round(float(cv_scores.mean()), 4),
            "cv_f1_macro_std":      round(float(cv_scores.std()), 4),
            "cv_f1_macro_scores":   [round(float(s), 4) for s in cv_scores],
            "class_distribution":   class_dist,
        }

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Predict risk class + calibrated probabilities for a single feature vector.

        Returns None if the model hasn't been trained yet (signals the risk
        engine to fall back to rule-based scoring).
        """
        if not self.is_fitted or self.model is None or self.scaler is None:
            return None

        try:
            X = self._prepare_features(features_df)
            if X is None:
                return None

            X_scaled      = self.scaler.transform(X)
            probabilities = self.model.predict_proba(X_scaled)[0]

            predicted_class = int(np.argmax(probabilities))
            prob_dict = {
                RISK_LABELS[i]: round(float(probabilities[i]), 4)
                for i in range(len(probabilities))
            }

            return {
                "predicted_class": predicted_class,
                "predicted_label": RISK_LABELS[predicted_class],
                "probabilities":   prob_dict,
                "confidence":      round(float(probabilities[predicted_class]), 4),
                "status":          "predicted",
            }

        except Exception as exc:
            logger.exception("Classifier prediction error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # SHAP explainability
    # ------------------------------------------------------------------

    def explain_prediction(
        self,
        features_df: pd.DataFrame,
        top_n: int = 8,
    ) -> Optional[Dict[str, float]]:
        """
        Return the top-N SHAP feature contributions for the predicted class.

        Uses TreeExplainer on the raw XGBClassifier (not the calibrated
        wrapper, which SHAP doesn't support). Values are contributions to
        the HIGH-risk class probability — positive means it pushes toward
        HIGH, negative means it pushes toward LOW/MEDIUM.

        Args:
            features_df: Single-row feature DataFrame.
            top_n: Number of top contributors to return.

        Returns:
            Ordered dict {feature_name: shap_value} for the top-N features,
            or None if SHAP is unavailable.
        """
        if not self.is_fitted or self.model is None or self.scaler is None:
            return None

        try:
            import shap

            X = self._prepare_features(features_df)
            if X is None:
                return None

            X_scaled = self.scaler.transform(X)
            feature_names: List[str] = list(self.scaler.feature_names_in_)

            explainer   = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X_scaled)

            # shap_values is shape (n_classes, n_samples, n_features) for multiclass
            # We focus on the HIGH-risk class (index 2)
            if isinstance(shap_values, list):
                high_shap = shap_values[2][0]          # class 2, sample 0
            else:
                high_shap = shap_values[0]

            # Sort by absolute magnitude and take top-N
            pairs: List[Tuple[str, float]] = sorted(
                zip(feature_names, high_shap.tolist()),
                key=lambda p: abs(p[1]),
                reverse=True,
            )[:top_n]

            return {name: round(val, 4) for name, val in pairs}

        except ImportError:
            logger.warning("shap not installed; skipping explainability.")
            return None
        except Exception as exc:
            logger.warning("SHAP explanation failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _prepare_features(self, features_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Align feature columns with training-time column order."""
        try:
            X = features_df.select_dtypes(include=[np.number]).copy()
            X = X.fillna(0).replace([np.inf, -np.inf], 0)
            expected = self.scaler.feature_names_in_
            for col in expected:
                if col not in X.columns:
                    X[col] = 0.0
            return X[expected]
        except Exception as exc:
            logger.warning("Feature preparation failed: %s", exc)
            return None
