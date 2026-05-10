/**
 * Tiny typed wrapper around `fetch` for the FastAPI backend.
 *
 * We deliberately avoid Axios here — the API surface is small and `fetch`
 * keeps the bundle lean. All endpoints are typed against `./types.ts`.
 */

import { API_BASE_URL } from "@/lib/constants";
import type {
  CheckInRequest,
  CheckInResponse,
  HealthCheckResponse,
  HistoryResponse,
  RiskTrendResponse,
  UserStatsResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  method: "GET" | "POST" | "DELETE",
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...init,
  });

  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = await response.text().catch(() => null);
    }
    const message =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : `HTTP ${response.status} from ${method} ${path}`;
    throw new ApiError(response.status, payload, message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** ----- Endpoint helpers ------------------------------------------------- */

export const api = {
  health: () => request<HealthCheckResponse>("GET", "/health"),

  submitCheckIn: (payload: CheckInRequest) =>
    request<CheckInResponse>("POST", "/api/checkin", payload),

  getHistory: (userId: string, opts: { days?: number; limit?: number } = {}) => {
    const params = new URLSearchParams();
    if (opts.days != null) params.set("days", String(opts.days));
    if (opts.limit != null) params.set("limit", String(opts.limit));
    const qs = params.toString();
    return request<HistoryResponse>(
      "GET",
      `/api/history/${encodeURIComponent(userId)}${qs ? `?${qs}` : ""}`,
    );
  },

  getStats: (userId: string) =>
    request<UserStatsResponse>(
      "GET",
      `/api/stats/${encodeURIComponent(userId)}`,
    ),

  getRiskTrend: (userId: string, days = 30) =>
    request<RiskTrendResponse>(
      "GET",
      `/api/risk-trend/${encodeURIComponent(userId)}?days=${days}`,
    ),

  deleteUser: (userId: string) =>
    request<void>("DELETE", `/api/user/${encodeURIComponent(userId)}`),
};
