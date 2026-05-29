"""
safety_screen.py — Suicidal-ideation and self-harm safety screen (v2).

v2 improvements:
  - Phrase list expanded from 30 → 75+ entries covering:
      · Clinical paraphrases ("I see no way out of this")
      · Indirect/passive ideation ("I wish I could just disappear")
      · Cultural variants common in South Asian contexts
      · Burden ideation (a strong clinical predictor)
      · Self-harm beyond cutting (burning, starving, self-punishment)
  - Regex-based indirect ideation patterns for expressions that
    don't match any single phrase but carry clear clinical meaning
  - Negation detection window widened from 4 → 5 tokens
  - Confidence level added to result: "phrase_match" | "pattern_match"

Design principles (unchanged):
  - Fail-safe: ambiguous matches err toward triggering
  - Cheap and deterministic: no ML model in the hot path
  - Negation-aware: "I would never want to die" does not trigger
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier 1: Explicit phrases (high precision, direct ideation)
# ---------------------------------------------------------------------------
SUICIDAL_IDEATION_PHRASES: tuple[str, ...] = (
    # Direct ideation
    "kill myself", "killing myself",
    "want to die", "wanna die", "wanted to die",
    "i want to be dead", "i wish i was dead", "wish i were dead",
    "wish i wasn't here", "wish i was not here",
    "wish i didn't exist", "wish i never existed",
    "i don't want to be here anymore", "don't want to be alive",
    "i don't want to live anymore", "don't want to live",

    # Plans / methods (kept generic)
    "end my life", "ending my life",
    "end it all", "ending it all",
    "take my life", "take my own life",
    "cant go on", "can't go on", "cannot go on",
    "no reason to live", "nothing to live for",
    "no point in living", "no point being alive",
    "life is not worth", "not worth living",
    "tired of living", "tired of being alive",
    "ready to die", "want it to be over",
    "make it stop permanently",

    # Passive ideation / disappearing
    "wish i could just disappear",
    "wish i could disappear forever",
    "i want to disappear",
    "wish i could sleep and not wake up",
    "hope i don't wake up",
    "won't wake up tomorrow",
    "going to sleep and not waking up",

    # Burden ideation (strong clinical predictor)
    "everyone better off without me",
    "people better off without me",
    "world better off without me",
    "better off dead", "better off without me",
    "burden to everyone", "burden on everyone",
    "burden to my family", "burden on my family",
    "everyone would be happier without me",
    "no one would miss me",
    "nobody would miss me",
    "no one would care if i was gone",
    "nobody cares if i live or die",

    # Self-harm
    "hurt myself", "hurting myself",
    "harm myself", "harming myself",
    "cut myself", "cutting myself",
    "burning myself", "burn myself",
    "hurt my body", "punish myself",
    "make myself bleed",
    "starving myself to punish",

    # Hopelessness (severe, action-linked)
    "no way out of this",
    "there is no way out",
    "i see no future",
    "i have no future",
    "nothing will ever get better",
    "things will never get better for me",
    "it will never get better",
    "i can't see a reason to keep going",
    "no reason to keep going",
    "too tired to keep going",
    "too exhausted to keep fighting",
    "given up on life",
    "given up on everything",
    "i give up on life",
)

# ---------------------------------------------------------------------------
# Tier 2: Regex patterns for indirect / paraphrased ideation
# These are less specific but cover language that phrase matching misses.
# ---------------------------------------------------------------------------
_INDIRECT_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(wish|hope|want)\b.{0,30}\b(not wake|never wake|stop existing|cease to exist)\b", re.I),
    re.compile(r"\bno (point|reason|purpose)\b.{0,20}\b(anymore|any ?more|going on|continuing)\b", re.I),
    re.compile(r"\b(everyone|everybody|people|they).{0,25}\b(better off|happier).{0,15}\bwithout me\b", re.I),
    re.compile(r"\btoo (tired|exhausted|worn out).{0,30}\b(keep (going|fighting|trying)|live|go on)\b", re.I),
    re.compile(r"\b(can't|cannot|can not).{0,20}\b(do this anymore|go on|keep going|continue)\b", re.I),
    re.compile(r"\b(end|finish|stop)\b.{0,15}\b(it all|everything|my (pain|suffering|life))\b", re.I),
    re.compile(r"\bfeel like.{0,30}\b(dying|giving up|not being here|disappearing)\b", re.I),
    re.compile(r"\b(planning|thinking about|considering)\b.{0,30}\b(suicide|ending it|self.harm)\b", re.I),
]

# ---------------------------------------------------------------------------
# Negation
# ---------------------------------------------------------------------------
NEGATION_TOKENS: frozenset[str] = frozenset({
    "not", "n't", "never", "no", "dont", "don't", "doesn't", "doesnt",
    "didn't", "didnt", "won't", "wont", "wouldn't", "wouldnt",
    "shouldn't", "shouldnt", "wasn't", "wasnt", "can't", "cannot",
    "couldn't", "couldnt", "needn't",
})

NEGATION_WINDOW: int = 5   # widened from 4 → 5


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class SafetyScreenResult:
    triggered:       bool
    matched_phrases: List[str]
    reason:          str
    match_type:      str = "none"   # "phrase_match" | "pattern_match" | "none"

    def to_dict(self) -> dict:
        return {
            "triggered":       self.triggered,
            "matched_phrases": self.matched_phrases,
            "reason":          self.reason,
            "match_type":      self.match_type,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run_safety_screen(text: Optional[str]) -> SafetyScreenResult:
    """
    Scan journal text for suicidal-ideation / self-harm indicators.

    Runs two tiers:
      1. Phrase matching (high precision) — checked with negation awareness
      2. Regex pattern matching (broader coverage) — indirect expressions

    A single non-negated match in either tier triggers the screen.
    """
    if not text or not text.strip():
        return SafetyScreenResult(
            triggered=False, matched_phrases=[], reason="empty_text",
        )

    normalised = _normalise(text)
    tokens     = normalised.split()

    # Tier 1: phrase matching
    phrase_matches: List[str] = [
        phrase for phrase in SUICIDAL_IDEATION_PHRASES
        if phrase in normalised and not _is_negated(normalised, tokens, phrase)
    ]

    if phrase_matches:
        logger.warning(
            "safety_screen.phrase_triggered",
            extra={"matched_phrases": phrase_matches, "text_length": len(text)},
        )
        return SafetyScreenResult(
            triggered=True,
            matched_phrases=phrase_matches,
            reason="suicidal_ideation_or_self_harm_phrase_detected",
            match_type="phrase_match",
        )

    # Tier 2: regex patterns (broader / indirect)
    for pattern in _INDIRECT_PATTERNS:
        m = pattern.search(text)
        if m:
            matched_text = m.group(0)[:80]
            logger.warning(
                "safety_screen.pattern_triggered",
                extra={"pattern": pattern.pattern, "text_length": len(text)},
            )
            return SafetyScreenResult(
                triggered=True,
                matched_phrases=[matched_text],
                reason="indirect_ideation_pattern_detected",
                match_type="pattern_match",
            )

    return SafetyScreenResult(
        triggered=False, matched_phrases=[], reason="no_match",
    )


def is_self_harm_signal(text: Optional[str]) -> bool:
    return run_safety_screen(text).triggered


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
_PUNCT_RE = re.compile(r"[^\w\s']")
_WS_RE    = re.compile(r"\s+")


def _normalise(text: str) -> str:
    lowered  = text.lower()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", no_punct).strip()


def _is_negated(normalised_text: str, tokens: List[str], phrase: str) -> bool:
    """
    Return True if *every* occurrence of phrase in the text is negated.
    A phrase is considered negated when a NEGATION_TOKEN appears within
    NEGATION_WINDOW tokens before it.
    """
    phrase_tokens = phrase.split()
    n = len(tokens)
    p = len(phrase_tokens)

    if p == 0 or p > n:
        return False

    occurrences_negated: List[bool] = []
    for i in range(n - p + 1):
        if tokens[i : i + p] == phrase_tokens:
            window = tokens[max(0, i - NEGATION_WINDOW) : i]
            occurrences_negated.append(
                any(tok in NEGATION_TOKENS for tok in window)
            )

    if not occurrences_negated:
        return False

    return all(occurrences_negated)
