import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/api/client";
import { Card, CardContent } from "@/components/ui/card";
import type { CheckInRecord, RiskTrendPoint } from "@/api/types";

interface TrendsTabProps {
  userId: string;
}

const formatTime = (iso: string) => {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

/* Recharts 3.x typed its tooltip callbacks against ReactNode, which we
 * cope with by accepting `unknown` and coercing to string. */
const tooltipLabel = (label: unknown) =>
  typeof label === "string" ? formatTime(label) : String(label ?? "");

const tooltipValueNumber =
  (label: string) =>
  (value: unknown): [string, string] => [
    typeof value === "number" ? String(value) : String(value ?? ""),
    label,
  ];

const tooltipValueFixed =
  (label: string, fractionDigits: number) =>
  (value: unknown): [string, string] => [
    typeof value === "number" ? value.toFixed(fractionDigits) : String(value ?? ""),
    label,
  ];

const tooltipStyle = {
  background: "rgba(15, 18, 32, 0.96)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 12,
  fontSize: 12,
  padding: "8px 12px",
};

export function TrendsTab({ userId }: TrendsTabProps) {
  const trimmed = userId.trim();

  const historyQuery = useQuery({
    queryKey: ["history", trimmed, { days: 7 }],
    queryFn: () => api.getHistory(trimmed, { days: 7 }),
    enabled: trimmed.length > 0,
  });

  const trendQuery = useQuery({
    queryKey: ["trend", trimmed, { days: 30 }],
    queryFn: () => api.getRiskTrend(trimmed, 30),
    enabled: trimmed.length > 0,
  });

  if (!trimmed) {
    return (
      <EmptyState
        title="Enter a User ID and submit a check-in first"
        body="Trends populate once you have at least one check-in for this user."
      />
    );
  }

  if (historyQuery.isLoading || trendQuery.isLoading) {
    return <EmptyState title="Loading trends…" body="Fetching from backend." />;
  }

  if (historyQuery.isError || trendQuery.isError) {
    return (
      <EmptyState
        title="Couldn't load trends"
        body="Make sure the FastAPI backend is running on localhost:8000."
        tone="error"
      />
    );
  }

  const history = historyQuery.data;
  const trend = trendQuery.data;

  if (!history || history.total_records === 0) {
    return (
      <EmptyState
        title="No check-in data yet"
        body="Submit your first check-in to start seeing trends."
      />
    );
  }

  const sortedRecords = [...history.records].sort(
    (a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="p-6">
          <h4 className="font-display text-lg font-semibold">
            Mood score (1–10)
          </h4>
          <p className="text-sm text-muted-foreground">
            Last 7 days · self-rated mood from each check-in.
          </p>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={sortedRecords}
                margin={{ top: 10, right: 10, left: -8, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="mood-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatTime}
                  tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 11]}
                  tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  labelFormatter={tooltipLabel}
                  formatter={tooltipValueNumber("Mood")}
                />
                <Area
                  type="monotone"
                  dataKey="mood_score"
                  stroke="#6366f1"
                  strokeWidth={3}
                  fill="url(#mood-fill)"
                  dot={{ r: 4, fill: "#6366f1", strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h4 className="font-display text-lg font-semibold">
            Sleep hours (0–12)
          </h4>
          <p className="text-sm text-muted-foreground">
            Last 7 days · the dashed line is the 7-hour minimum.
          </p>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={sortedRecords}
                margin={{ top: 10, right: 10, left: -8, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="sleep-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatTime}
                  tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 12]}
                  tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                />
                <ReferenceLine
                  y={7}
                  stroke="rgba(16,185,129,0.5)"
                  strokeDasharray="4 4"
                  label={{
                    value: "7h minimum",
                    position: "right",
                    fill: "#6ee7b7",
                    fontSize: 10,
                  }}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  labelFormatter={tooltipLabel}
                  formatter={tooltipValueFixed("Sleep (hr)", 1)}
                />
                <Area
                  type="monotone"
                  dataKey="sleep_hours"
                  stroke="#22d3ee"
                  strokeWidth={3}
                  fill="url(#sleep-fill)"
                  dot={{ r: 4, fill: "#22d3ee", strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h4 className="font-display text-lg font-semibold">
            Social interactions
          </h4>
          <p className="text-sm text-muted-foreground">
            Last 7 days · meaningful contacts per day.
          </p>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <SocialChart records={sortedRecords} />
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h4 className="font-display text-lg font-semibold">
            Risk-score trend (30 days)
          </h4>
          <p className="text-sm text-muted-foreground">
            Lower is better. Dashed lines mark MEDIUM (0.35) and HIGH (0.65)
            thresholds.
          </p>
          <div className="mt-5 h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <RiskTrendChart points={trend?.data_points ?? []} />
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SocialChart({ records }: { records: CheckInRecord[] }) {
  return (
    <LineChart
      data={records}
      margin={{ top: 10, right: 10, left: -8, bottom: 0 }}
    >
      <CartesianGrid stroke="rgba(255,255,255,0.06)" />
      <XAxis
        dataKey="timestamp"
        tickFormatter={formatTime}
        tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
        stroke="rgba(255,255,255,0.15)"
        tickLine={false}
      />
      <YAxis
        domain={[0, "dataMax"]}
        allowDecimals={false}
        tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
        stroke="rgba(255,255,255,0.15)"
        tickLine={false}
      />
      <Tooltip
        contentStyle={tooltipStyle}
        labelFormatter={tooltipLabel}
        formatter={tooltipValueNumber("Contacts")}
      />
      <Line
        type="monotone"
        dataKey="social_interactions"
        stroke="#14b8a6"
        strokeWidth={3}
        dot={{ r: 4, fill: "#14b8a6", strokeWidth: 0 }}
        activeDot={{ r: 6 }}
      />
    </LineChart>
  );
}

function RiskTrendChart({ points }: { points: RiskTrendPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Not enough history yet — submit a few check-ins to see the trend.
      </div>
    );
  }

  const data = [...points].sort(
    (a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  return (
    <AreaChart data={data} margin={{ top: 10, right: 10, left: -8, bottom: 0 }}>
      <defs>
        <linearGradient id="risk-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.35} />
          <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
        </linearGradient>
      </defs>
      <CartesianGrid stroke="rgba(255,255,255,0.06)" />
      <XAxis
        dataKey="timestamp"
        tickFormatter={formatTime}
        tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
        stroke="rgba(255,255,255,0.15)"
        tickLine={false}
      />
      <YAxis
        domain={[0, 1]}
        tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
        stroke="rgba(255,255,255,0.15)"
        tickLine={false}
      />
      <ReferenceLine
        y={0.35}
        stroke="rgba(245,158,11,0.5)"
        strokeDasharray="4 4"
        label={{
          value: "MEDIUM",
          position: "right",
          fill: "#fcd34d",
          fontSize: 10,
        }}
      />
      <ReferenceLine
        y={0.65}
        stroke="rgba(244,63,94,0.5)"
        strokeDasharray="4 4"
        label={{
          value: "HIGH",
          position: "right",
          fill: "#fda4af",
          fontSize: 10,
        }}
      />
      <Tooltip
        contentStyle={tooltipStyle}
        labelFormatter={tooltipLabel}
        formatter={tooltipValueFixed("Risk score", 3)}
      />
      <Area
        type="monotone"
        dataKey="risk_score"
        stroke="#f43f5e"
        strokeWidth={3}
        fill="url(#risk-fill)"
        dot={{ r: 4, fill: "#f43f5e", strokeWidth: 0 }}
      />
    </AreaChart>
  );
}

function EmptyState({
  title,
  body,
  tone,
}: {
  title: string;
  body: string;
  tone?: "error";
}) {
  return (
    <Card
      className={
        tone === "error"
          ? "border-brand-rose/30 bg-brand-rose/[0.05]"
          : undefined
      }
    >
      <CardContent className="p-10 text-center">
        <h4 className="font-display text-lg font-semibold">{title}</h4>
        <p className="mt-2 text-sm text-muted-foreground">{body}</p>
      </CardContent>
    </Card>
  );
}
