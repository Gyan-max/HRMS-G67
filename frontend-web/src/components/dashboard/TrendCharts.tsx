import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { Moon, Heart, Users, Activity, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface TrendData {
  timestamp: string;
  mood_score: number;
  sleep_hours: number;
  social_interactions: number;
  risk_score: number;
  risk_level: string;
}

interface TrendChartsProps {
  data: TrendData[];
}

const TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: "#111827",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "12px",
    fontSize: "12px",
    boxShadow: "0 16px 40px -12px rgba(0,0,0,0.7)",
  },
  labelStyle: { color: "rgba(255,255,255,0.5)", marginBottom: 4 },
};

export function TrendCharts({ data }: TrendChartsProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-3 p-10 text-center">
          <Activity className="h-8 w-8 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            No trends yet. Submit a check-in to unlock your 7-day behavioral charts.
          </p>
        </CardContent>
      </Card>
    );
  }

  const chartData = data
    .map((d) => ({
      ...d,
      displayDate: new Date(d.timestamp).toLocaleDateString([], {
        month: "short",
        day: "numeric",
      }),
    }))
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const latest = chartData[chartData.length - 1];
  const latestRiskLevel = latest?.risk_level ?? "LOW";
  const latestRisk = latest?.risk_score ?? 0;
  const avgRisk =
    chartData.reduce((sum, row) => sum + (row.risk_score || 0), 0) /
    chartData.length;
  const firstRisk = chartData[0]?.risk_score ?? latestRisk;
  const delta = latestRisk - firstRisk;

  const trendDir =
    delta > 0.05 ? "Worsening" : delta < -0.05 ? "Improving" : "Stable";
  const trendIcon =
    delta > 0.05 ? (
      <TrendingUp className="h-3.5 w-3.5" />
    ) : delta < -0.05 ? (
      <TrendingDown className="h-3.5 w-3.5" />
    ) : (
      <Minus className="h-3.5 w-3.5" />
    );

  const remarkVariant =
    latestRiskLevel === "HIGH"
      ? "danger"
      : latestRiskLevel === "MEDIUM"
        ? "warning"
        : "success";

  const remarkText =
    latestRiskLevel === "HIGH"
      ? "Risk is elevated. Prioritize rest, support, and follow recommendations."
      : latestRiskLevel === "MEDIUM"
        ? "Moderate risk. Small consistent interventions can stabilize trajectory."
        : "Low risk. Keep routines steady to preserve momentum.";

  const axisProps = {
    stroke: "rgba(255,255,255,0.2)",
    fontSize: 11,
    tickLine: false as const,
    axisLine: false as const,
  };

  const gridProps = {
    strokeDasharray: "3 3" as const,
    stroke: "rgba(255,255,255,0.05)",
    vertical: false as const,
  };

  return (
    <div className="space-y-4">
      {/* Summary pill */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={remarkVariant}>{latestRiskLevel} risk</Badge>
            <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium text-muted-foreground">
              {trendIcon}
              {trendDir}
            </div>
            <span className="text-xs text-muted-foreground">
              Latest{" "}
              <span className="font-medium text-foreground">
                {(latestRisk * 100).toFixed(0)}%
              </span>{" "}
              · Avg{" "}
              <span className="font-medium text-foreground">
                {(avgRisk * 100).toFixed(0)}%
              </span>
            </span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{remarkText}</p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Mood */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-indigo/15 text-brand-indigo">
                <Heart className="h-3.5 w-3.5" />
              </div>
              Mood Trend (1–10)
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Sustained dips below 4 are a key risk signal.
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="displayDate" {...axisProps} />
                  <YAxis {...axisProps} domain={[0, 10]} />
                  <Tooltip
                    {...TOOLTIP_STYLE}
                    itemStyle={{ color: "#6366f1" }}
                  />
                  <ReferenceLine
                    y={4}
                    stroke="rgba(244,63,94,0.35)"
                    strokeDasharray="4 4"
                  />
                  <Line
                    type="monotone"
                    dataKey="mood_score"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    dot={{ fill: "#6366f1", strokeWidth: 0, r: 3 }}
                    activeDot={{ r: 5, strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Sleep */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-cyan/15 text-brand-cyan">
                <Moon className="h-3.5 w-3.5" />
              </div>
              Sleep Hours
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Target band: 7–9 hours per night.
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="sleepGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="displayDate" {...axisProps} />
                  <YAxis {...axisProps} domain={[0, 12]} />
                  <Tooltip
                    {...TOOLTIP_STYLE}
                    itemStyle={{ color: "#22d3ee" }}
                  />
                  <ReferenceLine
                    y={7}
                    stroke="rgba(16,185,129,0.4)"
                    strokeDasharray="4 4"
                    label={{
                      value: "7h",
                      position: "insideTopRight",
                      fill: "rgba(16,185,129,0.7)",
                      fontSize: 10,
                    }}
                  />
                  <ReferenceLine
                    y={9}
                    stroke="rgba(16,185,129,0.25)"
                    strokeDasharray="4 4"
                    label={{
                      value: "9h",
                      position: "insideTopRight",
                      fill: "rgba(16,185,129,0.5)",
                      fontSize: 10,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="sleep_hours"
                    stroke="#22d3ee"
                    strokeWidth={2.5}
                    fill="url(#sleepGrad)"
                    dot={{ fill: "#22d3ee", strokeWidth: 0, r: 3 }}
                    activeDot={{ r: 5, strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Social */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-teal/15 text-brand-teal">
                <Users className="h-3.5 w-3.5" />
              </div>
              Social Contact
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Isolation accelerates risk faster than any other signal.
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="displayDate" {...axisProps} />
                  <YAxis {...axisProps} />
                  <Tooltip
                    {...TOOLTIP_STYLE}
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                  />
                  <Bar dataKey="social_interactions" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell
                        key={`cell-${i}`}
                        fill={
                          entry.social_interactions <= 1
                            ? "#f43f5e"
                            : entry.social_interactions <= 3
                              ? "#f59e0b"
                              : "#10b981"
                        }
                        fillOpacity={0.75}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Risk score */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-rose/15 text-brand-rose">
                <Activity className="h-3.5 w-3.5" />
              </div>
              Risk Intensity
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Thresholds: Low &lt;35% · Medium 35–65% · High &gt;65%.
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="displayDate" {...axisProps} />
                  <YAxis {...axisProps} domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip
                    {...TOOLTIP_STYLE}
                    itemStyle={{ color: "#f43f5e" }}
                    formatter={(v) => [`${((Number(v) || 0) * 100).toFixed(1)}%`, "Risk"]}
                  />
                  <ReferenceLine
                    y={0.65}
                    stroke="rgba(244,63,94,0.4)"
                    strokeDasharray="4 4"
                    label={{ value: "High", position: "insideTopRight", fill: "rgba(244,63,94,0.7)", fontSize: 10 }}
                  />
                  <ReferenceLine
                    y={0.35}
                    stroke="rgba(245,158,11,0.35)"
                    strokeDasharray="4 4"
                    label={{ value: "Med", position: "insideTopRight", fill: "rgba(245,158,11,0.6)", fontSize: 10 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="risk_score"
                    stroke="#f43f5e"
                    strokeWidth={2.5}
                    dot={{ fill: "#f43f5e", strokeWidth: 0, r: 3 }}
                    activeDot={{ r: 5, strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
