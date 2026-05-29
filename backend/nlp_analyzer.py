"""
nlp_analyzer.py — NLP-based mental health text analysis.

Upgraded from binary SST-2 sentiment (POSITIVE/NEGATIVE) to a 7-class
emotion detection model (j-hartmann/emotion-english-distilroberta-base)
that distinguishes: anger, disgust, fear, joy, neutral, sadness, surprise.

This gives far richer signal than a single positive/negative label:
  - sadness + fear together is a strong clinical indicator
  - joy is a protective factor that actively lowers the risk score
  - anger/disgust flag distress without necessarily flagging depression

The NLP risk score is a clinically-weighted sum of emotion probabilities.
Linguistic feature extraction (absolutist words, negative-emotion ratio,
first-person focus) is retained and enriched.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded globals for the HuggingFace pipeline.
# ---------------------------------------------------------------------------
_pipeline_instance = None
_EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"


def _get_pipeline():
    """
    Lazily load the emotion classification pipeline.

    Uses j-hartmann/emotion-english-distilroberta-base (~330 MB), a
    DistilRoBERTa model fine-tuned on multiple emotion datasets. Returns
    all 7 emotion scores per input (top_k=None). Cached after first load.
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading emotion model: %s", _EMOTION_MODEL)
        _pipeline_instance = hf_pipeline(
            "text-classification",
            model=_EMOTION_MODEL,
            top_k=None,       # Return all 7 emotion scores
            device=-1,        # CPU
        )
        logger.info("Emotion model loaded successfully")
    return _pipeline_instance


# ---------------------------------------------------------------------------
# Clinical word lists
# ---------------------------------------------------------------------------

ABSOLUTIST_WORDS = {
    "never", "always", "nothing", "everything", "completely", "totally",
    "absolutely", "constantly", "entirely", "impossible", "forever",
    "nobody", "everybody", "worthless", "hopeless", "pointless",
}

NEGATIVE_EMOTION_WORDS = {
    "sad", "hopeless", "tired", "worthless", "empty", "anxious",
    "worried", "alone", "hurt", "failed", "meaningless", "useless",
    "terrible", "depressed", "miserable", "exhausted", "overwhelmed",
    "drained", "numb", "frustrated", "angry", "scared", "panic",
    "broken", "crying", "suffering", "struggling", "desperate",
    "trapped", "stuck", "lost", "afraid", "ashamed", "guilty",
    "unloved", "unwanted", "forgotten", "invisible", "dying",
}

FIRST_PERSON_WORDS = {"i", "me", "my", "mine", "myself"}

# ---------------------------------------------------------------------------
# Emotion → risk weight mapping
# Calibrated so the weighted sum lands on a 0-1 scale under typical usage.
# Clinical basis: sadness and fear are the strongest predictors; joy is
# a genuine protective factor.
# ---------------------------------------------------------------------------
EMOTION_RISK_WEIGHTS: Dict[str, float] = {
    "sadness":  0.90,
    "fear":     0.80,
    "disgust":  0.55,
    "anger":    0.45,
    "surprise": 0.15,
    "neutral":  0.10,
    "joy":      0.02,
}

# Map dominant emotion → legacy sentiment_label for backward compatibility
EMOTION_TO_SENTIMENT: Dict[str, str] = {
    "sadness":  "NEGATIVE",
    "fear":     "NEGATIVE",
    "disgust":  "NEGATIVE",
    "anger":    "NEGATIVE",
    "surprise": "NEUTRAL",
    "neutral":  "NEUTRAL",
    "joy":      "POSITIVE",
}


class MentalHealthNLPAnalyzer:
    """
    Analyzes journal text for mental health risk indicators.

    Combines 7-class emotion detection with rule-based linguistic feature
    extraction to produce a comprehensive text risk profile.

    Usage::

        analyzer = MentalHealthNLPAnalyzer()
        result = analyzer.analyze("I feel so tired and alone.")
        # result["nlp_risk_score"]      → 0.82
        # result["emotions"]["sadness"] → 0.74
        # result["dominant_emotion"]    → "sadness"
    """

    def __init__(self):
        self._pipeline = None

    def _ensure_pipeline(self):
        if self._pipeline is None:
            self._pipeline = _get_pipeline()

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Run full NLP analysis on a journal text entry.

        Returns:
            Dictionary containing:
                - sentiment_label: dominant sentiment (POSITIVE/NEGATIVE/NEUTRAL)
                - sentiment_confidence: probability of dominant emotion
                - dominant_emotion: highest-scoring emotion label
                - emotions: dict of all 7 emotion probabilities
                - nlp_risk_score: composite risk (0-1, higher = riskier)
                - first_person_ratio, absolutist_ratio, negative_emotion_ratio
                - text_length, avg_word_length
                - status: "analyzed" or "no_journal"
        """
        if not text or not text.strip():
            return self._empty_result()

        self._ensure_pipeline()

        # ---------------------------------------------------------------
        # Step 1: Emotion detection
        # ---------------------------------------------------------------
        try:
            if len(text) > 1500:
                logger.warning(
                    "nlp_analyzer.text_truncated: text length %d chars; "
                    "only the first 512 tokens will be analyzed.",
                    len(text),
                )
            raw = self._pipeline(text, truncation=True, max_length=512)
            emotion_scores = self._parse_emotion_output(raw)
        except Exception as exc:
            logger.warning("Emotion pipeline failed (%s); using neutral fallback.", exc)
            emotion_scores = {e: (1.0 / 7) for e in EMOTION_RISK_WEIGHTS}

        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        sentiment_label = EMOTION_TO_SENTIMENT.get(dominant_emotion, "NEUTRAL")
        sentiment_confidence = float(emotion_scores[dominant_emotion])

        # ---------------------------------------------------------------
        # Step 2: Linguistic feature extraction
        # ---------------------------------------------------------------
        words: List[str] = re.findall(r"[a-z']+", text.lower())
        total_words = max(len(words), 1)

        first_person_ratio     = sum(1 for w in words if w in FIRST_PERSON_WORDS) / total_words
        absolutist_ratio       = sum(1 for w in words if w in ABSOLUTIST_WORDS) / total_words
        negative_emotion_ratio = sum(1 for w in words if w in NEGATIVE_EMOTION_WORDS) / total_words
        text_length            = total_words
        avg_word_length        = sum(len(w) for w in words) / total_words if words else 0.0

        # ---------------------------------------------------------------
        # Step 3: Composite NLP risk score
        # ---------------------------------------------------------------
        nlp_risk_score = self._compute_risk_score(
            emotion_scores=emotion_scores,
            first_person_ratio=first_person_ratio,
            absolutist_ratio=absolutist_ratio,
            negative_emotion_ratio=negative_emotion_ratio,
        )

        return {
            "sentiment_label":        sentiment_label,
            "sentiment_confidence":   round(sentiment_confidence, 4),
            "dominant_emotion":       dominant_emotion,
            "emotions":               {k: round(v, 4) for k, v in emotion_scores.items()},
            "nlp_risk_score":         round(nlp_risk_score, 4),
            "first_person_ratio":     round(first_person_ratio, 4),
            "absolutist_ratio":       round(absolutist_ratio, 4),
            "negative_emotion_ratio": round(negative_emotion_ratio, 4),
            "text_length":            text_length,
            "avg_word_length":        round(avg_word_length, 2),
            "status":                 "analyzed",
        }

    @staticmethod
    def _parse_emotion_output(raw) -> Dict[str, float]:
        """
        Normalise the pipeline output into a flat {label: score} dict.

        Handles two formats:
          - New (top_k=None):  [[{"label": "joy", "score": 0.9}, ...]]
          - Legacy (single):   [{"label": "POSITIVE", "score": 0.9}]
        """
        # top_k=None returns a list-of-lists
        if raw and isinstance(raw[0], list):
            items = raw[0]
            return {item["label"].lower(): float(item["score"]) for item in items}

        # Single-result fallback (legacy SST-2 or fake pipeline in tests)
        item = raw[0]
        label = item["label"].upper()
        score = float(item["score"])
        if label == "NEGATIVE":
            return {
                "sadness": score * 0.5, "fear": score * 0.3,
                "disgust": score * 0.2, "anger": 0.0,
                "neutral": 0.0, "surprise": 0.0, "joy": 1.0 - score,
            }
        return {
            "joy": score, "neutral": 1.0 - score,
            "sadness": 0.0, "fear": 0.0,
            "disgust": 0.0, "anger": 0.0, "surprise": 0.0,
        }

    @staticmethod
    def _compute_risk_score(
        emotion_scores: Dict[str, float],
        first_person_ratio: float,
        absolutist_ratio: float,
        negative_emotion_ratio: float,
    ) -> float:
        """
        Combine emotion probabilities and linguistic signals into a risk score.

        Weighting:
          60% — emotion-based risk (weighted sum of 7 emotion probabilities)
          20% — negative emotion word ratio in the text
          12% — absolutist thinking (linguistic marker of depression)
           8% — first-person focus (elevated in depressive states)
        """
        # Emotion-based component
        emotion_risk = sum(
            EMOTION_RISK_WEIGHTS.get(label, 0.1) * prob
            for label, prob in emotion_scores.items()
        )
        # Clamp to [0,1] since weights don't sum to 1
        emotion_risk = max(0.0, min(1.0, emotion_risk))

        score = (
            0.60 * emotion_risk
            + 0.20 * min(negative_emotion_ratio * 8, 1.0)
            + 0.12 * min(absolutist_ratio * 12, 1.0)
            + 0.08 * min(first_person_ratio * 4, 1.0)
        )
        return max(0.0, min(1.0, score))

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        """Return a neutral result when no journal text is provided."""
        return {
            "sentiment_label":        "NEUTRAL",
            "sentiment_confidence":   0.0,
            "dominant_emotion":       "neutral",
            "emotions":               {e: 0.0 for e in EMOTION_RISK_WEIGHTS},
            "nlp_risk_score":         0.0,
            "first_person_ratio":     0.0,
            "absolutist_ratio":       0.0,
            "negative_emotion_ratio": 0.0,
            "text_length":            0,
            "avg_word_length":        0.0,
            "status":                 "no_journal",
        }
