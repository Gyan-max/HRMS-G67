import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Wrench,
  Activity,
  Calendar,
  Heart,
  Zap,
  UserCircle2,
  AlertTriangle,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckInForm } from "@/components/dashboard/CheckInForm";
import { TrendCharts } from "@/components/dashboard/TrendCharts";
import { HistoryLog } from "@/components/dashboard/HistoryLog";

interface UserStats {
  avg_risk: number;
  total_days: number;
  low_risk_streak: number;
  trend_direction: string;
}

interface HistoryRecord {
  timestamp: string;
  mood_score: number;
  sleep_hours: number;
  social_interactions: number;
  risk_score: number;
  risk_level: string;
  activity_level: string;
}

interface HistoryResponse {
  records?: HistoryRecord[];
}

function getRiskBadgeVariant(level: string): "danger" | "warning" | "success" {
  if (level === "HIGH") return "danger";
  if (level === "MEDIUM") return "warning";
  return "success";
}

/**
 * Dashboard page featuring live check-in, trends, and history.
 */
export default function Dashboard() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [userId, setUserId] = useState("user_001");
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const streamlitUrl =
    import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";

  const fetchData = useCallback(async () => {
    const normalizedUserId = userId.trim();
    if (!normalizedUserId) {
      setStats(null);
      setHistory([]);
      setLoadError(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch(`${apiBaseUrl}/api/stats/${encodeURIComponent(normalizedUserId)}`),
        fetch(`${apiBaseUrl}/api/history/${encodeURIComponent(normalizedUserId)}?days=30`),
      ]);

      if (!statsRes.ok || !historyRes.ok) {
        throw new Error("Unable to fetch dashboard data");
      }

      const nextStats = (await statsRes.json()) as UserStats;
      const historyData = (await historyRes.json()) as HistoryResponse;
      setStats(nextStats);
      setHistory(historyData.records || []);
    } catch (err: unknown) {
      console.error("Failed to fetch dashboard data:", err);
      setLoadError(
        err instanceof Error ? err.message : "Failed to load dashboard data",
      );
      setStats(null);
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, userId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

  // Callback to refresh dashboard data after a new check-in
  const onCheckInSubmitted = () => {
    fetchData();
  };

  const latestRecord = useMemo(() => {
    if (!history.length) return null;
    return [...history].sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )[0];
  }, [history]);

  const latestRiskLevel = latestRecord?.risk_level ?? "LOW";
  const latestRiskScore = latestRecord?.risk_score ?? 0;
  const trendDirection = (stats?.trend_direction ?? "STABLE").toUpperCase();

  const trendIcon =
    trendDirection === "WORSENING" ? (
      <TrendingUp className="h-4 w-4 text-brand-rose" />
    ) : trendDirection === "IMPROVING" ? (
      <TrendingDown className="h-4 w-4 text-brand-emerald" />
    ) : (
      <Minus className="h-4 w-4 text-muted-foreground" />
    );

  return (
    <div className="container space-y-10 py-12">
      <section>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="eyebrow">Dashboard</div>
            <h1 className="mt-3 font-display text-4xl font-extrabold sm:text-5xl">
              Your health <span className="text-gradient">at a glance</span>.
            </h1>
            <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
              Track your daily signals, monitor trends, and stay ahead of mental
              health risks with Sentinel&apos;s real-time analysis.
            </p>
          </div>
          <Card className="w-full max-w-md">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                <UserCircle2 className="h-4 w-4 text-brand-cyan" />
                Active user context
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="user_001"
                  aria-label="Active user id"
                />
                <Button
                  variant="secondary"
                  onClick={fetchData}
                  className="shrink-0"
                >
                  Refresh
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                All metrics, trends, and history below are scoped to this user.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Sticky status strip */}
      <Card className="sticky top-[72px] z-30 border-white/15 bg-background/85 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Current prediction
              </p>
              <div className="mt-2 flex items-center gap-2">
                <Badge variant={getRiskBadgeVariant(latestRiskLevel)}>
                  {latestRiskLevel}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {(latestRiskScore * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Trend
              </p>
              <div className="mt-2 flex items-center gap-2 text-sm font-semibold">
                {trendIcon}
                <span className="capitalize">{trendDirection.toLowerCase()}</span>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Last update
              </p>
              <p className="mt-2 text-sm font-medium">
                {latestRecord
                  ? new Date(latestRecord.timestamp).toLocaleString()
                  : "No check-ins yet"}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Safety reminder
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Sentinel is an early-warning tool, not a diagnosis.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {loadError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center gap-3 p-4 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm font-medium">{loadError}</p>
          </CardContent>
        </Card>
      )}

      {latestRiskLevel === "HIGH" && (
        <Card className="border-brand-rose/40 bg-brand-rose/[0.08]">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 text-brand-rose" />
              <div>
                <p className="font-semibold text-brand-rose">
                  High-risk signals detected for this user.
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Use the check-in recommendation panel and consider immediate
                  support resources if distress is increasing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-brand-indigo/5 border-brand-indigo/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Risk Score</CardTitle>
            <Activity className="h-4 w-4 text-brand-indigo" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "..." : stats ? (stats.avg_risk * 100).toFixed(0) : "0"}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Last 30 days average
            </p>
          </CardContent>
        </Card>
        <Card className="bg-brand-teal/5 border-brand-teal/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Days Tracked</CardTitle>
            <Calendar className="h-4 w-4 text-brand-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "..." : stats?.total_days || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active journey length
            </p>
          </CardContent>
        </Card>
        <Card className="bg-brand-emerald/5 border-brand-emerald/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Mood Streak</CardTitle>
            <Heart className="h-4 w-4 text-brand-emerald" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "..." : stats?.low_risk_streak || 0}d</div>
            <p className="text-xs text-muted-foreground mt-1">
              Consecutive Low-risk days
            </p>
          </CardContent>
        </Card>
        <Card className="bg-brand-rose/5 border-brand-rose/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Trend Status</CardTitle>
            <Zap className="h-4 w-4 text-brand-rose" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {isLoading ? "..." : stats?.trend_direction?.toLowerCase() || "Stable"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Overall risk trajectory
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-10 lg:grid-cols-[1fr_400px]">
        <div className="space-y-12">
          {/* Main Content Area */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Behavioral Trends</h2>
              <span className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">
                Last 7 Days
              </span>
            </div>
            {isLoading ? (
              <Card>
                <CardContent className="p-6">
                  <div className="h-64 animate-pulse rounded-xl bg-white/[0.04]" />
                </CardContent>
              </Card>
            ) : (
              <TrendCharts data={history.slice(0, 7)} />
            )}
          </section>

          <section className="space-y-6">
            <h2 className="text-2xl font-bold">Activity History</h2>
            <HistoryLog records={history} userId={userId.trim() || "user"} />
          </section>
        </div>

        <div className="space-y-8">
          {/* Sidebar Area */}
          <section className="space-y-6">
            <h2 className="text-2xl font-bold">New Check-in</h2>
            <CheckInForm
              userId={userId}
              onUserIdChange={setUserId}
              apiBaseUrl={apiBaseUrl}
              onSubmissionSuccess={onCheckInSubmitted}
            />
          </section>

          <Card className="border-brand-amber/30 bg-brand-amber/[0.04]">
            <CardContent className="p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-amber/15 text-brand-amber mb-4">
                <Wrench className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg font-semibold">
                Legacy Dashboard
              </h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                Need more granular ML pipeline metrics or complex Plotly
                visualisations? The original Streamlit dashboard is still
                available.
              </p>
              <Button asChild className="mt-4 w-full" variant="secondary">
                <a href={streamlitUrl} target="_blank" rel="noopener noreferrer">
                  Open Legacy Dashboard
                </a>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
