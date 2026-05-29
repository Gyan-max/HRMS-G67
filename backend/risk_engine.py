"""
risk_engine.py — Weighted multi-factor risk scoring engine with personalized insights.

v2 improvements:
  - generate_observations() produces data-driven, number-specific observations
    that cite the user's actual values rather than generic template text.
  - Recommendations now open with these specific observations before adding
    actionable advice.
  - Sub-score calculators now accept the full features_dict so observations
    can reference exact numbers.
  - Safety override path unchanged (crisis resources always take priority).
"""

import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """
    Rule-based weighted risk scoring engine with personalized insight generation.

    Component weights (sum to 1.0 when all available):
      NLP sentiment    30%
      Behavioral anomaly 25%
      Sleep quality    18%
      Mood stability   17%
      Social engagement 10%
    """

    WEIGHTS = {
        "nlp":     0.30,
        "anomaly": 0.25,
        "sleep":   0.18,
        "mood":    0.17,
        "social":  0.10,
    }

    HIGH_THRESHOLD   = 0.65
    MEDIUM_THRESHOLD = 0.35

    COLOR_MAP = {
        "HIGH":   "#ff4444",
        "MEDIUM": "#ffaa00",
        "LOW":    "#00cc66",
    }

    # ------------------------------------------------------------------
    # SUB-SCORE CALCULATORS
    # ------------------------------------------------------------------

    @staticmethod
    def sleep_risk_score(avg_sleep: float, sleep_variance: float,
                         sleep_deficit_days: int) -> float:
        if avg_sleep < 5.0:      base = 0.9
        elif avg_sleep < 6.0:   base = 0.7
        elif avg_sleep < 7.0:   base = 0.4
        elif avg_sleep <= 9.0:  base = 0.1
        else:                    base = 0.5  # hypersomnia
        variance_penalty = max(0.0, (sleep_variance - 1.0) * 0.05)
        deficit_penalty  = sleep_deficit_days * 0.05
        return min(1.0, base + variance_penalty + deficit_penalty)

    @staticmethod
    def mood_risk_score(avg_mood: float, mood_trend: float,
                        mood_volatility: float, lowest_mood: float) -> float:
        if avg_mood < 4.0:      base = 0.9
        elif avg_mood < 5.0:   base = 0.7
        elif avg_mood < 6.0:   base = 0.5
        elif avg_mood < 7.0:   base = 0.3
        else:                   base = 0.1
        trend_penalty      = abs(mood_trend) * 0.15 if mood_trend < 0 else 0.0
        low_penalty        = 0.2 if lowest_mood <= 2 else (0.1 if lowest_mood <= 3 else 0.0)
        volatility_penalty = max(0.0, (mood_volatility - 2.0) * 0.05)
        return min(1.0, base + trend_penalty + low_penalty + volatility_penalty)

    @staticmethod
    def social_risk_score(avg_social: float, social_trend: float,
                          isolation_days: int) -> float:
        if avg_social < 1.0:      base = 0.9
        elif avg_social < 2.0:   base = 0.7
        elif avg_social < 4.0:   base = 0.4
        elif avg_social < 5.0:   base = 0.2
        else:                     base = 0.1
        isolation_penalty = isolation_days * 0.1
        trend_penalty     = abs(social_trend) * 0.1 if social_trend < 0 else 0.0
        return min(1.0, base + isolation_penalty + trend_penalty)

    # ------------------------------------------------------------------
    # MAIN RISK COMPUTATION
    # ------------------------------------------------------------------

    def compute_final_risk(
        self,
        nlp_score:               float,
        anomaly_score:           float,
        features_dict:           Dict[str, float],
        nlp_available:           bool = True,
        anomaly_available:       bool = True,
        safety_override:         bool = False,
        safety_matched_phrases:  Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute the final weighted risk assessment with personalized observations.
        """
        avg_sleep        = features_dict.get("avg_sleep",        7.0)
        sleep_variance   = features_dict.get("sleep_variance",   0.0)
        sleep_deficit_d  = int(features_dict.get("sleep_deficit_days", 0))
        avg_mood         = features_dict.get("avg_mood",         5.0)
        mood_trend       = features_dict.get("mood_trend",       0.0)
        mood_volatility  = features_dict.get("mood_volatility",  0.0)
        lowest_mood      = features_dict.get("lowest_mood",      5.0)
        avg_social       = features_dict.get("avg_social",       3.0)
        social_trend     = features_dict.get("social_trend",     0.0)
        isolation_days   = int(features_dict.get("isolation_days", 0))

        sleep_score  = self.sleep_risk_score(avg_sleep, sleep_variance, sleep_deficit_d)
        mood_score   = self.mood_risk_score(avg_mood, mood_trend, mood_volatility, lowest_mood)
        social_score = self.social_risk_score(avg_social, social_trend, isolation_days)

        component_scores = {
            "nlp":     round(nlp_score,    4),
            "anomaly": round(anomaly_score, 4),
            "sleep":   round(sleep_score,  4),
            "mood":    round(mood_score,   4),
            "social":  round(social_score, 4),
        }

        active_weights = self._active_weights(nlp_available, anomaly_available)
        final_score = round(
            max(0.0, min(1.0, sum(
                active_weights[k] * component_scores[k] for k in active_weights
            ))),
            4,
        )

        if final_score >= self.HIGH_THRESHOLD:      risk_level = "HIGH"
        elif final_score >= self.MEDIUM_THRESHOLD:  risk_level = "MEDIUM"
        else:                                        risk_level = "LOW"

        weighted_contributions = {
            k: active_weights[k] * component_scores[k] for k in active_weights
        }
        dominant_factor = (
            max(weighted_contributions, key=weighted_contributions.get)
            if weighted_contributions else "mood"
        )

        if safety_override:
            logger.warning(
                "risk_engine.safety_override_applied phrases=%s",
                list(safety_matched_phrases) if safety_matched_phrases else [],
            )
            risk_level      = "HIGH"
            final_score     = max(final_score, self.HIGH_THRESHOLD)
            dominant_factor = "safety"
            recommendation  = self._safety_override_recommendation(safety_matched_phrases)
            observations: List[str] = []
        else:
            observations   = self.generate_observations(features_dict, component_scores, risk_level)
            recommendation = self._generate_recommendation(
                risk_level, dominant_factor, component_scores, features_dict, observations
            )

        return {
            "final_score":       final_score,
            "risk_level":        risk_level,
            "component_scores":  component_scores,
            "dominant_factor":   dominant_factor,
            "recommendation":    recommendation,
            "observations":      observations,
            "color_code":        self.COLOR_MAP[risk_level],
            "safety_override":   bool(safety_override),
            "active_weights":    {k: round(v, 4) for k, v in active_weights.items()},
        }

    @classmethod
    def _active_weights(cls, nlp_available: bool = True,
                         anomaly_available: bool = True) -> Dict[str, float]:
        weights = dict(cls.WEIGHTS)
        if not nlp_available:     weights.pop("nlp",     None)
        if not anomaly_available: weights.pop("anomaly", None)
        total = sum(weights.values())
        if total <= 0:
            return dict(cls.WEIGHTS)
        return {k: v / total for k, v in weights.items()}

    # ------------------------------------------------------------------
    # PERSONALIZED OBSERVATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def generate_observations(
        features_dict:   Dict[str, float],
        component_scores: Dict[str, float],
        risk_level:      str,
    ) -> List[str]:
        """
        Generate specific, data-driven observations about the user's actual values.

        Each observation cites real numbers so the user knows exactly *why*
        a signal is flagged — not a generic template.
        """
        obs: List[str] = []

        avg_sleep    = features_dict.get("avg_sleep", 7.0)
        sleep_debt   = features_dict.get("sleep_debt", 0.0)
        sleep_streak = int(features_dict.get("consecutive_low_sleep_days", 0))
        avg_mood     = features_dict.get("avg_mood", 5.0)
        mood_trend   = features_dict.get("mood_trend", 0.0)
        mood_streak  = int(features_dict.get("consecutive_low_mood_days", 0))
        mood_drop    = features_dict.get("mood_drop_from_peak", 0.0)
        avg_social   = features_dict.get("avg_social", 3.0)
        iso_streak   = int(features_dict.get("social_isolation_streak", 0))
        cross_dis    = features_dict.get("cross_signal_distress", 0.0)

        # Sleep observations
        if avg_sleep < 5.5:
            obs.append(
                f"Average sleep this week: {avg_sleep:.1f}h — "
                f"{7.0 - avg_sleep:.1f}h below the 7h baseline. "
                "This level of deprivation impairs emotional regulation and decision-making."
            )
        elif avg_sleep < 6.5:
            obs.append(
                f"Average sleep: {avg_sleep:.1f}h/night ({7.0 - avg_sleep:.1f}h below baseline). "
                "Chronic mild deprivation accumulates faster than acute sleep loss."
            )
        if sleep_streak >= 3:
            obs.append(
                f"{sleep_streak} consecutive nights below 6h detected. "
                f"Cumulative sleep debt: approximately {sleep_debt:.0f}h."
            )
        elif sleep_debt >= 5:
            obs.append(f"Accumulated {sleep_debt:.0f}h of sleep debt this week vs the 7h nightly target.")

        # Mood observations
        if avg_mood < 4.0:
            obs.append(
                f"Average mood: {avg_mood:.1f}/10 — consistently in the low range. "
                "Sustained low mood (not just a bad day) is the primary clinical signal here."
            )
        elif avg_mood < 5.0:
            obs.append(f"Average mood score: {avg_mood:.1f}/10, below the neutral midpoint.")
        if mood_streak >= 3:
            obs.append(
                f"Mood has been below 5/10 for {mood_streak} consecutive days — "
                "a persistent pattern rather than an isolated dip."
            )
        if mood_trend < -0.3:
            days_estimated = max(3, round(abs(avg_mood / mood_trend))) if mood_trend != 0 else "?"
            obs.append(
                f"Mood trend: {mood_trend:+.2f} points/day — a consistent downward trajectory."
            )
        if mood_drop >= 3:
            obs.append(
                f"Mood has dropped {mood_drop:.0f} points from its recent high. "
                "Even a moderate current score can mask significant relative deterioration."
            )

        # Social observations
        if avg_social < 1.5:
            obs.append(
                f"Average social contact: {avg_social:.1f} interactions/day — "
                "near-total isolation. Social connection is one of the most powerful "
                "protective factors for mental health."
            )
        elif avg_social < 2.5:
            obs.append(f"Low social engagement detected — averaging {avg_social:.1f} interactions/day.")
        if iso_streak >= 3:
            obs.append(
                f"{iso_streak} consecutive days of near-total social isolation (≤1 interaction/day). "
                "Isolation and mood reinforce each other in a negative feedback loop."
            )

        # Cross-signal observation
        if cross_dis >= 0.67:
            obs.append(
                "Sleep, mood, and social contact are all simultaneously below healthy thresholds. "
                "Co-occurring signals amplify each other's impact."
            )

        # Cap at 4 observations to avoid overwhelming the user
        return obs[:4]

    # ------------------------------------------------------------------
    # RECOMMENDATION GENERATOR
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_recommendation(
        risk_level:       str,
        dominant_factor:  str,
        component_scores: Dict[str, float],
        features_dict:    Dict[str, float],
        observations:     List[str],
    ) -> str:
        """
        Build a recommendation that starts with the key observation (if any)
        and ends with specific, actionable advice matched to the dominant factor.
        """
        advice_map: Dict[str, Dict[str, str]] = {
            "HIGH": {
                "sleep": (
                    "Please speak with a healthcare professional about your sleep. "
                    "Sleep disruption at this level is both a symptom and a driver of mental health "
                    "challenges — addressing it with professional support makes a real difference."
                ),
                "mood": (
                    "Please reach out to a counselor or someone you trust today. "
                    "Sustained low mood responds well to early professional support — "
                    "you don't need to feel this way alone."
                ),
                "social": (
                    "Social isolation at this level is a major risk factor. "
                    "Please consider reaching out to one person today, or contacting "
                    "a helpline if connecting feels difficult right now."
                ),
                "nlp": (
                    "Your journal reflects patterns that warrant a conversation with a "
                    "mental health professional. Writing is healthy — but what you're writing "
                    "about suggests you'd benefit from additional support."
                ),
                "anomaly": (
                    "A significant behavioral shift from your baseline has been detected. "
                    "Sudden changes can be early warning signs. Please check in with a "
                    "counselor for a proactive conversation."
                ),
            },
            "MEDIUM": {
                "sleep": (
                    "Try setting a fixed bedtime ±30 min, avoiding screens 1h before sleep, "
                    "and keeping your room cool and dark. Small wins in sleep quality often "
                    "produce noticeable mood improvements within 3–4 days."
                ),
                "mood": (
                    "Consider a brief daily routine: 10 min of movement, a brief journal entry, "
                    "and one intentional connection with someone. These small anchors help "
                    "stabilize mood during mild dips."
                ),
                "social": (
                    "Try to reconnect with one person today — even a short message helps. "
                    "Social contact is one of the fastest-acting mood regulators available."
                ),
                "nlp": (
                    "Your journal reflects some emotional weight. Consider structured "
                    "journaling (write the thought, then challenge it) or discussing "
                    "these feelings with someone you trust."
                ),
                "anomaly": (
                    "Your behavior patterns have shifted from your usual routine. "
                    "Reflect on what's changed — maintaining consistent habits is a "
                    "strong foundation for mental stability."
                ),
            },
            "LOW": {
                "default": (
                    "Your indicators are within healthy ranges. "
                    "Keep up your routines — consistent sleep, regular social contact, and "
                    "physical movement are the most evidence-backed foundations of resilience. "
                    "Check in again tomorrow to maintain your streak."
                ),
            },
        }

        if risk_level == "LOW":
            base_advice = advice_map["LOW"]["default"]
        else:
            level_advice = advice_map.get(risk_level, advice_map["MEDIUM"])
            base_advice  = level_advice.get(dominant_factor, level_advice.get("mood", ""))

        # Prepend the top observation for context
        if observations:
            return f"{observations[0]}\n\n{base_advice}"
        return base_advice

    @staticmethod
    def _safety_override_recommendation(
        matched_phrases: Optional[Iterable[str]] = None,
    ) -> str:
        return (
            "Your journal entry contains language that suggests you may be "
            "experiencing thoughts of self-harm or hopelessness. You are not "
            "alone, and help is available right now. Please reach out:\n\n"
            "• iCall (India): 9152987821 — Mon-Sat 8am–10pm\n"
            "• AASRA (India): 9820466627 — 24/7\n"
            "• 988 Suicide & Crisis Lifeline (US): call or text 988\n"
            "• Samaritans (UK): 116 123 — 24/7\n"
            "• iCall WhatsApp: +91 9152987821\n\n"
            "If you are in immediate danger, please call your local emergency services. "
            "Talking to someone can make a real difference."
        )
