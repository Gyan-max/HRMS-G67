"""
database.py — SQLAlchemy ORM models and SQLite database configuration.

This module defines the database schema for the Behavioral Health Risk
Monitoring System. It uses SQLite for zero-configuration local storage
and SQLAlchemy as the ORM layer.

Tables:
    - users: Stores user profiles and baseline tracking status.
    - checkins: Stores daily behavioral check-in records with computed risk scores.
"""

import os
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# Database path — stored alongside the backend code for portability
# ---------------------------------------------------------------------------
DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'health_monitor.db')}"

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ===========================================================================
# ORM MODELS
# ===========================================================================

class User(Base):
    """
    Represents a registered user in the system.

    Attributes:
        id: Auto-incrementing primary key.
        user_id: Unique human-readable identifier (e.g. "user_001").
        created_at: UTC timestamp of first registration.
        baseline_established: True once the system has ≥ 3 days of data
                              and can produce reliable risk assessments.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    baseline_established = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id!r}, baseline={self.baseline_established})>"


class CheckIn(Base):
    """
    A single daily behavioral check-in record.

    Captures the raw self-reported data plus the computed risk outputs
    so that historical analyses don't need to re-run the ML pipeline.

    Attributes:
        sleep_hours: Hours of sleep reported (0–12).
        mood_score: Self-rated mood on a 1–10 scale.
        activity_level: One of sedentary / light / moderate / active.
        social_interactions: Count of meaningful social interactions (0–30).
        journal_text: Optional free-text journal entry.
        risk_score: Computed weighted risk score (0.0–1.0).
        risk_level: Categorical risk label (LOW / MEDIUM / HIGH).
    """
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sleep_hours = Column(Float, nullable=False)
    mood_score = Column(Integer, nullable=False)
    activity_level = Column(String(20), nullable=False)
    social_interactions = Column(Integer, nullable=False)
    journal_text = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(10), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CheckIn(user={self.user_id!r}, mood={self.mood_score}, "
            f"risk={self.risk_level})>"
        )


# ===========================================================================
# UTILITY FUNCTIONS
# ===========================================================================

def create_tables() -> None:
    """Create all tables in the database if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session.

    Usage::

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request completes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
