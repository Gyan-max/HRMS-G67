"""
risk_engine.py — Weighted multi-factor risk scoring engine.

Combines NLP, anomaly detection, sleep, mood, and social risk sub-scores
into a final weighted risk assessment. Acts as the rule-based fallback
(and complement) to the ML classifier. Generates human-readable
recommendations based on the dominant risk factor.

The engine also supports a *safety override* path: when an upstream
safety screen flags suicidal ideation or self-harm content, the risk
level is forced to HIGH and a crisis-resource recommendation is
emitted, regardless of how the weighted components would otherwise
score.
"""

import logging
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """
    Rule-based weighted risk scoring engine.

    Computes a composite risk score from five behavioral dimensions:
      - NLP sentiment analysis (30%)
      - Behavioral anomaly detection (25%)
      - Sleep quality (18%)
      - Mood stability (17%)
      - Social engagement (10%)

    The weights reflect clinical research on the relative predictive
    power of each signal for mental health deterioration.

    Usage::

        engine = RiskScoringEngine()
        result = engine.compute_final_risk(
            nlp_score=0.7, anomaly_score=0.3, features_dict={...}
        )
    """

    # Component weights — must sum to 1.0 when ALL components are available.
    # When some components are unavailable (e.g. no journal text → no NLP
    # signal, or fewer than 5 days of history → no anomaly signal), the
    # remaining weights are re-normalised so the final score is still on a
    # 0-1 scale instead of being silently deflated.
    WEIGHTS = {
        "nlp": 0.30,
        "anomaly": 0.25,
        "sleep": 0.18,
        "mood": 0.17,
        "social": 0.10,
    }

    # Risk level thresholds
    HIGH_THRESHOLD = 0.65
    MEDIUM_THRESHOLD = 0.35

    # Color codes for UI display
    COLOR_MAP = {
        "HIGH": "#ff4444",
        "MEDIUM": "#ffaa00",
        "LOW": "#00cc66",
    }

    # ------------------------------------------------------------------
    # SUB-SCORE CALCULATORS
    # ------------------------------------------------------------------

    @staticmethod
    def sleep_risk_score(avg_sleep: float, sleep_variance: float,
                         sleep_deficit_days: int) -> float:
        """
        Compute sleep-related risk score.

        Clinical logic:
          - < 5 hrs average: severe sleep deprivation → very high risk
          - 5–6 hrs: chronic mild deprivation → elevated risk
          - > 9 hrs: hypersomnia (possible depression marker) → moderate risk
          - 7–9 hrs: healthy range → low risk

        Penalties are added for high variance (irregular sleep) and
        for days with < 6 hrs (deficit days).
        """
        # Base score from average sleep hours
        if avg_sleep < 5.0:
            base = 0.9
        elif avg_sleep < 6.0:
            base = 0.7
        elif avg_sleep < 7.0:
            base = 0.4
        elif avg_sleep <= 9.0:
            base = 0.1
        else:
            # Hypersomnia — sleeping too much can indicate depression
            base = 0.5

        # Variance penalty: irregular sleep is concerning even if average is OK
        variance_penalty = max(0.0, (sleep_variance - 1.0) * 0.05)

        # Deficit day penalty: each day below 6hrs adds risk
        deficit_penalty = sleep_deficit_days * 0.05

        return min(1.0, base + variance_penalty + deficit_penalty)

    @staticmethod
    def mood_risk_score(avg_mood: float, mood_trend: float,
                        mood_volatility: float, lowest_mood: float) -> float:
        """
        Compute mood-related risk score.

        Clinical logic:
          - avg_mood < 4: severely low mood → very high risk
          - 4–5: moderately low → elevated risk
          - 5–6: mild concern → moderate risk
          - ≥ 7: healthy range → low risk

        Declining trend (negative slope) and extreme lows are penalized.
        """
        # Base score from average mood
        if avg_mood < 4.0:
            base = 0.9
        elif avg_mood < 5.0:
            base = 0.7
        elif avg_mood < 6.0:
            base = 0.5
        elif avg_mood < 7.0:
            base = 0.3
        else:
            base = 0.1

        # Trend penalty: negative slope means mood is declining over time
        trend_penalty = 0.0
        if mood_trend < 0:
            trend_penalty = abs(mood_trend) * 0.15

        # Extreme low penalty: a single very bad day is clinically significant
        low_penalty = 0.0
        if lowest_mood <= 2:
            low_penalty = 0.2
        elif lowest_mood <= 3:
            low_penalty = 0.1

        # Volatility bonus: large mood swings add moderate risk
        volatility_penalty = max(0.0, (mood_volatility - 2.0) * 0.05)

        return min(1.0, base + trend_penalty + low_penalty + volatility_penalty)

    @staticmethod
    def social_risk_score(avg_social: float, social_trend: float,
                          isolation_days: int) -> float:
        """
        Compute social engagement risk score.

        Clinical logic:
          - < 1 avg interactions: severe isolation → very high risk
          - 1–2: mild isolation → elevated risk
          - 2–4: moderate engagement → moderate risk
          - ≥ 5: healthy social life → low risk

        Each day of isolation (≤ 1 interaction) adds incremental risk.
        """
        # Base score from average social interactions
        if avg_social < 1.0:
            base = 0.9
        elif avg_social < 2.0:
            base = 0.7
        elif avg_social < 4.0:
            base = 0.4
        elif avg_social < 5.0:
            base = 0.2
        else:
            base = 0.1

        # Isolation day penalty
        isolation_penalty = isolation_days * 0.1

        # Declining social trend
        trend_penalty = 0.0
        if social_trend < 0:
            trend_penalty = abs(social_trend) * 0.1

        return min(1.0, base + isolation_penalty + trend_penalty)

    # ------------------------------------------------------------------
    # MAIN RISK COMPUTATION
    # ------------------------------------------------------------------

    def compute_final_risk(
        self,
        nlp_score: float,
        anomaly_score: float,
        features_dict: Dict[str, float],
        nlp_available: bool = True,
        anomaly_available: bool = True,
        safety_override: bool = False,
        safety_matched_phrases: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute the final weighted risk assessment.

        Combines all sub-scores using predefined weights, determines
        the risk level, identifies the dominant risk factor, and
        generates a targeted recommendation.

        Args:
            nlp_score: NLP risk score (0-1) from journal analysis.
            anomaly_score: Anomaly normalized risk (0-1).
            features_dict: Dict of extracted behavioral features
                          (from feature_engineering.extract_features).
            nlp_available: True iff a non-empty journal was provided AND
                          the NLP pipeline produced a result. When False,
                          the NLP weight is dropped and remaining weights
                          are re-normalised.
            anomaly_available: True iff the anomaly detector is fitted
                          AND produced an analysed result. When False,
                          the anomaly weight is dropped and remaining
                          weights are re-normalised.
            safety_override: When True, the safety screen has flagged
                          self-harm / suicidal-ideation content and the
                          final risk level is forced to HIGH regardless
                          of the weighted score.
            safety_matched_phrases: Optional list of matched phrases
                          from the safety screen, used to enrich the
                          dominant_factor / recommendation.

        Returns:
            Comprehensive risk assessment dictionary.
        """
        # Extract individual features with safe defaults
        avg_sleep = features_dict.get("avg_sleep", 7.0)
        sleep_variance = features_dict.get("sleep_variance", 0.0)
        sleep_deficit_days = int(features_dict.get("sleep_deficit_days", 0))

        avg_mood = features_dict.get("avg_mood", 5.0)
        mood_trend = features_dict.get("mood_trend", 0.0)
        mood_volatility = features_dict.get("mood_volatility", 0.0)
        lowest_mood = features_dict.get("lowest_mood", 5.0)

        avg_social = features_dict.get("avg_social", 3.0)
        social_trend = features_dict.get("social_trend", 0.0)
        isolation_days = int(features_dict.get("isolation_days", 0))

        # Compute component sub-scores
        sleep_score = self.sleep_risk_score(avg_sleep, sleep_variance, sleep_deficit_days)
        mood_score = self.mood_risk_score(avg_mood, mood_trend, mood_volatility, lowest_mood)
        social_score = self.social_risk_score(avg_social, social_trend, isolation_days)

        # Assemble component scores dict (rounded for response payloads)
        component_scores = {
            "nlp": round(nlp_score, 4),
            "anomaly": round(anomaly_score, 4),
            "sleep": round(sleep_score, 4),
            "mood": round(mood_score, 4),
            "social": round(social_score, 4),
        }

        # Re-normalise weights over the components that are actually available
        # so missing journal / insufficient history doesn't silently halve
        # the final score for the most vulnerable users.
        active_weights = self._active_weights(
            nlp_available=nlp_available,
            anomaly_available=anomaly_available,
        )

        final_score = sum(
            active_weights[key] * component_scores[key]
            for key in active_weights
        )
        final_score = round(max(0.0, min(1.0, final_score)), 4)

        # Determine risk level from the weighted score
        if final_score >= self.HIGH_THRESHOLD:
            risk_level = "HIGH"
        elif final_score >= self.MEDIUM_THRESHOLD:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Identify dominant risk factor (highest contributing component)
        weighted_contributions = {
            key: active_weights[key] * component_scores[key]
            for key in active_weights
        }
        dominant_factor = (
            max(weighted_contributions, key=weighted_contributions.get)
            if weighted_contributions
            else "mood"
        )

        # ------------------------------------------------------------------
        # SAFETY OVERRIDE: when the upstream safety screen flags suicidal
        # ideation / self-harm content we unconditionally escalate to HIGH
        # and emit a crisis-resource recommendation. The numeric score is
        # bumped up to (at least) the HIGH_THRESHOLD so downstream charts
        # and alerts agree with the categorical level.
        # ------------------------------------------------------------------
        if safety_override:
            logger.warning(
                "risk_engine.safety_override_applied phrases=%s",
                list(safety_matched_phrases) if safety_matched_phrases else [],
            )
            risk_level = "HIGH"
            final_score = max(final_score, self.HIGH_THRESHOLD)
            dominant_factor = "safety"
            recommendation = self._safety_override_recommendation(
                safety_matched_phrases
            )
        else:
            recommendation = self._generate_recommendation(
                risk_level, dominant_factor, component_scores
            )

        return {
            "final_score": final_score,
            "risk_level": risk_level,
            "component_scores": component_scores,
            "dominant_factor": dominant_factor,
            "recommendation": recommendation,
            "color_code": self.COLOR_MAP[risk_level],
            "safety_override": bool(safety_override),
            "active_weights": {k: round(v, 4) for k, v in active_weights.items()},
        }

    @classmethod
    def _active_weights(
        cls,
        nlp_available: bool = True,
        anomaly_available: bool = True,
    ) -> Dict[str, float]:
        """
        Return component weights re-normalised over only the available
        components.

        If every component is unavailable (shouldn't happen — sleep / mood /
        social are always available because they come from the request
        itself) we fall back to the full WEIGHTS dict to avoid division by
        zero.
        """
        weights = dict(cls.WEIGHTS)
        if not nlp_available:
            weights.pop("nlp", None)
        if not anomaly_available:
            weights.pop("anomaly", None)

        total = sum(weights.values())
        if total <= 0:
            return dict(cls.WEIGHTS)
        return {k: v / total for k, v in weights.items()}

    # ------------------------------------------------------------------
    # RECOMMENDATION GENERATOR
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_recommendation(risk_level: str, dominant_factor: str,
                                  component_scores: Dict[str, float]) -> str:
        """
        Generate a specific, actionable recommendation based on risk level
        and the dominant contributing factor.

        Recommendations are designed to be empathetic, non-diagnostic,
        and action-oriented.
        """
        recommendations = {
            "HIGH": {
                "sleep": (
                    "Your sleep patterns show serious disruption over the past 7 days. "
                    "Combined with other behavioral signals, this warrants speaking with "
                    "a healthcare professional. Poor sleep is both a symptom and a driver "
                    "of mental health challenges — addressing it early makes a real difference."
                ),
                "mood": (
                    "A consistent decline in mood has been detected across multiple days. "
                    "Please reach out to a counselor or trusted person today. You don't have "
                    "to feel this way alone — professional support can provide concrete strategies "
                    "to help you feel better."
                ),
                "social": (
                    "Significant social withdrawal has been detected. Isolation is one of the "
                    "strongest risk factors for mental health deterioration. Please consider "
                    "reaching out to someone you trust, or contacting a helpline if you're "
                    "finding it hard to connect."
                ),
                "nlp": (
                    "Your journal entries reflect patterns of distress that our analysis has "
                    "flagged as concerning. Writing about your feelings is a healthy coping "
                    "mechanism, but the patterns suggest you may benefit from speaking with "
                    "a mental health professional."
                ),
                "anomaly": (
                    "We've detected a significant shift in your behavioral patterns compared "
                    "to your baseline. Sudden changes can be early warning signs. Please check "
                    "in with yourself and consider reaching out to a counselor for a proactive "
                    "conversation."
                ),
            },
            "MEDIUM": {
                "sleep": (
                    "Your sleep quality has been inconsistent recently. Try setting a consistent "
                    "bedtime, limiting screens an hour before sleep, and aiming for 7–9 hours. "
                    "Small improvements in sleep often lead to noticeable mood gains."
                ),
                "mood": (
                    "Your mood has been fluctuating or trending slightly lower. This is common "
                    "and manageable — consider keeping a gratitude journal, getting some light "
                    "exercise, or talking to a friend about how you're feeling."
                ),
                "social": (
                    "Social withdrawal patterns are emerging. Try reconnecting with one person "
                    "today — even a short message helps. Social connection is one of the most "
                    "powerful protective factors for mental well-being."
                ),
                "nlp": (
                    "Your journal reflects some emotional challenges. This awareness is valuable. "
                    "Consider exploring structured journaling techniques like CBT thought records, "
                    "or discussing these feelings with someone you trust."
                ),
                "anomaly": (
                    "Your recent behavior patterns differ from your usual routine. While change "
                    "isn't always negative, it's worth reflecting on what might have shifted. "
                    "Maintaining consistent routines supports mental stability."
                ),
            },
            "LOW": {
                "default": (
                    "You're doing well! Your behavioral indicators are within healthy ranges. "
                    "Keep up your current routines — consistent sleep, social connection, and "
                    "physical activity are the foundation of mental resilience. Check in again "
                    "tomorrow to maintain your streak!"
                ),
            },
        }

        if risk_level == "LOW":
            return recommendations["LOW"]["default"]

        level_recs = recommendations.get(risk_level, recommendations["MEDIUM"])
        return level_recs.get(dominant_factor, level_recs.get("mood", "Please take care of yourself today."))

    @staticmethod
    def _safety_override_recommendation(
        matched_phrases: Optional[Iterable[str]] = None,
    ) -> str:
        """
        Recommendation emitted whenever the safety screen has triggered.

        We deliberately do NOT echo the matched phrases back to the user —
        seeing one's own crisis language quoted back can be retraumatising.
        The phrases are preserved in logs / API responses for audit, but
        the user-facing text is empathetic and action-oriented.
        """
        return (
            "Your journal entry contains language that suggests you may be "
            "experiencing thoughts of self-harm or hopelessness. You are not "
            "alone, and help is available right now. Please reach out:\n\n"
            "• 🇮🇳 iCall: 9152987821 (Mon-Sat, 8am-10pm)\n"
            "• 🇮🇳 AASRA: 9820466726 (24/7)\n"
            "• 🇺🇸 988 Suicide & Crisis Lifeline: call or text 988\n"
            "• 🇬🇧 Samaritans: 116 123\n\n"
            "If you are in immediate danger, please call your local emergency "
            "services. Talking to someone can make a real difference."
        )
