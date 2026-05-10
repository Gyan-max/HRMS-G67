"""
Tests for the rule-based risk scoring engine.

Covers:
  - Sub-score calculators at boundary conditions
  - Weight re-normalisation when NLP / anomaly are unavailable
  - Safety override forces HIGH regardless of underlying scores
  - Dominant factor identification
  - Recommendation lookup
"""

from __future__ import annotations

import math

import pytest

from risk_engine import RiskScoringEngine


@pytest.fixture
def engine() -> RiskScoringEngine:
    return RiskScoringEngine()


# ---------------------------------------------------------------------------
# Sub-score sanity
# ---------------------------------------------------------------------------
def test_sleep_risk_score_severe_deprivation_high(engine: RiskScoringEngine) -> None:
    score = engine.sleep_risk_score(avg_sleep=4.0, sleep_variance=0.5, sleep_deficit_days=5)
    assert score >= 0.85


def test_sleep_risk_score_healthy_low(engine: RiskScoringEngine) -> None:
    score = engine.sleep_risk_score(avg_sleep=8.0, sleep_variance=0.2, sleep_deficit_days=0)
    assert score <= 0.15


def test_sleep_risk_score_hypersomnia_moderate(engine: RiskScoringEngine) -> None:
    # Hypersomnia (>9 hrs) should score in the moderate band.
    score = engine.sleep_risk_score(avg_sleep=10.5, sleep_variance=0.5, sleep_deficit_days=0)
    assert 0.4 <= score <= 0.7


def test_mood_risk_score_severely_low(engine: RiskScoringEngine) -> None:
    score = engine.mood_risk_score(avg_mood=2.5, mood_trend=-0.3, mood_volatility=2.0, lowest_mood=1.0)
    assert score >= 0.9


def test_mood_risk_score_healthy(engine: RiskScoringEngine) -> None:
    score = engine.mood_risk_score(avg_mood=8.0, mood_trend=0.1, mood_volatility=0.5, lowest_mood=7.0)
    assert score <= 0.2


def test_social_risk_score_isolation(engine: RiskScoringEngine) -> None:
    score = engine.social_risk_score(avg_social=0.5, social_trend=-0.2, isolation_days=5)
    assert score >= 0.9


def test_social_risk_score_healthy(engine: RiskScoringEngine) -> None:
    score = engine.social_risk_score(avg_social=6.0, social_trend=0.0, isolation_days=0)
    assert score <= 0.15


# ---------------------------------------------------------------------------
# Final risk \u2014 normal flow
# ---------------------------------------------------------------------------
def _high_features() -> dict:
    return {
        "avg_sleep": 4.0,
        "sleep_variance": 1.5,
        "sleep_deficit_days": 5,
        "avg_mood": 3.0,
        "mood_trend": -0.3,
        "mood_volatility": 2.5,
        "lowest_mood": 1.5,
        "avg_social": 0.5,
        "social_trend": -0.3,
        "isolation_days": 5,
    }


def _low_features() -> dict:
    return {
        "avg_sleep": 8.0,
        "sleep_variance": 0.2,
        "sleep_deficit_days": 0,
        "avg_mood": 8.0,
        "mood_trend": 0.1,
        "mood_volatility": 0.4,
        "lowest_mood": 7.0,
        "avg_social": 6.0,
        "social_trend": 0.0,
        "isolation_days": 0,
    }


def test_compute_final_risk_high_profile(engine: RiskScoringEngine) -> None:
    out = engine.compute_final_risk(
        nlp_score=0.85, anomaly_score=0.7, features_dict=_high_features()
    )
    assert out["risk_level"] == "HIGH"
    assert out["final_score"] >= engine.HIGH_THRESHOLD
    assert out["color_code"] == "#ff4444"
    assert out["safety_override"] is False
    assert out["dominant_factor"] in {"nlp", "anomaly", "sleep", "mood", "social"}


def test_compute_final_risk_low_profile(engine: RiskScoringEngine) -> None:
    out = engine.compute_final_risk(
        nlp_score=0.05, anomaly_score=0.05, features_dict=_low_features()
    )
    assert out["risk_level"] == "LOW"
    assert out["final_score"] < engine.MEDIUM_THRESHOLD


# ---------------------------------------------------------------------------
# Weight re-normalisation when components are unavailable
# ---------------------------------------------------------------------------
def test_active_weights_sum_to_one_when_all_components_available() -> None:
    weights = RiskScoringEngine._active_weights(nlp_available=True, anomaly_available=True)
    assert math.isclose(sum(weights.values()), 1.0)
    assert set(weights.keys()) == {"nlp", "anomaly", "sleep", "mood", "social"}


def test_active_weights_sum_to_one_without_nlp() -> None:
    weights = RiskScoringEngine._active_weights(nlp_available=False, anomaly_available=True)
    assert math.isclose(sum(weights.values()), 1.0)
    assert "nlp" not in weights


def test_active_weights_sum_to_one_without_nlp_or_anomaly() -> None:
    weights = RiskScoringEngine._active_weights(nlp_available=False, anomaly_available=False)
    assert math.isclose(sum(weights.values()), 1.0)
    assert "nlp" not in weights and "anomaly" not in weights


def test_missing_nlp_does_not_deflate_score(engine: RiskScoringEngine) -> None:
    """
    Regression test for the previous behaviour where a user with a HIGH
    sleep / mood / social profile but no journal entry was systematically
    under-scored because the NLP weight (30%) was forced to zero.
    """
    feats = _high_features()
    with_nlp = engine.compute_final_risk(
        nlp_score=0.0, anomaly_score=0.0, features_dict=feats,
        nlp_available=True, anomaly_available=True,
    )
    without_nlp = engine.compute_final_risk(
        nlp_score=0.0, anomaly_score=0.0, features_dict=feats,
        nlp_available=False, anomaly_available=False,
    )
    # Without NLP / anomaly weights, the same severe sleep/mood/social
    # signals should produce a HIGHER (or at least not lower) final score
    # because the remaining weights are re-normalised.
    assert without_nlp["final_score"] > with_nlp["final_score"]


# ---------------------------------------------------------------------------
# Safety override \u2014 must force HIGH no matter what
# ---------------------------------------------------------------------------
def test_safety_override_forces_high_even_on_low_profile(engine: RiskScoringEngine) -> None:
    out = engine.compute_final_risk(
        nlp_score=0.0,
        anomaly_score=0.0,
        features_dict=_low_features(),
        safety_override=True,
        safety_matched_phrases=["want to die"],
    )
    assert out["risk_level"] == "HIGH"
    assert out["final_score"] >= engine.HIGH_THRESHOLD
    assert out["color_code"] == "#ff4444"
    assert out["safety_override"] is True
    assert out["dominant_factor"] == "safety"
    # The recommendation must reference crisis resources \u2014 we test for the
    # presence of at least one helpline keyword to remain robust to wording
    # tweaks while still asserting the user-facing intent.
    assert any(
        keyword in out["recommendation"]
        for keyword in ("988", "iCall", "Samaritans", "AASRA", "emergency")
    )


def test_safety_override_does_not_echo_phrases_back(engine: RiskScoringEngine) -> None:
    """
    The recommendation must NOT echo the matched phrases back to the user
    \u2014 surfacing one's own crisis language can be retraumatising.
    """
    out = engine.compute_final_risk(
        nlp_score=0.0,
        anomaly_score=0.0,
        features_dict=_low_features(),
        safety_override=True,
        safety_matched_phrases=["want to die", "kill myself"],
    )
    assert "want to die" not in out["recommendation"].lower()
    assert "kill myself" not in out["recommendation"].lower()


# ---------------------------------------------------------------------------
# Dominant factor & recommendation
# ---------------------------------------------------------------------------
def test_dominant_factor_reflects_largest_weighted_component(engine: RiskScoringEngine) -> None:
    # NLP gets the highest weight (0.30) with the highest value here.
    out = engine.compute_final_risk(
        nlp_score=0.95, anomaly_score=0.1, features_dict=_low_features()
    )
    assert out["dominant_factor"] == "nlp"


def test_recommendation_changes_with_risk_level(engine: RiskScoringEngine) -> None:
    high = engine.compute_final_risk(0.95, 0.9, _high_features())
    low = engine.compute_final_risk(0.05, 0.05, _low_features())
    assert high["recommendation"] != low["recommendation"]
