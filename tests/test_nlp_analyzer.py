"""
Tests for the NLP analyser — specifically the parts that DON'T require
loading the emotion model (linguistic features and risk score computation).

We monkey-patch the transformer pipeline so tests run offline / on CI
without downloading model weights.

v2: _FakePipeline now returns the 7-emotion format that the upgraded
    analyzer expects (top_k=None style: list-of-lists).
"""

from __future__ import annotations

from typing import Any, List

import pytest

from nlp_analyzer import MentalHealthNLPAnalyzer, EMOTION_RISK_WEIGHTS


# ---------------------------------------------------------------------------
# Fake pipeline — returns the emotion model's top_k=None format
# ---------------------------------------------------------------------------

class _FakePipeline:
    """
    Drop-in replacement for the HuggingFace emotion pipeline.

    Returns [[{label, score}, ...]] (list-of-lists) matching the
    top_k=None output format of j-hartmann/emotion-english-distilroberta-base.
    """

    def __init__(self, dominant: str = "sadness", dominant_score: float = 0.80):
        self.dominant       = dominant.lower()
        self.dominant_score = dominant_score
        self.calls: List[str] = []

    def __call__(self, text: str, **kwargs: Any):
        self.calls.append(text)
        remaining = max(0.0, 1.0 - self.dominant_score)
        others    = [e for e in EMOTION_RISK_WEIGHTS if e != self.dominant]
        per_other = remaining / len(others) if others else 0.0
        items = [{"label": self.dominant, "score": self.dominant_score}]
        items += [{"label": e, "score": round(per_other, 4)} for e in others]
        return [items]   # wrapped in a list (list-of-lists)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer_negative(monkeypatch: pytest.MonkeyPatch) -> MentalHealthNLPAnalyzer:
    """Analyzer whose pipeline strongly predicts sadness (high risk)."""
    fake     = _FakePipeline(dominant="sadness", dominant_score=0.88)
    analyzer = MentalHealthNLPAnalyzer()
    analyzer._pipeline = fake
    return analyzer


@pytest.fixture
def analyzer_positive(monkeypatch: pytest.MonkeyPatch) -> MentalHealthNLPAnalyzer:
    """Analyzer whose pipeline strongly predicts joy (low risk)."""
    fake     = _FakePipeline(dominant="joy", dominant_score=0.92)
    analyzer = MentalHealthNLPAnalyzer()
    analyzer._pipeline = fake
    return analyzer


# ---------------------------------------------------------------------------
# Empty / null text
# ---------------------------------------------------------------------------

def test_analyze_empty_text_returns_neutral() -> None:
    analyzer = MentalHealthNLPAnalyzer()
    result   = analyzer.analyze("")
    assert result["status"]         == "no_journal"
    assert result["nlp_risk_score"] == 0.0
    assert result["sentiment_label"] == "NEUTRAL"
    assert result["dominant_emotion"] == "neutral"


def test_analyze_none_text_returns_neutral() -> None:
    analyzer = MentalHealthNLPAnalyzer()
    result   = analyzer.analyze(None)
    assert result["status"]         == "no_journal"
    assert result["nlp_risk_score"] == 0.0


# ---------------------------------------------------------------------------
# Negative / high-risk text
# ---------------------------------------------------------------------------

def test_analyze_negative_text_yields_high_risk(analyzer_negative: MentalHealthNLPAnalyzer) -> None:
    text = (
        "I feel completely hopeless and exhausted. Nothing ever gets better. "
        "I'm always tired, always alone, and absolutely worthless."
    )
    result = analyzer_negative.analyze(text)

    assert result["status"]           == "analyzed"
    assert result["sentiment_label"]  == "NEGATIVE"
    assert result["dominant_emotion"] == "sadness"
    assert result["nlp_risk_score"]   >= 0.5
    assert result["absolutist_ratio"] > 0       # "always", "never", "absolutely", "nothing"
    assert result["negative_emotion_ratio"] > 0
    assert 0.0 <= result["first_person_ratio"] <= 1.0
    # v2: emotions dict present
    assert "emotions" in result
    assert "sadness" in result["emotions"]


# ---------------------------------------------------------------------------
# Positive / low-risk text
# ---------------------------------------------------------------------------

def test_analyze_positive_text_yields_low_risk(analyzer_positive: MentalHealthNLPAnalyzer) -> None:
    text   = "Today was really nice. I had a great walk and felt grateful for my friends."
    result = analyzer_positive.analyze(text)

    assert result["status"]           == "analyzed"
    assert result["sentiment_label"]  == "POSITIVE"
    assert result["dominant_emotion"] == "joy"
    assert result["nlp_risk_score"]   <= 0.3
    assert "emotions" in result


# ---------------------------------------------------------------------------
# Risk score bounds
# ---------------------------------------------------------------------------

def test_compute_risk_score_caps_at_one() -> None:
    emotions = {e: (1.0 if e == "sadness" else 0.0) for e in EMOTION_RISK_WEIGHTS}
    score = MentalHealthNLPAnalyzer._compute_risk_score(
        emotion_scores=emotions,
        first_person_ratio=1.0,
        absolutist_ratio=1.0,
        negative_emotion_ratio=1.0,
    )
    assert 0.0 <= score <= 1.0
    assert score >= 0.8


def test_compute_risk_score_floor_at_zero() -> None:
    emotions = {e: (1.0 if e == "joy" else 0.0) for e in EMOTION_RISK_WEIGHTS}
    score = MentalHealthNLPAnalyzer._compute_risk_score(
        emotion_scores=emotions,
        first_person_ratio=0.0,
        absolutist_ratio=0.0,
        negative_emotion_ratio=0.0,
    )
    assert score >= 0.0
    assert score < 0.1


# ---------------------------------------------------------------------------
# Long-input truncation
# ---------------------------------------------------------------------------

def test_pipeline_called_for_long_input(analyzer_negative: MentalHealthNLPAnalyzer) -> None:
    """Long inputs are forwarded to the pipeline with truncation kwargs."""
    long_text = "I am tired and sad. " * 200   # ~4 000 chars
    analyzer_negative.analyze(long_text)
    assert analyzer_negative._pipeline.calls        # pipeline was invoked
    assert analyzer_negative._pipeline.calls[0] == long_text   # full text forwarded


# ---------------------------------------------------------------------------
# Emotion dict present in result
# ---------------------------------------------------------------------------

def test_emotions_dict_in_result(analyzer_negative: MentalHealthNLPAnalyzer) -> None:
    result = analyzer_negative.analyze("I feel so sad and empty today.")
    assert isinstance(result["emotions"], dict)
    assert set(result["emotions"].keys()) == set(EMOTION_RISK_WEIGHTS.keys())


# ---------------------------------------------------------------------------
# Empty result has all emotion keys zeroed
# ---------------------------------------------------------------------------

def test_empty_result_has_all_emotion_keys() -> None:
    analyzer = MentalHealthNLPAnalyzer()
    result   = analyzer.analyze("   ")
    assert result["status"] == "no_journal"
    for key in EMOTION_RISK_WEIGHTS:
        assert result["emotions"][key] == 0.0
