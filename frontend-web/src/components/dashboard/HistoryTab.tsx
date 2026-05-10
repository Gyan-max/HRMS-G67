import { useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import type { CheckInRecord, RiskLevel } from "@/api/types";

interface HistoryTabProps {
  userId: string;
}

const formatTimestamp = (iso: string) => {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const riskVariant = (
  level: RiskLevel | null | undefined,
): BadgeProps["variant"] => {
  if (level === "HIGH") return "danger";
  if (level === "MEDIUM") return "warning";
  if (level === "LOW") return "success";
  return "muted";
};

export function HistoryTab({ userId }: HistoryTabProps) {
  const trimmed = userId.trim();

  const historyQuery = useQuery({
    queryKey: ["history", trimmed, { limit: 30 }],
    queryFn: () => api.getHistory(trimmed, { limit: 30 }),
    enabled: trimmed.length > 0,
  });

  if (!trimmed) {
    return (
      <Empty
        title="Enter a User ID and submit a check-in first"
        body="History only shows after at least one check-in for this user."
      />
    );
  }

  if (historyQuery.isLoading) {
    return <Empty title="Loading history…" body="Fetching from backend." />;
  }
  if (historyQuery.isError) {
    return (
      <Empty
        title="Couldn't load history"
        body="Make sure the FastAPI backend is running on localhost:8000."
        tone="error"
      />
    );
  }

  const records = historyQuery.data?.records ?? [];
  if (records.length === 0) {
    return (
      <Empty
        title="No check-in data yet"
        body="Submit your first check-in to start building history."
      />
    );
  }

  const sorted = [...records].sort(
    (a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  return (
    <Card>
      <CardContent className="p-0">
        <div className="flex items-center justify-between p-6">
          <div>
            <h4 className="font-display text-lg font-semibold">
              Recent check-ins
            </h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Most recent {sorted.length} check-ins for{" "}
              <span className="font-medium text-foreground">{trimmed}</span>.
            </p>
          </div>
        </div>
        <div className="overflow-x-auto border-t border-white/5">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/[0.02] text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
              <tr>
                <Th>When</Th>
                <Th>Risk</Th>
                <Th>Score</Th>
                <Th>Sleep</Th>
                <Th>Mood</Th>
                <Th>Activity</Th>
                <Th>Social</Th>
                <Th>Journal</Th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((rec) => (
                <Row key={rec.id} rec={rec} />
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ rec }: { rec: CheckInRecord }) {
  return (
    <tr className="border-t border-white/5 transition-colors hover:bg-white/[0.02]">
      <Td className="whitespace-nowrap text-foreground/90">
        {formatTimestamp(rec.timestamp)}
      </Td>
      <Td>
        <Badge variant={riskVariant(rec.risk_level)}>
          {rec.risk_level ?? "—"}
        </Badge>
      </Td>
      <Td className="font-mono text-xs text-foreground/85">
        {typeof rec.risk_score === "number"
          ? rec.risk_score.toFixed(3)
          : "—"}
      </Td>
      <Td>{rec.sleep_hours.toFixed(1)} hr</Td>
      <Td>{rec.mood_score}/10</Td>
      <Td className="capitalize text-muted-foreground">{rec.activity_level}</Td>
      <Td>{rec.social_interactions}</Td>
      <Td className="max-w-[280px] truncate text-muted-foreground">
        {rec.journal_text ? rec.journal_text : "—"}
      </Td>
    </tr>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-6 py-3 font-semibold">{children}</th>;
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={`px-6 py-3 ${className}`}>{children}</td>;
}

function Empty({
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
