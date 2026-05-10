"""
Tests for the NLP analyser \u2014 specifically the parts that DON'T require
loading DistilBERT (the linguistic features and risk score computation).

We monkey-patch the transformer pipeline so tests run offline / on CI
without downloading model weights.
"""

from __future__ import annotations

from typing import List

import pytest

from nlp_analyzer import MentalHealthNLPAnalyzer


class _FakePipeline:
    """A drop-in replacement for the HuggingFace sentiment pipeline."""

    def __init__(self, label: str = "NEGATIVE", score: float = 0.95):
        self.label = label
        self.score = score
        self.calls: List[str] = []

    def __call__(self, text: str):
        self.calls.append(text)
        return [{"label": self.label, "score": self.score}]


@pytest.fixture
def analyzer_negative(monkeypatch: pytest.MonkeyPatch) -> MentalHealthNLPAnalyzer:
    fake = _FakePipeline(label="NEGATIVE", score=0.95)
    analyzer = MentalHealthNLPAnalyzer()
    analyzer._pipeline = fake
    return analyzer


@pytest.fixture
def analyzer_positive(monkeypatch: pytest.MonkeyPatch) -> MentalHealthNLPAnalyzer:
    fake = _FakePipeline(label="POSITIVE", score=0.92)
    analyzer = MentalHealthNLPAnalyzer()
    analyzer._pipeline = fake
    return analyzer


def test_analyze_empty_text_returns_neutral() -> None:
    analyzer = MentalHealthNLPAnalyzer()
    result = analyzer.analyze("")
    assert result["status"] == "no_journal"
    assert result["nlp_risk_score"] == 0.0
    assert result["sentiment_label"] == "NEUTRAL"


def test_analyze_none_text_returns_neutral() -> None:
    analyzer = MentalHealthNLPAnalyzer()
    result = analyzer.analyze(None)
    assert result["status"] == "no_journal"
    assert result["nlp_risk_score"] == 0.0


def test_analyze_negative_text_yields_high_risk(analyzer_negative: MentalHealthNLPAnalyzer) -> None:
    text = (
        "I feel completely hopeless and exhausted. Nothing ever gets better. "
        "I'm always tired, always alone, and absolutely worthless."
    )
    result = analyzer_negative.analyze(text)

    assert result["status"] == "analyzed"
    assert result["sentiment_label"] == "NEGATIVE"
    assert result["nlp_risk_score"] >= 0.5
    assert result["absolutist_ratio"] > 0  # "always", "never", "absolutely", "nothing"
    assert result["negative_emotion_ratio"] > 0
    assert 0.0 <= result["first_person_ratio"] <= 1.0


def test_analyze_positive_text_yields_low_risk(analyzer_positive: MentalHealthNLPAnalyzer) -> None:
    text = "Today was really nice. I had a great walk and felt grateful for my friends."
    result = analyzer_positive.analyze(text)

    assert result["status"] == "analyzed"
    assert result["sentiment_label"] == "POSITIVE"
    assert result["nlp_risk_score"] <= 0.3


def test_compute_risk_score_caps_at_one() -> None:
    score = MentalHealthNLPAnalyzer._compute_risk_score(
        sentiment_label="NEGATIVE",
        sentiment_confidence=0.99,
        first_person_ratio=1.0,
        absolutist_ratio=1.0,
        negative_emotion_ratio=1.0,
    )
    assert 0.0 <= score <= 1.0
    assert score >= 0.9


def test_compute_risk_score_floor_at_zero() -> None:
    score = MentalHealthNLPAnalyzer._compute_risk_score(
        sentiment_label="POSITIVE",
        sentiment_confidence=0.99,
        first_person_ratio=0.0,
        absolutist_ratio=0.0,
        negative_emotion_ratio=0.0,
    )
    assert score >= 0.0
    assert score < 0.1


def test_pipeline_truncates_long_input(analyzer_negative: MentalHealthNLPAnalyzer) -> None:
    """Inputs over 512 characters are truncated before being passed to the model."""
    long_text = "I am tired and sad. " * 200  # ~4000 chars
    analyzer_negative.analyze(long_text)
    assert analyzer_negative._pipeline.calls
    assert len(analyzer_negative._pipeline.calls[0]) <= 512
