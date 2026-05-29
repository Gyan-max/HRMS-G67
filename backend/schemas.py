"""
schemas.py — Pydantic request / response models for the FastAPI endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ===========================================================================
# REQUEST MODELS
# ===========================================================================

class CheckInRequest(BaseModel):
    user_id:             str   = Field(..., min_length=1, max_length=64)
    sleep_hours:         float = Field(..., ge=0.0, le=12.0)
    mood_score:          int   = Field(..., ge=1, le=10)
    activity_level: Literal["sedentary", "light", "moderate", "active"] = Field(...)
    social_interactions: int   = Field(..., ge=0, le=30)
    journal_text:        Optional[str] = Field(None, max_length=5000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_001",
                "sleep_hours": 5.5,
                "mood_score": 4,
                "activity_level": "sedentary",
                "social_interactions": 1,
                "journal_text": "Feeling really tired and disconnected today.",
            }
        }
    }


# ===========================================================================
# RESPONSE MODELS
# ===========================================================================

class CheckInResponse(BaseModel):
    """Full risk assessment returned after processing a check-in."""
    user_id:          str
    timestamp:        datetime
    risk_level:       str   = Field(..., description="LOW, MEDIUM, or HIGH")
    risk_score:       float = Field(..., ge=0.0, le=1.0)
    component_scores: Dict[str, float] = Field(
        ..., description="Breakdown: sleep, mood, social, nlp, anomaly"
    )
    recommendation:   str
    nlp_analysis:     Dict[str, Any]
    anomaly_detected: bool
    days_tracked:     int = Field(..., ge=0)
    dominant_factor:  Optional[str] = None
    color_code:       Optional[str] = None
    safety_override:  bool = False

    # v2 additions
    observations:       List[str]            = Field(
        default_factory=list,
        description="Data-driven observations citing the user's actual values",
    )
    shap_contributions: Optional[Dict[str, float]] = Field(
        None,
        description="SHAP feature contributions for the predicted risk class (top-8 features)",
    )
    early_warnings:     List[Dict[str, str]] = Field(
        default_factory=list,
        description="Multi-day pattern warnings detected in the user's recent history",
    )
    anomaly_model_used: Optional[str] = Field(
        None,
        description="'personal' if per-user anomaly model was used, 'population' otherwise",
    )


class CheckInRecord(BaseModel):
    """Single historical check-in row."""
    id:                  int
    user_id:             str
    timestamp:           datetime
    sleep_hours:         float
    mood_score:          int
    activity_level:      str
    social_interactions: int
    journal_text:        Optional[str]  = None
    risk_score:          Optional[float] = None
    risk_level:          Optional[str]  = None


class HistoryResponse(BaseModel):
    user_id:       str
    total_records: int
    records:       List[CheckInRecord]


class UserStatsResponse(BaseModel):
    user_id:         str
    avg_risk:        float
    highest_risk_day: Optional[datetime] = None
    trend_direction: str
    total_days:      int = Field(..., ge=0)
    avg_sleep:       Optional[float] = None
    avg_mood:        Optional[float] = None
    avg_social:      Optional[float] = None
    low_risk_streak: int = 0


class RiskTrendPoint(BaseModel):
    timestamp:  datetime
    risk_score: float


class RiskTrendResponse(BaseModel):
    user_id:     str
    data_points: List[RiskTrendPoint]


class HealthCheckResponse(BaseModel):
    status:       str  = "healthy"
    version:      str  = "2.0.0"
    models_loaded: bool = False


# ---------------------------------------------------------------------------
# Early-warning endpoint
# ---------------------------------------------------------------------------

class EarlyWarningItem(BaseModel):
    code:        str
    title:       str
    description: str
    severity:    str  # "high" | "medium" | "low"


class EarlyWarningResponse(BaseModel):
    user_id:     str
    days_scanned: int
    warning_count: int
    warnings:    List[EarlyWarningItem]
