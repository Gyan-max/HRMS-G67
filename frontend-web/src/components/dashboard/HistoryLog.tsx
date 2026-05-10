import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

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

export function HistoryLog({ records, userId }: HistoryLogProps) {
  const downloadCSV = () => {
    if (!records.length) return;
    
    const headers = ["Timestamp", "Sleep", "Mood", "Activity", "Social", "Risk Score", "Risk Level"];
    const rows = records.map(r => [
      new Date(r.timestamp).toLocaleString(),
      r.sleep_hours,
      r.mood_score,
      r.activity_level,
      r.social_interactions,
      r.risk_score,
      r.risk_level
    ]);
    
    const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `sentinel_history_${userId}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div>
          <CardTitle>History Log</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Your check-ins from the last 30 days for <span className="font-semibold text-foreground">{userId}</span>.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={downloadCSV} disabled={!records.length}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 md:hidden">
          {records.length === 0 ? (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 text-center text-sm text-muted-foreground">
              No check-in history found.
            </div>
          ) : (
            records.slice(0, 12).map((record, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">
                      {new Date(record.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(record.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <Badge variant={
                    record.risk_level === 'HIGH' ? 'danger' :
                    record.risk_level === 'MEDIUM' ? 'warning' : 'success'
                  }>
                    {record.risk_level}
                  </Badge>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded-md bg-white/[0.04] p-2">
                    <p className="text-muted-foreground">Mood</p>
                    <p className="font-semibold">{record.mood_score}/10</p>
                  </div>
                  <div className="rounded-md bg-white/[0.04] p-2">
                    <p className="text-muted-foreground">Sleep</p>
                    <p className="font-semibold">{record.sleep_hours}h</p>
                  </div>
                  <div className="rounded-md bg-white/[0.04] p-2">
                    <p className="text-muted-foreground">Social</p>
                    <p className="font-semibold">{record.social_interactions}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="relative hidden w-full overflow-auto md:block">
          <table className="w-full caption-bottom text-sm">
            <thead className="[&_tr]:border-b border-white/10">
              <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                <th className="h-10 px-2 text-left align-middle font-medium text-muted-foreground">Date</th>
                <th className="h-10 px-2 text-center align-middle font-medium text-muted-foreground">Mood</th>
                <th className="h-10 px-2 text-center align-middle font-medium text-muted-foreground">Sleep</th>
                <th className="h-10 px-2 text-center align-middle font-medium text-muted-foreground">Social</th>
                <th className="h-10 px-2 text-right align-middle font-medium text-muted-foreground">Assessment</th>
              </tr>
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {records.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    No check-in history found.
                  </td>
                </tr>
              ) : (
                records.map((record, i) => (
                  <tr key={i} className="border-b border-white/5 transition-colors hover:bg-white/[0.02]">
                    <td className="p-2 align-middle">
                      <div className="font-medium">
                        {new Date(record.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(record.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                    <td className="p-2 text-center align-middle">{record.mood_score}/10</td>
                    <td className="p-2 text-center align-middle">{record.sleep_hours}h</td>
                    <td className="p-2 text-center align-middle">{record.social_interactions}</td>
                    <td className="p-2 text-right align-middle">
                      <Badge variant={
                        record.risk_level === 'HIGH' ? 'danger' : 
                        record.risk_level === 'MEDIUM' ? 'warning' : 'success'
                      }>
                        {record.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
