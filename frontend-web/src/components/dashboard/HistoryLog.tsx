import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Download, ClipboardList } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface HistoryRecord {
  timestamp: string;
  sleep_hours: number;
  mood_score: number;
  activity_level: string;
  social_interactions: number;
  risk_score: number;
  risk_level: string;
}

interface HistoryLogProps {
  records: HistoryRecord[];
  userId: string;
}

function riskBorderClass(level: string) {
  if (level === "HIGH")   return "border-l-brand-rose";
  if (level === "MEDIUM") return "border-l-brand-amber";
  return "border-l-brand-emerald";
}

function riskBarColor(level: string) {
  if (level === "HIGH")   return "bg-brand-rose";
  if (level === "MEDIUM") return "bg-brand-amber";
  return "bg-brand-emerald";
}

function badgeVariant(level: string): "danger" | "warning" | "success" {
  if (level === "HIGH")   return "danger";
  if (level === "MEDIUM") return "warning";
  return "success";
}

function escapeCSV(val: unknown): string {
  const str = String(val ?? "");
  return str.includes(",") || str.includes('"') || str.includes("\n")
    ? `"${str.replace(/"/g, '""')}"`
    : str;
}

export function HistoryLog({ records, userId }: HistoryLogProps) {
  const downloadCSV = () => {
    if (!records.length) return;
    const headers = ["Timestamp", "Sleep (h)", "Mood", "Activity", "Social", "Risk Score", "Risk Level"];
    const rows = records.map((r) => [
      new Date(r.timestamp).toLocaleString(),
      r.sleep_hours,
      r.mood_score,
      r.activity_level,
      r.social_interactions,
      r.risk_score,
      r.risk_level,
    ]);
    const csv = [headers, ...rows].map((row) => row.map(escapeCSV).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sentinel_history_${userId}_${new Date().toISOString().split("T")[0]}.csv`;
    a.style.visibility = "hidden";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const empty = records.length === 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div>
          <CardTitle>History Log</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            30-day record for{" "}
            <span className="font-semibold text-foreground">{userId}</span>.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={downloadCSV}
          disabled={empty}
          className="shrink-0"
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />
          Export CSV
        </Button>
      </CardHeader>

      <CardContent>
        {empty ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <ClipboardList className="h-8 w-8 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">
              No check-in history yet. Submit your first check-in above.
            </p>
          </div>
        ) : (
          <>
            {/* ── Mobile cards ── */}
            <div className="space-y-2 md:hidden">
              {records.slice(0, 14).map((record, i) => (
                <div
                  key={i}
                  className={cn(
                    "rounded-xl border border-white/10 bg-white/[0.025] p-4",
                    "border-l-2",
                    riskBorderClass(record.risk_level),
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold">
                        {new Date(record.timestamp).toLocaleDateString([], {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        })}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(record.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <Badge variant={badgeVariant(record.risk_level)}>
                      {record.risk_level}
                    </Badge>
                  </div>

                  <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
                    {[
                      { label: "Mood",   value: `${record.mood_score}/10` },
                      { label: "Sleep",  value: `${record.sleep_hours}h` },
                      { label: "Social", value: `${record.social_interactions}` },
                      { label: "Risk",   value: `${(record.risk_score * 100).toFixed(0)}%` },
                    ].map(({ label, value }) => (
                      <div key={label} className="rounded-md bg-white/[0.04] p-2">
                        <p className="text-muted-foreground">{label}</p>
                        <p className="mt-0.5 font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {records.length > 14 && (
                <p className="pt-2 text-center text-xs text-muted-foreground">
                  Showing 14 of {records.length} — export CSV for the full set.
                </p>
              )}
            </div>

            {/* ── Desktop table ── */}
            <div className="relative hidden w-full overflow-auto md:block">
              <table className="w-full caption-bottom text-sm">
                <thead>
                  <tr className="border-b border-white/8">
                    {["Date", "Mood", "Sleep", "Social", "Activity", "Risk"].map((h) => (
                      <th
                        key={h}
                        className={cn(
                          "h-10 px-3 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground",
                          h === "Date" ? "text-left" : "text-center",
                          h === "Risk" && "text-right",
                        )}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {records.map((record, i) => (
                    <tr
                      key={i}
                      className="border-b border-white/[0.04] transition-colors hover:bg-white/[0.02]"
                    >
                      <td className="p-3 align-middle">
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              "h-7 w-1 rounded-full shrink-0",
                              riskBarColor(record.risk_level),
                              "opacity-60",
                            )}
                          />
                          <div>
                            <p className="text-sm font-medium">
                              {new Date(record.timestamp).toLocaleDateString([], {
                                month: "short",
                                day: "numeric",
                              })}
                            </p>
                            <p className="text-[11px] text-muted-foreground">
                              {new Date(record.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="p-3 text-center align-middle tabular-nums">
                        {record.mood_score}/10
                      </td>
                      <td className="p-3 text-center align-middle tabular-nums">
                        {record.sleep_hours}h
                      </td>
                      <td className="p-3 text-center align-middle tabular-nums">
                        {record.social_interactions}
                      </td>
                      <td className="p-3 text-center align-middle capitalize text-muted-foreground">
                        {record.activity_level}
                      </td>
                      <td className="p-3 text-right align-middle">
                        <div className="inline-flex flex-col items-end gap-1">
                          <Badge variant={badgeVariant(record.risk_level)}>
                            {record.risk_level}
                          </Badge>
                          <div className="h-1 w-14 overflow-hidden rounded-full bg-white/[0.06]">
                            <div
                              className={cn("h-full rounded-full", riskBarColor(record.risk_level), "opacity-70")}
                              style={{ width: `${(record.risk_score * 100).toFixed(0)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
