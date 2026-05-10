import { useState, useEffect } from "react";
import { Wrench, Activity, Calendar, Heart, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckInForm } from "@/components/dashboard/CheckInForm";
import { TrendCharts } from "@/components/dashboard/TrendCharts";
import { HistoryLog } from "@/components/dashboard/HistoryLog";

/**
 * Dashboard page featuring live check-in, trends, and history.
 */
export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const userId = "user_001"; // Default for now
  
  const streamlitUrl =
    import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";

  const fetchData = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch(`http://localhost:8000/api/stats/${userId}`),
        fetch(`http://localhost:8000/api/history/${userId}?days=30`)
      ]);
      
      if (statsRes.ok) setStats(await statsRes.json());
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData.records || []);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Callback to refresh dashboard data after a new check-in
  const onCheckInSubmitted = () => {
    fetchData();
  };

  return (
    <div className="container space-y-10 py-16">
      <section>
        <div className="eyebrow">Dashboard</div>
        <h1 className="mt-3 font-display text-4xl font-extrabold sm:text-5xl">
          Your health <span className="text-gradient">at a glance</span>.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
          Track your daily signals, monitor trends, and stay ahead of mental health risks
          with Sentinel's real-time analysis.
        </p>
      </section>

      {/* Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-brand-indigo/5 border-brand-indigo/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Risk Score</CardTitle>
            <Activity className="h-4 w-4 text-brand-indigo" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats ? (stats.avg_risk * 100).toFixed(0) : "0"}%
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
            <div className="text-2xl font-bold">{stats?.total_days || 0}</div>
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
            <div className="text-2xl font-bold">{stats?.low_risk_streak || 0}d</div>
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
              {stats?.trend_direction?.toLowerCase() || "Stable"}
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
              <span className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">Last 7 Days</span>
            </div>
            <TrendCharts data={history.slice(0, 7)} />
          </section>

          <section className="space-y-6">
            <h2 className="text-2xl font-bold">Activity History</h2>
            <HistoryLog records={history} />
          </section>
        </div>

        <div className="space-y-8">
          {/* Sidebar Area */}
          <section className="space-y-6">
            <h2 className="text-2xl font-bold">New Check-in</h2>
            <CheckInForm onSubmissionSuccess={onCheckInSubmitted} />
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
                Need more granular ML pipeline metrics or complex Plotly visualisations?
                The original Streamlit dashboard is still available.
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


