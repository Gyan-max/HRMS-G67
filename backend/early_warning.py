"""
early_warning.py — Pattern-based early warning signal detection.

Scans a user's recent check-in history for concerning multi-day patterns
that the per-day risk score can miss. A single bad day is noise; the same
signal persisting for 3+ days is a trend worth flagging.

Each warning has:
  - code:        machine-readable identifier
  - title:       short human label (≤ 50 chars)
  - description: specific, data-driven sentence explaining the finding
  - severity:    "high" | "medium" | "low"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class EarlyWarning:
    code:        str
    title:       str
    description: str
    severity:    str  # "high" | "medium" | "low"

    def to_dict(self) -> Dict[str, str]:
        return {
            "code":        self.code,
            "title":       self.title,
            "description": self.description,
            "severity":    self.severity,
        }


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
LOW_MOOD_THRESHOLD    = 5.0
LOW_SLEEP_THRESHOLD   = 6.0
LOW_SOCIAL_THRESHOLD  = 1
HIGH_RISK_THRESHOLD   = 0.50
STREAK_TRIGGER        = 3     # consecutive days needed to fire most warnings
SLEEP_DEBT_TRIGGER    = 10.0  # cumulative hours below 7h
MOOD_DROP_TRIGGER     = 3.0   # points dropped from peak to trigger warning


def detect_early_warnings(
    history_df: pd.DataFrame,
    window: int = 14,
) -> List[EarlyWarning]:
    """
    Scan the most recent `window` days of a user's check-in history for
    multi-day warning patterns.

    Args:
        history_df: DataFrame with columns sleep_hours, mood_score,
                    social_interactions, risk_score, risk_level, timestamp.
                    Should be ordered oldest → newest.
        window:     How many recent days to examine (default 14).

    Returns:
        List of EarlyWarning objects (may be empty).
    """
    if history_df is None or len(history_df) < 2:
        return []

    df = history_df.tail(window).copy()

    # Sort oldest → newest so iterating is chronological
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp")

    # Coerce numeric columns
    for col in ["sleep_hours", "mood_score", "social_interactions", "risk_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    warnings: List[EarlyWarning] = []

    _check_mood_freefall(df, warnings)
    _check_sleep_debt(df, warnings)
    _check_social_withdrawal(df, warnings)
    _check_multi_signal_crisis(df, warnings)
    _check_sustained_high_risk(df, warnings)
    _check_mood_drop_from_peak(df, warnings)
    _check_worsening_acceleration(df, warnings)

    return warnings


# ---------------------------------------------------------------------------
# Individual pattern detectors
# ---------------------------------------------------------------------------

def _check_mood_freefall(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """3+ consecutive days where mood is strictly declining below threshold."""
    if "mood_score" not in df.columns:
        return
    moods = df["mood_score"].tolist()
    streak = _declining_streak(moods)
    if streak >= STREAK_TRIGGER:
        start_val = moods[-streak]
        end_val   = moods[-1]
        out.append(EarlyWarning(
            code="MOOD_FREEFALL",
            title="Mood declining for multiple days",
            description=(
                f"Mood has declined every day for {streak} consecutive days "
                f"({start_val:.0f} → {end_val:.0f}/10). "
                "A consistent downward trajectory is more clinically significant "
                "than a single low reading."
            ),
            severity="high" if streak >= 5 or end_val < 4 else "medium",
        ))


def _check_sleep_debt(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """Cumulative sleep deficit exceeds SLEEP_DEBT_TRIGGER hours."""
    if "sleep_hours" not in df.columns:
        return
    sleep  = df["sleep_hours"]
    debt   = float(max(0.0, 7.0 * len(sleep) - sleep.sum()))
    streak = _trailing_below(sleep.tolist(), LOW_SLEEP_THRESHOLD)
    if debt >= SLEEP_DEBT_TRIGGER:
        avg = round(float(sleep.mean()), 1)
        out.append(EarlyWarning(
            code="SLEEP_DEBT_ACCUMULATION",
            title="Significant cumulative sleep deficit",
            description=(
                f"You've accumulated approximately {debt:.0f} hours of sleep debt "
                f"over the past {len(sleep)} days (avg {avg}h/night vs the 7h baseline). "
                "Sleep debt compounds — cognitive and emotional impact grows with each night."
            ),
            severity="high" if debt >= 15 else "medium",
        ))
    elif streak >= STREAK_TRIGGER:
        out.append(EarlyWarning(
            code="SLEEP_DEFICIT_STREAK",
            title=f"{streak}-night sleep deficit streak",
            description=(
                f"{streak} consecutive nights below {LOW_SLEEP_THRESHOLD}h of sleep detected. "
                f"Average over this streak: {float(df['sleep_hours'].tail(streak).mean()):.1f}h."
            ),
            severity="medium",
        ))


def _check_social_withdrawal(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """3+ consecutive days of near-total social isolation."""
    if "social_interactions" not in df.columns:
        return
    streak = _trailing_below(df["social_interactions"].tolist(), LOW_SOCIAL_THRESHOLD + 0.5)
    if streak >= STREAK_TRIGGER:
        out.append(EarlyWarning(
            code="SOCIAL_WITHDRAWAL_TREND",
            title=f"{streak}-day social isolation streak",
            description=(
                f"{streak} consecutive days with ≤{LOW_SOCIAL_THRESHOLD} meaningful social "
                "interactions detected. Social isolation is one of the strongest independent "
                "predictors of mental health deterioration."
            ),
            severity="high" if streak >= 5 else "medium",
        ))


def _check_multi_signal_crisis(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """All three primary signals in the danger zone simultaneously."""
    recent = df.tail(3)
    if len(recent) < 3:
        return

    bad_sleep  = "sleep_hours" in df.columns and float(recent["sleep_hours"].mean()) < LOW_SLEEP_THRESHOLD
    bad_mood   = "mood_score" in df.columns and float(recent["mood_score"].mean()) < LOW_MOOD_THRESHOLD
    bad_social = "social_interactions" in df.columns and float(recent["social_interactions"].mean()) <= LOW_SOCIAL_THRESHOLD

    flags = sum([bad_sleep, bad_mood, bad_social])
    if flags >= 2:
        components = []
        if bad_sleep:
            components.append(f"sleep avg {recent['sleep_hours'].mean():.1f}h")
        if bad_mood:
            components.append(f"mood avg {recent['mood_score'].mean():.1f}/10")
        if bad_social:
            components.append(f"social avg {recent['social_interactions'].mean():.1f}/day")

        out.append(EarlyWarning(
            code="MULTI_SIGNAL_DISTRESS",
            title="Multiple risk signals active simultaneously",
            description=(
                f"Over the past 3 days: {', '.join(components)} — all below healthy thresholds. "
                "Co-occurring signals amplify each other: poor sleep worsens mood regulation, "
                "which reduces motivation for social contact, which worsens sleep."
            ),
            severity="high" if flags == 3 else "medium",
        ))


def _check_sustained_high_risk(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """Risk score has been above 0.50 for 3+ consecutive days."""
    if "risk_score" not in df.columns:
        return
    streak = _trailing_above(df["risk_score"].tolist(), HIGH_RISK_THRESHOLD)
    if streak >= STREAK_TRIGGER:
        avg_risk = float(df["risk_score"].tail(streak).mean())
        out.append(EarlyWarning(
            code="SUSTAINED_ELEVATED_RISK",
            title=f"Elevated risk score for {streak} consecutive days",
            description=(
                f"Risk score has remained above {int(HIGH_RISK_THRESHOLD*100)}% "
                f"for {streak} consecutive days (avg {avg_risk*100:.0f}%). "
                "Persistent elevation is more concerning than a brief spike."
            ),
            severity="high" if streak >= 5 else "medium",
        ))


def _check_mood_drop_from_peak(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """Mood has fallen significantly from its recent best."""
    if "mood_score" not in df.columns or len(df) < 4:
        return
    peak    = float(df["mood_score"].max())
    current = float(df["mood_score"].iloc[-1])
    drop    = peak - current
    if drop >= MOOD_DROP_TRIGGER and current < LOW_MOOD_THRESHOLD + 1:
        out.append(EarlyWarning(
            code="MOOD_DROP_FROM_PEAK",
            title="Significant mood decline from recent best",
            description=(
                f"Mood has dropped {drop:.0f} points from a recent high of {peak:.0f}/10 "
                f"to {current:.0f}/10. Even when the current level seems 'not that low', "
                "a sharp relative decline is a meaningful early warning signal."
            ),
            severity="medium",
        ))


def _check_worsening_acceleration(df: pd.DataFrame, out: List[EarlyWarning]) -> None:
    """The rate of mood decline is accelerating (velocity increasing)."""
    if "mood_score" not in df.columns or len(df) < 6:
        return
    moods = df["mood_score"].tolist()
    mid   = len(moods) // 2
    # Slope of first half vs second half
    first_slope  = _slope(moods[:mid])
    second_slope = _slope(moods[mid:])
    if second_slope < first_slope - 0.3 and second_slope < -0.2:
        out.append(EarlyWarning(
            code="DETERIORATION_ACCELERATING",
            title="Mood decline is speeding up",
            description=(
                "The rate of mood decline has increased in the second half of the "
                f"observation window (slope: {first_slope:+.2f} → {second_slope:+.2f} per day). "
                "Accelerating deterioration warrants closer attention than a gradual drift."
            ),
            severity="high",
        ))


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _trailing_below(values: list, threshold: float) -> int:
    """Count consecutive values at the *end* of the list below threshold."""
    count = 0
    for v in reversed(values):
        if v < threshold:
            count += 1
        else:
            break
    return count


def _trailing_above(values: list, threshold: float) -> int:
    count = 0
    for v in reversed(values):
        if v > threshold:
            count += 1
        else:
            break
    return count


def _declining_streak(values: list) -> int:
    """Count consecutive strictly-declining values at the end of the list."""
    count = 0
    for i in range(len(values) - 1, 0, -1):
        if values[i] < values[i - 1]:
            count += 1
        else:
            break
    return count


def _slope(values: list) -> float:
    """Linear regression slope of a list of values."""
    import numpy as np
    if len(values) < 2:
        return 0.0
    x = list(range(len(values)))
    return float(np.polyfit(x, values, 1)[0])
