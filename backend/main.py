"""
main.py — FastAPI application for the Behavioral Health Risk Monitoring System.

This is the central API server that orchestrates the full ML pipeline:
  1. Receive daily check-in data
  2. Extract behavioral features from history
  3. Run NLP analysis on journal text
  4. Detect behavioral anomalies
  5. Classify risk level (ML + rule-based)
  6. Return comprehensive risk assessment

All ML models are initialized on startup and trained on synthetic data
if no pre-trained models are found.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Ensure the backend package is importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, get_db
from logging_config import configure_logging
from schemas import (
    CheckInRequest,
    CheckInResponse,
    HealthCheckResponse,
    HistoryResponse,
    CheckInRecord,
    RiskTrendResponse,
    RiskTrendPoint,
    UserStatsResponse,
)
from data_ingestion import (
    log_checkin,
    update_checkin_risk,
    get_user_history,
    get_user_history_records,
    get_days_tracked,
    get_all_users,
    delete_user_data,
)
from feature_engineering import extract_features, get_feature_names
from nlp_analyzer import MentalHealthNLPAnalyzer
from anomaly_detector import BehavioralAnomalyDetector
from risk_classifier import RiskClassifier
from risk_engine import RiskScoringEngine
from safety_screen import run_safety_screen

configure_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global ML component instances (initialized once on startup)
# ---------------------------------------------------------------------------
nlp_analyzer: Optional[MentalHealthNLPAnalyzer] = None
anomaly_detector: Optional[BehavioralAnomalyDetector] = None
risk_classifier: Optional[RiskClassifier] = None
risk_engine: Optional[RiskScoringEngine] = None
models_loaded: bool = False


def _enrich_features_with_nlp(
    features_df: pd.DataFrame,
    nlp_result: dict,
) -> pd.DataFrame:
    """
    Add NLP feature columns expected by external 20-feature models.

    The legacy in-repo models use only engineered behavioral features, while
    externally trained artifacts in /data may also require NLP-derived columns.
    """
    enriched = features_df.copy()
    enriched["nlp_risk_score"] = float(nlp_result.get("nlp_risk_score", 0.0) or 0.0)
    enriched["first_person_ratio"] = float(nlp_result.get("first_person_ratio", 0.0) or 0.0)
    enriched["absolutist_ratio"] = float(nlp_result.get("absolutist_ratio", 0.0) or 0.0)
    enriched["negative_emotion_ratio"] = float(
        nlp_result.get("negative_emotion_ratio", 0.0) or 0.0
    )
    return enriched


def _train_models_if_needed():
    """
    Train ML models on synthetic data if no saved models exist.

    This ensures the system works out-of-the-box on first run without
    requiring manual training steps.
    """
    global anomaly_detector, risk_classifier

    synthetic_data_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "data", "synthetic_training_data.csv",
    )

    if not os.path.exists(synthetic_data_path):
        logger.warning(
            "No synthetic training data found at %s; models will use fallback mode.",
            synthetic_data_path,
        )
        logger.warning(
            "Run `python data/generate_synthetic_data.py` to create training data."
        )
        return

    logger.info("Loading synthetic training data...")
    data = pd.read_csv(synthetic_data_path)

    feature_cols = get_feature_names()
    # Use only columns that exist in both the data and feature list
    available_cols = [c for c in feature_cols if c in data.columns]

    if not available_cols:
        logger.warning("No matching feature columns in synthetic data.")
        return

    X = data[available_cols]
    y = data["risk_label"] if "risk_label" in data.columns else None

    # Train anomaly detector if not already fitted
    if not anomaly_detector.is_fitted:
        logger.info("Training anomaly detector on synthetic data...")
        result = anomaly_detector.fit(X)
        logger.info("Anomaly detector: %s", result)

    # Train risk classifier if not already fitted
    if y is not None and not risk_classifier.is_fitted:
        logger.info("Training risk classifier on synthetic data...")
        result = risk_classifier.train(X, y)
        logger.info("Risk classifier: %s", result)


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize database and ML components on startup.
    Cleanup resources on shutdown.
    """
    global nlp_analyzer, anomaly_detector, risk_classifier, risk_engine, models_loaded

    logger.info("Behavioral Health Risk Monitor — starting up")

    # Step 1: Create database tables
    logger.info("Initialising database...")
    create_tables()

    # Step 2: Initialize ML components
    logger.info("Loading NLP analyzer...")
    nlp_analyzer = MentalHealthNLPAnalyzer()

    logger.info("Loading anomaly detector...")
    anomaly_detector = BehavioralAnomalyDetector()

    logger.info("Loading risk classifier...")
    risk_classifier = RiskClassifier()

    logger.info("Initialising risk scoring engine...")
    risk_engine = RiskScoringEngine()

    # Step 3: Train models if no saved models found
    _train_models_if_needed()

    models_loaded = True
    logger.info("All components initialised successfully")

    yield  # Application runs

    # Shutdown
    logger.info("Behavioral Health Risk Monitor stopped")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Behavioral Health Risk Monitor API",
    description=(
        "AI-powered behavioral health risk assessment system that monitors "
        "daily behavioral signals and uses ML/NLP to detect early signs of "
        "mental health risks."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS configuration.
#
# The previous configuration combined `allow_origins=["*"]` with
# `allow_credentials=True`, which is invalid per the CORS spec — browsers
# refuse credentialed requests against a wildcard origin. We now allow a
# specific list of origins (overridable via the BHRM_CORS_ORIGINS env var,
# comma-separated) and only enable credentials when the origins are
# concrete.
# ---------------------------------------------------------------------------
_default_origins = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:5173,http://127.0.0.1:5173"
_cors_origins_env = os.environ.get("BHRM_CORS_ORIGINS", _default_origins)
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
_allow_credentials = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ===========================================================================
# API ROUTES
# ===========================================================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to the interactive API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    """Health check endpoint for uptime monitoring."""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        models_loaded=models_loaded,
    )


@app.post("/api/checkin", response_model=CheckInResponse, tags=["Check-In"])
async def submit_checkin(request: CheckInRequest, db: Session = Depends(get_db)):
    """
    Submit a daily behavioral check-in and receive a risk assessment.

    This endpoint runs the full ML pipeline:
      1. Log the check-in data to the database
      2. Extract behavioral features from the last 7 days of history
      3. Analyze journal text with NLP (sentiment + linguistic features)
      4. Run anomaly detection on the behavioral feature vector
      5. Predict risk level using XGBoost classifier
      6. Compute weighted risk score with the rule-based engine
      7. Update the database record with risk results
      8. Return the comprehensive assessment
    """
    # Validate activity level
    valid_levels = {"sedentary", "light", "moderate", "active"}
    if request.activity_level.lower() not in valid_levels:
        raise HTTPException(
            status_code=422,
            detail=f"activity_level must be one of: {', '.join(valid_levels)}",
        )

    # ------------------------------------------------------------------
    # Step 1: Log the check-in (risk fields updated later)
    # ------------------------------------------------------------------
    checkin = log_checkin(
        db=db,
        user_id=request.user_id,
        sleep_hours=request.sleep_hours,
        mood_score=request.mood_score,
        activity_level=request.activity_level.lower(),
        social_interactions=request.social_interactions,
        journal_text=request.journal_text,
    )

    # ------------------------------------------------------------------
    # Step 2: Extract behavioral features from 7-day history
    # ------------------------------------------------------------------
    history = get_user_history(db, request.user_id, days=7)
    features_df = extract_features(history)
    features_dict = features_df.iloc[0].to_dict() if len(features_df) > 0 else {}

    # ------------------------------------------------------------------
    # Step 3a: Safety screen — runs BEFORE the weighted scorer so that
    # explicit suicidal-ideation / self-harm content can force HIGH
    # regardless of how the other signals balance out.
    # ------------------------------------------------------------------
    safety_result = run_safety_screen(request.journal_text)
    if safety_result.triggered:
        logger.warning(
            "checkin.safety_triggered user=%s phrases=%s",
            request.user_id,
            safety_result.matched_phrases,
        )

    # ------------------------------------------------------------------
    # Step 3b: NLP analysis on journal text
    # ------------------------------------------------------------------
    nlp_result = nlp_analyzer.analyze(request.journal_text)
    nlp_risk = nlp_result.get("nlp_risk_score", 0.0)
    nlp_available = nlp_result.get("status") == "analyzed"
    model_features_df = _enrich_features_with_nlp(features_df, nlp_result)

    # ------------------------------------------------------------------
    # Step 4: Anomaly detection
    # ------------------------------------------------------------------
    anomaly_result = anomaly_detector.detect(model_features_df)
    anomaly_risk = anomaly_result.get("normalized_risk", 0.0)
    anomaly_available = anomaly_result.get("status") == "analyzed"

    # ------------------------------------------------------------------
    # Step 5: ML classifier prediction (may return None if not trained)
    # ------------------------------------------------------------------
    ml_prediction = risk_classifier.predict(model_features_df)

    # ------------------------------------------------------------------
    # Step 6: Rule-based weighted risk scoring (with safety override and
    # weight re-normalisation when components are unavailable).
    # ------------------------------------------------------------------
    risk_result = risk_engine.compute_final_risk(
        nlp_score=nlp_risk,
        anomaly_score=anomaly_risk,
        features_dict=features_dict,
        nlp_available=nlp_available,
        anomaly_available=anomaly_available,
        safety_override=safety_result.triggered,
        safety_matched_phrases=safety_result.matched_phrases,
    )

    # If the safety screen triggered, never let ML blending downgrade the
    # decision — we already pinned risk to HIGH and want to preserve that.
    safety_override_active = safety_result.triggered

    # If ML classifier is available, blend its output with rule-based score
    if ml_prediction is not None and not safety_override_active:
        ml_risk_score = ml_prediction["probabilities"].get("HIGH", 0.0) * 0.5 + \
                        ml_prediction["probabilities"].get("MEDIUM", 0.0) * 0.25
        # Blend: 60% rule-based, 40% ML
        blended_score = 0.6 * risk_result["final_score"] + 0.4 * ml_risk_score
        blended_score = round(max(0.0, min(1.0, blended_score)), 4)

        # Re-determine risk level from blended score
        if blended_score >= 0.65:
            risk_result["risk_level"] = "HIGH"
            risk_result["color_code"] = "#ff4444"
        elif blended_score >= 0.35:
            risk_result["risk_level"] = "MEDIUM"
            risk_result["color_code"] = "#ffaa00"
        else:
            risk_result["risk_level"] = "LOW"
            risk_result["color_code"] = "#00cc66"
        risk_result["final_score"] = blended_score

    # ------------------------------------------------------------------
    # Step 7: Update the database record with risk results
    # ------------------------------------------------------------------
    update_checkin_risk(
        db=db,
        checkin_id=checkin.id,
        risk_score=risk_result["final_score"],
        risk_level=risk_result["risk_level"],
    )

    # ------------------------------------------------------------------
    # Step 8: Build and return the response
    # ------------------------------------------------------------------
    days = get_days_tracked(db, request.user_id)

    return CheckInResponse(
        user_id=request.user_id,
        timestamp=checkin.timestamp,
        risk_level=risk_result["risk_level"],
        risk_score=risk_result["final_score"],
        component_scores=risk_result["component_scores"],
        recommendation=risk_result["recommendation"],
        nlp_analysis=nlp_result,
        anomaly_detected=anomaly_result.get("is_anomaly", False),
        days_tracked=days,
        dominant_factor=risk_result.get("dominant_factor"),
        color_code=risk_result.get("color_code"),
        safety_override=bool(risk_result.get("safety_override", False)),
    )


@app.get("/api/history/{user_id}", response_model=HistoryResponse, tags=["History"])
async def get_history(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to retrieve"),
    db: Session = Depends(get_db),
):
    """Retrieve check-in history for a user over the specified number of days."""
    records = get_user_history_records(db, user_id, days=days)
    return HistoryResponse(
        user_id=user_id,
        total_records=len(records),
        records=[CheckInRecord(**r) for r in records],
    )


@app.get("/api/stats/{user_id}", response_model=UserStatsResponse, tags=["Analytics"])
async def get_stats(user_id: str, db: Session = Depends(get_db)):
    """Get aggregate statistics and trend information for a user."""
    history = get_user_history(db, user_id, days=365)

    if len(history) == 0:
        return UserStatsResponse(
            user_id=user_id,
            avg_risk=0.0,
            highest_risk_day=None,
            trend_direction="STABLE",
            total_days=0,
        )

    # Compute aggregate stats
    avg_risk = float(history["risk_score"].mean()) if history["risk_score"].notna().any() else 0.0

    # Find highest risk day
    highest_risk_day = None
    if history["risk_score"].notna().any():
        max_idx = history["risk_score"].idxmax()
        highest_risk_day = history.loc[max_idx, "timestamp"]

    # Determine trend direction from last 7 entries
    recent = history.tail(7)
    if len(recent) >= 3 and recent["risk_score"].notna().any():
        risk_values = recent["risk_score"].dropna().values
        if len(risk_values) >= 3:
            first_half = risk_values[:len(risk_values) // 2].mean()
            second_half = risk_values[len(risk_values) // 2:].mean()
            diff = second_half - first_half
            if diff > 0.05:
                trend_direction = "WORSENING"
            elif diff < -0.05:
                trend_direction = "IMPROVING"
            else:
                trend_direction = "STABLE"
        else:
            trend_direction = "STABLE"
    else:
        trend_direction = "STABLE"

    # Count consecutive LOW risk days (streak)
    low_risk_streak = 0
    for _, row in history.iloc[::-1].iterrows():
        if row.get("risk_level") == "LOW":
            low_risk_streak += 1
        else:
            break

    return UserStatsResponse(
        user_id=user_id,
        avg_risk=round(avg_risk, 4),
        highest_risk_day=highest_risk_day,
        trend_direction=trend_direction,
        total_days=len(history),
        avg_sleep=round(float(history["sleep_hours"].mean()), 2) if "sleep_hours" in history else None,
        avg_mood=round(float(history["mood_score"].mean()), 2) if "mood_score" in history else None,
        avg_social=round(float(history["social_interactions"].mean()), 2) if "social_interactions" in history else None,
        low_risk_streak=low_risk_streak,
    )


@app.get("/api/risk-trend/{user_id}", response_model=RiskTrendResponse, tags=["Analytics"])
async def get_risk_trend(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Return time-series risk score data for charting."""
    history = get_user_history(db, user_id, days=days)

    data_points = []
    for _, row in history.iterrows():
        if pd.notna(row.get("risk_score")) and pd.notna(row.get("timestamp")):
            data_points.append(RiskTrendPoint(
                timestamp=row["timestamp"],
                risk_score=float(row["risk_score"]),
            ))

    return RiskTrendResponse(user_id=user_id, data_points=data_points)


@app.delete("/api/user/{user_id}", tags=["User Management"])
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Permanently delete all data for a user (GDPR-style).

    This action is irreversible and removes all check-in records
    and the user profile.
    """
    result = delete_user_data(db, user_id)
    return result


# ===========================================================================
# Entry point for direct execution
# ===========================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
