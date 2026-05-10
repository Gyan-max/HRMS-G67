/**
 * TypeScript mirrors of the Pydantic schemas in `backend/schemas.py`.
 *
 * Keeping these in sync with the backend is currently a manual exercise.
 * Running `npx openapi-typescript http://localhost:8000/openapi.json -o
 * src/api/types.generated.ts` is on the roadmap once
 * openapi-typescript supports TypeScript 6.x.
 */

export type ActivityLevel = "sedentary" | "light" | "moderate" | "active";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type TrendDirection = "IMPROVING" | "STABLE" | "WORSENING";

/** POST /api/checkin */
export interface CheckInRequest {
  user_id: string;
  /** 0.0 – 12.0 */
  sleep_hours: number;
  /** Integer 1 – 10 */
  mood_score: number;
  activity_level: ActivityLevel;
  /** Integer 0 – 30 */
  social_interactions: number;
  journal_text?: string | null;
}

/** Component sub-scores: sleep, mood, social, nlp, anomaly (0 – 1 each). */
export type ComponentScores = Record<string, number>;

export interface NlpAnalysis {
  status?: "no_journal" | "ok" | string;
  sentiment_label?: string;
  sentiment_confidence?: number;
  nlp_risk_score?: number;
  text_length?: number;
  first_person_ratio?: number;
  absolutist_ratio?: number;
  negative_emotion_ratio?: number;
  [key: string]: unknown;
}

/** Response of POST /api/checkin */
export interface CheckInResponse {
  user_id: string;
  /** ISO 8601 timestamp */
  timestamp: string;
  risk_level: RiskLevel;
  risk_score: number;
  component_scores: ComponentScores;
  recommendation: string;
  nlp_analysis: NlpAnalysis;
  anomaly_detected: boolean;
  days_tracked: number;
  dominant_factor?: string | null;
  color_code?: string | null;
  safety_override: boolean;
}

export interface CheckInRecord {
  id: number;
  user_id: string;
  timestamp: string;
  sleep_hours: number;
  mood_score: number;
  activity_level: string;
  social_interactions: number;
  journal_text?: string | null;
  risk_score?: number | null;
  risk_level?: RiskLevel | null;
}

/** Response of GET /api/history/{user_id} */
export interface HistoryResponse {
  user_id: string;
  total_records: number;
  records: CheckInRecord[];
}

/** Response of GET /api/stats/{user_id} */
export interface UserStatsResponse {
  user_id: string;
  avg_risk: number;
  highest_risk_day?: string | null;
  trend_direction: TrendDirection;
  total_days: number;
  avg_sleep?: number | null;
  avg_mood?: number | null;
  avg_social?: number | null;
  low_risk_streak: number;
}

export interface RiskTrendPoint {
  timestamp: string;
  risk_score: number;
}

/** Response of GET /api/risk-trend/{user_id} */
export interface RiskTrendResponse {
  user_id: string;
  data_points: RiskTrendPoint[];
}

/** Response of GET /health */
export interface HealthCheckResponse {
  status: string;
  version: string;
  models_loaded: boolean;
}
