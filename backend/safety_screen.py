"""
safety_screen.py — Suicidal-ideation and self-harm safety screen.

This module runs *before* the weighted risk engine on any incoming journal
text. If the screen triggers, the system unconditionally escalates the
risk level to HIGH and surfaces emergency-resource recommendations,
regardless of how the rule-based weights would otherwise score the
check-in.

Design principles:
  - **Fail-safe**, not fail-quiet: on ambiguous matches the screen errs
    toward triggering rather than missing a real signal.
  - **Cheap and deterministic**: phrase-based detection so the safety
    pathway never depends on a model that might be unavailable. A
    semantic (embedding-based) layer can be added later as a second
    line of defence — see `is_self_harm_signal()` for the extension
    point.
  - **Negation-aware**: phrases preceded by "not", "don't", "never",
    "wouldn't" within a small window are not treated as a trigger
    (e.g. "I would never want to die" should not fire).

This is intentionally NOT a clinical screening instrument and does not
replace tools like C-SSRS or PHQ-9. It is a minimum-viable safety net
for an educational tool.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trigger phrases.
# Keep the list deliberately conservative — we want very high precision on
# "this person is in distress" so the screen rarely no-ops on real signals.
# Lower-cased; matched against lemma-friendly normalised input.
# ---------------------------------------------------------------------------
SUICIDAL_IDEATION_PHRASES: tuple[str, ...] = (
    # Direct ideation
    "kill myself",
    "killing myself",
    "want to die",
    "wanna die",
    "i want to be dead",
    "i wish i was dead",
    "wish i were dead",
    "wish i wasn't here",
    "wish i was not here",
    "wish i didn't exist",

    # Plans / methods (kept generic — no detail)
    "end my life",
    "ending my life",
    "end it all",
    "take my life",
    "take my own life",
    "ending it all",
    "cant go on",
    "can't go on",
    "cannot go on",
    "no reason to live",
    "nothing to live for",
    "no point in living",
    "life is not worth",
    "not worth living",
    "tired of living",
    "tired of being alive",

    # Burden ideation (a strong predictor in clinical research)
    "everyone better off without me",
    "people better off without me",
    "world better off without me",
    "better off dead",
    "better off without me",
    "burden to everyone",
    "burden on everyone",

    # Self-harm
    "hurt myself",
    "hurting myself",
    "harm myself",
    "harming myself",
    "cut myself",
    "cutting myself",
)

# Words that, when within NEGATION_WINDOW tokens before a phrase, neutralise
# the trigger. e.g. "I do not want to die" → not a trigger.
NEGATION_TOKENS: frozenset[str] = frozenset({
    "not", "n't", "never", "no", "dont", "don't", "doesn't", "doesnt",
    "didn't", "didnt", "won't", "wont", "wouldn't", "wouldnt",
    "shouldn't", "shouldnt", "wasn't", "wasnt",
})

# How many tokens before a matched phrase to scan for negation.
NEGATION_WINDOW: int = 4


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class SafetyScreenResult:
    """Result of running the safety screen on a journal text."""

    triggered: bool
    matched_phrases: List[str]
    reason: str

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation."""
        return {
            "triggered": self.triggered,
            "matched_phrases": self.matched_phrases,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run_safety_screen(text: Optional[str]) -> SafetyScreenResult:
    """
    Scan free-text journal content for suicidal-ideation / self-harm phrases.

    Args:
        text: Raw journal text (may be None, empty, or any length).

    Returns:
        SafetyScreenResult with `triggered=True` if any non-negated phrase
        from SUICIDAL_IDEATION_PHRASES is present, plus the list of matched
        phrases for downstream logging / explainability.
    """
    if not text or not text.strip():
        return SafetyScreenResult(
            triggered=False,
            matched_phrases=[],
            reason="empty_text",
        )

    normalised = _normalise(text)
    tokens = normalised.split()

    matches: List[str] = []
    for phrase in SUICIDAL_IDEATION_PHRASES:
        if phrase in normalised and not _is_negated(normalised, tokens, phrase):
            matches.append(phrase)

    if matches:
        # Log without echoing the full journal (PII / PHI).
        logger.warning(
            "safety_screen.triggered",
            extra={"matched_phrases": matches, "text_length": len(text)},
        )
        return SafetyScreenResult(
            triggered=True,
            matched_phrases=matches,
            reason="suicidal_ideation_or_self_harm_phrase_detected",
        )

    return SafetyScreenResult(
        triggered=False,
        matched_phrases=[],
        reason="no_match",
    )


# ---------------------------------------------------------------------------
# Extension point — semantic similarity check.
# Stub kept so callers can swap in a sentence-transformer-based check
# (e.g. all-MiniLM-L6-v2) without changing the public API. We intentionally
# do not add the dependency in this PR to keep it lightweight; the phrase-
# based screen above is the primary safety layer.
# ---------------------------------------------------------------------------
def is_self_harm_signal(text: Optional[str]) -> bool:
    """
    Higher-level helper: returns True if the safety screen would trigger.

    Currently delegates to phrase-matching; future versions may add an
    embedding-based fallback to catch paraphrases the phrase list misses.
    """
    return run_safety_screen(text).triggered


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
_PUNCT_RE = re.compile(r"[^\w\s']")
_WS_RE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """
    Lower-case, strip punctuation (keeping apostrophes), collapse whitespace.

    Apostrophes are preserved so "i'm", "don't" survive intact for negation
    detection.
    """
    lowered = text.lower()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", no_punct).strip()


def _is_negated(normalised_text: str, tokens: List[str], phrase: str) -> bool:
    """
    Return True if any occurrence of `phrase` in the text is preceded by
    a negation token within NEGATION_WINDOW tokens.

    We scan all occurrences; a phrase is considered "non-negated" (i.e.
    the screen should still fire) if at least one occurrence is not
    negated. Only when *every* occurrence is negated do we treat the
    phrase as neutralised.
    """
    phrase_tokens = phrase.split()
    n = len(tokens)
    p = len(phrase_tokens)

    if p == 0 or p > n:
        return False

    occurrences_negated: List[bool] = []
    for i in range(n - p + 1):
        if tokens[i:i + p] == phrase_tokens:
            window = tokens[max(0, i - NEGATION_WINDOW):i]
            occurrences_negated.append(
                any(tok in NEGATION_TOKENS for tok in window)
            )

    if not occurrences_negated:
        return False

    # If every occurrence is negated, treat the phrase as neutralised.
    return all(occurrences_negated)
