"""
Tests for the suicidal-ideation / self-harm safety screen.

The safety screen is a critical safety component — every change to it
must be covered. These tests assert:
  - True positives on direct ideation phrases
  - True positives on burden / hopelessness ideation
  - True positives on self-harm phrases
  - True negatives on benign / positive text
  - True negatives on negated phrases ("I would never want to die")
  - Robustness to punctuation, casing, and extra whitespace
  - Empty / whitespace-only input does not trigger
"""

from __future__ import annotations

import pytest

from safety_screen import (
    SafetyScreenResult,
    is_self_harm_signal,
    run_safety_screen,
)


# ---------------------------------------------------------------------------
# True positives \u2014 the screen MUST trigger on these
# ---------------------------------------------------------------------------
TRUE_POSITIVES = [
    "I want to die.",
    "I just want to kill myself.",
    "Honestly I wish I was dead today.",
    "Some days I think about ending my life.",
    "Everyone would be better off without me.",
    "I'm such a burden to everyone around me.",
    "There's no reason to live anymore.",
    "I'm so tired of living like this.",
    "I keep cutting myself when nobody is watching.",
    "I can't go on like this much longer.",
    "Life is not worth living anymore.",
    "i WANT to DIE",  # case insensitive
    "I want to die...",  # punctuation
    "I    want  to   die",  # whitespace
]


@pytest.mark.parametrize("text", TRUE_POSITIVES)
def test_safety_screen_triggers_on_true_positive(text: str) -> None:
    result = run_safety_screen(text)
    assert isinstance(result, SafetyScreenResult)
    assert result.triggered is True, f"expected trigger for: {text!r}"
    assert len(result.matched_phrases) >= 1
    assert result.reason == "suicidal_ideation_or_self_harm_phrase_detected"


# ---------------------------------------------------------------------------
# True negatives \u2014 the screen MUST NOT trigger on these
# ---------------------------------------------------------------------------
TRUE_NEGATIVES_BENIGN = [
    "Today was great. I had a wonderful time with friends.",
    "I'm tired but optimistic about therapy starting next week.",
    "Work was tough but I made progress on a project I care about.",
    "Got 8 hours of sleep, mood is around a 7/10.",
    "Felt down earlier but my brother called and we laughed for an hour.",
]


@pytest.mark.parametrize("text", TRUE_NEGATIVES_BENIGN)
def test_safety_screen_does_not_trigger_on_benign_text(text: str) -> None:
    result = run_safety_screen(text)
    assert result.triggered is False
    assert result.matched_phrases == []


# ---------------------------------------------------------------------------
# Negation \u2014 phrases preceded by "never / not / no" should be neutralised
# ---------------------------------------------------------------------------
NEGATED_PHRASES = [
    "I would never want to die.",
    "Honestly I do not want to die.",
    "I don't want to kill myself, I just feel exhausted.",
    "I never want to hurt myself.",
    "There is no reason to live? I disagree completely.",  # punctuation only, still has the phrase
]


def test_safety_screen_neutralises_negated_phrases() -> None:
    # The first three are clearly negated and should not trigger.
    for text in NEGATED_PHRASES[:4]:
        result = run_safety_screen(text)
        assert result.triggered is False, f"expected no trigger (negated): {text!r}"


# ---------------------------------------------------------------------------
# Mixed: a negated occurrence next to a non-negated one MUST still trigger.
# Safety property: we err on the side of triggering when ambiguous.
# ---------------------------------------------------------------------------
def test_safety_screen_triggers_when_at_least_one_occurrence_is_unnegated() -> None:
    text = "I don't want to die... but honestly some nights I do want to die."
    result = run_safety_screen(text)
    assert result.triggered is True


# ---------------------------------------------------------------------------
# Empty / None inputs
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [None, "", "   ", "\n\t  \n"])
def test_safety_screen_handles_empty_input(text):
    result = run_safety_screen(text)
    assert result.triggered is False
    assert result.matched_phrases == []
    assert result.reason == "empty_text"


# ---------------------------------------------------------------------------
# Public helper alias
# ---------------------------------------------------------------------------
def test_is_self_harm_signal_returns_bool() -> None:
    assert is_self_harm_signal("I want to die") is True
    assert is_self_harm_signal("Today was good") is False
    assert is_self_harm_signal(None) is False


# ---------------------------------------------------------------------------
# Result.to_dict shape
# ---------------------------------------------------------------------------
def test_result_to_dict_serialisation() -> None:
    result = run_safety_screen("I want to die.")
    payload = result.to_dict()
    assert {"triggered", "matched_phrases", "reason"}.issubset(payload.keys())
    assert payload["triggered"] is True
    assert isinstance(payload["matched_phrases"], list)
    assert isinstance(payload["reason"], str)
