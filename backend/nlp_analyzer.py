"""
nlp_analyzer.py — NLP-based mental health text analysis.

Uses a HuggingFace DistilBERT sentiment pipeline plus hand-crafted
linguistic feature extraction to assess journal text for mental health
risk indicators. The linguistic features are grounded in clinical
psychology research on language markers of depression and anxiety.
"""

import re
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Lazy-loaded globals for the HuggingFace pipeline.
# The model is only downloaded / loaded once on first use.
# ---------------------------------------------------------------------------
_pipeline_instance = None


def _get_pipeline():
    """
    Lazily load the HuggingFace sentiment analysis pipeline.

    Uses distilbert-base-uncased-finetuned-sst-2-english, a lightweight
    model (~260 MB) that runs well on CPU. Cached after first load.
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        from transformers import pipeline
        _pipeline_instance = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,  # Force CPU — no GPU required
        )
    return _pipeline_instance


# ---------------------------------------------------------------------------
# Clinical word lists (based on published research on linguistic markers)
# ---------------------------------------------------------------------------

# Absolutist words correlate with depression / suicidal ideation
# (Al-Mosaiwi & Johnstone, 2018)
ABSOLUTIST_WORDS = {
    "never", "always", "nothing", "everything", "completely", "totally",
    "absolutely", "constantly", "entirely", "impossible", "forever",
}

# Negative emotion words signalling distress
NEGATIVE_EMOTION_WORDS = {
    "sad", "hopeless", "tired", "worthless", "empty", "anxious",
    "worried", "alone", "hurt", "failed", "meaningless", "useless",
    "terrible", "depressed", "miserable", "exhausted", "overwhelmed",
    "drained", "numb", "frustrated", "angry", "scared", "panic",
    "broken", "crying", "suffering", "struggling", "desperate",
}

# First-person singular pronouns — elevated usage linked to depression
FIRST_PERSON_WORDS = {"i", "me", "my", "mine", "myself"}


class MentalHealthNLPAnalyzer:
    """
    Analyzes journal text for mental health risk indicators.

    Combines transformer-based sentiment analysis with rule-based
    linguistic feature extraction to produce a comprehensive
    text risk profile.

    Usage::

        analyzer = MentalHealthNLPAnalyzer()
        result = analyzer.analyze("I feel so tired and alone.")
        # result["nlp_risk_score"]  → 0.82
    """

    def __init__(self):
        """Initialize the analyzer. Model loading is deferred to first use."""
        self._pipeline = None

    def _ensure_pipeline(self):
        """Load the sentiment pipeline if not already loaded."""
        if self._pipeline is None:
            self._pipeline = _get_pipeline()

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Run full NLP analysis on a journal text entry.

        Args:
            text: Raw journal text (can be None or empty).

        Returns:
            Dictionary containing:
                - sentiment_label: POSITIVE or NEGATIVE
                - sentiment_confidence: Model confidence (0-1)
                - nlp_risk_score: Composite NLP risk (0-1, higher = riskier)
                - first_person_ratio: Proportion of first-person pronouns
                - absolutist_ratio: Proportion of absolutist words
                - negative_emotion_ratio: Proportion of negative emotion words
                - text_length: Word count
                - avg_word_length: Average characters per word
                - status: "analyzed" or "no_journal"
        """
        # Handle missing or empty text gracefully
        if not text or not text.strip():
            return self._empty_result()

        # Ensure the transformer model is loaded
        self._ensure_pipeline()

        # ---------------------------------------------------------------
        # Step 1: Transformer-based sentiment analysis
        # ---------------------------------------------------------------
        try:
            sentiment_result = self._pipeline(text[:512])[0]  # Truncate to model max
            sentiment_label = sentiment_result["label"]
            sentiment_confidence = float(sentiment_result["score"])
        except Exception:
            # Fallback if model inference fails for any reason
            sentiment_label = "NEUTRAL"
            sentiment_confidence = 0.5

        # ---------------------------------------------------------------
        # Step 2: Linguistic feature extraction
        # ---------------------------------------------------------------
        # Tokenize: lowercase, strip punctuation, split on whitespace
        words = re.findall(r"[a-z']+", text.lower())
        total_words = len(words) if words else 1  # Avoid division by zero

        # First-person pronoun ratio
        first_person_count = sum(1 for w in words if w in FIRST_PERSON_WORDS)
        first_person_ratio = first_person_count / total_words

        # Absolutist language ratio
        absolutist_count = sum(1 for w in words if w in ABSOLUTIST_WORDS)
        absolutist_ratio = absolutist_count / total_words

        # Negative emotion word ratio
        negative_count = sum(1 for w in words if w in NEGATIVE_EMOTION_WORDS)
        negative_emotion_ratio = negative_count / total_words

        # Text length and average word length
        text_length = total_words
        avg_word_length = (
            sum(len(w) for w in words) / total_words if words else 0.0
        )

        # ---------------------------------------------------------------
        # Step 3: Compute composite NLP risk score
        # ---------------------------------------------------------------
        nlp_risk_score = self._compute_risk_score(
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_confidence,
            first_person_ratio=first_person_ratio,
            absolutist_ratio=absolutist_ratio,
            negative_emotion_ratio=negative_emotion_ratio,
        )

        return {
            "sentiment_label": sentiment_label,
            "sentiment_confidence": round(sentiment_confidence, 4),
            "nlp_risk_score": round(nlp_risk_score, 4),
            "first_person_ratio": round(first_person_ratio, 4),
            "absolutist_ratio": round(absolutist_ratio, 4),
            "negative_emotion_ratio": round(negative_emotion_ratio, 4),
            "text_length": text_length,
            "avg_word_length": round(avg_word_length, 2),
            "status": "analyzed",
        }

    @staticmethod
    def _compute_risk_score(
        sentiment_label: str,
        sentiment_confidence: float,
        first_person_ratio: float,
        absolutist_ratio: float,
        negative_emotion_ratio: float,
    ) -> float:
        """
        Combine sentiment and linguistic signals into a single risk score.

        The weighting reflects clinical research:
          - Negative sentiment is the strongest single signal (50%)
          - Negative emotion words add direct evidence (25%)
          - Absolutist thinking is a subtle but robust marker (15%)
          - Excessive first-person focus adds context (10%)

        Returns:
            Float between 0.0 (no risk) and 1.0 (maximum risk).
        """
        # Base score from sentiment: NEGATIVE → use confidence as risk,
        # POSITIVE → invert confidence to get (low) risk
        if sentiment_label == "NEGATIVE":
            sentiment_risk = sentiment_confidence
        else:
            sentiment_risk = 1.0 - sentiment_confidence

        # Weighted combination
        score = (
            0.50 * sentiment_risk
            + 0.25 * min(negative_emotion_ratio * 10, 1.0)  # Scale up (rare words)
            + 0.15 * min(absolutist_ratio * 15, 1.0)        # Scale up
            + 0.10 * min(first_person_ratio * 5, 1.0)       # Scale up
        )

        return max(0.0, min(1.0, score))  # Clamp to [0, 1]

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        """Return a neutral result when no journal text is provided."""
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_confidence": 0.0,
            "nlp_risk_score": 0.0,
            "first_person_ratio": 0.0,
            "absolutist_ratio": 0.0,
            "negative_emotion_ratio": 0.0,
            "text_length": 0,
            "avg_word_length": 0.0,
            "status": "no_journal",
        }
