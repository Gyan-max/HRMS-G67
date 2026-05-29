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
import { cn } from "@/lib/utils";

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

function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} />;
}

const STORAGE_KEY = "sentinel_user_id";

export default function Dashboard() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [userId, setUserId] = useState<string>(
    () => localStorage.getItem(STORAGE_KEY) ?? "user_001",
  );
  const [debouncedUserId, setDebouncedUserId] = useState<string>(userId);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const streamlitUrl =
    import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";

  useEffect(() => {
    const trimmed = userId.trim();
    if (trimmed) localStorage.setItem(STORAGE_KEY, trimmed);
  }, [userId]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedUserId(userId.trim()), 400);
    return () => clearTimeout(t);
  }, [userId]);

  const fetchData = useCallback(async () => {
    if (!debouncedUserId) {
      setStats(null);
      setHistory([]);
      setLoadError(null);
      return;
    }
    setIsLoading(true);
    setLoadError(null);
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch(`${apiBaseUrl}/api/stats/${encodeURIComponent(debouncedUserId)}`),
        fetch(`${apiBaseUrl}/api/history/${encodeURIComponent(debouncedUserId)}?days=30`),
      ]);
      if (!statsRes.ok || !historyRes.ok) throw new Error("Unable to fetch dashboard data");
      const nextStats = (await statsRes.json()) as UserStats;
      const historyData = (await historyRes.json()) as HistoryResponse;
      setStats(nextStats);
      setHistory(historyData.records || []);
    } catch (err: unknown) {
      console.error("Failed to fetch dashboard data:", err);
      setLoadError(err instanceof Error ? err.message : "Failed to load dashboard data");
      setStats(null);
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, debouncedUserId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const latestRecord = useMemo(() => {
    if (!history.length) return null;
    return [...history].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )[0];
  }, [history]);

  const recentHistory = useMemo(
    () =>
      [...history]
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        .slice(-7),
    [history],
  );

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

  const METRIC_CARDS = [
    {
      label: "Avg Risk Score",
      icon: Activity,
      iconColor: "text-brand-indigo",
      cardColor: "bg-brand-indigo/5 border-brand-indigo/20",
      value: isLoading
        ? null
        : `${stats ? (stats.avg_risk * 100).toFixed(0) : "0"}%`,
      sub: "Last 30 days average",
    },
    {
      label: "Days Tracked",
      icon: Calendar,
      iconColor: "text-brand-teal",
      cardColor: "bg-brand-teal/5 border-brand-teal/20",
      value: isLoading ? null : `${stats?.total_days ?? 0}`,
      sub: "Active journey length",
    },
    {
      label: "Low-risk Streak",
      icon: Heart,
      iconColor: "text-brand-emerald",
      cardColor: "bg-brand-emerald/5 border-brand-emerald/20",
      value: isLoading ? null : `${stats?.low_risk_streak ?? 0}d`,
      sub: "Consecutive low-risk days",
    },
    {
      label: "Trend Status",
      icon: Zap,
      iconColor: "text-brand-rose",
      cardColor: "bg-brand-rose/5 border-brand-rose/20",
      value: isLoading
        ? null
        : (stats?.trend_direction?.toLowerCase() ?? "Stable"),
      valueClass: "capitalize",
      sub: "Overall risk trajectory",
    },
  ] as const;

  return (
    <div className="container space-y-10 py-12">
      {/* ── Header ── */}
      <section className="animate-fade-in-up">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="eyebrow">Dashboard</div>
            <h1 className="mt-3 font-display text-4xl font-extrabold sm:text-5xl">
              Your health{" "}
              <span className="text-gradient">at a glance</span>.
            </h1>
            <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
              Track your daily signals, monitor trends, and stay ahead of mental
              health risks with Sentinel&apos;s real-time analysis.
            </p>
          </div>

          {/* User context card */}
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
                <Button variant="secondary" onClick={fetchData} className="shrink-0">
                  Refresh
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                All metrics, trends, and history are scoped to this user.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ── Sticky status strip ── */}
      <Card className="sticky top-[64px] z-30 border-white/15 bg-background/85 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Current prediction
              </p>
              <div className="mt-2 flex items-center gap-2">
                <Badge
                  variant={getRiskBadgeVariant(latestRiskLevel)}
                  className={cn(
                    latestRiskLevel === "HIGH" && "animate-pulse ring-1 ring-brand-rose/40",
                  )}
                >
                  {latestRiskLevel}
                </Badge>
                <span className="text-sm font-medium tabular-nums text-muted-foreground">
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
              <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                Sentinel is an early-warning tool, not a diagnosis.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Error banner ── */}
      {loadError && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center gap-3 p-4 text-destructive">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <p className="text-sm font-medium">{loadError}</p>
          </CardContent>
        </Card>
      )}

      {/* ── HIGH risk alert ── */}
      {latestRiskLevel === "HIGH" && (
        <Card className="border-brand-rose/40 bg-brand-rose/[0.08]">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-brand-rose" />
              <div>
                <p className="font-semibold text-brand-rose">
                  High-risk signals detected for this user.
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Review the recommendation panel and consider immediate support
                  resources if distress is increasing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Metric cards ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {METRIC_CARDS.map(({ label, icon: Icon, iconColor, cardColor, value, sub, ...rest }) => (
          <Card key={label} className={cardColor}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg bg-white/5", iconColor)}>
                <Icon className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              {value === null ? (
                <Skeleton className="h-8 w-20 mb-1" />
              ) : (
                <div className={cn("text-2xl font-bold tabular-nums", "valueClass" in rest ? rest.valueClass : "")}>
                  {value}
                </div>
              )}
              <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── Main grid ── */}
      <div className="grid gap-10 lg:grid-cols-[1fr_400px]">
        <div className="space-y-12">
          {/* Trends */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Behavioral Trends</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Sleep, mood, social contact, and risk over the last 7 check-ins.
                </p>
              </div>
              <span className="hidden text-xs font-semibold uppercase tracking-widest text-muted-foreground sm:block">
                7-day window
              </span>
            </div>

            {isLoading ? (
              <Card>
                <CardContent className="p-6 space-y-4">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-52 w-full" />
                </CardContent>
              </Card>
            ) : (
              <TrendCharts data={recentHistory} />
            )}
          </section>

          {/* History */}
          <section className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold">Activity History</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Last 30 days of check-ins for{" "}
                <span className="font-medium text-foreground">{debouncedUserId || "—"}</span>.
              </p>
            </div>
            {isLoading ? (
              <Card>
                <CardContent className="p-6 space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} className="h-14 w-full" />
                  ))}
                </CardContent>
              </Card>
            ) : (
              <HistoryLog records={history} userId={debouncedUserId || "user"} />
            )}
          </section>
        </div>

        {/* ── Sidebar ── */}
        <div className="space-y-8">
          <section className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold">New Check-in</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Takes under a minute. Results appear immediately.
              </p>
            </div>
            <CheckInForm
              userId={userId}
              onUserIdChange={setUserId}
              apiBaseUrl={apiBaseUrl}
              onSubmissionSuccess={fetchData}
            />
          </section>

          <Card className="border-brand-amber/30 bg-brand-amber/[0.04]">
            <CardContent className="p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-amber/15 text-brand-amber">
                <Wrench className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg font-semibold">Legacy Dashboard</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Need granular ML pipeline metrics or Plotly visualisations? The
                original Streamlit dashboard is still available.
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
