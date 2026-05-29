"""
main.py — FastAPI application for the Behavioral Health Risk Monitoring System v2.

Pipeline (per check-in):
  1. Log raw check-in to DB
  2. Extract enriched feature vector (26+ features, 7-day window)
  3. Safety screen on journal text
  4. NLP emotion analysis (7-class emotion model)
  5. Anomaly detection — personal model if available, population otherwise
  6. XGBoost risk classification with calibrated probabilities
  7. Rule-based weighted risk scoring + personalized insight generation
  8. ML blending (60% rule / 40% ML, skipped on safety override)
  9. SHAP feature contributions for explainability
 10. Early-warning pattern scan over 14-day history
 11. Persist risk result; return full response
"""

import asyncio
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, get_db
from logging_config import configure_logging
from schemas import (
    CheckInRequest, CheckInResponse,
    HealthCheckResponse,
    HistoryResponse, CheckInRecord,
    RiskTrendResponse, RiskTrendPoint,
    UserStatsResponse,
    EarlyWarningResponse, EarlyWarningItem,
)
from data_ingestion import (
    log_checkin, update_checkin_risk,
    get_user_history, get_user_history_records,
    get_days_tracked, get_all_users, delete_user_data,
)
from feature_engineering import extract_features, get_feature_names
from nlp_analyzer import MentalHealthNLPAnalyzer
from anomaly_detector import BehavioralAnomalyDetector
from risk_classifier import RiskClassifier
from risk_engine import RiskScoringEngine
from safety_screen import run_safety_screen
from early_warning import detect_early_warnings

configure_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global ML components
# ---------------------------------------------------------------------------
nlp_analyzer:    Optional[MentalHealthNLPAnalyzer]  = None
anomaly_detector: Optional[BehavioralAnomalyDetector] = None
risk_classifier: Optional[RiskClassifier]           = None
risk_engine:     Optional[RiskScoringEngine]        = None
models_loaded:   bool                               = False


def _enrich_features_with_nlp(features_df: pd.DataFrame, nlp_result: dict) -> pd.DataFrame:
    enriched = features_df.copy()
    enriched["nlp_risk_score"]         = float(nlp_result.get("nlp_risk_score",         0.0) or 0.0)
    enriched["first_person_ratio"]     = float(nlp_result.get("first_person_ratio",     0.0) or 0.0)
    enriched["absolutist_ratio"]       = float(nlp_result.get("absolutist_ratio",       0.0) or 0.0)
    enriched["negative_emotion_ratio"] = float(nlp_result.get("negative_emotion_ratio", 0.0) or 0.0)
    return enriched


def _train_models_if_needed():
    global anomaly_detector, risk_classifier

    synthetic_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic_training_data.csv"
    )
    if not os.path.exists(synthetic_path):
        logger.warning("No synthetic training data at %s; run generate_synthetic_data.py", synthetic_path)
        return

    logger.info("Loading synthetic training data from %s", synthetic_path)
    data = pd.read_csv(synthetic_path)

    feature_cols      = get_feature_names()
    available_cols    = [c for c in feature_cols if c in data.columns]
    if not available_cols:
        logger.warning("No matching feature columns in synthetic data.")
        return

    X = data[available_cols]
    y = data["risk_label"] if "risk_label" in data.columns else None

    if not anomaly_detector.is_fitted:
        logger.info("Training population anomaly detector…")
        result = anomaly_detector.fit(X)
        logger.info("Anomaly detector: %s", result)

    if y is not None and not risk_classifier.is_fitted:
        logger.info("Training risk classifier…")
        result = risk_classifier.train(X, y)
        logger.info(
            "Risk classifier trained — CV F1-macro: %.4f ± %.4f",
            result.get("cv_f1_macro_mean", 0),
            result.get("cv_f1_macro_std", 0),
        )


async def _maybe_train_personal_anomaly_model(user_id: str, db: Session) -> None:
    """
    Asynchronously train (or refresh) a per-user anomaly model once the user
    has accumulated at least MIN_DAYS_FOR_PERSONAL_MODEL check-ins.
    Runs in a thread pool so it doesn't block the event loop.
    """
    from anomaly_detector import MIN_DAYS_FOR_PERSONAL_MODEL
    history = get_user_history(db, user_id, days=90)
    if len(history) < MIN_DAYS_FOR_PERSONAL_MODEL:
        return

    feature_cols   = get_feature_names()
    available_cols = [c for c in feature_cols if c in history.columns]
    if not available_cols:
        return

    user_features = history[available_cols]
    await asyncio.to_thread(
        anomaly_detector.fit_for_user, user_id, user_features
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global nlp_analyzer, anomaly_detector, risk_classifier, risk_engine, models_loaded

    logger.info("Behavioral Health Risk Monitor v2 — starting up")
    create_tables()

    nlp_analyzer     = MentalHealthNLPAnalyzer()
    anomaly_detector = BehavioralAnomalyDetector()
    risk_classifier  = RiskClassifier()
    risk_engine      = RiskScoringEngine()

    await asyncio.to_thread(_train_models_if_needed)

    models_loaded = True
    logger.info("All components ready")
    yield
    logger.info("Behavioral Health Risk Monitor stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Behavioral Health Risk Monitor API v2",
    description=(
        "AI-powered behavioral health risk assessment — emotion NLP, per-user "
        "anomaly detection, SHAP explainability, and early-warning pattern detection."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

_default_origins = (
    "http://localhost:8501,http://127.0.0.1:8501,"
    "http://localhost:5173,http://127.0.0.1:5173"
)
_cors_origins_env = os.environ.get("BHRM_CORS_ORIGINS", _default_origins)
_cors_origins     = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=("*" not in _cors_origins),
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ===========================================================================
# ROUTES
# ===========================================================================

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    return HealthCheckResponse(status="healthy", version="2.0.0", models_loaded=models_loaded)


@app.post("/api/checkin", response_model=CheckInResponse, tags=["Check-In"])
async def submit_checkin(request: CheckInRequest, db: Session = Depends(get_db)):
    """
    Submit a daily check-in and receive a full risk assessment with:
    - 7-class emotion analysis of journal text
    - Per-user or population anomaly detection
    - SHAP feature contributions (top-8)
    - Data-driven personalized observations
    - Early-warning pattern scan
    """
    # 1. Log check-in
    checkin = log_checkin(
        db=db,
        user_id=request.user_id,
        sleep_hours=request.sleep_hours,
        mood_score=request.mood_score,
        activity_level=request.activity_level.lower(),
        social_interactions=request.social_interactions,
        journal_text=request.journal_text,
    )

    # 2. Feature extraction (7-day window)
    history_7    = get_user_history(db, request.user_id, days=7)
    features_df  = extract_features(history_7)
    features_dict = features_df.iloc[0].to_dict() if len(features_df) > 0 else {}

    # 3. Safety screen first — may short-circuit the weighted score
    safety_result = run_safety_screen(request.journal_text)
    if safety_result.triggered:
        logger.warning(
            "checkin.safety_triggered user=%s phrases=%s",
            request.user_id, safety_result.matched_phrases,
        )

    # 4. NLP emotion analysis
    nlp_result    = nlp_analyzer.analyze(request.journal_text)
    nlp_risk      = nlp_result.get("nlp_risk_score", 0.0)
    nlp_available = nlp_result.get("status") == "analyzed"
    model_features_df = _enrich_features_with_nlp(features_df, nlp_result)

    # 5. Anomaly detection (personal model preferred)
    anomaly_result    = anomaly_detector.detect(model_features_df, user_id=request.user_id)
    anomaly_risk      = anomaly_result.get("normalized_risk", 0.0)
    anomaly_available = anomaly_result.get("status") == "analyzed"
    anomaly_model_used = anomaly_result.get("model_used")

    # 6. XGBoost classification
    ml_prediction = risk_classifier.predict(model_features_df)

    # 7. Weighted rule-based scoring + personalized observations
    risk_result = risk_engine.compute_final_risk(
        nlp_score=nlp_risk,
        anomaly_score=anomaly_risk,
        features_dict=features_dict,
        nlp_available=nlp_available,
        anomaly_available=anomaly_available,
        safety_override=safety_result.triggered,
        safety_matched_phrases=safety_result.matched_phrases,
    )

    # 8. ML blending (skipped on safety override)
    if ml_prediction is not None and not safety_result.triggered:
        ml_risk_score = (
            ml_prediction["probabilities"].get("HIGH", 0.0) * 0.5
            + ml_prediction["probabilities"].get("MEDIUM", 0.0) * 0.25
        )
        blended = round(max(0.0, min(1.0, 0.6 * risk_result["final_score"] + 0.4 * ml_risk_score)), 4)

        if blended >= 0.65:
            risk_result["risk_level"]  = "HIGH"
            risk_result["color_code"]  = "#ff4444"
        elif blended >= 0.35:
            risk_result["risk_level"]  = "MEDIUM"
            risk_result["color_code"]  = "#ffaa00"
        else:
            risk_result["risk_level"]  = "LOW"
            risk_result["color_code"]  = "#00cc66"
        risk_result["final_score"] = blended

    # 9. SHAP explainability (non-blocking; returns None if unavailable)
    shap_contributions = risk_classifier.explain_prediction(model_features_df)

    # 10. Early-warning pattern scan (14-day history)
    history_14    = get_user_history(db, request.user_id, days=14)
    raw_warnings  = detect_early_warnings(history_14, window=14)
    early_warnings = [w.to_dict() for w in raw_warnings]

    # 10b. Trigger async per-user anomaly model refresh (fire-and-forget)
    asyncio.create_task(
        _maybe_train_personal_anomaly_model(request.user_id, db)
    )

    # 11. Persist risk result
    update_checkin_risk(
        db=db,
        checkin_id=checkin.id,
        risk_score=risk_result["final_score"],
        risk_level=risk_result["risk_level"],
    )

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
        # v2
        observations=risk_result.get("observations", []),
        shap_contributions=shap_contributions,
        early_warnings=early_warnings,
        anomaly_model_used=anomaly_model_used,
    )


@app.get("/api/history/{user_id}", response_model=HistoryResponse, tags=["History"])
async def get_history(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    records = get_user_history_records(db, user_id, days=days)
    return HistoryResponse(
        user_id=user_id,
        total_records=len(records),
        records=[CheckInRecord(**r) for r in records],
    )


@app.get("/api/stats/{user_id}", response_model=UserStatsResponse, tags=["Analytics"])
async def get_stats(user_id: str, db: Session = Depends(get_db)):
    history = get_user_history(db, user_id, days=365)
    if len(history) == 0:
        return UserStatsResponse(
            user_id=user_id, avg_risk=0.0, trend_direction="STABLE", total_days=0,
        )

    avg_risk = float(history["risk_score"].mean()) if history["risk_score"].notna().any() else 0.0
    highest_risk_day = None
    if history["risk_score"].notna().any():
        highest_risk_day = history.loc[history["risk_score"].idxmax(), "timestamp"]

    recent = history.tail(7)
    trend_direction = "STABLE"
    if len(recent) >= 3 and recent["risk_score"].notna().any():
        vals = recent["risk_score"].dropna().values
        if len(vals) >= 3:
            mid = len(vals) // 2
            diff = vals[mid:].mean() - vals[:mid].mean()
            if diff > 0.05:      trend_direction = "WORSENING"
            elif diff < -0.05:   trend_direction = "IMPROVING"

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
    history = get_user_history(db, user_id, days=days)
    data_points = [
        RiskTrendPoint(timestamp=row["timestamp"], risk_score=float(row["risk_score"]))
        for _, row in history.iterrows()
        if pd.notna(row.get("risk_score")) and pd.notna(row.get("timestamp"))
    ]
    return RiskTrendResponse(user_id=user_id, data_points=data_points)


@app.get("/api/early-warning/{user_id}", response_model=EarlyWarningResponse, tags=["Analytics"])
async def get_early_warnings(
    user_id: str,
    days: int = Query(default=14, ge=7, le=30, description="History window to scan"),
    db: Session = Depends(get_db),
):
    """
    Scan the user's recent check-in history for multi-day warning patterns
    that a single-day risk score can miss (declining streaks, sleep debt,
    multi-signal crisis, accelerating deterioration, etc.).
    """
    history  = get_user_history(db, user_id, days=days)
    warnings = detect_early_warnings(history, window=days)
    return EarlyWarningResponse(
        user_id=user_id,
        days_scanned=days,
        warning_count=len(warnings),
        warnings=[EarlyWarningItem(**w.to_dict()) for w in warnings],
    )


@app.delete("/api/user/{user_id}", tags=["User Management"])
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Permanently delete all data for a user (GDPR-style)."""
    return delete_user_data(db, user_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
