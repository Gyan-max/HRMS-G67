"""
schemas.py — Pydantic request / response models for the FastAPI endpoints.

All data flowing into and out of the API is validated through these schemas,
ensuring consistent types, ranges, and documentation for the OpenAPI spec.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ===========================================================================
# REQUEST MODELS
# ===========================================================================

class CheckInRequest(BaseModel):
    """
    Payload submitted by the user (or frontend) for a daily check-in.

    Attributes:
        user_id: Unique identifier for the user (e.g. "user_001").
        sleep_hours: Hours of sleep last night (0.0–12.0).
        mood_score: Self-rated mood on a 1–10 Likert scale.
        activity_level: Physical activity category for the day.
        social_interactions: Count of meaningful social contacts (0–30).
        journal_text: Optional free-text journal entry for NLP analysis.
    """
    user_id: str = Field(..., min_length=1, max_length=64, description="Unique user identifier")
    sleep_hours: float = Field(..., ge=0.0, le=12.0, description="Hours of sleep (0-12)")
    mood_score: int = Field(..., ge=1, le=10, description="Mood rating 1-10")
    activity_level: str = Field(
        ...,
        description="Activity level: sedentary, light, moderate, or active",
    )
    social_interactions: int = Field(..., ge=0, le=30, description="Social interaction count (0-30)")
    journal_text: Optional[str] = Field(None, max_length=5000, description="Optional journal entry")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "sleep_hours": 5.5,
                "mood_score": 4,
                "activity_level": "sedentary",
                "social_interactions": 1,
                "journal_text": "Feeling really tired and disconnected today.",
            }
        }


# ===========================================================================
# RESPONSE MODELS
# ===========================================================================

class CheckInResponse(BaseModel):
    """
    Full risk assessment response returned after processing a check-in.

    Includes the computed risk score, all component sub-scores,
    NLP analysis results, anomaly detection status, and a human-readable
    recommendation string.
    """
    user_id: str
    timestamp: datetime
    risk_level: str = Field(..., description="LOW, MEDIUM, or HIGH")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Weighted risk score 0-1")
    component_scores: Dict[str, float] = Field(
        ..., description="Breakdown: sleep, mood, social, nlp, anomaly"
    )
    recommendation: str = Field(..., description="Actionable wellness recommendation")
    nlp_analysis: Dict[str, object] = Field(
        ..., description="Sentiment and linguistic analysis results"
    )
    anomaly_detected: bool = Field(..., description="Whether behavioral anomaly was flagged")
    days_tracked: int = Field(..., ge=0, description="Total days of data for this user")
    dominant_factor: Optional[str] = Field(None, description="Highest contributing risk factor")
    color_code: Optional[str] = Field(None, description="Hex color for risk level badge")
    safety_override: bool = Field(
        False,
        description=(
            "True when the safety screen detected suicidal-ideation / "
            "self-harm content in the journal text and forced the risk "
            "level to HIGH. The frontend should surface crisis resources "
            "prominently when this is true."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "timestamp": "2025-01-15T14:30:00",
                "risk_level": "MEDIUM",
                "risk_score": 0.52,
                "component_scores": {
                    "sleep": 0.6,
                    "mood": 0.5,
                    "social": 0.3,
                    "nlp": 0.7,
                    "anomaly": 0.4,
                },
                "recommendation": "Social withdrawal patterns are emerging...",
                "nlp_analysis": {
                    "sentiment_label": "NEGATIVE",
                    "sentiment_confidence": 0.85,
                },
                "anomaly_detected": False,
                "days_tracked": 5,
                "dominant_factor": "nlp",
                "color_code": "#ffaa00",
            }
        }


class CheckInRecord(BaseModel):
    """Single historical check-in row for the History endpoint."""
    id: int
    user_id: str
    timestamp: datetime
    sleep_hours: float
    mood_score: int
    activity_level: str
    social_interactions: int
    journal_text: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None


class HistoryResponse(BaseModel):
    """Paginated list of past check-in records for a user."""
    user_id: str
    total_records: int
    records: List[CheckInRecord]


class UserStatsResponse(BaseModel):
    """Aggregate statistics and trend information for a user."""
    user_id: str
    avg_risk: float = Field(..., description="Average risk score across all check-ins")
    highest_risk_day: Optional[datetime] = Field(None, description="Timestamp of peak risk")
    trend_direction: str = Field(
        ..., description="IMPROVING, STABLE, or WORSENING based on recent trend"
    )
    total_days: int = Field(..., ge=0, description="Total number of check-in days")
    avg_sleep: Optional[float] = None
    avg_mood: Optional[float] = None
    avg_social: Optional[float] = None
    low_risk_streak: int = Field(0, description="Consecutive recent days at LOW risk")


class RiskTrendPoint(BaseModel):
    """Single data point in a risk score time-series."""
    timestamp: datetime
    risk_score: float


class RiskTrendResponse(BaseModel):
    """Time-series of risk scores for charting."""
    user_id: str
    data_points: List[RiskTrendPoint]


class HealthCheckResponse(BaseModel):
    """Simple health check for uptime monitors."""
    status: str = "healthy"
    version: str = "1.0.0"
    models_loaded: bool = False
