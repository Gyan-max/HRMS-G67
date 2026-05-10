import { useEffect, useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { CheckInForm } from "@/components/dashboard/CheckInForm";
import { TodayAssessment } from "@/components/dashboard/TodayAssessment";
import { TrendsTab } from "@/components/dashboard/TrendsTab";
import { HistoryTab } from "@/components/dashboard/HistoryTab";
import type { CheckInResponse } from "@/api/types";

const ACTIVE_USER_KEY = "sentinel.activeUserId";

export default function Dashboard() {
  const [activeUserId, setActiveUserId] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    return window.localStorage.getItem(ACTIVE_USER_KEY) ?? "";
  });

  const [latest, setLatest] = useState<CheckInResponse | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (activeUserId) {
      window.localStorage.setItem(ACTIVE_USER_KEY, activeUserId);
    }
  }, [activeUserId]);

  const handleSuccess = (result: CheckInResponse) => {
    setActiveUserId(result.user_id);
    setLatest(result);
  };

  return (
    <div className="container space-y-10 py-12">
      <header className="space-y-3">
        <p className="eyebrow">Dashboard</p>
        <h1 className="font-display text-4xl font-bold tracking-tight md:text-5xl">
          <span className="text-gradient">Daily check-in &amp; trends</span>
        </h1>
        <p className="max-w-3xl text-base text-muted-foreground">
          Submit a one-minute check-in. Sentinel runs the same safety screen,
          weighted risk engine, NLP analyser, and anomaly detector as the
          legacy Streamlit dashboard — and surfaces crisis resources
          immediately when self-harm language is detected.
        </p>
      </header>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        <div className="space-y-6">
          <CheckInForm
            defaultUserId={activeUserId}
            onSuccess={handleSuccess}
          />
          <Card>
            <CardContent className="p-6">
              <p className="eyebrow">Tip</p>
              <p className="mt-3 text-sm text-muted-foreground">
                Submitting at the same time each day gives the anomaly detector
                a cleaner baseline. Three days of check-ins are enough to
                establish that baseline.
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="today" className="w-full">
          <TabsList>
            <TabsTrigger value="today">Today</TabsTrigger>
            <TabsTrigger value="trends">Trends (7d)</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="today">
            {latest ? (
              <TodayAssessment result={latest} />
            ) : (
              <Card>
                <CardContent className="p-10 text-center">
                  <h4 className="font-display text-lg font-semibold">
                    Submit a check-in to see today's assessment
                  </h4>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Once you submit, your risk badge, component scores,
                    recommendation, and (when relevant) the crisis banner
                    will appear here.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="trends">
            <TrendsTab userId={activeUserId} />
          </TabsContent>

          <TabsContent value="history">
            <HistoryTab userId={activeUserId} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
