"""
data_ingestion.py — Check-in logging, retrieval, and data management.

Handles all CRUD operations for behavioral check-in records and user profiles.
Converts SQLAlchemy rows to pandas DataFrames for downstream ML pipelines.
"""

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from database import CheckIn, User


# ===========================================================================
# CHECK-IN OPERATIONS
# ===========================================================================

def log_checkin(db: Session, user_id: str, sleep_hours: float, mood_score: int,
                activity_level: str, social_interactions: int,
                journal_text: Optional[str] = None,
                risk_score: Optional[float] = None,
                risk_level: Optional[str] = None) -> CheckIn:
    """
    Persist a new daily check-in record to the database.

    If the user doesn't exist yet, a new User row is created automatically.
    After ≥ 3 check-ins the user's baseline_established flag is set to True,
    indicating the ML models have enough history for reliable predictions.

    Args:
        db: Active SQLAlchemy session.
        user_id: Unique user identifier string.
        sleep_hours: Hours of sleep (0-12).
        mood_score: Self-rated mood (1-10).
        activity_level: One of sedentary/light/moderate/active.
        social_interactions: Count of social contacts (0-30).
        journal_text: Optional free-text journal entry.
        risk_score: Computed risk score (filled after ML pipeline runs).
        risk_level: Computed risk label (filled after ML pipeline runs).

    Returns:
        The newly created CheckIn ORM instance.
    """
    # Ensure the user profile exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, created_at=datetime.utcnow())
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create the check-in record
    checkin = CheckIn(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        sleep_hours=sleep_hours,
        mood_score=mood_score,
        activity_level=activity_level,
        social_interactions=social_interactions,
        journal_text=journal_text,
        risk_score=risk_score,
        risk_level=risk_level,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    # Update baseline flag after accumulating enough data points
    total_checkins = db.query(CheckIn).filter(CheckIn.user_id == user_id).count()
    if total_checkins >= 3 and not user.baseline_established:
        user.baseline_established = True
        db.commit()

    return checkin


def update_checkin_risk(db: Session, checkin_id: int,
                        risk_score: float, risk_level: str) -> None:
    """
    Update the risk score and level on an existing check-in record.

    Called after the ML pipeline finishes processing a new check-in.
    """
    checkin = db.query(CheckIn).filter(CheckIn.id == checkin_id).first()
    if checkin:
        checkin.risk_score = risk_score
        checkin.risk_level = risk_level
        db.commit()


# ===========================================================================
# HISTORY & RETRIEVAL
# ===========================================================================

def get_user_history(db: Session, user_id: str, days: int = 7) -> pd.DataFrame:
    """
    Retrieve the most recent `days` of check-in data for a user as a DataFrame.

    Args:
        db: Active SQLAlchemy session.
        user_id: The user to query.
        days: Number of past days to include (default 7).

    Returns:
        pandas DataFrame with columns matching the CheckIn table,
        sorted by timestamp ascending. Returns an empty DataFrame
        if no records are found.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id, CheckIn.timestamp >= cutoff)
        .order_by(CheckIn.timestamp.asc())
        .all()
    )

    if not records:
        return pd.DataFrame(columns=[
            "id", "user_id", "timestamp", "sleep_hours", "mood_score",
            "activity_level", "social_interactions", "journal_text",
            "risk_score", "risk_level",
        ])

    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "timestamp": r.timestamp,
            "sleep_hours": r.sleep_hours,
            "mood_score": r.mood_score,
            "activity_level": r.activity_level,
            "social_interactions": r.social_interactions,
            "journal_text": r.journal_text,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
        }
        for r in records
    ]
    return pd.DataFrame(data)


def get_user_history_records(db: Session, user_id: str, days: int = 30) -> List[dict]:
    """
    Return raw check-in records as a list of dicts (for JSON serialization).
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id, CheckIn.timestamp >= cutoff)
        .order_by(CheckIn.timestamp.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "timestamp": r.timestamp,
            "sleep_hours": r.sleep_hours,
            "mood_score": r.mood_score,
            "activity_level": r.activity_level,
            "social_interactions": r.social_interactions,
            "journal_text": r.journal_text,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
        }
        for r in records
    ]


def get_days_tracked(db: Session, user_id: str) -> int:
    """Return the total number of check-in records for a user."""
    return db.query(CheckIn).filter(CheckIn.user_id == user_id).count()


# ===========================================================================
# USER MANAGEMENT
# ===========================================================================

def get_all_users(db: Session) -> List[str]:
    """Return a list of all distinct user_id values in the system."""
    users = db.query(User.user_id).all()
    return [u[0] for u in users]


def delete_user_data(db: Session, user_id: str) -> dict:
    """
    GDPR-style complete data deletion for a user.

    Removes all check-in records and the user profile. This action
    is irreversible.

    Returns:
        Dict with deletion counts for confirmation.
    """
    checkin_count = db.query(CheckIn).filter(CheckIn.user_id == user_id).delete()
    user_count = db.query(User).filter(User.user_id == user_id).delete()
    db.commit()

    return {
        "user_id": user_id,
        "checkins_deleted": checkin_count,
        "user_deleted": user_count > 0,
        "message": f"All data for user '{user_id}' has been permanently deleted.",
    }
